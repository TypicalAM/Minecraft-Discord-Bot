"""Utilities for the Minecraft Discord Bot"""

import logging
import os
import asyncio
import subprocess
from typing import Optional
import dotenv
from mcstatus import MinecraftServer
from rcon import rcon

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
fh = logging.StreamHandler()
fh_formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
fh.setFormatter(fh_formatter)
logger.addHandler(fh)

dotenv.load_dotenv()
TOKEN       = os.getenv("DISCORD_TOKEN")
SERVER_PATH = os.getenv("SERVER_PATH")
OWNER_NAME  = os.getenv("OWNER_NICK")
TMUX_COMMAND= os.getenv("TMUX_COMMAND")
RCON_PASS   = os.getenv("RCON_PASS")

STATUS_CHECK_FREQUENCY  = int(os.getenv("STATUS_CHECK_FREQUENCY"))
STATUS_CHECK_NUM        = int(os.getenv("STATUS_CHECK_NUMBER"))

RCON_ARGS = {
        "host": "127.0.0.1",
        "port": 25575,
        "passwd": RCON_PASS
}

server = MinecraftServer.lookup(RCON_ARGS["host"])

async def status_check() -> Optional[int]:
    """Check if the server is up, if yes, return the number of players"""

    logger.info('Checking status')
    try:
        status = await server.async_status()
    except ConnectionRefusedError:
        logger.warning('Status: closed')
        return

    logger.info('Status: running')
    return -1 if not status.players.online else status.players.online

async def inject_command(command: tuple) -> Optional[str]:
    """Try to inject a command using the rcon protocol"""

    logger.info('Injecting a command')

    if not command:
        logger.warning('Injection: no command given')
        return

    try:
        output = await rcon(*command, **RCON_ARGS)
    except ConnectionRefusedError:
        logger.warning('Injection: Connection refused')
        return
    except TimeoutError:
        logger.warning('Injection: Connection timeout')
        return

    logger.warning('Injection: Output received')

    output = (output[:100] + '..') if len(output) > 100 else output
    return output

async def close_server() -> bool:
    """Close the server using the rcon protocol"""

    logger.info('Closing server')
    try:
        await rcon("stop", **RCON_ARGS)
    except ConnectionRefusedError:
        logger.warning('Closing: Server already closed')
        return False

    logger.info('Closing: closed')
    await asyncio.sleep(STATUS_CHECK_FREQUENCY)
    return True


async def players_check() -> Optional[list]:
    """Check the names of the players in the server"""

    logger.info('Checking players by query')
    try:
        query = await server.async_query()
    except ConnectionRefusedError:
        logger.warning('Query: Server closed')
        return
    logger.info('Query: received player data')
    return query.players.names

async def start_server() -> bool:
    """Try to start the server"""
    logger.info('Starting server')

    try:
        subprocess.check_output(TMUX_COMMAND.split(), cwd=SERVER_PATH)
    except subprocess.CalledProcessError:
        logger.warning('Starting: CalledProcessError')
        return False
    logger.info('Start: server is starting')
    return True

async def run_post_start() -> bool:
    """Confirm that the server can be connected to"""

    logger.info('Running post start operations')
    for i in range(STATUS_CHECK_NUM):
        await asyncio.sleep(STATUS_CHECK_FREQUENCY)
        try:
            await rcon("help", **RCON_ARGS)
        except ConnectionRefusedError:
            pass
        except TimeoutError:
            pass
        else:
            logger.info('Post start: Confirmed running (%s attempt)', i)
            break
    else:
        # If the server console failed then the 2nd check will not be attempted
        logger.info('Post start: failed to connect after %s tries', STATUS_CHECK_NUM)
        return False

    # Second check to make sure the client can connect
    logger.info('Post start: 2nd check')
    data = await status_check()
    if not data:
        return False
    logger.info('Post start: server is up and running')
    return True

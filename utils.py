"""Utilities for the minecraft discord bot"""

import logging
from typing import Optional
import settings
import subprocess
import asyncio

from mcstatus import JavaServer
from rcon import rcon


def get_logger() -> logging.Logger:
    fh = logging.StreamHandler()
    fh_formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    fh.setFormatter(fh_formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    logger.addHandler(fh)
    return logger


# Get the logger and the server instance
logger = get_logger()


async def status_check() -> bool:
    """Check if the server is up"""

    logger.info("Checking status")
    try:
        server = JavaServer.lookup(settings.RCON_ARGS["host"])
        await server.async_status()
    except Exception as e:
        logger.warning(f"Status: {e.__class__.__name__}")                       
        return False

    logger.info("Status: running")
    return True


async def inject_command(command: str) -> Optional[str]:
    """Try to inject a command using the rcon protocol"""

    logger.info("Injecting a command")

    if not command:
        logger.warning("Injection: no command given")
        return

    try:
        output = await rcon(*command.split(), **settings.RCON_ARGS)
    except ConnectionRefusedError:
        logger.warning("Injection: Connection refused")
        return
    except TimeoutError:
        logger.warning("Injection: Connection timeout")
        return

    logger.warning("Injection: Output received")

    if output is None:
        output = ""
    else:
        output = (output[:100] + "..") if len(output) > 100 else output
    return output


async def close_server() -> bool:
    """Close the server using the rcon protocol"""

    logger.info("Closing server")
    try:
        await rcon("stop", **settings.RCON_ARGS)
    except Exception as e:
        logger.warning("Closing: Server already closed")
        logger.warning("Closing: %s", e)
        return False

    logger.info("Closing: closed")
    await asyncio.sleep(settings.STATUS_CHECK_FREQUENCY)
    return True


async def players_check() -> Optional[list]:
    """Check the names of the players in the server"""

    logger.info("Checking players by query")
    try:
        server = JavaServer.lookup(settings.RCON_ARGS["host"])
        query = await server.async_query()
    except Exception as e:
        logger.warning("Query: %s", e.__class__.__name__)
        logger.warning("Query: Server closed")
        return
    logger.info("Query: received player data")
    return query.players.names


async def start_server() -> bool:
    """Try to start the server"""
    logger.info("Starting server")

    try:
        subprocess.check_output(settings.TMUX_COMMAND.split(), cwd=settings.SERVER_PATH)
    except subprocess.CalledProcessError:
        logger.warning("Starting: CalledProcessError")
        return False
    logger.info("Start: server is starting")
    return True


async def run_post_start() -> bool:
    """Confirm that the server can be connected to"""

    logger.info("Running post start operations")
    for i in range(settings.STATUS_CHECK_NUMBER):
        await asyncio.sleep(settings.STATUS_CHECK_FREQUENCY)
        try:
            await rcon("help", **settings.RCON_ARGS)
        except TimeoutError:
            pass
        else:
            logger.info("Post start: Confirmed running (%s attempt)", i)
            break
    else:
        # If the server console failed then the 2nd check will not be attempted
        logger.info(
            "Post start: failed to connect after %s tries", settings.STATUS_CHECK_NUMBER
        )
        return False

    # Second check to make sure the client can connect
    logger.info("Post start: 2nd check")
    data = await status_check()
    if not data:
        return False
    logger.info("Post start: server is up and running")
    return True

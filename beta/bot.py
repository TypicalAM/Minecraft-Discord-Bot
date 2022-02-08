import subprocess
import sys
import os

import logging
import asyncio
from typing import Optional

try:
    from rcon import rcon
    import discord
    from dotenv import load_dotenv
    from mcstatus import MinecraftServer
except ImportError:
    logging.info(
        """
    One of the following libraries was not loaded:
    rcon, discord, dotenv, MinecraftServer
   """
    )
    sys.exit()


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
BOT_NAME = os.getenv("BOT_NAME")
JAVA_WD = os.getenv("JAVA_WD")
OWNER_NAME = os.getenv("OWNER_NAME")

CHECK_FREQ = 5
TIMEOUT = 10

JAVA_ARGS = "/usr/bin/java -Xmx5G -Xms5G -jar server.jar nogui"
TMUX_SESSION = "tmux new-session -d -s 'java_server' " + JAVA_ARGS
RCON_ARGS = {"host": "127.0.0.1", "port": 25575, "passwd": "password"}
ON_MESSAGE_MAP = {
    "mc stop": "mc_stop_server",
    "mc start": "mc_start_server",
    "mc help": "mc_show_help",
    "mc status": "mc_check_status",
}
STATUS_MESSAGES = {
    "mc_server_turned_off": "Serwera nie ma, nie żyje.",
    "mc_post_start_first": "Sprawdzanie rozruchu",
    "mc_post_start_checks": "Sprawdzanie rozruchu (RCON)",
    "mc_post_start_checks_2":"Sprawdzenie rozruchu (LOOKUP)",
    "mc_server_error": "Jeszcze nie skończyłem",
    "mc_status_players": "Graczy online:",
    "mc_status_ping": "Czas odp natalki",
    "mc_status_started":"Wystartował!",
    "mc_already_started":"Już jest włączony",
    "mc_starting":"Startowanie...",
    "mc_stop_people_still_playing":"Nie zrobie tego, zraniłbym graczy...",
    "mc_stopping":"Zatrzymywanie",
    "mc_stopped":"Zatrzymany!",
    "mc_help": "To jest bot na discordzie, żeby włączać i wyłączać serwer mc:\nmc start - włącz serwer\nmc stop - wyłącz serwer\nmc help - pomoc\nmc status - sprawdź status (przed tym jak włączysz jak debil jebany)",
    "mc_inject_noargs":"Nie ma argumentów!",
    "mc_process_started":"Sesja tmux już wystartowała! (to troche dziwne)\nSpróbuj zrestartowac serwer",
}

client = discord.Client()

async def status_check() -> Optional[tuple]:
    logging.info('Checking status')
    try:
        status = MinecraftServer.lookup(RCON_ARGS["host"]).status()
    except ConnectionRefusedError:
        logging.warning('The server refused the status check')
        return
    return (
        None
        if "Error" in status.version.name or "Offline" in status.version.name
        else (status.players.online, status.latency)
    )

async def players_check() -> Optional[list]:
    logging.info('Trying a lookup check')
    try:
        query = MinecraftServer.lookup(RCON_ARGS["host"]).query()
    except ConnectionRefusedError:
        logging.warning('The server refused the lookup check')
        return
    except TimeoutError:
        logging.warning('The server timed out the connection')
        return
    logging.info('Player names retrieved')
    return query.players.names

async def mc_check_status(channel):
    logging.info('Command issued: status check')
    data = await status_check()
    if not data:
        await channel.send(STATUS_MESSAGES["mc_server_turned_off"])
    else:
        players = await players_check()
        mess = f"""\n{STATUS_MESSAGES['mc_status_ping']} {round(data[1],2)}\n{STATUS_MESSAGES['mc_status_players']} {data[0]}"""
        if players:
            mess += f'\n'
            for player in players:
                mess += player+"\n"
        await channel.send(mess)


async def mc_post_start(to_edit):
    logging.info('Running post-start operations')
    await asyncio.sleep(CHECK_FREQ)
    await to_edit.edit(content=STATUS_MESSAGES["mc_post_start_first"])
    for check_num in range(TIMEOUT):
        await to_edit.edit(
            content=f"{STATUS_MESSAGES['mc_post_start_checks']} [{check_num+1}/{TIMEOUT}]"
        )
        try:
            await rcon("help", **RCON_ARGS)
        except ConnectionRefusedError:
            logging.info(f"Checking startup [{check_num+1}/{TIMEOUT}]")
        else:
            break
        await asyncio.sleep(CHECK_FREQ)

    await to_edit.edit(content=STATUS_MESSAGES["mc_post_start_checks_2"])
    data = await status_check()
    if data:
        logging.info('Server has started')
        await to_edit.edit(content=STATUS_MESSAGES["mc_status_started"])
    else:
        await to_edit.edit(content=STATUS_MESSAGES["mc_server_error"])


async def mc_start_server(channel):
    """A function to try to start up the minecraft server"""

    logging.info('Command issued: Server start')

    if await status_check():
        await channel.send(STATUS_MESSAGES["mc_status_started"])
        logging.info('Trying to start server')
        return
    try:
        subprocess.check_output(TMUX_SESSION.split(),cwd=JAVA_WD)
    except subprocess.CalledProcessError:
        logging.warning('Server start failed: subprocess already exists')
        await channel.send(STATUS_MESSAGES["mc_process_started"])
    except Exception:
        logging.warning('Server start failed: random exception')
        await channel.send(STATUS_MESSAGES["mc_server_error"])
        return

    logging.info('Subprocess started')

    to_edit = await channel.send(STATUS_MESSAGES["mc_starting"])
    await mc_post_start(to_edit)


async def mc_stop_server(channel):
    logging.info('Command issued: Stop server')
    data = await status_check()
    if not data:
        await channel.send(STATUS_MESSAGES["mc_server_turned_off"])
        logging.warning('Server is down')
    else:
        if data[0] > 0:
            logging.warning('Shutdown prevented: people alredy on the server')
            await channel.send(STATUS_MESSAGES["mc_stop_people_still_playing"])
            return
        else:
            logging.info('Trying to stop')
            to_edit = await channel.send(STATUS_MESSAGES["mc_stopping"])
            try:
                await rcon("stop", **RCON_ARGS)
            except ConnectionRefusedError:
                logging.warning('Server stop failed: Server stopped somewhere down the line')
                pass
            await asyncio.sleep(CHECK_FREQ)
            logging.info('Server stopped')
            await to_edit.edit(content=STATUS_MESSAGES["mc_stopped"])

async def mc_inject_command(channel, command):
    logging.info('Command issued: Server command injection')
    logging.info(f'Injecting command {command}')
    if not command:
        await channel.send(STATUS_MESSAGES["mc_inject_noargs"])
        return
    data = await status_check()
    if not data:
        logging.warning('Command not issued: server down')
        await channel.send(STATUS_MESSAGES["mc_server_turned_off"])
        return
    try:
        result = await rcon(*command.split(), **RCON_ARGS)
    except ConnectionRefusedError:
        logging.warning('Injecting failed: server down')
        await channel.send(STATUS_MESSAGES["mc_server_turned_off"])
        return

    logging.info('Command injection successfull: returning the result')
    mess = (result[:100] + '..') if len(result) > 100 else result
    await channel.send(f'Result:\n{mess}')

async def mc_show_help(channel):
    logging.info('Command triggered: Show help')
    await channel.send(STATUS_MESSAGES["mc_help"])


@client.event
async def on_ready():
    logging.info(f"{client.user} is online")


@client.event
async def on_message(message):
    if message.author.name == BOT_NAME:
        return
    if 'mc inject' in message.content.lower():
        if message.author.name == OWNER_NAME:
            await mc_inject_command(message.channel, message.content[len('mc inject')+1:])

    if message.content.lower() in ON_MESSAGE_MAP:
        logging.info(f'{message.author.name} issued a valid command!')
        function = ON_MESSAGE_MAP[message.content.lower()]
        await globals()[function](message.channel)

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d %I:%M:%S %p')
logging.getLogger().setLevel(logging.INFO)
client.run(TOKEN)

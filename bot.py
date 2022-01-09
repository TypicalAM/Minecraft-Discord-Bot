import subprocess
import sys
import os

import asyncio
from typing import Optional

try:
    from rcon import rcon
    import discord
    from dotenv import load_dotenv
    from mcstatus import MinecraftServer
except ImportError:
    print(
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

JAVA_ARGS = "/usr/bin/java -Xmx5G -Xms5G -jar server.jar nogui"
TMUX_SESSION = "tmux new-session -d -s 'java_server' "+JAVA_ARGS
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
    "mc_process_started":"Sesja tmux już wystartowała! (to troche dziwne)\nSpróbuj zrestartowac serwer"
}


CHECK_FREQ = 5
TIMEOUT = 10

client = discord.Client()


async def status_check() -> Optional[tuple]:
    try:
        status = MinecraftServer.lookup(RCON_ARGS["host"]).status()
    except ConnectionRefusedError:
        return
    return (
        None
        if "Error" in status.version.name or "Offline" in status.version.name
        else (status.players.online, status.latency)
    )

async def players_check() -> Optional[list]:
    try:
        query = MinecraftServer.lookup(RCON_ARGS["host"]).query()
    except ConnectionRefusedError:
        return
    except TimeoutError:
        return
    return query.players.names

async def mc_check_status(channel):
    print('Checking status')
    data = await status_check()
    players = await players_check()
    if not data:
        await channel.send(STATUS_MESSAGES["mc_server_turned_off"])
    else:
        mess = f"""{STATUS_MESSAGES['mc_status_players']} {data[0]}\n{STATUS_MESSAGES['mc_status_ping']} {round(data[1],2)}"""
        if players:
            mess += '\nGracze:\n'
            for player in players:
                mess += player+"\n"
        await channel.send(mess)


async def mc_post_start(to_edit):
    await asyncio.sleep(CHECK_FREQ)
    await to_edit.edit(content=STATUS_MESSAGES["mc_post_start_first"])
    for check_num in range(TIMEOUT):
        await to_edit.edit(
            content=f"{STATUS_MESSAGES['mc_post_start_checks']} [{check_num+1}/{TIMEOUT}]"
        )
        try:
            await rcon("help", **RCON_ARGS)
        except ConnectionRefusedError:
            print(f"Sprawdzenie [{check_num+1}/{TIMEOUT}]")
        else:
            break
        await asyncio.sleep(CHECK_FREQ)

    await to_edit.edit(content=STATUS_MESSAGES["mc_post_start_checks_2"])
    data = await status_check()
    if data:
        await to_edit.edit(content=STATUS_MESSAGES["mc_status_started"])
    else:
        await to_edit.edit(content=STATUS_MESSAGES["mc_server_error"])


async def mc_start_server(channel):
    """A function to try to start up the minecraft server"""

    if await status_check():
        await channel.send(STATUS_MESSAGES["mc_status_started"])
        return
    try:
        print('Odpalanie serwa')
        subprocess.check_output(TMUX_SESSION.split(),cwd=JAVA_WD)
    except subprocess.CalledProcessError:
        print('Subproces juz istnieje mimo tego ze serwer nie jest offline')
        await channel.send(STATUS_MESSAGES["mc_process_started"])
    except Exception:
        await channel.send(STATUS_MESSAGES["mc_server_error"])
        return
        
    print('Odpalony')

    to_edit = await channel.send(STATUS_MESSAGES["mc_starting"])
    await mc_post_start(to_edit)


async def mc_stop_server(channel):
    print('Stopping')
    data = await status_check()
    if not data:
        await channel.send(STATUS_MESSAGES["mc_server_turned_off"])
    else:
        if data[0] > 0:
            await channel.send(STATUS_MESSAGES["mc_stop_people_still_playing"])
            return
        else:
            to_edit = await channel.send(STATUS_MESSAGES["mc_stopping"])
            try:
                await rcon("stop", **RCON_ARGS)
            except ConnectionRefusedError:
                pass
            await asyncio.sleep(CHECK_FREQ)
            await to_edit.edit(content=STATUS_MESSAGES["mc_stopped"])

async def mc_inject_command(channel, command):
    print(f'Injecting command {command}')
    if not command:
        await channel.send(STATUS_MESSAGES["mc_inject_noargs"])
        return
    data = await status_check()
    if not data:
        await channel.send(STATUS_MESSAGES["mc_server_turned_off"])
    try:
        result = await rcon(*command.split(), **RCON_ARGS)
    except ConnectionRefusedError:
        await channel.send(STATUS_MESSAGES["mc_server_turned_off"])

    mess = (result[:100] + '..') if len(result) > 100 else result
    await channel.send(f'Result:\n{mess}')

async def mc_show_help(channel):
    await channel.send(STATUS_MESSAGES["mc_help"])


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


@client.event
async def on_message(message):
    if message.author.name == BOT_NAME:
        return
    if 'mc inject' in message.content.lower():
        if message.author.name == OWNER_NAME:
            await mc_inject_command(message.channel, message.content[len('mc inject')+1:])

    if message.content.lower() in ON_MESSAGE_MAP:
        function = ON_MESSAGE_MAP[message.content.lower()]
        await globals()[function](message.channel)

client.run(TOKEN)

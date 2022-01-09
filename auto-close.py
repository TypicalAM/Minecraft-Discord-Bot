import sys
import os
from time import sleep
from typing import Optional

try:
    from mcstatus import MinecraftServer
    from dotenv import load_dotenv
    from rcon import Client
except ImportError:
    print("Not able to restart the server")
    sys.exit()

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RCON_PASS = os.getenv("RCON_PASS")
HOST = "127.0.0.1"
RCON_PORT = 25575
DELAY = 1


def lookup() -> Optional[int]:
    try:
        status = MinecraftServer.lookup(HOST).status()
    except ConnectionRefusedError:
        print("Not able to connect to the server")
        return
    if "Error" in status.version.name or "Offline" in status.version.name:
        print("Server is turned off")
        return
    online = status.players.online
    return online


def main() -> None:
    players_online = lookup()
    if players_online != None and players_online == 0:
        print("First status successfull")
        print(players_online)
        sleep(DELAY)
        players_online = lookup()
        if players_online != None and players_online == 0:
            print("Second status successfull")
            try:
                with Client(host=HOST, port=RCON_PORT, passwd=RCON_PASS) as client:
                    client.run("stop")
                    print("help ran")
            except ConnectionRefusedError:
                return

main()

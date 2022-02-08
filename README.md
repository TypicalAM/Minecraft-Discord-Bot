# Minecraft Server Bot

---

A small discord bot to manage a local minecraft server

---

## Dependencies

Install the following python packages before you use this bot.

- `mcstatus` : Checking the status of your minecraft server

- `rcon` : Communication with the server using the `rcon` protocol

- `dotenv` : To avoid hard coding sensitive information (like a [Discord Token](https://discord.com/developers/docs/topics/oauth2))

- `discord.py` : Arriving at your discord server!

## Installation guide

Follow these steps to get the bot on your sever.

- Clone this repo

```shell
git clone https://github.com/TypicalAM/Minecraft-Discord-Bot
```

- Install the dependencies (all of them are available using [pip3](https://pip.pypa.io/en/stable/getting-started/))

```shell
pip3 install mcstatus rcon dotenv discord
```

- Create and invite a discord bot

[This](https://discordpy.readthedocs.io/en/stable/discord.html) official guide is very helpful in creating the bot and getting the discord token that we need.

- Create the .env file

The `.env` file inside the project directory is read to get the sensitive data of the application, it should look something like this:

```shell
# Your discord token
DISCORD_TOKEN='abc123def'
# Your rcon password
RCON_PASS='mypassword'
# The nickname of the owner of the bot
OWNER_NICK='test#0001'
# The path where server.jar resides
SERVER_PATH='/opt/minecraft/Paper'
STATUS_CHECK_FREQUENCY='5'
STATUS_CHECK_NUMBER='10'
TMUX_COMMAND='...'
```

Let's give special attention to the last variable `TMUX_COMMMAND`. This command generates a [tmux](https://www.hamvocke.com/blog/a-quick-and-easy-guide-to-tmux/) session to monitor the console of the Java server. Once the server starts, it can be easily accessed using `tmux attach`.

An example command for starting a minecraft server would look something like this:

```shell
tmux new-session -d -s 'java_server' /usr/bin/java -Xmx3G -Xms3G -jar server.jar nogui"
```

Where the amount of RAM used is 3G

- Once the `.env` file is created, we are basically done and we can start the server using the below command. If successful, we should see something like this:

```shell
python3 mc_bot_discord.py
[16:10:14] MyBot#2986 logged in!
```

# Minecraft Server Bot

A small discord bot to manage a local minecraft server

---

## Available commands

Here are the commands that the bot can respond to:

- `/status` : Show the status of the server

- `/start` : Start the server if it isn't started yet

- `/stop` : Stop the server if it isn't stopped yet and there are no people

- `/inject` : Owner command to inject a command into the server's console, e.g. `/inject kick my_user` would insert `kick my_user`

- `/lightning` : Strike a player with mighty lightning

---

## Dependencies

Install the following python packages before you use this bot.

- `mcstatus` : Checking the status of your minecraft server

- `rcon` : Communication with the server using the `rcon` protocol

- `dotenv` : To avoid hard coding sensitive information (like a [Discord Token](https://discord.com/developers/docs/topics/oauth2))

- `discord-py-interactions` : Arriving at your discord server!

- Rcon and query enabled in your minecraft server settings. Here is a [quick rundown of the options](https://minecraft.fandom.com/wiki/Server.properties)

## Installation guide

Follow these steps to get the bot on your server.

- Clone this repo

```shell
git clone https://github.com/TypicalAM/Minecraft-Discord-Bot
```

- Install the dependencies (all of them are available using [pip3](https://pip.pypa.io/en/stable/getting-started/))

```shell
pip3 install -r requirements.txt
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
# The path where server.jar resides
SERVER_PATH='/opt/minecraft/Paper'
# The nickname of the owner of the bot (optional)
OWNER_NICK='test'
# The status check frequency (optional)
STATUS_CHECK_FREQUENCY='5'
# The status check amount (optional)
STATUS_CHECK_NUMBER='10'
# The tmux command used to open the minecraft server
TMUX_COMMAND='tmux new-session -d -s 'java_server' /usr/bin/java -Xmx5G -Xms5G -jar server.jar nogui'
```

Let's give special attention to the last variable `TMUX_COMMMAND`. This command generates a [tmux](https://www.hamvocke.com/blog/a-quick-and-easy-guide-to-tmux/) session to monitor the console of the Java server. Once the server starts, it can be easily accessed using `tmux attach`.

An example command for starting a minecraft server would look something like this:

```shell
tmux new-session -d -s 'java_server' /usr/bin/java -Xmx3G -Xms3G -jar server.jar nogui"
```

Where the amount of RAM used is 3G

- Once the `.env` file is created, we are basically done and we can start the server using the below command. If successful, we should see no errors - if there is an `ImproperlyConfigured` exception it means that some of the initial setup failed (check the description of the error for more info!).

## Additional information

Modifications of the bot are allowed, just be sure to read the `interactions.py` docs over [here](https://discord-interactions.readthedocs.io/en/latest/quickstart.html). 

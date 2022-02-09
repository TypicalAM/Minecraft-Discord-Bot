"""This module runs a discord bot for a local minecraft server"""

import logging
from discord.ext.commands import Bot
from utils import OWNER_NAME, TOKEN, status_check, players_check, start_server, \
        close_server, inject_command, run_post_start

fh = logging.StreamHandler()
fh_formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
fh.setFormatter(fh_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
logger.addHandler(fh)

bot = Bot(command_prefix='mc ')

@bot.event
async def on_ready():
    """Function ran when the bot logs in"""
    logger.info('%s logged in!', bot.user)

@bot.event
async def on_message(message):
    """Function ran on every message"""
    if message.author == bot.user:
        return

    await bot.process_commands(message)

@bot.command()
async def status(ctx) -> None:
    """Check the status of the server"""

    data = await status_check()
    if not data:
        await ctx.send('The server is closed...')
        return

    players = await players_check()
    if not players:
        await ctx.send('The server is online, but there are no players')
        return
    await ctx.send(f'The server is online, players:\n{", ".join(str(x) for x in players)}')

@bot.command()
async def start(ctx) -> None:
    """Start the server"""

    data = await status_check()
    if data:
        await ctx.send('The server is already online, no need to start')
        return
    msg = await ctx.send('Starting...')

    started = await start_server()
    if not started:
        await msg.edit(content='Starting failed')
        return
    await msg.edit(content='Running post-start operations')

    post_start_status = await run_post_start()
    if not post_start_status:
        await msg.edit(content="The server hasn't started yet")
        return
    await msg.edit(content='The server is opened')

@bot.command()
async def stop(ctx) -> None:
    """Try to stop the server via rcon"""
    data = await status_check()
    if not data:
        await ctx.send('The server is already closed...')
        return

    players = await players_check()
    if players:
        await ctx.send("I can't close the server, there are people on it")
        return

    msg = await ctx.send('Closing the server...')
    closed_status = await close_server()
    if not closed_status:
        await msg.edit(content='Closing failed for some reason, maybe already closed?')
        return

    await msg.edit(content='Closed successfully')

@bot.command()
async def inject(ctx, *args) -> None:
    """Inject a command into the server's console via rcon"""

    if str(ctx.author) != OWNER_NAME:
        logger.warning('Injection: attempt by %s', ctx.author)
        await ctx.send('You do not have permission to inject commands')
        return

    data = await status_check()
    if not data:
        await ctx.send('The server is closed...')
        return

    inject_output = await inject_command(args)
    if not inject_output:
        await ctx.send('Command not injected, check logs')
        return

    await ctx.send(f'Command injected, output:\n{inject_output}')

bot.run(TOKEN)

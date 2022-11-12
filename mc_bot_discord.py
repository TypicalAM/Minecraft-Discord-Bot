"""The main entrypoint for the minecraft discord bot"""

import interactions
import utils
import settings

bot = interactions.Client(token=settings.TOKEN)

@bot.command()
async def status(ctx: interactions.CommandContext) -> None:
    """Check the status of the server"""

    is_open = await utils.status_check()
    if not is_open:
        await ctx.send('The server is closed...')
        return

    players = await utils.players_check()
    if players is None:
        await ctx.send("The server is online, but it doesn't respond")
        return
    if not players:
        await ctx.send('The server is online, but there are no players')
        return
    await ctx.send(f'The server is online, players:\n{", ".join(str(x) for x in players)}')

@bot.command()
async def start(ctx: interactions.CommandContext) -> None:
    """Start the server"""

    is_open = await utils.status_check()
    if is_open:
        await ctx.send('The server is already online, no need to start')
        return
    msg = await ctx.send('Starting...')

    started = await utils.start_server()
    if not started:
        await msg.edit(content='Starting failed')
        return
    await msg.edit(content='Running post-start operations')

    post_start_status = await utils.run_post_start()
    if not post_start_status:
        await msg.edit(content="The server hasn't started yet")
        return
    await msg.edit(content='The server is opened')

@bot.command()
async def stop(ctx: interactions.CommandContext) -> None:
    """Try to stop the server via rcon"""
    is_open = await utils.status_check()
    if not is_open:
        await ctx.send('The server is already closed...')
        return

    players = await utils.players_check()
    if players:
        await ctx.send("I can't close the server, there are people on it")
        return

    msg = await ctx.send('Closing the server...')
    closed_status = await utils.close_server()
    if not closed_status:
        await msg.edit(content='Closing failed for some reason, maybe we are already closed?')
        return

    await msg.edit(content='Closed successfully')

@bot.command()
@interactions.option(description="the command that you want to inject")
async def inject(ctx: interactions.CommandContext, command: str) -> None:
    """Inject a command into the server's console via rcon"""

    if str(ctx.author) != settings.OWNER_NICK:
        await ctx.send('You do not have permission to inject commands')
        return

    is_open = await utils.status_check()
    if not is_open:
        await ctx.send('The server is closed...')
        return

    inject_output = await utils.inject_command(command)
    if inject_output is None:
        await ctx.send('Command not injected, check logs')
        return

    if not inject_output:
        await ctx.send('Command was injected, but returned no output')
        return

    await ctx.send(f'Command injected, output:\n{inject_output}')

@bot.command()
@interactions.option(description="the player that you want to strike")
async def lightning(ctx: interactions.CommandContext, player_name: str):
    """Strike a player with mightly lightning"""

    if len(player_name.split()) > 1:
        await ctx.send('More than one player specified?')
        return

    is_open = await utils.status_check()
    if not is_open:
        await ctx.send('The server is closed...')
        return

    lightning_args = f'execute at @p[name={player_name}] run summon minecraft:lightning_bolt'
    inject_output = await utils.inject_command(lightning_args)
    if not inject_output:
        await ctx.send('Command not injected, check logs')
        return

    await ctx.send(f'Command injected, output:\n{inject_output}')

bot.start()

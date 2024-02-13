"""The main entrypoint for the minecraft discord bot"""

from interactions import (
    Client,
    Intents,
    OptionType,
    SlashContext,
    listen,
    slash_command,
    slash_option,
)

import settings
import utils

bot = Client(intents=Intents.DEFAULT, token=settings.TOKEN)


@listen()
async def on_ready() -> None:
    """Print a message when the bot is ready"""
    print(f"Logged in as {bot.user}")


@slash_command(name="status", description="Check the status of the server")
async def status(ctx: SlashContext) -> None:
    """Check the status of the server"""
    await ctx.defer()

    is_open = await utils.status_check()
    if not is_open:
        await ctx.send("The server is closed...")
        return

    players = await utils.players_check()
    if players is None:
        await ctx.send("The server is online, but it doesn't respond")
        return
    if not players:
        await ctx.send("The server is online, but there are no players")
        return
    await ctx.send(
        f'The server is online, players:\n{", ".join(str(x) for x in players)}'
    )


@slash_command(name="start", description="Start the server")
async def start(ctx: SlashContext) -> None:
    """Start the server"""
    await ctx.defer()

    is_open = await utils.status_check()
    if is_open:
        await ctx.send("The server is already online, no need to start")
        return
    msg = await ctx.send("Starting...")

    started = await utils.start_server()
    if not started:
        await msg.edit(content="Starting failed")
        return
    await msg.edit(content="Running post-start operations")

    try:
        post_start_status = await utils.run_post_start()
        if not post_start_status:
            await msg.edit(content="The server hasn't started yet")
            return
        await msg.edit(content="The server is opened")
    except:
        await msg.edit(content="Still waiting on the server, it might be starting up very slowly")


@slash_command(name="stop", description="Stop the server")
async def stop(ctx: SlashContext) -> None:
    """Try to stop the server via rcon"""
    await ctx.defer()

    is_open = await utils.status_check()
    if not is_open:
        await ctx.send("The server is already closed...")
        return

    players = await utils.players_check()
    if players:
        await ctx.send("I can't close the server, there are people on it")
        return

    msg = await ctx.send("Closing the server...")
    closed_status = await utils.close_server()
    if not closed_status:
        await msg.edit(
            content="Closing failed for some reason, maybe we are already closed?"
        )
        return

    await msg.edit(content="Closed successfully")


@slash_command(
    name="inject", description="Inject a command into the server's console via rcon"
)
@slash_option(
    name="command_to_inject",
    description="The command to inject",
    required=True,
    opt_type=OptionType.STRING,
)
async def inject(ctx: SlashContext, command_to_inject: str) -> None:
    """Inject a command into the server's console via rcon"""
    await ctx.defer()

    if str(ctx.author) != settings.OWNER_NICK:
        await ctx.send("You do not have permission to inject commands")
        return

    is_open = await utils.status_check()
    if not is_open:
        await ctx.send("The server is closed...")
        return

    inject_output = await utils.inject_command(command_to_inject)
    if inject_output is None:
        await ctx.send("Command not injected, check logs")
        return

    if not inject_output:
        await ctx.send("Command was injected, but returned no output")
        return

    await ctx.send(f"Command injected, output:\n{inject_output}")


@slash_command(name="lightning", description="Strike a player with mightly lightning")
@slash_option(
    name="player_name",
    description="The player to strike",
    required=True,
    opt_type=OptionType.STRING,
)
async def lightning(ctx: SlashContext, player_name: str):
    """Strike a player with mightly lightning"""

    if len(player_name.split()) > 1:
        await ctx.send("More than one player specified?")
        return

    is_open = await utils.status_check()
    if not is_open:
        await ctx.send("The server is closed...")
        return

    lightning_args = (
        f"execute at @p[name={player_name}] run summon minecraft:lightning_bolt"
    )
    inject_output = await utils.inject_command(lightning_args)
    if not inject_output:
        await ctx.send("Command not injected, check logs")
        return

    await ctx.send(f"Command injected, output:\n{inject_output}")


bot.start(settings.TOKEN)

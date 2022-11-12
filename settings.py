"""Settings for the minecraft discord bot"""

import os

class ImproperlyConfigured(Exception):
    """Raise this error if the constants are not what they should be"""
    pass

# Try to import the dotenv module
try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:
    pass
else:
    if not load_dotenv(find_dotenv('.env')):
        raise ImproperlyConfigured("Not a single environment variable has been set")

# Load the necessary env variables
TOKEN = os.getenv("DISCORD_TOKEN", default="example-token")
RCON_PASS = os.getenv("RCON_PASS", default="example-pass")
SERVER_PATH = os.getenv("SERVER_PATH", default="example-path")
TMUX_COMMAND = os.getenv("TMUX_COMMAND", default="example-tmux-command")

# Load the optional env variables
OWNER_NICK = os.getenv("OWNER_NICK")
STATUS_CHECK_FREQUENCY = int(os.getenv("STATUS_CHECK_FREQUENCY", default=5))
STATUS_CHECK_NUMBER = int(os.getenv("STATUS_CHECK_NUMBER", default=10))

# Check the required settings are set
if any(setting.startswith("example") for setting in [TOKEN,RCON_PASS,SERVER_PATH,TMUX_COMMAND]):
    raise ImproperlyConfigured("Some of the required settings are not set")

# Set the rcon connection arguments
RCON_ARGS = {
        "host": "127.0.0.1",
        "port": 25575,
        "passwd": RCON_PASS
}

# Try to import mcstatus and rcon
try:
    import mcstatus
    import rcon
except ImportError:
    raise ImproperlyConfigured("Some of the needed modules are not present: rcon or mcstatus")

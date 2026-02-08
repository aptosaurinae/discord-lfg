"""Dungeon Buddy discord bot."""

try:
    import tomllib
except ModuleNotFoundError:
    import pip._vendor.tomli as tomllib

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord import app_commands

from discord_lfg.commands import CommandArgument, build_lfg_command, command_argument_from_config
from discord_lfg.lfg import lfgdebug
from discord_lfg.utils import create_roles_from_config

# --- Config setup

parser = argparse.ArgumentParser(description="Configuration for discord bot")
parser.add_argument("token_file", type=str, help="Discord Token")
parser.add_argument("config", type=str, help="configuration file")

args = vars(parser.parse_args())
with open(args["token_file"], "rb") as token_file:
    token_data = tomllib.load(token_file)
with open(args["config"], "rb") as config_file:
    CONFIG_DATA = tomllib.load(config_file)


def _validate_config(CONFIG_DATA: dict):
    config_errors = []
    if CONFIG_DATA.get("role") is None:
        config_errors.append("You must define roles in the config, see readme for details")
    for role_data in CONFIG_DATA.get("role", {}).values():
        if (
            role_data.get("count") is None
            or role_data.get("emoji") is None
            or role_data.get("identifier") is None
        ):
            config_errors.append(
                "Role input is missing data, needs ['count', 'emoji', 'identifier']"
            )
    if len(config_errors) > 0:
        conf_errors = "".join([f"{err}\n" for err in config_errors])
        raise ValueError(f"Config is missing required arguments: \n{conf_errors}")


_validate_config(CONFIG_DATA)

TOKEN = token_data["discord"]["token"]
GUILD_ID = discord.Object(CONFIG_DATA["guild_id"])
DEBUG = CONFIG_DATA.get("debug", 0)
LOG_FOLDER = Path(CONFIG_DATA.get("log_folder", ""))
ROLES = create_roles_from_config(CONFIG_DATA.get("role", {}))
HELP_MESSAGE = CONFIG_DATA.get("messages", {"help": "missing help definition"}).get("help")

ACTIVITY_ARG = command_argument_from_config(CONFIG_DATA.get("activity", {}), "activity")
TIMING_AIM_ARG = command_argument_from_config(CONFIG_DATA.get("option", {}).get("1", {}), "option1")
CREATOR_ROLE_ARG = CommandArgument(
    "creator_role", str, True, "The role you are filling for this group.", list(ROLES.keys())
)
REQUIRED_SPOTS_ARG = CommandArgument(
    "required_spots",
    str,
    True,
    f"valid identifiers: {[role.identifier for role in ROLES.values()]}",
    None,
)
DIFFICULTY_ARG = CommandArgument(
    "difficulty", int, True, "The difficulty level of the key.", None, True
)


dt_now = datetime.now(timezone.utc)
datetime_str = (
    f"{dt_now.year}-{dt_now.month}-{dt_now.day}_{dt_now.hour}-{dt_now.minute}-{dt_now.second}"
)
if LOG_FOLDER != "" and LOG_FOLDER.exists():
    log_file_path = LOG_FOLDER / f"{datetime_str}_dungeon_buddy.log"
    logging.basicConfig(
        level=logging.DEBUG if DEBUG == 1 else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_file_path, encoding="utf-8")],
    )

# --- Bot setup


# see the example app_commands/basic on the discord-py GitHub repo
class BotClient(discord.Client):
    """Main client for Discord."""

    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self, *, intents: discord.Intents):
        """Init."""
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)


intents = discord.Intents.default()
client = BotClient(intents=intents)


@client.event
async def on_ready():
    """Startup tasks."""
    global CONFIG_DATA
    CONFIG_DATA["guild_roles"] = {guild.id: guild.roles for guild in client.guilds}[
        CONFIG_DATA["guild_id"]
    ]
    lfg_fixed_args = {"roles": ROLES, "config": CONFIG_DATA}
    lfg_command = build_lfg_command(
        [ACTIVITY_ARG, DIFFICULTY_ARG, TIMING_AIM_ARG, CREATOR_ROLE_ARG, REQUIRED_SPOTS_ARG],
        lfg_fixed_args,
    )
    client.tree.add_command(lfg_command, guild=GUILD_ID)

    await client.tree.sync(guild=GUILD_ID)

    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")
    print("Discord-LFG started")
    if LOG_FOLDER != "" and LOG_FOLDER.exists():
        print(f"logging to: {LOG_FOLDER}")


# -- Help


@client.tree.command(guild=GUILD_ID)
async def lfghelp(interaction: discord.Interaction):
    """Help with using Group Builder."""
    response = HELP_MESSAGE
    await interaction.response.send_message(response, ephemeral=True)


# -- LFG

if CONFIG_DATA.get("debug") is not None:

    @client.tree.command(guild=GUILD_ID, name="lfgdebug")
    async def lfgdebug_command(interaction: discord.Interaction):
        """Some quick-fire group listings for debug purposes (including what should be invalid setups)."""
        for num in range(6):
            await lfgdebug(interaction=interaction, debug_type=num, config=CONFIG_DATA)

# -- Stats


@client.tree.command(guild=GUILD_ID)
async def lfghistory(interaction: discord.Interaction):
    """Review your last 10 group signups."""
    response = "temp"
    await interaction.response.send_message(response, ephemeral=True)


@client.tree.command(guild=GUILD_ID)
async def lfgstats(interaction: discord.Interaction):
    """Review recent and all-time numbers of group listings."""
    response = "temp"
    await interaction.response.send_message(response, ephemeral=True)


@client.tree.command(guild=GUILD_ID)
async def lfguserhistory(interaction: discord.Interaction):
    """Review a specific users group signup history."""
    response = "temp"
    await interaction.response.send_message(response, ephemeral=True)


# --- Run bot


client.run(token=TOKEN)

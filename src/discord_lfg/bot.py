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

from discord_lfg.autocompletion import (
    difficulty_autocomplete,
    dungeon_autocomplete,
    dungeon_short_autocomplete,
    role_autocomplete,
    time_type_autocomplete,
)
from discord_lfg.commands.help import help_response
from discord_lfg.commands.lfg import lfg, lfgdebug, lfgquick
from discord_lfg.roles import create_roles_from_config

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
    if CONFIG_DATA.get("expansion") is None:
        config_errors.append(
            "You must define an expansion in the config using the 'expansion' argument"
        )
    if CONFIG_DATA.get("season") is None:
        config_errors.append("You must define a season in the config using the 'season' argument")
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
CURRENT_EXPANSION = str(CONFIG_DATA.get("expansion"))
CURRENT_SEASON = str(CONFIG_DATA.get("season"))
DEBUG = CONFIG_DATA.get("debug", 0)
LOG_FOLDER = Path(CONFIG_DATA.get("log_folder", ""))
ROLES = create_roles_from_config(CONFIG_DATA.get("role", {}))

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

    async def setup_hook(self):
        """Update commands on guild."""
        await self.tree.sync(guild=GUILD_ID)


intents = discord.Intents.default()
client = BotClient(intents=intents)


@client.event
async def on_ready():
    """Startup tasks."""
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")
    print("Discord-LFG started")
    if LOG_FOLDER != "" and LOG_FOLDER.exists():
        print(f"logging to: {LOG_FOLDER}")
    global CONFIG_DATA
    CONFIG_DATA["guild_roles"] = {guild.id: guild.roles for guild in client.guilds}[
        CONFIG_DATA["guild_id"]
    ]


# -- Help


@client.tree.command(guild=GUILD_ID)
async def lfghelp(interaction: discord.Interaction):
    """Help with using Group Builder."""
    await help_response(interaction)


# -- LFG


@client.tree.command(guild=GUILD_ID, name="lfg")
@app_commands.describe(
    dungeon="The dungeon you are listing a key for.",
    listed_as="The in-game name. Leave blank to automatically generate a name for you (recommended)",
    creator_notes="Extra notes you want to make players signing up aware of.",
)
@app_commands.autocomplete(dungeon=dungeon_autocomplete(CURRENT_EXPANSION, CURRENT_SEASON))
async def lfg_command(
    interaction: discord.Interaction, dungeon: str, listed_as: str = "", creator_notes: str = ""
):
    """Generates a Group Builder listing using a guided wizard."""
    await lfg(
        interaction=interaction,
        dungeon=dungeon,
        listed_as=listed_as,
        creator_notes=creator_notes,
        roles=ROLES,
        config=CONFIG_DATA,
    )


@client.tree.command(guild=GUILD_ID, name="lfgquick")
@app_commands.describe(
    dungeon="The short name of the dungeon you are listing a key for.",
    difficulty="The difficulty of the dungeon.",
    time_type="The timing type you are aiming for e.g. 'toa' for 'Time or Abandon'.",
    your_role="The role you are filling for this group.",
    required_spots="'t' for tank, 'h' for healer, 'd' for dps. e.g. 'thdd' for all spots if you're dps",
    listed_as="The in-game name. Leave blank to automatically generate a name for you (recommended)",
    creator_notes="Extra notes you want to make players signing up aware of.",
)
@app_commands.autocomplete(
    dungeon=dungeon_short_autocomplete(CURRENT_EXPANSION, CURRENT_SEASON),
    time_type=time_type_autocomplete(),
    your_role=role_autocomplete(ROLES),
    difficulty=difficulty_autocomplete,
)
async def lfgstring_command(
    interaction: discord.Interaction,
    dungeon: str,
    difficulty: int,
    time_type: str,
    your_role: str,
    required_spots: str,
    listed_as: str = "",
    creator_notes: str = "",
):
    """Generates a Dungeon Buddy listing using a quick text-based input."""
    await lfgquick(
        interaction=interaction,
        dungeon=dungeon,
        difficulty=difficulty,
        time_type=time_type,
        creator_role=your_role,
        listed_as=listed_as,
        creator_notes=creator_notes,
        required_spots=required_spots,
        roles=ROLES,
        config=CONFIG_DATA,
    )


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

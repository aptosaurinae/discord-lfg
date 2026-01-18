"""Dungeon Buddy discord bot."""

try:
    import tomllib
except ModuleNotFoundError:
    import pip._vendor.tomli as tomllib

import argparse

import discord
from discord import app_commands

from db_py.autocompletion import (
    difficulty_autocomplete,
    dungeon_autocomplete,
    dungeon_short_autocomplete,
    role_autocomplete,
    time_type_autocomplete,
)
from db_py.commands.help import help_response
from db_py.commands.lfg import lfg, lfgdebug, lfgquick

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
        config_errors.append("You must define an expansion in the config using the 'expansion' argument")
    if CONFIG_DATA.get("season") is None:
        config_errors.append("You must define a season in the config using the 'season' argument")
    if len(config_errors) > 0:
        conf_errors = "".join([f'{err}\n' for err in config_errors])
        raise ValueError(f"Config is missing required arguments: \n{conf_errors}")


_validate_config(CONFIG_DATA)

TOKEN = token_data["discord"]["token"]
GUILD_ID = discord.Object(CONFIG_DATA["guild_id"])
CURRENT_EXPANSION = str(CONFIG_DATA.get("expansion"))
CURRENT_SEASON = str(CONFIG_DATA.get("season"))


# see the example app_commands/basic on the discord-py GitHub repo
class DungeonBuddyClient(discord.Client):
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
client = DungeonBuddyClient(intents=intents)


@client.event
async def on_ready():
    """Startup tasks."""
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    print('Dungeon Buddy started')

# -- Help


@client.tree.command(guild=GUILD_ID)
async def lfghelp(interaction: discord.Interaction):
    """Help with using Dungeon Buddy."""
    await help_response(interaction)

# -- LFG


@client.tree.command(guild=GUILD_ID, name="lfg")
@app_commands.describe(
    dungeon="The dungeon you are listing a key for.",
    listed_as="The in-game name. Leave blank to automatically generate a name for you (recommended)",
    creator_notes="Extra notes you want to make players signing up aware of."
)
@app_commands.autocomplete(dungeon=dungeon_autocomplete(CURRENT_EXPANSION, CURRENT_SEASON))
async def lfg_command(
    interaction: discord.Interaction,
    dungeon: str,
    listed_as: str = "",
    creator_notes: str = "",
):
    """Generates a Dungeon Buddy listing using a guided wizard."""
    await lfg(
        interaction=interaction,
        dungeon=dungeon,
        listed_as=listed_as,
        creator_notes=creator_notes,
        config=CONFIG_DATA,
    )


@client.tree.command(guild=GUILD_ID, name="lfg2")
@app_commands.describe(
    dungeon="The short name of the dungeon you are listing a key for.",
    difficulty="The difficulty of the dungeon.",
    time_type="The timing type you are aiming for e.g. 'toa' for 'Time or Abandon'.",
    your_role="The role you are filling for this group.",
    filled_spots="A string noting which spots you already have filled. 't' for tank, 'h' for healer, 'd' for dps. e.g. 'tdd' if you already have a tank and two dps as well as your role.",
    listed_as="The in-game name. Leave blank to automatically generate a name for you (recommended)",
    creator_notes="Extra notes you want to make players signing up aware of."
)
@app_commands.autocomplete(
    dungeon=dungeon_short_autocomplete(CURRENT_EXPANSION, CURRENT_SEASON),
    time_type=time_type_autocomplete(),
    your_role=role_autocomplete(),
    difficulty=difficulty_autocomplete,
)
async def lfgstring_command(
    interaction: discord.Interaction,
    dungeon: str,
    difficulty: int,
    time_type: str,
    your_role: str,
    filled_spots: str,
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
        filled_spots=filled_spots,
        config=CONFIG_DATA,
    )


if CONFIG_DATA.get("debug") is not None:
    @client.tree.command(guild=GUILD_ID, name="lfgdebug")
    async def lfgdebug_command(
        interaction: discord.Interaction,
    ):
        """Generates a Dungeon Buddy listing using a quick text-based input."""
        await lfgdebug(
            interaction=interaction,
            config=CONFIG_DATA,
        )

# -- Stats


@client.tree.command(guild=GUILD_ID)
async def lfghistory(interaction: discord.Interaction):
    """Review your last 10 dungeon buddy signups."""
    response = "temp"
    await interaction.response.send_message(response, ephemeral=True)


@client.tree.command(guild=GUILD_ID)
async def lfgstats(interaction: discord.Interaction):
    """Review recent and all-time numbers of dungeon listings."""
    response = "temp"
    await interaction.response.send_message(response, ephemeral=True)


@client.tree.command(guild=GUILD_ID)
async def lfguserhistory(interaction: discord.Interaction):
    """Review a specific users dungeon buddy signup history."""
    response = "temp"
    await interaction.response.send_message(response, ephemeral=True)

# ---


client.run(token=TOKEN)

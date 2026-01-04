"""Dungeon Buddy discord bot."""

try:
    import tomllib
except ModuleNotFoundError:
    import pip._vendor.tomli as tomllib

import argparse

import discord
from discord import app_commands

from db_py.resources import load_dungeons

parser = argparse.ArgumentParser(description="Configuration for discord bot")
parser.add_argument("token_file", type=str, help="Discord Token")
parser.add_argument("config", type=str, help="configuration file")

args = vars(parser.parse_args())
with open(args["token_file"], "rb") as token_file:
    token_data = tomllib.load(token_file)
with open(args["config"], "rb") as config_file:
    config_data = tomllib.load(config_file)

TOKEN = token_data["discord"]["token"]
GUILD_ID = discord.Object(config_data["guild_id"])
CURRENT_EXPANSION = config_data["expansion"]
CURRENT_SEASON = config_data["season"]

CHANNEL_WHITELIST = [
    "bot-control"
]


# TODO: Move this to an autocompletion file?
async def dungeon_autocomplete(interaction: discord.Interaction, current: str):
    """Autocompletion system for dungeon strings."""
    dungeons = load_dungeons(CURRENT_EXPANSION, CURRENT_SEASON)
    return [
        app_commands.Choice(name=dungeon, value=dungeon)
        for dungeon in dungeons.values() if current.lower() in dungeon.lower()
    ]


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

# -- Help


@client.tree.command(guild=GUILD_ID)
async def lfghelp(interaction: discord.Interaction):
    """Help with using Dungeon Buddy."""
    response = "help"
    await interaction.response.send_message(response, ephemeral=True)

# -- LFG


@client.tree.command(guild=GUILD_ID)
@app_commands.describe(
    dungeon="The dungeon you are listing a key for.",
    listed_as="The in-game name. Leave blank to automatically generate a name for you (recommended)",
    creator_notes="Extra notes you want to make players signing up aware of."
)
@app_commands.autocomplete(dungeon=dungeon_autocomplete)
async def lfg(
    interaction: discord.Interaction,
    dungeon: str,
    listed_as: str = "",
    creator_notes: str = "",
):
    """Generates a Dungeon Buddy listing using a guided wizard."""
    response = "temp"
    await interaction.response.send_message(response, ephemeral=True)


@client.tree.command(guild=GUILD_ID)
async def lfgquick(interaction: discord.Interaction):
    """Generates a Dungeon Buddy listing using a quick text-based input."""
    response = "temp"
    await interaction.response.send_message(response, ephemeral=True)

# -- Utils


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

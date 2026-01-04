"""Dungeon Buddy discord bot"""
try:
    import tomllib
except ModuleNotFoundError:
    import pip._vendor.tomli as tomllib
import argparse
import discord
from discord import app_commands

parser = argparse.ArgumentParser(description="Configuration for discord bot")
parser.add_argument("token_file", type=str, help="Discord Token")
parser.add_argument("config", type=str, help="configuration file")

args = vars(parser.parse_args())
with open(args["token_file"], "rb") as token_file:
    token_data = tomllib.load(token_file)
with open(args["config"], "rb") as config_file:
    config_data = tomllib.load(config_file)

TOKEN = token_data["discord"]["token"]
GUILD_ID = config_data["guild_id"]
CURRENT_EXPANSION = config_data["expansion"]
CURRENT_SEASON = config_data["season"]

CHANNEL_WHITELIST = [
    "bot-control"
]

EMOJIS = {
    "tank": ":tankrole:",
    "healer": ":healerrole:",
    "dps": ":dpsrole:"
}

class DungeonBuddyClient(discord.Client):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=GUILD_ID)
        await self.tree.sync(guild=GUILD_ID)


intents = discord.Intents.default()
client = DungeonBuddyClient(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.tree.command()
async def lfghelp(interaction: discord.Interaction):
    response = "temp"
    await interaction.response.send_message(response)

@client.tree.command()
async def lfghelpdm(interaction: discord.Interaction):
    response = "temp"
    await interaction.user.create_dm()
    await interaction.user.dm_channel.send(response)

@client.tree.command()
async def lfg(interaction: discord.Interaction):
    response = "temp"
    await interaction.response.send_message(response)

@client.tree.command()
async def lfgquick(interaction: discord.Interaction):
    response = "temp"
    await interaction.response.send_message(response)

@client.tree.command()
async def lfghistory(interaction: discord.Interaction):
    response = "temp"
    await interaction.response.send_message(response)

@client.tree.command()
async def lfgstats(interaction: discord.Interaction):
    response = "temp"
    await interaction.response.send_message(response)

@client.tree.command()
async def lfguserhistory(interaction: discord.Interaction):
    response = "temp"
    await interaction.response.send_message(response)

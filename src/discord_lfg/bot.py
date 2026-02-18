"""Discord looking-for-group bot."""

from pathlib import Path

import discord
from discord import app_commands

from discord_lfg.commands import build_command
from discord_lfg.input_config import CommandConfig, parse_inputs
from discord_lfg.lfg import lfg, lfgdebug
from discord_lfg.stats import get_data

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


def _register_on_ready(
    client: BotClient,
    guild_id_obj: discord.Object,
    guild_id_int: int,
    log_folder: Path | None,
    stats_folder: Path | None,
    commands_configs: list[CommandConfig],
    debug: bool = False,
):
    @client.event
    async def on_ready():
        """Startup tasks."""
        guild_roles = {guild.id: guild.roles for guild in client.guilds}[guild_id_int]
        if stats_folder is not None and stats_folder.exists():
            get_data(stats_folder)
        else:
            get_data(None)

        for command_config in commands_configs:
            command_config.guild_roles = guild_roles
            command = build_command(
                command_config.args,
                command_config,
                command_config.name,
                command_config.description,
                lfg,
            )
            client.tree.add_command(command, guild=guild_id_obj)

        if debug:
            _register_lfgdebug(client, guild_id_obj)

        await client.tree.sync(guild=guild_id_obj)

        print(f"Logged in as {client.user} (ID: {client.user.id})")
        print("------")
        print("Discord-LFG started")
        if log_folder is not None and log_folder.exists():
            print(f"logging to: {log_folder}")
        if stats_folder is not None and stats_folder.exists():
            print(f"stats outputting to: {stats_folder}")
        else:
            print("stats being captured locally but will not be persistent")


# -- LFG


def _register_lfgdebug(client, guild_id_obj: discord.Object):
    @client.tree.command(guild=guild_id_obj, name="lfgdebug")
    async def lfgdebug_command(interaction: discord.Interaction):
        """Some quick-fire group listings for debug purposes (including what should be invalid setups)."""
        for num in range(6):
            await lfgdebug(interaction=interaction, debug_type=num)


# -- Stats


def _register_lfgstats(client, guild_id_obj: discord.Object):
    @client.tree.command(guild=guild_id_obj)
    async def lfghistory(interaction: discord.Interaction):
        """Review your last 10 group signups."""
        response = "temp"
        await interaction.response.send_message(response, ephemeral=True)

    @client.tree.command(guild=guild_id_obj)
    async def lfgstats(interaction: discord.Interaction):
        """Review recent and all-time numbers of group listings."""
        response = "temp"
        await interaction.response.send_message(response, ephemeral=True)

    @client.tree.command(guild=guild_id_obj)
    async def lfguserhistory(interaction: discord.Interaction):
        """Review a specific users group signup history."""
        response = "temp"
        await interaction.response.send_message(response, ephemeral=True)


if __name__ == "__main__":
    token, config, commands = parse_inputs()

    intents = discord.Intents.default()
    client = BotClient(intents=intents)
    _register_on_ready(
        client,
        config.guild_id_discord,
        config.guild_id_int,
        config.log_folder,
        config.stats_folder,
        commands,
        config.debug,
    )
    # _register_lfgstats(client, guild_id_obj)
    client.run(token=token)

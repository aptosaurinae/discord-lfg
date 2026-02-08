"""Discord looking-for-group bot."""

from pathlib import Path

import discord
from discord import app_commands

from discord_lfg.commands import build_lfg_command
from discord_lfg.input_config import parse_config
from discord_lfg.lfg import lfgdebug

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
    log_folder: Path,
    commands_and_args: dict[str, dict],
):
    @client.event
    async def on_ready():
        """Startup tasks."""
        guild_roles = {guild.id: guild.roles for guild in client.guilds}[guild_id_int]

        for command_name, command_elements in commands_and_args.items():
            if (roles := command_elements.get("roles")) is not None and (
                config_data := command_elements.get("config")
            ) is not None:
                config_data.guild_roles = guild_roles
                lfg_keyword_args = {"roles": roles, "config": config_data}
                command_args = command_elements.get("args")
                if isinstance(command_name, str) and isinstance(command_args, list):
                    command = build_lfg_command(command_args, lfg_keyword_args)
                    client.tree.add_command(command, guild=guild_id_obj)
            else:
                raise ValueError(f"{command_name} should not have an empty 'roles' or 'config'")

        _register_lfgdebug(client, guild_id_obj)

        await client.tree.sync(guild=guild_id_obj)

        print(f"Logged in as {client.user} (ID: {client.user.id})")
        print("------")
        print("Discord-LFG started")
        if log_folder != "" and log_folder.exists():
            print(f"logging to: {log_folder}")


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
    token, config, commands = parse_config()

    intents = discord.Intents.default()
    client = BotClient(intents=intents)
    _register_on_ready(
        client, config.guild_id_discord, config.guild_id_int, config.log_folder, commands
    )
    # _register_lfgstats(client, guild_id_obj)
    client.run(token=token)

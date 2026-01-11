"""Contains help functions."""

import discord

from db_py.resources import load_messages


async def help_response(interaction: discord.Interaction):
    """Sends a response detailing how to use Dungeon Buddy."""
    response = load_messages()["help"]
    await interaction.response.send_message(response, ephemeral=True)

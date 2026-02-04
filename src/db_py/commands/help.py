"""Contains help functions."""

import discord

from db_py.resources import load_help_message


async def help_response(interaction: discord.Interaction):
    """Sends a response detailing how to use Group Builder."""
    response = load_help_message()["help"]
    await interaction.response.send_message(response, ephemeral=True)

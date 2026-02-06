"""Contains autocompletion lists for dungeon buddy."""

import discord
from discord import app_commands

from discord_lfg.utils import get_numbers_from_channel_name


def autocomplete_choice(choices: list, command: app_commands.Command, name: str):
    """Creates an autocompletion choice interactable."""

    @command.autocomplete(name)
    async def autocompleter(interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=item, value=item)
            for item in choices
            if current.lower() in item.lower()
        ]

    return autocompleter


def autocomplete_choice_from_channel_numbers(command: app_commands.Command, name: str):
    """Creates an autocompletion choice interactable."""

    @command.autocomplete(name)
    async def autocompleter(interaction: discord.Interaction, current: str):
        if isinstance(interaction.channel.name, str):  # type: ignore
            choices = get_numbers_from_channel_name(interaction.channel.name)  # type: ignore
        if choices is None:
            return [app_commands.Choice(name="Invalid channel for LFG command", value=0)]
        return [
            app_commands.Choice(name=item, value=item)
            for item in choices
            if current.lower() in item.lower()
        ]

    return autocompleter

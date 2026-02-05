"""Contains autocompletion lists for dungeon buddy."""

import discord
from discord import app_commands

from discord_lfg.roles import RoleDefinition
from discord_lfg.utils import get_difficulty_start_and_end_from_channel_name


def _autocomplete_choice(choices: list):
    """Creates an autocompletion choice interactable."""

    async def autocompleter(interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=item, value=item)
            for item in choices
            if current.lower() in item.lower()
        ]

    return autocompleter


def dungeon_autocomplete(dungeons: dict[str, str]):
    """Autocompletion system for dungeon strings."""
    return _autocomplete_choice(list(dungeons.values()))


def dungeon_short_autocomplete(dungeons: dict[str, str]):
    """Autocompletion system for short dungeon strings."""
    return _autocomplete_choice(list(dungeons.keys()))


def time_type_autocomplete(time_types: dict[str, str]):
    """Autocompletion system for time types."""
    return _autocomplete_choice(list(time_types.keys()))


def role_autocomplete(roles: dict[str, RoleDefinition]):
    """Autocompletion system for user role."""
    return _autocomplete_choice(list(roles))


async def difficulty_autocomplete(interaction: discord.Interaction, current: str):
    """Autocompletion system for getting difficulty numbers from a channel name."""
    if isinstance(interaction.channel.name, str):  # type: ignore
        choices = get_difficulty_start_and_end_from_channel_name(interaction.channel.name)  # type: ignore
        if choices is None:
            return [app_commands.Choice(name="Invalid channel for LFG command", value=0)]
    return [
        app_commands.Choice(name=item, value=int(item))
        for item in choices
        if current.lower() in item.lower()
    ]

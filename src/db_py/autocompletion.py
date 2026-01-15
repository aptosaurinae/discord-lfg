"""Contains autocompletion lists for dungeon buddy."""

import discord
from discord import app_commands

from db_py.resources import load_dungeons, load_time_types


def _autocomplete_choice(choices: list):
    """Creates an autocompletion choice interactable."""
    async def autocompleter(interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=item, value=item)
            for item in choices if current.lower() in item.lower()
        ]
    return autocompleter


def dungeon_autocomplete(
    expansion: str,
    season: str
):
    """Autocompletion system for dungeon strings."""
    dungeons = load_dungeons(expansion, season)
    return _autocomplete_choice(list(dungeons.values()))


def dungeon_short_autocomplete(
    expansion: str,
    season: str
):
    """Autocompletion system for short dungeon strings."""
    dungeons = load_dungeons(expansion, season)
    return _autocomplete_choice(list(dungeons.keys()))


def time_type_autocomplete():
    """Autocompletion system for time types."""
    time_types = load_time_types()
    return _autocomplete_choice(list(time_types.keys()))


def difficulty_autocomplete(lower: int, upper: int):
    """Autocompletion system for short dungeon strings."""
    difficulties = list(range(lower, upper + 1))
    return _autocomplete_choice(difficulties)

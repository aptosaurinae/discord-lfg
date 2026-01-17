"""Contains autocompletion lists for dungeon buddy."""

import discord
from discord import app_commands

from db_py.resources import load_dungeons, load_time_types
from db_py.roles import RoleType


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


def role_autocomplete():
    """Autocompletion system for user role."""
    roles = [role.name for role in RoleType]
    return _autocomplete_choice(roles)


def _get_difficulty_start_and_end_from_channel_name(channel_name: str):
    if channel_name == "bot-control":
        return (2, 20)
    if channel_name[:5] != "lfg-m":
        return None
    start_start_idx = channel_name.find("m") + 1
    if channel_name.count("m") == 1:
        start_num = int(channel_name[start_start_idx:])
        end_num = start_num
        return (start_num, end_num)
    elif channel_name.count("m") == 2:
        start_end_idx = channel_name.find("-", start_start_idx)
        end_start_idx = channel_name.find("m", start_end_idx) + 1
        start_num = int(channel_name[start_start_idx:start_end_idx])
        end_num = int(channel_name[end_start_idx:])
        return (start_num, end_num)
    return None


async def difficulty_autocomplete(interaction: discord.Interaction, current: str):
    """Autocompletion system for getting difficulty numbers from a channel name."""
    if isinstance(interaction.channel.name, str):   # type: ignore
        numbers = _get_difficulty_start_and_end_from_channel_name(interaction.channel.name)  # type: ignore
        if numbers is None:
            return [app_commands.Choice(name="Invalid channel for LFG command", value=0)]
        choices = [str(num) for num in range(numbers[0], numbers[1] + 1)]
    return [
        app_commands.Choice(name=item, value=int(item))
        for item in choices if current.lower() in item.lower()
    ]

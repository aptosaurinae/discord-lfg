"""Utilities for Group Builder."""

import logging
import re
from datetime import datetime, timezone

import discord


def extract_numbers(text: str) -> list[int]:
    """Gets any numbers from a string and returns them as a list of integers."""
    return [int(num) for num in re.findall(r"\d+", text)]


def get_numbers_from_channel_name(channel_name: str) -> None | list:
    """Generates a set of numbers from a channel name.

    Assumes that at most there are 2 numbers in the channel name.
    If there are 0 or more than 2, will generate a list from 1-10.
    """
    numbers = extract_numbers(channel_name)
    if len(numbers) == 1:
        return [str(numbers[0])]
    elif len(numbers) == 2:
        return [str(num) for num in range(numbers[0], numbers[1])]
    else:
        return [str(num) for num in range(1, 11)]


def get_guild_role_mention_for_group_role(
    group_role: str, guild_roles: list[discord.Role], channel_name: str
) -> str:
    """Generates an expected role and retrieves this if it matches a real one."""
    logging.debug(f"getting role mentions: {group_role}, {channel_name}")
    if channel_name[:5] != "lfg-m":
        return ""
    channel_parts = channel_name.split("-")
    difficulty_start = channel_parts[1]
    # we need to strip out the extra "m" as roles don't have this
    difficulty_end = f"-{channel_parts[2][1:]}" if len(channel_parts) > 2 else ""
    mention_expected = f"{group_role}-{difficulty_start}{difficulty_end}".lower()
    logging.debug(f"expected: {mention_expected}")
    logging.debug(f"guild_roles mentions: {[role.name for role in guild_roles]}")
    guild_role_tags = {role.name.lower(): role.mention for role in guild_roles}
    if mention_expected in guild_role_tags:
        return guild_role_tags[mention_expected]
    return ""


def datetime_now_utc():
    """Gets the current time using the UTC timezone."""
    return datetime.now(tz=timezone.utc)

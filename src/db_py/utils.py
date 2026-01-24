"""Utilities for Dungeon Buddy."""

import discord

from db_py.roles import RoleType


def get_difficulty_start_and_end_from_channel_name(channel_name: str) -> None | list:
    """Generates a set of difficulty values from a channel name."""
    if channel_name == "bot-control":
        start_num = 2
        end_num = 20
        return [str(num) for num in range(start_num, end_num + 1)]
    if channel_name[:5] != "lfg-m":
        return None
    start_start_idx = channel_name.find("m") + 1
    if channel_name.count("m") == 1:
        start_num = int(channel_name[start_start_idx:])
        end_num = start_num
        return [str(num) for num in range(start_num, end_num + 1)]
    elif channel_name.count("m") == 2:
        start_end_idx = channel_name.find("-", start_start_idx)
        end_start_idx = channel_name.find("m", start_end_idx) + 1
        start_num = int(channel_name[start_start_idx:start_end_idx])
        end_num = int(channel_name[end_start_idx:])
        return [str(num) for num in range(start_num, end_num + 1)]
    return None


def get_guild_role_mention_for_dungeon_role(
    dungeon_role: RoleType,
    guild_roles: list[discord.Role],
    channel_name: str,
) -> str:
    """Generates an expected role and retrieves this if it matches a real one."""
    if channel_name[:5] != "lfg-m":
        return ""
    channel_parts = channel_name.split("-")
    difficulty_start = channel_parts[1]
    if len(channel_parts) > 2:
        # we need to strip out the extra "m" as roles don't have this
        difficulty_end = f"-{channel_parts[2][1:]}"
    mention_expected = f"{dungeon_role.name}-{difficulty_start}{difficulty_end}"
    if mention_expected in [role.mention for role in guild_roles]:
        return mention_expected
    return ""

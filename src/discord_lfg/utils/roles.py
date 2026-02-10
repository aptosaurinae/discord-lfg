"""Create a standardised role."""

import logging
from dataclasses import dataclass

import discord


@dataclass
class RoleDefinition:
    """Defines a role fed in by the config."""

    name: str
    count: int
    emoji: str
    identifier: str


def create_roles_from_config(
    roles: dict[str, dict[str, str]], role_counts: dict[str, int]
) -> dict[str, RoleDefinition]:
    """Creates roles from a config input.

    Args:
        roles: A dictionary which has the following structure:
            {
                name: {
                    emoji: emoji string,
                    identifier: single-character indicator,
                }
            }
        role_counts: a lookup of role name to the count of the number of role spots for a command.

    Returns:
        Dictionary of role name to definition
    """
    return {
        role_name: RoleDefinition(
            role_name, int(role_counts[role_name]), str(role["emoji"]), str(role["identifier"])
        )
        for role_name, role in roles.items()
        if role_name in role_counts
    }


def get_guild_role_mention_for_group_role(
    group_role: str,
    guild_roles: list[discord.Role],
    channel_name: str,
    channel_role_mentions: dict[str, str],
) -> str:
    """Generates an expected role and retrieves this if it matches a real one."""
    logging.debug(f"getting role mentions: {group_role}, {channel_name}, {channel_role_mentions}")
    if channel_name not in channel_role_mentions:
        logging.debug("did not find matching channel_name in channel_role_mentions")
        return ""
    mention_expected = f"{group_role}{channel_role_mentions[channel_name]}".lower()
    logging.debug(f"expected: {mention_expected}")
    logging.debug(f"guild_roles mentions: {[role.name for role in guild_roles]}")
    guild_role_tags = {role.name.lower(): role.mention for role in guild_roles}
    if mention_expected in guild_role_tags:
        logging.debug(f"found matching tag: {mention_expected}")
        return guild_role_tags[mention_expected]
    return ""

"""Contains role enumerations."""

from dataclasses import dataclass
from enum import Enum

import discord


class RoleType(Enum):
    """Enumeration for role types."""
    tank = 1
    healer = 2
    dps = 3


class RoleSpecific(Enum):
    """Enumeration for the role a particular user has been assigned."""
    none = 0
    tank = 1
    healer = 2
    dps1 = 3
    dps2 = 4
    dps3 = 5


@dataclass
class Role:
    """Container for a particular role type."""
    name: RoleType
    userids: list[int]
    display_names: list[str]
    assigned: list[bool]
    button_style: discord.ButtonStyle
    disabled: bool
    emoji: str

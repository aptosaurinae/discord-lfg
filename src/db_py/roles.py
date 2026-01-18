"""Contains role enumerations."""

from dataclasses import dataclass
from enum import Enum

import discord


class RoleType(Enum):
    """Enumeration for role types."""
    tank = 1
    healer = 2
    dps = 3


@dataclass
class Role:
    """Container for a particular role type."""
    name: str
    userids: list[int]
    display_names: list[str]
    assigned: list[bool]
    button_style: discord.ButtonStyle
    disabled: bool
    emoji: str

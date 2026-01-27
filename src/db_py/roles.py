"""Contains role enumerations."""

from enum import Enum


class RoleType(Enum):
    """Enumeration for role types."""
    tank = 1
    healer = 2
    dps = 3

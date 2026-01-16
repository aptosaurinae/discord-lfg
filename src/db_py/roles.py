"""Contains role enumerations."""

from enum import Enum


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

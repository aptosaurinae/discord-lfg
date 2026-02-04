"""Create a standardised role."""

from dataclasses import dataclass


@dataclass
class RoleDefinition:
    """Defines a role fed in by the config."""

    name: str
    count: int
    emoji: str
    indicator: str


def create_roles_from_config(roles: dict[str, dict[str, str | int]]) -> dict[str, RoleDefinition]:
    """Creates roles from a config input.

    Args:
        roles: A dictionary which has the following structure:
            {
                name: {
                    emoji: emoji string,
                    count: count integer,
                    indicator: single-character indicator,
                }
            }

    Returns:
        Dictionary of role name to definition
    """
    return {
        role_name: RoleDefinition(
            role_name, int(role["count"]), str(role["emoji"]), str(role["indicator"])
        )
        for role_name, role in roles.items()
    }

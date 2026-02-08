"""Create a standardised role."""

from dataclasses import dataclass


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

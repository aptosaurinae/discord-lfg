"""Controls the LFG system."""

import logging

import discord

from discord_lfg.group_builder import GroupBuilder
from discord_lfg.roles import RoleDefinition


class LFGValidationError(Exception):
    """LFG validation error message handler."""

    def __init__(self, messages):
        """Initialisation."""
        self.messages = messages


def _validate_lfg_inputs(
    difficulty: int,
    creator_role: str,
    filled_spots: dict[str, int],
    roles: dict[str, RoleDefinition],
):
    errors = []
    if difficulty == -1:
        errors.append("You cannot use this command in this channel.")

    max_counts = {role.name: role.count for role in roles.values()}
    max_counts[creator_role] -= 1
    for role, count in filled_spots.items():
        if count > max_counts[role]:
            errors.append(
                f"You cannot assign that many filled spots to that role "
                f"({role}, {count}, max: {max_counts[role]})"
            )
    if sum(filled_spots.values()) == sum(max_counts.values()):
        errors.append("You cannot list a group with no available spots")

    if errors:
        raise LFGValidationError(errors)


async def _lfg(
    interaction: discord.Interaction,
    activity: str,
    difficulty: int,
    creator_role: str,
    time_type: str,
    listed_as: str,
    creator_notes: str,
    filled_spots: dict[str, int],
    roles: dict[str, RoleDefinition],
    config: dict,
):
    logging.debug("".join([str((key, value)) for key, value in locals().items()]))
    try:
        _validate_lfg_inputs(difficulty, creator_role, filled_spots, roles)
    except LFGValidationError as e:
        response = "\n".join(e.messages)
        message_func = (
            interaction.followup.send
            if interaction.response.is_done()
            else interaction.response.send_message
        )
        await message_func(response, ephemeral=True)
        return None

    group_info = {
        "name": activity,
        "listed_as": listed_as,
        "creator_notes": creator_notes,
        "difficulty": difficulty,
        "time_type": time_type,
    }
    logging.debug(group_info)

    instance = GroupBuilder(
        interaction=interaction,
        group_info=group_info,
        config=config,
        creator_role=creator_role,
        roles=roles,
    )
    instance.fill_spots(filled_spots)
    await instance.send_message(interaction)
    await instance.send_passphrase(interaction)


async def lfg(
    interaction: discord.Interaction,
    dungeon: str,
    difficulty: int,
    timing_aim: str,
    creator_role: str,
    required_spots: str,
    listed_as: str,
    creator_notes: str,
    roles: dict[str, RoleDefinition],
    config: dict,
):
    """Creates a LFG listing."""
    role_counts = {role.name: role.count for role in roles.values()}
    required_spots_roles = {
        role_name: required_spots.count(role_def.identifier)
        for role_name, role_def in roles.items()
    }
    logging.debug(f"required_spots: {required_spots}")
    logging.debug(f"required_spots_roles: {required_spots_roles}")
    if required_spots_roles[creator_role] + 1 > role_counts[creator_role]:
        response = "You cannot assign that many filled roles when you are in that role"
        await interaction.response.send_message(response, ephemeral=True)
        return None
    filled_spots = {}
    for role_name, role_count in role_counts.items():
        filled_spots[role_name] = role_count - required_spots_roles[role_name]
    filled_spots[creator_role] -= 1
    logging.debug(f"filled_spots: {filled_spots}")
    return await _lfg(
        interaction=interaction,
        activity=dungeon,
        difficulty=difficulty,
        creator_role=creator_role,
        time_type=timing_aim,
        listed_as=listed_as,
        creator_notes=creator_notes,
        filled_spots=filled_spots,
        roles=roles,
        config=config,
    )


async def lfgdebug(interaction: discord.Interaction, debug_type: int, config: dict):
    """Creates a listing for debugging purposes."""
    roles = {
        "tank": RoleDefinition("tank", 1, "🛡️", "t"),
        "healer": RoleDefinition("healer", 1, "🪄", "h"),
        "dps": RoleDefinition("dps", 3, "⚔️", "t"),
    }
    if debug_type == 0:
        difficulty = 3
        filled_spots = {"tank": 1, "healer": 0, "dps": 2}
        await interaction.channel.send("Difficulty 3 group with 1 tank and 2 dps")  # type: ignore

    if debug_type == 1:
        difficulty = 5
        filled_spots = {"tank": 0, "healer": 0, "dps": 0}
        await interaction.channel.send("Difficulty 5 group with 1 tank, 1 healer, and 2 dps")  # type: ignore

    if debug_type == 2:
        difficulty = 0
        filled_spots = {"tank": 1, "healer": 0, "dps": 2}
        await interaction.channel.send("Difficulty 0 group with 1 tank, and 2 dps")  # type: ignore

    if debug_type == 3:
        difficulty = 3
        filled_spots = {"tank": 1, "healer": 0, "dps": 4}
        await interaction.channel.send("Invalid group (4 dps spots)")  # type: ignore

    if debug_type == 4:
        difficulty = -1
        filled_spots = {"tank": 1, "healer": 0, "dps": 4}
        await interaction.channel.send("Invalid group (4 dps spots and -1 difficulty)")  # type: ignore

    if debug_type == 5:
        difficulty = 4
        filled_spots = {"tank": 1, "healer": 1, "dps": 2}
        await interaction.channel.send("Invalid group (no available spots)")  # type: ignore

    return await _lfg(
        interaction=interaction,
        activity="test",
        difficulty=difficulty,
        creator_role="dps",
        time_type="tbc",
        listed_as=f"Dungeon Debug Test {debug_type}",
        creator_notes="debug creator notes blah blah",
        filled_spots=filled_spots,
        roles=roles,
        config=config,
    )

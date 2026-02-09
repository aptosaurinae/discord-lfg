"""Controls the LFG system."""

import logging

import discord

from discord_lfg.group_builder import GroupBuilder
from discord_lfg.input_config import CommandConfig
from discord_lfg.utils import RoleDefinition


class LFGValidationError(Exception):
    """LFG validation error message handler."""

    def __init__(self, messages):
        """Initialisation."""
        self.messages = messages


def _validate_lfg_inputs(
    creator_role: str, filled_spots: dict[str, int], roles: dict[str, RoleDefinition]
):
    errors = []
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


def _convert_required_spots_to_filled(
    roles: dict[str, RoleDefinition], required_spots: str, creator_role: str
):
    role_counts = {role.name: role.count for role in roles.values()}
    required_spots_roles = {
        role_name: required_spots.count(role_def.identifier)
        for role_name, role_def in roles.items()
    }
    logging.debug(f"required_spots: {required_spots}")
    logging.debug(f"required_spots_roles: {required_spots_roles}")
    if required_spots_roles[creator_role] + 1 > role_counts[creator_role]:
        raise LFGValidationError([
            "You cannot assign that many filled spots when you are in that role"
        ])
    filled_spots = {}
    for role_name, role_count in role_counts.items():
        filled_spots[role_name] = role_count - required_spots_roles[role_name]
    filled_spots[creator_role] -= 1
    return filled_spots


async def lfg(
    interaction: discord.Interaction,
    activity: str,
    creator_role: str,
    required_spots: str,
    listed_as: str,
    creator_notes: str,
    config: CommandConfig,
    **options,
):
    """Creates a GroupBuilder instance from a slash command."""
    logging.debug("".join([str((key, value)) for key, value in locals().items()]))
    try:
        filled_spots = _convert_required_spots_to_filled(config.roles, required_spots, creator_role)
        _validate_lfg_inputs(creator_role, filled_spots, config.roles)
    except LFGValidationError as e:
        response = "\n".join(e.messages)
        message_func = (
            interaction.followup.send
            if interaction.response.is_done()
            else interaction.response.send_message
        )
        await message_func(response, ephemeral=True)
        return None

    user_inputs = {
        "activity_name": activity,
        "listed_as": listed_as,
        "creator_notes": creator_notes,
        **options,
    }
    logging.debug(user_inputs)

    instance = GroupBuilder(
        interaction=interaction,
        group_info=user_inputs,
        config=config,
        creator_role=creator_role,
        filled_spots=filled_spots,
    )
    await instance.send_message(interaction)
    await instance.send_passphrase(interaction)


async def lfgdebug(interaction: discord.Interaction, debug_type: int):
    """Creates a listing for debugging purposes."""
    roles = {
        "tank": RoleDefinition("tank", 1, "🛡️", "t"),
        "healer": RoleDefinition("healer", 1, "🪄", "h"),
        "dps": RoleDefinition("dps", 3, "⚔️", "t"),
    }
    config = CommandConfig(
        [],
        roles,
        "lfgdebug",
        "Multiple LFG for debug purposes",
        True,
        "Debug",
        1,
        1,
        ["kick user"],
        [],
    )
    if debug_type == 0:
        difficulty = 3
        required_spots = "h"
        await interaction.channel.send("Difficulty 3 group with 1 healer spot")  # type: ignore

    if debug_type == 1:
        difficulty = 5
        required_spots = "thdd"
        await interaction.channel.send("Difficulty 5 group with all spots open")  # type: ignore

    if debug_type == 2:
        difficulty = 0
        required_spots = "h"
        await interaction.channel.send("Difficulty 0 group with 1 healer spot")  # type: ignore

    if debug_type == 3:
        difficulty = 3
        required_spots = "dddd"
        await interaction.channel.send("Invalid group (4 dps spots)")  # type: ignore

    if debug_type == 4:
        difficulty = -1
        required_spots = "ddd"
        await interaction.channel.send(  # type: ignore
            "Invalid group (3 dps spots when only 2 avail if creator is dps)"
        )

    if debug_type == 5:
        difficulty = 4
        required_spots = ""
        await interaction.channel.send("Invalid group (no available spots)")  # type: ignore

    return await lfg(
        interaction=interaction,
        activity="test",
        difficulty=difficulty,
        creator_role="dps",
        timing_aim="Time but complete",
        listed_as=f"Dungeon Debug Test {debug_type}",
        creator_notes="debug creator notes blah blah",
        required_spots=required_spots,
        config=config,
    )

"""Controls the LFG system."""

import logging

import discord

from db_py.group_builder import GroupBuilder
from db_py.lfg_options import LFGOptions
from db_py.resources import load_dungeons, load_time_types
from db_py.roles import RoleDefinition
from db_py.utils import get_difficulty_start_and_end_from_channel_name


class LFGValidationError(Exception):
    """LFG validation error message handler."""

    def __init__(self, messages):
        """Initialisation."""
        self.messages = messages


def _validate_lfg_inputs(
    difficulty: int,
    time_type: str,
    creator_role: str,
    filled_spots: dict[str, int],
    roles: dict[str, RoleDefinition],
):
    errors = []
    if difficulty == -1:
        errors.append("You cannot use this command in this channel.")

    time_types = load_time_types()
    if time_type not in time_types and time_type not in time_types.values():
        errors.append(f"time_type not recognised, given: {time_type}, valid: {time_types}")

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
    dungeon: str,
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
        _validate_lfg_inputs(
            difficulty, time_type, creator_role, filled_spots, config.get("role", {})
        )
    except LFGValidationError as e:
        response = "\n".join(e.messages)
        message_func = (
            interaction.followup.send
            if interaction.response.is_done()
            else interaction.response.send_message
        )
        await message_func(response, ephemeral=True)
        return None

    time_types = load_time_types()
    if time_type not in time_types.values():
        time_type = time_types.get(time_type, "")

    dungeons = load_dungeons(config.get("expansion"), config.get("season"))  # type: ignore

    if dungeon in dungeons:
        name_short = dungeon
        name_long = dungeons[dungeon]
    else:
        name_long = dungeon
        for key, value in dungeons.items():
            if value == dungeon:
                name_short = key
                break

    dungeon_info = {
        "name_short": name_short,
        "name_long": name_long,
        "listed_as": listed_as,
        "creator_notes": creator_notes,
        "difficulty": difficulty,
        "time_type": time_type,
    }
    logging.debug(dungeon_info)

    instance = GroupBuilder(
        interaction=interaction,
        group_info=dungeon_info,
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
    listed_as: str,
    creator_notes: str,
    roles: dict[str, RoleDefinition],
    config: dict,
):
    """Creates a LFG listing using an interactable interface."""
    difficulties = get_difficulty_start_and_end_from_channel_name(interaction.channel.name)  # type: ignore
    if difficulties is None:
        response = "You cannot use the LFG command in this channel"
        await interaction.response.send_message(response, ephemeral=True)
        return None

    role_counts = {role["name"]: role["count"] for role in config.get("roles", {})}

    view = LFGOptions(difficulties, config, role_counts)
    await interaction.response.send_message(view=view, ephemeral=True)
    await view.wait()
    if not view.confirmed:
        logging.debug("Group creation cancelled.")
        return None

    filled_spots = role_counts.copy()
    filled_spots[view.creator_role] -= 1
    for role, required_num in view.required_roles.items():
        filled_spots[role] -= required_num

    return await _lfg(
        interaction=interaction,
        dungeon=dungeon,
        difficulty=view.difficulty,
        creator_role=view.creator_role,
        time_type=view.time_type,
        listed_as=listed_as,
        creator_notes=creator_notes,
        filled_spots=filled_spots,
        roles=roles,
        config=config,
    )


async def lfgquick(
    interaction: discord.Interaction,
    dungeon: str,
    difficulty: int,
    time_type: str,
    creator_role: str,
    required_spots: str,
    listed_as: str,
    creator_notes: str,
    roles: dict[str, RoleDefinition],
    config: dict,
):
    """Creates a LFG listing using a quick-string."""
    role_counts = {role.name: role.count for role in roles.values()}
    required_spots_roles = {
        role_name: required_spots.count(role_def.indicator) for role_name, role_def in roles.items()
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
        dungeon=dungeon,
        difficulty=difficulty,
        creator_role=creator_role,
        time_type=time_type,
        listed_as=listed_as,
        creator_notes=creator_notes,
        filled_spots=filled_spots,
        roles=roles,
        config=config,
    )


async def lfgdebug(interaction: discord.Interaction, debug_type: int, config: dict):
    """Creates a listing for debugging purposes."""
    config["roles"] = {
        "tank": RoleDefinition("tank", 1, "🛡️", "t"),
        "healer": RoleDefinition("healer", 1, "🪄", "h"),
        "dps": RoleDefinition("dps", 1, "⚔️", "t"),
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
        dungeon=list(load_dungeons(config.get("expansion"), config.get("season")))[0],  # type: ignore
        difficulty=difficulty,
        creator_role="dps",
        time_type="tbc",
        listed_as=f"Dungeon Debug Test {debug_type}",
        creator_notes="debug creator notes blah blah",
        filled_spots=filled_spots,
        config=config,
    )

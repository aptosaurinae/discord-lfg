"""Controls the LFG system."""

import logging

import discord

from db_py.db_instance import DungeonInstance
from db_py.lfg_options import LFGOptions
from db_py.resources import load_dungeons, load_time_types
from db_py.roles import RoleType
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
):
    errors = []
    if difficulty == -1:
        errors.append("You cannot use this command in this channel.")

    time_types = load_time_types()
    if time_type not in time_types and time_type not in time_types.values():
        errors.append(f"time_type not recognised, given: {time_type}, valid: {time_types}")

    max_counts = DungeonInstance.role_counts.copy()
    max_counts[creator_role] -= 1
    for role, count in filled_spots.items():
        if count > max_counts[role]:
            errors.append(
                f"You cannot assign that many filled spots to that role "
                f"({role}, {count}, max: {max_counts[role]})"
            )

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
    config: dict,
):
    logging.debug("".join([str((key, value)) for key, value in locals().items()]))
    try:
        _validate_lfg_inputs(difficulty, time_type, creator_role, filled_spots)
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

    dungeons = load_dungeons(config.get("expansion"), config.get("season"))    # type: ignore

    if dungeon in dungeons:
        dungeon_short = dungeon
        dungeon_long = dungeons[dungeon]
    else:
        dungeon_long = dungeon
        for key, value in dungeons.items():
            if value == dungeon:
                dungeon_short = key
                break

    dungeon_info = {
        "dungeon_short": dungeon_short,
        "dungeon_long": dungeon_long,
        "listed_as": listed_as,
        "creator_notes": creator_notes,
        "difficulty": difficulty,
        "time_type": time_type,
    }
    logging.debug(dungeon_info)

    instance = DungeonInstance(interaction=interaction, dungeon_info=dungeon_info, config=config)
    instance.add_role(creator_role, interaction)
    instance.fill_spots(interaction, filled_spots)
    await instance.send_message(interaction)
    await instance.send_passphrase(interaction)


def _parse_filled_spots(input: str) -> dict:
    return {role: input.count(role[:1]) for role in [name.name for name in RoleType]}


async def lfg(
    interaction: discord.Interaction,
    dungeon: str,
    listed_as: str,
    creator_notes: str,
    config: dict,
):
    """Creates a LFG listing using an interactable interface."""
    difficulties = get_difficulty_start_and_end_from_channel_name(interaction.channel.name)  # type: ignore
    if difficulties is None:
        response = "You cannot use the LFG command in this channel"
        await interaction.response.send_message(response, ephemeral=True)
        return None

    view = LFGOptions(difficulties, config)
    await interaction.response.send_message(view=view, ephemeral=True)
    await view.wait()
    if not view.confirmed:
        logging.debug("Dungeon group creation cancelled.")
        return None

    filled_spots = DungeonInstance.role_counts.copy()
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
        config=config,
    )


async def lfgquick(
    interaction: discord.Interaction,
    dungeon: str,
    difficulty: int,
    time_type: str,
    creator_role: str,
    filled_spots: str,
    listed_as: str,
    creator_notes: str,
    config: dict
):
    """Creates a LFG listing using a quick-string."""
    return await _lfg(
        interaction=interaction,
        dungeon=dungeon,
        difficulty=difficulty,
        creator_role=creator_role,
        time_type=time_type,
        listed_as=listed_as,
        creator_notes=creator_notes,
        filled_spots=_parse_filled_spots(filled_spots),
        config=config,
    )


async def lfgdebug(
    interaction: discord.Interaction,
    debug_type: int,
    config: dict,
):
    """Creates a listing for debugging purposes."""
    if debug_type == 1:
        difficulty = 3
        filled_spots = {"tank": 1, "healer": 0, "dps": 2}

    if debug_type == 2:
        difficulty = 5
        filled_spots = {"tank": 0, "healer": 0, "dps": 0}

    if debug_type == 3:
        difficulty = 0
        filled_spots = {"tank": 1, "healer": 0, "dps": 2}

    if debug_type == 4:
        difficulty = 3
        filled_spots = {"tank": 1, "healer": 0, "dps": 4}

    if debug_type == 5:
        difficulty = -1
        filled_spots = {"tank": 1, "healer": 0, "dps": 4}

    if debug_type == 6:
        difficulty = 4
        filled_spots = {"tank": 1, "healer": 1, "dps": 2}

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

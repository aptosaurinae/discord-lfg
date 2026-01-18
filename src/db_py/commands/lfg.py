"""Controls the LFG system."""

import discord

from db_py.db_instance import DungeonInstance
from db_py.resources import load_dungeons, load_time_types
from db_py.roles import RoleType


class LFGValidationError(Exception):
    """LFG validation error message handler."""
    def __init__(self, messages):
        """Initialisation."""
        self.messages = messages


def _validate_lfg_inputs(
    difficulty: int,
    creator_role: str,
    filled_spots: dict[str, int],
):
    errors = []
    if difficulty == 0:
        errors.append("You cannot use this command in this channel.")

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
    try:
        _validate_lfg_inputs(difficulty, creator_role, filled_spots)
    except LFGValidationError as e:
        await interaction.response.send_message("\n".join(e.messages), ephemeral=True)

    time_type = load_time_types()[time_type]
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

    instance = DungeonInstance(interaction=interaction, dungeon_info=dungeon_info, config=config)
    instance.update_role(creator_role, interaction)
    instance.fill_spots(interaction, filled_spots)
    await instance.send_message(interaction)
    await instance.send_passphrase(interaction, True)


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
    difficulty = 1
    time_type = "vc"
    creator_role = "tank"
    filled_spots = {"tank": 0, "healer": 0, "dps": 0}
    return await _lfg(
        interaction=interaction,
        dungeon=dungeon,
        difficulty=difficulty,
        creator_role=creator_role,
        time_type=time_type,
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
        difficulty = 3
        filled_spots = {"tank": 0, "healer": 0, "dps": 0}

    if debug_type == 3:
        difficulty = 0
        filled_spots = {"tank": 1, "healer": 0, "dps": 2}

    if debug_type == 4:
        difficulty = 3
        filled_spots = {"tank": 1, "healer": 0, "dps": 4}

    if debug_type == 5:
        difficulty = 0
        filled_spots = {"tank": 1, "healer": 0, "dps": 4}

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

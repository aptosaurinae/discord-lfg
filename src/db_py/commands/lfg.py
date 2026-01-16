"""Controls the LFG system."""

import discord

from db_py.db_instance import DungeonInstance
from db_py.resources import load_dungeons, load_time_types


async def _lfg(
    interaction: discord.Interaction,
    dungeon: str,
    difficulty: int,
    creator_role: str,
    time_type: str,
    listed_as: str,
    creator_notes: str,
    config: dict,
):
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
    await instance.update_role(creator_role, interaction)
    await interaction.channel.send(**instance.listing_message_full)    # type: ignore
    await instance.send_passphrase(interaction)


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
    return await _lfg(
        interaction=interaction,
        dungeon=dungeon,
        difficulty=difficulty,
        creator_role=creator_role,
        time_type=time_type,
        listed_as=listed_as,
        creator_notes=creator_notes,
        config=config,
    )


async def lfgquick(
    interaction: discord.Interaction,
    dungeon: str,
    difficulty: int,
    time_type: str,
    creator_role: str,
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
        config=config,
    )

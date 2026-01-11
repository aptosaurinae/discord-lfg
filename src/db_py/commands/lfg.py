"""Controls the LFG system."""

import random
import string

import discord

from db_py.db_instance import DungeonInstance
from db_py.resources import load_dungeons, load_lists


def _generate_listing_name(dungeon_short: str, num_chars: int, guild_name):
    random_string = ""
    for _ in range(num_chars):
        random_string += random.choice(string.ascii_uppercase)

    if guild_name != "":
        guild_name += " "

    return f"{guild_name}{dungeon_short} {random_string}"


async def _lfg(
    interaction: discord.Interaction,
    dungeon: str,
    difficulty: int,
    time_type: str,
    listed_as: str,
    creator_notes: str,
    config: dict,
):
    time_type = load_lists()["time_types"][time_type]
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

    if creator_notes != "":
        creator_notes = f"Notes: {creator_notes}\n"
    if listed_as == "":
        listed_as = _generate_listing_name(
            dungeon_short,
            num_chars=3,
            guild_name=config.get("guild_name", "")
        )

    dungeon_info = {
        "dungeon_short": dungeon_short,
        "dungeon_long": dungeon_long,
        "listed_as": listed_as,
        "creator_notes": creator_notes,
        "difficulty": difficulty,
        "time_type": time_type,
    }

    instance = DungeonInstance(interaction=interaction, dungeon_info=dungeon_info, config=config)

    await interaction.channel.send(                             # type: ignore
        content=instance.listing_title,
        embed=discord.Embed(
            color=606675,
            title=instance.dungeon_title,
            description=instance.description
        )
    )

    passphrase = instance.metadata.get("passphrase")
    await interaction.response.send_message(
        f"The passphrase for your group is: {passphrase}",
        ephemeral=True
    )


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
    return await _lfg(
        interaction=interaction,
        dungeon=dungeon,
        difficulty=difficulty,
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
    listed_as: str,
    creator_notes: str,
    config: dict
):
    """Creates a LFG listing using a quick-string."""
    return await _lfg(
        interaction=interaction,
        dungeon=dungeon,
        difficulty=difficulty,
        time_type=time_type,
        listed_as=listed_as,
        creator_notes=creator_notes,
        config=config,
    )

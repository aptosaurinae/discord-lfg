"""Controls the LFG system."""

import random
import string

import discord

from db_py.resources import load_dungeons, load_lists

DEFAULT_EMOJIS = {
    "tank": ":shield:",
    "dps": ":crossed_swords:",
    "healer": ":magic_wand:",
}


def _generate_listing_name(dungeon_short: str, num_chars: int, guild_name):
    random_string = ""
    for _ in range(num_chars):
        random_string += random.choice(string.ascii_uppercase)
    if guild_name != "":
        guild_name += " "
    return f"{guild_name}{dungeon_short} {random_string}"


def _generate_passphrase(num_words: int):
    words = load_lists()["passphrase_words"]
    passphrase = ""
    for _ in range(num_words):
        passphrase += random.choice(words)
    return passphrase


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
    emojis = config.get("emojis", DEFAULT_EMOJIS)

    if dungeon in dungeons:
        dungeon_short = dungeon
        dungeon_long = dungeons[dungeon]
    else:
        dungeon_long = dungeon
        for key, value in dungeons:
            if value == dungeon:
                dungeon_short = key
                break

    if creator_notes != "":
        creator_notes = f"Notes: {creator_notes}\n"
    if listed_as == "":
        listed_as = _generate_listing_name(
            dungeon_short,
            num_chars=3,
            guild_name=config.get("guild_name")
        )

    await interaction.channel.send(                             # type: ignore
        content=f"{dungeon_long} +{difficulty} ({time_type})",
        embed=discord.Embed(
            color=606675,
            title=f"{listed_as}",
            description=f"""{creator_notes}

            {emojis["tank"]} : tankname
            {emojis["healer"]} : healername
            {emojis["dps"]} : dpsname 1
            {emojis["dps"]} : dpsname 2
            {emojis["dps"]} : dpsname 3
            """
        )
    )
    passphrase = _generate_passphrase(3)
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

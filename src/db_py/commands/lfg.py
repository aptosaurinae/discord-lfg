"""Controls the LFG system."""

import discord

from db_py.resources import load_lists

DEFAULT_EMOJIS = {
    "tank": ":shield:",
    "dps": ":crossed_swords:",
    "healer": ":magic_wand:",
}


async def _lfg(
    interaction: discord.Interaction,
    dungeon: str,
    difficulty: int,
    time_type: str,
    listed_as: str,
    creator_notes: str,
    emojis: dict[str, str]
):
    if emojis is None:
        emojis = DEFAULT_EMOJIS
    time_type = load_lists()["time_types"][time_type]
    await interaction.channel.send(                             # type: ignore
        content=f"{dungeon} +{difficulty} ({time_type})",
        embed=discord.Embed(
            color=606675,
            title=f"{dungeon} +{difficulty} ({time_type})",
            description=f"""
            {emojis["tank"]} : tankname
            {emojis["healer"]} : healername
            {emojis["dps"]} : dpsname 1
            {emojis["dps"]} : dpsname 2
            {emojis["dps"]} : dpsname 3
            """
        )
    )
    await interaction.response.send_message("Thanks for listing your group!", ephemeral=True)


async def lfg(
    interaction: discord.Interaction,
    dungeon: str,
    listed_as: str,
    creator_notes: str,
    emojis: dict[str, str]
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
        emojis=emojis,
    )


async def lfgquick(
    interaction: discord.Interaction,
    dungeon: str,
    difficulty: int,
    time_type: str,
    listed_as: str,
    creator_notes: str,
    emojis: dict[str, str]
):
    """Creates a LFG listing using a quick-string."""
    return await _lfg(
        interaction=interaction,
        dungeon=dungeon,
        difficulty=difficulty,
        time_type=time_type,
        listed_as=listed_as,
        creator_notes=creator_notes,
        emojis=emojis,
    )

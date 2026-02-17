"""Manages stats logging."""

from pathlib import Path

import polars as pl


def get_data(data_path: Path):
    """Gets the existing data ready to append to (for warm-starting the bot)."""
    if data_path.exists():
        return pl.read_parquet(data_path)
    else:
        return pl.DataFrame()


def _write_data(data_path: Path, df: pl.DataFrame):
    df.write_parquet(data_path, compression="lz4", partition_by="date")


def _create_entry(
    activity_name: str,
    listed_as: str,
    creator_notes: str,
    creator_id: int,
    extra_info: list[str],
    role_names: list[str],
    user_ids: list[int],
    user_display_names: list[str],
) -> pl.DataFrame:
    """Logs a single GroupBuilder entry into the database."""
    entry = pl.DataFrame({
        "activity_name": [activity_name],
        "listed_as": [listed_as],
        "creator_notes": [creator_notes],
        "creator_id": [creator_id],
        "extra_info": [extra_info],
        "role_names": [role_names],
        "user_ids": [user_ids],
        "user_display_names": [user_display_names],
    })
    return entry


def _listing_message(activity_name: str, extra_info: list[str]):
    main_string = f"{activity_name}{' ' if len(extra_info) > 0 else ''}"
    main_string += " ".join([f"[{item}]" for item in extra_info])
    return main_string


def _roles_description(
    creator_id: int, role_names: list[str], user_ids: list[int], user_names: list[str]
):
    def _role_string(role_name: str, creator: bool, user_name: str):
        bold = "**" if user_name != "" else ""
        return f"{role_name} : {bold}{user_name}{bold}{' 🚩' if creator else ''}"

    role_string = ""
    for idx, role_name in enumerate(role_names):
        user_name = user_names[idx]
        creator = user_ids[idx] == creator_id
        role_string += f"{_role_string(role_name, creator, user_name)}\n"

    return role_string


def historic_group_string(group_data: dict):
    """Creates a string representing the historic group appropriate for display to a user."""
    listing_message = _listing_message(
        group_data.get("activity_name", ""), group_data.get("extra_info", [])
    )
    creator_notes = group_data.get("creator_notes")
    roles_description = _roles_description(
        group_data.get("creator_id", 0),
        group_data.get("role_names", 0),
        group_data.get("user_ids", 0),
        group_data.get("user_display_names", 0),
    )
    return f"**{listing_message}**\n{creator_notes}\n{roles_description}\n"

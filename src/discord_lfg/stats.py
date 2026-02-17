"""Manages stats logging."""

from datetime import date
from pathlib import Path

import polars as pl

DATA = pl.DataFrame()


def get_data(data_path: Path | None) -> pl.DataFrame:
    """Gets the existing data ready to append to (for warm-starting the bot)."""
    global DATA
    if data_path is not None and data_path.exists():
        DATA = pl.read_parquet(data_path)
        return DATA
    else:
        DATA = pl.DataFrame(
            {
                "date_finished": [],
                "activity_name": [],
                "listed_as": [],
                "creator_notes": [],
                "creator_id": [],
                "extra_info": [],
                "role_names": [],
                "user_ids": [],
                "user_display_names": [],
            },
            schema={
                "date_finished": pl.Date,
                "activity_name": pl.String,
                "listed_as": pl.String,
                "creator_notes": pl.String,
                "creator_id": pl.Int64,
                "extra_info": pl.List(pl.String),
                "role_names": pl.List(pl.String),
                "user_ids": pl.List(pl.Int64),
                "user_display_names": pl.List(pl.String),
            },
        )
        return DATA


def _write_data(data_path: Path, df: pl.DataFrame, filter_date: date | None = None):
    if filter_date is not None:
        df = df.clone()
        df = df.filter(pl.col("date_finished") == filter_date)
    df.write_parquet(data_path, compression="lz4", partition_by="date_finished")


def _create_entry(
    date_finished: date,
    activity_name: str,
    listed_as: str,
    creator_notes: str,
    creator_id: int,
    extra_info: list[str],
    role_names: list[str],
    user_ids: list[int],
    user_display_names: list[str],
) -> pl.DataFrame:
    """Creates a single-row DataFrame with the GroupBuilder information."""
    entry = pl.DataFrame({
        "date_finished": [date_finished],
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


def record_group(
    date_finished: date,
    activity_name: str,
    listed_as: str,
    creator_notes: str,
    creator_id: int,
    extra_info: list[str],
    role_names: list[str],
    user_ids: list[int],
    user_display_names: list[str],
):
    """Records a finished group into the data table."""
    global DATA
    entry = _create_entry(
        date_finished,
        activity_name,
        listed_as,
        creator_notes,
        creator_id,
        extra_info,
        role_names,
        user_ids,
        user_display_names,
    )
    DATA = pl.concat([DATA, entry])


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

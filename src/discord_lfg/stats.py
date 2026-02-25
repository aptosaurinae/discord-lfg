"""Manages stats logging."""

import logging
from datetime import date, timedelta
from pathlib import Path

import discord
import polars as pl

from discord_lfg.utils import datetime_now_utc

DATA = pl.DataFrame()

DATA_SCHEMA = {
    "command_name": pl.String,
    "date_finished": pl.Date,
    "activity_name": pl.String,
    "listed_as": pl.String,
    "creator_notes": pl.String,
    "creator_id": pl.Int64,
    "extra_info": pl.List(pl.String),
    "role_names": pl.List(pl.String),
    "user_ids": pl.List(pl.Int64),
    "user_display_names": pl.List(pl.String),
}


def _write_data(data_path: Path | None, df: pl.DataFrame, filter_date: date | None = None):
    if data_path is None:
        global OUTPUT_PATH
        data_path = OUTPUT_PATH
    if data_path is not None:
        if filter_date is not None:
            df = df.clone()
            df = df.filter(pl.col("date_finished") == filter_date)
        df.write_parquet(data_path, compression="lz4", partition_by="date_finished")


def get_data(data_path: Path | None) -> pl.DataFrame:
    """Gets the existing data ready to append to (for warm-starting the bot)."""
    global DATA
    global OUTPUT_PATH
    if data_path is not None and data_path.exists():
        OUTPUT_PATH = data_path
        DATA = pl.read_parquet(data_path, schema=DATA_SCHEMA)
        return DATA
    else:
        OUTPUT_PATH = None
        DATA = pl.DataFrame(schema=DATA_SCHEMA)
        return DATA


def record_group(
    command_name: str,
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
        command_name,
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
    if OUTPUT_PATH is not None:
        _write_data(OUTPUT_PATH, DATA, date_finished)
    return entry


def _create_entry(
    command_name: str,
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
        "command_name": [command_name],
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


def _listing_message(activity_name: str, extra_info: list[str]):
    main_string = f"{activity_name}{' ' if len(extra_info) > 0 else ''}"
    main_string += " ".join([f"[{item}]" for item in extra_info])
    return main_string


def _roles_description(
    creator_id: int, role_names: list[str], user_ids: list[int], user_names: list[str]
):
    def _role_string(role_name: str, creator: bool, user_name: str, user_id: int):
        bold = "**" if user_name != "" else ""
        return (
            f"{role_name} : {bold}{user_name}{bold}{' 🚩' if creator else ''}"
            f"{f'[{user_id}]' if user_id > 0 else ''}"
        )

    role_string = ""
    for idx, role_name in enumerate(role_names):
        user_name = user_names[idx]
        creator = user_ids[idx] == creator_id
        role_string += f"{_role_string(role_name, creator, user_name, user_ids[idx])}\n"

    return role_string


def historic_group(group_data: dict):
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


def historic_group_embed(group_data: dict):
    """Generates a historic group embed."""
    description = historic_group(group_data)
    return discord.Embed(
        title=(
            f"{group_data.get('listed_as', 'Historic Group')} "
            f"[{group_data.get('date_finished', datetime_now_utc()).isoformat()}]"
        ),
        description=description,
        colour=discord.Colour.blue(),
    )


def end_of_month(start_date: date):
    """Creates a date for the last day of the month of a given date."""
    if start_date.month == 12:
        return start_date.replace(year=start_date.year + 1, month=1) - timedelta(days=1)
    else:
        return start_date.replace(month=start_date.month + 1) - timedelta(days=1)


def next_month(start_date: date):
    """Creates a date for the first day of the next month of a given date."""
    if start_date.month == 12:
        return start_date.replace(year=start_date.year + 1, month=1, day=1)
    else:
        return start_date.replace(month=start_date.month + 1)


class HistoricGroupCommandNameSelect(discord.ui.Select):
    """Select from command names."""

    def __init__(self, command_names: list[str]):
        """Initialisation."""
        options = [discord.SelectOption(label=f"{item}") for item in sorted(command_names)]
        super().__init__(
            placeholder="Choose a command type",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
            required=True,
            disabled=False,
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        assert self.view is not None
        logging.debug("CommandNameSelect callback")
        if self.values:
            self.view.command_selected = self.values[0]
        await interaction.response.defer()


class HistoricGroupDateSelect(discord.ui.Select):
    """Select from dates."""

    def __init__(self, start_date: date):
        """Initialisation."""
        current = start_date.replace(day=1)
        end_day = datetime_now_utc().date()
        month_start_days: list[date] = []
        while current <= end_day:
            month_start_days.append(current)
            current = next_month(current)

        options = [
            discord.SelectOption(label=f"{date_item.isoformat()}")
            for date_item in month_start_days[-24:]
        ]
        super().__init__(
            placeholder="Choose a month.",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
            required=True,
            disabled=False,
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        assert self.view is not None
        logging.debug("StatsDateSelect callback")
        if self.values:
            self.view.date_selected = date.fromisoformat(self.values[0])
        await interaction.response.defer()


class HistoricGroupViewer(discord.ui.View):
    """View historic groups."""

    def __init__(
        self,
        interaction: discord.Interaction,
        user_id_str: str = "0",
        moderator_role_name: str = "",
    ):
        """Initialisation."""
        super().__init__(timeout=120)
        self.message: discord.InteractionMessage = None  # type: ignore
        user_id = int(user_id_str)

        moderator = False
        for role in interaction.user.roles:  # type: ignore
            if moderator_role_name == role.name:
                moderator = True

        if not (moderator and user_id > 0):
            user_id = interaction.user.id
        self.user_data = DATA.filter(pl.col("user_ids").list.contains(user_id))
        if len(self.user_data) > 0:
            start_date = self.user_data.select("date_finished").min()[0, 0]
            command_options = self.user_data.select("command_name").unique().to_series().to_list()

            self.date_selected: date = start_date
            self.add_item(HistoricGroupDateSelect(start_date))

            self.command_selected = command_options[0]
            self.add_item(HistoricGroupCommandNameSelect(command_options))

    @discord.ui.button(label="Show Groups", style=discord.ButtonStyle.primary, row=4)
    async def show_groups(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show groups to the user."""
        start_date = self.date_selected
        end_date = end_of_month(start_date)
        self.group_data = self.user_data.filter(
            pl.col("command_name") == self.command_selected,
            pl.col("date_finished").dt.date() >= start_date,
            pl.col("date_finished").dt.date() <= end_date,
        ).sort("date_finished")
        if len(self.group_data) <= 1:
            self.next.disabled = True
            self.previous.disabled = True
        else:
            self.previous.disabled = True
            self.next.disabled = False
        if len(self.group_data) > 0:
            self.data_row = 0
            await self.message.edit(  # type: ignore
                embed=historic_group_embed(self.group_data.row(self.data_row, named=True)),
                view=self,
            )
        await interaction.response.defer()

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary, row=4, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Shows the chronologically previous group."""
        self.data_row -= 1
        if self.data_row == 0:
            button.disabled = True
        if self.data_row >= 0:
            self.next.disabled = False
            await self.message.edit(  # type: ignore
                embed=historic_group_embed(self.group_data.row(self.data_row, named=True)),
                view=self,
            )
        await interaction.response.defer()

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary, row=4, disabled=True)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Shows the chronologically next group."""
        self.data_row += 1
        if self.data_row == len(self.group_data) - 1:
            button.disabled = True
        if self.data_row <= len(self.group_data) - 1:
            self.previous.disabled = False
            await self.message.edit(  # type: ignore
                embed=historic_group_embed(self.group_data.row(self.data_row, named=True)),
                view=self,
            )
        await interaction.response.defer()

    async def on_timeout(self) -> None:
        """Do stuff when timeout occurs."""
        logging.debug("stats history timed out.")
        if self.message:
            await self.message.edit(content="Stats viewer has timed out.", view=None)  # type: ignore
        self.stop()

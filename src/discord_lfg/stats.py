"""Manages stats logging."""

import logging
from datetime import date, timedelta
from pathlib import Path

import discord
import polars as pl

from discord_lfg.utils import datetime_now_utc, end_of_month, next_month

DATA = pl.DataFrame()

DATA_SCHEMA = {
    "command_name": pl.String,
    "date_finished": pl.Date,
    "finished_state": pl.String,
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
    finished_state: str,
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
        finished_state,
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
    finished_state: str,
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
        "finished_state": [finished_state],
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
    finish_state = group_data.get("finished_state", "")
    if finish_state in ["timed_out", "cancelled"]:
        colour = discord.Colour.red()
    elif finish_state == "complete":
        colour = discord.Colour.blue()
    else:
        colour = discord.Colour.dark_grey()
    return discord.Embed(
        title=(
            f"{group_data.get('listed_as', 'Historic Group')} "
            f"[{group_data.get('date_finished', datetime_now_utc()).isoformat()} - "
            f"{finish_state.capitalize}]"
        ),
        description=description,
        colour=colour,
    )


class HistoricCommandNameSelect(discord.ui.Select):
    """Select from command names."""

    def __init__(self, command_names: list[str]):
        """Initialisation."""
        options = [discord.SelectOption(label=f"{item}") for item in sorted(command_names)]
        options[0].default = True
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
        logging.debug("HistoricCommandNameSelect callback")
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
        logging.debug("HistoricGroupDateSelect callback")
        if self.values:
            self.view.date_selected = date.fromisoformat(self.values[0])
        await interaction.response.defer()


class HistoricStatsDateSelect(discord.ui.Select):
    """Select from dates."""

    def __init__(self):
        """Initialisation."""
        today = datetime_now_utc().date()
        self.durations = {
            "Today": (today, today),
            "Last 7 days": (today - timedelta(days=7), today),
            "Last 28 days": (today - timedelta(days=28), today),
            "This month": (today.replace(day=1), today),
            "Last 6 months (180 days)": (today - timedelta(days=180), today),
            "All time": (today - timedelta(days=9999), today),
        }
        options = [discord.SelectOption(label=item) for item in self.durations]
        options[0].default = True
        super().__init__(
            placeholder="Choose a period.",
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
        logging.debug("HistoricStatsDateSelect callback")
        if self.values:
            self.view.date_start, self.view.date_end = self.durations[self.values[0]]
        await interaction.response.defer()


class HistoricStatsFinishTypeSelect(discord.ui.Select):
    """Select which users to remove."""

    def __init__(self):
        """Initialisation."""
        options = ["complete", "cancelled", "timed_out"]
        options = [discord.SelectOption(label=f"{item}") for item in options]
        options[0].default = True

        super().__init__(
            placeholder="Choose types of groups to include.",
            min_values=1,
            max_values=len(options),
            options=options,
            row=3,
            required=False,
            disabled=False,
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        assert self.view is not None
        logging.debug("HistoricStatsFinishTypeSelect callback")
        if self.values:
            self.view.finish_types = []
            for item in self.values:
                self.view.finish_types.append(item)
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
            self.add_item(HistoricCommandNameSelect(command_options))

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


class HistoricStatsViewer(discord.ui.View):
    """View historic stats."""

    def __init__(self):
        """Initialisation."""
        super().__init__(timeout=120)
        self.message: discord.InteractionMessage = None  # type: ignore

        self.stats_data = DATA.clone()
        command_options = self.stats_data.select("command_name").unique().to_series().to_list()

        self.date_start = datetime_now_utc().date()
        self.date_end = self.date_start
        self.date_selector = HistoricStatsDateSelect()
        self.add_item(self.date_selector)

        self.command_selected = command_options[0]
        self.command_selector = HistoricCommandNameSelect(command_options)
        self.add_item(self.command_selector)

        self.finish_types = ["complete"]
        self.finish_type_selector = HistoricStatsFinishTypeSelect()
        self.add_item(self.finish_type_selector)

    def retain_options(self):
        """Sets currently selected options as new defaults so these are retained through updates."""
        for selector in [self.date_selector, self.command_selector, self.finish_type_selector]:
            selector: discord.ui.Select
            selected = selector.values
            if selected:
                for option in selector.options:
                    option.default = option.value in selected

    @discord.ui.button(label="Show Stats", style=discord.ButtonStyle.primary, row=4)
    async def show_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show groups to the user."""
        display_data = self.stats_data.filter(
            pl.col("command_name") == self.command_selected,
            pl.col("date_finished").dt.date() >= self.date_start,
            pl.col("date_finished").dt.date() <= self.date_end,
            pl.col("finished_state").is_in(self.finish_types),
        )
        display_data = (
            display_data.group_by("activity_name").agg(
                pl.col("command_name").count().alias("count")
            )
        ).sort(by="activity_name")
        embed_description = ""
        for row in display_data.iter_rows(named=True):
            embed_description += f"{row['activity_name']}: {row['count']}\n"
        embed_title = (
            f"{self.command_selected} [{self.date_start.isoformat()} - {self.date_end.isoformat()}]"
        )
        embed = discord.Embed(
            title=embed_title, description=embed_description, colour=discord.Colour.dark_gold()
        )
        self.retain_options()
        await self.message.edit(embed=embed, view=self)  # type: ignore
        await interaction.response.defer()

    async def on_timeout(self) -> None:
        """Do stuff when timeout occurs."""
        logging.debug("stats history timed out.")
        if self.message:
            await self.message.edit(content="Stats viewer has timed out.", view=None)  # type: ignore
        self.stop()

"""Main DB instance control."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import discord

from db_py.resources import generate_listing_name, generate_passphrase, load_emojis
from db_py.roles import Role, RoleType


@dataclass
class DungeonDetails:
    """Container for dungeon details."""
    dungeon_short: str
    dungeon_long: str
    listed_as: str
    creator_notes: str
    difficulty: int
    time_type: str


@dataclass
class DungeonUser:
    """Container for discord user information relevant to Dungeon Buddy."""
    id: int
    tag: str
    name: str
    display_name: str
    global_name: str | None


@dataclass
class DungeonState:
    """Container for the state of the dungeon."""
    created_at: datetime
    close_group_at: datetime
    editable_length: int
    closed: bool
    cancelled: bool
    timed_out: bool
    empty_spots: int
    passphrase: str
    filled_spot_name: str
    debug: bool


class DungeonInstance:
    """A listing for a specific dungeon run."""

    role_counts = {
        RoleType.tank.name: 1,
        RoleType.healer.name: 1,
        RoleType.dps.name: 3
    }

    def __init__(self, interaction: discord.Interaction, dungeon_info: dict, config: dict):
        """Creates a DungeonInstance.

        Args:
            interaction: The discord interaction which created this DungeonInstance. This allows
                us to capture the user information depending on who created this instance.
            dungeon_info: A dictionary of the dungeon specific information
            config: A dictionary of configuration information for Dungeon Buddy
        """
        logging.debug(
            f"DungeonInstance created by "
            f"{interaction.user.id} {interaction.user.display_name}"
        )
        self._setup_dungeon(**dungeon_info, config=config)
        self._roles_init(config.get("emojis", load_emojis()))
        self._state_init(config)
        self._creator_init(interaction)
        logging.debug(
            f"DungeonInstance initialisation finished for "
            f"{self.listing_message} {self.dungeon_title}"
        )

    # --- Properties

    @property
    def _strikethrough(self) -> str:
        return "~~" if (self.state.closed or self.state.cancelled or self.state.timed_out) else ""

    @property
    def current_users(self) -> list:
        """Retrieves the current valid user IDs in the instance."""
        tank_id = self.roles[RoleType.tank.name].userids[0]
        healer_id = self.roles[RoleType.healer.name].userids[0]
        dps_ids = self.roles[RoleType.dps.name].userids
        return [tank_id] + [healer_id] + dps_ids

    @property
    def current_user_tags(self) -> str:
        """Retrieves a string tagging all current users listed in the group."""
        tagged_users = ""
        for role in self.roles.values():
            for userid in role.userids:
                if userid > 0:
                    tagged_users += f"<@{userid}> "
        return tagged_users

    @property
    def description(self) -> str:
        """Gets a standardised description for the dungeon including role spots."""
        logging.debug("get description")
        dungeon = self.dungeon_details
        tank = self.roles[RoleType.tank.name]
        healer = self.roles[RoleType.healer.name]
        dps = self.roles[RoleType.dps.name]
        footer = ""
        if not (self.state.closed or self.state.cancelled or self.state.timed_out):
            footer = "`/lfghelp for Dungeon Buddy help`"

        def _role_string(role: Role, creator_id: int, role_idx: int = 0):
            name = role.display_names[role_idx]
            id = role.userids[role_idx]
            return f"{role.emoji} : {name}{'🚩' if id == creator_id else ''}"

        return (
            f"**{self._listing_message_body}**\n"
            f"{dungeon.creator_notes}\n"
            f"{_role_string(tank, self.creator.id)}\n"
            f"{_role_string(healer, self.creator.id)}\n"
            f"{_role_string(dps, self.creator.id)}\n"
            f"{_role_string(dps, self.creator.id, 1)}\n"
            f"{_role_string(dps, self.creator.id, 2)}\n"
            f"{footer}"
        )

    @property
    def dungeon_title(self) -> str:
        """Gets a standardised title string for the dungeon."""
        return f"{self.dungeon_details.listed_as}"

    @property
    def filled_roles(self) -> str:
        """Gets a string indicating the roles that have been filled, as emojis."""
        filled_roles_icons = ""
        for role_data in self.roles.values():
            filled_roles_icons += "".join([role_data.emoji for assignment in role_data.assigned if assignment])
        return filled_roles_icons

    @property
    def _listing_message_body(self) -> str:
        dungeon = self.dungeon_details
        return (
            f"{self._strikethrough}{dungeon.dungeon_long} +{dungeon.difficulty} "
            f"({dungeon.time_type}){self._strikethrough}"
        )

    @property
    def listing_message(self) -> str:
        """Gets the listing message for the dungeon."""
        logging.debug("get listing message")
        tags = False
        if self.state.closed:
            message = "**Group full** and now closed. "
        elif self.state.timed_out:
            message = "**Group creation timed out**: "
            tags = True
        elif self.state.cancelled:
            message = "**Group cancelled** by the group creator: "
            tags = True
        else:
            message = ""

        user_tags = self.current_user_tags if tags else ""

        return f"{message}{self._listing_message_body}{user_tags}"

    @property
    def passphrase(self) -> str:
        """Retrieves the passphrase for this dungeon instance."""
        return self.state.passphrase

    @property
    def _dungeon_embed(self) -> discord.Embed:
        logging.debug("get dungeon embed")
        title = (
            f"{self._strikethrough}{self.dungeon_title}{self._strikethrough} "
            f"{self.filled_roles}"
        )
        return discord.Embed(title=title, description=self.description, colour=606675)

    @property
    def _dungeon_buttons(self) -> discord.ui.View | None:
        if self.state.closed or self.state.cancelled or self.state.timed_out:
            logging.debug("no buttons needed")
            return None
        logging.debug("retrieving buttons")
        tank_btn = self._role_button(RoleType.tank)
        healer_btn = self._role_button(RoleType.healer)
        dps_btn = self._role_button(RoleType.dps)
        passphrase_btn = self._passphrase_button()
        settings_btn = self._settings_button()

        buttons = discord.ui.View()
        for element in [tank_btn, healer_btn, dps_btn, passphrase_btn, settings_btn]:
            buttons.add_item(element)
        return buttons

    # --- General methods

    def role_info(self, role_name):
        """Gets information about the requested role."""
        if role_name in self.roles:
            return self.roles[role_name]
        else:
            raise ValueError(f"{role_name} not in roles: {list(self.roles.keys())}")

    async def cancel_group(self):
        """Cancels the group and informs all current signups that it's been cancelled."""
        logging.debug(
            f"{self.dungeon_title} cancelled by {self.creator.id} / {self.creator.display_name}"
        )
        self.state.cancelled = True
        await self.edit_message()
        await self.message.channel.send(content=self.listing_message)

    def is_closed(self):
        """Checks if the group should be closed or re-opened and sets a timer accordingly."""
        if self.state.empty_spots == 0 and not self.state.closed:
            logging.debug(f"{self.listing_message} {self.dungeon_title} closed as it is full")
            self.state.closed = True
            self.state.close_group_at = (
                datetime_now_utc() + timedelta(minutes=self.state.editable_length))
            logging.debug(f"group closed but editable until {self.state.close_group_at}")
        elif self.state.empty_spots > 0 and self.state.closed:
            logging.debug(f"{self.listing_message} {self.dungeon_title} reopened as it has space")
            self.state.closed = False
            self.state.close_group_at = (
                datetime_now_utc() + timedelta(minutes=self.state.editable_length))
            logging.debug(f"group reopened and editable until {self.state.close_group_at}")

    # --- Initialisation

    def _role_constructor(self, role: RoleType, emojis: dict):
        return Role(
                name=role.name,
                userids=[0 for _ in range(self.role_counts[role.name])],
                display_names=["" for _ in range(self.role_counts[role.name])],
                assigned=[False for _ in range(self.role_counts[role.name])],
                button_style=discord.ButtonStyle.secondary,
                disabled=False,
                emoji=emojis[role.name],
            )

    def _roles_init(self, emojis: dict):
        """Initialise roles information."""
        self.roles = {
            RoleType.tank.name: self._role_constructor(RoleType.tank, emojis),
            RoleType.healer.name: self._role_constructor(RoleType.healer, emojis),
            RoleType.dps.name: self._role_constructor(RoleType.dps, emojis)
        }

    def _setup_dungeon(
        self,
        dungeon_short: str,
        dungeon_long: str,
        listed_as: str,
        creator_notes: str,
        difficulty: str,
        time_type: str,
        config: dict,
    ):
        """Captures information from the initial listing process."""
        guild_name = config.get("guild_name", "")
        random_listing = generate_listing_name(dungeon_short, 3, guild_name)
        self.dungeon_details = DungeonDetails(
            dungeon_short=dungeon_short,
            dungeon_long=dungeon_long,
            listed_as=listed_as if (listed_as != "") else random_listing,
            creator_notes="" if (creator_notes == "") else f"**Notes:** *{creator_notes}*\n",
            difficulty=int(difficulty),
            time_type=time_type,
        )

    def _state_init(self, config: dict):
        """Initialise state."""
        guild_name = config.get("guild_name", "")
        timeout_length = config.get("timeout_length", 30)
        editable_length = config.get("editable_length", 5)
        debug = config.get("debug", False)
        now = datetime_now_utc()
        self.state = DungeonState(
            created_at=now,
            close_group_at=now + timedelta(minutes=timeout_length),
            editable_length=editable_length,
            closed=False,
            cancelled=False,
            timed_out=False,
            empty_spots=5,
            passphrase=generate_passphrase(),
            filled_spot_name=f"~~Filled {guild_name}{' ' if guild_name != '' else ''}Spot~~",
            debug=bool(debug)
        )

    def _creator_init(self, interaction: discord.Interaction):
        """Capture creator elements."""
        self.creator = DungeonUser(
            id=interaction.user.id,
            tag=f"<@{interaction.user.id}>",
            name=interaction.user.name,
            display_name=interaction.user.display_name,
            global_name=interaction.user.global_name,
        )

    async def _check_if_closed_or_timed_out(self):
        """Closes the group if the background timer has finished and the group is not cancelled."""
        logging.debug(
            f"_timeout\n"
            f"created at: {self.state.created_at}\n"
            f"timeout set to: {self.state.close_group_at}"
        )
        while self.state.close_group_at > datetime.now(timezone.utc) and not self.state.cancelled:
            logging.debug(f"{self.dungeon_title} still active")
            self.is_closed()
            await asyncio.sleep(10)

        if self.state.cancelled:
            logging.debug(f"{self.dungeon_title} was cancelled while waiting to be closed.")
            return None
        elif self.state.closed:
            logging.debug(f"{self.dungeon_title} closed")
        else:
            logging.debug(f"{self.dungeon_title} timed out")
            self.state.timed_out = True

        await self.edit_message()

    # --- Responses and discord message display handling

    @property
    def _message_content(self):
        logging.debug("retrieve message content")
        return {
            "content": self.listing_message,
            "embed": self._dungeon_embed,
            "view": self._dungeon_buttons
        }

    async def send_message(self, interaction: discord.Interaction):
        """Sends the initial message for Dungeon Buddy."""
        await interaction.response.send_message(**self._message_content)
        self.message = await interaction.original_response()
        self._task = asyncio.create_task(self._check_if_closed_or_timed_out())

    async def edit_message(self):
        """Updates the Discord displayed message based on the current status of the instance."""
        logging.debug("edit_message")
        await self.message.edit(**self._message_content)

    async def send_passphrase(self, interaction: discord.Interaction, followup: bool = False):
        """Sends the passphrase."""
        logging.debug(
            f"send_passphrase\n"
            f"user_id: {interaction.user.id}\n"
            f"display_name: {interaction.user.display_name}\n"
            f"passphrase: {self.passphrase}"
        )
        message_func = interaction.followup.send if followup else interaction.response.send_message
        await message_func(
            content=f"The passphrase for your group is: {self.passphrase}",
            ephemeral=True
        )

    def fill_spots(
            self,
            interaction: discord.Interaction,
            filled_spots: dict[str, int],
    ):
        """Fills spots in the listing based on the filled spots dictionary given."""
        for role_name, num_filled in filled_spots.items():
            for _ in range(num_filled):
                self.add_role(role_name, interaction, True)

    def remove_filled_spot(
        self,
        assigned_role: str,
    ):
        """Removes a filled spot from the given role."""
        role = self.roles[assigned_role]
        self.remove_role(role, -1)

    def remove_role(self, role: Role, id: int):
        """Removes the role from the given user."""
        logging.debug(f"remove_role\nrole: {role}\nid: {id}\nstate: {self.state}")
        role_idx = role.userids.index(id)
        role.userids[role_idx] = 0
        role.display_names[role_idx] = ""
        role.assigned[role_idx] = False
        role.disabled = False
        self.state.empty_spots += 1

    def add_role(
        self,
        assigned_role: str,
        interaction: discord.Interaction,
        filled_spot: bool = False
    ):
        """Update the specified role name with the given user ID and display name."""
        # a user can only be present in a group once,
        # so must be removed if present before being added.
        user = interaction.user
        if not filled_spot:
            for role_name in [name.name for name in RoleType]:
                remove_role = self.roles[role_name]
                if user.id in remove_role.userids:
                    self.remove_role(remove_role, user.id)

        role = self.roles[assigned_role]
        logging.debug(f"add_role\nrole: {role}\nid: {user.id}\nstate: {self.state}")
        role_idx = role.assigned.index(False)
        role.userids[role_idx] = -1 if filled_spot else user.id
        role.display_names[role_idx] = (
            self.state.filled_spot_name if filled_spot else user.display_name)
        role.assigned[role_idx] = True
        if all(role.assigned):
            role.disabled = True
        self.state.empty_spots -= 1

    # --- Buttons

    def _role_button(self, role_type: RoleType) -> discord.ui.Button:
        """Creates a button interactable formatted for a particular role."""
        async def btn_click(interaction: discord.Interaction):
            logging.debug(f"{role.name} button clicked by {interaction.user.display_name}")
            self.add_role(assigned_role=role_type.name, interaction=interaction)
            self.is_closed()
            await self.edit_message()
            await self.send_passphrase(interaction, False)

        role = self.role_info(role_type.name)
        btn = discord.ui.Button(
            custom_id=role.name,
            emoji=role.emoji,
            style=role.button_style,
            disabled=role.disabled,
            row=1
        )
        btn.callback = btn_click
        return btn

    def _passphrase_button(self) -> discord.ui.Button:
        """Creates an ephemeral passphrase message for valid callers."""
        async def btn_click(interaction: discord.Interaction):
            logging.debug(f"passphrase button clicked by {interaction.user.display_name}")
            if interaction.user.id in self.current_users:
                await self.send_passphrase(interaction, False)
            else:
                await interaction.response.send_message(
                    "You are not part of this group.",
                    ephemeral=True
                )

        btn = discord.ui.Button(
            custom_id="passphrase",
            emoji="🔑",
            style=discord.ButtonStyle.secondary,
            disabled=False,
            row=1,
        )
        btn.callback = btn_click
        return btn

    def _settings_button(self) -> discord.ui.Button:
        """Accesses control options for valid users."""
        async def btn_click(interaction: discord.Interaction):
            logging.debug(f"settings button clicked by {interaction.user.display_name}")
            if interaction.user.id == self.creator.id:
                await interaction.response.send_message(
                    "You are the creator and clicked settings.",
                    ephemeral=True
                )
            elif interaction.user.id in self.current_users:
                await interaction.response.send_message(
                    "You are a group member and clicked settings.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "You are not part of this group.",
                    ephemeral=True
                )

        btn = discord.ui.Button(
            custom_id="settings",
            emoji="⚙️",
            style=discord.ButtonStyle.secondary,
            disabled=False,
            row=1,
        )
        btn.callback = btn_click
        return btn


def datetime_now_utc():
    """Gets the current time using the UTC timezone."""
    return datetime.now(tz=timezone.utc)

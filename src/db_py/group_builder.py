"""Main DB instance control."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import discord

from db_py.resources import generate_listing_name, generate_passphrase
from db_py.roles import RoleDefinition
from db_py.utils import datetime_now_utc, get_guild_role_mention_for_group_role


@dataclass
class GroupDetails:
    """Container for group details."""

    name_short: str
    name_long: str
    listed_as: str
    creator_notes: str
    difficulty: int
    time_type: str


@dataclass
class GroupUser:
    """Container for discord user information relevant to building a group."""

    id: int
    tag: str
    name: str
    display_name: str
    global_name: str | None
    interaction: discord.Interaction | None
    creator: bool
    role: str
    removal_reason: str = ""


@dataclass
class GroupRole:
    """Container for a particular role type."""

    name: str
    users: list[GroupUser]
    assigned: list[bool]
    button_style: discord.ButtonStyle
    disabled: bool
    emoji: str
    role_mention: str

    def __str__(self):
        """Returns a string representation of the object."""
        return (
            f"name: {self.name}\n"
            f"users: {self.users}\n"
            f"assigned: {self.assigned}\n"
            f"button_style: {self.button_style}\n"
            f"disabled: {self.disabled}"
            f"role_mention: {self.role_mention}"
        )


@dataclass
class GroupState:
    """Container for the state of the group."""

    created_at: datetime
    close_group_at: datetime
    editable_length: int
    closed: bool
    cancelled: bool
    timed_out: bool
    empty_spots: int
    filled_spots: int
    filled_spot_name: str
    passphrase: str
    debug: bool


class GroupBuilder:
    """Builds a group dynamically."""

    def __init__(
        self,
        interaction: discord.Interaction,
        group_info: dict,
        config: dict,
        creator_role: str,
        roles: dict[str, RoleDefinition],
    ):
        """Creates a Group Builder.

        Args:
            interaction: The discord interaction which created this GroupBuilder. This allows
                us to capture the user information depending on who created this instance.
            group_info: A dictionary of the group specific information
            config: A dictionary of configuration information for Group Builder
            creator_role: The role the creator has chosen
            role_counts: A dictionary of role_name to the count of the number of roles.
                Role names must match those given in the configuration file.
            roles: A dictionary of role information based on RoleDefinition.
        """
        logging.debug(
            f"GroupBuilder created by {interaction.user.id} {interaction.user.display_name}"
        )
        self.role_counts = {role.name: role.count for role in roles.values()}
        self.emojis = {role.name: role.emoji for role in roles.values()}
        guild_name = config.get("guild_name", "")
        timeout_length = config.get("timeout_length", 30)
        editable_length = config.get("editable_length", 5)
        debug = config.get("debug", False)
        self._state_init(guild_name, timeout_length, editable_length, debug)
        self._setup_group(**group_info, guild_name=guild_name)
        self._roles_init(
            roles,
            config.get("guild_roles", {}),
            interaction.channel.name if isinstance(interaction.channel.name, str) else "",  # type: ignore
        )
        self.creator = self.create_user_from_interaction(interaction, creator_role, True)
        self.add_role(creator_role, self.creator)
        self.kicked_users: list[GroupUser] = []
        logging.debug(
            f"GroupBuilder initialisation finished for {self.listing_message} {self.group_title}"
        )

    # --- Properties

    @property
    def _strikethrough(self) -> str:
        return "~~" if (self.state.cancelled or self.state.timed_out) else ""

    @property
    def current_user_tags(self) -> str:
        """Retrieves a string tagging all current users listed in the group."""
        tagged_users = ""
        for role in self.roles.values():
            for userid in [user.id for user in role.users]:
                if userid > 0:
                    tagged_users += f"<@{userid}> "
        logging.debug(f"current user tags: {tagged_users}")
        return tagged_users

    @property
    def current_role_tags(self) -> str:
        """Retrieves a string tagging all current required roles listed in the group."""
        current_role_tags = " ".join([
            role.role_mention for role in self.roles.values() if not role.disabled
        ])
        logging.debug(f"current role tags: {current_role_tags}")
        return current_role_tags

    @property
    def group_title(self) -> str:
        """Gets a standardised title string for the group."""
        return f"{self.group_details.listed_as}"

    @property
    def listing_message_body(self) -> str:
        """Body of the listing message."""
        group = self.group_details
        return (
            f"{self._strikethrough}{group.name_long} +{group.difficulty} "
            f"({group.time_type}){self._strikethrough}"
        )

    @property
    def listing_message(self) -> str:
        """Gets the listing message for the group."""
        logging.debug(f"get listing message {self.group_title}")
        tag_users = False
        tag_roles = False
        if self.state.timed_out:
            message = "**Group creation timed out**: "
            tag_users = True
        elif self.state.cancelled:
            message = "**Group cancelled** by the group creator: "
            tag_users = True
        else:
            message = ""
            tag_roles = True

        user_tags = f" {self.current_user_tags}" if tag_users else ""
        role_tags = f" {self.current_role_tags}" if tag_roles else ""

        return f"{message}{self.listing_message_body}{role_tags}{user_tags}"

    @property
    def description(self) -> str:
        """Gets a standardised description for the group including role spots."""

        def _role_string(role: GroupRole, creator_id: int, role_idx: int = 0):
            user = role.users[role_idx]
            bold = "**" if user.display_name != "" else ""
            return f"{role.emoji} : {bold}{user.display_name}{bold}{' 🚩' if user.id == creator_id else ''}"

        logging.debug(f"get description {self.group_title}")
        group = self.group_details
        role_string = ""
        for role_name in self.role_counts:
            role_string += f"{_role_string(self.roles[role_name], self.creator.id)}\n"
        kicked_users = "\n".join([
            f"{user.display_name}: {user.removal_reason}" for user in self.kicked_users
        ])
        if kicked_users != "":
            kicked_users = f"\nRemoved users:\n{kicked_users}"
        footer = ""
        if not (self.state.closed or self.state.cancelled or self.state.timed_out):
            if kicked_users != "":
                kicked_users += "\n"
            footer = "`/lfghelp for Group Builder help`"

        return (
            f"**{self.listing_message_body}**\n"
            f"{group.creator_notes}\n"
            f"{role_string}\n"
            # f"{kicked_users}"
            f"{footer}"
        )

    @property
    def filled_roles(self) -> str:
        """Gets a string indicating the roles that have been filled, as emojis."""
        filled_roles_icons = ""
        for role_data in self.roles.values():
            filled_roles_icons += " ".join([
                role_data.emoji for assignment in role_data.assigned if assignment
            ])
        return filled_roles_icons

    @property
    def group_embed(self) -> discord.Embed:
        """Gets a Discord Embed of the current group user state."""
        logging.debug(f"get group embed {self.group_title}")
        title = f"{self._strikethrough}{self.group_title}{self._strikethrough} {self.filled_roles}"
        if self.state.timed_out or self.state.cancelled:
            colour = discord.Colour.red()
        elif self.state.closed and not self._is_finished:
            colour = discord.Colour.yellow()
        elif self.state.closed and self._is_finished:
            colour = discord.Colour.blue()
        else:
            colour = discord.Colour.green()
        return discord.Embed(title=title, description=self.description, colour=colour)

    # --- General methods

    def role_info(self, role_name):
        """Gets information about the requested role."""
        if role_name in self.roles:
            return self.roles[role_name]
        else:
            raise ValueError(f"{role_name} not in roles: {list(self.roles.keys())}")

    # --- Initialisation

    def _role_constructor(
        self, role: RoleDefinition, guild_roles: list[discord.Role], channel_name: str
    ):
        return GroupRole(
            name=role.name,
            users=[self._create_empty_spot_user(role.name) for _ in range(role.count)],
            assigned=[False for _ in range(role.count)],
            button_style=discord.ButtonStyle.secondary,
            disabled=False,
            emoji=role.emoji,
            role_mention=get_guild_role_mention_for_group_role(
                group_role=role.name, guild_roles=guild_roles, channel_name=channel_name
            ),
        )

    def _roles_init(
        self, roles: dict[str, RoleDefinition], guild_roles: list[discord.Role], channel_name: str
    ):
        """Initialise roles information."""
        constructor_info = {"guild_roles": guild_roles, "channel_name": channel_name}
        self.roles = {
            role_name: self._role_constructor(role_info, **constructor_info)
            for role_name, role_info in roles.items()
        }

    def _setup_group(
        self,
        name_short: str,
        name_long: str,
        listed_as: str,
        creator_notes: str,
        difficulty: str,
        time_type: str,
        guild_name: str,
    ):
        """Captures information from the initial listing process."""
        random_listing = generate_listing_name(name_short, 3, guild_name)
        self.group_details = GroupDetails(
            name_short=name_short,
            name_long=name_long,
            listed_as=listed_as if (listed_as != "") else random_listing,
            creator_notes="" if (creator_notes == "") else f"**Notes:** *{creator_notes}*\n",
            difficulty=int(difficulty),
            time_type=time_type,
        )

    def _state_init(self, guild_name: str, timeout_length: int, editable_length: int, debug: bool):
        """Initialise state."""
        now = datetime_now_utc()
        empty_spots = sum(self.role_counts.values())
        self.state = GroupState(
            created_at=now,
            close_group_at=now + timedelta(minutes=timeout_length),
            editable_length=editable_length,
            closed=False,
            cancelled=False,
            timed_out=False,
            empty_spots=empty_spots,
            filled_spots=0,
            filled_spot_name=f"~~Filled {guild_name}{' ' if guild_name != '' else ''}Spot~~",
            passphrase=generate_passphrase(),
            debug=bool(debug),
        )

    # --- Group finishing methods (timeout, cancel, close because full)

    @property
    def _is_finished(self) -> bool:
        return self.state.close_group_at <= datetime_now_utc()

    async def _check_if_closed_or_timed_out(self):
        """Closes the group if the background timer has finished and the group is not cancelled."""
        logging.debug(
            f"_timeout {self.group_title}\n"
            f"created at: {self.state.created_at}\n"
            f"timeout set to: {self.state.close_group_at}"
        )
        while not self._is_finished and not self.state.cancelled:
            logging.debug(f"{self.group_title} still active")
            self.is_closed()
            await asyncio.sleep(10)

        if self.state.cancelled:
            logging.debug(f"{self.group_title} was cancelled while waiting to be closed.")
            return None
        elif self.state.closed:
            logging.debug(f"{self.group_title} closed")
        else:
            logging.debug(f"{self.group_title} timed out")
            self.state.timed_out = True

        await self.edit_message()
        del self

    async def cancel_group(self):
        """Cancels the group and informs all current signups that it's been cancelled."""
        logging.debug(
            f"{self.group_title} cancelled by {self.creator.id} / {self.creator.display_name}"
        )
        self.state.cancelled = True
        await self.edit_message()
        await self.message.channel.send(content=self.listing_message)
        del self

    def is_closed(self):
        """Checks if the group should be closed or re-opened and sets a timer accordingly."""
        if self.state.empty_spots == 0 and not self.state.closed:
            logging.debug(f"{self.listing_message} {self.group_title} closed as it is full")
            self.state.closed = True
            self.state.close_group_at = datetime_now_utc() + timedelta(
                minutes=self.state.editable_length
            )
            logging.debug(f"group closed but editable until {self.state.close_group_at}")
        elif self.state.empty_spots > 0 and self.state.closed:
            logging.debug(f"{self.listing_message} {self.group_title} reopened as it has space")
            self.state.closed = False
            self.state.close_group_at = datetime_now_utc() + timedelta(
                minutes=self.state.editable_length
            )
            logging.debug(f"group reopened and editable until {self.state.close_group_at}")

    # --- Responses and discord message display handling

    @property
    def _message_content(self):
        return {
            "content": self.listing_message,
            "embed": self.group_embed,
            "view": self.group_buttons,
        }

    async def send_message(self, interaction: discord.Interaction):
        """Sends the initial message for the Group Builder."""
        self.message = await interaction.channel.send(**self._message_content)  # type: ignore
        self._task = asyncio.create_task(self._check_if_closed_or_timed_out())

    async def edit_message(self):
        """Updates the Discord displayed message based on the current status of the group."""
        logging.debug("edit_message")
        await self.message.edit(**self._message_content)

    @property
    def passphrase(self) -> str:
        """Retrieves the passphrase for this group."""
        return self.state.passphrase

    async def send_passphrase(self, interaction: discord.Interaction):
        """Sends the passphrase."""
        logging.debug(
            f"send_passphrase {self.group_title}\n"
            f"user_id: {interaction.user.id}\n"
            f"display_name: {interaction.user.display_name}\n"
            f"passphrase: {self.passphrase}"
        )
        message_func = (
            interaction.followup.send
            if interaction.response.is_done()
            else interaction.response.send_message
        )
        await message_func(
            content=f"The passphrase for your group is: {self.passphrase}", ephemeral=True
        )

    # --- User creation

    def _create_filled_spot_user(self, role: str):
        return GroupUser(
            self.state.filled_spots * -1,
            "",
            "filled_spot",
            self.state.filled_spot_name,
            None,
            None,
            False,
            role,
        )

    def _create_empty_spot_user(self, role: str):
        return GroupUser(
            (self.state.empty_spots + 1000) * -1, "", "empty_spot", "", None, None, False, role
        )

    def create_user_from_interaction(
        self, interaction: discord.Interaction, role: str, creator: bool = False
    ):
        """Creates a GroupUser from a given discord interaction."""
        return GroupUser(
            id=interaction.user.id,
            tag=f"<@{interaction.user.id}>",
            name=interaction.user.name,
            display_name=interaction.user.display_name,
            global_name=interaction.user.global_name,
            interaction=interaction,
            creator=creator,
            role=role,
        )

    def get_user_by_id(self, user_id: int) -> GroupUser:
        """Retrieves a user from the roles using their id."""
        for role in self.roles.values():
            for user in role.users:
                if user_id == user.id:
                    return user
        raise ValueError("get_user_by_id was given user not in the current group")

    def get_role_by_id(self, user_id: int) -> GroupRole:
        """Retrieves a user from the roles using their id."""
        for role in self.roles.values():
            for user in role.users:
                if user_id == user.id:
                    return role
        raise ValueError("get_role_by_id was given user not in the current group")

    # --- Adding and removing users

    def fill_spots(self, filled_spots: dict[str, int]):
        """Fills spots in the listing based on the filled spots dictionary given."""
        for role_name, num_filled in filled_spots.items():
            for _ in range(num_filled):
                self.state.filled_spots += 1
                self.add_role(
                    assigned_role=role_name,
                    group_user=self._create_filled_spot_user(role_name),
                    filled_spot=True,
                )

    def remove_filled_spot(self, user: GroupUser):
        """Removes a filled spot from the given role."""
        self.state.filled_spots -= 1
        role = self.roles[user.role]
        self.remove_role(role, user.id)

    def remove_role(self, role: GroupRole, id: int):
        """Removes the role from the given user."""
        logging.debug(
            f"remove_role {self.group_title}\nrole: {role}\nid: {id}\nstate: {self.state}"
        )
        role_idx = [user.id for user in role.users].index(id)
        role.users[role_idx] = self._create_empty_spot_user(role.name)
        role.assigned[role_idx] = False
        role.disabled = False
        self.state.empty_spots += 1

    def add_role(self, assigned_role: str, group_user: GroupUser, filled_spot: bool = False):
        """Update the specified role name with the given user ID and display name."""
        # a user can only be present in a group once,
        # so must be removed if present before being added.
        if not filled_spot:
            for role_name in self.role_counts:
                remove_role = self.roles[role_name]
                if group_user.id in [user.id for user in remove_role.users]:
                    self.remove_role(remove_role, group_user.id)

        role = self.roles[assigned_role]
        logging.debug(
            f"add_role {self.group_title}\nrole: {role}\nid: {group_user.id}\nstate: {self.state}"
        )
        role_idx = role.assigned.index(False)
        role.users[role_idx] = (
            self._create_filled_spot_user(role.name) if filled_spot else group_user
        )
        role.assigned[role_idx] = True
        if all(role.assigned):
            role.disabled = True
        self.state.empty_spots -= 1

    # --- Buttons

    @property
    def current_user_ids(self) -> list[int]:
        """Retrieves the current valid user IDs in the instance."""
        ids = []
        for role_name in self.roles:
            for user in self.roles[role_name].users:
                ids.append(user.id)
        return ids

    @property
    def group_buttons(self) -> discord.ui.View | None:
        """A set of buttons for manipulating the group while it's open."""
        if self._is_finished or self.state.cancelled:
            logging.debug(f"no buttons needed {self.group_title}")
            return None
        logging.debug(f"retrieving buttons {self.group_title}")
        role_btns = [self._role_button(role_name) for role_name in self.role_counts]
        passphrase_btn = self._passphrase_button()
        settings_btn = self._settings_button()

        buttons = discord.ui.View()
        for element in role_btns + [passphrase_btn, settings_btn]:
            buttons.add_item(element)
        return buttons

    def _role_button(self, role_name: str) -> discord.ui.Button:
        """Creates a button interactable formatted for a particular role."""

        async def btn_click(interaction: discord.Interaction):
            logging.debug(
                f"{self.group_title} {role_name} button clicked by {interaction.user.display_name}"
            )
            if interaction.user.id in [user.id for user in self.kicked_users]:
                logging.debug(f"Sending kicked user message: {interaction.user.id}")
                for user in self.kicked_users:
                    if user.id == interaction.user.id:
                        removal_reason = user.removal_reason
                        await interaction.response.send_message(
                            f"You cannot rejoin a group you were removed from\nRemoval reason: {removal_reason}",
                            ephemeral=True,
                        )
                        return None
            if interaction.user.id == self.creator.id:
                logging.debug("Filling spots because creator clicked button")
                self.fill_spots({role_name: 1})
            else:
                logging.debug("Adding user because non-creator clicked button")
                self.add_role(
                    assigned_role=role_name,
                    group_user=self.create_user_from_interaction(interaction, role_name),
                )
            self.is_closed()
            await self.edit_message()
            if interaction.user.id != self.creator.id:
                await self.send_passphrase(interaction)
            if not interaction.response.is_done():
                await interaction.response.defer()

        role = self.role_info(role_name)
        btn = discord.ui.Button(
            custom_id=role.name,
            emoji=role.emoji,
            style=role.button_style,
            disabled=role.disabled,
            row=1,
        )
        btn.callback = btn_click
        return btn

    def _passphrase_button(self) -> discord.ui.Button:
        """Creates an ephemeral passphrase message for valid callers."""

        async def btn_click(interaction: discord.Interaction):
            logging.debug(
                f"{self.group_title} passphrase button clicked by {interaction.user.display_name}"
            )
            if interaction.user.id in self.current_user_ids:
                await self.send_passphrase(interaction)
            else:
                await interaction.response.send_message(
                    "You are not part of this group.", ephemeral=True
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
            logging.debug(
                f"{self.group_title} settings button clicked by {interaction.user.display_name}"
            )
            if interaction.user.id == self.creator.id:
                view = GroupEditOptions(self)
                content = (
                    f"\nMake changes to {self.group_title} below.\n"
                    f"**To cancel your group click the 'Cancel Group' button 2x.**"
                )
                await interaction.response.send_message(content=content, view=view, ephemeral=True)
                view.message = await interaction.original_response()  # type: ignore
                view.interaction = interaction
                await view.wait()
            elif interaction.user.id in self.current_user_ids:
                user_role = self.get_role_by_id(interaction.user.id)
                self.remove_role(user_role, interaction.user.id)
                self.is_closed()
                await self.edit_message()
                await interaction.response.send_message(
                    f"You have removed yourself from {self.group_title}.", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "You are not part of this group.", ephemeral=True
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


# --- Editing menus for DB instance (creator can access from settings)


class EditRemoveUser(discord.ui.Select):
    """Select which users to remove."""

    def __init__(self, users: dict[int, GroupUser]):
        """Initialisation."""
        disabled = True
        options = [discord.SelectOption(label="placeholder")]
        if len(users) > 0:
            options = [
                discord.SelectOption(
                    label=f"{group_user.role.capitalize()}: {group_user.display_name}",
                    value=f"{user_id}",
                )
                for user_id, group_user in users.items()
            ]
            disabled = False

        super().__init__(
            placeholder="Choose people to remove from the group",
            min_values=1,
            max_values=len(options),
            options=options,
            row=0,
            required=False,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        assert self.view is not None
        logging.debug(f"EditRemoveUser callback {self.view.group_builder.group_title}")
        for user_id in self.values:
            user_id = int(user_id)
            self.view.remove_users.append(self.view.group_builder.get_user_by_id(user_id))
        await interaction.response.defer()


class EditRemoveUserReason(discord.ui.Select):
    """Provide a reason for removing users."""

    def __init__(self, users: dict[int, GroupUser]):
        """Initialisation."""
        disabled = True
        options = [discord.SelectOption(label="placeholder")]
        if len(users) > 0 and any([user > 0 for user in users]):
            reasons = [
                "Low itemlevel",
                "Not experienced enough",
                "Want bloodlust",
                "Want combat resurrection",
                "Other - please message separately",
            ]
            options = [discord.SelectOption(label=reason) for reason in reasons]
            disabled = False

        super().__init__(
            placeholder="Choose a reason for removing people",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
            required=False,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        assert self.view is not None
        logging.debug(f"EditRemoveUserReason callback {self.view.group_builder.group_title}")
        if self.values:
            self.view.remove_users_reason = self.values[0]
        await interaction.response.defer()


class EditCreatorRole(discord.ui.Select):
    """Creator role selector."""

    def __init__(self, open_roles: list[str]):
        """Initialisation."""
        options = [discord.SelectOption(label=f"{role_name}") for role_name in open_roles]
        disabled = False
        placeholder = "Choose the role you want to swap to"
        if len(options) == 0:
            disabled = True
            options = [discord.SelectOption(label="placeholder")]
            placeholder = "All roles are full"

        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            row=2,
            required=False,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        assert self.view is not None
        logging.debug(f"EditCreatorRole callback {self.view.group_builder.group_title}")
        if self.values:
            self.view.new_creator_role = self.values[0]
        await interaction.response.defer()


class GroupEditOptions(discord.ui.View):
    """LFG options menu."""

    def __init__(self, group_builder: GroupBuilder):
        """Initialisation."""
        super().__init__(timeout=60)
        self.message: discord.InteractionMessage = None  # type: ignore
        self.interaction: discord.Interaction = None  # type: ignore
        self.group_builder = group_builder
        self.filled_spot_name = self.group_builder.state.filled_spot_name
        removeable_users = {}
        for role_name, role_item in self.group_builder.roles.items():
            for user in role_item.users:
                if user.creator:
                    self.creator_role = role_name
                elif user.id > -100:
                    removeable_users[user.id] = user
        self.new_creator_role = self.creator_role
        self.open_roles = [
            role.name for role in self.group_builder.roles.values() if not all(role.assigned)
        ]
        self.remove_users: list[GroupUser] = []
        self.remove_users_reason = ""
        self.confirmed = False
        self.cancel_group_state = 0

        self.edit_remove_users = EditRemoveUser(removeable_users)
        self.edit_remove_users_reason = EditRemoveUserReason(removeable_users)
        self.edit_creator_role = EditCreatorRole(self.open_roles)

        self.add_item(self.edit_remove_users)
        self.add_item(self.edit_remove_users_reason)
        self.add_item(self.edit_creator_role)

    def _remove_users(self) -> bool | None:
        logging.debug(f"Attempting to remove users from {self.group_builder.group_title}")
        logging.debug(f"remove users: {self.remove_users}")
        if len(self.remove_users) > 0:
            logging.debug(f"users_to_remove: {self.remove_users}")
            logging.debug(f"{[user.id > 0 for user in self.remove_users]}")
            is_not_all_filled = any([user.id > 0 for user in self.remove_users])
            logging.debug(
                f"is_not_all_filled: {is_not_all_filled}, "
                f"self.remove_users_reason: {self.remove_users_reason}"
            )
            if is_not_all_filled and self.remove_users_reason == "":
                return False
            for user in self.remove_users:
                if user.id < 0:
                    self.group_builder.remove_filled_spot(user)
                else:
                    self.group_builder.remove_role(self.group_builder.roles[user.role], user.id)
                    user.removal_reason = self.remove_users_reason
                    self.group_builder.kicked_users.append(user)
            self.group_builder.is_closed()
            return True
        return None

    def _change_creator_role(self):
        if self.new_creator_role != self.creator_role:
            if all(self.group_builder.roles[self.new_creator_role].assigned):
                return False
            else:
                self.group_builder.add_role(self.new_creator_role, self.group_builder.creator)
            return True
        return None

    @discord.ui.button(label="Confirm changes", style=discord.ButtonStyle.green, row=4)
    async def confirm_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm the edits."""
        self.confirmed = True
        is_creator_role_swapped = self._change_creator_role()
        is_removed_users = self._remove_users()
        self.group_builder.is_closed()
        await self.group_builder.edit_message()
        logging.debug(
            f"edit confirm {self.group_builder.group_title}: {is_creator_role_swapped}, {is_removed_users}"
        )

        return_content = "Editing complete."

        if is_creator_role_swapped is not None and not is_creator_role_swapped:
            logging.debug("not is_creator_role_swapped")
            await self.interaction.followup.send(
                content="The role you wanted to swap to is no longer available", ephemeral=True
            )
            await interaction.response.defer()
            return None
        elif is_creator_role_swapped is not None:
            logging.debug("is_creator_role_swapped is not None")
            return_content += (
                f"\nCreator role swapped from {self.creator_role} to {self.new_creator_role}"
            )

        if is_removed_users is not None and not is_removed_users:
            logging.debug("not is_removed_users")
            await self.interaction.followup.send(
                content="You must provide a removal reason if you are removing users",
                ephemeral=True,
            )
            await interaction.response.defer()
            return None
        elif is_removed_users is not None:
            logging.debug("is_removed_users is not None")
            users_removed_str = [
                f"- `{user.display_name}`: {user.removal_reason}" for user in self.remove_users
            ]
            users_removed_str = "\n".join(users_removed_str)
            return_content += f"\nUsers removed: \n{users_removed_str}"
            for user in self.remove_users:
                if user.id > 0:
                    assert user.interaction is not None
                    message_func = (
                        user.interaction.followup.send
                        if user.interaction.response.is_done()
                        else user.interaction.response.send_message
                    )
                    await message_func(
                        content=(
                            f"{user.tag} You have been removed from the group with the reason: "
                            f"{user.removal_reason}"
                        ),
                        ephemeral=True,
                    )

        await self.message.edit(content=return_content, view=None)  # type: ignore
        self.stop()

    @discord.ui.button(label="Abort changes", style=discord.ButtonStyle.secondary, row=4)
    async def cancel_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the menu."""
        self.confirmed = False
        await self.message.edit(content="Group editing cancelled.", view=None)  # type: ignore
        self.stop()

    @discord.ui.button(label="Cancel group", style=discord.ButtonStyle.danger, row=4)
    async def cancel_group(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the menu."""
        self.cancel_group_state += 1
        self.confirmed = False
        if self.cancel_group_state == 2:
            await self.message.edit(content="Group cancelled.", view=None)  # type: ignore
            await self.group_builder.cancel_group()
            self.stop()
        else:
            await interaction.response.defer()

    async def on_timeout(self) -> None:
        """Do stuff when timeout occurs."""
        logging.debug("edit menu timed out.")
        if self.message:
            await self.message.edit(content="Group editing has timed out.", view=None)  # type: ignore
        self.stop()

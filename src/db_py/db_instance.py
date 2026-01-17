"""Main DB instance control."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import discord

from db_py.resources import generate_listing_name, generate_passphrase, load_emojis
from db_py.roles import RoleSpecific, RoleType


def timestamp():
    """Returns an iso formatted timestamp."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Role:
    """Container for a particular role type."""
    name: RoleType
    userids: list[int]
    display_names: list[str]
    assigned: list[bool]
    button_style: discord.ButtonStyle
    disabled: bool
    emoji: str


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
    chosen_role: RoleSpecific


@dataclass
class DungeonState:
    """Container for the state of the dungeon."""
    created_at: datetime
    timeout_length: timedelta
    empty_spots: int
    passphrase: str
    filled_spot_name: str
    debug: bool


class DungeonInstance:
    """Container for the primary information relating to a dungeon instance."""

    def __init__(self, interaction: discord.Interaction, dungeon_info: dict, config: dict):
        """Creates a DungeonInstance.

        Args:
            interaction: The discord interaction which created this DungeonInstance. This allows
                us to capture the user information depending on who created this instance.
            dungeon_info: A dictionary of the dungeon specific information
            config: A dictionary of configuration information for Dungeon Buddy
        """
        self._setup_dungeon(**dungeon_info, config=config)
        self._roles_init(config.get("emojis", load_emojis()))
        self._state_init(config)
        self._interaction_init(interaction)

    # --- Properties

    @property
    def creator(self) -> DungeonUser:
        """Returns the user that created this."""
        return self.interactions["creator"]

    @property
    def current_users(self) -> list:
        """Retrieves the current valid user IDs in the instance."""
        tank_id = self.roles[RoleType.tank.name].userids[0]
        healer_id = self.roles[RoleType.healer.name].userids[0]
        dps_ids = self.roles[RoleType.dps.name].userids
        return [tank_id] + [healer_id] + dps_ids

    @property
    def description(self) -> str:
        """Gets a standardised description for the dungeon including role spots."""
        dungeon = self.dungeon_details
        tank = self.roles[RoleType.tank.name]
        healer = self.roles[RoleType.healer.name]
        dps = self.roles[RoleType.dps.name]
        footer = ""
        if self.state.empty_spots > 0:
            footer = "`/lfghelp for Dungeon Buddy help`"

        return f"""{dungeon.creator_notes}

{tank.emoji} : {tank.display_names[0]}{'🚩' if tank.userids[0] == self.creator.id else ''}
{healer.emoji} : {healer.display_names[0]}{'🚩' if healer.userids[0] == self.creator.id else ''}
{dps.emoji} : {dps.display_names[0]}{'🚩' if dps.userids[0] == self.creator.id else ''}
{dps.emoji} : {dps.display_names[1]}{'🚩' if dps.userids[1] == self.creator.id else ''}
{dps.emoji} : {dps.display_names[2]}{'🚩' if dps.userids[2] == self.creator.id else ''}
{footer}"""

    @property
    def dungeon_title(self) -> str:
        """Gets a standardised title string for the dungeon."""
        return f"{self.dungeon_details.listed_as}"

    @property
    def listing_message(self) -> str:
        """Gets a standardised listing title for the dungeon including difficulty and time type."""
        dungeon = self.dungeon_details
        return f"{dungeon.dungeon_long} +{dungeon.difficulty} ({dungeon.time_type})"

    @property
    def passphrase(self) -> str:
        """Retrieves the passphrase for this dungeon instance."""
        return self.state.passphrase

    # --- General methods

    def role_info(self, role_name):
        """Gets information about the requested role."""
        if role_name in self.roles:
            return self.roles[role_name]
        else:
            raise ValueError(f"{role_name} not in roles: {list(self.roles.keys())}")

    # --- Initialisation

    def _roles_init(self, emojis: dict):
        """Initialise roles information."""
        self.roles = {
            "tank": Role(
                name=RoleType.tank,
                userids=[0],
                display_names=[""],
                assigned=[False],
                button_style=discord.ButtonStyle.secondary,
                disabled=False,
                emoji=emojis[RoleType.tank.name],
            ),
            "healer": Role(
                name=RoleType.healer,
                userids=[0],
                display_names=[""],
                assigned=[False],
                button_style=discord.ButtonStyle.secondary,
                disabled=False,
                emoji=emojis[RoleType.healer.name],
            ),
            "dps": Role(
                name=RoleType.dps,
                userids=[0, 0, 0],
                display_names=["", "", ""],
                assigned=[False, False, False],
                button_style=discord.ButtonStyle.secondary,
                disabled=False,
                emoji=emojis[RoleType.dps.name],
            )
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
            creator_notes="" if (creator_notes == "") else f"**Notes:** *{creator_notes}*",
            difficulty=int(difficulty),
            time_type=time_type,
        )

    def _state_init(self, config: dict):
        """Initialise state."""
        guild_name = config.get("guild_name", "")
        timeout_length = config.get("timeout_length", 30)
        debug = config.get("debug", False)
        self.state = DungeonState(
            created_at=datetime.now(tz=timezone.utc),
            timeout_length=timedelta(minutes=timeout_length),
            empty_spots=5,
            passphrase=generate_passphrase(),
            filled_spot_name=f"~~Filled {guild_name}{' ' if guild_name != '' else ''}Spot~~",
            debug=bool(debug)
        )

    def _interaction_init(self, interaction: discord.Interaction):
        """Initialise interaction elements."""
        self.interactions = {
            "id": interaction.id,
            "creator": _create_dungeon_user(interaction=interaction, chosen_role=RoleSpecific.none)
        }

    # --- Responses and discord message display handling

    async def send_passphrase(self, interaction: discord.Interaction, followup: bool = False):
        """Sends the passphrase."""
        if self.state.debug:
            print(f"{timestamp()}: send_passphrase", interaction.user.id, interaction.user.display_name, self.passphrase)
        message_func = interaction.followup.send if followup else interaction.response.send_message
        await message_func(
            content=f"The passphrase for your group is: {self.passphrase}",
            ephemeral=True
        )

    async def update_role(self, assigned_role: str, interaction: discord.Interaction):
        """Update the specified role name with the given user ID and display name."""
        if self.state.debug:
            print(f"{timestamp()}: update_role", interaction.user.id, interaction.user.display_name, assigned_role)
        role = self.roles[assigned_role]
        userid = interaction.user.id

        for role_name in [name.name for name in RoleType]:
            remove_role = self.roles[role_name]
            if userid in remove_role.userids:
                role_idx = remove_role.userids.index(userid)
                remove_role.userids[role_idx] = 0
                remove_role.display_names[role_idx] = ""
                remove_role.assigned[role_idx] = False
                remove_role.disabled = False
                self.state.empty_spots += 1

        role_idx = role.assigned.index(False)
        role.userids[role_idx] = userid
        role.display_names[role_idx] = interaction.user.display_name
        role.assigned[role_idx] = True
        if all(role.assigned):
            role.disabled = True
        self.state.empty_spots -= 1

    async def update_display(self, interaction: discord.Interaction):
        """Updates the Discord displayed message based on the current status of the instance."""
        if self.state.debug:
            print(f"{timestamp()}: update_display", interaction.user.id, interaction.user.display_name)
        await interaction.response.edit_message(
            embed=self._dungeon_embed,
            view=self._dungeon_buttons,
        )

    @property
    def _dungeon_embed(self) -> discord.Embed:
        return discord.Embed(
            title=self.dungeon_title,
            description=self.description,
            colour=606675,
        )

    @property
    def _dungeon_buttons(self) -> discord.ui.View:
        tank_btn = self._role_button(RoleType.tank)
        healer_btn = self._role_button(RoleType.healer)
        dps_btn = self._role_button(RoleType.dps)
        passphrase_btn = self._passphrase_button()

        buttons = discord.ui.View()
        for element in [tank_btn, healer_btn, dps_btn, passphrase_btn]:
            buttons.add_item(element)
        return buttons

    @property
    def listing_message_full(self) -> dict:
        """Creates all elements of a discord message for the dungeon instance."""
        return {
            "content": self.listing_message,
            "embed": self._dungeon_embed,
            "view": self._dungeon_buttons,
        }

    def _role_button(self, role_type: RoleType) -> discord.ui.Button:
        """Creates a button interactable formatted for a particular role."""
        async def btn_click(interaction: discord.Interaction):
            await self.update_role(assigned_role=role_type.name, interaction=interaction)
            await self.update_display(interaction)
            await self.send_passphrase(interaction, True)

        role = self.role_info(role_type.name)
        btn = _button_from_role(role, 1)
        btn.callback = btn_click
        return btn

    def _passphrase_button(self) -> discord.ui.Button:
        """Creates an ephemeral passphrase message for valid callers."""
        async def btn_click(interaction: discord.Interaction):
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


def _create_dungeon_user(interaction: discord.Interaction, chosen_role: RoleSpecific):
    return DungeonUser(
        id=interaction.user.id,
        tag=f"<@{interaction.user.id}>",
        name=interaction.user.name,
        display_name=interaction.user.display_name,
        global_name=interaction.user.global_name,
        chosen_role=chosen_role,
    )


def _button_from_role(role: Role, row: int) -> discord.ui.Button:
    return discord.ui.Button(
        custom_id=role.name.name,
        emoji=role.emoji,
        style=role.button_style,
        disabled=role.disabled,
        row=row
    )

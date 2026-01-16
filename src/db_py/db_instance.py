"""Main DB instance control."""

from dataclasses import dataclass

import discord

from db_py.resources import generate_listing_name, generate_passphrase, load_emojis
from db_py.roles import RoleSpecific, RoleType


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
class DBUser:
    """Container for discord user information relevant to Dungeon Buddy."""
    id: int
    tag: str
    name: str
    display_name: str
    global_name: str | None
    chosen_role: RoleSpecific


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
        self._meta_init(config)
        self._interaction_init(interaction)

    # --- Properties

    @property
    def creator(self) -> DBUser:
        """Returns the user that created this."""
        return self.interactions["creator"]

    @property
    def description(self):
        """Gets a standardised description for the dungeon including role spots."""
        dungeon = self.dungeon_details
        tank = self.roles[RoleType.tank.name]
        healer = self.roles[RoleType.healer.name]
        dps = self.roles[RoleType.dps.name]
        footer = ""
        if self.metadata["filled_spot_counter"] < 5:
            footer = "`/lfghelp for Dungeon Buddy help`"

        return f"""{dungeon.creator_notes}

{tank.emoji} : {tank.display_names[0]}{'🚩' if tank.userids[0] == self.creator.id else ''}
{healer.emoji} : {healer.display_names[0]}{'🚩' if healer.userids[0] == self.creator.id else ''}
{dps.emoji} : {dps.display_names[0]}{'🚩' if dps.userids[0] == self.creator.id else ''}
{dps.emoji} : {dps.display_names[1]}{'🚩' if dps.userids[1] == self.creator.id else ''}
{dps.emoji} : {dps.display_names[2]}{'🚩' if dps.userids[2] == self.creator.id else ''}
{footer}"""

    @property
    def dungeon_title(self):
        """Gets a standardised title string for the dungeon."""
        return f"{self.dungeon_details.listed_as}"

    @property
    def listing_message(self):
        """Gets a standardised listing title for the dungeon including difficulty and time type."""
        dungeon = self.dungeon_details
        return f"{dungeon.dungeon_long} +{dungeon.difficulty} ({dungeon.time_type})"

    @property
    def passphrase(self):
        """Retrieves the passphrase for this dungeon instance."""
        return self.metadata.get("passphrase")

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
            listed_as="" if (listed_as != "") else random_listing,
            creator_notes="" if (creator_notes == "") else f"**Notes:** *{creator_notes}*",
            difficulty=int(difficulty),
            time_type=time_type,
        )

    def _meta_init(self, config: dict):
        """Initialise metadata."""
        guild_name = config.get("guild_name", "")
        self.metadata = {
            "spot_icons": [],
            "filled_spot": f"~~Filled {guild_name}{' ' if guild_name != '' else ''}Spot~~",
            "filled_spot_counter": 0,
            "roles_to_tag": "",
            "passphrase": generate_passphrase(),
        }

    def _interaction_init(self, interaction: discord.Interaction):
        """Initialise interaction elements."""
        self.interactions = {
            "id": interaction.id,
            "creator": _create_db_user(interaction=interaction, chosen_role=RoleSpecific.none)
        }

    # --- Responses and discord message display handling

    async def send_passphrase(self, interaction: discord.Interaction, followup: bool = False):
        """Sends the passphrase."""
        message_func = interaction.followup.send if followup else interaction.response.send_message
        await message_func(
            content=f"The passphrase for your group is: {self.passphrase}",
            ephemeral=True
        )

    async def update_role(self, role_name: str, interaction: discord.Interaction):
        """Update the specified role name with the given user ID and display name."""
        role = self.roles[role_name]
        if role_name in ["tank", "healer"]:
            role.userids[0] = interaction.user.id
            role.display_names[0] = interaction.user.display_name
            role.assigned = [True]
            role.disabled = True
        else:
            role_idx = role.assigned.index(False)
            role.userids[role_idx] = interaction.user.id
            role.display_names[role_idx] = interaction.user.display_name
            role.assigned[role_idx] = True
            if role.assigned == [True, True, True]:
                role.disabled = True

    async def update_display(self, interaction: discord.Interaction):
        """Updates the Discord displayed message based on the current status of the instance."""
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

        buttons = discord.ui.View()
        for element in [tank_btn, healer_btn, dps_btn]:
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
            await self.update_role(role_name=role_type.name, interaction=interaction)
            await self.update_display(interaction)
            await self.send_passphrase(interaction, True)

        role = self.role_info(role_type.name)
        btn = _button_from_role(role, 1)
        btn.callback = btn_click
        return btn


def _create_db_user(interaction: discord.Interaction, chosen_role: RoleSpecific):
    return DBUser(
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

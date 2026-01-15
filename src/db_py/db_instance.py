"""Main DB instance control."""

from dataclasses import dataclass
from enum import Enum

import discord

from db_py.resources import generate_passphrase

DEFAULT_EMOJIS = {
    "tank": ":shield:",
    "dps": ":crossed_swords:",
    "healer": ":magic_wand:",
}


class RoleType(Enum):
    """Enumeration for role types."""
    tank = 1
    healer = 2
    dps = 3


class RoleSpecific(Enum):
    """Enumeration for the role a particular user has been assigned."""
    tank = 1
    healer = 2
    dps1 = 3
    dps2 = 4
    dps3 = 5
    none = 0


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
        self._setup_dungeon(**dungeon_info)
        self._roles_init(config.get("emojis", DEFAULT_EMOJIS))
        self._meta_init(config)
        self._interaction_init(interaction)

    @property
    def listing_title(self):
        """Gets a standardised listing title for the dungeon including difficulty and time type."""
        dungeon = self.dungeon_details
        return f"{dungeon['dungeon_long']} +{dungeon['difficulty']} ({dungeon['time_type']})"

    @property
    def dungeon_title(self):
        """Gets a standardised title string for the dungeon."""
        return f"{self.dungeon_details['listed_as']}"

    @property
    def description(self):
        """Gets a standardised description for the dungeon including role spots."""
        dungeon = self.dungeon_details
        tank = self.roles[RoleType.tank.name]
        healer = self.roles[RoleType.healer.name]
        dps = self.roles[RoleType.dps.name]
        footer = ""
        if self.metadata["filled_spot_counter"] < 5:
            footer = "/lfghelp for Dungeon Buddy help"
        return f"""{dungeon['creator_notes']}

            {tank.emoji} : {tank.display_names[0]}
            {healer.emoji} : {healer.display_names[0]}
            {dps.emoji} : {dps.display_names[0]}
            {dps.emoji} : {dps.display_names[1]}
            {dps.emoji} : {dps.display_names[2]}
            {footer}"""

    def role_info(self, role_name):
        """Gets information about the requested role."""
        if role_name in self.roles:
            return self.roles[role_name]
        else:
            raise ValueError(f"{role_name} not in roles: {list(self.roles.keys())}")

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
        time_type: str
    ):
        """Captures information from the initial listing process."""
        self.dungeon_details = {}
        self.dungeon_details["dungeon_short"] = dungeon_short
        self.dungeon_details["dungeon_long"] = dungeon_long
        self.dungeon_details["listed_as"] = listed_as
        self.dungeon_details["creator_notes"] = creator_notes
        self.dungeon_details["difficulty"] = difficulty
        self.dungeon_details["time_type"] = time_type

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
            "user": _create_db_user(interaction=interaction, chosen_role=RoleSpecific.none)
        }

    def update_role(self, role_name: str, user_id: int, display_name: str):
        """Update the specified role name with the given user ID and display name."""
        if role_name in ["tank", "healer"]:
            self.roles[role_name].userids[0] = user_id
            self.roles[role_name].display_names[0] = display_name
        elif _valid_dps_role(role_name):
            role_idx = int(role_name[-1]) - 1
            self.roles[role_name].userids[role_idx] = user_id
            self.roles[role_name].display_names[role_idx] = display_name


def _valid_dps_role(role_name: str):
    return bool(
        role_name[:3] == "dps"
        and len(role_name) == 4
        and role_name[-1].isdigit()
        and int(role_name[-1]) > 0
        and int(role_name[-1]) < 4
    )


def _create_db_user(interaction: discord.Interaction, chosen_role: RoleSpecific):
    return DBUser(
        id=interaction.user.id,
        tag=f"<@{interaction.user.id}>",
        name=interaction.user.name,
        display_name=interaction.user.display_name,
        global_name=interaction.user.global_name,
        chosen_role=RoleSpecific.none,
    )

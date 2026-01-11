"""Main DB instance control."""

import discord

from db_py.resources import generate_passphrase

DEFAULT_EMOJIS = {
    "tank": ":shield:",
    "dps": ":crossed_swords:",
    "healer": ":magic_wand:",
}


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
        tank = self.roles["tank"]
        healer = self.roles["healer"]
        dps1 = self.roles["dps1"]
        dps2 = self.roles["dps2"]
        dps3 = self.roles["dps3"]
        footer = ""
        if self.metadata["filled_spot_counter"] < 5:
            footer = "/lfghelp for Dungeon Buddy help"
        return f"""{dungeon['creator_notes']}

            {tank["emoji"]} : {tank["display_name"]}
            {healer["emoji"]} : {healer["display_name"]}
            {dps1["emoji"]} : {dps1["display_name"]}
            {dps2["emoji"]} : {dps2["display_name"]}
            {dps3["emoji"]} : {dps3["display_name"]}
            {footer}"""

    def _roles_init(self, emojis: dict):
        """Initialise roles information."""
        self.roles = {
            "tank": {
                "userid": 0,
                "display_name": "",
                "assigned": False,
                "buttonstyle": discord.ButtonStyle.secondary,
                "disabled": False,
                "emoji": emojis["tank"],
            },
            "healer": {
                "userid": 0,
                "display_name": "",
                "assigned": False,
                "buttonstyle": discord.ButtonStyle.secondary,
                "disabled": False,
                "emoji": emojis["healer"],
            },
            "dps1": {
                "userid": 0,
                "display_name": "",
                "assigned": False,
                "buttonstyle": discord.ButtonStyle.secondary,
                "disabled": False,
                "emoji": emojis["dps"],
            },
            "dps2": {
                "userid": 0,
                "display_name": "",
                "emoji": emojis["dps"],
            },
            "dps3": {
                "userid": 0,
                "display_name": "",
                "emoji": emojis["dps"],
            }
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
            "user": {
                "id": interaction.user.id,
                "tag": f"<@{interaction.user.id}>",
                "name": interaction.user.name,
                "display_name": interaction.user.display_name,
                "global_name": interaction.user.global_name,
                "chosen_role": "",
            }
        }

    def update_role(self, role_name: str, user_id: int, display_name: str):
        """Update the specified role name with the given user ID and display name."""
        self.roles[role_name]["user_id"] = user_id
        self.roles[role_name]["display_name"] = display_name

"""Main DB instance control."""

import discord

from db_py.resources import generate_passphrase, load_emojis

EMOJIS = load_emojis()


class DungeonInstance:
    """Container for the primary information relating to a dungeon instance."""

    def __init__(self, interaction: discord.Interaction):
        """Init."""
        self._roles_init()
        self._meta_init()
        self._interaction_init(interaction)

    def _roles_init(self):
        """Initialise roles information."""
        self.roles = {
            "tank": {
                "userid": 0,
                "display_name": "",
                "assigned": False,
                "buttonstyle": discord.ButtonStyle.secondary,
                "disabled": False,
                "emoji": EMOJIS["tank"],
            },
            "healer": {
                "userid": 0,
                "display_name": "",
                "assigned": False,
                "buttonstyle": discord.ButtonStyle.secondary,
                "disabled": False,
                "emoji": EMOJIS["healer"],
            },
            "dps1": {
                "userid": 0,
                "display_name": "",
                "assigned": False,
                "buttonstyle": discord.ButtonStyle.secondary,
                "disabled": False,
                "emoji": EMOJIS["dps"],
            },
            "dps2": {
                "userid": 0,
                "display_name": "",
                "emoji": EMOJIS["dps"],
            },
            "dps3": {
                "userid": 0,
                "display_name": "",
                "emoji": EMOJIS["dps"],
            }
        }

    def update_role(self, role_name: str, user_id: int, display_name: str):
        """Update the specified role name with the given user ID and display name."""
        self.roles[role_name]["user_id"] = user_id
        self.roles[role_name]["display_name"] = display_name

    def _meta_init(self):
        """Initialise metadata."""
        self.metadata = {
            "dungeon_name": "",
            "listed_as": "",
            "creator_notes": "",
            "dungeon_difficulty": "",
            "time_type": "",
            "spot_icons": [],
            "filled_spot": "~~Filled NoP Spot~~",
            "filled_spot_counter": 0,
            "roles_to_tag": "",
            "passphrase": generate_passphrase(),
        }

    def setup_dungeon(
        self,
        dungeon_name: str,
        listed_as: str,
        creator_notes: str,
        dungeon_difficulty: int,
        time_type: str
    ):
        """Captures information from the initial listing process."""
        self.metadata["dungeon_name"] = dungeon_name
        self.metadata["listed_as"] = listed_as
        self.metadata["creator_notes"] = creator_notes
        self.metadata["dungeon_difficulty"] = dungeon_difficulty
        self.metadata["time_type"] = time_type

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

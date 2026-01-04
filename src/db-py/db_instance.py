"""Main DB instance control."""

import discord


class Dungeon:
    """Container for the primary information relating to a dungeon instance."""

    def __init__(self, interaction: discord.Interaction):
        """Init."""
        self.roles = self._roles_init()
        self.metadata = self._meta_init()

    def _roles_init(self):
        """Initialise roles information."""
        tank = {
            "userid": 0,
            "name": "",
            "assigned": False,
            "buttonstyle": discord.ButtonStyle.secondary,
            "disabled": False,
            "emoji": ":tankrole:"
        }
        return tank

    def _meta_init(self):
        """Initialise metadata."""

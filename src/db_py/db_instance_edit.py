"""Editing system for active dungeon instance."""

import logging

import discord

from db_py.db_instance import DungeonInstance


class RemoveUser(discord.ui.Select):
    """Creator role selector."""
    def __init__(self, users: dict[str, tuple[str, int]]):
        """Initialisation."""
        options = [
            discord.SelectOption(label=f"{userinfo[0]}: {user}", value=user)
            for user, userinfo
            in users.items()
        ]

        super().__init__(
            placeholder="Select the people you want to remove from the group",
            min_values=0,
            max_values=4,
            options=options,
            row=0,
            required=False,
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        logging.debug("creator callback")
        assert self.view is not None
        self.view.remove_users = self.values
        await interaction.response.defer()


class DBEditOptions(discord.ui.View):
    """LFG options menu."""
    def __init__(self, db_instance: DungeonInstance):
        """Initialisation."""
        super().__init__(timeout=120)
        self.db_instance = db_instance
        self.creator_role = db_instance.current_user_roles[db_instance.creator.display_name][0]
        self.new_creator_role = self.creator_role
        self.remove_users = []
        self.confirmed = False

        self.edit_remove_users = RemoveUser(db_instance.current_user_roles)

        self.add_item(self.edit_remove_users)

    @discord.ui.button(label="Confirm changes", style=discord.ButtonStyle.green, row=4)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm the edits."""
        self.confirmed = True
        if len(self.remove_users) > 0:
            for user in self.remove_users:
                self.db_instance.remove_role(
                    self.db_instance.roles[self.db_instance.current_user_roles[user][0]], user)
        await interaction.response.edit_message(content="Changes applied.", view=None)
        self.stop()

    @discord.ui.button(label="Abort changes", style=discord.ButtonStyle.secondary, row=4)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the menu."""
        self.confirmed = False
        await interaction.response.edit_message(content="Group editing cancelled.", view=None)
        self.stop()

    # add cancel button

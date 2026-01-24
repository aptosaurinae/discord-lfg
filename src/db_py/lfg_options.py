"""Contains the system for doing LFG related interactions."""

import logging

import discord

from db_py.db_instance import DungeonInstance
from db_py.resources import load_emojis, load_time_types
from db_py.roles import RoleType


class LFGDifficulty(discord.ui.Select):
    """Difficulty selector."""
    def __init__(self, difficulties: list[int]):
        """Initialisation."""
        options = [discord.SelectOption(label=str(num)) for num in difficulties]

        super().__init__(
            placeholder="Select a difficulty",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        logging.debug("difficulty callback")
        assert self.view is not None
        self.view.difficulty = int(self.values[0])
        await interaction.response.defer()


class LFGTimeType(discord.ui.Select):
    """Time type selector."""
    def __init__(self):
        """Initialisation."""
        options = [discord.SelectOption(label=value) for value in load_time_types().values()]

        super().__init__(
            placeholder="Trying to Time or Complete?",
            min_values=1,
            max_values=1,
            options=options,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        logging.debug("time type callback")
        assert self.view is not None
        self.view.time_type = self.values[0]
        await interaction.response.defer()


class LFGCreatorRole(discord.ui.Select):
    """Creator role selector."""
    def __init__(self, emojis: dict,):
        """Initialisation."""
        options = [
            discord.SelectOption(
                label=value.name.capitalize(), value=value.name, emoji=emojis[value.name])
            for value in RoleType
        ]

        super().__init__(
            placeholder="Select your role",
            min_values=1,
            max_values=1,
            options=options,
            row=2
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        logging.debug("creator callback")
        assert self.view is not None
        self.view.creator_role = self.values[0]
        self.view._update_roles_required_selector()
        await interaction.response.edit_message(view=self.view)


class LFGRolesRequired(discord.ui.Select):
    """Roles required selector."""
    def __init__(self, emojis: dict, creator_role: str | None = None):
        """Initialisation."""
        if creator_role is None:
            logging.debug("roles required not given creator role")
            max_values = 1
            options = [discord.SelectOption(label="Choose your role first.")]
        else:
            logging.debug("creator role chosen, updating role required dropdown")
            max_values = 4
            role_counts = DungeonInstance.role_counts.copy()
            role_counts[creator_role] -= 1
            options = [
                discord.SelectOption(label=key.capitalize(), value=f"{key}_{idx}", emoji=emojis[key])
                for key, value
                in role_counts.items()
                for idx in range(value)
            ]

        super().__init__(
            placeholder="Select the roles you require",
            min_values=1,
            max_values=max_values,
            options=options,
            row=3
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        logging.debug("roles required callback")
        assert self.view is not None
        required_roles = {role.name: 0 for role in RoleType}
        for item in self.values:
            item_name = item.split("_")[0]
            required_roles[item_name] += 1
        self.view.required_roles = required_roles
        await interaction.response.defer()


class LFGOptions(discord.ui.View):
    """LFG options menu."""
    def __init__(self, difficulties: list[int], config: dict):
        """Initialisation."""
        super().__init__(timeout=120)
        self.difficulty = 0
        self.time_type = ""
        self.creator_role = ""
        self.required_roles = {}
        self.confirmed = False
        self.emojis = config.get("emojis", load_emojis())

        self.lfg_difficulties = LFGDifficulty(difficulties)
        self.lfg_time_types = LFGTimeType()
        self.lfg_creator_role = LFGCreatorRole(self.emojis)
        self.lfg_roles_required = LFGRolesRequired(self.emojis)

        self.add_item(self.lfg_difficulties)
        self.add_item(self.lfg_time_types)
        self.add_item(self.lfg_creator_role)
        self.add_item(self.lfg_roles_required)

    @discord.ui.button(label="Create group", style=discord.ButtonStyle.green, row=4)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm the menu selections."""
        if not (
            self.difficulty == 0
            and self.time_type == ""
            and self.creator_role == ""
            and self.required_roles == {}
        ):
            self.confirmed = True
            await interaction.response.edit_message(content="Group created.", view=None)
            self.stop()

    @discord.ui.button(label="Cancel creation", style=discord.ButtonStyle.red, row=4)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the menu."""
        self.confirmed = False
        await interaction.response.edit_message(content="Group creation cancelled.", view=None)
        self.stop()

    def _restore_options(self, select: discord.ui.Select, current_selection):
        logging.debug(f"restoring options for {select}: {current_selection}")
        for opt in select.options:
            opt.default = (opt.value == str(current_selection))
        logging.debug([(item.value, item.default) for item in select.options])

    def _update_roles_required_selector(self):
        if not self.creator_role:
            max_values = 1
            options = [discord.SelectOption(label="Choose your role first.")]
        else:
            max_values = 4
            role_counts = DungeonInstance.role_counts.copy()
            role_counts[self.creator_role] -= 1
            options = [
                discord.SelectOption(
                    label=key.capitalize(), value=f"{key}_{idx}", emoji=self.emojis[key])
                for key, value in role_counts.items()
                for idx in range(value)
            ]

        self.lfg_roles_required.options = options
        self.lfg_roles_required.max_values = max_values
        self._restore_options(self.lfg_difficulties, self.difficulty)
        self._restore_options(self.lfg_time_types, self.time_type)
        self._restore_options(self.lfg_creator_role, self.creator_role)

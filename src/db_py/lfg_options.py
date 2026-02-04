"""Contains the system for doing LFG related interactions."""

import logging

import discord

from db_py.resources import load_time_types
from db_py.roles import RoleDefinition


class LFGDifficulty(discord.ui.Select):
    """Difficulty selector."""

    def __init__(self, difficulties: list[int]):
        """Initialisation."""
        options = [discord.SelectOption(label=str(num)) for num in difficulties]
        if len(options) == 1:
            options[0].default = True

        super().__init__(
            placeholder="Select a difficulty",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
            disabled=len(options) == 1,
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
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        logging.debug("time type callback")
        assert self.view is not None
        self.view.time_type = self.values[0]
        await interaction.response.defer()


class LFGCreatorRole(discord.ui.Select):
    """Creator role selector."""

    def __init__(self, roles: dict[str, RoleDefinition]):
        """Initialisation."""
        options = [
            discord.SelectOption(
                label=role_info.name.capitalize(), value=role_info.name, emoji=role_info.emoji
            )
            for role_info in roles.values()
        ]

        super().__init__(
            placeholder="Select your role", min_values=1, max_values=1, options=options, row=2
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

    def __init__(self, roles: dict[str, RoleDefinition], creator_role: str | None = None):
        """Initialisation."""
        max_values, options, disabled, placeholder = self._get_roles_required_info(
            roles, creator_role
        )

        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=max_values,
            options=options,
            row=3,
            disabled=disabled,
        )

    def _get_roles_required_info(
        self, roles: dict[str, RoleDefinition], creator_role: str | None = None
    ):
        if creator_role is None:
            logging.debug("roles required not given creator role")
            max_values = 1
            options = [discord.SelectOption(label="Choose your role first.")]
            disabled = True
            placeholder = "Choose your role first"
        else:
            logging.debug("creator role chosen, updating role required dropdown")
            max_values = sum([role.count for role in roles.values()]) - 1
            logging.debug(f"max_values: {max_values}")
            options = [
                discord.SelectOption(
                    label=role_name.capitalize(), value=f"{role_name}_{idx}", emoji=role_info.emoji
                )
                for role_name, role_info in roles.items()
                for idx in range(
                    role_info.count if role_info.name != creator_role else role_info.count - 1
                )
            ]
            disabled = False
            placeholder = "Select the roles you require"
        return max_values, options, disabled, placeholder

    async def callback(self, interaction: discord.Interaction):
        """Does the thing."""
        logging.debug("roles required callback")
        assert self.view is not None
        if self.values[0] == "Choose your role first.":
            return await interaction.response.defer()
        required_roles = {role_name: 0 for role_name in self.view.roles}
        for item in self.values:
            item_name = item.split("_")[0]
            required_roles[item_name] += 1
        self.view.required_roles = required_roles
        await interaction.response.defer()


class LFGOptions(discord.ui.View):
    """LFG options menu."""

    def __init__(self, difficulties: list[int], roles: dict[str, RoleDefinition]):
        """Initialisation."""
        super().__init__(timeout=120)
        self.roles = roles
        self.role_counts = {role.name: role.count for role in roles.values()}
        self.difficulty = -1 if len(difficulties) > 1 else difficulties[0]
        self.time_type = ""
        self.creator_role = ""
        self.required_roles = {}
        self.confirmed = False
        self.emojis = {role.name: role.emoji for role in roles.values()}

        self.lfg_difficulties = LFGDifficulty(difficulties)
        self.lfg_time_types = LFGTimeType()
        self.lfg_creator_role = LFGCreatorRole(roles)
        self.lfg_roles_required = LFGRolesRequired(roles)

        self.add_item(self.lfg_difficulties)
        self.add_item(self.lfg_time_types)
        self.add_item(self.lfg_creator_role)
        self.add_item(self.lfg_roles_required)

    @discord.ui.button(label="Create group", style=discord.ButtonStyle.green, row=4)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm the menu selections."""
        if (
            self.difficulty == -1
            or self.time_type == ""
            or self.creator_role == ""
            or self.required_roles == {}
        ):
            message_func = (
                interaction.followup.send
                if interaction.response.is_done()
                else interaction.response.send_message
            )
            await message_func(content="You must select options from all menus.", ephemeral=True)
        else:
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
        if any([opt.value == str(current_selection) for opt in select.options]):
            for opt in select.options:
                opt.default = opt.value == str(current_selection)
        logging.debug([(item.value, item.default) for item in select.options])

    def _update_roles_required_selector(self):
        max_values, options, disabled, placeholder = (
            self.lfg_roles_required._get_roles_required_info(self.roles, self.creator_role)
        )

        self.lfg_roles_required.disabled = disabled
        self.lfg_roles_required.placeholder = placeholder
        self.lfg_roles_required.options = options
        self.lfg_roles_required.max_values = max_values
        self._restore_options(self.lfg_difficulties, self.difficulty)
        self._restore_options(self.lfg_time_types, self.time_type)
        self._restore_options(self.lfg_creator_role, self.creator_role)

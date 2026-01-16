"""Contains buttons for dungeon buddy."""

import discord

from db_py.db_instance import DungeonInstance, Role, RoleType


def _button(
        custom_id: str,
        emoji: str,
        button_style: discord.ButtonStyle,
        disabled: bool,
        row: int,
    ) -> discord.ui.Button:
    button = discord.ui.Button(
        style=button_style,
        disabled=disabled,
        custom_id=custom_id,
        emoji=emoji,
        row=row,
    )
    return button


def button_from_role(role: Role, row: int) -> discord.ui.Button:
    """Creates a button from a given Role."""
    return discord.ui.Button(
        custom_id=role.name.name,
        emoji=role.emoji,
        style=role.button_style,
        disabled=role.disabled,
        row=row
    )

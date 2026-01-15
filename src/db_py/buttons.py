"""Contains buttons for dungeon buddy."""

import discord

from db_py.db_instance import DungeonInstance, Role, RoleType


def _button(
        custom_id: str,
        emoji: str,
        button_style: discord.ButtonStyle,
        disabled: bool,
        row: int
    ) -> discord.ui.Button:
    return discord.ui.Button(
        style=button_style,
        disabled=disabled,
        custom_id=custom_id,
        emoji=emoji,
        row=row,
    )


def _button_from_role(role: Role, row: int) -> discord.ui.Button:
    return _button(
        custom_id=role.name.name,
        emoji=role.emoji,
        button_style=role.button_style,
        disabled=role.disabled,
        row=row
    )


def tank_button(dungeon_instance: DungeonInstance) -> discord.ui.Button:
    """Creates a button interactable formatted for a tank."""
    tank = dungeon_instance.role_info(RoleType.tank.name)
    return _button_from_role(tank, 1)


def healer_button(dungeon_instance: DungeonInstance) -> discord.ui.Button:
    """Creates a button interactable formatted for a healer."""
    healer = dungeon_instance.role_info(RoleType.healer.name)
    return _button_from_role(healer, 2)


def dps_button(dungeon_instance: DungeonInstance) -> discord.ui.Button:
    """Creates a button interactable formatted for a dps."""
    dps = dungeon_instance.role_info(RoleType.dps.name)
    return _button_from_role(dps, 3)

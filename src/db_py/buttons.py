"""Contains buttons for dungeon buddy."""

import discord

from db_py.db_instance import DungeonInstance, Role


def _button(custom_id: str, label: str, emoji: str, button_style: discord.ButtonStyle, disabled: bool):
    return discord.ui.Button(
        style=button_style, label=label, disabled=disabled, custom_id=custom_id, emoji=emoji)


def _button_from_role(role: Role):
    return _button(
        custom_id=role.name.name,
        label=role.name.name,
        emoji=role.emoji,
        button_style=role.button_style,
        disabled=role.disabled
    )


def tank_button(dungeon_instance: DungeonInstance):
    """Creates a button interactable formatted for a tank."""
    tank = dungeon_instance.role_info("tank")
    return _button_from_role(tank)


def healer_button(dungeon_instance: DungeonInstance):
    """Creates a button interactable formatted for a healer."""
    healer = dungeon_instance.role_info("healer")
    return _button_from_role(healer)


def dps_button(dungeon_instance: DungeonInstance):
    """Creates a button interactable formatted for a dps."""
    dps = dungeon_instance.role_info("dps")
    return _button_from_role(dps)

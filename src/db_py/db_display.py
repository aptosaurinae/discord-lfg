"""Contains an embed-like element displaying the DB listing for users to interact with."""


import discord
from discord import ui

from db_py.buttons import dps_button, healer_button, tank_button
from db_py.db_instance import DungeonInstance


class EmbedChangeButtons(ui.ActionRow):
    """Blah."""
    def __init__(self, view: 'EmbedLikeView') -> None:
        """Blah."""
        self.__view = view
        super().__init__()

    @ui.button(label='Change Text', style=discord.ButtonStyle.primary)
    async def change_text(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Blah."""
        await interaction.response.send_modal(ChangeTextModal(self.__view))


class ChangeTextModal(ui.Modal, title='Change Text'):
    """Blah."""
    new_text = ui.TextInput(label='The new text', style=discord.TextStyle.long)

    def __init__(self, view: 'EmbedLikeView') -> None:
        """Blah."""
        self.__view = view
        self.new_text.default = view.random_text.content
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        """Blah."""
        self.__view.random_text.content = str(self.new_text.value)
        await interaction.response.edit_message(view=self.__view)
        self.stop()


class EmbedLikeView(ui.LayoutView):
    """Blah."""
    def __init__(self) -> None:
        """Blah."""
        super().__init__()

        self.random_text = ui.TextDisplay('Hello')
        self.buttons = EmbedChangeButtons(self)

        container = ui.Container(self.random_text, self.buttons, accent_color=discord.Color.blurple())
        self.add_item(container)


def get_embed(dungeon_instance: DungeonInstance):
    """Temp."""
    layout = ui.LayoutView()
    layout.add_item(
        ui.Container(
            ui.TextDisplay(content=dungeon_instance.description),
            ui.ActionRow(
                tank_button(dungeon_instance),
                healer_button(dungeon_instance),
                dps_button(dungeon_instance)),
            accent_color=606675,
        )
    )
    return layout

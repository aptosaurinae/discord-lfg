"""Creates discord commands programmatically."""

import inspect

import discord
from discord import app_commands

from discord_lfg.input_config import CommandArgument, CommandConfig
from discord_lfg.utils import get_numbers_from_channel_name


class AutocompleteError(Exception):
    """Autocompletion error message handler."""

    def __init__(self, messages):
        """Initialisation."""
        self.messages = messages


class ChannelWhitelistError(Exception):
    """Autocompletion error message handler."""

    def __init__(self, message):
        """Initialisation."""
        self.messages = message


def autocomplete_validator(interaction: discord.Interaction, **kwargs):
    """Validates that the user inputs match the autocomplete lists they choose from.

    When discord shows an autocompletion list to a user, there is no validation of what the user
    puts in, so you can get a result that doesn't match the autocomplete list.
    This function is designed to validate the result and respond to the user if they
    did not enter values that match the autocompletion list.
    """
    errors = []
    for arg_value, command_arg in kwargs.items():
        command_arg: CommandArgument
        if command_arg.autocomplete_channel_numbers:
            if isinstance(interaction.channel.name, str):  # type: ignore
                choices = get_numbers_from_channel_name(interaction.channel.name)  # type: ignore
        else:
            choices = command_arg.autocomplete_options
        if choices is not None and arg_value not in choices:
            errors.append(
                f"You must provide an input matching the autocomplete list for "
                f"`{command_arg.displayed_name}`\n"
                f"You input: `{arg_value}`. "
                f"It must match one of: `{choices}`"
            )

    if errors:
        raise AutocompleteError(errors)


def _message_func(interaction: discord.Interaction):
    return (
        interaction.followup.send
        if interaction.response.is_done()
        else interaction.response.send_message
    )


def build_command(
    user_inputs: list[CommandArgument],
    command_config: CommandConfig,
    func_name: str,
    func_desc: str,
    func_call,
) -> discord.app_commands.Command:
    """Builds a discord slash command programmatically."""
    input_params = [user_input.as_parameter for user_input in user_inputs]
    interaction_param = inspect.Parameter(
        "interaction", inspect.Parameter.POSITIONAL_ONLY, annotation=discord.Interaction
    )
    params = [interaction_param, *input_params]

    sig = inspect.Signature(parameters=params)

    user_inputs_dict = {user_input.name: user_input for user_input in user_inputs}

    async def wrapper(interaction: discord.Interaction, **kwargs):
        if interaction.channel.name not in command_config.channel_whitelist:  # type: ignore
            await _message_func(interaction)(
                "This command cannot be used in this channel.", ephemeral=True
            )
            return None

        try:
            autocomplete_validator(
                interaction, **{str(value): user_inputs_dict[key] for key, value in kwargs.items()}
            )
        except AutocompleteError as e:
            response = "\n".join(e.messages)
            await _message_func(interaction)(response, ephemeral=True)
            return None

        return await func_call(interaction, **kwargs, config=command_config)

    wrapper.__signature__ = sig
    wrapper.__name__ = func_name

    cmd = app_commands.Command(name=func_name, description=func_desc, callback=wrapper)

    for user_input in user_inputs:
        user_input.discord_rename(cmd)
        user_input.discord_description(cmd)
        user_input.discord_autocomplete(cmd)

    return cmd

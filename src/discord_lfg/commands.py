"""Creates discord commands programmatically."""

import inspect
from dataclasses import dataclass

import discord
from discord import app_commands

from discord_lfg.lfg import lfg
from discord_lfg.utils import (
    autocomplete_choice_from_channel_numbers,
    autocomplete_choice_from_list,
    get_numbers_from_channel_name,
)

TYPE_LOOKUPS = {"str": str, "int": int, "float": float, "discord.member": discord.Member}


class AutocompleteError(Exception):
    """Autocompletion error message handler."""

    def __init__(self, messages):
        """Initialisation."""
        self.messages = messages


@dataclass
class CommandArgument:
    """For storage of parameters and creation of discord.app_command.Command arguments."""

    name: str
    python_type: type
    required: bool
    description: str
    autocomplete_options: list | None
    autocomplete_channel_numbers: bool = False
    display_name: str = ""

    @property
    def displayed_name(self):
        """Gets the name that is displayed to discord users."""
        return self.display_name if self.display_name != "" else self.name

    @property
    def as_parameter(self):
        """Gets the definition of an argument for a function.

        More specifically, this uses the `inspect.Parameter` functionality to programmatically
        define what the argument should look like.

        e.g. if you had a function defined like this:
        `def func(name_arg: str, detail_info: dict):`
        the two arguments would look like this:
        ``` python
        name_arg = inspect.Parameter(
            name="name_arg",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=str,
            default=inspect.Parameter.empty
        )
        detail_info = inspect.Parameter(
            name="detail_info",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=dict,
            default=inspect.Parameter.empty
        )
        ```
        and you could then create a function by defining a function and then overriding the
        signature of the function using `func.__signature__` and `inspect.Signature`.
        """
        if self.required:
            default = inspect.Parameter.empty
        else:
            if self.python_type is str:
                default = ""
            elif self.python_type is int:
                default = 0
            elif self.python_type is float:
                default = 0.0
            else:
                default = inspect.Parameter.empty
        if self.required:
            kind = inspect.Parameter.POSITIONAL_OR_KEYWORD
        else:
            kind = inspect.Parameter.KEYWORD_ONLY

        return inspect.Parameter(
            name=self.name, kind=kind, annotation=self.python_type, default=default
        )

    def discord_rename(self, command: discord.app_commands.Command):
        """Renames how discord displays the name of this command.

        This will make it so that although Python thinks the argument is named one thing,
        the name displayed to the user when they use the slash command is something different.
        This makes it possible to have a generalised function, but make it so that
        discord displays a customised name to the user.
        """
        if self.display_name != "":
            command._params[self.name]._rename = self.display_name

    def discord_description(self, command: discord.app_commands.Command):
        """Applies a description for a discord command that has had this parameter added."""
        command._params[self.name].description = self.description

    def discord_autocomplete(self, command: discord.app_commands.Command):
        """Applies an autocompleter for a discord command that has had this parameter added.

        Note that just because an argument has an autocomplete set, discord does not enforce the
        autocomplete values. See `_autocomplete_validator`.
        """
        if self.autocomplete_channel_numbers:
            autocomplete_choice_from_channel_numbers(command, self.name)
        elif self.autocomplete_options is not None:
            autocomplete_choice_from_list(self.autocomplete_options, command, self.name)


def command_argument_from_config(argument_definition: dict, arg_name: str):
    """Builds a command argument based on information given in a toml config."""
    required_elements = ["display_name", "python_type", "required", "description"]
    errors = []
    for element in required_elements:
        if argument_definition.get(element) is None:
            errors.append(f"missing {element} from argument definition: {arg_name}")
    display_name = argument_definition.get("display_name", "")
    python_type = TYPE_LOOKUPS[argument_definition.get("python_type", "").lower()]
    required = argument_definition.get("required", False)
    description = argument_definition.get("description", "")
    autocomplete_options = argument_definition.get("options", {})
    return CommandArgument(
        name=arg_name,
        python_type=python_type,
        required=required,
        description=description,
        autocomplete_options=autocomplete_options,
        display_name=display_name,
    )


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


def build_command(
    user_inputs: list[CommandArgument],
    fixed_inputs: dict,
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
        try:
            autocomplete_validator(
                interaction, **{str(value): user_inputs_dict[key] for key, value in kwargs.items()}
            )
        except AutocompleteError as e:
            response = "\n".join(e.messages)
            message_func = (
                interaction.followup.send
                if interaction.response.is_done()
                else interaction.response.send_message
            )
            await message_func(response, ephemeral=True)
            return None

        return await func_call(interaction, **kwargs, **fixed_inputs)

    wrapper.__signature__ = sig
    wrapper.__name__ = func_name

    cmd = app_commands.Command(name=func_name, description=func_desc, callback=wrapper)

    for user_input in user_inputs:
        user_input.discord_rename(cmd)
        user_input.discord_description(cmd)
        user_input.discord_autocomplete(cmd)

    return cmd


def build_lfg_command(arguments: list[CommandArgument], fixed_lfg_inputs: dict):
    """Builds the LFG command programmatically."""
    standard_args = [
        CommandArgument(
            "listed_as",
            str,
            False,
            "The in-game name. Leave blank to automatically generate a name for you (recommended)",
            None,
        ),
        CommandArgument(
            "creator_notes",
            str,
            False,
            "Extra notes you want to make players signing up aware of.",
            None,
        ),
    ]
    arguments = arguments + standard_args
    return build_command(
        arguments, fixed_lfg_inputs, "lfg", "Generates a Group Builder listing.", lfg
    )

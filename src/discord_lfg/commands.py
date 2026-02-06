"""Creates discord commands programmatically."""

import inspect
from dataclasses import dataclass

import discord
from discord import app_commands

from discord_lfg.autocompletion import (
    autocomplete_choice_from_channel_numbers,
    autocomplete_choice_from_list,
)
from discord_lfg.lfg import lfg

TYPE_LOOKUPS = {"str": str, "int": int, "float": float, "discord.member": discord.Member}


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
    def as_parameter(self):
        """Gets the definition of an argument for a function."""
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
        """Renames how discord displays the name of this command."""
        if self.display_name != "":
            command._params[self.name]._rename = self.display_name

    def discord_description(self, command: discord.app_commands.Command):
        """Applies a description for a discord command that has had this parameter added."""
        command._params[self.name].description = self.description

    def discord_autocomplete(self, command: discord.app_commands.Command):
        """Applies an autocompleter for a discord command that has had this parameter added."""
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


def build_command(
    user_inputs: list[CommandArgument], fixed_inputs: dict, func_name, func_desc, func_call
) -> discord.app_commands.Command:
    """Builds a discord slash command programmatically."""
    input_params = [user_input.as_parameter for user_input in user_inputs]
    interaction_param = inspect.Parameter(
        "interaction", inspect.Parameter.POSITIONAL_ONLY, annotation=discord.Interaction
    )
    params = [interaction_param, *input_params]

    sig = inspect.Signature(parameters=params)

    async def wrapper(interaction, **kwargs):
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

"""Process configs for the bot."""

try:
    import tomllib
except ModuleNotFoundError:
    import pip._vendor.tomli as tomllib

import argparse
import inspect
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import discord

from discord_lfg.utils import (
    autocomplete_choice_from_channel_numbers,
    autocomplete_choice_from_list,
    create_roles_from_config,
)


class ConfigValueError(Exception):
    """Autocompletion error message handler."""

    def __init__(self, messages):
        """Initialisation."""
        self.messages = messages


@dataclass
class LFGConfig:
    """Configuration for LFG bot."""

    debug: bool
    guild_id_int: int
    guild_id_discord: discord.Object
    guild_name: str
    log_folder: Path
    all_roles: dict[str, dict[str, str]]
    commands: list[Path]

    def validate(self):
        """Validates the config inputs."""
        errors = []
        if len(errors) > 0:
            conf_errors = "".join([f"{err}\n" for err in errors])
            raise ValueError(f"Config is missing required arguments: \n{conf_errors}")

    def _validate_roles(self):
        errors = []
        if self.all_roles is None or len(self.all_roles) == 0:
            errors.append("You must define at least one role in the config, see readme for details")
        for role_name, role_data in self.all_roles.items():
            if role_data.get("emoji") is None or role_data.get("identifier") is None:
                errors.append(
                    f"Role input is missing data: {role_name} needs 'emoji' and 'identifier'"
                )
        return errors


@dataclass
class CommandConfig:
    """Configuration for individual command."""

    name: str
    description: str
    debug: bool
    guild_name: str
    timeout_length: int
    editable_length: int
    guild_roles: list


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
    type_lookups = {"str": str, "int": int, "float": float, "discord.member": discord.Member}

    required_elements = ["display_name", "python_type", "required", "description"]
    errors = []
    for element in required_elements:
        if argument_definition.get(element) is None:
            errors.append(f"missing {element} from argument definition: {arg_name}")
    display_name = argument_definition.get("display_name", "")
    python_type = type_lookups[argument_definition.get("python_type", "").lower()]
    required = argument_definition.get("required", False)
    description = argument_definition.get("description", "")
    autocomplete_channel_numbers = argument_definition.get("options_from_channel_numbers", False)
    autocomplete_options = argument_definition.get("options", {})
    return CommandArgument(
        name=arg_name,
        python_type=python_type,
        required=required,
        description=description,
        autocomplete_options=autocomplete_options,
        autocomplete_channel_numbers=autocomplete_channel_numbers,
        display_name=display_name,
    )


def _argparser():
    parser = argparse.ArgumentParser(description="Configuration for discord bot")
    parser.add_argument("token_file", type=str, help="Discord Token")
    parser.add_argument("config", type=str, help="configuration file")
    args = vars(parser.parse_args())
    with open(args["token_file"], "rb") as token_file:
        token_data = tomllib.load(token_file)
    with open(args["config"], "rb") as config_file:
        config_data = tomllib.load(config_file)
    return token_data, config_data


def _parse_token(token_data: dict):
    """Gets a token string from a token file."""
    if (token := token_data.get("discord", {}).get("token")) is not None:
        return token
    else:
        raise ValueError("Token file must define a 'token' value within '[discord]'")


def _parse_config(config_data: dict) -> tuple[LFGConfig, list[dict]]:
    """Setup config for inputs."""
    config = LFGConfig(
        debug=config_data.get("debug", 0),
        guild_id_int=config_data.get("guild_id", ""),
        guild_id_discord=discord.Object(config_data.get("guild_id", "")),
        guild_name=config_data.get("guild_name", ""),
        log_folder=Path(config_data.get("log_folder", "")),
        all_roles=config_data.get("role", {}),
        commands=[Path(command) for command in config_data.get("commands", [])],
    )
    try:
        config.validate()
    except ConfigValueError as e:
        response = "\n".join(e.messages)
        logging.critical(response)
        raise
    setup_logging(config.log_folder, config.debug)

    commands = []
    errors = []
    for command_path in config_data.get("command_files", ""):
        command_path = Path(command_path)
        logging.debug(command_path)
        if command_path.exists() and command_path.suffix == ".toml":
            with open(command_path, "rb") as config_file:
                command_config_input = tomllib.load(config_file)
            command_data = _parse_command(config, command_config_input)
            commands.append(command_data)
        else:
            errors.append(f"Command path doesn't exit or is not a .toml file: {command_path}")

    return config, commands


def _parse_command(config: LFGConfig, command_config_input) -> dict:
    """Parses data from a specific command configuration."""
    # command-specific config inputs
    activity_arg = command_argument_from_config(
        command_config_input.get("activity", {}), "activity"
    )
    option_args = []
    options = command_config_input.get("option", {})
    for option_name, option_data in options.items():
        option_args.append(command_argument_from_config(option_data, f"option_{option_name}"))

    # generated from a mix of command-specific role values and general role inputs
    # this will need adjusting for per-command config input
    command_roles = create_roles_from_config(
        config.all_roles, command_config_input.get("role_counts", {})
    )
    creator_role_arg = CommandArgument(
        "creator_role",
        str,
        True,
        "The role you are filling for this group.",
        list(command_roles.keys()),
    )
    required_spots_arg = CommandArgument(
        "required_spots",
        str,
        True,
        f"valid identifiers: {[role.identifier for role in command_roles.values()]}",
        None,
    )

    command_name = command_config_input.get("name", "")
    command_description = command_config_input.get("description", "")
    command_data = {
        "args": [activity_arg] + option_args + [creator_role_arg, required_spots_arg],
        "roles": command_roles,
        "config": CommandConfig(
            command_name,
            command_description,
            config.debug,
            config.guild_name,
            command_config_input.get("timeout_length", 30),
            command_config_input.get("editable_length", 5),
            [],
        ),
    }
    logging.debug(command_data)
    return command_data


def parse_inputs() -> tuple[str, LFGConfig, list[dict]]:
    """Parse the inputs to the bot.py script."""
    token_data, config_data = _argparser()
    token = _parse_token(token_data)
    config, commands = _parse_config(config_data)
    return token, config, commands


def setup_logging(log_folder: Path, debug: bool = False):
    """Setup logger."""
    dt_now = datetime.now(timezone.utc)
    datetime_str = (
        f"{dt_now.year}-{dt_now.month}-{dt_now.day}_{dt_now.hour}-{dt_now.minute}-{dt_now.second}"
    )
    if log_folder != "" and log_folder.exists():
        log_file_path = log_folder / f"{datetime_str}_dungeon_buddy.log"
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[logging.FileHandler(log_file_path, encoding="utf-8")],
        )

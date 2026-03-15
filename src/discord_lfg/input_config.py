"""Process configs for the bot."""

from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:
    import pip._vendor.tomli as tomllib  # pyright: ignore[reportMissingImports]

import argparse
import inspect
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import discord
from discord import Role

from discord_lfg.utils import (
    RoleDefinition,
    autocomplete_choice_from_channel_numbers,
    autocomplete_choice_from_list,
    create_roles_from_config,
)

logger = logging.getLogger(__name__)


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
    moderator_role_name: str
    log_folder: Path | None
    stats_folder: Path | None
    all_roles: dict[str, dict[str, str]]
    commands: list[Path]

    def validate(self):
        """Validates the config inputs."""
        errors = []
        if not isinstance(self.debug, bool):
            errors.append("Debug must be `true` or `false`")
        if self.guild_id_int <= 0:
            errors.append("Guild ID must not be 0 or negative")
        if self.log_folder is not None and not self.log_folder.exists():
            errors.append(f"Log folder given does not exist, please create it: {self.log_folder}")
        if self.stats_folder is not None and not self.stats_folder.exists():
            errors.append(
                f"Data folder given does not exist, please create it: {self.stats_folder}"
            )
        errors += self._validate_roles()
        for command_path in self.commands:
            if not command_path.exists():
                errors.append(f"Command path given does not exist: {command_path}")
        return errors

    def _validate_roles(self):
        errors = []
        if self.all_roles is None or len(self.all_roles) == 0:
            errors.append("You must define at least one role in the config, see readme for details")
        for role_name, role_data in self.all_roles.items():
            if role_data.get("emoji") is None:
                errors.append(f"Role input is missing data: {role_name} needs 'emoji'.")
            if role_data.get("identifier") is None:
                errors.append(f"Role input is missing data: {role_name} needs 'identifier'.")
        return errors


@dataclass
class CommandConfig:
    """Configuration for individual command."""

    args: list[CommandArgument]
    roles: dict[str, RoleDefinition]
    name: str
    description: str
    debug: bool
    guild_name: str
    timeout_length: float
    editable_length: float
    kick_reasons: list[str]
    channel_whitelist: list[str]
    channel_role_mentions: dict[str, str]
    guild_roles: Sequence[Role]

    def validate(self):
        """Validates the config inputs."""
        errors = []
        if self.name == "":
            errors.append("Commands must have a name.")
        if self.description == "":
            errors.append("Commands must have a description.")
        return errors


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

    def validate(self):
        """Validates that the argument elements are acceptable."""
        errors = []
        if self.display_name == "":
            errors.append("    Command arguments must have a name.")
        if self.description == "":
            errors.append("    Command arguments must have a description.")
        if self.autocomplete_channel_numbers and self.autocomplete_options is not None:
            errors.append(
                f"    {self.name}: If you define `options_from_channel_numbers` "
                f"you cannot provide an options list."
            )
        return errors

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


def parse_inputs() -> tuple[str, LFGConfig, list[CommandConfig]]:
    """Parse the inputs to the bot.py script."""
    token, config_data = _argparser()
    config, commands = _parse_config(config_data)
    return token, config, commands


def _argparser():
    parser = argparse.ArgumentParser(description="Configuration for discord bot")
    parser.add_argument("--token", required=True, type=str, help="Discord Token as a string")
    parser.add_argument("--config", required=True, type=str, help="configuration file")
    args = parser.parse_args()
    with open(args.config, "rb") as config_file:
        config_data = tomllib.load(config_file)
    return args.token, config_data


def _parse_config(config_data: dict) -> tuple[LFGConfig, list[CommandConfig]]:
    """Setup config for inputs."""
    log_folder = config_data.get("log_folder")
    stats_folder = config_data.get("stats_folder")
    config = LFGConfig(
        debug=config_data.get("debug", False),
        guild_id_int=int(config_data.get("guild_id", 0)),
        guild_id_discord=discord.Object(config_data.get("guild_id", 0)),
        guild_name=config_data.get("guild_name", ""),
        moderator_role_name=config_data.get("moderator_role_name", ""),
        log_folder=Path(log_folder) if log_folder is not None else None,
        stats_folder=Path(stats_folder) if stats_folder is not None else None,
        all_roles=config_data.get("role", {}),
        commands=[Path(command) for command in config_data.get("commands", [])],
    )
    errors = []
    errors += config.validate()
    setup_logging(config.log_folder, config.debug)

    commands = []
    for command_path in config_data.get("command_files", ""):
        command_path = Path(command_path)
        logger.debug(command_path)
        if command_path.exists() and command_path.suffix == ".toml":
            with open(command_path, "rb") as config_file:
                command_config_input = tomllib.load(config_file)
            try:
                command_data = _parse_command(config, command_config_input)
                commands.append(command_data)
            except ConfigValueError as e:
                errors.append(f"{command_path} contained errors:")
                messages = [f"    {message}" for message in e.messages]
                errors += messages
        else:
            errors.append(f"Command path doesn't exist or is not a .toml file: {command_path}")
    if len(errors) > 0:
        response = "\nThere are errors in your config file:\n    "
        response += "\n    ".join(errors)
        logger.critical(response)
        raise ConfigValueError(response)

    return config, commands


def _parse_command(config: LFGConfig, command_config_input: dict) -> CommandConfig:
    """Parses data from a specific command configuration."""
    name = command_config_input.get("name", "")
    description = command_config_input.get("description", "")
    timeout_length = command_config_input.get("timeout_length", 30)
    editable_length = command_config_input.get("editable_length", 5)
    channel_role_mentions: dict = command_config_input.get("channel_role_mentions", {})

    channel_whitelist: list = command_config_input.get("channel_whitelist", [])
    if "bot-control" not in channel_whitelist:
        channel_whitelist.append("bot-control")

    kick_reasons: list = command_config_input.get("kick_reasons", [])
    other_str = "Other - please message separately"
    if other_str not in kick_reasons:
        kick_reasons.append(other_str)

    roles = create_roles_from_config(config.all_roles, command_config_input.get("role_counts", {}))
    argument_errors = []
    try:
        args = _build_arguments(command_config_input, roles)
    except ConfigValueError as e:
        argument_errors += e.messages
        args = []

    command_data = CommandConfig(
        args,
        roles,
        name,
        description,
        config.debug,
        config.guild_name,
        timeout_length,
        editable_length,
        kick_reasons,
        channel_whitelist,
        channel_role_mentions,
        [],
    )
    logger.debug(command_data)
    main_config_errors = command_data.validate()
    errors = main_config_errors + argument_errors
    if len(errors) > 0:
        raise ConfigValueError(errors)

    return command_data


def _build_arguments(config_input, roles: dict[str, RoleDefinition]):
    errors = []
    try:
        activity_arg = command_argument_from_config(config_input.get("activity", {}), "activity")
    except ConfigValueError as e:
        errors.append("activity contains errors:")
        errors += e.messages

    option_args = []
    options = config_input.get("option", {})
    for option_name, option_data in options.items():
        try:
            option_args.append(command_argument_from_config(option_data, f"option_{option_name}"))
        except ConfigValueError as e:
            errors.append(f"option_{option_name} contains errors:")
            errors += e.messages
    if len(errors) > 0:
        raise ConfigValueError(errors)

    creator_role_arg = CommandArgument(
        "creator_role",
        str,
        True,
        "The role you are filling for this group.",
        list(roles.keys()),
        display_name="your_role",
    )
    filled_spots_arg = CommandArgument(
        "filled_spots",
        str,
        False,
        f"Use {str([role.identifier for role in roles.values()])[1:-1]} for already filled spots",
        None,
    )
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
    return [activity_arg] + option_args + [creator_role_arg, filled_spots_arg] + standard_args


def command_argument_from_config(argument_definition: dict, arg_name: str):
    """Builds a command argument based on information given in a toml config."""
    type_lookups = {
        "str": str,
        "int": int,
        "float": float,
        "discord.member": discord.Member,
        "": None,
    }

    required_elements = ["display_name", "python_type", "description"]
    errors = []
    for element in required_elements:
        if argument_definition.get(element) is None:
            errors.append(f"    {arg_name} is missing {element} from argument definition")
    display_name = argument_definition.get("display_name", "")
    python_type = type_lookups[argument_definition.get("python_type", "").lower()]
    required_default = arg_name == "activity"
    required = argument_definition.get("required", required_default)
    description = argument_definition.get("description", "")
    autocomplete_options = argument_definition.get("options")
    autocomplete_channel_numbers = argument_definition.get("options_from_channel_numbers", False)
    command_argument = CommandArgument(
        name=arg_name,
        python_type=python_type,
        required=required,
        description=description,
        autocomplete_options=autocomplete_options,
        autocomplete_channel_numbers=autocomplete_channel_numbers,
        display_name=display_name,
    )
    errors += command_argument.validate()
    if len(errors) > 0:
        raise ConfigValueError(errors)

    return command_argument


def setup_logging(log_folder: Path | None, debug: bool = False) -> logging.Logger:
    """Setup logger."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_folder is not None and log_folder.exists():
        dt = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        log_file_path = log_folder / f"{dt}_dungeon_buddy.log"

        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger

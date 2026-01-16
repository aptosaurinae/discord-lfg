"""Access to resources."""

try:
    import tomllib
except ModuleNotFoundError:
    import pip._vendor.tomli as tomllib

import random
import string
from pathlib import Path

RESOURCES = Path(__file__).parent.parent.parent / "resources"


def _load_resource(filename: str, folders: str | None = None):
    if folders is None:
        file_path = RESOURCES / f"{filename}.toml"
    else:
        file_path = RESOURCES / folders / f"{filename}.toml"
    if not file_path.exists():
        raise FileNotFoundError(f"Could not file {file_path} while loading resources.")

    with open(file_path, "rb") as resource_file:
        return tomllib.load(resource_file)


def load_messages() -> dict:
    """Loads standard messages."""
    return _load_resource("messages")


def _load_lists() -> dict:
    """Loads standard lists."""
    return _load_resource("lists")


def load_emojis() -> dict:
    """Loads standard emojis."""
    emojis: dict = _load_lists()["emojis"]
    return emojis


def load_time_types() -> dict:
    """Loads time types for dungeons."""
    return _load_lists()["time_types"]


def load_passphrase_words() -> list:
    """Loads passphrase words."""
    return _load_lists()["passphrase_words"]


def load_dungeons(expansion: str, season: str | int) -> dict:
    """Loads a dungeon set."""
    return _load_resource(f"{expansion}-{season}", "dungeons")


def generate_passphrase(num_words: int = 3) -> str:
    """Creates a 3-word passphrase from the list of passphrase words."""
    passphrase_words = load_passphrase_words()
    return "".join(random.choices(population=passphrase_words, k=num_words))


def generate_listing_name(dungeon_short: str, num_chars: int, guild_name):
    """Creates a listing name from a dungeon name."""
    random_string = ""
    for _ in range(num_chars):
        random_string += random.choice(string.ascii_uppercase)

    if guild_name != "":
        guild_name += " "

    return f"{guild_name}{dungeon_short} {random_string}"

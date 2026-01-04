"""Access to resources."""

try:
    import tomllib
except ModuleNotFoundError:
    import pip._vendor.tomli as tomllib

import random
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


def load_lists() -> dict:
    """Loads standard lists."""
    return _load_resource("lists")


def load_dungeons(expansion: str, season: str | int) -> dict:
    """Loads a dungeon set."""
    return _load_resource(f"{expansion}-{season}", "dungeons")


def generate_passphrase(num_words: int = 3) -> str:
    """Creates a 3-word passphrase from the list of passphrase words."""
    passphrase_words = _load_resource("lists")["passphrase_words"]
    return "".join(random.choices(population=passphrase_words, k=num_words))

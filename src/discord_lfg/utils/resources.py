"""Access to resources."""

try:
    import tomllib
except ModuleNotFoundError:
    import pip._vendor.tomli as tomllib

import random
from importlib.resources import files


def _load_resource(filename: str, folders: str | None = None):
    base = files("discord_lfg.resources")

    if folders is None:
        resource_path = base / f"{filename}.toml"
    else:
        resource_path = base / folders / f"{filename}.toml"

    if not resource_path.is_file():
        raise FileNotFoundError(f"Could not file {resource_path} while loading resources.")

    return tomllib.loads(resource_path.read_text())


def load_passphrase_words() -> list[str]:
    """Loads passphrase words."""
    return _load_resource("passphrases")["passphrase_words"]


def load_name_suffix_words() -> list[str]:
    """Loads passphrase words."""
    return _load_resource("names")["alphabet_names"]


def generate_passphrase(num_words: int = 3) -> str:
    """Creates a 3-word passphrase from the list of passphrase words."""
    passphrase_words = load_passphrase_words()
    return "".join(random.choices(population=passphrase_words, k=num_words))


def generate_listing_name(name: str, num_chars: int, guild_name):
    """Creates a listing name from a given name."""
    name_short = name[:3].upper()
    random_string = ""
    random_words = [word.capitalize() for word in load_name_suffix_words()]
    for _ in range(num_chars):
        random_string += random.choice(random_words)

    if guild_name != "":
        guild_name += " "

    return f"{guild_name}{name_short} {random_string}"

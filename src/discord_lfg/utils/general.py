"""Utilities for Group Builder."""

import re
from datetime import datetime, timezone


def extract_numbers(text: str) -> list[int]:
    """Gets any numbers from a string and returns them as a list of integers."""
    return [int(num) for num in re.findall(r"\d+", text)]


def get_numbers_from_channel_name(channel_name: str) -> None | list:
    """Generates a set of numbers from a channel name.

    Assumes that at most there are 2 numbers in the channel name.
    If this is the bot-control channel, generates a list of 1-10.
    Otherwise, generates a list with just -1 as a difficulty.
    """
    numbers = extract_numbers(channel_name)
    if len(numbers) == 1:
        return [str(numbers[0])]
    elif len(numbers) == 2:
        return [str(num) for num in range(numbers[0], numbers[1] + 1)]
    elif channel_name == "bot-control":
        return [str(num) for num in range(1, 11)]
    else:
        return [str(-1)]


def datetime_now_utc():
    """Gets the current time using the UTC timezone."""
    return datetime.now(tz=timezone.utc)

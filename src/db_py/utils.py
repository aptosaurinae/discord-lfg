"""Utilities for Dungeon Buddy."""


def get_difficulty_start_and_end_from_channel_name(channel_name: str) -> None | list:
    """Generates a set of difficulty values from a channel name."""
    if channel_name == "bot-control":
        start_num = 2
        end_num = 20
        return [str(num) for num in range(start_num, end_num + 1)]
    if channel_name[:5] != "lfg-m":
        return None
    start_start_idx = channel_name.find("m") + 1
    if channel_name.count("m") == 1:
        start_num = int(channel_name[start_start_idx:])
        end_num = start_num
        return [str(num) for num in range(start_num, end_num + 1)]
    elif channel_name.count("m") == 2:
        start_end_idx = channel_name.find("-", start_start_idx)
        end_start_idx = channel_name.find("m", start_end_idx) + 1
        start_num = int(channel_name[start_start_idx:start_end_idx])
        end_num = int(channel_name[end_start_idx:])
        return [str(num) for num in range(start_num, end_num + 1)]
    return None

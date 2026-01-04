# dungeon-buddy-py

This is a Python implementation of Dungeon Buddy, using the library [`discord-py`](https://discordpy.readthedocs.io/en/stable/).

## Background

Dungeon Buddy is a Discord bot for easy creation of groups for World of Warcraft dungeons. These groups have one tank, one healer, and three damage dealers in each group. Dungeon Buddy provides a structured embed with buttons for joining groups, making it easier to track Discord usernames when groups are formed, providing passwords only to those who sign up enabling a link between the Discord signup and the in-game signup.

The [original Dungeon Buddy](https://bit.ly/3ZrVj7C) was built by Baddadan/Kashual using DiscordJS for the [No Pressure EU](https://no-pressure.eu) Discord server. This is an implementation of the same system in Python.

## Commands

`/lfg` - create a group for the dungeon. Choose desired dungeon > dungeon difficulty > timed/completed > your role >
required roles from a drop-down style menu.

`/lfgquick` - create a group using a '_quick string_' rather than a drop-down style menu.

Example quick string: `fall 10t d hdd`

    <dungeonShorthand> <keyLevel><timed/completed> <yourRole> <requiredRoles>

`/lfghistory` - check up-to 10 of your latest groups. Previous teammates & passphrases can be found here.

`/lfgstats` - check total groups created, groups created in the last 24h, 7d, 30d & also the most popular dungeons for
each key range.

## License

This project is licensed under the [CC BY-NC 4.0 License](https://creativecommons.org/licenses/by-nc/4.0/).

### Conditions

-   You **must credit** the original author in any fork, modification, or usage of this project by adding the following
    to your Discord bot description:
    > Original code by Baddadan/Kashual for NoP EU. GitHub: https://bit.ly/3ZrVj7C
-   This code **cannot** be used in any product that is sold for money or restricted by a paywall. This includes Discord
    member sections

If you have questions about the licensing terms, please contact me at the [No Pressure](https://discord.gg/nopressureeu)
discord server.

# Discord-LFG

This is a Python based system for Discord to allow easy creation of groups, using the library [`discord-py`](https://discordpy.readthedocs.io/en/stable/).

It was originally based on the Dungeon Buddy system written by Baddadan for No Pressure EU, and
is still significantly inspired by that system.

## TODO

- Make commands build from the config?
  - update readme for config
  - this will mean needing to move role counts to the commands? keep roles as-is and re-use for command definitions

For feature parity with the original Dungeon Buddy, the following is missing:

- Log group members when group completes in any way (full, timeout, cancelled)
- Add `/lfgstats` reporting
- Add history for users (both personal and for mods)
- Error handling for failed interactions?

And finally:

- Tests, Tests, Tests

## Background

Discord-LFG is a Discord bot originally created for easy creation of groups for World of Warcraft dungeons.
These groups typically have one tank, one healer, and three damage dealers in each group.
Discord-LFG provides a structured embed with buttons for joining groups, making it easier to track Discord
usernames when groups are formed, providing passwords only to those who sign up enabling a link
between the Discord signup and the in-game signup.

The commands and group listings are able to be configured by the bot host. A template for
"traditional" World of Warcraft 5-person dungeon groups is included in the docs.

The [original Dungeon Buddy](https://bit.ly/3ZrVj7C) was built by Baddadan/Kashual using `DiscordJS` for
the [No Pressure EU](https://no-pressure.eu) Discord server.
This system is inspired by Dungeon Buddy, and implementated in
Python using [discord-py](https://discordpy.readthedocs.io/en/latest/api.html).

## Installation and setup

### Installation

<!--- --8<-- [start:docs-install-general] -->

To install Discord-LFG (discord_lfg), we recommend using the [conda](https://docs.conda.io/en/latest/) package manager,
accessible from the terminal by installing [miniforge](https://github.com/conda-forge/miniforge?tab=readme-ov-file#download).

Note that the `discord-py` package is not up to date on conda, so you will need to add this from `pip` after
setting up the environment initially with `conda`.

<!--- --8<-- [end:docs-install-general] -->

#### As a user

<!--- --8<-- [start:docs-install-user] -->

``` shell
git clone git@github.com:aptosaurinae/discord-lfg.git
cd discord-lfg
conda env create -n discord-lfg -f requirements/base.txt
conda activate discord-lfg
pip install discord-py
pip install --no-deps -e .
```

<!--- --8<-- [end:docs-install-user] -->

#### Development / Contributing

<!--- --8<-- [start:docs-install-dev] -->

``` shell
git clone git@github.com:aptosaurinae/discord-lfg.git
cd discord-lfg
conda env create -n discord-lfg -f requirements/base.txt -f requirements/dev.txt
conda activate discord-lfg
pip install discord-py
pip install --no-deps -e .
```

This will enable `pre-commit` and `pytest`.

<!--- --8<-- [end:docs-install-dev] -->

### Running

To run the bot you can then do the following:

``` shell
python src/discord_lfg/bot.py path/to/token.toml path/to/config.toml
```

which should result in something like the following:

``` shell
(discord-lfg) D:\Programming\github-repos\discord-lfg>python src/discord_lfg/bot.py "D:\Programming\discord-lfg-config\test_token.toml" "D:\Programming\discord-lfg\test_config.toml"
[2026-01-04 15:24:28] [INFO    ] discord.client: logging in using static token
[2026-01-04 15:24:31] [INFO    ] discord.gateway: Shard ID None has connected to Gateway (Session ID: <id number>).
Logged in as app-commands-test#2842 (ID: <app id number>)
------
Discord-LFG started
```

You should find that the bot slash commands are then active in the relevant server when it's given
a valid configuration file.

### File setup

The token toml file needs to look like the following:

``` toml
[discord]
token = "abcd123"
```

where the token string is a valid Discord bot token.

The config file needs to look like the following:

``` toml
guild_id = 123456789
guild_name = "NoP"

[activity]
name = "dungeon"
python_type = "str"
required = true
description = "The dungeon you are listing a key for."
options = [
    DN = "dungeon name",
]

[timing_aim]
name = "timing_aim"
python_type = "str"
required = true
description = "The timing type you are aiming for."
options = [
    "dungeon timing type",
]

[role.tank]
emoji = "<:tankemojiname:123456789>"
count = 1
indicator = "t"

[role.healer]
emoji = "<:healeremojiname:123456789>"
count = 1
indicator = "h"

[role.dps]
emoji = "<:dpsemojiname:123456789>"
count = 3
indicator = "d"

[messages]
help = "help message response"
```

- `guild_id` is the Discord ID of the server that you are wanting the host the bot in.
- `activity` is a list of the dungeons for users to choose with metadata about how options
are presented to users.
- `timing_aim` is a dictionary of the timing types for users to choose with metadata.
- `messages` must contain a `help` response.
- `role` dictionary for each of the required roles you want in the group.
  - `emoji`: The emoji names and numbers need to match the names and IDs of the emojis in the server you are hosting the bot. The names can be found as the ":name:" names in the server. The IDs can be found by right clicking on the emojis in the server you're in and opening the link, then looking at the number of their name in the URL.
  - `count`: the number of spots in the group for this role.
  - `indicator`: the single character indicator for quick group building.
- *Optional*: `guild_name` modifies the automatic listing group names and filled spots.
- *Optional*: `timeout_length`, a float in minutes. This controls how long the listing exists for before
timing out. This is a float, so can be set to 0.1 or similar for testing purposes.
- *Optional*: `editable_length`, a float in minutes. This controls how long the listing is able to
be edited for once the group is full.
- *Optional*: `debug`, set to 1 to turn on debug mode, which will be more verbose in the console
and enable `/lfgdebug` which is a pre-set listing for test purposes.
- *Optional*: `log_folder`, set this to a folder that already exists and it will dump a log file here.

## Bot Commands

Once the bot is up and running, the following commands should be available from within the relevant server.

`/lfg` - create a group for the dungeon. Choose desired dungeon > dungeon difficulty > timed/completed > your role >
required roles from a drop-down style menu.

`/lfgquick` - create a group using autocomplete fields instead of an interactive drop down menu system.

[NYI] `/lfghistory` - check up-to 10 of your latest groups. Previous teammates & passphrases can be found here.

[NYI] `/lfgstats` - check total groups created, groups created in the last 24h, 7d, 30d &
also the most popular dungeons for each key range.

## License

This project uses the same license as the original Dungeon Buddy, as below.

This project is licensed under the [CC BY-NC 4.0 License](https://creativecommons.org/licenses/by-nc/4.0/).

### Conditions

-   You **must credit** the original author in any fork, modification, or usage of this project by
adding the following to your Discord bot description:
    > Original code by Baddadan/Kashual for NoP EU. GitHub: https://bit.ly/3ZrVj7C
-   This code **cannot** be used in any product that is sold for money or restricted by a paywall.
This includes Discord member sections

If you have questions about the licensing terms, please contact Baddadan/Kashual at the
[No Pressure](https://discord.gg/nopressureeu) discord server.

### Modifications

As noted in the licence terms, modifications should be noted.
Primarily for this project this is that the discord bot has been rebuilt in Python,
which alters the structure of how many aspects are set up in and of itself.
It would be difficult to provide a full listing of all changes as a result.
The following list of changes has been made to functionality:

- The `/lfgquick` command has been changed to use auto-complete fields instead of a pure-string.
- Signficantly more configuration is available directly from the config:
  - commands
  - roles
  - guild name
  - debug flag
  - timeout durations for the groups
- The embed has a colour stripe that matches the state of the group:
  - Green for open
  - Yellow for full but editable
  - Blue for full and not editable
  - Red for cancelled or timed out

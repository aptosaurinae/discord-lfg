# Discord-LFG

This is a Python based system for Discord to allow easy creation of groups, using the library [`discord-py`](https://discordpy.readthedocs.io/en/stable/).

It was originally based on the Dungeon Buddy system written by Baddadan for No Pressure EU, and
is still significantly inspired by that system although has been generalised significantly.

## TODO

For feature parity with the original Dungeon Buddy, the following is missing:

- Log group members when group completes in any way (full, timeout, cancelled)
- Add `/lfgstats` reporting
- Add history for users (both personal and for mods) -
probably do this through `lfgstats` or equivalent command to avoid command clutter?
- Error handling for failed interactions?

And finally:

- Tests, Tests, Tests
- Documentation
- Look at UV for install instead of conda?

## Background

<!--- --8<-- [start:docs] -->

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

<!--- --8<-- [end:docs] -->

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

<!--- --8<-- [start:docs-running] -->

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
a valid set of configuration files.

<!--- --8<-- [end:docs-running] -->

### File setup

In order to run the bot you'll need to give it a discord bot authentication token,
as well as a configuration of where the bot is going to load into and what commands it will
load.

See the documentation for full details of the configuration setup. Some simple templates
are provided below as somewhat of a quick-start for setting up a typical 5 person dungeon group.

#### Token file

``` toml
[discord]
token = "abcd123"
```

#### Primary config

``` toml
guild_id = 123456789
guild_name = "NoP"
commands = [
    "path/to/command_file.toml"
]

[role.tank]
emoji = "<:tankemojiname:123456789>"
indicator = "t"

[role.healer]
emoji = "<:healeremojiname:123456789>"
indicator = "h"

[role.dps]
emoji = "<:dpsemojiname:123456789>"
indicator = "d"
```

#### Command configs

``` toml
name = "lfg_command"
description = "This description is shown to the user."
channel_whitelist = [
    "lfg-dungeon"
]

[channel_role_mention]
lfg-dungeon = "dungeon"

[activity]
name = "dungeon"
python_type = "str"
required = true
description = "The dungeon you are listing a key for."
options = [
    DN = "dungeon name",
]

[option.timing_aim]
name = "timing_aim"
python_type = "str"
required = true
description = "The timing type you are aiming for."
options = [
    "dungeon timing type",
]

[role_counts]
tank = 1
healer = 1
dps = 3
```

## Bot Commands

Once the bot is up and running, the commands that are active should match those defined in
the command files referenced by the main config.

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

- The backend has been generalised significantly to make it possible to create custom commands,
although still within a "looking-for-group"/"group-building" framework.
- Significantly more configuration is available directly from the config, including the definition
of different commands that use the group builder with a variety of roles or user input options.
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
- When users are removed from the group, they are notified why and blocked from rejoining.

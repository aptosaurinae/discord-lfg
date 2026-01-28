# dungeon-buddy-py

This is a Python implementation of Dungeon Buddy, using the library [`discord-py`](https://discordpy.readthedocs.io/en/stable/).

## Background

Dungeon Buddy is a Discord bot for easy creation of groups for World of Warcraft dungeons.
These groups typically have one tank, one healer, and three damage dealers in each group. Dungeon Buddy
provides a structured embed with buttons for joining groups, making it easier to track Discord
usernames when groups are formed, providing passwords only to those who sign up enabling a link
between the Discord signup and the in-game signup.

The [original Dungeon Buddy](https://bit.ly/3ZrVj7C) was built by Baddadan/Kashual using `DiscordJS` for
the [No Pressure EU](https://no-pressure.eu) Discord server. This is an implementation of the same system in Python using [discord-py](https://discordpy.readthedocs.io/en/latest/api.html).

## To do

For feature parity with the original Dungeon Buddy, the following is missing:

- Log group members when group completes in any way (full, timeout, cancelled)
- Add `/lfgstats` reporting
- Add history for users (both personal and for mods)
- Error handling for failed interactions?

## Installation and setup

### Installation

<!--- --8<-- [start:docs-install-general] -->

To install dungeon-buddy-py (db_py), we recommend using the [conda](https://docs.conda.io/en/latest/) package manager,
accessible from the terminal by installing [miniforge](https://github.com/conda-forge/miniforge?tab=readme-ov-file#download).

Note that the `discord-py` package is not up to date on conda, so you will need to add this from `pip` after
setting up the environment initially with `conda`.

<!--- --8<-- [end:docs-install-general] -->

#### As a user

<!--- --8<-- [start:docs-install-user] -->

``` shell
git clone git@github.com:aptosaurinae/dungeon-buddy-py.git
cd dungeon-buddy-py
conda env create -n dungeon-buddy-py -f requirements/base.txt
conda activate dungeon-buddy-py
pip install discord-py
pip install --no-deps -e .
```

<!--- --8<-- [end:docs-install-user] -->

#### Development / Contributing

<!--- --8<-- [start:docs-install-dev] -->

``` shell
git clone git@github.com:aptosaurinae/dungeon-buddy-py.git
cd dungeon-buddy-py
conda env create -n dungeon-buddy-py -f requirements/base.txt -f dev.txt
conda activate dungeon-buddy-py
pip install discord-py
pip install --no-deps -e .
```

This will enable `pre-commit` and `pytest`.

<!--- --8<-- [end:docs-install-dev] -->

### Running

To run the bot you can then do the following:

``` shell
python bot.py path/to/token.toml path/to/config.toml
```

which should result in something like the following:

``` shell
(discord-bot-db) D:\Programming\github-repos\dungeon-buddy-py>python bot.py "D:\Programming\dungeon-buddy-config\test_token.toml" "D:\Programming\dungeon-buddy-config\test_config.toml"
[2026-01-04 15:24:28] [INFO    ] discord.client: logging in using static token
[2026-01-04 15:24:31] [INFO    ] discord.gateway: Shard ID None has connected to Gateway (Session ID: <id number>).
Logged in as app-commands-test#2842 (ID: <app id number>)
------
Dungeon Buddy started
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
expansion = "tww"
season = "3"

[emojis]
tank = "<:tankemojiname:123456789>"
healer = "<:healeremojiname:123456789>"
dps = "<:dpsemojiname:123456789>"
```

- `guild_id` is the Discord ID of the server that you are wanting the host the bot in.
- The `expansion` and `season` match a valid dungeon lookup file in `/resources/dungeons`.
- *Optional*: `guild_name` modifies the automatic listing group names and filled spots.
- *Optional*: `emojis` dictionary for each of `tank`, `healer`, and `dps`.
If you don't provide these then Dungeon Buddy will default to using 🛡️, 🪄, ⚔️ for each role.
The emoji names and numbers need to match the names and IDs of the emojis in the server you are hosting the bot.
The names can be found as the ":name:" names in the server.
The IDs can be found by right clicking on the emojis in the server you're in and opening the link,
then looking at the number of their name in the URL.
- *Optional*: `timeout_length`, a float in minutes. This controls how long the listing exists for before
timing out. This is a float, so can be set to 0.1 or similar for testing purposes.
- *Optional*: `editable_length`, a float in minutes. This controls how long the listing is able to
be edited for once the group is full.
- *Optional*: `debug`, set to 1 to turn on debug mode, which will be more verbose in the console
and enable `/lfgdebug` which is a pre-set listing for test purposes.
- *Optional*: `log_folder`, set this to a folder that already exists and it will dump a log file here.

If you need to add a new dungeon pool, create a new `toml` file in the `/resources/dungeons` file
where each line is a short name reference to a long name string e.g.

``` toml
EDA = "Eco-dome Al'dani"
```

## Bot Commands

Once the bot is up and running, the following commands should be available from within the relevant server.

`/lfg` - create a group for the dungeon. Choose desired dungeon > dungeon difficulty > timed/completed > your role >
required roles from a drop-down style menu.

`/lfgquick` - create a group using autocomplete fields instead of an interactive drop down menu system.

[NYI] `/lfghistory` - check up-to 10 of your latest groups. Previous teammates & passphrases can be found here.

[NYI] `/lfgstats` - check total groups created, groups created in the last 24h, 7d, 30d &
also the most popular dungeons for each key range.

## License

This project has inherited the license from the original Dungeon Buddy, as below.

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
- More config flags are available, including:
  - `debug`
  - `timeout_length`
  - `guild_name`
- A default set of standard emojis (🛡️, 🪄, ⚔️) is applied if emojis are not configured.
- The embed has a colour stripe that matches the state of the group:
  - Green for open
  - Yellow for full but editable
  - Blue for full and not editable
  - Red for cancelled or timed out

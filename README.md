# dungeon-buddy-py

This is a Python implementation of Dungeon Buddy, using the library [`discord-py`](https://discordpy.readthedocs.io/en/stable/).

## Background

Dungeon Buddy is a Discord bot for easy creation of groups for World of Warcraft dungeons. These groups have one tank, one healer, and three damage dealers in each group. Dungeon Buddy provides a structured embed with buttons for joining groups, making it easier to track Discord usernames when groups are formed, providing passwords only to those who sign up enabling a link between the Discord signup and the in-game signup.

The [original Dungeon Buddy](https://bit.ly/3ZrVj7C) was built by Baddadan/Kashual using DiscordJS for the [No Pressure EU](https://no-pressure.eu) Discord server. This is an implementation of the same system in Python.

## Installation and setup

### Installation

To install dungeon-buddy-py, we recommend using the [conda](https://docs.conda.io/en/latest/) package manager, accessible from the terminal by installing [miniforge](https://github.com/conda-forge/miniforge?tab=readme-ov-file#download).

``` shell
git clone git@github.com:aptosaurinae/dungeon-buddy-py.git
cd dungeon-buddy-py
conda create -n discord-bot-db -c conda-forge --file environment.yml
conda activate discord-bot-db
pip install --no-deps -e .
```

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
```

You should find that the bot slash commands are then active in the relevant server.

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
expansion = "tww"
season = "3"
```

where `guild_id` is the Discord ID of the server that you are wanting the host the bot in, and the expansion and season match a valid dungeon lookup file in `/resources/dungeons`.

If you need to add a new dungeon pool, create a new `toml` file in the `/resources/dungeons` file where each line is a short name reference to a long name string e.g.

``` toml
EDA = "Eco-dome Al'dani"
```

## Bot Commands

Once the bot is up and running, the following commands should be available from within the relevant server.

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

If you have questions about the licensing terms, please contact Baddadan/Kashual at the [No Pressure](https://discord.gg/nopressureeu)
discord server.

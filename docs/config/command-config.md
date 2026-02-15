# Command configs

There are a set of required elements for each command, and then some optional settings.

## Config Elements

### Required Elements

#### Command Name

The name of the slash command shown to users. Do not include the leading slash.

- Format: `str`
- Example: `name = lfg_dungeon`

#### Command Description

The description shown within Discord when viewing the list of slash commands.

- Format: `str`
- Example: `Creates a LFG listing for a standard dungeon group`

#### Channel Whitelist

A list of the channels where this command should be active.
Note that due to the limitations of the command system, commands are registered to a "guild"
(i.e. a Discord server) rather than being able to limit them to specific channels.
This channel whitelist will be checked when the command is used and if the channel is not
in the whitelist then users will be told they cannot use the command here.

There is a hard-coded override for a channel named `#bot-control` to make sure that there is always
a testing ground for all commands.

- Format: `list[str]`
- Example: `channel_whitelist = ["#lfg-m0"]`

#### Channel Role Mentions

A lookup of what role name should be used for pings in which channel. Role mentions are
constructed as:

`<role_name><channel_role_mention>`

- Format: `dict[str, str]`
- Example:
    ``` toml
    [channel_role_mentions]
    lfg-m0 = "-m0"
    ```

e.g. if a group is listed looking for a `tank` role, then this would mean that the role
`tank-m0` would be pinged if it exists in the server. If this role doesn't exist then the role
will just not be pinged.

Roles mentions are not case sensitive when setting them up in this way. You can capitalise the
role names within Discord however you like and the comparison will be on a fully lowercase version.

#### Activity Definition

A dictionary including a number of elements defining the activities that users can choose between.
An activity list must be provided as it is used to construct the group name
(taking the first 3 letters and upper-casing them).
Activities need the following elements:

- display_name: The name of the activity
    - Format: `str`
- python_type: The way that python stores the activity type, used for validation when the user
inputs a value.
    - Format: one of `"str"`, `"int"`, or `"float"`
- description: The description displayed to the user when choosing an activity from the list
    - Format: `str`
- options: A list of options for the user to choose between.
    - Format: `list[str]`
- options_from_channel_numbers: **If this is `true` then the `options` list will be ignored.**
Whether to construct a list of numbers for input based on the
numbers included in the channel name.
If there is a single number in the channel name then this number will be available as an option.
If there are two numbers in the channel name then these numbers will be used as the start and end
of a range, e.g. `lfg-2-5` would make the valid inputs be `[2, 3, 4, 5]`.
    - Format: `bool`

Example:

``` toml
[activity]
display_name = "dungeon"
python_type = "str"
description = "The dungeon you are forming a group for."
options = ["Blackrock Spire", "Stratholme"]
```

#### Role Counts

A dictionary showing how many spots there should be in a group.
The names used in this dictionary must be defined in the primary config.

- Format: `dict[str, int]`
- Example:
    ``` toml
    [role_counts]
    tank = 1
    healer = 1
    dps = 3
    ```

### Optional Elements

#### Timeout Length

The length of time in minutes before a group that has been listed times out if not full.

- Format: `float`
- Example: `timeout_length = 30.0`

#### Editable Length

The length of time in minutes before a group that has been filled is locked for editing.
This provides time for the creator to review the applicants in-game and remove them if they find
that they don't meet any requirements.

- Format: `float`
- Example: `editable_length = 2.0`

#### Kick Reasons

A list of reasons that creators can select from when kicking signees from the group.
By default there will always be one base option of
`Other - please message separately`.

- Format: `list[str]`
- Example: `kick_reasons = ["Not experienced enough"]`

#### Additional Option Definitions

Other information can be requested from the group lead, as input elements either required or not.
These option sets follow the format of the `Activity` input although with an additional flag:

- required: Whether the option is required to be input by the user.
    - Format: `bool`

Examples:

``` toml
[option.difficulty]
display_name = "difficulty"
python_type = "str"
description = "The difficulty level of the dungeon."
options = ["Normal", "Heroic"]
required = true
```

``` toml
[option.key_level]
display_name = "key_level"
python_type = "str"
description = "The key level of the mythic dungeon."
options_from_channel_numbers = true
required = true
```

Additional options will be displayed in the group listing as information for potential joiners
but otherwise are not used.

## Example config

``` toml
name = "lfg_command"
description = "This description is shown to the user."
channel_whitelist = [
    "lfg-dungeons",
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

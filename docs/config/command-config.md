#### Command configs

The commands config files need to look like the following:

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

- `name`: The name of the slash command used by users.
- `description`: The text description shown to users.
- `channel_whitelist`: A list of strings of the channels that you want this command to be active
in. If `bot-control` is not included then it will be added to the list.
- `channel_role_mention`: A dictionary of channel name to role-mention, where the role which is
mentioned is constructed as `<role-name>-<role-mention>`.
e.g. a specification here of `dungeon` with a role of `tank` would make the role that you need
to set up in Discord for it to be mentioned is `tank-dungeon`. This doesn't care about
capitalisation so your discord role name could be `Tank-Dungeon` or `tAnK-DuNgEoN`.
- *Optional*: `timeout_length`, a float in minutes. This controls how long the listing exists for before
timing out. Default is 30 minutes.
- *Optional*: `editable_length`, a float in minutes. This controls how long the listing is able to
be edited for once the group is full. Default is 5 minutes.
- *Optional*: `kick_reasons`, a list of strings defining reasons a creator can kick users from
this type of group.
- `activity` is a definition of the list of activities a user can pick from. This requires:
  - `name`: the displayed name of this option for discord users
  - `python_type` (one of "str", "int", "float")
  - `required`: whether this is a required field or not
  - `description`: the description displayed to users
  - `options`: a list of options for the user to choose from.
  - *Special Optional* `options_from_channel_numbers`: If this is set to `true` then a list of
  options will be generated from the channel name. The name will be parsed for numbers, and if
  there is one number it will be the only option, or if there are two numbers then they will be
  used to generate a range of numbers. e.g. `#lfg-m2-m4` will generate a list of `[2, 3, 4]` to
  as choices, while `#lfg-m0` would generate a single element list `[0]`.
  Channels without numbers stop that specific command working, apart from the special `bot-control`
  channel which will generate a list of 1-10 for testing purposes.
- *Optional* `option.name` are additional definitions of the same format as `activity`
which give additional options for the user when setting up the group.
- `role_counts` is a lookup of role name to count. You don't have to include all roles here.

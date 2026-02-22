"""Test functions for `group_builder.py`."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import discord
import pytest

from discord_lfg.commands import CommandArgument, CommandConfig
from discord_lfg.group_builder import GroupBuilder
from discord_lfg.utils import RoleDefinition


class TestGroupBuilder:
    @pytest.fixture(scope="class")
    def discord_interaction(self):
        user = Mock()
        user.id = 123
        user.name = "testuser"
        user.display_name = "interaction_user_display_name"

        interaction = AsyncMock()
        interaction.user = user

        interaction.response = AsyncMock()
        interaction.response.send_message = AsyncMock()

        interaction.followup = AsyncMock()
        interaction.followup.send = AsyncMock()

        return interaction

    @pytest.fixture(scope="class")
    def blank_group_info(self):
        return {"activity_name": "blank", "listed_as": "", "creator_notes": "", "extra_info_1": ""}

    @pytest.fixture(scope="class")
    def blank_command(self):
        return CommandArgument(
            name="command_argument",
            python_type=str,
            required=False,
            description="",
            autocomplete_options=[],
            autocomplete_channel_numbers=False,
            display_name="",
        )

    @pytest.fixture(scope="class")
    def basic_role(self) -> RoleDefinition:
        return RoleDefinition(name="role1", count=2, emoji="🔷", identifier="r")

    def blank_config(self, command, roles):
        return CommandConfig(
            [command],
            roles,
            name="command_name",
            description="",
            debug=False,
            guild_name="",
            timeout_length=1,
            editable_length=1,
            kick_reasons=[],
            channel_whitelist=[],
            channel_role_mentions={},
            guild_roles=[],
        )

    @pytest.fixture(scope="class")
    def basic_config(self, blank_command, basic_role):
        return self.blank_config(blank_command, {basic_role.name: basic_role})

    @pytest.fixture(scope="class")
    def typical_group(self, basic_config, discord_interaction, blank_group_info):
        return GroupBuilder(
            interaction=discord_interaction,
            group_info=blank_group_info,
            config=basic_config,
            creator_role="role1",
            filled_spots={},
        )

    def test_group_state_initialises_when_given_typical_inputs(
        self, typical_group: GroupBuilder, basic_config: CommandConfig
    ):
        assert typical_group.state.command_name == basic_config.name
        assert typical_group.state.created_at < datetime.now(tz=timezone.utc) + timedelta(
            seconds=1
        ) and typical_group.state.created_at > datetime.now(tz=timezone.utc) + timedelta(seconds=-1)
        assert typical_group.state.close_group_at < (
            datetime.now(tz=timezone.utc)
            + timedelta(minutes=basic_config.timeout_length, seconds=1)
        ) and typical_group.state.close_group_at > (
            datetime.now(tz=timezone.utc)
            + timedelta(minutes=basic_config.timeout_length, seconds=-1)
        )
        assert typical_group.state.editable_length == basic_config.editable_length
        assert not typical_group.state.closed
        assert not typical_group.state.cancelled
        assert not typical_group.state.timed_out
        assert typical_group.state.empty_spots == 1
        assert typical_group.state.filled_spots == 0
        assert typical_group.state.filled_spot_name == "~~Filled Spot~~"
        assert typical_group.state.debug == basic_config.debug

    def test_group_roles_initialises_when_given_typical_inputs(
        self, typical_group: GroupBuilder, basic_role: RoleDefinition
    ):
        assert isinstance(typical_group.roles, dict)
        assert len(typical_group.roles) == 1
        assert list(typical_group.roles) == [basic_role.name]
        assert typical_group.roles[basic_role.name].name == basic_role.name
        assert len(typical_group.roles[basic_role.name].users) == basic_role.count
        assert len(typical_group.roles[basic_role.name].assigned) == basic_role.count
        assert typical_group.roles[basic_role.name].emoji == basic_role.emoji
        assert typical_group.roles[basic_role.name].role_mention == ""

    def test_group_details_initialises_when_given_typical_inputs(
        self,
        typical_group: GroupBuilder,
        blank_group_info: dict,
        blank_command: CommandArgument,
        basic_role: RoleDefinition,
    ):
        config = self.blank_config(blank_command, {basic_role.name: basic_role})
        assert typical_group.group_details.activity_name == blank_group_info.get("activity_name")
        assert typical_group.group_details.listed_as != blank_group_info.get("listed_as")
        assert typical_group.group_details.creator_notes == blank_group_info.get("creator_notes")
        assert typical_group.group_details.extra_info == [blank_group_info.get("extra_info_1", "")]
        assert typical_group.group_details.kick_reasons == config.kick_reasons

    def test_creator_initialises_when_given_typical_inputs(
        self, typical_group: GroupBuilder, discord_interaction: discord.Interaction
    ):
        assert typical_group.creator.name == discord_interaction.user.name
        assert typical_group.creator.id == discord_interaction.user.id
        assert typical_group.creator.display_name == discord_interaction.user.display_name

    def test_discord_string_display_includes_roles_when_given_typical_inputs(
        self, typical_group: GroupBuilder, basic_role: RoleDefinition
    ):
        assert typical_group.description.count(basic_role.emoji) == basic_role.count

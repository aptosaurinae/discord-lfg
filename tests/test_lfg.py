"""Test functions for `lfg.py`."""

import pytest

from discord_lfg import lfg
from discord_lfg.utils import RoleDefinition


@pytest.fixture(scope="module")
def roles_simple():
    return {"test": RoleDefinition("test", 2, "🟥", "t")}


@pytest.fixture(scope="module")
def roles_dungeon():
    return {
        "tank": RoleDefinition("tank", 1, "🛡️", "t"),
        "healer": RoleDefinition("healer", 1, "🪄", "h"),
        "dps": RoleDefinition("dps", 3, "⚔️", "d"),
    }


class TestValidateLfgInputs:
    def test_filled_spots_is_too_large_raises_error(self, roles_dungeon):
        with pytest.raises(
            lfg.LFGValidationError, match="You cannot assign that many filled spots to that role"
        ):
            lfg._validate_lfg_inputs("tank", {"tank": 1}, roles_dungeon)

    def test_all_spots_are_filled_raises_error(self, roles_dungeon):
        with pytest.raises(
            lfg.LFGValidationError, match="You cannot list a group with no available spots"
        ):
            lfg._validate_lfg_inputs("tank", {"tank": 0, "healer": 1, "dps": 3}, roles_dungeon)


class TestConvertShortFilledSpotsToFull:
    def test_no_filled_roles_returns_dictionary_of_zeros(self, roles_simple):
        result = lfg._convert_short_filled_spots_to_full(roles_simple, "")
        expected = {"test": 0}
        assert result == expected

    def test_single_filled_role_returns_dictionary_with_count(self, roles_simple):
        result = lfg._convert_short_filled_spots_to_full(roles_simple, "t")
        expected = {"test": 1}
        assert result == expected

    def test_complex_filled_roles_returns_dictionary_with_counts(self, roles_dungeon):
        result = lfg._convert_short_filled_spots_to_full(roles_dungeon, "thddd")
        expected = {"tank": 1, "healer": 1, "dps": 3}
        assert result == expected

    def test_erroneous_identifier_is_ignored(self, roles_simple):
        result = lfg._convert_short_filled_spots_to_full(roles_simple, "thd")
        expected = {"test": 1}
        assert result == expected

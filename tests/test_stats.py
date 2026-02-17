"""Test functions for `stats.py`."""

import tempfile
from datetime import date
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from discord_lfg import stats

DATES_LIST = [
    {"year": 2026, "month": 1, "day": 1},
    {"year": 2020, "month": 1, "day": 2},
    {"year": 2026, "month": 4, "day": 1},
]


class TestWriteData:
    @pytest.fixture(scope="class")
    def df(self, request):
        date_values = []
        for items in request.param:
            date_values.append(date(**items))
        return pl.DataFrame({"date_finished": date_values}, schema={"date_finished": pl.Date})

    @pytest.mark.parametrize(
        "df",
        [tuple([data]) for data in DATES_LIST]
        + [pytest.param({"year": 2026, "month": 1, "day": 50}, marks=pytest.mark.xfail)],
        indirect=["df"],
    )
    def test_single_date_writes_successfully(self, df):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            stats._write_data(tmp_path, df)

            partitions = list(tmp_path.iterdir())
            assert partitions
            assert len(partitions) == 1

    @pytest.mark.parametrize("df", [DATES_LIST], indirect=["df"])
    def test_multi_date_writes_multi_files(self, df):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            stats._write_data(tmp_path, df)

            partitions = list(tmp_path.iterdir())
            assert partitions
            assert len(partitions) == 3


class TestGetData:
    def test_partitioned_data_reads_as_single_table(self):
        result = stats.get_data(Path(__file__).parent / "fixture_data" / "lfg_data")

        date_values = []
        for items in DATES_LIST:
            date_values.append(date(**items))
        expected = pl.DataFrame({"date_finished": date_values}, schema={"date_finished": pl.Date})

        assert_frame_equal(result, expected, check_row_order=False)

    def test_non_existant_folder_returns_empty_df(self):
        result = stats.get_data(Path(__file__).parent / "non_existant_folder")
        assert result.is_empty()

"""Test functions for `stats.py`."""

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
    def test_single_date_writes_successfully(self, tmp_path: Path, df: pl.DataFrame):
        tmp_path = tmp_path / "write_data"
        stats._write_data(tmp_path / "write_data", df)

        partitions = list(tmp_path.iterdir())
        assert partitions, "no data was written"
        assert len(partitions) == 1, "only one date should be written"

    @pytest.mark.parametrize("df", [DATES_LIST], indirect=["df"])
    def test_multi_date_writes_multi_files(self, tmp_path: Path, df: pl.DataFrame):
        tmp_path = tmp_path / "write_data"
        stats._write_data(tmp_path, df)

        partitions = list(tmp_path.iterdir())
        assert partitions, "no data was written"
        assert len(partitions) == 3, "three dates should be written"

    @pytest.mark.parametrize("df", [DATES_LIST], indirect=["df"])
    def test_filter_reduces_output_df_to_single_value(self, tmp_path: Path, df: pl.DataFrame):
        tmp_path = tmp_path / "write_data"
        stats._write_data(tmp_path, df, filter_date=date(**DATES_LIST[0]))

        partitions = list(tmp_path.iterdir())
        assert partitions, "no data was written"
        assert len(partitions) == 1, "only one date should be written"


class TestGetData:
    def test_partitioned_disk_data_reads_as_single_table(self):
        result = stats.get_data(Path(__file__).parent / "fixture_data" / "lfg_data")

        date_values = []
        for items in DATES_LIST:
            date_values.append(date(**items))
        df_dict = {key: [None, None, None] for key in stats.DATA_SCHEMA}
        df_dict["date_finished"] = date_values
        expected = pl.DataFrame(df_dict, schema=stats.DATA_SCHEMA)

        assert_frame_equal(result, expected, check_row_order=False)

    def test_non_existant_folder_returns_empty_df(self):
        result = stats.get_data(Path(__file__).parent / "non_existant_folder")
        assert result.is_empty(), "the dataframe should be empty"

    def test_non_existant_folder_returns_df_with_expected_columns(self):
        result = stats.get_data(Path(__file__).parent / "non_existant_folder")
        columns = [
            "command_name",
            "date_finished",
            "activity_name",
            "listed_as",
            "creator_notes",
            "creator_id",
            "extra_info",
            "role_names",
            "user_ids",
            "user_display_names",
        ]
        assert result.columns == columns, "the dataframe should have a standard set of columns"


class TestRecordGroup:
    @pytest.fixture(scope="class")
    def setup_data(self):
        return stats.get_data(None)

    @pytest.fixture(scope="class")
    def record_data(self):
        return {
            "command_name": "lfg_test",
            "date_finished": date(2026, 1, 1),
            "activity_name": "test",
            "listed_as": "test group 1",
            "creator_notes": "creator notes test",
            "creator_id": 1,
            "extra_info": ["extra", "info"],
            "role_names": ["role1", "role2"],
            "user_ids": [1, 2],
            "user_display_names": ["user1", "user2"],
        }

    def test_typical_input_is_written_to_data(self, setup_data, record_data: dict):
        assert_frame_equal(
            stats.DATA, pl.DataFrame({key: [] for key in record_data}), check_dtypes=False
        )

        stats.record_group(**record_data)
        expected = pl.DataFrame({key: [value] for key, value in record_data.items()})

        assert_frame_equal(stats.DATA, expected)


if __name__ == "__main__":
    date_values = []
    for items in DATES_LIST:
        date_values.append(date(**items))
    df_dict = {key: [None, None, None] for key in stats.DATA_SCHEMA}
    df_dict["date_finished"] = date_values
    df = pl.DataFrame(df_dict, schema=stats.DATA_SCHEMA)
    df.write_parquet(
        Path(__file__).parent / "fixture_data" / "lfg_data", partition_by="date_finished"
    )

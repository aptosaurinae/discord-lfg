"""Manages stats logging."""

from pathlib import Path

import polars as pl


def get_data(data_path: Path):
    """Gets the existing data ready to append to (for warm-starting the bot)."""
    if data_path.exists():
        return pl.read_parquet(data_path)
    else:
        return pl.DataFrame()


def _write_data(data_path: Path, df: pl.DataFrame):
    df.write_parquet(data_path, compression="lz4", partition_by="date")


def log_entry():
    """Logs a single entry into the database."""
    return pl.DataFrame()

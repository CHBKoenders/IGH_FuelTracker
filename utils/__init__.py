"""Data helpers, DuckDB access, and plotting — import from the submodule you need."""

from .data import (
    DIESEL_THRESHOLD,
    FUEL_LABELS,
    MA_WINDOWS,
    NOMINAL_COLS,
    REAL_COLS,
    add_real_prices,
    check_pump_prices,
    label_for,
    nested_moving_averages,
    resample_mean_sem,
    slug_for,
)

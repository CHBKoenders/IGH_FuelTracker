"""Data helpers: CBS month names, quality checks, CPI rebase, moving averages."""

import numpy as np
import pandas as pd

# CBS Perioden strings use Dutch month names
MONTH_MAP = {
    "januari": 1,
    "februari": 2,
    "maart": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "augustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}

NOMINAL_COLS = ["BenzineEuro95_1", "Diesel_2", "Lpg_3"]
REAL_COLS = ["Euro95_real", "Diesel_real", "LPG_real"]
FUEL_LABELS = ["Euro95", "Diesel", "LPG"]
DIESEL_THRESHOLD = 1.60

_LABEL_BY_COL = {
    "BenzineEuro95_1": "Euro95",
    "Euro95_real": "Euro95",
    "Diesel_2": "Diesel",
    "Diesel_real": "Diesel",
    "Lpg_3": "LPG",
    "LPG_real": "LPG",
}


def label_for(col):
    return _LABEL_BY_COL.get(col, col)


def slug_for(col):
    return label_for(col).lower()


def check_pump_prices(df, verbose=True):
    issues = []

    key_cols = ["parsed_date", "BenzineEuro95_1", "Diesel_2", "Lpg_3", "CPI"]
    na_counts = df[key_cols].isna().sum()
    if verbose:
        print("N/A counts:")
        print(na_counts.to_string())
    for col, n in na_counts.items():
        if n:
            issues.append(f"{n} N/A in {col}")

    n_dup = df.duplicated(subset=["parsed_date"]).sum()
    if verbose:
        print("duplicate dates:", n_dup)
    if n_dup:
        issues.append(f"{n_dup} duplicate dates")

    dates = pd.to_datetime(df["parsed_date"]).sort_values()
    expected = pd.date_range(dates.min(), dates.max(), freq="D")
    missing = expected.difference(pd.Index(dates))
    if verbose:
        print(
            "date gaps:",
            len(missing),
            "missing days between",
            dates.min().date(),
            "and",
            dates.max().date(),
        )
    if len(missing):
        issues.append(f"{len(missing)} missing days")
        if verbose:
            print(missing[:15].tolist())

    for col in NOMINAL_COLS:
        lo, hi = df[col].min(), df[col].max()
        bad = ~df[col].between(0.2, 4.0) & df[col].notna()
        if verbose:
            print(f"{col} range {lo:.3f}–{hi:.3f}, outside [0.2, 4.0]: {int(bad.sum())}")
        if bad.sum():
            issues.append(f"{int(bad.sum())} {col} values outside [0.2, 4.0]")

    mismatch = (df["diesel_above_1_60"] != (df["Diesel_2"] > DIESEL_THRESHOLD)).sum()
    if verbose:
        print("indicator mismatches:", int(mismatch))
    if mismatch:
        issues.append("diesel_above_1_60 does not match Diesel_2 > 1.60")

    if verbose:
        print("rows:", len(df))
        print(
            "diesel > 1.60:",
            int(df["diesel_above_1_60"].sum()),
            f"({df['diesel_above_1_60'].mean():.1%})",
        )

    if issues:
        if verbose:
            print("ISSUES:", issues)
    elif verbose:
        print("checks passed")
    return issues


def add_real_prices(df):
    """Convert nominal pump prices to December-2025 euros."""
    year = df["year"].astype(int)
    month = df["month"].astype(int)
    cpi_dec_2025 = df.loc[(year == 2025) & (month == 12), "CPI"].iloc[0]
    print("CPI Dec 2025 (2015=100):", round(float(cpi_dec_2025), 2))
    out = df.copy()
    out["Euro95_real"] = out["BenzineEuro95_1"] * cpi_dec_2025 / out["CPI"]
    out["Diesel_real"] = out["Diesel_2"] * cpi_dec_2025 / out["CPI"]
    out["LPG_real"] = out["Lpg_3"] * cpi_dec_2025 / out["CPI"]
    return out, float(cpi_dec_2025)


def resample_mean_sem(df, freq, cols, drop_years=None, date_col="parsed_date"):
    """Period mean and standard error of the mean (std / sqrt(n))."""
    g = df.groupby(pd.Grouper(key=date_col, freq=freq))[cols]
    avg = g.mean().reset_index()
    n = g.count().reset_index()
    std = g.std(ddof=1).reset_index()
    sem = avg.copy()
    for col in cols:
        sem[col] = std[col] / np.sqrt(n[col].replace(0, np.nan))
        sem[col] = sem[col].fillna(0)
    if drop_years:
        keep = ~avg[date_col].dt.year.isin(drop_years)
        avg = avg.loc[keep].reset_index(drop=True)
        sem = sem.loc[keep].reset_index(drop=True)
    return avg, sem


MA_WINDOWS = (365, 91, 30)  # year, quarter, month (days)


def nested_moving_averages(series, windows=MA_WINDOWS):
    """Centered rolling means and nested residuals.

    yearly + (quarterly − yearly) + (monthly − quarterly) = monthly MA
    """
    year_window, quarter_window, month_window = windows
    values = series.astype(float)
    yearly = values.rolling(year_window, center=True, min_periods=year_window).mean()
    quarterly = values.rolling(quarter_window, center=True, min_periods=quarter_window).mean()
    monthly = values.rolling(month_window, center=True, min_periods=month_window).mean()
    scales = pd.DataFrame(
        {
            "yearly": yearly,
            "quarterly": quarterly,
            "monthly": monthly,
            "quarterly_detail": quarterly - yearly,
            "monthly_detail": monthly - quarterly,
            "daily": values,
        }
    ).dropna()
    reconstructed = scales["yearly"] + scales["quarterly_detail"] + scales["monthly_detail"]
    err = float((reconstructed - scales["monthly"]).abs().max())
    if err > 1e-10:
        print("multiscale reconstruction error:", err)
    return scales

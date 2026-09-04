"""Data-quality checks that run at ingest. These should fail closed."""

import pandas as pd
import pytest

from utils import check_pump_prices


def _clean(n=10, diesel=1.50):
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {
            "parsed_date": dates,
            "BenzineEuro95_1": 1.80,
            "Diesel_2": diesel,
            "Lpg_3": 0.80,
            "CPI": 130.0,
            "diesel_above_1_60": diesel > 1.60,
        }
    )


def test_clean_frame_passes():
    assert check_pump_prices(_clean(), verbose=False) == []


def test_null_price_is_flagged():
    df = _clean()
    df.loc[3, "Diesel_2"] = pd.NA
    issues = check_pump_prices(df, verbose=False)
    assert any("N/A in Diesel_2" in i for i in issues)


def test_duplicate_date_is_flagged():
    df = pd.concat([_clean(), _clean().iloc[[0]]], ignore_index=True)
    issues = check_pump_prices(df, verbose=False)
    assert any("duplicate dates" in i for i in issues)


def test_calendar_gap_is_flagged():
    df = _clean(n=10).drop(index=4)
    issues = check_pump_prices(df, verbose=False)
    assert any("missing days" in i for i in issues)


def test_price_out_of_bounds_is_flagged():
    df = _clean()
    df.loc[2, "Lpg_3"] = 9.99
    issues = check_pump_prices(df, verbose=False)
    assert any("Lpg_3" in i and "outside" in i for i in issues)


def test_indicator_must_match_diesel():
    df = _clean(diesel=1.50)
    df["diesel_above_1_60"] = True
    issues = check_pump_prices(df, verbose=False)
    assert any("diesel_above_1_60" in i for i in issues)


def test_ingest_aborts_on_issues(monkeypatch):
    from utils.database import ingest

    bad = _clean()
    bad.loc[0, "Diesel_2"] = pd.NA

    monkeypatch.setattr("utils.database.fetch_pump_prices", lambda: bad)
    monkeypatch.setattr("utils.database.parse_dates_and_indicator", lambda df: df)
    monkeypatch.setattr("utils.database.join_cpi", lambda df: df)
    monkeypatch.setattr("utils.database.write_table", lambda *a, **k: 0)

    with pytest.raises(RuntimeError, match="quality checks failed"):
        ingest()

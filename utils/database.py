"""CBS download, date parsing, CPI join, DuckDB read/write."""

from pathlib import Path

import cbsodata
import duckdb
import pandas as pd

from .data import MONTH_MAP, DIESEL_THRESHOLD, add_real_prices, check_pump_prices

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "fuel_prices.duckdb"
PLOTS_DIR = ROOT / "plots"
RAW_TABLE = "raw_pump_prices"
CURATED_TABLE = "pump_prices"
CBS_PUMP = "80416ned"
CBS_CPI = "83131NED"


def write_table(df, table_name, db_path=DB_PATH):
    con = duckdb.connect(str(db_path))
    con.register("df_in", df)
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_in")
    n = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    con.close()
    print(f"wrote {n} rows -> {db_path}:{table_name}")
    return n


def read_table(table_name, db_path=DB_PATH, order_by=None):
    con = duckdb.connect(str(db_path), read_only=True)
    sql = f"SELECT * FROM {table_name}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    frame = con.execute(sql).df()
    con.close()
    return frame


def fetch_pump_prices():
    return pd.DataFrame(cbsodata.get_data(CBS_PUMP))


def parse_dates_and_indicator(df):
    out = df.copy()
    out["diesel_above_1_60"] = out.Diesel_2 > DIESEL_THRESHOLD
    out[["year", "weekday", "day", "month_name"]] = out["Perioden"].str.split(
        " ", expand=True
    )
    out["month"] = out["month_name"].str.lower().map(MONTH_MAP)
    out["parsed_date"] = pd.to_datetime(out[["year", "month", "day"]])
    return out


def fetch_cpi_monthly():
    cpi = pd.DataFrame(
        cbsodata.get_data(
            CBS_CPI,
            filters="startswith(Bestedingscategorieen,'T001112')",
        )
    )
    # CBS also ships yearly totals (Perioden = "2024"); keep months only.
    n_tokens = cpi["Perioden"].str.split().str.len()
    cpi = cpi.loc[n_tokens > 1].copy()
    cpi[["year", "month_name"]] = cpi["Perioden"].str.split(" ", expand=True)
    cpi["month"] = cpi["month_name"].str.lower().map(MONTH_MAP)
    cpi["year"] = cpi["year"].astype(str).str.strip().astype(int)
    return cpi


def join_cpi(df):
    cpi = fetch_cpi_monthly()
    out = df.copy()
    out["year"] = out["year"].astype(str).str.strip().astype(int)
    out = out.merge(
        cpi[["year", "month", "CPI_1"]].rename(columns={"CPI_1": "CPI"}),
        on=["year", "month"],
        how="left",
    )
    # 83131NED currently ends 2025-12; later days reuse the last CPI.
    out = out.sort_values("parsed_date")
    out["CPI"] = out["CPI"].ffill()
    print("missing CPI:", int(out["CPI"].isna().sum()))
    return out


def ingest():
    """Download CBS, write raw + curated tables. A re-run always replaces."""
    raw = fetch_pump_prices()
    write_table(raw, RAW_TABLE)
    df = parse_dates_and_indicator(raw)
    df = join_cpi(df)
    issues = check_pump_prices(df)
    if issues:
        raise RuntimeError("quality checks failed:\n- " + "\n- ".join(issues))
    df, _cpi_2025 = add_real_prices(df)
    write_table(df, CURATED_TABLE)
    return df, issues

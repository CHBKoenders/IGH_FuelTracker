from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from utils.database import CURATED_TABLE, read_table

app = FastAPI()


def load_prices():
    df = read_table(CURATED_TABLE, order_by="parsed_date")
    df["parsed_date"] = df["parsed_date"].astype(str).str[:10]
    return df[
        [
            "parsed_date",
            "BenzineEuro95_1",
            "Diesel_2",
            "Lpg_3",
            "Euro95_real",
            "Diesel_real",
            "LPG_real",
            "diesel_above_1_60",
            "CPI",
        ]
    ]


@app.get("/")
def redirect_docs():
    return RedirectResponse("/docs")


@app.get("/meta")
def meta():
    df = load_prices()
    return {
        "rows": int(len(df)),
        "start": df["parsed_date"].iloc[0],
        "end": df["parsed_date"].iloc[-1],
    }


@app.get("/latest")
def latest():
    return load_prices().iloc[-1].to_dict()


@app.get("/prices")
def prices(start: str | None = None, end: str | None = None):
    """All rows, or a date range (YYYY-MM-DD)."""
    df = load_prices()
    if start:
        df = df[df["parsed_date"] >= start]
    if end:
        df = df[df["parsed_date"] <= end]
    return df.to_dict(orient="records")


@app.get("/prices/{day}")
def price_on_day(day: str):
    df = load_prices()
    hit = df[df["parsed_date"] == day]
    if hit.empty:
        raise HTTPException(status_code=404, detail=f"no row for {day}")
    return hit.iloc[0].to_dict()


@app.get("/diesel/below_160")
def diesel_below_160():
    """Days where diesel is at or below €1.60 (nominal)."""
    df = load_prices()
    return df[~df["diesel_above_1_60"]].to_dict(orient="records")

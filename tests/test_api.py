from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_meta():
    body = client.get("/meta").json()
    assert body["rows"] > 7000
    assert body["start"] < body["end"]


def test_latest():
    body = client.get("/latest").json()
    assert "Diesel_2" in body
    assert "Diesel_real" in body
    assert "parsed_date" in body



def test_prices_full_table():
    rows = client.get("/prices").json()
    assert len(rows) == client.get("/meta").json()["rows"]


def test_prices_range():
    rows = client.get("/prices", params={"start": "2024-01-01", "end": "2024-01-31"}).json()
    assert len(rows) == 31
    assert rows[0]["parsed_date"] == "2024-01-01"
    assert rows[-1]["parsed_date"] == "2024-01-31"


def test_prices_on_day():
    r = client.get("/prices/2024-06-15")
    assert r.status_code == 200
    assert r.json()["parsed_date"] == "2024-06-15"


def test_missing_day():
    assert client.get("/prices/1999-01-01").status_code == 404


def test_diesel_below_160():
    rows = client.get("/diesel/below_160").json()
    assert rows
    assert all(not r["diesel_above_1_60"] for r in rows)

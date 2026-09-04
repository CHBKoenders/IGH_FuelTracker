# FuelTracker

Dagelijkse Nederlandse pompprijzen (Euro95, diesel, LPG) van het CBS,
opgeslagen in DuckDB, gecontroleerd, en geplot.

Bronnen: [CBS 80416ned](https://opendata.cbs.nl/statline/#/CBS/nl/dataset/80416ned)
(pompprijzen) en [CBS 83131NED](https://opendata.cbs.nl/statline/#/CBS/nl/dataset/83131NED)
(CPI, 2015=100). Reeks vanaf 2006.

---

## Installeren

Python 3.10+. In deze map:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Eerste run heeft netwerk nodig (CBS Open Data).

## Draaien

```bash
python run.py
```

Dat doet achtereenvolgens:

1. Pompprijzen en CPI downloaden.
2. CPI koppelen op jaar-maand. Dagen zonder CPI krijgen de laatst bekende waarde.
3. Kwaliteitschecks (nulls, dubbele datums, kalendergaten, prijsgrenzen). Bij falen stopt de run.
4. Tabellen schrijven naar `fuel_prices.duckdb` (`CREATE OR REPLACE`).
5. Grafieken schrijven naar `plots/`.

Queryen:

```python
import duckdb
con = duckdb.connect("fuel_prices.duckdb")
con.sql("SELECT parsed_date, Diesel_2, Diesel_real, CPI FROM pump_prices LIMIT 5").show()
```

---

## Data

| Tabel | Inhoud |
|---|---|
| `raw_pump_prices` | CBS-extract, ongewijzigd |
| `pump_prices` | datums, indicator, CPI, prijzen in euro’s van 2025 |

Kolommen in `pump_prices`: `parsed_date`, `BenzineEuro95_1`, `Diesel_2`,
`Lpg_3`, `diesel_above_1_60`, `year`, `month`, `CPI`, `Euro95_real`,
`Diesel_real`, `LPG_real`.

```
real = nominaal × CPI_dec_2025 / CPI
```

`CPI_dec_2025` is de CPI van december 2025.

---

## Plots

`run.py` schrijft:

| Bestand | Inhoud |
|---|---|
| `diesel_vs_160.png` | Diesel versus €1,60 (nominaal) |
| `diesel_vs_160_real.png` | Idem, euro’s van 2025 |
| `multiscale_yearly.png` | 365-daags voortschrijdend gemiddelde |
| `multiscale_yq.png` | Diesel: 365- + 91-daags gemiddelde |
| `multiscale_monthly.png` | Maandcomponent (30-daags minus 91-daags) |
| `multiscale_zoom.png` | Twee periodes, vier tijdschalen |
| `weekday_real.png` | Boxplots per weekdag |
| `spectrum_season.png` | Kalenderprofiel t.o.v. 365-daags EMA |
| `spectrum_season_stability.png` | Dat profiel per periode (Euro95) |
| `spectrum_spectrogram.png` | Spectrogram van diesel |

`analysis/*.run(df, plots_dir)` schrijft dezelfde analyses per brandstof
(`real=True` voor euro’s van 2025). `run.py` houdt de slide-bestanden over.

---

## Layout

```
FuelTracker/
  run.py              inladen + slide-grafieken
  api.py              FastAPI
  utils/
    data.py           checks, rebase, moving averages
    database.py       CBS, joins, DuckDB
    plotting.py       matplotlib-helpers
  analysis/           één module per analyse
  tests/
  plots/
  fuel_prices.duckdb
```

---

## API

`api.py` is een FastAPI-app op de curated tabel.

| Pad | Inhoud |
|---|---|
| `/meta` | aantal rijen, start, eind |
| `/latest` | laatste dag |
| `/prices` | hele tabel, of `?start=&end=` (YYYY-MM-DD) |
| `/prices/{dag}` | één dag |
| `/diesel/below_160` | dagen met diesel ≤ €1,60 |

`pytest tests/test_api.py` dekt deze endpoints.

---

## Tests

Ingest voert de kwaliteitschecks uit en schrijft niet bij falen.
`pytest` herhaalt dat op synthetische frames:

```bash
pytest
```

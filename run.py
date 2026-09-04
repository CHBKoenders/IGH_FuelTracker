"""Ingest CBS pump prices into DuckDB and write the slide charts."""

import matplotlib

matplotlib.use("Agg")

from analysis.multiscale import write_slides as multiscale_slides
from analysis.spectrum import write_slides as spectrum_slides
from analysis.threshold import run as threshold
from analysis.weekday import run as weekday
from utils.database import CURATED_TABLE, PLOTS_DIR, ingest, read_table


def _clear_plots(plots_dir):
    plots_dir.mkdir(exist_ok=True)
    for path in plots_dir.glob("*.png"):
        path.unlink()


def write_slide_charts(df, plots_dir):
    _clear_plots(plots_dir)
    threshold(df, plots_dir, cols=["Diesel_2"])
    threshold(df, plots_dir, cols=["Diesel_real"], real=True)
    weekday(df, plots_dir, real=True)
    multiscale_slides(df, plots_dir)
    spectrum_slides(df, plots_dir)
    print("plots in", plots_dir)


def analyse():
    df = read_table(CURATED_TABLE, order_by="parsed_date")
    print("analysis from DuckDB:", df.shape, list(df.columns))
    write_slide_charts(df, PLOTS_DIR)
    return df


def main():
    ingest()
    analyse()


if __name__ == "__main__":
    main()

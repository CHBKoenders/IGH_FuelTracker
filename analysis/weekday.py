"""Weekday boxplots. Pass real=True for 2025 euros."""

from utils.plotting import plot_weekday_boxplots

from utils import FUEL_LABELS, NOMINAL_COLS, REAL_COLS


def run(df, plots_dir, real=False):
    cols = REAL_COLS if real else NOMINAL_COLS
    kind = "euro's van 2025" if real else "nominaal"
    name = "weekday_real.png" if real else "weekday.png"
    plot_weekday_boxplots(
        df,
        cols,
        labels=FUEL_LABELS,
        title=f"Pompprijzen per weekdag ({kind})",
        outfile=plots_dir / name,
    )

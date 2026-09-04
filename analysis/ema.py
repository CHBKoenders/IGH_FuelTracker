"""Exponential moving averages. Pass real=True for 2025 euros."""

from utils.plotting import plot_ema

from utils import FUEL_LABELS, NOMINAL_COLS, REAL_COLS

SPANS = (30, 90, 365)


def run(df, plots_dir, real=False):
    cols = REAL_COLS if real else NOMINAL_COLS
    kind = "euro's van 2025" if real else "nominaal"
    ylabel = "euro 2025 / liter" if real else "euro / liter"
    suffix = "_real" if real else ""
    for span in SPANS:
        plot_ema(
            df, cols, span=span, labels=FUEL_LABELS, ylabel=ylabel,
            title=f"{span}-daags exponentieel voortschrijdend gemiddelde ({kind}, band = ±1 SE)",
            outfile=plots_dir / f"ema_{span}d{suffix}.png",
        )

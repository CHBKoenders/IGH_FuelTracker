"""Nested moving averages: year overlay, then year+quarter / month leftover / zoom per fuel."""

from utils.plotting import (

    plot_monthly_leftover,
    plot_scale_zoom,
    plot_yearly_ma,
    plot_yearly_quarterly,
)
from utils import FUEL_LABELS, REAL_COLS, label_for, slug_for

ZOOM_WINDOWS = [
    ("2014-01-01", "2016-12-31", "2014–2016"),
    ("2022-01-01", "2023-06-30", "2022"),
]


def run(df, plots_dir, cols=None):
    """One overlay for all cols, then a slugged detail set per fuel."""
    cols = list(cols) if cols is not None else list(REAL_COLS)
    labels = [label_for(col) for col in cols]
    plot_yearly_ma(
        df, cols, labels=labels, ylabel="euro 2025 / liter",
        title="365-daags voortschrijdend gemiddelde (euro's van 2025)",
        outfile=plots_dir / "multiscale_yearly.png",
    )
    for col in cols:
        slug = slug_for(col)
        plot_yearly_quarterly(
            df, col=col, ylabel="euro 2025 / liter",
            outfile=plots_dir / f"multiscale_yq_{slug}.png",
        )
        plot_monthly_leftover(df, col=col, outfile=plots_dir / f"multiscale_monthly_{slug}.png")
        plot_scale_zoom(
            df, col=col, windows=ZOOM_WINDOWS, ylabel="euro 2025 / liter",
            outfile=plots_dir / f"multiscale_zoom_{slug}.png",
        )


def write_slides(df, plots_dir):
    """The four charts used on the slides (all fuels on year, diesel on the rest)."""
    plot_yearly_ma(
        df, REAL_COLS, labels=FUEL_LABELS, ylabel="euro 2025 / liter",
        title="365-daags voortschrijdend gemiddelde (euro's van 2025)",
        outfile=plots_dir / "multiscale_yearly.png",
    )
    plot_yearly_quarterly(
        df, col="Diesel_real", ylabel="euro 2025 / liter",
        outfile=plots_dir / "multiscale_yq.png",
    )
    plot_monthly_leftover(df, col="Diesel_real", outfile=plots_dir / "multiscale_monthly.png")
    plot_scale_zoom(
        df, col="Diesel_real", windows=ZOOM_WINDOWS, ylabel="euro 2025 / liter",
        outfile=plots_dir / "multiscale_zoom.png",
    )

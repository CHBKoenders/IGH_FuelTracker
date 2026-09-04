"""Calendar profile and spectrogram of 2025-euro pump prices.

Prices wander like a random walk, so we first subtract a 365-day EMA.
What remains is the leftover used in the spectrogram and the day-of-year
profile.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
from scipy import signal

from utils.plotting import (

    BLUE,
    MUTED,
    NAVY,
    ORANGE,
    RED,
    SLIDE_FIGSIZE,
    color_for,
    save_figure,
    style_ax,
)
from utils import REAL_COLS, label_for, slug_for

PERIOD_LABELS = [(7, "week"), (30, "maand"), (91, "kwartaal"), (365, "jaar")]


def subtract_year_ema(series, span=365):
    values = series.astype(float)
    ema = values.ewm(span=span, min_periods=span, adjust=False).mean()
    return (values - ema).dropna()


def plot_spectrogram(series, dates, label, outfile=None, show=False, title=None):
    values = np.asarray(series, dtype=float)
    values = values - np.nanmean(values)
    nperseg = 512
    freq, time, spec = signal.spectrogram(
        values,
        fs=1.0,
        nperseg=nperseg,
        noverlap=int(nperseg * 0.85),
        detrend="constant",
        scaling="density",
    )
    period = 1 / np.maximum(freq, 1e-12)
    band = (period >= 8) & (period <= 400)
    order = np.argsort(period[band])
    period_band = period[band][order]
    spec_band = spec[band][order]
    times = dates[0] + pd.to_timedelta(time, unit="D")

    fig, ax = plt.subplots(figsize=SLIDE_FIGSIZE)
    cmap = LinearSegmentedColormap.from_list(
        "igh", ["#001749", "#0046C4", "#E63321", "#F0C14A"]
    )
    mesh = ax.pcolormesh(
        times,
        period_band,
        10 * np.log10(spec_band + 1e-18),
        shading="gouraud",
        cmap=cmap,
    )
    ax.set_yscale("log")
    ax.set_ylim(8, 400)
    for days, name in PERIOD_LABELS:
        if 8 <= days <= 400:
            ax.axhline(days, color="white", lw=0.6, ls="--", alpha=0.55)
            ax.text(times[0], days, " " + name, va="bottom", color="white", fontsize=8)
    ax.set_ylabel("Periode (dagen)")
    ax.set_title(
        title or f"Spectrogram van {label} (residu t.o.v. 365-daags EMA)",
        loc="left",
    )
    style_ax(ax, date=True)
    fig.colorbar(mesh, ax=ax, label="dB", pad=0.01)
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.055, right=0.94, top=0.86, bottom=0.13),
    )


def plot_calendar_profile(residuals, outfile=None, show=False, title=None):
    fig, ax = plt.subplots(figsize=SLIDE_FIGSIZE)
    for i, col in enumerate(residuals):
        color = color_for(col, i)
        frame = residuals[col].to_frame("leftover")
        frame["day_of_year"] = frame.index.dayofyear
        frame = frame[frame["day_of_year"] <= 365]
        grouped = frame.groupby("day_of_year")["leftover"].agg(["mean", "std", "count"])
        grouped["se"] = grouped["std"] / np.sqrt(grouped["count"])
        ax.plot(grouped.index, grouped["mean"], color=color, lw=1.8, label=label_for(col))
        ax.fill_between(
            grouped.index,
            grouped["mean"] - grouped["se"],
            grouped["mean"] + grouped["se"],
            color=color, alpha=0.18, linewidth=0,
        )
    ax.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335])
    ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.axhline(0, color=MUTED, lw=0.8)
    style_ax(ax)
    ax.legend(loc="upper left", ncol=max(1, len(residuals)))
    ax.set_ylabel("euro 2025 / liter  (t.o.v. 365-daags EMA)")
    ax.set_xlabel("Maand")
    ax.set_title(
        title or "Kalenderprofiel t.o.v. 365-daags EMA (euro's van 2025, band = ±1 SE)",
        loc="left",
    )
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.055, right=0.985, top=0.86, bottom=0.13),
    )


def plot_calendar_stability(series, label, outfile=None, show=False, title=None):
    periods = [
        (2006, 2012, "2006–2012"),
        (2013, 2019, "2013–2019"),
        (2020, 2025, "2020–2025"),
    ]
    fig, ax = plt.subplots(figsize=SLIDE_FIGSIZE)
    full_leftover = subtract_year_ema(series).to_frame("leftover")
    full_leftover["day_of_year"] = full_leftover.index.dayofyear
    full_leftover = full_leftover[full_leftover["day_of_year"] <= 365]
    full_profile = full_leftover.groupby("day_of_year")["leftover"].mean()
    ax.plot(full_profile.index, full_profile, color=NAVY, lw=2.2, label="hele reeks", zorder=3)

    for (start_year, end_year, name), color in zip(periods, [ORANGE, RED, BLUE]):
        slice_ = series[(series.index.year >= start_year) & (series.index.year <= end_year)]
        leftover = subtract_year_ema(slice_).to_frame("leftover")
        leftover["day_of_year"] = leftover.index.dayofyear
        leftover = leftover[leftover["day_of_year"] <= 365]
        profile = leftover.groupby("day_of_year")["leftover"].mean()
        corr = float(np.corrcoef(full_profile.reindex(profile.index), profile)[0, 1])
        ax.plot(profile.index, profile, color=color, lw=1.3, label=f"{name}  (r = {corr:.2f})")
        print(f"calendar stability {label} {name}: corr vs full = {corr:.2f}")
    ax.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335])
    ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.axhline(0, color=MUTED, lw=0.8)
    style_ax(ax)
    ax.legend(loc="upper left", ncol=4)
    ax.set_ylabel("euro 2025 / liter")
    ax.set_title(
        title or f"Kalenderprofiel {label} per periode (euro's van 2025)",
        loc="left",
    )
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.055, right=0.985, top=0.86, bottom=0.13),
    )


def run(df, plots_dir, cols=None):
    """Spectrogram, calendar profile and stability for each fuel in cols."""
    cols = list(cols) if cols is not None else list(REAL_COLS)
    indexed = df.sort_values("parsed_date").set_index("parsed_date")
    residuals = {col: subtract_year_ema(indexed[col]) for col in cols}
    plot_calendar_profile(residuals, outfile=plots_dir / "spectrum_season.png")
    for col in cols:
        leftover = residuals[col]
        label = label_for(col)
        slug = slug_for(col)
        plot_spectrogram(
            leftover.to_numpy(), leftover.index, label=label,
            outfile=plots_dir / f"spectrum_spectrogram_{slug}.png",
        )
        plot_calendar_stability(
            indexed[col], label=label,
            outfile=plots_dir / f"spectrum_season_stability_{slug}.png",
        )


def write_slides(df, plots_dir):
    """The three charts used on the slides."""
    indexed = df.sort_values("parsed_date").set_index("parsed_date")
    residuals = {col: subtract_year_ema(indexed[col]) for col in REAL_COLS}
    diesel = residuals["Diesel_real"]
    plot_spectrogram(
        diesel.to_numpy(), diesel.index, label="Diesel",
        outfile=plots_dir / "spectrum_spectrogram.png",
    )
    plot_calendar_profile(residuals, outfile=plots_dir / "spectrum_season.png")
    plot_calendar_stability(
        indexed["Euro95_real"], label="Euro95",
        outfile=plots_dir / "spectrum_season_stability.png",
    )

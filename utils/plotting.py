"""Matplotlib helpers. All figures are the 16:9 slide box."""

import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from .data import label_for, nested_moving_averages

NAVY = "#071F65"
RED = "#E63321"
ORANGE = "#F05213"
BLUE = "#0046C4"
MUTED = "#6B7380"
GRID = "#E8EBF0"
SPINE = "#D0D5DE"
BELOW = "#1F8A70"

FUEL_COLORS = {
    "BenzineEuro95_1": RED,
    "Euro95_real": RED,
    "Diesel_2": NAVY,
    "Diesel_real": NAVY,
    "Lpg_3": ORANGE,
    "LPG_real": ORANGE,
}

SLIDE_FIGSIZE = (11.90, 5.00)
SLIDE_DPI = 180
DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
WEEKDAY_LABELS = ["ma", "di", "wo", "do", "vr", "za", "zo"]


def _apply_style():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Calibri", "DejaVu Sans", "Arial"],
            "axes.titlesize": 14,
            "axes.titlecolor": NAVY,
            "axes.titleweight": "regular",
            "axes.titlepad": 10,
            "axes.labelsize": 11,
            "axes.labelcolor": MUTED,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.dpi": SLIDE_DPI,
            "savefig.facecolor": "white",
            "savefig.edgecolor": "none",
        }
    )


_apply_style()


def color_for(col, i=0):
    palette = [RED, NAVY, ORANGE]
    return FUEL_COLORS.get(col, palette[i % len(palette)])


def style_ax(ax, date=False):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SPINE)
    ax.spines["bottom"].set_color(SPINE)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, length=3, width=0.6)
    if date:
        ax.xaxis.set_major_formatter(
            mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())
        )


def save_figure(fig, outfile=None, show=False, margins=None):
    if margins:
        fig.subplots_adjust(**margins)
    if outfile is not None:
        fig.savefig(outfile, dpi=SLIDE_DPI, facecolor="white")
        print("wrote", outfile)
    if show:
        plt.show()
    else:
        plt.close(fig)
    return fig


def plot_lines(
    df,
    cols,
    labels=None,
    ylabel=None,
    title=None,
    date_col="parsed_date",
    sem=None,
    markers=False,
    outfile=None,
    show=False,
):
    labels = labels or cols
    fig, ax = plt.subplots(figsize=SLIDE_FIGSIZE)
    for i, (col, label) in enumerate(zip(cols, labels)):
        color = color_for(col, i)
        kw = {"label": label, "color": color, "lw": 1.8}
        if markers:
            kw.update(
                marker="o",
                markersize=5.5,
                markerfacecolor="white",
                markeredgecolor=color,
                markeredgewidth=1.2,
            )
        ax.plot(df[date_col], df[col], **kw)
        if sem is not None:
            ax.fill_between(
                df[date_col],
                df[col] - sem[col],
                df[col] + sem[col],
                color=color,
                alpha=0.18,
                linewidth=0,
            )
    style_ax(ax, date=True)
    ax.legend(loc="upper left", ncol=len(cols))
    if title:
        ax.set_title(title, loc="left")
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.set_xlim(df[date_col].min(), df[date_col].max())
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.055, right=0.985, top=0.86, bottom=0.13),
    )


def plot_weekday_boxplots(
    df,
    cols,
    labels=None,
    title=None,
    note=None,
    date_col="parsed_date",
    outfile=None,
    show=False,
):
    labels = labels or cols
    plot_df = df.copy()
    plot_df["_day_num"] = plot_df[date_col].dt.weekday
    plot_df["_day_name"] = pd.Categorical(
        plot_df[date_col].dt.day_name(), categories=DAY_ORDER, ordered=True
    )
    plot_df = plot_df.sort_values("_day_num")

    fig, axes = plt.subplots(1, len(cols), figsize=SLIDE_FIGSIZE, squeeze=False)
    for i, (ax, col, label) in enumerate(zip(axes[0], cols, labels)):
        color = color_for(col, i)
        bp = plot_df.boxplot(
            column=col, by="_day_name", ax=ax, grid=False,
            whis=(0, 100), patch_artist=True, return_type="dict",
        )
        if isinstance(bp, pd.Series):
            bp = bp.iloc[0]
        for box in bp["boxes"]:
            box.set_facecolor(color)
            box.set_alpha(0.18)
            box.set_edgecolor(color)
            box.set_linewidth(1.2)
        for med in bp["medians"]:
            med.set_color(RED)
            med.set_linewidth(1.6)
        for whisk in bp["whiskers"] + bp["caps"]:
            whisk.set_color(MUTED)
        ax.set_title(label, loc="left", color=NAVY)
        ax.set_xlabel("")
        ax.set_ylabel("euro / liter" if i == 0 else "")
        ax.set_xticklabels(WEEKDAY_LABELS)
        style_ax(ax)
    fig.suptitle(title or "", color=NAVY, fontsize=14, x=0.055, ha="left")
    if note:
        fig.text(0.055, 0.02, note, ha="left", va="bottom", fontsize=9, color=MUTED, style="italic")
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.055, right=0.985, top=0.82, bottom=0.14, wspace=0.28),
    )


def plot_vs_threshold(
    df,
    col,
    threshold,
    title=None,
    ylabel=None,
    date_col="parsed_date",
    above_col=None,
    fill_label=None,
    label=None,
    outfile=None,
    show=False,
):
    label = label or label_for(col)
    plot_df = df.sort_values(date_col)
    x = plot_df[date_col]
    y = plot_df[col]
    if above_col is None:
        mask = (y < threshold).to_numpy()
    else:
        mask = ~plot_df[above_col].astype(bool).to_numpy()
    if fill_label is None:
        fill_label = f"onder €{threshold:.2f}".replace(".", ",")

    fig, ax = plt.subplots(figsize=SLIDE_FIGSIZE)
    ax.plot(x, y, lw=1.1, color=color_for(col), label=label)
    ax.axhline(threshold, color=RED, ls="--", lw=1.4, label=f"€{threshold:.2f}".replace(".", ","))
    ax.fill_between(
        x, y, threshold, where=mask, interpolate=True,
        alpha=0.28, color=BELOW, label=fill_label,
    )
    span = max(float(y.max() - threshold), float(threshold - y.min()), 0.05)
    ax.set_ylim(threshold - span * 1.08, threshold + span * 1.08)
    style_ax(ax, date=True)
    if title:
        ax.set_title(title, loc="left")
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.legend(loc="upper left", ncol=3)
    ax.set_xlim(x.min(), x.max())
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.055, right=0.985, top=0.86, bottom=0.13),
    )


def plot_ema(
    df,
    cols,
    span,
    labels=None,
    ylabel=None,
    title=None,
    date_col="parsed_date",
    outfile=None,
    show=False,
):
    labels = labels or cols
    plot_df = df.sort_values(date_col).set_index(date_col)
    alpha = 2 / (span + 1)
    n_eff = (2 - alpha) / alpha
    n = len(cols)
    fig, axes = plt.subplots(n, 1, figsize=SLIDE_FIGSIZE, sharex=True, squeeze=False)
    for i, (ax, col, label) in enumerate(zip(axes[:, 0], cols, labels)):
        color = color_for(col, i)
        s = plot_df[col].astype(float)
        ewm = s.ewm(span=span, min_periods=int(span), adjust=False)
        mean = ewm.mean()
        sem = ewm.std() / np.sqrt(n_eff)
        ax.plot(mean.index, mean.to_numpy(), color=color, lw=1.5)
        ax.fill_between(
            mean.index, (mean - sem).to_numpy(), (mean + sem).to_numpy(),
            color=color, alpha=0.22, linewidth=0,
        )
        style_ax(ax, date=(i == n - 1))
        if ylabel:
            ax.set_ylabel(ylabel)
        ax.set_title(label, loc="left", fontsize=12, color=NAVY)
        ax.set_xlim(mean.index.min(), mean.index.max())
    if title:
        fig.suptitle(title, color=NAVY, fontsize=14, x=0.055, ha="left")
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.055, right=0.985, top=0.88, bottom=0.10, hspace=0.42),
    )


def _rms_eurocents(series):
    return float(np.sqrt(np.mean(np.square(series.to_numpy(dtype=float))))) * 100


def plot_yearly_ma(
    df, cols, labels=None, ylabel=None, title=None,
    date_col="parsed_date", outfile=None, show=False,
):
    labels = labels or cols
    plot_df = df.sort_values(date_col).set_index(date_col)
    fig, ax = plt.subplots(figsize=SLIDE_FIGSIZE)
    for i, (col, label) in enumerate(zip(cols, labels)):
        y = nested_moving_averages(plot_df[col])["yearly"]
        ax.plot(y.index, y.to_numpy(), color=color_for(col, i), lw=2.2, label=label)
    style_ax(ax, date=True)
    ax.legend(loc="upper left", ncol=len(cols))
    if title:
        ax.set_title(title, loc="left")
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.set_xlim(y.index.min(), y.index.max())
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.055, right=0.985, top=0.86, bottom=0.13),
    )


def plot_yearly_quarterly(
    df, col, ylabel=None, title=None,
    date_col="parsed_date", outfile=None, show=False,
):
    label = label_for(col)
    if title is None:
        title = f"{label}: 365-daags en 91-daags voortschrijdend gemiddelde (euro's van 2025)"
    plot_df = df.sort_values(date_col).set_index(date_col)
    scales = nested_moving_averages(plot_df[col])
    t = scales.index
    yearly, quarterly = scales["yearly"], scales["quarterly"]
    fig, ax = plt.subplots(figsize=SLIDE_FIGSIZE)
    ax.fill_between(
        t, yearly, quarterly, color=ORANGE, alpha=0.35, linewidth=0,
        label="kwartaal − jaar",
    )
    ax.plot(t, yearly.to_numpy(), color=NAVY, lw=2.4, label="365-daags gemiddelde")
    ax.plot(t, quarterly.to_numpy(), color=ORANGE, lw=1.5, label="91-daags gemiddelde")
    style_ax(ax, date=True)
    ax.legend(loc="upper left", ncol=3)
    ax.set_title(title, loc="left")
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.set_xlim(t.min(), t.max())
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.055, right=0.985, top=0.86, bottom=0.13),
    )


def plot_monthly_leftover(
    df, col, title=None, date_col="parsed_date", outfile=None, show=False,
):
    if title is None:
        title = (
            f"Maandcomponent {label_for(col)}: "
            "30-daags minus 91-daags gemiddelde (euro's van 2025)"
        )
    plot_df = df.sort_values(date_col).set_index(date_col)
    scales = nested_moving_averages(plot_df[col])
    leftover_cents = scales["monthly_detail"] * 100
    monthly_rms = _rms_eurocents(scales["monthly_detail"])
    quarterly_rms = _rms_eurocents(scales["quarterly_detail"])
    print(f"multiscale RMS  quarterly={quarterly_rms:.1f} ct  monthly={monthly_rms:.1f} ct")

    fig, ax = plt.subplots(figsize=SLIDE_FIGSIZE)
    ax.fill_between(leftover_cents.index, 0, leftover_cents.to_numpy(), color=RED, alpha=0.28, linewidth=0)
    ax.plot(leftover_cents.index, leftover_cents.to_numpy(), color=RED, lw=1.0)
    ax.axhline(0, color=NAVY, lw=1.0)
    ax.axhline(monthly_rms, color=MUTED, ls=":", lw=0.9)
    ax.axhline(-monthly_rms, color=MUTED, ls=":", lw=0.9)
    style_ax(ax, date=True)
    ax.set_ylabel("eurocent / liter")
    ax.set_title(title, loc="left")
    ax.set_xlim(leftover_cents.index.min(), leftover_cents.index.max())
    ax.text(
        0.99, 0.06,
        f"RMS {monthly_rms:.1f} ct   (kwartaalcomponent: {quarterly_rms:.1f} ct)",
        transform=ax.transAxes, ha="right", va="bottom", color=MUTED, fontsize=10,
    )
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.06, right=0.985, top=0.86, bottom=0.13),
    )


def plot_scale_zoom(
    df, col, windows, ylabel=None, title=None,
    date_col="parsed_date", outfile=None, show=False,
):
    if title is None:
        title = f"{label_for(col)} in twee periodes, vier tijdschalen (euro's van 2025)"
    plot_df = df.sort_values(date_col).set_index(date_col)
    scales = nested_moving_averages(plot_df[col])
    fig, axes = plt.subplots(1, len(windows), figsize=SLIDE_FIGSIZE, sharey=False, squeeze=False)
    for ax, (start, end, label) in zip(axes[0], windows):
        window = slice(start, end)
        daily = scales["daily"].loc[window]
        ax.plot(daily.index, daily.to_numpy(), color=MUTED, lw=0.6, alpha=0.55, label="dag")
        ax.plot(scales["monthly"].loc[window].index, scales["monthly"].loc[window].to_numpy(),
                color=RED, lw=1.8, label="30-daags")
        ax.plot(scales["quarterly"].loc[window].index, scales["quarterly"].loc[window].to_numpy(),
                color=ORANGE, lw=2.0, label="91-daags")
        ax.plot(scales["yearly"].loc[window].index, scales["yearly"].loc[window].to_numpy(),
                color=NAVY, lw=2.4, label="365-daags")
        style_ax(ax, date=True)
        ax.set_title(label, loc="left", fontsize=12, color=NAVY)
        if ylabel:
            ax.set_ylabel(ylabel)
        ax.set_xlim(daily.index.min(), daily.index.max())
    handles, leg_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, leg_labels, loc="upper right", ncol=4, frameon=False, fontsize=9)
    fig.suptitle(title, color=NAVY, fontsize=14, x=0.055, ha="left")
    return save_figure(
        fig, outfile=outfile, show=show,
        margins=dict(left=0.055, right=0.985, top=0.80, bottom=0.13, wspace=0.22),
    )

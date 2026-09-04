"""Price vs €1.60. Pass real=True for 2025 euros; cols defaults to all fuels."""

from utils.plotting import plot_vs_threshold

from utils import DIESEL_THRESHOLD, NOMINAL_COLS, REAL_COLS, label_for, slug_for


def run(df, plots_dir, cols=None, real=False, threshold=DIESEL_THRESHOLD):
    cols = list(cols) if cols is not None else list(REAL_COLS if real else NOMINAL_COLS)
    kind = "euro's van 2025" if real else "nominaal"
    ylabel = "euro 2025 / liter" if real else "euro / liter"
    suffix = "_real" if real else ""
    for col in cols:
        extra = {}
        if col == "Diesel_2":
            extra["above_col"] = "diesel_above_1_60"
        plot_vs_threshold(
            df,
            col=col,
            threshold=threshold,
            title=f"{label_for(col)} versus €1,60 ({kind})",
            ylabel=ylabel,
            outfile=plots_dir / f"{slug_for(col)}_vs_160{suffix}.png",
            **extra,
        )

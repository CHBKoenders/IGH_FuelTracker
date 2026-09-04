"""Calendar month / quarter / year means. Pass real=True for 2025 euros."""

from utils.plotting import plot_lines

from utils import FUEL_LABELS, NOMINAL_COLS, REAL_COLS, resample_mean_sem


def run(df, plots_dir, real=False):
    cols = REAL_COLS if real else NOMINAL_COLS
    kind = "euro's van 2025" if real else "nominaal"
    ylabel = "euro 2025 / liter" if real else "euro / liter"
    suffix = "_real" if real else ""
    specs = [
        ("ME", f"monthly{suffix}.png", f"Maandgemiddelde pompprijs ({kind}, band = ±1 SE)", False, None),
        ("QE", f"quarterly{suffix}.png", f"Kwartaalgemiddelde pompprijs ({kind}, band = ±1 SE)", True, None),
        ("YE", f"yearly{suffix}.png", f"Jaargemiddelde pompprijs ({kind}, band = ±1 SE)", True, [2026]),
    ]
    for freq, name, title, markers, drop_years in specs:
        avg, sem = resample_mean_sem(df, freq, cols, drop_years=drop_years)
        plot_lines(
            avg, cols, labels=FUEL_LABELS, ylabel=ylabel, title=title,
            sem=sem, markers=markers, outfile=plots_dir / name,
        )

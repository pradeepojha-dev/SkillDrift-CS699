"""SkillDrift: visualize the real Oct 15 / Nov 22 skill-demand snapshots.

Run from anywhere (after putting this file in SkillDrift-CS699/analysis):
    python analysis/08_visualize_skill_drift.py

Reads:
    outputs/skill_snapshot_2026-10-15.csv
    outputs/skill_snapshot_2026-11-22.csv

Creates only new PNG files in outputs/visualizations/; original CSVs and graphs
are never modified. Values are percentages of JOBS IN OUR SMALL SAMPLES,
not statistically established labor-market trends.
"""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
OUTPUTS = PROJECT / "outputs"
VIS_DIR = OUTPUTS / "visualizations"
OLD_DATE = "2026-10-15"
NEW_DATE = "2026-11-22"
CITIES = ("Mumbai", "Pune", "Bengaluru")
COLUMNS = ["Skill"] + [f"{city} %" for city in CITIES]


def load_snapshot(date):
    path = OUTPUTS / f"skill_snapshot_{date}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing snapshot: {path}")
    frame = pd.read_csv(path, encoding="utf-8-sig")
    required = set(COLUMNS)
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    if frame.empty or frame["Skill"].isna().any() or frame["Skill"].duplicated().any():
        raise ValueError(f"{path.name}: empty, missing or repeated skill names")
    if "Date" in frame.columns and not frame["Date"].astype(str).eq(date).all():
        raise ValueError(f"{path.name}: 'Date' column does not match {date}")
    for city in CITIES:
        col = f"{city} %"
        frame[col] = pd.to_numeric(frame[col], errors="raise")
        if frame[col].isna().any() or not frame[col].between(0, 100).all():
            raise ValueError(f"{path.name}: invalid percentages in {col}")
    return frame.set_index("Skill")[COLUMNS[1:]]


def save_heatmap(old, new):
    changes = (new - old).round(1)
    values = changes.to_numpy(dtype=float)
    limit = max(5, float(np.ceil(np.abs(values).max() / 5) * 5))
    fig, ax = plt.subplots(figsize=(10.6, 7.2))
    cmap = plt.get_cmap("RdBu")
    im = ax.imshow(values, cmap=cmap, vmin=-limit, vmax=limit, aspect="auto")
    ax.set_xticks(np.arange(len(CITIES)), CITIES, fontsize=12, fontweight="bold")
    ax.set_yticks(np.arange(len(changes)), [s.title() for s in changes.index], fontsize=11)
    ax.tick_params(axis="both", length=0, pad=10)
    for i in range(len(changes)):
        for j in range(len(CITIES)):
            val = values[i, j]
            text_color = "white" if abs(val) > 0.6 * limit else "#172335"
            ax.text(j, i, f"{val:+.1f}", ha="center", va="center",
                    color=text_color, fontsize=11, fontweight="bold")
    fig.suptitle("SkillDrift  |  October → November 2026", x=0.12, y=0.975,
                 ha="left", fontsize=19, fontweight="bold")
    fig.text(0.12, 0.925, "Change in % of sampled job postings mentioning each skill (percentage points)",
             fontsize=10.5, color="#3b4856")
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
    cbar.set_label("Percentage-point change", fontsize=10)
    fig.text(0.12, 0.025,
             "Dates: 15 Oct vs 22 Nov 2026  •  Small sample (~20–21 jobs/city/date). "
             "Colors show observed sample changes, not proven market trends.",
             fontsize=9.2, color="#555b67")
    fig.subplots_adjust(left=0.23, right=0.87, top=0.84, bottom=0.09)
    target = VIS_DIR / "01_skill_change_heatmap.png"
    fig.savefig(target, dpi=200, facecolor="white")
    plt.close(fig)
    return target


def save_city_chart(city, old, new):
    skills = list(old.index)
    y = np.arange(len(skills))
    height = 0.38
    fig, ax = plt.subplots(figsize=(11.3, 7.5))
    ax.barh(y - height/2, old[f"{city} %"], height, label="15 Oct 2026", color="#7893a9")
    ax.barh(y + height/2, new[f"{city} %"], height, label="22 Nov 2026", color="#087e87")
    ax.set_yticks(y, [s.title() for s in skills], fontsize=11)
    ax.invert_yaxis()
    ax.set_xlim(0, max(70, float(max(old[f"{city} %"].max(), new[f"{city} %"].max())) + 10))
    ax.set_xlabel("% of sampled jobs mentioning the skill", fontsize=11)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)
    for edge in ("top", "right", "left"):
        ax.spines[edge].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=10)
    ax.legend(loc="lower right", frameon=False, fontsize=10)
    ax.set_title(f"{city}  |  Skill demand in two samples", fontsize=19,
                 fontweight="bold", loc="left", pad=23)
    fig.text(0.13, 0.03,
             "Comparison of observed Naukri sample shares; not a census or a statistical market forecast.",
             fontsize=9.5, color="#555b67")
    fig.subplots_adjust(left=0.23, right=0.96, top=0.88, bottom=0.11)
    target = VIS_DIR / f"02_{city.lower()}_oct_vs_nov.png"
    fig.savefig(target, dpi=200, facecolor="white")
    plt.close(fig)
    return target


def main():
    print("SKILLDRIFT - VISUAL COMPARISON")
    print("Reading exactly these two dated snapshots:")
    print(" -", f"skill_snapshot_{OLD_DATE}.csv")
    print(" -", f"skill_snapshot_{NEW_DATE}.csv")
    old = load_snapshot(OLD_DATE)
    new = load_snapshot(NEW_DATE)
    if set(old.index) != set(new.index):
        raise ValueError("The two snapshots contain different skill sets; review before comparing")
    new = new.loc[old.index]
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    paths = [save_heatmap(old, new)]
    for city in CITIES:
        paths.append(save_city_chart(city, old, new))
    print("\nSUCCESS: Created", len(paths), "charts:")
    for path in paths:
        print(" -", path.relative_to(PROJECT))
    print("\nThe original snapshots and prior analysis outputs were NOT changed.")
    print("Reminder: rising/declining in this small sample does not establish a true market trend.")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as error:
        print("\nSTOP:", error, file=sys.stderr)
        raise SystemExit(1)

from pathlib import Path
 
import matplotlib.pyplot as plt
import nflreadpy as nfl
import pandas as pd
 
SEASONS = list(range(2021, 2026))
 
# Save outputs into a "figures" folder next to this script, so they land in the
# repo no matter which folder you run it from (falls back to the current folder
# in Jupyter, where __file__ doesn't exist).
try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    BASE_DIR = Path.cwd()
OUT_DIR = BASE_DIR / "figures"
OUT_DIR.mkdir(exist_ok=True)
 
# ---- Average EP by yard line and down ----
pbp = nfl.load_pbp(seasons=SEASONS).select(["down", "yardline_100", "ep"]).to_pandas()
pbp = pbp[pbp["down"].notna() & pbp["ep"].notna() & pbp["yardline_100"].between(1, 99)]
pbp["yardline_100"] = pbp["yardline_100"].astype(int)
pbp["down"] = pbp["down"].astype(int)
 
ep = (
    pbp.groupby(["yardline_100", "down"])["ep"].mean()
    .unstack()
    .reindex(range(1, 100))
    .rolling(5, center=True, min_periods=1).mean()  # smooth yard-to-yard noise
)
 
# x-axis runs from your own goal line (left) to the opponent's (right)
x = 100 - ep.index
 
# ---- Plot ----
fig, ax = plt.subplots(figsize=(11, 6))
colors = {1: "#1f5fa8", 2: "#3f9f5f", 3: "#e08a1e", 4: "#c23b3b"}
labels = {1: "1st down", 2: "2nd down", 3: "3rd down", 4: "4th down"}
for d in [1, 2, 3, 4]:
    ax.plot(x, ep[d], color=colors[d], linewidth=2.2, label=labels[d])
 
ax.axhline(0, color="gray", linewidth=0.8)
ax.axvline(50, color="gray", linewidth=0.8, linestyle="--")
 
ticks = list(range(0, 101, 10))
tick_labels = ["Own GL" if t == 0 else "Opp GL" if t == 100 else "50" if t == 50
               else (f"Own {t}" if t < 50 else f"Opp {100 - t}") for t in ticks]
ax.set_xticks(ticks)
ax.set_xticklabels(tick_labels)
ax.set_xlim(0, 100)
 
ax.set_xlabel("Line of scrimmage")
ax.set_ylabel("Expected points")
ax.set_title(f"nflverse expected points by field position and down "
             f"({SEASONS[0]}–{SEASONS[-1]} average)")
ax.grid(alpha=0.3)
ax.legend(frameon=False)
fig.tight_layout()
 
png_path = OUT_DIR / "ep_by_down.png"   # renders directly on GitHub
pdf_path = OUT_DIR / "ep_by_down.pdf"   # vector version for LaTeX (\includegraphics)
csv_path = OUT_DIR / "ep_by_down.csv"   # GitHub shows CSVs as a searchable table
 
fig.savefig(png_path, dpi=200, facecolor="white")
fig.savefig(pdf_path)
ep.round(2).rename_axis("yardline_100").to_csv(csv_path)
 
print("Saved:")
for p in (png_path, pdf_path, csv_path):
    print(f"  {p}")
plt.show()
# Reproducible 2025 benchmark vs nfl4th

**Prerequisites:** Google Colab with `pbp_all` (nflreadpy play-by-play, 2022–2025) and Google Drive mounted; a Mac with Python venv from this project, plus R installed and the `nfl4th` R package. The scripts run in different environments; no in-app R server is required.

1. In Colab, run your daily setup, then paste and execute `01_export_2025_colab.py`. It writes `My Drive/NFL_4th_Down_Project/benchmark/benchmark_scenarios_2025.csv`.
2. Download that CSV into this project's `benchmark/` folder.
3. Install R from https://cran.r-project.org/ and, once, in a Mac terminal run: `Rscript -e "install.packages('nfl4th', repos='https://cloud.r-project.org')"`.
4. Open VS Code terminal in the **project root**, and run `Rscript benchmark/02_run_nfl4th.R`. This writes `benchmark/nfl4th_results_2025.csv`. An internet connection is needed for package game-context resources. Some scenarios may fail to compute; the script reports failures instead of inventing results.
5. In the same project root, activate `.venv` and run: `python benchmark/03_compare_benchmark.py` (the Python requirements match `requirements.txt`). This writes `benchmark/benchmark_comparison_2025.csv` and prints aggregate statistics.

## Methodology / interpretation

- Held-out **2025** fourth-down situations are sampled (up to 30 each actually chosen go/FG/punt). The **observed choice is used only for stratified sampling**, not as a label for the right decision.
- Restrict to **regulation**, yards-to-go 1–15, `yardline_100` 16–58, 20–900 seconds remaining in quarter, score difference -35 through +35, no goal-to-go. These constraints mirror the existing decision engine. If game context is missing, that row is omitted.
- `nfl4th` requires actual home/away teams, possession team, year, game type, opening kickoff and timeouts. Do **not** benchmark a fictitious scenario without legitimate matching game context.
- Compare **go_wp**, **fg_wp**, **punt_wp** on a consistent 0–1 scale. Missing `punt_wp` / other inapplicable action makes the full-three-action comparison impossible for that row. Report both full 3-option agreement and agreement over just the choices `nfl4th` scored.
- Report agreement, WP difference MAE in percentage points, confusion table, and close-call agreement. The CSV supports plots by yardline, yards-to-go, game clock and score.
- `nfl4th` uses additional game context and different training data/model structure. Disagreement is **not** evidence either model is wrong. Our model has simplified clock and 2025 kickoff transition assumptions. Neither this benchmark nor the empirical bootstrap proves the decisions causally optimal.
- The copied ZIP **does not include the user's local `punt_outcomes.csv`**. Copy that into the `data/` folder **before** computing our predictions, otherwise our punt values will use the fallback point prediction and will not be exactly comparable to the punt-enhanced app screenshots.

References: https://www.nfl4th.com/reference/add_4th_probs.html and https://www.nfl4th.com/articles/nfl4th.html

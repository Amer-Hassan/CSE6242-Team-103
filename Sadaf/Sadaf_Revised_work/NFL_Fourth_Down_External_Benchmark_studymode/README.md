# NFL Fourth-Down Decision Explorer

Interactive Flask + D3 research prototype. It compares *estimated* win probabilities for going for it, kicking a field goal, or punting. This is just for demo for optimal-coaching decision engine.

## Start on Mac / VS Code

1. Open `NFL_Fourth_Down_Starter` in VS Code.
2. In Terminal:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python app.py
   ```
3. Open `http://127.0.0.1:5000` in your browser. D3 loads from a CDN, so internet access is needed for the chart.
4. If you already have the original `.venv`, use it, but ensure `scikit-learn==1.6.1` before loading the trusted models.

## Data and methodology

- `models/` has the **four models required by this application**: fourth-down conversion, field goal, punt field position, and win probability. The separate expected-points model was *not included* in the uploaded ZIP and is not required by this app.
- `data/conversion_outcomes.csv` contains 2022–24 successful conversion outcomes. The decision engine conditions observed gains on yards to go and, where enough samples exist, on starting field position. The engine explicitly approximates touchdowns with seven points and one average kickoff state.
- `data/field_goal_transitions.csv` contains the matched 2022–24 made/missed/blocked field-goal possessions. Only made kickoffs are used in the made-FG transition distribution; misses use a simplified kick-spot rule. Blocked and returned kicks are not separately modeled.
- Punt remains a single predicted average opponent starting position; the empirical punt outcomes needed for a distribution **were not present**.
- All transition estimates are provisional. 2025 kickoff rule changes, end-of-quarter game state, touchdown conversion choices, blocked kicks, timeouts and selection effects are incompletely represented. Do not claim the new estimates are calibrated or more accurate without external validation.
- `/api/predict` returns all three estimated win probabilities. `/api/sensitivity` compares decisions over nearby yards-to-go values.

## Suggested evaluation

Test the original and revised models on out-of-sample 2025 outcome states; report held-out distribution errors, recommendation agreement with external models (not yet measured), and behavioral usability results separately. Don't describe the modeling-output differences as performance improvements.


## Decision boundary map
Click **Generate decision map** below the sensitivity chart. The server evaluates 64 scenarios (eight field positions by eight fourth-down distances) while holding score, quarter, clock, home/away and timeouts fixed. Color shows the highest *estimated* WP; dashed squares show model gaps under 2 percentage points. Hover or keyboard-focus to inspect all outcomes; click or press Enter to load a scenario into the main controls. Re-generate after changing the game context. The map is computed on demand and cached server-side; it is not an external benchmark or validated causal decision boundary.

## Optional punt distribution upgrade (next phase)

The app works without `data/punt_outcomes.csv` and retains the previous
Random Forest point prediction for punts. To enable empirical punt variability:

1. In Google Colab, run the daily setup that loads `pbp_all` for 2022–2025.
2. Run the supplied `export_punt_outcomes_colab.py` script as a Colab cell
   (copy its contents into a cell; or `%run` it after uploading the script).
3. Download `MyDrive/NFL_4th_Down_Project/data/punt_outcomes.csv` and put it
   into this project's `data/` folder.
4. Restart Flask (`Ctrl+C`, then `python app.py`). The dashboard now shows
   the historical punt sample size and a 10th–90th percentile range of
   predicted opponent starting positions.

**Interpretation:** The engine computes empirical residuals (actual opponent
start minus the existing punt regression prediction) from 2022–24 matched
punts. It evaluates many plausible future punt states, averaging their WP.
This is **not a calibrated prediction interval**: the regression was fitted
on overlapping years and the residual spread can be optimistic. The matching
algorithm excludes many unusual plays. Do not claim 2025 validation or
uncertainty calibration until a separate held-out evaluation is completed.


## Section 05: Outcome-sampling uncertainty

Press **Analyze uncertainty** to run 400 repeat resamples of the conditional
historical outcome arrays. Displays centered percentile bootstrap ranges for
the three **fixed-model** estimates, plus a bootstrap ranking frequency and
point-estimate top-two gap range *only if* `data/punt_outcomes.csv` is present.

**Important limitations:** These are *not* calibrated uncertainty intervals
for true counterfactual win probability. The code keeps trained models,
conversion and FG success probabilities, and simplified rules fixed. It samples
observed outcomes by row rather than by game, does not capture model-training
uncertainty, and cannot correct selection bias or 2025 rule changes. The
bootstrap intervals should be described as *sensitivity to observed outcome
sampling*, not formal forecast confidence intervals. In a final report, a
better validation would retrain all models in game-level bootstrap resamples,
use held-out games, and test calibration against actual wins.

## External benchmark (2025)
See `benchmark/README_BENCHMARK.md` for the Colab export, R `nfl4th` runner, and Python comparison scripts. Benchmark results are **not** precomputed and require your Colab 2025 plays, R, and the locally exported punt data.


## Classroom evaluation / Study Mode

Open **http://127.0.0.1:5001/study** after starting Flask to run a twelve-task, counterbalanced static-vs-D3 interface study. Responses stay in the participant browser and are exported manually as CSV. See `study/README_STUDY.md` for experiment protocol, pilot instructions, and results analysis.

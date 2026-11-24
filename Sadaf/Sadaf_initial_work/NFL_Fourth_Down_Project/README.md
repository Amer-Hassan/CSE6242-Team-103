# NFL Fourth-Down Decision Explorer

Interactive Flask + D3 research prototype. It compares *estimated* win probabilities for going for it, kicking a field goal, or punting. This is **not** a validated causal or optimal-coaching decision engine.

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

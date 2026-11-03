# NFL Fourth-Down Explorer — Flask + D3 starter

## 1. Set up
Copy your own trusted `.pkl` model files from Google Drive into `models/`:
- `fourth_down_conversion_model.pkl`
- `field_goal_model.pkl`
- `punt_prediction_model.pkl`
- `win_probability_model.pkl`

The EP model is not used by the WP dashboard yet. Do not commit model files if sharing the repository publicly without checking their licenses and content.

Open this folder in VS Code, then run in its terminal:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit http://127.0.0.1:5000

## 2. Verification
With the same models and scikit-learn compatibility, the default scenario (4th & 3, opponent 40, trailing 4, Q4 5:00) should approximately reproduce Go 33.49%, FG 29.22%, Punt 26.32%.

## 3. Important limitations
- This first implementation is restricted to regulation, non-goal-to-go situations and avoids quarter boundaries.
- FG options outside the model's learned kick-distance range are omitted.
- Made-FG kickoff starts at own 30 by simplifying assumption, which is not a reliable representation of every season's NFL kickoff rules.
- Successful conversion assumes exactly the needed yards; punt uses only predicted mean field position; clock deductions and missed-FG placements are approximations.
- The WP model was trained to approximate nflverse probabilities and evaluated on actual results, but the action counterfactual engine is not validated.
- Never load untrusted pickle/joblib files.

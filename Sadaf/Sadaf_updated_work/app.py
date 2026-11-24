from flask import Flask, jsonify, render_template, request
from functools import lru_cache
from decision_engine import compare_fourth_down, estimate_outcome_uncertainty

app = Flask(__name__)


def parse_inputs(payload):
    defaults = {
        'ydstogo':3, 'yardline_100':40, 'score_differential':-4,
        'qtr':4, 'seconds_in_quarter':300, 'offense_is_home':1,
        'offense_timeouts':3, 'defense_timeouts':3,
    }
    return {k:int(payload.get(k,v)) for k,v in defaults.items()}


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/study')
def study():
    """Client-side anonymous classroom task study (no response collection server-side)."""
    return render_template('study.html')


@app.post('/api/predict')
def predict():
    try:
        inputs = parse_inputs(request.get_json(silent=True) or {})
        result = compare_fourth_down(**inputs)
        return jsonify({'scenario':inputs,**result})
    except (ValueError, TypeError, OverflowError) as exc:
        return jsonify({'error':str(exc)}),400


@app.post('/api/sensitivity')
def sensitivity():
    try:
        scenario = parse_inputs(request.get_json(silent=True) or {})
        # Evaluate near scenario +/- 2 yards-to-go, keeping target in supported range.
        distances = sorted(set(max(1,min(15,scenario['ydstogo']+delta)) for delta in (-2,-1,0,1,2)))
        points = []
        for d in distances:
            result = compare_fourth_down(**{**scenario, 'ydstogo':d})
            points.append({'ydstogo':d,**{row['name']:row['win_probability_pct'] for row in result['decisions']}})
        return jsonify({'points':points})
    except (ValueError, TypeError, OverflowError) as exc:
        return jsonify({'error':str(exc)}),400


# A fixed, reproducible grid, computed on demand rather than on each slider drag.
# Cache by the remaining scenario context so repeated map requests are instant.
FIELD_DISTANCES = (55, 50, 45, 40, 35, 30, 25, 20)
TO_GO_DISTANCES = (1, 2, 3, 4, 5, 7, 10, 15)


@lru_cache(maxsize=48)
def _boundary_grid(score_differential, qtr, seconds_in_quarter,
                   offense_is_home, offense_timeouts, defense_timeouts):
    cells = []
    for to_go in TO_GO_DISTANCES:
        for field in FIELD_DISTANCES:
            scenario = {
                'ydstogo': to_go, 'yardline_100': field,
                'score_differential': score_differential, 'qtr': qtr,
                'seconds_in_quarter': seconds_in_quarter,
                'offense_is_home': offense_is_home,
                'offense_timeouts': offense_timeouts,
                'defense_timeouts': defense_timeouts,
            }
            result = compare_fourth_down(**scenario)
            options = {d['name']:d['win_probability_pct'] for d in result['decisions']}
            cells.append({
                'yardline_100': field, 'ydstogo': to_go,
                'best_decision': result['best_decision'],
                'top_two_gap_pp': result['top_two_gap_pp'],
                'probabilities': options,
            })
    return cells


@app.post('/api/decision-boundary')
def decision_boundary():
    try:
        v = parse_inputs(request.get_json(silent=True) or {})
        # This grid varies the two dimensions below; everything else is held fixed.
        cells = _boundary_grid(
            v['score_differential'], v['qtr'], v['seconds_in_quarter'],
            v['offense_is_home'], v['offense_timeouts'], v['defense_timeouts'])
        counts = {name:sum(c['best_decision']==name for c in cells)
                  for name in ('Go for it', 'Field goal', 'Punt')}
        return jsonify({'field_positions':FIELD_DISTANCES,
                        'yards_to_go':TO_GO_DISTANCES,
                        'cells':cells, 'counts':counts,
                        'context':{key:v[key] for key in (
                            'score_differential','qtr','seconds_in_quarter',
                            'offense_is_home','offense_timeouts','defense_timeouts')},
                        'description':'Model preference across 64 scenarios; not an accuracy or causal validation.'})
    except (ValueError, TypeError, OverflowError) as exc:
        return jsonify({'error':str(exc)}),400


@app.post('/api/uncertainty')
def uncertainty():
    try:
        inputs = parse_inputs(request.get_json(silent=True) or {})
        results = estimate_outcome_uncertainty(**inputs, repetitions=400)
        return jsonify(results)
    except (ValueError, TypeError, OverflowError) as exc:
        return jsonify({'error': str(exc)}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5001)

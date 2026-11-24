from flask import Flask, jsonify, render_template, request
from decision_engine import compare_fourth_down

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


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, jsonify, render_template, request
from decision_engine import compare_fourth_down

app = Flask(__name__)

@app.get('/')
def index():
    return render_template('index.html')

@app.post('/api/predict')
def predict():
    payload=request.get_json(silent=True) or {}
    try:
        inputs={
            'ydstogo':int(payload.get('ydstogo',3)),
            'yardline_100':int(payload.get('yardline_100',40)),
            'score_differential':int(payload.get('score_differential',-4)),
            'qtr':int(payload.get('qtr',4)),
            'seconds_in_quarter':int(payload.get('seconds_in_quarter',300)),
            'offense_is_home':int(payload.get('offense_is_home',1)),
            'offense_timeouts':int(payload.get('offense_timeouts',3)),
            'defense_timeouts':int(payload.get('defense_timeouts',3)),
        }
        result=compare_fourth_down(**inputs)
        return jsonify({'scenario':inputs,**result})
    except (ValueError,TypeError) as e:
        return jsonify({'error':str(e)}),400

if __name__=='__main__':
    app.run(debug=True)

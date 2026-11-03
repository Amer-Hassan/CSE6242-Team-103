"""Prototype game-state transitions for a D3 fourth-down explorer.
All win probabilities are conditional on simplified play outcomes, not validated causal effects.
"""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parent / 'models'

def load_models():
    def load(filename):
        path = MODEL_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f'Missing model: {path}. Copy from Google Drive/models.')
        return joblib.load(path)  # load only your own trusted model files

    conversion = load('fourth_down_conversion_model.pkl')
    fg = load('field_goal_model.pkl')
    punt = load('punt_prediction_model.pkl')
    wp_package = load('win_probability_model.pkl')
    return conversion, fg, punt, wp_package['model'], list(wp_package['features'])

conversion_model, fg_model, punt_model, wp_model, wp_features = load_models()

def _features(model):
    return list(model.feature_names_in_)

def predict_wp(down, ydstogo, yardline_100, score_differential, qtr,
               game_seconds_remaining, half_seconds_remaining,
               posteam_timeouts_remaining, defteam_timeouts_remaining, offense_is_home):
    row = pd.DataFrame([locals()])
    return float(np.clip(wp_model.predict(row[wp_features])[0], 0, 1))

def compare_fourth_down(ydstogo=3, yardline_100=40, score_differential=-4,
                        qtr=4, seconds_in_quarter=300, offense_is_home=1,
                        offense_timeouts=3, defense_timeouts=3):
    # Scope matches the supported states of the training datasets and current prototype.
    if not isinstance(qtr, int) or qtr not in (1, 2, 3, 4):
        raise ValueError('Quarter must be 1–4.')
    if not 16 <= yardline_100 <= 75:
        raise ValueError('This prototype supports yardline_100 from 16 to 75 (FG model distance 33–92; longer FG is not shown).')
    if not 1 <= ydstogo <= 15 or ydstogo >= yardline_100:
        raise ValueError('Use 1–15 yards to go; goal-to-go is not supported yet.')
    if not 15 <= seconds_in_quarter <= 900:
        raise ValueError('Use 15–900 seconds remaining in the quarter.')
    if not -35 <= score_differential <= 35:
        raise ValueError('Score differential must be between -35 and +35.')
    if offense_is_home not in (0,1) or offense_timeouts not in (0,1,2,3) or defense_timeouts not in (0,1,2,3):
        raise ValueError('Invalid home/away indicator or timeout count.')

    game_s = (4-qtr)*900+seconds_in_quarter
    half_s = (900 if qtr in (1,3) else 0)+seconds_in_quarter

    base = pd.DataFrame([{
        'ydstogo':ydstogo, 'yardline_100':yardline_100,
        'score_differential':score_differential, 'game_seconds_remaining':game_s
    }])
    p_go = float(conversion_model.predict_proba(base[_features(conversion_model)])[0,1])
    fg_distance=yardline_100+17
    fg_possible=15 <= fg_distance <= 75
    p_fg=None
    if fg_possible:
        p_fg=float(fg_model.predict_proba(pd.DataFrame([{'kick_distance':fg_distance}])[_features(fg_model)])[0,1])
    punt_start=float(np.clip(punt_model.predict(base[_features(punt_model)])[0],1,99))

    def clocks(elapsed):
        return game_s-elapsed, half_s-elapsed

    def other_team_wp(opponent_yardline_100, score_after, elapsed):
        gt, ht=clocks(elapsed)
        opponent_wp=predict_wp(
            down=1, ydstogo=min(10,opponent_yardline_100),
            yardline_100=opponent_yardline_100,
            score_differential=-score_after, qtr=qtr,
            game_seconds_remaining=gt, half_seconds_remaining=ht,
            posteam_timeouts_remaining=defense_timeouts,
            defteam_timeouts_remaining=offense_timeouts,
            offense_is_home=1-offense_is_home)
        return 1-opponent_wp

    success_yardline=yardline_100-ydstogo
    gt,ht=clocks(5)
    wp_success=predict_wp(
        down=1, ydstogo=min(10,success_yardline),yardline_100=success_yardline,
        score_differential=score_differential,qtr=qtr,
        game_seconds_remaining=gt,half_seconds_remaining=ht,
        posteam_timeouts_remaining=offense_timeouts,
        defteam_timeouts_remaining=defense_timeouts,
        offense_is_home=offense_is_home)
    wp_failed=other_team_wp(100-yardline_100,score_differential,5)
    wp_go=p_go*wp_success+(1-p_go)*wp_failed

    wp_fg=None
    if fg_possible:
        # Own 30 on kickoff and default ball placement on a miss are provisional.
        wp_made=other_team_wp(70,score_differential+3,11)
        wp_missed=other_team_wp(float(np.clip(100-(yardline_100+7),1,99)),score_differential,5)
        wp_fg=p_fg*wp_made+(1-p_fg)*wp_missed
    wp_punt=other_team_wp(100-punt_start,score_differential,10)

    decisions=[{'name':'Go for it','win_probability':float(wp_go)},
               {'name':'Punt','win_probability':float(wp_punt)}]
    if wp_fg is not None:
        decisions.append({'name':'Field goal','win_probability':float(wp_fg)})
    decisions.sort(key=lambda r:r['win_probability'],reverse=True)
    best=decisions[0]['win_probability']
    for d in decisions:
        d['win_probability_pct']=round(100*d['win_probability'],2)
        d['gap_from_best_pp']=round(100*(best-d['win_probability']),2)
    return {
        'decisions':decisions,
        'best_decision':decisions[0]['name'],
        'top_two_gap_pp':round((decisions[0]['win_probability']-decisions[1]['win_probability'])*100,2),
        'outcome_models':{
            'conversion_probability':round(p_go,4),
            'field_goal_success_probability':round(p_fg,4) if p_fg is not None else None,
            'opponent_start_after_punt':round(punt_start,1)},
        'disclaimer':'Prototype only: assumes minimum conversion gain, fixed play durations, simplified missed field goal and kickoff spots, and mean punt field position. Not validated counterfactual win probabilities.'
    }

"""NFL fourth-down research explorer.

Conditional post-play states are empirical approximations, NOT measured causal
counterfactuals. Fit outcome distributions on 2022-24 only; 2025 stays held out.
"""
from pathlib import Path
from functools import lru_cache
import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / 'models'
DATA_DIR = ROOT / 'data'


def _load(name):
    path = MODEL_DIR / name
    if not path.exists():
        raise FileNotFoundError(f'Missing trained model: {path}')
    return joblib.load(path)  # Only open trusted model files.


conversion_model = _load('fourth_down_conversion_model.pkl')
fg_model = _load('field_goal_model.pkl')
punt_model = _load('punt_prediction_model.pkl')
_wp = _load('win_probability_model.pkl')
wp_model, wp_features = _wp['model'], list(_wp['features'])

conversion_data = pd.read_csv(DATA_DIR / 'conversion_outcomes.csv')
conversion_data = conversion_data.loc[
    conversion_data.season.between(2022, 2024) &
    conversion_data.ydstogo.notna() &
    conversion_data.yardline_100.between(1, 99) &
    conversion_data.yards_gained.notna() &
    (conversion_data.yards_gained >= conversion_data.ydstogo)
].copy()
fg_transitions = pd.read_csv(DATA_DIR / 'field_goal_transitions.csv')
fg_transitions = fg_transitions.loc[
    fg_transitions.season.between(2022, 2024) &
    fg_transitions.opponent_start.between(1, 99) &
    fg_transitions.elapsed_seconds.between(0, 45)
].copy()
made_kicks = fg_transitions.loc[fg_transitions.field_goal_result.eq('made')]

# Optional 2022-24 historical punt calibration observations.
# If absent, do not fabricate a punt-outcome distribution.
PUNT_DATA_FILE = DATA_DIR / 'punt_outcomes.csv'
PUNT_DISTRIBUTION_AVAILABLE = False
punt_outcomes = pd.DataFrame()
if PUNT_DATA_FILE.exists():
    _p = pd.read_csv(PUNT_DATA_FILE)
    _needed = {
        'season', 'yardline_100', 'ydstogo', 'score_differential',
        'game_seconds_remaining', 'opponent_start', 'elapsed_seconds'
    }
    if not _needed.issubset(_p.columns):
        raise ValueError(f'Punt CSV missing columns: {sorted(_needed - set(_p.columns))}')
    _p = _p.copy()
    for _c in _needed:
        _p[_c] = pd.to_numeric(_p[_c], errors='coerce')
    _p = _p.loc[
        _p.season.between(2022, 2024) &
        _p.yardline_100.between(1, 99) &
        _p.ydstogo.between(1, 40) &
        _p.opponent_start.between(1, 99) &
        _p.elapsed_seconds.between(0, 45)
    ].dropna(subset=list(_needed)).copy()
    if len(_p) >= 30:
        _features_punt = list(punt_model.feature_names_in_)
        _p['predicted_start'] = punt_model.predict(_p[_features_punt])
        _p['start_residual'] = _p['opponent_start'] - _p['predicted_start']
        punt_outcomes = _p
        PUNT_DISTRIBUTION_AVAILABLE = True

# To avoid returning hundreds of nearly identical rows for each request, use
# stable binning (quantiles over observed starts and elapsed time).


def _features(model):
    return list(model.feature_names_in_)


def _wp(states):
    if not states:
        return np.array([])
    frame = pd.DataFrame.from_records(states)
    return np.clip(wp_model.predict(frame[wp_features]), 0, 1)


def _clock(qtr, seconds_in_quarter, elapsed):
    # Limited to same-quarter outcomes; cross-quarter play transitions need
    # separate handling in a future model. Restricted to >= 20 seconds left.
    left = max(1.0, seconds_in_quarter - elapsed)
    return (4 - qtr) * 900 + left, (900 if qtr in (1, 3) else 0) + left


def _state(down, ydstogo, yardline, score, qtr, seconds, elapsed, offense_home,
           offense_timeouts, defense_timeouts):
    game_s, half_s = _clock(qtr, seconds, elapsed)
    return {
        'down': down, 'ydstogo': max(1.0, float(ydstogo)),
        'yardline_100': float(np.clip(yardline, 1, 99)),
        'score_differential': score, 'qtr': qtr,
        'game_seconds_remaining': game_s, 'half_seconds_remaining': half_s,
        'posteam_timeouts_remaining': offense_timeouts,
        'defteam_timeouts_remaining': defense_timeouts,
        'offense_is_home': offense_home,
    }


def _opponent_state(own_start, score_after, qtr, seconds, elapsed,
                    offense_home, offense_timeouts, defense_timeouts):
    # own_start is opponent's own-yard line; in nflverse's coordinate system,
    # yardline_100 for opponent is 100 - own_start.
    opp_y100 = float(np.clip(100 - own_start, 1, 99))
    return _state(1, min(10, opp_y100), opp_y100, -score_after, qtr,
                  seconds, elapsed, 1 - offense_home,
                  defense_timeouts, offense_timeouts)


@lru_cache(maxsize=512)
def _success_gains(ydstogo, yardline):
    """Empirical gain distribution conditioned on fourth-down distance and field zone.

    Smooth sparse distance buckets with nearby yards-to-go; never include
    target season 2025. Nearby sample needs >=20; otherwise use broader data.
    """
    exact = conversion_data.loc[conversion_data.ydstogo.eq(ydstogo)]
    near = exact.loc[exact.yardline_100.between(yardline - 15, yardline + 15)]
    if len(near) >= 20:
        selected = near
        method = 'Exact distance + ±15 yards field position'
    elif len(exact) >= 20:
        selected = exact
        method = 'Exact distance (all field positions)'
    else:
        close = conversion_data.loc[
            conversion_data.ydstogo.between(max(1, ydstogo - 2), ydstogo + 2) &
            conversion_data.yards_gained.ge(ydstogo)
        ]
        selected = close if len(close) >= 10 else conversion_data.loc[
            conversion_data.yards_gained.ge(ydstogo)
        ]
        method = 'Nearby distance fallback (sparse sample)'
    if selected.empty:
        return (float(ydstogo),), method, 0
    # Cap outcome count for quick UI interaction, using deterministic equally
    # spaced order statistics (retains the shape, avoids randomness in UI).
    gains = np.sort(selected.yards_gained.to_numpy(dtype=float))
    if len(gains) > 120:
        positions = np.linspace(0, len(gains)-1, 120).astype(int)
        gains = gains[positions]
    return tuple(gains.tolist()), method, len(selected)


def _made_transitions():
    return made_kicks[['opponent_start', 'elapsed_seconds']].to_numpy(dtype=float)


def _punt_residual_distribution(ydstogo, yardline):
    """Historical residuals conditioned on approximate field zone and distance.

    Punt_model was fitted on the development seasons, so these are IN-SAMPLE
    residuals, not calibrated forecast intervals; use as a provisional outcome
    spread and validate against held-out 2025 later.
    """
    if not PUNT_DISTRIBUTION_AVAILABLE:
        return None, 'No punt outcomes CSV; using point prediction', 0
    near = punt_outcomes.loc[
        punt_outcomes.yardline_100.between(yardline - 12, yardline + 12) &
        punt_outcomes.ydstogo.between(max(1, ydstogo - 3), ydstogo + 3)
    ]
    if len(near) >= 30:
        selected, method = near, 'Local field position and yards-to-go'
    else:
        zone = punt_outcomes.loc[
            punt_outcomes.yardline_100.between(yardline - 15, yardline + 15)
        ]
        if len(zone) >= 30:
            selected, method = zone, 'Field-position fallback'
        else:
            selected, method = punt_outcomes, 'All training punts fallback'
    # Stable sorted empirical quantiles avoid request-to-request jitter.
    ordered = selected.sort_values('start_residual')
    if len(ordered) > 100:
        ordered = ordered.iloc[
            np.linspace(0, len(ordered) - 1, 100).astype(int)
        ]
    return ordered[['start_residual', 'elapsed_seconds']].to_numpy(dtype=float), method, len(selected)


def compare_fourth_down(ydstogo=3, yardline_100=40, score_differential=-4,
                        qtr=4, seconds_in_quarter=300, offense_is_home=1,
                        offense_timeouts=3, defense_timeouts=3):
    if qtr not in (1, 2, 3, 4):
        raise ValueError('Choose a quarter between 1 and 4.')
    if not (16 <= yardline_100 <= 58):
        raise ValueError('Field position must be 16–58 yards from the opponent goal for a supported FG comparison.')
    if not (1 <= ydstogo <= 15) or ydstogo >= yardline_100:
        raise ValueError('Yards to go must be 1–15 and less than distance to goal (no goal-to-go).')
    if not (20 <= seconds_in_quarter <= 900):
        raise ValueError('Choose 20–900 seconds left in the quarter.')
    if not (-35 <= score_differential <= 35):
        raise ValueError('Score differential must be between -35 and 35.')
    if offense_is_home not in (0, 1) or offense_timeouts not in (0, 1, 2, 3) or defense_timeouts not in (0, 1, 2, 3):
        raise ValueError('Home indicator and timeout counts are invalid.')

    game_s, _ = _clock(qtr, seconds_in_quarter, 0)
    base = pd.DataFrame([{
        'ydstogo': ydstogo, 'yardline_100': yardline_100,
        'score_differential': score_differential,
        'game_seconds_remaining': game_s,
    }])
    p_convert = float(conversion_model.predict_proba(base[_features(conversion_model)])[0, 1])
    kick_distance = yardline_100 + 17
    p_fg = float(fg_model.predict_proba(pd.DataFrame([{'kick_distance': kick_distance}])[_features(fg_model)])[0, 1])
    punt_start = float(np.clip(punt_model.predict(base[_features(punt_model)])[0], 1, 99))

    # Go: average WP across historical successful yards, touchdown as a separate
    # approximate 7-point scoring outcome. This ignores two-point attempts and
    # factors not in the trained model. TD conversion is a separate kickoff state.
    gains, method, n_gains = _success_gains(ydstogo, yardline_100)
    success_states, success_is_opponent = [], []
    kickoff = _made_transitions()
    avg_kickoff_start = float(np.mean(kickoff[:, 0])) if len(kickoff) else 25.0
    for gain in gains:
        if gain >= yardline_100:
            success_states.append(_opponent_state(
                avg_kickoff_start, score_differential + 7, qtr,
                seconds_in_quarter, 12, offense_is_home, offense_timeouts,
                defense_timeouts))
            success_is_opponent.append(True)
        else:
            new_y = max(1.0, yardline_100 - gain)
            success_states.append(_state(
                1, min(10, new_y), new_y, score_differential, qtr,
                seconds_in_quarter, 5, offense_is_home, offense_timeouts,
                defense_timeouts))
            success_is_opponent.append(False)
    success_wps = _wp(success_states)
    success_wps[np.array(success_is_opponent, dtype=bool)] = 1 - success_wps[np.array(success_is_opponent, dtype=bool)]
    wp_success = float(success_wps.mean())
    wp_failure = float(1 - _wp([_opponent_state(
        100-yardline_100, score_differential, qtr, seconds_in_quarter,
        5, offense_is_home, offense_timeouts, defense_timeouts)])[0])
    wp_go = p_convert * wp_success + (1 - p_convert) * wp_failure

    # Made FG: use observed 2022–24 kickoff start AND elapsed time together.
    # 2025+ rule changes may produce different kickoff locations.
    if len(kickoff) > 0:
        # Deterministic compact subsample preserves empirical variation.
        sampled = kickoff[np.linspace(0, len(kickoff)-1, min(150,len(kickoff))).astype(int)]
        made_states = [_opponent_state(
            own, score_differential+3, qtr, seconds_in_quarter,
            max(5.0, elapsed), offense_is_home, offense_timeouts,
            defense_timeouts) for own, elapsed in sampled]
        wp_made = float(np.mean(1 - _wp(made_states)))
    else:
        wp_made = float(1 - _wp([_opponent_state(
            25, score_differential+3, qtr, seconds_in_quarter,
            11, offense_is_home, offense_timeouts, defense_timeouts)])[0])

    # Conventional unreturned missed FG: opponent starts at spot of kick,
    # roughly yardline_100 + 8 from their own goal, min own 20. The holder
    # position and penalties vary; blocked/returned attempts are not modeled.
    miss_start = float(np.clip(max(20, yardline_100 + 8), 1, 99))
    wp_miss = float(1 - _wp([_opponent_state(
        miss_start, score_differential, qtr, seconds_in_quarter, 5,
        offense_is_home, offense_timeouts, defense_timeouts)])[0])
    wp_fg = p_fg * wp_made + (1-p_fg) * wp_miss

    # Punt: condition empirical historical residuals on similar situations.
    # All residuals are from training seasons; outcomes are illustrative and
    # not calibrated uncertainty intervals. If the CSV is missing, retain the
    # previous point estimate explicitly.
    punt_residuals, punt_method, n_punt_outcomes = _punt_residual_distribution(
        ydstogo, yardline_100)
    if punt_residuals is not None:
        punt_starts = np.clip(punt_start + punt_residuals[:, 0], 1, 99)
        punt_states = [_opponent_state(
            own, score_differential, qtr, seconds_in_quarter,
            max(1.0, elapsed), offense_is_home, offense_timeouts,
            defense_timeouts) for own, elapsed in zip(punt_starts, punt_residuals[:, 1])]
        wp_punt = float(np.mean(1 - _wp(punt_states)))
        punt_start_p10 = round(float(np.quantile(punt_starts, 0.1)), 1)
        punt_start_p90 = round(float(np.quantile(punt_starts, 0.9)), 1)
    else:
        wp_punt = float(1 - _wp([_opponent_state(
            punt_start, score_differential, qtr, seconds_in_quarter, 10,
            offense_is_home, offense_timeouts, defense_timeouts)])[0])
        punt_start_p10 = punt_start_p90 = None
    decisions = [
        {'name':'Go for it', 'win_probability':wp_go},
        {'name':'Field goal', 'win_probability':wp_fg},
        {'name':'Punt', 'win_probability':wp_punt},
    ]
    decisions.sort(key=lambda r: r['win_probability'], reverse=True)
    best = decisions[0]['win_probability']
    for d in decisions:
        d['win_probability_pct'] = round(100*d['win_probability'], 2)
        d['gap_from_best_pp'] = round(100*(best-d['win_probability']), 2)
    return {
        'decisions':decisions, 'best_decision':decisions[0]['name'],
        'top_two_gap_pp':round(100*(decisions[0]['win_probability']-decisions[1]['win_probability']),2),
        'outcome_models':{
            'conversion_probability':round(p_convert,4),
            'field_goal_success_probability':round(p_fg,4),
            'opponent_start_after_punt':round(punt_start,1),
            'punt_outcome_method':punt_method,
            'punt_outcome_sample_size':n_punt_outcomes,
            'punt_start_p10':punt_start_p10,
            'punt_start_p90':punt_start_p90,
            'missed_fg_opponent_start':round(miss_start,1),
            'made_fg_avg_opponent_start':round(avg_kickoff_start,1),
            'conversion_gain_sample_size':n_gains,
            'conversion_gain_method':method,
            'success_gain_mean':round(float(np.mean(gains)),2),
            'success_td_fraction':round(float(np.mean(np.array(gains)>=yardline_100)),4),
        },
        'disclaimer':('Research prototype, not a validated causal recommendation. '
            'Conversion gains and made-FG kickoff states use 2022–24 observations. '
            'Missed kicks use a conventional kick-spot approximation. '
            + ('Punts use empirical in-sample residuals (not calibrated uncertainty). ' if PUNT_DISTRIBUTION_AVAILABLE else 'Punt uses a single predicted mean until punt_outcomes.csv is added. ') +
            'Clock transitions, touchdown/extra-point sequences, blocked kicks, 2025 kickoff rules, and game-end states remain simplified.'),
    }


@lru_cache(maxsize=96)
def _uncertainty_cached(ydstogo, yardline_100, score_differential, qtr,
                        seconds_in_quarter, offense_is_home, offense_timeouts,
                        defense_timeouts, repetitions):
    """Bootstrap variability of empirical outcome averages, conditional on FIXED trained models.

    This is not a confidence interval for actual counterfactual win probabilities.
    Observations are resampled at row level (not game-clustered); model-parameter
    uncertainty, nonrandom choice of fourth-down actions, and rule changes omitted.
    """
    scenario = dict(ydstogo=ydstogo, yardline_100=yardline_100,
                    score_differential=score_differential, qtr=qtr,
                    seconds_in_quarter=seconds_in_quarter,
                    offense_is_home=offense_is_home,
                    offense_timeouts=offense_timeouts,
                    defense_timeouts=defense_timeouts)
    point = compare_fourth_down(**scenario)  # Also validates input.
    game_s, _ = _clock(qtr, seconds_in_quarter, 0)
    frame = pd.DataFrame([{'ydstogo': ydstogo, 'yardline_100': yardline_100,
                           'score_differential': score_differential,
                           'game_seconds_remaining': game_s}])
    p_convert = float(conversion_model.predict_proba(
        frame[_features(conversion_model)])[0, 1])
    p_make = float(fg_model.predict_proba(pd.DataFrame([
        {'kick_distance': yardline_100 + 17}])[_features(fg_model)])[0, 1])
    predicted_punt_start = float(np.clip(punt_model.predict(
        frame[_features(punt_model)])[0], 1, 99))

    # Each array is the original offense's probability of winning after one
    # plausible outcome. Bootstrap resamples these per-outcome probabilities.
    gains, gain_method, gain_count = _success_gains(ydstogo, yardline_100)
    kickoff = _made_transitions()
    avg_kickoff = float(kickoff[:, 0].mean()) if len(kickoff) else 25.0
    go_states, turnover_flags = [], []
    for gain in gains:
        is_td = gain >= yardline_100
        turnover_flags.append(is_td)
        if is_td:
            go_states.append(_opponent_state(avg_kickoff,
                score_differential + 7, qtr, seconds_in_quarter, 12,
                offense_is_home, offense_timeouts, defense_timeouts))
        else:
            new_y = max(1, yardline_100 - gain)
            go_states.append(_state(1, min(10, new_y), new_y,
                score_differential, qtr, seconds_in_quarter, 5,
                offense_is_home, offense_timeouts, defense_timeouts))
    go_success = _wp(go_states)
    go_success[np.array(turnover_flags, dtype=bool)] = (
        1 - go_success[np.array(turnover_flags, dtype=bool)])
    go_fail = float(1 - _wp([_opponent_state(100 - yardline_100,
        score_differential, qtr, seconds_in_quarter, 5,
        offense_is_home, offense_timeouts, defense_timeouts)])[0])

    # Mirror the main engine's deterministic kickoff subsample.
    if len(kickoff):
        kickoff = kickoff[np.linspace(0, len(kickoff) - 1,
            min(150, len(kickoff))).astype(int)]
        made_states = [_opponent_state(own, score_differential + 3,
            qtr, seconds_in_quarter, max(5, elapsed),
            offense_is_home, offense_timeouts, defense_timeouts)
            for own, elapsed in kickoff]
        fg_made = 1 - _wp(made_states)
    else:
        fg_made = np.array([1 - _wp([_opponent_state(25,
            score_differential + 3, qtr, seconds_in_quarter, 11,
            offense_is_home, offense_timeouts, defense_timeouts)])[0]])
    missed_start = np.clip(max(20, yardline_100 + 8), 1, 99)
    fg_miss = float(1 - _wp([_opponent_state(missed_start,
        score_differential, qtr, seconds_in_quarter, 5,
        offense_is_home, offense_timeouts, defense_timeouts)])[0])

    residuals, punt_method, punt_count = _punt_residual_distribution(
        ydstogo, yardline_100)
    punt_possible = residuals is not None and len(residuals) >= 2
    punt_values = None
    if punt_possible:
        starts = np.clip(predicted_punt_start + residuals[:, 0], 1, 99)
        punt_states = [_opponent_state(own, score_differential,
            qtr, seconds_in_quarter, max(1, elapsed),
            offense_is_home, offense_timeouts, defense_timeouts)
            for own, elapsed in zip(starts, residuals[:, 1])]
        punt_values = 1 - _wp(punt_states)

    # Fixed reproducible random stream for this particular scenario.
    import hashlib
    seed_input = repr((ydstogo, yardline_100, score_differential, qtr,
        seconds_in_quarter, offense_is_home, offense_timeouts,
        defense_timeouts, repetitions)).encode('utf-8')
    seed = int.from_bytes(hashlib.sha256(seed_input).digest()[:8], 'little')
    rng = np.random.default_rng(seed)
    names = ['Go for it', 'Field goal'] + (['Punt'] if punt_possible else [])
    draws = np.empty((repetitions, len(names)), dtype=float)
    for b in range(repetitions):
        draws[b, 0] = (p_convert * np.mean(rng.choice(go_success,
            size=len(go_success), replace=True)) + (1 - p_convert) * go_fail)
        draws[b, 1] = (p_make * np.mean(rng.choice(fg_made,
            size=len(fg_made), replace=True)) + (1 - p_make) * fg_miss)
        if punt_possible:
            draws[b, 2] = float(np.mean(rng.choice(punt_values,
                size=len(punt_values), replace=True)))

    point_estimates = {d['name']:float(d['win_probability']) for d in point['decisions']}
    # Reflect any difference between the auxiliary resampling and main estimate
    # by centering bootstrap deviations on the displayed point estimate.
    centers = np.mean(draws, axis=0)
    centered = np.clip(draws + np.array([point_estimates[n] for n in names]) - centers, 0, 1)
    intervals = []
    for j, name in enumerate(names):
        low, high = np.quantile(centered[:, j], [0.025, 0.975])
        intervals.append({'name':name,
            'estimate_pct':round(point_estimates[name] * 100, 2),
            'lower_pct':round(float(low) * 100, 2),
            'upper_pct':round(float(high) * 100, 2)})

    if punt_possible:
        winner_idx = np.argmax(centered, axis=1)
        top_frequency = {name:round(float(np.mean(winner_idx == j)) * 100, 1)
                         for j, name in enumerate(names)}
        best, second = sorted(point_estimates, key=point_estimates.get,
                              reverse=True)[:2]
        diff = centered[:, names.index(best)] - centered[:, names.index(second)]
        gap_interval = [round(float(x) * 100, 2)
                        for x in np.quantile(diff, [0.025, 0.975])]
    else:
        top_frequency, gap_interval = None, None

    return {
        'scenario': scenario,
        'repetitions': repetitions,
        'intervals': intervals,
        'rank_first_frequency_pct': top_frequency,
        'gap_interval_pp': gap_interval,
        'is_complete': bool(punt_possible),
        'sample_sizes': {
            'conversion_success_gains_used': len(go_success),
            'made_fg_transitions_used': len(fg_made),
            'punt_residuals_used': len(punt_values) if punt_possible else 0,
        },
        'method': 'Percentile bootstrap of empirical outcome averages, with fixed trained models and fixed conversion/kick probabilities; row-level resampling.',
        'limitations': (
            'These are sensitivity intervals for historical outcome-sampling variability, '
            'NOT validated 95% confidence intervals for actual win probability. '
            'They exclude model-parameter uncertainty, game-level dependence, '
            'coach selection bias, miss/blocked-kick variation, rule changes and counterfactual model error. '
            + ('' if punt_possible else
                'Punt uncertainty and all-three rank frequency are unavailable without data/punt_outcomes.csv.')
        )
    }


def estimate_outcome_uncertainty(ydstogo=3, yardline_100=40,
        score_differential=-4, qtr=4, seconds_in_quarter=300,
        offense_is_home=1, offense_timeouts=3, defense_timeouts=3,
        repetitions=400):
    if not isinstance(repetitions, int) or not 100 <= repetitions <= 1000:
        raise ValueError('Bootstrap repetitions must be between 100 and 1000.')
    return _uncertainty_cached(ydstogo, yardline_100, score_differential,
        qtr, seconds_in_quarter, offense_is_home,
        offense_timeouts, defense_timeouts, repetitions)

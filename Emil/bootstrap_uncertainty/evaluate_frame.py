import numpy as np
import pandas as pd

def evaluate_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Evaluate every row. Needs columns: qtr, game_seconds_remaining,
    yardline_100, ydstogo, score_differential, posteam_timeouts_remaining."""
    y = df["yardline_100"].astype(int).clip(1, 99).to_numpy()
    ytg = np.minimum(df["ydstogo"].astype(int).clip(lower=1).to_numpy(), y)
    k = np.minimum(ytg, MAX_YTG)
 
    p = P_CONVERT[k]
    succ = np.where(ytg >= y, TD_POINTS, SUCCESS[y, k])  # 4th & goal: converting = TD
    fail = -EP1[100 - y]                                  # opponent gets it here
    go = p * succ + (1 - p) * fail
    punt = PUNT[y]
    fg = FG_EP[y]
    secs = df["game_seconds_remaining"].to_numpy(dtype=float)
    qtr = df["qtr"].to_numpy()
 
    # Situation override 1: last play of the half / game
    # Nothing after this play counts, so only points scored ON the play matter:
    # a first down short of the end zone is worth 0, and so is giving the ball away.
    half_secs = np.where(qtr == 2, secs - 1800, np.where(qtr >= 4, secs, np.inf))
    last_play = half_secs <= END_OF_HALF_SECS
    td_share = np.where(ytg >= y, 1.0, TD_SHARE[y, k])
    succ = np.where(last_play, td_share * TD_POINTS, succ)
    fail = np.where(last_play, 0.0, fail)
    go = p * succ + (1 - p) * fail
    punt = np.where(last_play & ~np.isnan(punt), 0.0, punt)
    fg = np.where(last_play & ~np.isnan(fg), P_FG[y] * FG_POINTS, fg)
 
    # --- Situation override 2: trailing late, can you get the ball back? ---
    tos = df["posteam_timeouts_remaining"].fillna(3).clip(0, 3).to_numpy()
    stops = tos + (secs > 120)                      # two-minute warning acts as a stop
    kneel_out = 40 * np.clip(3 - stops, 0, 3) + 10  # time opponent can burn kneeling
    behind = -df["score_differential"].fillna(0).to_numpy(dtype=float)
    desperate = (
        (qtr >= 4)
        & (behind > 0)
        & (secs <= kneel_out + MIN_TIME_TO_SCORE)
    )
    punt = np.where(desperate & ~np.isnan(punt), fail, punt)              # punting ends it
    fg = np.where(desperate & (behind > 3) & ~np.isnan(fg), fail, fg)     # FG can't tie/win
 
    best_alt = np.fmax(punt, fg)
    best_alt = np.where(np.isnan(best_alt), fail, best_alt)
    options = np.column_stack([go, punt, fg])
    rec = np.array(["go", "punt", "field_goal"])[np.nanargmax(options, axis=1)]
 
    return pd.DataFrame(
        {
            "p_convert": p,
            "ep_if_convert": succ,
            "ep_if_fail": fail,
            "ep_go": go,
            "ep_punt": punt,
            "ep_fg": fg,
            "best_alt_ep": best_alt,
            "points_if_convert": succ - best_alt,
            "points_if_fail": fail - best_alt,
            "breakeven_rate": np.clip((best_alt - fail) / (succ - fail), 0, 1),
            "go_advantage": go - best_alt,
            "recommendation": rec,
            "desperation": desperate,
            "last_play": last_play,
        },
        index=df.index,
    )
"""Paste into Google Colab after daily setup: pbp_all (nflreadpy polars frame)."""
import numpy as np
import pandas as pd
from pathlib import Path

needed = [
    'game_id', 'play_id', 'season', 'week', 'season_type', 'home_team',
    'away_team', 'posteam', 'qtr', 'quarter_seconds_remaining',
    'ydstogo', 'yardline_100', 'score_differential',
    'home_opening_kickoff', 'posteam_timeouts_remaining',
    'defteam_timeouts_remaining', 'play_type', 'down'
]
missing = [x for x in needed if x not in pbp_all.columns]
if missing:
    raise ValueError('Expected nflverse columns missing: ' + ', '.join(missing))

plays = pbp_all.select(needed).to_pandas()
plays = plays[
    (plays['season'] == 2025) &
    (plays['down'] == 4) &
    (plays['qtr'].between(1, 4)) &
    (plays['ydstogo'].between(1, 15)) &
    (plays['yardline_100'].between(16, 58)) &
    (plays['ydstogo'] < plays['yardline_100']) &
    (plays['quarter_seconds_remaining'].between(20, 900)) &
    (plays['score_differential'].between(-35, 35)) &
    (plays['play_type'].isin(['run', 'pass', 'punt', 'field_goal']))
].copy()
plays = plays.dropna(subset=[x for x in needed if x != 'play_type'])
plays['type'] = plays['season_type'].astype(str).str.lower().map({'reg': 'reg', 'post': 'post'})
plays = plays[plays['type'].notna()].copy()
plays['offense_is_home'] = (plays['posteam'] == plays['home_team']).astype(int)
plays['seconds_in_quarter'] = plays['quarter_seconds_remaining'].astype(int)
plays['offense_timeouts'] = plays['posteam_timeouts_remaining'].astype(int)
plays['defense_timeouts'] = plays['defteam_timeouts_remaining'].astype(int)
plays['actual_action'] = plays['play_type'].map({
    'run': 'Go for it', 'pass': 'Go for it',
    'field_goal': 'Field goal', 'punt': 'Punt'
})
plays = plays.drop_duplicates(['game_id', 'play_id'])
# Stratify by what coaches actually chose, avoiding a sample made only of FG attempts.
# Benchmark predictions themselves will not use actual_action.
max_per_action = 30
sampled = pd.concat([
    g.sample(n=min(max_per_action, len(g)), random_state=42)
    for _, g in plays.groupby('actual_action')
], ignore_index=True)
sampled = sampled.sort_values(['game_id', 'play_id']).reset_index(drop=True)
assert sampled[['game_id','play_id']].duplicated().sum() == 0
out_dir = Path('/content/drive/MyDrive/NFL_4th_Down_Project/benchmark')
out_dir.mkdir(parents=True, exist_ok=True)
output = out_dir / 'benchmark_scenarios_2025.csv'
sampled.to_csv(output, index=False)
print('Eligible 2025 plays:', len(plays))
print('Sampled:', len(sampled))
print(sampled['actual_action'].value_counts().to_string())
print('Saved:', output)
print(sampled[['game_id','play_id','ydstogo','yardline_100','actual_action']].head())

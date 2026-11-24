"""RUN IN GOOGLE COLAB after your Daily Setup cells (pbp_all is Polars).

Exports training-season (2022-2024) matched punt outcomes to Google Drive.
Download the resulting CSV and place it in the application's data/ folder.
2025 is deliberately excluded for held-out validation.
"""
import numpy as np
import pandas as pd
from pathlib import Path

cols = [
    'game_id', 'season', 'play_id', 'qtr', 'play_type', 'posteam',
    'defteam', 'down', 'ydstogo', 'yardline_100',
    'score_differential', 'game_seconds_remaining', 'touchdown'
]
all_plays = (
    pbp_all.select(cols).to_pandas()
    .sort_values(['game_id', 'play_id'])
    .reset_index(drop=True)
)
punts = all_plays.loc[
    all_plays.season.isin([2022, 2023, 2024]) &
    all_plays.play_type.eq('punt') &
    all_plays.down.eq(4) &
    all_plays.posteam.notna() & all_plays.defteam.notna() &
    all_plays.yardline_100.between(1, 99) &
    all_plays.ydstogo.between(1, 40) &
    all_plays.score_differential.notna() &
    all_plays.game_seconds_remaining.notna() &
    all_plays.touchdown.fillna(0).eq(0)
].copy()
scrimmage = all_plays.loc[
    all_plays.play_type.isin(['run', 'pass', 'qb_kneel', 'qb_spike']) &
    all_plays.posteam.notna() &
    all_plays.yardline_100.between(1, 99)
].copy()
by_game = {g: group.sort_values('play_id').reset_index(drop=True)
           for g, group in scrimmage.groupby('game_id')}
matched = []
for g, group in punts.groupby('game_id'):
    follow = by_game.get(g)
    if follow is None:
        continue
    ids = follow.play_id.to_numpy()
    for row in group.itertuples(index=False):
        ix = int(np.searchsorted(ids, row.play_id, side='right'))
        if ix >= len(follow):
            continue
        nxt = follow.iloc[ix]
        if nxt.posteam != row.defteam:
            continue
        # Do not treat halftime or end-of-game starts as punt outcomes.
        if (row.qtr <= 2) != (nxt.qtr <= 2):
            continue
        elapsed = float(row.game_seconds_remaining - nxt.game_seconds_remaining)
        if not 0 <= elapsed <= 45:
            continue
        opponent_start = 100.0 - float(nxt.yardline_100)
        if not 1 <= opponent_start <= 99:
            continue
        matched.append({
            'game_id': row.game_id, 'season': int(row.season),
            'play_id': row.play_id, 'yardline_100': row.yardline_100,
            'ydstogo': row.ydstogo,
            'score_differential': row.score_differential,
            'game_seconds_remaining': row.game_seconds_remaining,
            'opponent_start': opponent_start,
            'elapsed_seconds': elapsed,
        })
punt_outcomes = pd.DataFrame(matched)
print('Total eligible punts:', len(punts))
print('Matched punts:', len(punt_outcomes))
print('Match rate:', f'{len(punt_outcomes)/len(punts):.1%}' if len(punts) else 'N/A')
if punt_outcomes.empty:
    raise RuntimeError('No punts matched; inspect the play-by-play dataset.')
display(punt_outcomes[['opponent_start', 'elapsed_seconds']].describe())

from google.colab import drive
drive.mount('/content/drive')
path = Path('/content/drive/MyDrive/NFL_4th_Down_Project/data/punt_outcomes.csv')
path.parent.mkdir(parents=True, exist_ok=True)
punt_outcomes.to_csv(path, index=False)
print('Saved:', path)
print('Download this CSV from Google Drive and copy it to NFL_Fourth_Down_Starter/data/')

"""Run from project root: python benchmark/03_compare_benchmark.py"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd
from decision_engine import compare_fourth_down

folder = Path(__file__).resolve().parent
s_file = folder/'benchmark_scenarios_2025.csv'
b_file = folder/'nfl4th_results_2025.csv'
if not s_file.exists() or not b_file.exists():
    raise SystemExit('Copy both benchmark_scenarios_2025.csv and nfl4th_results_2025.csv into benchmark/')
s = pd.read_csv(s_file, dtype={'game_id':str})
b = pd.read_csv(b_file, dtype={'game_id':str})
if s[['game_id','play_id']].duplicated().any() or b[['game_id','play_id']].duplicated().any():
    raise ValueError('Duplicate game_id/play_id keys; cannot safely compare.')
rows = []
for r in s.itertuples(index=False):
    result = compare_fourth_down(
        ydstogo=int(r.ydstogo), yardline_100=int(r.yardline_100),
        score_differential=int(r.score_differential), qtr=int(r.qtr),
        seconds_in_quarter=int(r.seconds_in_quarter),
        offense_is_home=int(r.offense_is_home),
        offense_timeouts=int(r.offense_timeouts), defense_timeouts=int(r.defense_timeouts))
    opts = {d['name']:d['win_probability'] for d in result['decisions']}
    rows.append({'game_id':str(r.game_id), 'play_id':r.play_id,
                 'our_go_wp':opts['Go for it'], 'our_fg_wp':opts['Field goal'],
                 'our_punt_wp':opts['Punt'], 'our_recommendation':result['best_decision'],
                 'our_gap_pp':result['top_two_gap_pp']})
ours = pd.DataFrame(rows)
merged = s.merge(ours, on=['game_id','play_id'], validate='one_to_one')
merged = merged.merge(b, on=['game_id','play_id'], how='inner', validate='one_to_one')
if merged.empty:
    raise ValueError('No matching IDs! Inspect exported CSVs.')
options = [('Go for it','our_go_wp','go_wp'),
           ('Field goal','our_fg_wp','fg_wp'), ('Punt','our_punt_wp','punt_wp')]
for _, oc, nc in options:
    merged[nc] = pd.to_numeric(merged[nc], errors='coerce')
    merged[f'difference_{nc}_pp'] = 100*(merged[oc]-merged[nc])

# For each row, compare best choice only over options which nfl4th scored;
# separately report cases where all three are scored.
def compare_row(r):
    allowed = [(label,float(r[oc]),float(r[nc])) for label,oc,nc in options
               if pd.notna(r[nc]) and np.isfinite(r[nc])]
    if len(allowed) < 2:
        return pd.Series({'shared_actions':len(allowed), 'our_shared_best':None,
                          'nfl4th_best':None, 'recommendation_agrees':np.nan,
                          'three_action_case':False,
                          'nfl4th_gap_pp':np.nan})
    own_best = max(allowed, key=lambda o:o[1])[0]
    ref_best = max(allowed, key=lambda o:o[2])[0]
    vals = sorted([x[2] for x in allowed],reverse=True)
    return pd.Series({'shared_actions':len(allowed),'our_shared_best':own_best,
                      'nfl4th_best':ref_best,
                      'recommendation_agrees':int(own_best==ref_best),
                      'three_action_case':len(allowed)==3,
                      'nfl4th_gap_pp':100*(vals[0]-vals[1])})
merged = pd.concat([merged, merged.apply(compare_row,axis=1)],axis=1)
valid = merged[merged['shared_actions'] >= 2]
full = valid[valid['three_action_case']]

print('\nNFL FOURTH-DOWN BENCHMARK — HELD-OUT 2025')
print('Scenario rows:',len(s),' | nfl4th rows:',len(b),' | Matched:',len(merged))
print('At least two shared actions:',len(valid),' | All three actions:',len(full))
if len(valid):
    print('Shared-available-action recommendation agreement: '
          f"{valid['recommendation_agrees'].mean():.1%}")
if len(full):
    print('Strict three-action agreement: '
          f"{full['recommendation_agrees'].mean():.1%}")
print('\nAbsolute differences between estimated win probabilities:')
for name,oc,nc in options:
    dif = (100*(merged[oc]-merged[nc])).dropna()
    if len(dif):
        print(f'{name:11s} n={len(dif):3d} MAE={dif.abs().mean():.2f} pp; mean bias={dif.mean():+.2f} pp')
if len(full):
    print('\nConfusion matrix (our model rows, nfl4th columns):')
    print(pd.crosstab(full['our_shared_best'],full['nfl4th_best']).to_string())
    close = full[full['our_gap_pp'] < 2]
    if len(close):
        print(f'Close calls (<2 pp by our model): {len(close)}; agreement {close["recommendation_agrees"].mean():.1%}')
    decisive = full[full['our_gap_pp'] >= 2]
    if len(decisive):
        print(f'Non-close calls (>=2 pp by our model): {len(decisive)}; agreement {decisive["recommendation_agrees"].mean():.1%}')

outfile = folder/'benchmark_comparison_2025.csv'
merged.to_csv(outfile,index=False)
print('\nSaved scenario-by-scenario comparison:',outfile)
print('IMPORTANT: Agreement with nfl4th is a benchmark, not ground-truth decision accuracy.')

"""Summarize anonymous exported study CSVs.

Usage from project root:
    python study/analyze_study.py
Place participant exports in study/results/ first. The 9999 pilot ID is excluded.
"""
from pathlib import Path
import pandas as pd

RESULTS = Path(__file__).resolve().parent / 'results'
files = sorted(RESULTS.glob('fourth_down_study_P*.csv'))
if not files:
    raise SystemExit('No participant CSV files in study/results/.')
frames=[]
for file in files:
    df=pd.read_csv(file)
    if len(df)!=12:
        print(f'Skipping {file.name}: expected 12 tasks, found {len(df)}')
        continue
    if df['participant_id'].nunique()!=1:
        print(f'Skipping {file.name}: multiple IDs')
        continue
    if int(df['participant_id'].iloc[0])==9999:
        print('Skipping pilot:',file.name)
        continue
    frames.append(df)
if not frames:
    raise SystemExit('No usable non-pilot datasets.')
all_df=pd.concat(frames,ignore_index=True)
all_df=all_df.drop_duplicates(subset=['participant_id','scenario_id','condition'])
all_df=all_df.loc[all_df.condition.isin(['static','interactive'])]
# Require each participant to contribute six trials in each condition.
counts=all_df.groupby(['participant_id','condition']).size().unstack(fill_value=0)
valid=counts.index[(counts.get('static',0)==6)&(counts.get('interactive',0)==6)]
all_df=all_df.loc[all_df.participant_id.isin(valid)].copy()
if all_df.empty: raise SystemExit('No fully completed paired participants.')
metrics=['best_correct','close_correct','gap_absolute_error_pp','duration_seconds']
for col in metrics:all_df[col]=pd.to_numeric(all_df[col],errors='coerce')
by_person=all_df.groupby(['participant_id','condition'])[metrics].mean().reset_index()
print(f'Completed paired participants: {len(valid)}; task responses: {len(all_df)}')
print('\nMean task outcomes (per participant averages; lower is better for gap error/time):')
print(by_person.groupby('condition')[metrics].mean().round(3).to_string())
wide=by_person.pivot(index='participant_id',columns='condition',values=metrics)
print('\nMean within-participant interactive minus static:')
for metric in metrics:
    dif=wide[(metric,'interactive')]-wide[(metric,'static')]
    print(f'  {metric}: {dif.mean():+.3f} (n={dif.notna().sum()})')
print('\nClose-call recognition specifically for objectively close tasks:')
close=all_df.loc[all_df.correct_close.eq('yes')]
print(close.groupby('condition').close_correct.mean().round(3).to_string())
results=RESULTS/'combined_study_results.csv';all_df.to_csv(results,index=False)
print('\nWrote',results)

"""Regenerate classroom study fixed scenarios (run in project root)."""
from pathlib import Path
import sys, json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from decision_engine import compare_fourth_down
SPECS = [
    ('A01',55,15,-4,4,300),('A02',45,7,-4,4,300),('A03',40,3,-3,4,180),
    ('A04',40,3,-4,4,300),('A05',35,7,-4,4,300),('A06',30,3,3,3,600),
    ('B01',50,10,-4,4,300),('B02',45,7,3,3,600),('B03',40,3,0,2,240),
    ('B04',40,1,-4,4,300),('B05',25,7,-4,4,300),('B06',45,7,-3,4,180),
]
rows=[]
for id_,yard,ytg,score,quarter,time_left in SPECS:
    scenario={'yardline_100':yard,'ydstogo':ytg,'score_differential':score,
              'qtr':quarter,'seconds_in_quarter':time_left,
              'offense_is_home':1,'offense_timeouts':3,'defense_timeouts':3}
    result=compare_fourth_down(**scenario)
    opts={d['name']:d['win_probability_pct'] for d in result['decisions']}
    gap=round(max(opts.values())-sorted(opts.values())[-2],2)
    rows.append({'id':id_,'set':id_[0],'scenario':scenario,'probabilities':opts,
                 'correct_best':max(opts,key=opts.get),'correct_gap_pp':gap,
                 'correct_close':gap<2})
    print(id_, 'close' if gap<2 else 'clear', result['best_decision'],gap)
assert all(sum(r['correct_close'] == kind for r in rows if r['set']==s)==3 for s in 'AB' for kind in (True,False))
root=Path(__file__).resolve().parents[1]
out=root/'static/data/study_scenarios.json'
out.write_text(json.dumps({'version':'study-v1','source':'Current trained engine; fixed post-play assumptions','scenarios':rows},indent=2))
print('Saved',out)

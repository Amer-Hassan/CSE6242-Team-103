const ids=['ydstogo','yardline_100','score_differential','qtr','seconds_in_quarter','offense_is_home','offense_timeouts','defense_timeouts'];
const colors={'Go for it':'#38b889','Field goal':'#e5a344','Punt':'#65a4f1'};
let generation=0;
function values(){const o={};for(const id of ids)o[id]=Number(document.getElementById(id).value);return o;}
async function update(){
  const tag=++generation;
  for(const id of ids){const out=document.getElementById(id+'_value');if(out)out.textContent=document.getElementById(id).value;}
  const status=document.getElementById('status');status.textContent='Calculating…';
  try{
    const resp=await fetch('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(values())});
    const data=await resp.json();if(tag!==generation)return;
    if(!resp.ok)throw new Error(data.error||'Prediction failed');
    status.textContent='Model-based prototype · Not a calibrated counterfactual prediction';
    document.getElementById('best').textContent=data.best_decision;
    document.getElementById('gap').textContent=data.top_two_gap_pp.toFixed(2)+' percentage points';
    const k=data.outcome_models;
    document.getElementById('details').textContent=`Conversion: ${(k.conversion_probability*100).toFixed(1)}% · FG success: ${k.field_goal_success_probability==null?'Not evaluated':(k.field_goal_success_probability*100).toFixed(1)+'%'} · Opponent start after punt: own ${k.opponent_start_after_punt.toFixed(1)}`;
    draw(data.decisions);
  }catch(err){if(tag!==generation)return;status.textContent=err.message;document.getElementById('chart').replaceChildren();}
}
function draw(decisions){
 const w=760,h=decisions.length*64+12,left=95,right=75;
 const svg=d3.select('#chart').selectAll('svg').data([null]).join('svg').attr('viewBox',`0 0 ${w} ${h}`).style('width','100%').attr('role','img').attr('aria-label','Win probability comparison chart');
 const x=d3.scaleLinear().domain([0,100]).range([left,w-right]);
 const rows=svg.selectAll('g.row').data(decisions,d=>d.name).join(enter=>enter.append('g').attr('class','row'));
 rows.transition().duration(350).attr('transform',(d,i)=>`translate(0,${i*64+16})`);
 rows.selectAll('text.name').data(d=>[d]).join('text').attr('class','name bar-label').attr('x',2).attr('y',24).text(d=>d.name);
 rows.selectAll('rect.track').data(d=>[d]).join('rect').attr('class','track').attr('x',left).attr('y',8).attr('width',x(100)-left).attr('height',25).attr('rx',6).attr('fill','#2d3c4f');
 rows.selectAll('rect.value').data(d=>[d]).join('rect').attr('class','value').attr('x',left).attr('y',8).attr('height',25).attr('rx',6).attr('fill',d=>colors[d.name]).transition().duration(350).attr('width',d=>x(d.win_probability_pct)-left);
 rows.selectAll('text.percent').data(d=>[d]).join('text').attr('class','percent bar-value').attr('x',w-67).attr('y',26).text(d=>d.win_probability_pct.toFixed(2)+'%');
}
ids.forEach(id=>document.getElementById(id).addEventListener('input',update));
update();

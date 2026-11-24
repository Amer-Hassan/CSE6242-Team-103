const ids=['ydstogo','yardline_100','score_differential','qtr','seconds_in_quarter','offense_is_home','offense_timeouts','defense_timeouts'];
const colors={'Go for it':'#70d2a7','Field goal':'#ebaf63','Punt':'#79aaf2'};
const defaults={ydstogo:3,yardline_100:40,score_differential:-4,qtr:4,seconds_in_quarter:300,offense_is_home:1,offense_timeouts:3,defense_timeouts:3};
let generation=0, timer=null;
const el=id=>document.getElementById(id);
function values(){return Object.fromEntries(ids.map(id=>[id,Number(el(id).value)]));}
function clock(s){return `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;}
function refreshLabels(){const v=values();for(const id of ['ydstogo','yardline_100','score_differential','seconds_in_quarter']){const output=el(id+'_value'); output.textContent=id==='seconds_in_quarter'?clock(v[id]):id==='score_differential'?(v[id]>0?'+':'')+v[id]:v[id];}el('field-position-label').textContent=`Opponent's ${v.yardline_100}`;drawField(v);}
function drawField(v){const w=780,h=114;const svg=d3.select('#field').selectAll('svg').data([null]).join('svg').attr('viewBox',`0 0 ${w} ${h}`).attr('role','img').attr('aria-label',`Ball ${v.yardline_100} yards from goal, ${v.ydstogo} yards to go`);svg.selectAll('*').remove();svg.append('rect').attr('width',w).attr('height',h).attr('fill','#19473d');const x=d3.scaleLinear().domain([100,0]).range([0,w]);d3.range(10,100,10).forEach(yd=>{svg.append('line').attr('x1',x(yd)).attr('x2',x(yd)).attr('y1',0).attr('y2',h).attr('stroke','#ffffff').attr('opacity',.25);svg.append('text').attr('x',x(yd)).attr('y',21).attr('text-anchor','middle').attr('fill','#c6eee0').attr('opacity',.65).attr('font-size',11).text(yd<=50?yd:100-yd);});svg.append('rect').attr('x',w-49).attr('width',49).attr('height',h).attr('fill','#0c2d25');svg.append('text').attr('transform',`translate(${w-17},${h/2}) rotate(-90)`).attr('text-anchor','middle').attr('fill','#8ac4a9').attr('font-size',11).attr('font-weight',800).text('END ZONE');const ballX=x(v.yardline_100), firstX=x(v.yardline_100-v.ydstogo);svg.append('line').attr('x1',firstX).attr('x2',firstX).attr('y1',0).attr('y2',h).attr('stroke','#ffc55c').attr('stroke-width',3);svg.append('line').attr('x1',ballX).attr('x2',ballX).attr('y1',0).attr('y2',h).attr('stroke','#a0e8f3').attr('stroke-width',3);svg.append('circle').attr('cx',ballX).attr('cy',h/2).attr('r',10).attr('fill','#fff').attr('stroke','#1d5660').attr('stroke-width',3);svg.append('text').attr('x',ballX).attr('y',h-13).attr('text-anchor','middle').attr('fill','white').attr('font-weight',800).attr('font-size',12).text('4th & '+v.ydstogo);}
async function post(path,inputs){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(inputs)});const data=await response.json();if(!response.ok)throw new Error(data.error||'Prediction failed');return data;}
async function update(){const tag=++generation;const v=values();refreshLabels();el('status').textContent='Updating model estimates…';try{const data=await post('/api/predict',v);if(tag!==generation)return;el('status').textContent='Model-based estimates · Historical post-play states';el('best').textContent=data.best_decision;el('gap').textContent=data.top_two_gap_pp.toFixed(2)+' pp';el('interpretation').textContent=data.top_two_gap_pp<2?'Close decision':data.top_two_gap_pp<5?'Moderate difference':'Clearer estimated gap';const k=data.outcome_models;el('model-stats').innerHTML=`<b>Conversion</b> ${(100*k.conversion_probability).toFixed(1)}% &nbsp;·&nbsp; <b>FG make</b> ${(100*k.field_goal_success_probability).toFixed(1)}%<br><b>Mean gain after conversion</b> ${k.success_gain_mean.toFixed(1)} yd (${k.conversion_gain_sample_size} historical plays)<br><b>Made FG: opponent own</b> ${k.made_fg_avg_opponent_start.toFixed(1)} &nbsp;·&nbsp; <b>Miss: own</b> ${k.missed_fg_opponent_start.toFixed(1)}<br><b>Punt: opponent own</b> ${k.opponent_start_after_punt.toFixed(1)}<br><b>Punt outcomes</b> ${k.punt_outcome_sample_size ? `${k.punt_outcome_sample_size} historical plays · typical start range (10th–90th): own ${k.punt_start_p10.toFixed(1)}–${k.punt_start_p90.toFixed(1)}` : 'Point estimate only · export punt_outcomes.csv to enable distribution'}`;el('disclaimer').textContent=data.disclaimer;drawBars(data.decisions);const sensitivity=await post('/api/sensitivity',v);if(tag!==generation)return;drawSensitivity(sensitivity.points,v.ydstogo);}catch(error){if(tag!==generation)return;el('status').textContent=error.message;el('chart').replaceChildren();el('sensitivity').textContent='Unable to calculate sensitivity for this scenario.';}}
function drawBars(rows){const w=650,h=rows.length*77+16,left=112,right=74;const svg=d3.select('#chart').selectAll('svg').data([null]).join('svg').attr('viewBox',`0 0 ${w} ${h}`).attr('role','img').attr('aria-label','Estimated win probability comparison');svg.selectAll('*').remove();const x=d3.scaleLinear().domain([0,100]).range([left,w-right]);rows.forEach((d,i)=>{const y=i*77+12;svg.append('text').attr('class','bar-label').attr('x',0).attr('y',y+25).text(d.name);svg.append('rect').attr('x',left).attr('y',y).attr('width',w-right-left).attr('height',34).attr('rx',7).attr('fill','#283945');svg.append('rect').attr('x',left).attr('y',y).attr('width',Math.max(0,x(d.win_probability_pct)-left)).attr('height',34).attr('rx',7).attr('fill',colors[d.name]);svg.append('text').attr('class','bar-value').attr('x',w-right+10).attr('y',y+23).text(d.win_probability_pct.toFixed(2)+'%');svg.append('text').attr('x',left).attr('y',y+52).attr('fill','#9cacb8').attr('font-size',11).text(i===0?'Highest estimated WP':`${d.gap_from_best_pp.toFixed(2)} pp behind best`);});}
function drawSensitivity(points,current){if(!points.length)return;const w=980,h=285,margin={top:20,right:72,bottom:43,left:60};d3.select('#sensitivity').selectAll('p').remove();const svg=d3.select('#sensitivity').selectAll('svg').data([null]).join('svg').attr('viewBox',`0 0 ${w} ${h}`).attr('role','img').attr('aria-label','Win probability sensitivity to yards to go');svg.selectAll('*').remove();const x=d3.scaleLinear().domain(d3.extent(points,d=>d.ydstogo)).range([margin.left,w-margin.right]);const nums=points.flatMap(d=>['Go for it','Field goal','Punt'].map(k=>d[k]));const ymin=Math.max(0,Math.floor((Math.min(...nums)-6)/5)*5),ymax=Math.min(100,Math.ceil((Math.max(...nums)+6)/5)*5);const y=d3.scaleLinear().domain([ymin,ymax===ymin?ymin+10:ymax]).range([h-margin.bottom,margin.top]);svg.append('g').attr('class','axis').attr('transform',`translate(0,${h-margin.bottom})`).call(d3.axisBottom(x).tickValues(points.map(p=>p.ydstogo)).tickFormat(d=>`4th & ${d}`));svg.append('g').attr('class','axis').attr('transform',`translate(${margin.left},0)`).call(d3.axisLeft(y).ticks(5).tickFormat(d=>d+'%'));svg.append('line').attr('x1',x(current)).attr('x2',x(current)).attr('y1',margin.top).attr('y2',h-margin.bottom).attr('stroke','#e1e8eb').attr('stroke-width',1.1).attr('stroke-dasharray','4 5').attr('opacity',.55);['Go for it','Field goal','Punt'].forEach(key=>{const line=d3.line().x(d=>x(d.ydstogo)).y(d=>y(d[key]));svg.append('path').datum(points).attr('d',line).attr('fill','none').attr('stroke',colors[key]).attr('stroke-width',3);svg.selectAll('circle.'+key.replaceAll(' ','')).data(points).enter().append('circle').attr('cx',d=>x(d.ydstogo)).attr('cy',d=>y(d[key])).attr('r',d=>d.ydstogo===current?6:4).attr('fill',colors[key]).attr('stroke','#17212a').attr('stroke-width',2).append('title').text(d=>`${key}: ${d[key].toFixed(2)}% at 4th & ${d.ydstogo}`);const last=points[points.length-1];svg.append('text').attr('x',x(last.ydstogo)+8).attr('y',y(last[key])+4).attr('fill',colors[key]).attr('font-size',12).attr('font-weight',700).text(last[key].toFixed(1)+'%');});}
function schedule(){refreshLabels();markBoundaryStale();clearTimeout(timer);timer=setTimeout(update,260);}
ids.forEach(id=>el(id).addEventListener('input',schedule));
el('reset').addEventListener('click',()=>{Object.entries(defaults).forEach(([k,v])=>el(k).value=v);schedule();});
const presets={close:{ydstogo:1,yardline_100:25,score_differential:-3,qtr:4,seconds_in_quarter:180},late:{ydstogo:3,yardline_100:40,score_differential:-4,qtr:4,seconds_in_quarter:300},mid:{ydstogo:7,yardline_100:55,score_differential:3,qtr:3,seconds_in_quarter:600}};
document.querySelectorAll('[data-preset]').forEach(button=>button.addEventListener('click',()=>{Object.entries(presets[button.dataset.preset]).forEach(([k,v])=>el(k).value=v);schedule();}));
refreshLabels();update();



// A two-dimensional decision-boundary map. It is intentionally generated
// on demand; a full map calls 64 scenario evaluations on the backend.
let boundaryGeneration=0;
let activeBoundaryData=null;
let activeBoundaryContext=null;
function boundaryContext(v){
  return ['score_differential','qtr','seconds_in_quarter','offense_is_home','offense_timeouts','defense_timeouts'].map(k=>v[k]).join('|');
}
function markBoundaryStale(){
  if(!activeBoundaryData)return;
  if(boundaryContext(values()) !== activeBoundaryContext){
    el('boundary-status').textContent='Game context changed. Regenerate the map for updated estimates.';
    el('decision-boundary').style.opacity='.48';
    el('boundary-details').innerHTML='<h3>Map needs refreshing</h3><p class="small muted">Generate the map again to compare this game context.</p>';
  }else{
    el('decision-boundary').style.opacity='1';
    el('boundary-status').textContent='64 scenarios mapped. Hover for details, click to load a scenario.';
  }
}
function setBoundaryDetails(d){
  const ordered=Object.entries(d.probabilities).sort((a,b)=>b[1]-a[1]);
  const heading=`4th & ${d.ydstogo} · Opponent's ${d.yardline_100}`;
  const aside=d3.select('#boundary-details');aside.selectAll('*').remove();
  aside.append('h3').text(heading);
  aside.append('div').attr('class','boundary-winner').text('Highest estimated WP: '+d.best_decision);
  const dl=aside.append('dl');
  ordered.forEach(([name,value])=>{const r=dl.append('div');r.append('dt').text(name);r.append('dd').text(value.toFixed(2)+'%');});
  aside.append('p').attr('class','boundary-gap').text(`Gap between top two: ${d.top_two_gap_pp.toFixed(2)} percentage points`);
  aside.append('p').attr('class','small muted').text('Click this square to update the main scenario.');
}
function drawDecisionBoundary(data){
  activeBoundaryData=data;
  activeBoundaryContext=boundaryContext(data.context);
  el('decision-boundary').style.opacity='1';
  const positions=data.field_positions, distances=data.yards_to_go;
  const cellW=72,cellH=40,left=90,top=42,right=16,bottom=67;
  const w=left+cellW*positions.length+right,h=top+cellH*distances.length+bottom;
  const svg=d3.select('#decision-boundary').selectAll('svg').data([null]).join('svg')
    .attr('viewBox',`0 0 ${w} ${h}`).attr('role','img')
    .attr('aria-label','Heatmap of the best estimated decision by yards to go and opponent goal distance; click a cell to load it');
  svg.selectAll('*').remove();
  svg.append('text').attr('class','boundary-axis-title').attr('x',left+cellW*positions.length/2).attr('y',h-12)
    .attr('text-anchor','middle').text('Distance to opponent goal (yards)');
  svg.append('text').attr('class','boundary-axis-title').attr('transform',`translate(20,${top+cellH*distances.length/2}) rotate(-90)`)
    .attr('text-anchor','middle').text('Yards to go');
  positions.forEach((field,i)=>svg.append('text').attr('class','boundary-axis')
    .attr('x',left+(i+.5)*cellW).attr('y',top-15).attr('text-anchor','middle').text(field));
  distances.forEach((d,i)=>svg.append('text').attr('class','boundary-axis')
    .attr('x',left-14).attr('y',top+(i+.5)*cellH+4).attr('text-anchor','end').text(d));
  const group=svg.selectAll('g.boundary-cell').data(data.cells,d=>`${d.ydstogo}:${d.yardline_100}`).enter()
    .append('g').attr('class','boundary-cell').attr('role','button').attr('tabindex',0)
    .attr('aria-label',d=>`Fourth and ${d.ydstogo}, opponent ${d.yardline_100}, best ${d.best_decision}, gap ${d.top_two_gap_pp} percentage points`)
    .attr('transform',d=>`translate(${left+positions.indexOf(d.yardline_100)*cellW},${top+distances.indexOf(d.ydstogo)*cellH})`);
  group.append('rect').attr('x',2).attr('y',2).attr('width',cellW-4).attr('height',cellH-4)
    .attr('rx',5).attr('fill',d=>colors[d.best_decision]).attr('opacity',d=>d.top_two_gap_pp<2?.43:.9)
    .attr('stroke',d=>d.top_two_gap_pp<2?'#e8eff7':'#17212a')
    .attr('stroke-width',d=>d.top_two_gap_pp<2?2:1)
    .attr('stroke-dasharray',d=>d.top_two_gap_pp<2?'4 3':null);
  group.append('text').attr('x',cellW/2).attr('y',cellH/2+4)
    .attr('fill','#07131b').attr('text-anchor','middle').attr('font-size',11).attr('font-weight',800)
    .text(d=>({'Go for it':'GO','Field goal':'FG','Punt':'PUNT'})[d.best_decision]);
  group.append('title').text(d=>`4th & ${d.ydstogo}, opponent ${d.yardline_100}\nGo: ${d.probabilities['Go for it'].toFixed(2)}%\nFG: ${d.probabilities['Field goal'].toFixed(2)}%\nPunt: ${d.probabilities.Punt.toFixed(2)}%\nGap: ${d.top_two_gap_pp.toFixed(2)} pp`);
  group.on('mouseenter focus',(_,d)=>setBoundaryDetails(d));
  const choose=(_,d)=>{
    el('ydstogo').value=d.ydstogo;el('yardline_100').value=d.yardline_100;
    schedule();document.querySelector('.setup').scrollIntoView({behavior:'smooth',block:'start'});
  };
  group.on('click',choose).on('keydown',(event,d)=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();choose(event,d);}});
  const start=data.cells.find(d=>d.ydstogo===3&&d.yardline_100===40)||data.cells[0];
  setBoundaryDetails(start);
}
async function generateBoundary(){
  const tag=++boundaryGeneration;
  const button=el('generate-boundary');button.disabled=true;
  el('boundary-status').textContent='Computing 64 game scenarios…';
  try{
    const data=await post('/api/decision-boundary',values());
    if(tag!==boundaryGeneration)return;
    drawDecisionBoundary(data);
    const {counts}=data;
    el('boundary-status').textContent=`64 scenarios mapped · GO ${counts['Go for it']} · FG ${counts['Field goal']} · PUNT ${counts.Punt} — Hover or click a square.`;
  }catch(error){if(tag===boundaryGeneration)el('boundary-status').textContent=`Unable to generate map: ${error.message}`;}
  finally{if(tag===boundaryGeneration)button.disabled=false;}
}
el('generate-boundary').addEventListener('click',generateBoundary);


// Outcome-sampling sensitivity intervals are generated only on demand.
let uncertaintyGeneration=0;
let uncertaintyScenario=null;
function markUncertaintyStale(){
  if(!uncertaintyScenario)return;
  if(JSON.stringify(values())!==uncertaintyScenario){
    el('uncertainty-status').textContent='Scenario changed. Re-run analysis for updated intervals.';
    el('uncertainty-chart').style.opacity='.45';
  }
}
const uncertaintyNames=['Go for it','Field goal','Punt'];
function drawUncertainty(data){
  const rows=uncertaintyNames.map(n=>data.intervals.find(d=>d.name===n)).filter(Boolean);
  const w=740,h=rows.length*76+65,left=132,right=84;
  const x=d3.scaleLinear().domain([0,100]).range([left,w-right]);
  const holder=d3.select('#uncertainty-chart');holder.selectAll('*').remove();
  const svg=holder.append('svg').attr('viewBox',`0 0 ${w} ${h}`)
    .attr('role','img').attr('aria-label','Outcome-sampling ranges for estimated win probability');
  const ticks=[0,20,40,60,80,100];
  svg.append('g').attr('class','axis').attr('transform',`translate(0,${h-37})`)
    .call(d3.axisBottom(x).tickValues(ticks).tickFormat(d=>d+'%'));
  rows.forEach((d,i)=>{
    const y=25+i*76;
    svg.append('text').attr('x',6).attr('y',y+5).attr('fill','#deebf1')
      .attr('font-size',14).attr('font-weight',700).text(d.name);
    svg.append('line').attr('x1',x(d.lower_pct)).attr('x2',x(d.upper_pct))
      .attr('y1',y).attr('y2',y).attr('stroke',colors[d.name]).attr('stroke-width',7)
      .attr('stroke-linecap','round');
    [d.lower_pct,d.upper_pct].forEach(q=>svg.append('line')
      .attr('x1',x(q)).attr('x2',x(q)).attr('y1',y-10).attr('y2',y+10)
      .attr('stroke','#f2f6f9').attr('stroke-width',1.5));
    svg.append('circle').attr('cx',x(d.estimate_pct)).attr('cy',y).attr('r',7)
      .attr('fill',colors[d.name]).attr('stroke','#f5faff').attr('stroke-width',2);
    svg.append('text').attr('x',w-74).attr('y',y+5).attr('fill','#e6eef1')
      .attr('font-size',13).attr('font-weight',700).text(d.estimate_pct.toFixed(2)+'%');
    svg.append('text').attr('x',left).attr('y',y+25).attr('fill','#aebcc7')
      .attr('font-size',11).text(`${d.lower_pct.toFixed(2)}%–${d.upper_pct.toFixed(2)}% (resampling range)`);
  });
  const detail=el('uncertainty-details');
  detail.replaceChildren();
  const heading=document.createElement('h3');heading.textContent='Bootstrap summary';detail.append(heading);
  const info=document.createElement('p');info.className='small muted';
  info.textContent=`${data.repetitions} resamples · ${data.sample_sizes.conversion_success_gains_used} conversion gains · ${data.sample_sizes.made_fg_transitions_used} kickoff transitions · ${data.sample_sizes.punt_residuals_used} punt residuals`;
  detail.append(info);
  if(data.rank_first_frequency_pct){
    const title=document.createElement('p');title.className='small';
    title.textContent='Ranked first in resamples (not true probability of being optimal):';detail.append(title);
    const dl=document.createElement('dl');
    uncertaintyNames.forEach(name=>{
      const line=document.createElement('div');const dt=document.createElement('dt');dt.textContent=name;
      const dd=document.createElement('dd');dd.textContent=data.rank_first_frequency_pct[name].toFixed(1)+'%';
      line.append(dt,dd);dl.append(line);
    });detail.append(dl);
    const gap=document.createElement('p');gap.className='small muted';
    gap.textContent=`Top-two estimated gap resampling range: ${data.gap_interval_pp[0].toFixed(2)} to ${data.gap_interval_pp[1].toFixed(2)} pp`;
    detail.append(gap);
  }else{
    const note=document.createElement('p');note.className='small muted';
    note.textContent='Punt outcomes CSV missing; only Go and FG resampling ranges are shown. Three-way ranking frequencies are disabled.';detail.append(note);
  }
  el('uncertainty-footnote').textContent=data.limitations;
}
async function generateUncertainty(){
  const tag=++uncertaintyGeneration;
  const button=el('generate-uncertainty');button.disabled=true;
  el('uncertainty-status').textContent='Resampling historical outcomes (400 repetitions)…';
  const selected=values();
  try{
    const data=await post('/api/uncertainty',selected);
    if(tag!==uncertaintyGeneration)return;
    uncertaintyScenario=JSON.stringify(selected);
    drawUncertainty(data);el('uncertainty-chart').style.opacity='1';
    el('uncertainty-status').textContent=`Completed ${data.repetitions} fixed-model outcome resamples. Intervals exclude model-training uncertainty.`;
  }catch(err){if(tag===uncertaintyGeneration)el('uncertainty-status').textContent=`Unable to analyze uncertainty: ${err.message}`;}
  finally{if(tag===uncertaintyGeneration)button.disabled=false;}
}
el('generate-uncertainty').addEventListener('click',generateUncertainty);
// Wrap the existing scenario-change handler without running bootstrap on slider moves.
ids.forEach(id=>el(id).addEventListener('input',markUncertaintyStale));

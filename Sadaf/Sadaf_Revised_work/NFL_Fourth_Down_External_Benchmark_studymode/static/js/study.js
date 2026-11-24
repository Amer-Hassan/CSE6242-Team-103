/* Anonymous, client-only classroom evaluation. No server-side response storage. */
'use strict';
const $ = id => document.getElementById(id);
const actions = ['Go for it','Field goal','Punt'];
const colors = {'Go for it':'#6ad0a9','Field goal':'#edab5e','Punt':'#77aaee'};
const statements = [
  'I could identify the highest estimated win-probability option.',
  'I could recognize when two options had similar estimates.',
  'The interface made it easy to compare the three options.',
  'The probability information was clear.',
  'I felt confident interpreting the estimates.'
];
let state = null;
function show(id) { for(const s of ['intro','trial','survey','done']) $(s).classList.toggle('hidden',s!==id); window.scrollTo(0,0); }
function safeNum(v) { return Number.isFinite(Number(v)) ? Number(v) : null; }
function clock(s) {return `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;}
function context(row){const s=row.scenario;return `4th & ${s.ydstogo} · Opponent's ${s.yardline_100} · ${s.score_differential<0?'Trailing by '+Math.abs(s.score_differential):s.score_differential>0?'Leading by '+s.score_differential:'Tied'} · Q${s.qtr} · ${clock(s.seconds_in_quarter)} left in quarter`;}
function renderTable(row){
 const table=document.createElement('table');table.className='prob-table';
 const head=document.createElement('thead');head.innerHTML='<tr><th>Decision</th><th>Estimated win probability</th></tr>';table.append(head);
 const body=document.createElement('tbody');for(const n of actions){const tr=document.createElement('tr');const a=document.createElement('td');a.textContent=n;const b=document.createElement('td');b.textContent=row.probabilities[n].toFixed(2)+'%';tr.append(a,b);body.append(tr);}table.append(body);$('display-area').replaceChildren(table);
}
function renderInteractive(row){
 const mount=$('display-area');mount.replaceChildren();
 if(typeof d3==='undefined'){const p=document.createElement('p');p.textContent='Chart library unavailable; displaying accessible equivalent table.';mount.append(p);renderTable(row);return;}
 const widths=720,h=260,m={left:95,right:32,top:24,bottom:40},inner=widths-m.left-m.right;
 const svg=d3.select(mount).append('svg').attr('viewBox',`0 0 ${widths} ${h}`).attr('role','img').attr('aria-label','Interactive bar chart of estimated win probabilities').style('max-width','100%');
 const x=d3.scaleLinear().domain([0,100]).range([m.left,widths-m.right]);
 svg.append('g').attr('transform',`translate(0,${h-m.bottom})`).call(d3.axisBottom(x).tickValues([0,20,40,60,80,100]).tickFormat(d=>d+'%')).selectAll('text').attr('fill','#bbd0d9');
 const tip=document.createElement('div');tip.className='viz-tip';tip.textContent='Hover over a bar to read its exact estimate.';
 for(let i=0;i<actions.length;i++){
  const name=actions[i],v=row.probabilities[name],y=m.top+i*62;
  svg.append('text').attr('x',m.left-12).attr('y',y+23).attr('text-anchor','end').attr('fill','#dbe9eb').attr('font-size',15).text(name);
  svg.append('rect').attr('x',x(0)).attr('y',y).attr('width',inner).attr('height',32).attr('rx',6).attr('fill','#263b49');
  svg.append('rect').attr('x',x(0)).attr('y',y).attr('width',Math.max(1,x(v)-x(0))).attr('height',32).attr('rx',6).attr('fill',colors[name]).attr('tabindex',0).attr('role','img').attr('aria-label',`${name}: ${v.toFixed(2)} percent`).on('mouseenter focus',()=>tip.textContent=`${name}: ${v.toFixed(2)}% estimated win probability`).on('mouseleave blur',()=>tip.textContent='Hover over a bar to read its exact estimate.');
  svg.append('text').attr('x',x(v)+8).attr('y',y+22).attr('fill','#f0f7f8').attr('font-size',14).text(`${v.toFixed(2)}%`);
 }
 mount.append(tip);
}
function renderTrial(){
 const b=state.blocks[state.block],r=b.rows[state.task];
 $('progress').textContent=`TASK ${state.trials.length+1} OF 12 · BLOCK ${state.block+1} OF 2`;
 $('condition-title').textContent=b.mode==='static'?'Read the probability table':'Explore the probability chart';
 $('condition-pill').textContent=b.mode==='static'?'A / Static table':'B / Interactive chart';
 $('instruction').textContent=b.mode==='static'?'Use the numerical values in the static table.':'The chart is interactive: hover over each bar to inspect its estimate.';
 $('game-context').textContent=context(r);
 if(b.mode==='static')renderTable(r);else renderInteractive(r);
 $('answers').reset();state.trialStart=performance.now();show('trial');
}
function begin(){
 const n=Number($('participant').value),foot=$('football').value,charts=$('charts').value,prior=$('prior').value;
 if(!Number.isSafeInteger(n)||n<1||n>9999||!foot||!charts||!prior||!$('consent').checked){$('intro-error').textContent='Enter an assigned participant number, answer all background questions, and check voluntary consent.';return;}
 $('intro-error').textContent='';
 const scenarios=state.scenarios;const a=scenarios.filter(r=>r.set==='A'),b=scenarios.filter(r=>r.set==='B');
 // 4 counterbalanced allocations: AB on sets A/B, BA on A/B, AB on B/A, BA on B/A.
 const allocation=(n-1)%4,order=allocation%2===0?['static','interactive']:['interactive','static'];
 const sets=allocation<2?[a,b]:[b,a];
 state={...state,participant:n,background:{football:foot,chart_comfort:charts,prior},allocation:allocation+1,blocks:[{mode:order[0],rows:sets[0]},{mode:order[1],rows:sets[1]}],block:0,task:0,trials:[],survey:{}};
 renderTrial();
}
function submitTrial(e){
 e.preventDefault();const form=new FormData(e.currentTarget),row=state.blocks[state.block].rows[state.task];
 const choice=form.get('best'),gap=safeNum(form.get('gap')),close=form.get('close');
 if(!actions.includes(choice)||gap===null||gap<0||gap>100||!['yes','no'].includes(close))return;
 const duration=Math.round((performance.now()-state.trialStart)/100)/10;
 state.trials.push({study_version:'study-v1',participant_id:state.participant,allocation:state.allocation,
  block:state.block+1,trial_number:state.trials.length+1,condition:state.blocks[state.block].mode,scenario_set:row.set,scenario_id:row.id,
  ydstogo:row.scenario.ydstogo,yardline_100:row.scenario.yardline_100,score_differential:row.scenario.score_differential,qtr:row.scenario.qtr,seconds_in_quarter:row.scenario.seconds_in_quarter,
  wp_go:row.probabilities['Go for it'],wp_fg:row.probabilities['Field goal'],wp_punt:row.probabilities['Punt'],
  response_best:choice,correct_best:row.correct_best,best_correct:Number(choice===row.correct_best),response_gap_pp:gap,correct_gap_pp:row.correct_gap_pp,gap_absolute_error_pp:+Math.abs(gap-row.correct_gap_pp).toFixed(2),response_close:close,correct_close:row.correct_close?'yes':'no',close_correct:Number((close==='yes')===row.correct_close),duration_seconds:duration});
 state.task++;
 if(state.task===6)renderSurvey();else renderTrial();
}
function renderSurvey(){
 const mode=state.blocks[state.block].mode;
 $('survey-progress').textContent=`AFTER BLOCK ${state.block+1} OF 2`;
 $('survey-title').textContent=`Rate the ${mode==='static'?'static table':'interactive chart'}`;
 const target=$('survey-items');target.replaceChildren();
 statements.forEach((s,i)=>{const row=document.createElement('label');row.className='likert-row';const title=document.createElement('span');title.textContent=s;const sel=document.createElement('select');sel.name='q'+(i+1);sel.required=true;const prompt=document.createElement('option');prompt.value='';prompt.textContent='Select 1–5';sel.append(prompt);for(let v=1;v<=5;v++){const o=document.createElement('option');o.value=v;o.textContent=v;sel.append(o);}row.append(title,sel);target.append(row);});
 show('survey');
}
function submitSurvey(e){
 e.preventDefault();const scores={};for(let i=1;i<=5;i++){let sel=e.currentTarget.elements['q'+i],v=sel.value;if(!v)return;scores['usability_q'+i]=Number(v);}state.survey[state.blocks[state.block].mode]=scores;
 if(state.block===0){state.block=1;state.task=0;renderTrial();}else show('done');
}
function csvValue(v){const s=String(v??'');return '"'+s.replace(/"/g,'""')+'"';}
function exportCSV(){
 const pref=$('preferred').value;
 if(!pref){$('export-status').textContent='Choose an interface preference before exporting.';return;}
 const fb=$('feedback').value.slice(0,500);
 const records=state.trials.map(r=>({...r,football_familiarity:state.background.football,chart_comfort:state.background.chart_comfort,prior_analytics:state.background.prior,
     ...state.survey[r.condition],preferred_interface:pref,optional_feedback:fb}));
 const headers=Object.keys(records[0]);const csv=[headers.join(','),...records.map(r=>headers.map(h=>csvValue(r[h])).join(','))].join('\r\n');
 const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`fourth_down_study_P${String(state.participant).padStart(3,'0')}.csv`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
 $('export-status').textContent=`Downloaded ${records.length} task rows. Give the CSV file to the study facilitator.`;
}
async function init(){
 try{const response=await fetch('/static/data/study_scenarios.json',{cache:'no-store'});if(!response.ok)throw Error('Unable to load study scenarios');const data=await response.json();if(data.scenarios.length!==12)throw Error('Study requires exactly 12 tasks');state={scenarios:data.scenarios};}
 catch(err){$('intro-error').textContent=`Study setup unavailable: ${err.message}`;$('begin').disabled=true;}
 $('begin').addEventListener('click',begin);$('answers').addEventListener('submit',submitTrial);$('survey-form').addEventListener('submit',submitSurvey);$('export').addEventListener('click',exportCSV);
}
init();

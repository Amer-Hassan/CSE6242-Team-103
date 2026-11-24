// Benchmark visualizations are independent of live decision-engine calls.
// Reference data contains the exact paired 2025 model outputs from the uploaded CSV.
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const names = ['Go for it','Field goal','Punt'];
  const colors = {'Go for it':'#70d2a7','Field goal':'#ebaf63','Punt':'#79aaf2'};
  const num = v => typeof v === 'number' && Number.isFinite(v);
  const pct = v => num(v) ? (v*100).toFixed(2)+'%' : 'N/A';
  const pp = v => num(v) ? v.toFixed(2)+' pp' : 'N/A';
  let all = [];
  let activeId = null;
  const key = r => `${r.game_id}:${r.play_id}`;
  const safe = n => Number.isFinite(n) ? n : 0;
  const distanceGroup = d => d<=3?'short':d<=7?'medium':'long';
  const maximumDiff = r => Math.max(...['go','fg','punt'].map(a => Math.abs(r['difference_'+a+'_wp_pp'])).filter(num));
  const compact = name => name==='Go for it'?'GO':name==='Field goal'?'FG':'PUNT';
  const scored = r => num(r.our_gap_pp)?r.our_gap_pp:Infinity;
  function makeCard(label,value,note){
    const card = document.createElement('div');card.className='benchmark-kpi';
    const l=document.createElement('span');l.textContent=label;
    const v=document.createElement('strong');v.textContent=value;
    const n=document.createElement('small');n.textContent=note;
    card.append(l,v,n);return card;
  }
  function current(){
    const act=$('bm-action').value, dist=$('bm-distance').value, scope=$('bm-scope').value, agree=$('bm-agreement').value;
    return all.filter(r=>
      (act==='all'||r.actual_action===act) &&
      (dist==='all'||distanceGroup(r.ydstogo)===dist) &&
      (scope==='all'||(r.three_action_case && (scope==='three'||(scope==='close'?r.our_gap_pp<2:r.our_gap_pp>=2)))) &&
      (agree==='all'||Boolean(r.recommendation_agrees)===(agree==='agree'))
    );
  }
  function drawKPIs(rows){
    const three=rows.filter(r=>r.three_action_case);
    const matches=rows.filter(r=>Boolean(r.recommendation_agrees));
    const strict=three.filter(r=>Boolean(r.recommendation_agrees));
    const k=$('benchmark-kpis');k.replaceChildren();
    k.append(
      makeCard('Matched situations',rows.length,'From the balanced 2025 sample'),
      makeCard('Shared-action agreement',rows.length?(matches.length/rows.length*100).toFixed(1)+'%':'—',`${matches.length} / ${rows.length} comparable cases`),
      makeCard('Three-action agreement',three.length?(strict.length/three.length*100).toFixed(1)+'%':'—',`${strict.length} / ${three.length} complete cases`),
      makeCard('Missing nfl4th punt',rows.length-three.length+'', 'Excluded only from three-action analysis')
    );
  }
  function drawMatrix(rows){
    const data=rows.filter(r=>r.three_action_case);
    const svgW=430, svgH=345,left=108,top=74,size=93;
    const holder=d3.select('#benchmark-matrix');holder.selectAll('*').remove();
    const svg=holder.append('svg').attr('viewBox',`0 0 ${svgW} ${svgH}`).attr('role','img').attr('aria-label','Three-action recommendation confusion matrix');
    if(!data.length){holder.append('p').attr('class','small muted').text('No complete three-action cases in the selected filters.');return;}
    const maxVal=d3.max(names.flatMap(a=>names.map(b=>data.filter(r=>r.our_shared_best===a&&r.nfl4th_best===b).length)))||1;
    names.forEach((a,i)=>{
      const l=svg.append('text').attr('x',left-10).attr('y',top+i*size+size/2+4).attr('text-anchor','end').attr('class','bm-label');l.text(compact(a));
      svg.append('text').attr('x',left+i*size+size/2).attr('y',top-17).attr('text-anchor','middle').attr('class','bm-label').text(compact(a));
      names.forEach((b,j)=>{
        const n=data.filter(r=>r.our_shared_best===a&&r.nfl4th_best===b).length;
        svg.append('rect').attr('x',left+j*size+3).attr('y',top+i*size+3).attr('width',size-6).attr('height',size-6).attr('rx',8)
          .attr('fill',a===b?'#2d8f70':'#344958').attr('opacity',.20+.8*n/maxVal);
        svg.append('text').attr('x',left+j*size+size/2).attr('y',top+i*size+size/2+6).attr('class','bm-number').attr('text-anchor','middle').text(n);
      });
    });
    svg.append('text').attr('x',left+size*1.5).attr('y',top-48).attr('text-anchor','middle').attr('class','bm-axis-title').text('nfl4th recommendation →');
    svg.append('text').attr('transform',`translate(20,${top+size*1.5}) rotate(-90)`).attr('text-anchor','middle').attr('class','bm-axis-title').text('Our recommendation →');
  }
  function drawMAE(rows){
    const values=[['Go for it','go'],['Field goal','fg'],['Punt','punt']].map(([name,code])=>{
      const available=rows.map(r=>r['difference_'+code+'_wp_pp']).filter(num);
      return {name,count:available.length,value:available.length?d3.mean(available.map(Math.abs)):null};
    });
    const holder=d3.select('#benchmark-mae');holder.selectAll('*').remove();
    const w=420,h=315,left=90,right=77,top=36;
    const maxVal=d3.max(values.map(d=>d.value||0))||1;
    const x=d3.scaleLinear().domain([0,Math.max(10,maxVal*1.15)]).range([left,w-right]);
    const svg=holder.append('svg').attr('viewBox',`0 0 ${w} ${h}`).attr('role','img').attr('aria-label','Mean absolute differences between models in percentage points');
    svg.append('g').attr('transform',`translate(0,${h-45})`).attr('class','axis').call(d3.axisBottom(x).ticks(4).tickFormat(d=>d+' pp'));
    values.forEach((d,i)=>{
      const y=55+i*69;
      svg.append('text').attr('x',left-9).attr('y',y+15).attr('text-anchor','end').attr('class','bm-label').text(compact(d.name));
      if(d.value!==null)svg.append('rect').attr('x',left).attr('y',y).attr('height',25).attr('width',Math.max(1,x(d.value)-x(0))).attr('rx',5).attr('fill',colors[d.name]);
      svg.append('text').attr('x',w-right+9).attr('y',y+16).attr('class','bm-mae-value').text(d.value===null?'N/A':d.value.toFixed(2));
      svg.append('text').attr('x',left).attr('y',y+42).attr('class','bm-note').text(`n = ${d.count}`);
    });
  }
  function drawSelected(row){
    const aside=$('benchmark-selected');aside.replaceChildren();
    if(!row){aside.innerHTML='<h3>Select a game</h3><p class="small muted">Click a benchmark case to inspect both predictions.</p>';return;}
    const head=document.createElement('h3');head.textContent=`${row.game_id.replaceAll('_',' ')} · play ${row.play_id}`;aside.append(head);
    const sit=document.createElement('p');sit.className='small muted';sit.textContent=`Q${row.qtr} · 4th & ${row.ydstogo} · ${row.yardline_100} yards to goal · score difference ${row.score_differential>=0?'+':''}${row.score_differential}`;aside.append(sit);
    const actual=document.createElement('p');actual.className='small';actual.textContent=`Actual coaching choice: ${row.actual_action}`;aside.append(actual);
    const title=document.createElement('p');title.className='small';title.textContent=`Our shared-action choice: ${row.our_shared_best} · nfl4th: ${row.nfl4th_best}`;aside.append(title);
    const table=document.createElement('table');table.className='benchmark-detail-table';
    const h=document.createElement('thead');const hr=document.createElement('tr');['Decision','Our WP','nfl4th WP','Difference'].forEach(t=>{let el=document.createElement('th');el.textContent=t;hr.append(el)});h.append(hr);table.append(h);
    const body=document.createElement('tbody');
    [['Go for it','go'],['Field goal','fg'],['Punt','punt']].forEach(([name,code])=>{
      const tr=document.createElement('tr');
      [name,pct(row['our_'+code+'_wp']),pct(row[code+'_wp']),pp(row['difference_'+code+'_wp_pp'])].forEach(value=>{const cell=document.createElement('td');cell.textContent=value;tr.append(cell);});body.append(tr);
    });table.append(body);aside.append(table);
    const gap=document.createElement('p');gap.className='small muted';gap.textContent=`Our model's decision gap: ${pp(row.our_gap_pp)}. ${row.three_action_case?'All three nfl4th actions available.':'nfl4th punt estimate unavailable; recommendation compares only shared actions.'}`;aside.append(gap);
  }
  function drawTable(rows){
    const sorted=[...rows];const sort=$('bm-sort').value;
    sorted.sort((a,b)=>sort==='week'?(a.week-b.week):(sort==='close'?(scored(a)-scored(b)):(maximumDiff(b)-maximumDiff(a))));
    const body=$('benchmark-tbody');body.replaceChildren();
    sorted.slice(0,35).forEach(r=>{
      const tr=document.createElement('tr');tr.tabIndex=0;tr.setAttribute('role','button');tr.setAttribute('aria-label',`Inspect ${r.game_id} play ${r.play_id}`);
      if(key(r)===activeId)tr.className='selected';
      [r.game_id.replace('2025_','').replaceAll('_',' '),`4th & ${r.ydstogo}, goal ${r.yardline_100}`,r.actual_action,r.our_shared_best,r.nfl4th_best,r.recommendation_agrees?'Yes':'No'].forEach((v,i)=>{const td=document.createElement('td');td.textContent=v;if(i===5)td.className=r.recommendation_agrees?'bm-agree':'bm-disagree';tr.append(td);});
      const select=()=>{activeId=key(r);drawSelected(r);body.querySelectorAll('tr').forEach(item=>item.classList.toggle('selected',item===tr));};
      tr.addEventListener('click',select);tr.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}});body.append(tr);
    });
    if(!sorted.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=6;td.textContent='No cases match these filters.';tr.append(td);body.append(tr);}
    $('benchmark-status').textContent=`Showing ${rows.length} matched cases (${Math.min(rows.length,35)} rows below). ${rows.filter(r=>r.three_action_case).length} have all three nfl4th actions.`;
    drawSelected(sorted.find(r=>key(r)===activeId)||sorted[0]||null);
  }
  function render(){const rows=current();drawKPIs(rows);drawMatrix(rows);drawMAE(rows);drawTable(rows);}
  ['bm-action','bm-distance','bm-scope','bm-agreement','bm-sort'].forEach(id=>$(id).addEventListener('change',render));
  fetch('/static/data/benchmark_2025.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error(`HTTP ${r.status}`);return r.json();})
    .then(data=>{all=data.rows;render();}).catch(err=>{$('benchmark-status').textContent='Unable to load benchmark data: '+err.message;});
})();

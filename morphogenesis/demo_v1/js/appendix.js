/* Appendix A (why the memory can be switched) and B (glossary) */
'use strict';
function loopDiagram(cv,w,h){
  const g=cv.getContext('2d'),d=Math.min(window.devicePixelRatio||1,2);cv.width=w*d;cv.height=h*d;cv.style.width=w+'px';cv.style.height=h+'px';g.setTransform(d,0,0,d,0,0);g.fillStyle='#fff';g.fillRect(0,0,w,h);
  const node=(x,y,r,f)=>{g.fillStyle=f;g.strokeStyle='rgba(0,0,0,.5)';g.lineWidth=1.5;g.beginPath();g.arc(x,y,r,0,6.3);g.fill();g.stroke();};
  const arrow=(a,b,c2,col,wd)=>{g.strokeStyle=col||C.ink;g.fillStyle=col||C.ink;g.lineWidth=wd||2.4;g.beginPath();g.moveTo(a[0],a[1]);g.lineTo(b[0],b[1]);g.stroke();const an=Math.atan2(b[1]-a[1],b[0]-a[0]);g.beginPath();g.moveTo(b[0],b[1]);g.lineTo(b[0]-10*Math.cos(an-.4),b[1]-10*Math.sin(an-.4));g.lineTo(b[0]-10*Math.cos(an+.4),b[1]-10*Math.sin(an+.4));g.fill();};
  g.textBaseline='top';g.font='700 15px '+FONT;g.fillStyle=C.ink;g.textAlign='left';g.fillText('Earlier version: a cell counts its own signal',20,10);g.fillText('Here: a cell listens only to its neighbours',w/2+20,10);
  // v2
  node(150,130,30,C.sa);g.strokeStyle=C.ink;g.lineWidth=2.6;g.beginPath();g.arc(150,84,24,Math.PI*0.72,Math.PI*0.28,false);g.stroke();{const ex=150+24*Math.cos(Math.PI*0.28),ey=84+24*Math.sin(Math.PI*0.28);g.fillStyle=C.ink;g.beginPath();g.moveTo(ex+2,ey+4);g.lineTo(ex+9,ey-9);g.lineTo(ex-8,ey-5);g.closePath();g.fill();}g.font='13px '+FONT;g.fillStyle='#333';g.textAlign='center';g.fillText('its own signal counts as evidence',150,190);g.fillText('→ confirms itself, cannot switch',150,208);
  [[40,170],[260,170],[270,95]].forEach(p=>{node(p[0],p[1],14,'#CCC');});
  g.textAlign='left';g.fillStyle=C.bad;g.font='700 13.5px '+FONT;g.fillText('never switched',20,34);
  // v3
  const cx=w/2+170,cy=125;node(cx,cy,30,C.sa);[[cx-120,cy-60],[cx-130,cy+40],[cx+110,cy-60],[cx+120,cy+50]].forEach(p=>{node(p[0],p[1],14,C.sa);arrow([p[0]+(p[0]<cx?14:-14)*Math.cos(0),p[1]+(p[1]<cy?8:-8)],[cx+(p[0]<cx?-28:28),cy+(p[1]<cy?-10:10)],0,'#555',2);});
  g.fillStyle='#eee';g.fillRect(cx-70,cy+52,140,12);for(let u=0;u<140;u++){g.fillStyle=rhoColor(u/140);g.fillRect(cx-70+u,cy+52,1,12);}g.fillStyle=C.ink;g.fillRect(cx-70+0.88*139,cy+48,3,20);
  g.font='13px '+FONT;g.fillStyle='#333';g.textAlign='center';g.fillText('share of blue signal from neighbours only',cx,cy+70);g.fillText('no self-confirming → can be switched',cx,cy+88);
  g.textAlign='left';g.fillStyle=C.ok;g.font='700 13.5px '+FONT;g.fillText('can be switched',w/2+20,34);
}
Demo.register({id:'A',act:'A',title:COPY['A'].title,data:[],duration:0,truthOffered:false,legend:[{color:C.sa,label:'blue state'},{color:C.sb,label:'pink state'}],
  caption:COPY['A'].caption,takeaway:COPY['A'].takeaway,
  notes:'dl/dt = −2r sinh l + g(2f − 1). l = memory logit of a cell, rho = sigma(l) its belief in the blue state (state a); r = relaxation rate towards undecided (0.05); g = coupling gain (0.6); f = fraction A/(A+B) of memory ligand sensed from neighbours j != i (kernel-weighted); in the mean field f = rho, so g(2f−1) = g tanh(l/2). Potential U(l) = 2r cosh l − 2g ln cosh(l/2): minima at ±l* = ±2 arccosh sqrt(g/4r) = ±2.292 and a barrier at l = 0 when g > 4r (here g/4r = 3, barrier 0.26). Isolated cell: f = 1/2 exactly, so l relaxes at rate 2r. The earlier model (v2, a cell reads its own secretion) switched in 0 of 560 trials; the present model (v3) in 57 of 60 held-out dishes.',
  sources:[{what:'Memory module equation, parameters r = 0.05, g = 0.6',file:'testbed_v3/ENGINE_SPEC_V3.md',sec:'Model as implemented'},{what:'Mean-field theory: l* = 2.292, barrier 0.259',file:'testbed_v3/MEMORY_V3.md',sec:'H2'},{what:'v2 (self-reading) never switched',file:'testbed_v2/SWITCH.md',sec:'Gate G3'}],
  setup(c){
    c.state.r=0.05;c.state.g=0.6;c.state.ball={l:-0.8,v:0};const top=el('div',{class:'pw',style:'width:100%'},c.vis);c.dg=makeCanvas(top,1060,235);
    const row=el('div',{style:'display:flex;gap:16px;flex-wrap:wrap;justify-content:center;width:100%;margin-top:4px'},c.vis);
    const w1=el('div',{class:'pw'},row);c.cv=makeCanvas(w1,560,300);c.cv.style.cursor='crosshair';
    const w2=el('div',{class:'pw'},row);c.eq=makeCanvas(w2,520,300);
    c.cv.addEventListener('click',e=>{const r=c.cv.getBoundingClientRect(),x=(e.clientX-r.left)*(560/r.width);const l=-5+(x-46)/(560-46-14)*10;c.state.ball={l:Math.max(-5,Math.min(5,l)),v:0};});
    const sl=(lab,min,max,step,val,key)=>{const L=el('label',{},c.ctrls,lab+' <input type="range" min="'+min+'" max="'+max+'" step="'+step+'" value="'+val+'"> <b>'+val+'</b>');L.querySelector('input').oninput=function(){c.state[key]=+this.value;L.querySelector('b').textContent=(+this.value).toFixed(3);};};
    sl('r = '+COPY['A'].r,0.01,0.2,0.005,0.05,'r');sl('g = '+COPY['A'].g,0.05,1.2,0.01,0.6,'g');
    const rs=el('button',{class:'btn'},c.ctrls,'reset');rs.onclick=()=>{c.state.r=0.05;c.state.g=0.6;c.ctrls.querySelectorAll('input').forEach((i,k)=>{i.value=k?0.6:0.05;i.nextElementSibling.textContent=k?'0.600':'0.050';});};
    Demo.tickers.push(()=>{const s=c.state,b=s.ball;const dU=(l)=>2*s.r*2*Math.sinh(l)/2*1-0;const F=(l)=>-2*s.r*Math.sinh(l)+s.g*Math.tanh(l/2);for(let k=0;k<4;k++){b.l+=0.04*F(b.l)*2.0;}Demo.redraw();});},
  draw(c){
    loopDiagram(c.dg,1060,235);
    const s=c.state,U=(l)=>2*s.r*Math.cosh(l)-2*s.g*Math.log(Math.cosh(l/2));const g=c.cv.getContext('2d');const ls=[];for(let i=0;i<=200;i++)ls.push(-5+i*0.05);const us=ls.map(U);const ym=Math.min(...us),yM=Math.min(Math.max(...us),ym+3.2);
    const ch=new Chart(c.cv,{w:560,h:300,xlim:[-5,5],ylim:[ym-1.1,yM+0.3],yticks:[],xticks:[-4,-2,0,2,4],xlabel:'leaning l (negative: pink · positive: blue)'});ch.clear();ch.axes();
    ch.line(ls,us.map(u=>Math.min(u,yM+0.25)),{color:C.ink,w:2.6});const bist=s.g>4*s.r,lst=bist?2*Math.acosh(Math.sqrt(s.g/(4*s.r))):0;
    if(bist){[-lst,lst].forEach(v=>{ch.dot(v,U(v),{color:v>0?C.sa:C.sb,r:6});ch.text('stable',ch.X(v),ch.Y(U(v))-14,{align:'center',size:12.5,bold:true,color:v>0?'#1f7fb5':'#a0457f'});});ch.dot(0,U(0),{color:'#fff',stroke:C.ink,r:5});ch.text('tipping point',ch.X(0),ch.Y(U(0))-12,{align:'center',size:12,color:C.mute});}
    const b=s.ball;ch.dot(b.l,U(b.l),{color:rhoColor(1/(1+Math.exp(-b.l))),stroke:C.ink,r:9});
    ch.text(bist?COPY['A'].readout+' ✔':'only one stable state (no memory): g is not more than 4 times r',ch.X(0),ch.Y(yM)+4,{size:14,bold:true,align:'center',color:bist?C.ok:C.bad});
    const e=c.eq.getContext('2d'),dpr=Math.min(window.devicePixelRatio||1,2);c.eq.width=520*dpr;c.eq.height=300*dpr;c.eq.style.width='520px';c.eq.style.height='300px';e.setTransform(dpr,0,0,dpr,0,0);e.fillStyle='#fff';e.fillRect(0,0,520,300);
    e.fillStyle=C.ink;e.textAlign='left';e.textBaseline='top';e.font='700 17px '+FONT;e.fillText('dl/dt = −2r·sinh l + g·(2f − 1)',12,14);
    e.font='14px '+FONT;COPY['A'].symbols.forEach((t,i)=>{wrapText(e,t,496).forEach((ln,j)=>e.fillText(ln,12,52+i*40+j*18));});
    e.font='700 14px '+FONT;e.fillText('here r = '+s.r.toFixed(3)+', g = '+s.g.toFixed(3),12,230);
  }
});

/* ---------------- B glossary ---------------- */
const GLOSS=[
 ['organism','a group of cells that we treat as one body (also called the collective).'],
 ['cell','one of the 24 units of the model (also called a node); it has a position, releases signals and senses its neighbours.'],
 ['group state','which of two lasting memories the organism holds, the blue state or the pink state.'],
 ['blue state / pink state','the two group states; sky blue and reddish purple on every picture.'],
 ['memory signals','the blue and pink signals every cell releases; their mix shows which state the cell believes in.'],
 ['yellow marker','a visible marker lit on one row of cells to show the group state; no cell reacts to it.'],
 ['body signals','the signals that tell a cell what kind it is (head, middle, side or tail) and hold the body\'s shape.'],
 ['outline','a line drawn around the cells we count as one organism; a grouping we choose.'],
 ['blanket','the inputs and outputs of a cell (what it senses and what it does) that separate its inside from the outside.'],
 ['interface','the place where a push gets in; for a lit patch, its edge.'],
 ['same-body check','passes only if the same cells are present and the shape stays inside the range an untouched organism shows by itself.'],
 ['untouched twin','a copy of the dish with identical random jitter but no treatment.'],
 ['fake treatment','the same procedure with the light switched to zero; it behaves like the untouched twin.'],
 ['new dishes it had never seen','dishes kept locked away until the controller and its tests were fixed.'],
 ['blind analysis','a program that saw only what an observer can see and had to work out identity by itself.'],
 ['blind controller','a program that saw only what an observer can see and chose where, when and how long to shine.'],
 ['tipping point','the point beyond which the organism finishes switching state by itself.'],
 ['time unit','the model\'s unit of time.'],
 ['cell-width','the usual distance between two neighbouring cells; our unit of length.']];
Demo.register({id:'B',act:'A',title:COPY['B'].title,data:[],duration:0,truthOffered:false,legend:[],
  caption:COPY['B'].caption,takeaway:COPY['B'].takeaway,
  notes:'Internal names: organism = collective; cell = node; blue/pink state = state a/b = S+/S−; memory signals = memory ligands A/B (c4, c5); yellow marker = reporter (c0); body signals = c1–c3; head-to-tail signal = c6; same-body check = V_body; untouched twin = CRN twin; fake treatment = sham; new dishes = held-out; blind analysis = T4; blind controller = T5; Light n = Ln; tracked cells / unlabelled dots / microscope images = O1 / O2 / O3.',
  sources:[{what:'Definitions',file:'t5_blind_control/MONITOR.md, CONTROLLER.md; testbed_v3/ENGINE_SPEC_V3.md'},{what:'Package-label mapping',file:'testbed_v3/audit_t4/AUDIT_T4.md; AUDIT_T5 A5'}],
  setup(c){const g=el('div',{class:'tcap',style:'display:grid;grid-template-columns:240px 1fr;gap:6px 14px;max-width:1100px;margin:0 auto;font-size:15px;line-height:1.35'},c.vis);GLOSS.forEach(t=>{el('div',{style:'font-weight:700;text-align:right'},g,t[0]);el('div',{},g,t[1]);});},
  draw(){}
});

/* ---------------- C about the data ---------------- */
const PROV=[
 ['1.1','Octave oracle (canonical clock); natural body 2100','oracle seed 0; run_00011','m2a_audit_and_library/data/part0/direct_primary_0000.mat; testbed_v3/data/raw_v4/natural/a_cal_2100.pkl'],
 ['1.2–1.4','same body, states a (run_00011) and b (run_00133), t = 3000–3059','body 2100','a_cal_2100.pkl, b_cal_2100.pkl'],
 ['1.5','re-simulated N = 1, 4, 24, sigma_h = 0.7, 600 tu','seed 0 (rule in build_mem15.py)','data/mem15.js'],
 ['2.1, 2.3','package observables + hidden tier','run_00011, 00263, 00640, 01105','testbed_blind_v3/runs; testbed_v3/data/blind_v3_hidden'],
 ['2.2','six tool clips, truth view','run_00283 (cut), 00515 (pull out), 00953 (replace), 00640 (merge), 01105 (light), 01924 (bath)','data/c22b.js; build/build_c22b.py'],
 ['2.3, 3.1','per-view outlines from the blind pipelines’ grouping code (T4 pipeline for tracked cells, dots, glow; T5 spot detection + same linking rule for cell markers)','run_01105 (2.3), run_00283 (3.1)','data/c23o.js, data/c31.js; build/build_c31.py'],
 ['3.2','frozen T5 monitor (hash in FROZEN_HASH.txt) on run_00266, run_00263, held-out seed 6007 controller (164/164 frames equal the live log)','6007','data/c32.js'],
 ['3.3','serial replacement, noise-free','seed 0','data/c33.js'],
 ['3.4','T4 outputs + true state','260 natural dishes','t4_blind_identity/outputs; testbed_v3/data/blind_v2_hidden'],
 ['4.1','re-simulated lights L1–L5, amp 5, 10 tu, both start states','dev seed 5001','data/c41.js'],
 ['4.2','T5 blind dose map; audit A4 true maps and duration curve; equal-dose clips','4 dev dishes; 6000/6003/6007; dev seed 5004','data/c42map.js, data/c42clips.js'],
 ['4.3','body frame of a settled organism, kernel coupling','body 2100','data/body2100.js'],
 ['4.4','sealed hidden logs + T5 episode logs','seed 6007: episodes 988 (controller), 991 (random), 994 (whole body, same light), 989 (twin)','data/c43.js'],
 ['4.5','heldout_eval.json, audit A1 truth, audit A3 regret, worst episode','60 dishes; seed 6026 (ep 1121)','data/c44stats.js, data/c44worst.js'],
 ['5.1','syntheses, audit, flock clip, oracle, 4.4 clip','flock seed 37','data/c51flock.js']];
Demo.register({id:'C',act:'A',title:COPY['C'].title,data:[],duration:0,truthOffered:false,legend:[],
  caption:COPY['C'].caption,takeaway:COPY['C'].takeaway,
  notes:'All provenance of the demo lives here (moved out of the chapter screens and out of DEMO_README.md).',
  sources:[],
  setup(c){const w=el('div',{style:'max-width:1100px;margin:0 auto;font-size:15px;line-height:1.4'},c.vis);
    el('p',{},w,'Every picture in this demo comes from simulated runs of the model. Where a chapter shows what an observer sees, the views are the ones a blind program received. Where it shows hidden things (guesses, memory, true cell types), they come from the hidden record of the same run, which no blind program ever saw. A few short clips were re-simulated exactly (same random numbers, same actions) to show something the original run did not record.');
    el('p',{},w,'This demo contains hidden information and must never be given to a blind session.');
    const dr=el('details',{class:'srcdrawer'},w,'<summary style="cursor:pointer;font-weight:700">Sources: full provenance table</summary>');
    let h='<table style="border-collapse:collapse;font-size:13px;margin-top:8px"><tr>'+['chapter','what','run ids / seeds','files'].map(x=>'<th style="text-align:left;border-bottom:1px solid #999;padding:3px 8px">'+x+'</th>').join('')+'</tr>';
    PROV.forEach(r=>{h+='<tr>'+r.map(x=>'<td style="vertical-align:top;border-bottom:1px solid #ddd;padding:3px 8px">'+x+'</td>').join('')+'</tr>';});dr.insertAdjacentHTML('beforeend',h+'</table>');},
  draw(){}
});

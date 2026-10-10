/* Act 5 - What it means (5.1, 5.2) */
'use strict';
function chk(kind,text){return '<div style="margin:2px 0">'+badge(kind==='ok'?'yes':kind==='bad'?'no':'partly',kind==='ok'?'ok':kind==='bad'?'bad':'neu')+'</div><div style="font-size:12.5px;color:#333;line-height:1.3">'+text+'</div>';}
Demo.register({id:'5.1',act:5,title:'Three collectives, one set of measures',data:['data/c51flock.js','data/oracle8.js','data/c43.js'],duration:0,
  legend:[{color:'#222',label:'flock: tracked collective'},{color:'#BBBBBB',label:'flock: other birds'}].concat(TYPELEG.map(x=>({color:x.color,label:x.label+' cell'}))).slice(0,6).concat(LEG.state),
  caption:'The same five measures applied to three collectives: a translating flock, the published 8-cell morphogenesis model and our testbed. Each row is one measure with its verdict and the number behind it; the verdicts are taken from the programme\'s own syntheses and audits.',
  takeaway:'The same measures separate a collective with no interface from one with a selective, durable interface.',
  notes:'Flock column: TRANSLATING_FLOCK_FINAL_SYNTHESIS (identity tracker with 0 erroneous cross-population transfers in 72 traces; pooled forcing ≈ 0 and heterogeneous; actuator selectivity never beats random; no stable interface). Model column: VANILLA_CLOSURE (shape returns after withdrawal in all 300 runs; only role relabelling persists; no defect-free durable shape change; 6 of 246 directions switch shape, always into the defective class). Testbed column: EVALUATION + AUDIT_T5 (controller 93 % monitor-scored, 95 % by true state; random location 7 %; V_body = twin; 0 identity events in 428 episodes). The flock clip is the Stage 6.9 translation pilot of the specified model (it does not pass the translation gate; the tracked collective drifts and splits); the 8-cell clip is the Octave oracle; the testbed clip is the controller on seed 6007. “partly” = a real but limited effect.',
  audit:'Testbed verdicts use the audited truth: true success 95 %, true selectivity +0.87, 0 identity events (AUDIT_T5 A1).',
  sources:[{what:'Flock identity, efficacy, selectivity, persistence, conclusion',file:'stage6_flock/TRANSLATING_FLOCK_FINAL_SYNTHESIS.md',sec:'§1, §2, §3, §7, §8'},{what:'Published model: withdrawal, role relabelling, minimal perturbations',file:'morphogenesis/VANILLA_CLOSURE.md',sec:'§b, §c'},{what:'Testbed: controller vs random / twin, V_body',file:'t5_blind_control/EVALUATION.md',sec:'Headline table, Selectivity'},{what:'Testbed truth of the claims',file:'testbed_v3/audit_t5/AUDIT_T5.md',sec:'A1, A9'},{what:'Flock clip (Stage 6.9 specified model, seed 37)',file:'stage6_flock/interactive_demo/data/stage6_9_bundle.json',sec:'spec.frames'}],
  setup(c){
    const tbl=el('div',{style:'display:grid;grid-template-columns:150px repeat(3,minmax(250px,1fr));gap:8px 10px;width:100%;max-width:1220px;margin:0 auto'},c.vis);c.state.tbl=tbl;
    const hdr=['','Translating flock','Published 8-cell model','Testbed v3 (24 cells)'];hdr.forEach((h,i)=>el('div',{style:'font-weight:700;font-size:15px;text-align:center'},tbl,h));
    el('div',{},tbl,'');c.state.panels=[];
    for(let i=0;i<3;i++){const cell=el('div',{style:'display:flex;flex-direction:column;align-items:center'},tbl);const p=new Panel(cell,{size:210,fov:i===0?12:i===1?3.4:5.8,title:''});p.wrap=cell;p.tEl.remove();p.noBubble=true;c.panels.push(p);c.state.panels.push(p);}
    const rows=[['Identity tracked',[['ok','material tracker: 0 erroneous cross-population transfers in 72 traces'],['neu','cells fixed by construction; roles need a Hungarian match (relabelling ≠ shape change)'],['ok','O1/O2: 0 identity events in 428 held-out episodes; O3 cannot resolve cells']]],
      ['Intervention efficacy',[['neu','pooled forcing ≈ 0 (CI spans 0); some seeds respond'],['neu','role swap: displacement 0.7–8.1 or pulse 3.3–37.8; a shape switch in 6 of 246 directions'],['ok','controller flips the state in 93 % (95 % by true state) vs 0 % untreated']]],
      ['Persistence after release',[['bad','no persistent benefit reported; longer schedules raise target loss'],['bad','shape returns after withdrawal in 300/300 runs; only role relabelling stays'],['ok','held ≥ 120 tu after the last action; 57/60 dishes truly stayed switched']]],
      ['Held-out selectivity',[['bad','actuator choice never beats random on held-out (permutation null)'],['neu','tail end easiest; one body, so few independent samples (not tested held-out)'],['ok','controller − random location at matched dose: +0.87 [0.77, 0.95], p < 5·10⁻⁵']]],
      ['Durable change, identity preserved',[['bad','none demonstrated (conservative V 64 %)'],['bad','no defect-free durable shape change from the healthy body'],['ok','state change held with the body intact (V_body = untreated twin; 0 events)']]]];
    rows.forEach(r=>{el('div',{style:'font-weight:700;font-size:14.5px;align-self:center'},tbl,r[0]);r[1].forEach(x=>el('div',{style:'border:1px solid #D9D9D2;border-radius:6px;padding:6px 8px;background:#fff'},tbl,chk(x[0],x[1])));});
    // clips (tickers)
    const F=DATA.c51flock,O=DATA.oracle8,P=DATA.c43,A=P.arms.ctrl;const xf=B64.i16(F.X,1000),xo=B64.i16(O.X,1000),xc=B64.i16(A.X,1000),rc=B64.i16(A.rho,20000);const mem=F.members.map(m=>new Set(m));
    const t0=performance.now();Demo.tickers.push((ts)=>{const f=(ts-t0)/1000;
      const k=Math.max(0,Math.floor(f*6))%(F.T+4),kk=Math.min(k,F.T-1),p0=c.state.panels[0];p0.clear();const Lh=F.L/2;
      for(let i=0;i<F.N;i++){let x=xf[(kk*F.N+i)*2],y=xf[(kk*F.N+i)*2+1];const m=mem[kk].has(i);const q=p0.w2p(x,y);const g=p0.ctx;g.fillStyle=m?'#222':'#BBBBBB';g.beginPath();g.arc(q[0],q[1],m?2.6:2,0,6.3);g.fill();}
      p0.setSub('flock clip: tracked collective ('+mem[kk].size+' birds) · Stage 6.9, specified model');
      const b=Math.max(0,Math.floor(f*5))%(O.T+8),bb=Math.min(b,O.T-1),p1=c.state.panels[1];p1.clear();for(let i=0;i<8;i++)p1.node({x:xo[(bb*8+i)*2],y:xo[(bb*8+i)*2+1],fill:TYPEC[O.types[i]],r:0.28});p1.setSub('8-cell model: self-assembly, bins 1–'+O.T);
      const T=A.T,s=Math.max(0,Math.floor(f*14))%(T+30),ss=Math.min(s,T-1),p2=c.state.panels[2];p2.clear();A.acts.forEach(ac=>drawLight(p2,ac.xy,ac.r,lightWindow(ss,ac.t,ac.t+ac.dur,ac.ramp)));
      for(let i=0;i<24;i++)p2.node({x:xc[(ss*24+i)*2],y:xc[(ss*24+i)*2+1],fill:rhoColor(rc[ss*24+i]),r:0.4});p2.setSub('testbed: controller, seed 6007 (hidden memory shown) t = '+ss);});
  },
  draw(c){}
});

/* ---------------- 5.2 ---------------- */
function cardIcon(g,kind,x,y){g.save();g.translate(x,y);g.scale(1.6,1.6);g.strokeStyle=C.ink;g.fillStyle='#fff';g.lineWidth=2.2;
  const dot=(a,b,r,f)=>{g.fillStyle=f||'#777';g.beginPath();g.arc(a,b,r||5,0,6.3);g.fill();g.strokeStyle='rgba(0,0,0,.4)';g.lineWidth=1;g.stroke();};
  if(kind==='outlive'){[[-14,-6],[0,-10],[14,-6],[-7,6],[7,6]].forEach((p,i)=>dot(p[0],p[1],6,i<3?'#DDD':C.sa));g.strokeStyle=C.ink;g.lineWidth=2;g.beginPath();g.moveTo(-18,18);g.lineTo(18,18);g.lineTo(12,13);g.moveTo(18,18);g.lineTo(12,23);g.stroke();}
  else if(kind==='quorum'){dot(-17,10,4,'#DDD');[[-4,6],[2,6],[-4,12],[2,12]].forEach(p=>dot(p[0],p[1],4,C.sa));[[10,-6],[16,-6],[22,-6],[10,0],[16,0],[22,0],[10,6],[16,6],[22,6]].forEach(p=>dot(p[0]-2,p[1]+2,3.6,C.sa));}
  else if(kind==='duration'){g.strokeStyle=C.ink;g.lineWidth=2.2;g.beginPath();g.arc(0,0,17,0,6.3);g.stroke();g.beginPath();g.moveTo(0,0);g.lineTo(0,-12);g.moveTo(0,0);g.lineTo(9,5);g.stroke();g.fillStyle='rgba(192,57,43,.25)';g.beginPath();g.moveTo(0,0);g.arc(0,0,17,-Math.PI/2,-Math.PI/2+1.2);g.closePath();g.fill();}
  else if(kind==='coupling'){[[-14,0],[-4,-8],[-4,8],[6,0],[16,0]].forEach(p=>dot(p[0],p[1],5,'#999'));dot(-4,0,6,'#DDD');g.fillStyle='rgba(255,230,120,.6)';g.strokeStyle=C.ink;g.setLineDash([3,3]);g.beginPath();g.arc(-4,0,12,0,6.3);g.fill();g.stroke();}
  else{dot(-10,0,8,'#999');g.strokeStyle=C.ink;g.lineWidth=2.4;g.beginPath();g.arc(-10,-14,8,0.3,Math.PI+0.2);g.stroke();g.beginPath();g.moveTo(-17,-12);g.lineTo(-19,-6);g.lineTo(-12,-8);g.stroke();dot(12,0,6,'#CCC');g.beginPath();g.moveTo(-1,0);g.lineTo(5,0);g.stroke();g.fillStyle=C.ink;g.font='700 13px '+FONT;g.fillText('×',15,-10);}
  g.restore();}
Demo.register({id:'5.2',act:5,title:'Predictions for biology, and what\'s next',data:[],duration:0,legend:[],
  caption:'Five predictions that follow from the testbed and could be tested in real tissue — each is a measured result here, not an assumption — and four next steps.',
  takeaway:'Collective memory as a controllable, identity-preserving interface — testable in real tissue.',
  notes:'Each card cites its result. (1) serial replacement: all 24 original cells replaced, state intact in 4/4 runs; (2) group lifetime grows as exp(0.31 N) at σ_h = 0.7; an isolated cell relaxes at rate 2r = 0.1; (3) no threshold below l*/g ≈ 3.8 tu (theory; no switch up to amplitude 2,000 at 1.7 tu); T5: 2 tu never, 5 tu needs 3–4× dose; (4) location explains 54 % of the variance of log dose; threshold amplitude falls with the kernel connectivity of the lit disc (Spearman −0.98); (5) the v2 model (a cell reads its own secreted signal) never switched: 0/93 scans, 0/560 trials. These are predictions of this model, not of biology: whether real tissue has a ratiometric, neighbour-only memory signal is the experiment.',
  sources:[{what:'Memory outlives cells (serial replacement 4/4)',file:'testbed_v3/IDENTITY_EVENTS_V3.md',sec:'Serial replacement'},{what:'Quorum: lifetime ∝ exp(0.31 N)',file:'testbed_v3/MEMORY_V3.md',sec:'(d) Quorum curve'},{what:'Minimum duration',file:'testbed_v3/SWITCH_V3.md',sec:'No threshold at 1/g; T5 SYSID B2'},{what:'Location explains 54 % of dose variance; connectivity rule',file:'t5_blind_control/EVALUATION.md; testbed_v3/SWITCH_V3.md; AUDIT_T5 A4'},{what:'v2: a self-reading memory never switched (0/93)',file:'testbed_v2/SWITCH.md',sec:'Gate G3'}],
  setup(c){
    const w=el('div',{class:'pw'},c.vis);c.cv=makeCanvas(w,1180,520);c.cv.dataset.avoid='1';},
  draw(c){
    const cv=c.cv,g=cv.getContext('2d'),d=Math.min(window.devicePixelRatio||1,2);cv.width=1180*d;cv.height=520*d;cv.style.width='1180px';cv.style.height='520px';g.setTransform(d,0,0,d,0,0);g.fillStyle='#fff';g.fillRect(0,0,1180,520);
    const cards=[['outlive','Memory outlives its cells','Replace all 24 cells one by one: the state survives in 4/4 runs.'],['quorum','Memory needs a quorum','Lifetime grows exponentially with group size; one isolated cell forgets in ~10 tu.'],['duration','There is a minimum reprogramming duration','No pulse shorter than ≈ 3.8 tu flips the collective, however strong.'],['coupling','Push where coupling is strongest','Place explains 54 % of the dose spread; well-connected centres need the least.'],['rigid','Self-sensing makes collectives rigid','A cell that reads its own signal never switched (0 of 560 trials).']];
    const cw=212,gap=16,x0=(1180-5*cw-4*gap)/2;
    g.fillStyle=C.ink;g.font='700 17px '+FONT;g.textAlign='left';g.fillText('Five predictions',x0,22);
    cards.forEach((cd,i)=>{const x=x0+i*(cw+gap),y=36;g.fillStyle='#FAFAF7';g.strokeStyle='#C9C9C0';g.lineWidth=1.5;g.beginPath();g.roundRect(x,y,cw,215,10);g.fill();g.stroke();cardIcon(g,cd[0],x+cw/2,y+46);
      g.fillStyle=C.ink;g.font='700 15px '+FONT;g.textAlign='center';g.textBaseline='top';wrapText(g,cd[1],cw-24).forEach((l,j)=>g.fillText(l,x+cw/2,y+90+j*19));
      g.font='13.5px '+FONT;g.fillStyle='#333';wrapText(g,cd[2],cw-26).forEach((l,j)=>g.fillText(l,x+cw/2,y+138+j*18));});
    g.textAlign='left';g.fillStyle=C.ink;g.font='700 17px '+FONT;g.fillText('What is next',x0,278);
    const nx=[['1','Memory → shape coupling','let the collective state feed back on structure'],['2','Harder hidden variants','for adaptive control (history, drifting thresholds)'],['3','Control from images','O3 cell-resolving images instead of tracked cells'],['4','Blanket / interface measures','the same three boundaries across all three systems']];
    nx.forEach((n,i)=>{const x=x0+i*(1180-2*x0)/4,y=302,w=(1180-2*x0)/4-14;g.fillStyle='#fff';g.strokeStyle='#C9C9C0';g.lineWidth=1.5;g.beginPath();g.roundRect(x,y,w,150,10);g.fill();g.stroke();g.fillStyle=C.ink;g.beginPath();g.arc(x+22,y+24,13,0,6.3);g.fill();g.fillStyle='#fff';g.font='700 14px '+FONT;g.textAlign='center';g.textBaseline='middle';g.fillText(n[0],x+22,y+24);
      g.fillStyle=C.ink;g.textAlign='left';g.textBaseline='top';g.font='700 15px '+FONT;wrapText(g,n[1],w-30).forEach((l,j)=>g.fillText(l,x+16,y+48+j*19));g.font='13.5px '+FONT;g.fillStyle='#333';wrapText(g,n[2],w-30).forEach((l,j)=>g.fillText(l,x+16,y+92+j*18));});
    g.fillStyle=C.mute;g.font='13px '+FONT;g.textAlign='left';g.fillText('These are predictions of the model, to be tested — not findings about real tissue.',x0,480);
  }
});

/* Act 5 - What it means (5.1, 5.2) */
'use strict';
Demo.register({id:'5.1',act:5,title:COPY['5.1'].title,data:['data/c51flock.js','data/oracle8.js','data/c43.js'],duration:0,
  legend:[{color:'#222',label:'bird flock: the followed group'},{color:'#BBBBBB',label:'bird flock: other birds'}].concat(LEG.types,LEG.state),
  caption:COPY['5.1'].caption,takeaway:COPY['5.1'].takeaway,
  notes:'Flock column: TRANSLATING_FLOCK_FINAL_SYNTHESIS (§1 identity tracker with 0 erroneous cross-population transfers in 72 traces; §2 pooled forcing ≈ 0 but heterogeneous, some seeds respond; §3 actuator choice never beats random on held-out; §8 no successful control demonstrated). “Does the change last?” is NOT TESTED for the flock: the synthesis records late-release alignment but gives no persistence verdict, so the cell reads “not tested” (see COPY_CHANGES.md). Published-model column: VANILLA_CLOSURE (§b4 shape returns after withdrawal in 300/300 runs; §b6 6 of 246 directions switch the shape, always into the defective class; §b/§g one body, no held-out test of where; §c no defect-free durable shape change). Our organism: EVALUATION + AUDIT_T5 (true success 57/60 = 95 %; controller − random +0.87; 0 identity events in 428 episodes). The flock clip is the Stage 6.9 translation pilot of the specified model; the 8-cell clip is the Octave oracle; the right clip is the controller on seed 6007.',
  audit:'AUDIT_T5 A1/A9 for the right-hand column.',
  sources:[{what:'Flock identity, efficacy, selectivity, conclusion',file:'stage6_flock/TRANSLATING_FLOCK_FINAL_SYNTHESIS.md',sec:'§1, §2, §3, §8'},{what:'Published model',file:'morphogenesis/VANILLA_CLOSURE.md',sec:'§b, §c, §g'},{what:'Our organism',file:'t5_blind_control/EVALUATION.md; testbed_v3/audit_t5/AUDIT_T5.md',sec:'A1, A9'},{what:'Flock clip (seed 37)',file:'stage6_flock/interactive_demo/data/stage6_9_bundle.json',sec:'spec.frames'}],
  setup(c){
    const K=COPY['5.1'];const tbl=el('div',{style:'display:grid;grid-template-columns:200px repeat(3,minmax(230px,1fr));gap:8px 10px;width:100%;max-width:1220px;margin:0 auto'},c.vis);c.state.panels=[];
    el('div',{},tbl,'');K.columns.forEach(h=>el('div',{style:'font-weight:700;font-size:16px;text-align:center'},tbl,h));
    el('div',{},tbl,'');
    for(let i=0;i<3;i++){const cell=el('div',{style:'display:flex;flex-direction:column;align-items:center'},tbl);const p=new Panel(cell,{size:200,fov:i===0?12:i===1?3.4:5.8,title:''});p.wrap=cell;p.tEl.remove();p.noBubble=true;c.panels.push(p);c.state.panels.push(p);}
    const kind=v=>v==='yes'?'ok':(v.startsWith('no')||v==='only while poked')?'bad':'neu';
    K.rows.forEach(r=>{el('div',{style:'font-weight:700;font-size:14.5px;align-self:center'},tbl,r[0]);for(let j=1;j<4;j++){let v=r[j];if(r[0]==='Does the change last?'&&j===1)v='not tested';el('div',{style:'border:1px solid #D9D9D2;border-radius:6px;padding:7px 9px;background:#fff;font-size:14.5px;font-weight:600;color:'+(v==='yes'?'#1b6b3a':v==='not tested'||v.startsWith('not tested')||v.startsWith('sometimes')?'#444':'#9b1c1c')+'"'.replace('"','')},tbl,v);}});
    const F=DATA.c51flock,O=DATA.oracle8,P=DATA.c43,A=P.arms.ctrl;const xf=B64.i16(F.X,1000),xo=B64.i16(O.X,1000),xc=B64.i16(A.X,1000),rc=B64.i16(A.rho,20000);const mem=F.members.map(m=>new Set(m));
    const t0=performance.now();Demo.tickers.push((ts)=>{const f=(ts-t0)/1000;
      const k=Math.max(0,Math.floor(f*6))%(F.T+4),kk=Math.min(k,F.T-1),p0=c.state.panels[0];p0.clear();
      for(let i=0;i<F.N;i++){const x=xf[(kk*F.N+i)*2],y=xf[(kk*F.N+i)*2+1];const m=mem[kk].has(i);const q=p0.w2p(x,y);const g=p0.ctx;g.fillStyle=m?'#222':'#BBBBBB';g.beginPath();g.arc(q[0],q[1],m?2.6:2,0,6.3);g.fill();}
      const b=Math.max(0,Math.floor(f*5))%(O.T+8),bb=Math.min(b,O.T-1),p1=c.state.panels[1];p1.clear();for(let i=0;i<8;i++)p1.node({x:xo[(bb*8+i)*2],y:xo[(bb*8+i)*2+1],fill:TYPEC[O.types[i]],r:0.28});
      const T=A.T,s=Math.max(0,Math.floor(f*14))%(T+30),ss=Math.min(s,T-1),p2=c.state.panels[2];p2.clear();A.acts.forEach(ac=>drawLight(p2,ac.xy,ac.r,lightWindow(ss,ac.t,ac.t+ac.dur,ac.ramp)));
      for(let i=0;i<24;i++)p2.node({x:xc[(ss*24+i)*2],y:xc[(ss*24+i)*2+1],fill:rhoColor(rc[ss*24+i]),r:0.4});});
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
Demo.register({id:'5.2',act:5,title:COPY['5.2'].title,data:[],duration:0,legend:[],
  caption:COPY['5.2'].caption,takeaway:COPY['5.2'].takeaway,
  notes:'Each card cites its result. (1) serial replacement: all 24 original cells replaced, state intact in 4/4 runs; (2) group lifetime grows as exp(0.31 N) at sigma_h = 0.7; (3) no threshold below l*/g ≈ 3.8 tu; T5: 2 tu never, 5 tu needs 3–4x the dose; (4) location explains 54 % of the variance of log dose; threshold amplitude falls with kernel connectivity of the lit disc (Spearman −0.98); (5) the earlier model (a cell reads its own signal) never switched: 0/93 scans, 0/560 trials. These are predictions of this model, not findings about real tissue.',
  sources:[{what:'Memory outlives cells (serial replacement 4/4)',file:'testbed_v3/IDENTITY_EVENTS_V3.md',sec:'Serial replacement'},{what:'Quorum',file:'testbed_v3/MEMORY_V3.md',sec:'(d)'},{what:'Minimum duration',file:'testbed_v3/SWITCH_V3.md; T5 SYSID B2'},{what:'Location / connectivity',file:'t5_blind_control/EVALUATION.md; testbed_v3/SWITCH_V3.md; AUDIT_T5 A4'},{what:'Self-reading memory never switched',file:'testbed_v2/SWITCH.md',sec:'Gate G3'}],
  setup(c){const w=el('div',{class:'pw'},c.vis);c.cv=makeCanvas(w,1180,560);c.cv.dataset.avoid='1';},
  draw(c){
    const cv=c.cv,g=cv.getContext('2d'),d=Math.min(window.devicePixelRatio||1,2);cv.width=1180*d;cv.height=560*d;cv.style.width='1180px';cv.style.height='560px';g.setTransform(d,0,0,d,0,0);g.fillStyle='#fff';g.fillRect(0,0,1180,560);
    const kinds=['outlive','quorum','duration','coupling','rigid'];const cw=222,gap=14,x0=(1180-5*cw-4*gap)/2;
    COPY['5.2'].cards.forEach((txt,i)=>{const x=x0+i*(cw+gap),y=14;g.fillStyle='#FAFAF7';g.strokeStyle='#C9C9C0';g.lineWidth=1.5;g.beginPath();g.roundRect(x,y,cw,300,10);g.fill();g.stroke();cardIcon(g,kinds[i],x+cw/2,y+44);
      const dot=txt.indexOf('. ');const head=txt.slice(0,dot+1),rest=txt.slice(dot+2);g.fillStyle=C.ink;g.font='700 15.5px '+FONT;g.textAlign='left';g.textBaseline='top';let yy=y+92;wrapText(g,head,cw-28).forEach(l=>{g.fillText(l,x+14,yy);yy+=20;});
      g.font='14px '+FONT;g.fillStyle='#333';yy+=6;wrapText(g,rest,cw-28).forEach(l=>{g.fillText(l,x+14,yy);yy+=19;});});
    g.fillStyle=C.ink;g.font='700 17px '+FONT;g.textAlign='left';g.textBaseline='top';g.fillText('Next steps',x0,334);
    COPY['5.2'].next.forEach((n,i)=>{const w=(1180-2*x0-3*gap)/4,x=x0+i*(w+gap),y=364;g.fillStyle='#fff';g.strokeStyle='#C9C9C0';g.lineWidth=1.5;g.beginPath();g.roundRect(x,y,w,130,10);g.fill();g.stroke();g.fillStyle=C.ink;g.beginPath();g.arc(x+22,y+24,13,0,6.3);g.fill();g.fillStyle='#fff';g.font='700 14px '+FONT;g.textAlign='center';g.textBaseline='middle';g.fillText(String(i+1),x+22,y+24);
      g.fillStyle=C.ink;g.textAlign='left';g.textBaseline='top';g.font='15px '+FONT;wrapText(g,n,w-28).forEach((l,j)=>g.fillText(l,x+14,y+50+j*20));});
  }
});

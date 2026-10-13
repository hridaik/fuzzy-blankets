/* Act 3 - Is it still the same organism? (3.1 - 3.4) */
'use strict';
function pageAnchor(canvas,x,y){const sw=document.getElementById('stagewrap').getBoundingClientRect(),r=canvas.getBoundingClientRect();return [r.left-sw.left+x*(r.width/(canvas.clientWidth||r.width)),r.top-sw.top+y];}
/* ---------------- 3.1 (rebuilt) ---------------- */
Demo.register({id:'3.1',act:3,title:COPY['3.1'].title,data:['data/c31.js'],duration:120,rate:9,truthOffered:false,
  legend:[{color:'#777',label:'cell or dot'},{cls:'solid',color:'#222',label:'outline (drawn by the blind analysis)'}],
  caption:COPY['3.1'].caption,takeaway:COPY['3.1'].takeaway,
  notes:'One package-v3 run with an x-cut at t = 50 (run_00283), seen at four levels. Outlines are the groupings produced by the blind pipelines’ own code: O1/O2 = T4 pipeline (single linkage r_link 1.6 with hysteresis, at least 3 cells, forward organism tracker; O2 ids from T4’s cell tracker); O3a = T4 O3 front end (foreground of the smoothed c6 field, components, same tracker; organism = foreground pixels); O3c = T5’s spot detection (gaussian smoothing + local maxima, a_track.o3c_eval) followed by the same linking rule (position-only cell tracker). The run was chosen because it shows the blurry image failing to split; in the 6 x-cut runs of this kind the glow image splits at once in 4 (run_00263, 00303, 00328, 00369) and has trouble in 2 (run_00283, 00344). The stepper replays the O1 rule on the current frame (points, links closer than 1.6, groups, alpha-hull outline, head-to-tail axis from the c6 gradient slope). The outline is a grouping we choose; the Markov blanket and the interface are different objects (see 4.3).',
  sources:[{what:'Run with a cut, four levels, per-view grouping',file:'testbed_blind_v3/runs/run_00283_{O1,O2,O3a,O3c}.npz',sec:'catalog.csv'},{what:'Grouping code',file:'t4_blind_identity/t4/{pipeline,orgtrack,o3}.py; t5_blind_control/code/a_track.py (o3c_eval)'},{what:'Build script',file:'demo_v1/build/build_c31.py'}],
  setup(c){
    const D=DATA.c31;c.state.D=D;c.state.step=0;const sz=Demo.arenaSize(4,0);const f=11,T=COPY['2.3'].panels;
    c.p=[0,1,2,3].map(i=>c.panel({size:sz,fov:f,title:T[i]}));
    c.state.X1=D.O1.xy.map(s=>B64.i16(s,1000));c.state.X2=D.O2.xy.map(s=>B64.i16(s,1000));c.state.C6=D.O1.c6.map(s=>B64.i16(s,1000));c.state.Ma=D.O3a.lab.map(s=>B64.u8(s));c.state.Xc=D.O3c.xy.map(s=>B64.i16(s,1000));c.state.ia={};c.state.ic={};
    const b=el('button',{class:'btn'},c.ctrls,COPY['3.1'].button);const seg=el('div',{class:'seg',id:'steps31',style:'display:none'},c.ctrls);
    COPY['3.1'].steps.forEach((nm,i)=>{const bb=el('button',{},seg,(i+1)+' '+nm);bb.onclick=()=>{c.state.step=i+1;seg.querySelectorAll('button').forEach((x,j)=>x.classList.toggle('on',j===i));Demo.redraw();};});
    b.onclick=()=>{const on=c.state.step===0;c.state.step=on?1:0;b.classList.toggle('on',on);seg.style.display=on?'inline-flex':'none';seg.querySelectorAll('button').forEach((x,j)=>x.classList.toggle('on',on&&j===0));Demo.redraw();};},
  draw(c,t){
    const D=c.state.D,k=Math.max(0,Math.min(D.ts.length-1,Math.round(t))),T=D.ts[k],P=c.p,st=c.state.step;
    const crop=(p,cv,half,px)=>{p.clear('#000');const g=p.ctx;const s0=(half-p.fov)/(2*half)*px,sw=2*p.fov/(2*half)*px;g.save();g.imageSmoothingEnabled=true;g.drawImage(cv,s0,s0,sw,sw,0,0,p.w,p.h);g.restore();p.scaleBar();};
    // 1 tracked cells
    const p1=P[0],xy=c.state.X1[k],n=xy.length/2;p1.clear();p1.scaleBar();const lab=D.O1.lab[k],pts=[];for(let i=0;i<n;i++)pts.push([xy[2*i],xy[2*i+1]]);
    if(st>=2){const r=1.6;for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)if(dist(pts[i],pts[j])<r)p1.line(pts[i],pts[j],{color:'#444',w:1.6});}
    for(let i=0;i<n;i++){const mem=lab[i]>=0;p1.node({x:pts[i][0],y:pts[i][1],fill:st>=3&&!mem?'#CCC':'#777',r:0.38,label:String(D.O1.id[k][i]),stroke:st>=3&&mem?C.ink:'rgba(0,0,0,.35)',lw:st>=3&&mem?2:1});}
    if(st===0||st>=4)groupOutlinePts(p1,xy,lab);
    if(st===3){const g={};for(let i=0;i<n;i++)if(lab[i]>=0)(g[lab[i]]=g[lab[i]]||[]).push(pts[i]);Object.keys(g).forEach(q=>{const sub=g[q],cx=sub.reduce((a,b)=>a+b[0],0)/sub.length,top=Math.max(...sub.map(b=>b[1]));p1.label('group '+(+q+1)+': '+sub.length+' cells',cx,top+1.15,{align:'center',size:13,bold:true,world:true,bg:true});});}
    if(st>=5){D.O1.org[k].forEach(o=>{const cen=[o[2],o[3]],e1=[o[4],o[5]];p1.arrow(cen,[cen[0]+3*e1[0],cen[1]+3*e1[1]],{color:C.ink,w:3,head:12});p1.label('head → tail',cen[0]+3.2*e1[0],cen[1]+3.2*e1[1],{world:true,size:13,bold:true,bg:true,align:e1[0]<0?'right':'left'});});}
    if(st===0)drawnTag(p1);
    // 2 dots
    const p2=P[1],x2=c.state.X2[k];p2.clear();p2.scaleBar();for(let i=0;i<x2.length/2;i++)p2.node({x:x2[2*i],y:x2[2*i+1],fill:'#777',r:0.4});groupOutlinePts(p2,x2,D.O2.lab[k]);drawnTag(p2);
    // 3 glow image
    const p3=P[2];if(!c.state.ia[k])c.state.ia[k]=imgCanvas(D.O3a.img[k],64,64,3,true);crop(p3,c.state.ia[k],D.fov,64);groupOutlineMask(p3,c.state.Ma[k],64,D.fov,{col:'#fff'});drawnTag(p3);
    // 4 cell markers
    const p4=P[3];if(!c.state.ic[k])c.state.ic[k]=imgCanvas(D.O3c.img[k],128,128,1,true);crop(p4,c.state.ic[k],D.fovc,128);const sp=c.state.Xc[k];groupOutlinePts(p4,sp,D.O3c.lab[k],{col:'#fff'});drawnTag(p4);
    p1.setSub('time '+T);
  },
  pauses:[{t:10,text:COPY['3.1'].callouts[0],side:'top',anchor:c=>({panel:c.p[0],x:0,y:-3.6})},
          {t:32,text:COPY['3.1'].callouts[1],side:'top',anchor:c=>({panel:c.p[2],x:0,y:-1})},
          {t:120,text:COPY['3.1'].callouts[2],side:'top',anchor:c=>({panel:c.p[0],x:0,y:0})}]
});

const L32=[{cls:'solid',color:'#777',label:'which cells'},{cls:'solid',color:'#222',label:'shape'},{cls:'dash',label:'pattern'},{cls:'band',label:'normal range (grey band)'},{color:C.sa,label:'blue state'},{color:C.sb,label:'pink state'}];
/* ---------------- 3.2 ---------------- */
function stackCharts(parent,w,h,n){const arr=[];for(let i=0;i<n;i++){const cv=makeCanvas(parent,w,h);cv.style.display='block';cv.style.marginBottom='4px';arr.push(cv);}return arr;}
Demo.register({id:'3.2',act:3,title:COPY['3.2'].title,data:['data/c32.js'],duration:150,rate:12,truthOffered:false,
  legend:L32,
  caption:COPY['3.2'].caption,takeaway:COPY['3.2'].takeaway,
  notes:'Frozen T5 monitor on three exemplars. material = 1 − Jaccard of the id set to the first frame (a cut loses no ids, so this stays flat while the shape trace breaks); geometry = worst of cohesion bridge ≤ 1.40, shape change ≤ 4.9 % / 6.6 %, 24 cells in one linked component; pattern = largest standardized deviation of 14 state-independent channel features, bound 4.83; state = two-state Gaussian posterior (S+ = blue state, S− = pink state). V_body (same-body check) is cumulative. NOTE: the supplied cut callout says “Cells leave”; in the data the cut moves 12 cells away at once without losing any, so the which-cells trace stays flat (AUDIT_T5 A2). Exemplars: undisturbed/cut = runs 00266/00263 (body 2700); light switch = T5 held-out seed 6007 controller (O1 frames regenerated; monitor reproduces the logged verdicts in 164/164 frames).',
  audit:'AUDIT_T5 A2.',
  sources:[{what:'Monitor traces on three exemplars',file:'demo_v1/data/c32.js',sec:'build/build_ch3.py'},{what:'Monitor implementation',file:'t5_blind_control/code/t5mon/monitor.py',sec:'lines 19–63'},{what:'Bounds',file:'t5_blind_control/MONITOR_CONFIG.json'},{what:'Runs',file:'testbed_blind_v3/runs/run_00263, run_00266; t5_blind_control/episodes_heldout/ep_00988.json'}],
  setup(c){
    const D=DATA.c32;c.state.D=D;c.state.ex='undisturbed';const sz=Math.min(Demo.arenaSize(2,0),520);
    const sel=el('div',{class:'seg',id:'ex32'},c.ctrls);const names={undisturbed:COPY['3.2'].buttons[0],cut:COPY['3.2'].buttons[1],light:COPY['3.2'].buttons[2]};
    c.pa=c.panel({size:sz,fov:11,title:'Dish'});c.pa.noBubble=false;
    const w=document.createElement('div');w.className='pw';c.vis.appendChild(w);c.state.badges=el('div',{style:'min-height:26px'},w,'');
    c.chH=Math.floor((sz-30)/4)-4;c.cvs=stackCharts(w,590,c.chH,4);
    ['undisturbed','cut','light'].forEach((k,i)=>{const b=el('button',{},sel,names[k]);b.onclick=()=>{this.pick(c,k);};if(i===0)b.classList.add('on');});
    ['undisturbed','cut','light'].forEach(k=>{const e=D[k];e.XY=e.xy.map(s=>B64.i16(s,1000));});
    c.state.pick=(k)=>this.pick(c,k);this.pick(c,'undisturbed',true);},
  variants:[{name:'undisturbed',apply(c){c.state.pick('undisturbed');}},{name:'cut',apply(c){c.state.pick('cut');}},{name:'light',apply(c){c.state.pick('light');}}],
  pick(c,k,first){
    const D=c.state.D,e=D[k];c.state.ex=k;document.querySelectorAll('#ex32 button').forEach((b,i)=>b.classList.toggle('on',['undisturbed','cut','light'][i]===k));
    const tr=e.tr,t=tr.t;const def=Demo.byId['3.2'];def.duration=t[t.length-1];def.rate=def.duration/14;
    const firstV=(()=>{const i=tr.V.findIndex(v=>!v);return i<0?null:t[i];})();const sw=(()=>{for(let i=0;i<t.length;i++){if(tr.state.slice(i).every(s=>s==='S-'))return t[i];}return null;})();
    const here=(ci,x,y)=>({px:pageAnchor(c.cvs[ci],c.cvs[ci].clientWidth*x,y)});
    const K=COPY['3.2'].callouts;const pl={undisturbed:[{t:110,text:K.Untouched,anchor:()=>here(1,0.7,40)}],
      cut:[{t:(firstV||51),text:K.Cut,anchor:()=>here(1,0.34,30)}],
      light:[{t:(sw||94)+6,text:K['Light switch'],anchor:()=>here(3,0.6,40)}]}[k];
    def.pauses=pl;Demo.buildTicks();Demo.t=Math.min(Demo.t,def.duration);Demo.hideCallout();Demo.playing=false;Demo.seek(0);
    Demo.setLegend(L32);
    document.getElementById('caption').innerHTML=def.caption;},
  draw(c,tcur){
    const D=c.state.D,k=c.state.ex,e=D[k],tr=e.tr,t=tr.t;let i=0;while(i+1<t.length&&t[i+1]<=tcur+1e-9)i++;const p=c.pa;
    const xy=e.XY[i],n=xy.length/2;let cx=0,cy=0;for(let j=0;j<n;j++){cx+=xy[2*j];cy+=xy[2*j+1];}p.cx=cx/n;p.cy=cy/n;p.clear();p.scaleBar();
    if(k==='light'){e.acts.forEach(a=>{const ph=lightWindow(tr.t[i],a.t,a.t+a.dur,a.ramp);drawLight(p,a.xy,a.r,ph);});}
    for(let j=0;j<n;j++)p.node({x:xy[2*j],y:xy[2*j+1],fill:'#777',r:0.38});
    if(k==='cut'&&tcur>=50)p.label('cut',p.w/2,18,{align:'center',size:13,bold:true,color:'#222'});
    if(k==='light')p.label('light at the middle of the body',p.w/2,18,{align:'center',size:12.5,color:C.mute});
    p.setTitle({undisturbed:'Untouched organism',cut:'After a cut',light:'Light switch'}[k]);p.setSub('time '+tr.t[i].toFixed(0));
    const B=D.bounds;const mk=(cv,title,ys,o)=>{const ch=new Chart(cv,{w:590,h:c.chH,xlim:[0,t[t.length-1]],ylim:o.ylim,yticks:o.yticks,m:{l:44,r:10,t:18,b:o.last?22:6},title:title,xlabel:o.last?'time units':null,yfmt:o.yfmt});ch.clear();if(o.band)ch.hband(o.band[0],o.band[1],C.band);ch.axes();
      if(o.hl!=null)ch.hline(o.hl,{color:'#999',dash:[4,3],label:o.hlab});if(k==='cut')ch.vline(50,{color:'#C0392B',dash:[3,3]});if(k==='light'){ch.vline(20,{color:'#999',dash:[3,3]});}
      const xs=t.slice(0,i+1),yy=ys.slice(0,i+1).map(v=>Math.min(v,o.ylim[1]));if(o.state)ch.segColor(xs,yy,(j)=>yy[j]>0.5?C.sa:C.sb,3.2);else ch.line(xs,yy,{color:o.color,w:2.2,dash:o.dash});
      ch.vline(tr.t[i],{color:'#222',w:1});return ch;};
    mk(c.cvs[0],'Which cells',tr.material,{ylim:[0,1.05],yticks:[0,0.5,1],band:[0,0.02],color:'#777',hl:0.02,hlab:''});
    mk(c.cvs[1],'Shape',tr.geometry,{ylim:[0,3],yticks:[0,1,2,3],band:[0,1],color:'#222'});
    mk(c.cvs[2],'Pattern of signals',tr.pattern,{ylim:[0,3],yticks:[0,1,2,3],band:[0,1],color:'#222',dash:[6,4]});
    mk(c.cvs[3],'Group state (blue above, pink below)',tr.p_plus,{ylim:[0,1.02],yticks:[0,0.5,1],state:true,last:true,hl:0.5});
    const V=tr.V[i],st=tr.state[i];c.state.badges.innerHTML=badge('same-body check '+(V?'passes':'fails'),V?'ok':'bad')+badge('which cells '+(tr.mat_ok[i]?'inside range':'outside'),tr.mat_ok[i]?'ok':'bad')+badge('shape '+(tr.geo_ok[i]?'inside range':'outside'),tr.geo_ok[i]?'ok':'bad')+badge('group state: '+(st==='S+'?'blue':st==='S-'?'pink':'changing'),'neu');
  }
});

/* ---------------- 3.3 ---------------- */
Demo.register({id:'3.3',act:3,title:COPY['3.3'].title,data:['data/c33.js'],duration:2800,rate:100,truthOffered:false,legend:LEG.rho.concat([{color:'#fff',label:'newcomer: bright halo for 3 time units'},{cls:'solid',color:'#222',label:'thick outline = original cell'}]),
  caption:COPY['3.3'].caption,takeaway:COPY['3.3'].takeaway,
  notes:'Protocol of IDENTITY_EVENTS_V3 (job_serial, seed 0), regenerated deterministically at 1 tu resolution (noise-free). Newcomers start undecided (rho = 1/2, no secretion) and read only their neighbours’ ligand fraction, so they inherit the state at once. The shape is not repaired by the structure module (G1 repairs a single swap 17/24 times, not serial replacement: 0/4 complete): a structure result, not a memory result. Playback slows near the first three swaps.',
  sources:[{what:'Serial replacement, seed 0: 24 swaps x 100 tu + 400 tu settle',file:'testbed_v3/IDENTITY_EVENTS_V3.md',sec:'Serial replacement'},{what:'Regenerated frames',file:'demo_v1/data/c33.js',sec:'build/build_ch3.py'}],
  setup(c){
    const D=DATA.c33;c.state.X=B64.i16(D.X,1000);c.state.R=B64.i16(D.rho,20000);c.state.I=B64.i16(D.ids,1);c.state.D=D;const sz=Math.min(Demo.arenaSize(2,0),560);
    const lc=el('div',{class:'pw'},c.vis);c.strip=makeCanvas(lc,sz,52);c.pa=new Panel(lc,{size:sz,fov:9,title:''});c.pa.wrap=lc;c.panels.push(c.pa);const w=document.createElement('div');w.className='pw';c.vis.appendChild(w);el('div',{class:'ptitle'},w,'');c.cvH=sz;c.cv=makeCanvas(w,560,sz);
    c.state.type=(i)=>D.tmplType[D.perm0[i]];D.speedAt=(t)=>{for(const r of D.reps.slice(0,3)){if(t>=r[0]-1&&t<=r[0]+5)return 0.04;}return 1;};},
  speedAt(c,t){return c.state.D.speedAt(t);},
  draw(c,t){
    const D=c.state.D,k=Math.min(Math.round(t),D.T-1),N=24,p=c.pa;const qx=[],qy=[];for(let i=0;i<N;i++){qx.push(c.state.X[(k*N+i)*2]);qy.push(c.state.X[(k*N+i)*2+1]);}const med=v=>v.slice().sort((a,b)=>a-b)[N>>1];p.cx=med(qx);p.cy=med(qy);{const ds=qx.map((x,i)=>Math.hypot(x-p.cx,qy[i]-p.cy)).sort((a,b)=>a-b);p.fov=Math.max(9,Math.min(30,ds[Math.floor(N*0.8)]+2));p.scale=Math.min(p.w,p.h)/(2*p.fov);}
    p.clear();p.scaleBar();let flash=-1;D.reps.forEach(r=>{if(t>=r[0]&&t<r[0]+3)flash=r[1];});
    for(let i=0;i<N;i++){const id=c.state.I[k*N+i],orig=id<24,fl=(i===flash);p.node({x:c.state.X[(k*N+i)*2],y:c.state.X[(k*N+i)*2+1],fill:rhoColor(c.state.R[k*N+i]),r:0.4,stroke:orig?C.ink:'rgba(0,0,0,.4)',lw:orig?2.4:1,hl:fl});}
    if(flash>=0){const q=p.w2p(c.state.X[(k*N+flash)*2],c.state.X[(k*N+flash)*2+1]);p.ctx.save();p.ctx.strokeStyle='#fff';p.ctx.lineWidth=5;p.ctx.beginPath();p.ctx.arc(q[0],q[1],0.4*p.scale+10,0,6.3);p.ctx.stroke();p.ctx.strokeStyle=C.ink;p.ctx.lineWidth=1.5;p.ctx.stroke();p.ctx.restore();}
    p.label(COPY['3.3'].counter+': '+D.orig[k]+' / 24',p.w/2,20,{align:'center',size:16,bold:true});p.setSub('time '+t.toFixed(0));
    {const sc=c.strip,g=sc.getContext('2d'),W=sc.width,H=sc.height;g.setTransform(1,0,0,1,0,0);g.fillStyle='#fff';g.fillRect(0,0,W,H);const X=u=>10+u/D.T*(W-20);g.strokeStyle='#999';g.lineWidth=1;g.beginPath();g.moveTo(X(0),30);g.lineTo(X(D.T),30);g.stroke();g.font='11px '+FONT;g.fillStyle=C.mute;g.textAlign='center';g.textBaseline='top';for(let u=0;u<=D.T;u+=100){g.beginPath();g.moveTo(X(u),30);g.lineTo(X(u),36);g.stroke();if(u%500===0)g.fillText(String(u),X(u),38);}
      D.reps.forEach(r=>{g.fillStyle=r[0]<=t?C.ink:'#bbb';g.beginPath();g.arc(X(r[0]),30,4.5,0,6.3);g.fill();});g.strokeStyle=C.ink;g.lineWidth=2;g.beginPath();g.moveTo(X(t),20);g.lineTo(X(t),40);g.stroke();g.fillStyle=C.ink;g.font='700 13px '+FONT;g.textAlign='left';g.textBaseline='top';g.fillText(COPY['3.3'].counter+': '+D.orig[k]+' / 24',10,2);g.font='11px '+FONT;g.fillStyle=C.mute;g.textAlign='right';g.fillText('time units',W-10,2);}
    const g=c.cv,ch=new Chart(g,{w:560,h:c.cvH,xlim:[0,D.T],ylim:[0,1.08],yticks:[0,0.5,1],m:{l:46,r:12,t:24,b:28},xlabel:'time units'});ch.clear();ch.axes();
    const xs=[],mat=[],rho=[],geo=[];for(let j=0;j<=k;j+=5){xs.push(j);mat.push(D.orig[j]/24);rho.push(D.rho_mean[j]);geo.push(D.geo[j]<=1?1:0);}
    ch.line(xs,mat,{color:'#777',w:3});ch.line(xs,rho,{color:C.sa,w:3});ch.line(xs,geo,{color:'#222',w:2.2,dash:[6,4]});ch.vline(t,{color:'#222',w:1});
    ch.text('which cells: share of original cells',ch.X(1900),ch.Y(0.06),{align:'right',color:'#555',bold:true});ch.text('group state: blue share',ch.X(2790),ch.Y(0.82),{align:'right',color:'#1f7fb5',bold:true});ch.text('shape inside normal range (1 = yes)',ch.X(2790),ch.Y(1.04),{align:'right',color:'#222',size:12});},
  pauses:[{t:3,text:COPY['3.3'].callouts[0],side:'left',anchor:c=>{const D=c.state.D,i=D.reps[0][1],k=3;return {panel:c.pa,x:c.state.X[(k*24+i)*2]-c.pa.cx,y:c.state.X[(k*24+i)*2+1]-c.pa.cy};}},
          {t:2301,text:COPY['3.3'].callouts[1],side:'left',anchor:c=>({panel:c.pa,x:0,y:-3.9})},
          {t:2800,text:COPY['3.3'].callouts[2],side:'left',anchor:c=>({panel:c.pa,x:0,y:3.9})}]
});

/* ---------------- 3.4 ---------------- */
Demo.register({id:'3.4',act:3,title:COPY['3.4'].title,data:['data/c34.js','data/body2100.js'],duration:3,rate:0.3,unit:'step',truthOffered:true,
  legend:[{color:'#777',label:'● first group'},{color:'#222',label:'▲ second group'},{color:'#fff',label:'■ small third group'},{cls:'solid',color:'#888',label:'× outside the usual range'}],
  caption:COPY['3.4'].caption,takeaway:COPY['3.4'].takeaway,
  notes:'T4 labelled the two big clusters 0 and 2 and a small third cluster 1 (4 % of dishes). Truth: label 0 = state b (978/978 frames), label 2 = state a (972/972); the rare label 1 holds both states (a 43, b 47) — a body-specific structural variant, not a third collective state (AUDIT_T4 A4). T4 called the two states “mirror images”; the audit corrected this: the same body, only the reporter row and ligand levels differ (inset). Axes: reporter left–right dipole (c0) and memory-ligand difference (c4 − c5).',
  audit:'Corrects T4: “mirror-image organisations” → one chiral body, reporter row moved (AUDIT_T4 A4).',
  sources:[{what:'Descriptors c0_dq_sens and c4_mean − c5_mean, T4 label per frame (O1, 260 natural dishes x 8 frames)',file:'t4_blind_identity/outputs/run_*.json.gz',sec:'levels.O1.frames[].organisms[].desc, C3.label'},{what:'True state (hidden tier)',file:'testbed_v3/data/blind_v2_hidden/run_*.json',sec:'meta.state'},{what:'Agreement 99–100 %; mirror image corrected',file:'testbed_v3/audit_t4/AUDIT_T4.md',sec:'A4'}],
  setup(c){
    const D=DATA.c34;c.state.D=D;const w=document.createElement('div');w.className='pw';c.vis.appendChild(w);el('div',{class:'ptitle'},w,'');c.sc=makeCanvas(w,640,560);
    const w2=document.createElement('div');w2.className='pw';c.vis.appendChild(w2);
    c.inset=new Panel(w2,{size:340,fov:5.4,title:''});c.inset.wrap=w2;c.panels.push(c.inset);c.inset.noBubble=true;c.inset.setSub('Blue state (filled) and pink state (dashed ring), same body');
    const X=x=>56+(x+0.25)/0.5*(640-56-14),Y=y=>560-46-(y+1)/2*(560-26-46);
    Demo.byId['3.4'].pauses=[{t:0,text:COPY['3.4'].callouts[0],side:'right',anchor:cc=>({px:pageAnchor(cc.sc,X(0.15),Y(0.55))})},
      {t:1,text:COPY['3.4'].callouts[1],side:'right',anchor:cc=>({px:pageAnchor(cc.sc,X(-0.15),Y(-0.55))})},
      {t:2,text:COPY['3.4'].callouts[2],side:'left',anchor:cc=>({panel:cc.inset,x:0,y:1.8})}];Demo.buildTicks();},
  draw(c,t,truth){
    const D=c.state.D,ch=new Chart(c.sc,{w:640,h:560,xlim:[-0.25,0.25],ylim:[-1,1],m:{l:56,r:14,t:26,b:46},xticks:[-0.2,-0.1,0,0.1,0.2],yticks:[-1,-0.5,0,0.5,1],xfmt:v=>v.toFixed(1),yfmt:v=>v.toFixed(1)});ch.clear();ch.axes();
    const g=ch.c;g.save();g.font='13px '+FONT;g.fillStyle=C.ink;g.textAlign='center';g.fillText('yellow marker: left–right difference',ch.X(0),ch.h-8);g.translate(14,ch.Y(0));g.rotate(-Math.PI/2);g.fillText('blue signal minus pink signal',0,0);g.restore();
    for(let i=0;i<D.x.length;i++){const L=D.lab[i],px=ch.X(D.x[i]),py=ch.Y(D.y[i]);const col=truth?(D.truth[i]?C.sa:C.sb):(L===0?'#777':L===2?'#222':L===1?'#fff':'#999');g.save();g.fillStyle=col;g.strokeStyle=truth?'rgba(0,0,0,.45)':'#222';g.lineWidth=L===1?1.8:0.8;
      if(L===-1){g.strokeStyle=truth?col:'#999';g.lineWidth=1.6;g.beginPath();g.moveTo(px-3.5,py-3.5);g.lineTo(px+3.5,py+3.5);g.moveTo(px+3.5,py-3.5);g.lineTo(px-3.5,py+3.5);g.stroke();}
      else if(L===1){g.beginPath();g.rect(px-3.5,py-3.5,7,7);g.fill();g.stroke();}else if(L===2){g.beginPath();g.moveTo(px,py-4.5);g.lineTo(px+4.2,py+3.2);g.lineTo(px-4.2,py+3.2);g.closePath();g.fill();g.stroke();}else{g.beginPath();g.arc(px,py,3.4,0,6.3);g.fill();g.stroke();}g.restore();}
    Demo.setLegend(truth?[{color:C.sa,label:'true blue state'},{color:C.sb,label:'true pink state'},{cls:'solid',color:'#888',label:'marker shapes = the program\'s own groups'}]:[{color:'#777',label:'● first group'},{color:'#222',label:'▲ second group'},{color:'#fff',label:'■ small third group'},{cls:'solid',color:'#888',label:'× outside the usual range'}]);
    const p=c.inset;p.clear();p.scaleBar();const B=decodeBody();const na=bodyNodes(B,10,'a',{ring:true}),nb=bodyNodes(B,10,'b',{ring:true});
    na.forEach(n=>p.node({x:n.x,y:n.y,fill:TYPEC[n.type],ring:n.ring,r:0.38}));nb.forEach(n=>{const q=p.w2p(n.x,n.y),cc=p.ctx;cc.save();cc.strokeStyle=C.sb;cc.lineWidth=2.2;cc.setLineDash([4,3]);cc.beginPath();cc.arc(q[0],q[1],0.6*p.scale,0,6.3);cc.stroke();cc.restore();});
  }
});

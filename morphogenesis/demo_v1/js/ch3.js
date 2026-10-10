/* Act 3 - Identity (chapters 3.1 - 3.4) */
'use strict';
function pageAnchor(canvas,x,y){const sw=document.getElementById('stagewrap').getBoundingClientRect(),r=canvas.getBoundingClientRect();return [r.left-sw.left+x*(r.width/(canvas.clientWidth||r.width)),r.top-sw.top+y];}
/* ---------------- 3.1 ---------------- */
function bodyFrameOf(P,lev6){ // centroid, principal axis, sign from the gradient (c6) slope -> e1 = head -> tail, e2 = rot90(e1)
  const n=P.length;let cx=0,cy=0;P.forEach(p=>{cx+=p[0];cy+=p[1];});cx/=n;cy/=n;let sxx=0,sxy=0,syy=0;P.forEach(p=>{const x=p[0]-cx,y=p[1]-cy;sxx+=x*x;sxy+=x*y;syy+=y*y;});sxx/=n;sxy/=n;syy/=n;
  const th=0.5*Math.atan2(2*sxy,sxx-syy);let e1=[Math.cos(th),Math.sin(th)];let sl=0;P.forEach((p,i)=>{sl+=((p[0]-cx)*e1[0]+(p[1]-cy)*e1[1])*lev6[i];});if(sl<0)e1=[-e1[0],-e1[1]];return {c:[cx,cy],e1:e1,e2:[-e1[1],e1[0]]};}
function boundariesIcons(cv,w,h){
  const g=cv.getContext('2d'),d=Math.min(window.devicePixelRatio||1,2);cv.width=w*d;cv.height=h*d;cv.style.width=w+'px';cv.style.height=h+'px';g.setTransform(d,0,0,d,0,0);g.fillStyle='#fff';g.fillRect(0,0,w,h);g.textBaseline='top';
  const dots=(x,y)=>{g.fillStyle='#777';[[-12,-6],[0,-10],[12,-6],[-7,6],[7,6],[0,0]].forEach(a=>{g.beginPath();g.arc(x+a[0],y+a[1],4.5,0,6.3);g.fill();});};
  const row=(y,title,sub,fn)=>{fn(52,y+34);g.fillStyle=C.ink;g.font='700 15px '+FONT;g.textAlign='left';g.fillText(title,112,y+8);g.font='13.5px '+FONT;g.fillStyle='#444';sub.forEach((s,i)=>g.fillText(s,112,y+30+i*17));};
  g.fillStyle=C.ink;g.font='700 15px '+FONT;g.textAlign='left';g.fillText('Three different boundaries',10,8);
  row(36,'OUTLINE = who belongs',['geometric: which nodes are in the','collective (found here, in Act 3)'],(x,y)=>{dots(x,y);g.strokeStyle=C.ink;g.lineWidth=2.2;g.beginPath();g.ellipse(x,y-1,24,17,0,0,6.3);g.stroke();});
  row(136,'BLANKET = what shields',['statistical: which variables make the','inside independent of the outside'],(x,y)=>{g.strokeStyle=C.ink;g.lineWidth=2;g.fillStyle='#fff';g.beginPath();g.arc(x,y,9,0,6.3);g.stroke();g.setLineDash([3,3]);g.beginPath();g.arc(x,y,20,0,6.3);g.stroke();g.setLineDash([]);
    g.fillStyle=C.ink;[[-26,-26,-14,-14],[26,26,14,14]].forEach(a=>{g.beginPath();g.moveTo(x+a[0],y+a[1]);g.lineTo(x+a[2],y+a[3]);g.stroke();});g.font='11px '+FONT;g.fillText('s',x-34,y-34);g.fillText('a',x+28,y+22);});
  row(236,'INTERFACE = where a push couples in',['causal: where an intervention enters','(found in Act 4: the body centre)'],(x,y)=>{dots(x,y);g.save();g.fillStyle='rgba(255,230,120,.45)';g.strokeStyle=C.ink;g.setLineDash([4,3]);g.lineWidth=1.6;g.beginPath();g.arc(x+4,y,15,0,6.3);g.fill();g.stroke();g.restore();});
  g.fillStyle=C.mute;g.font='12.5px '+FONT;g.fillText('The three need not coincide.',10,h-22);
}
Demo.register({id:'3.1',act:3,title:'Finding the collective (the outline is not the blanket)',data:['data/c31.js'],duration:0,
  legend:[{color:'#777',label:'tracked cell (O1)'}],
  caption:'Step through how a collective is found from tracked cells: points → links between nodes closer than the link radius (default 1.6) → connected group = member set → outline (alpha hull) with an organism ID → body frame (head→tail axis from the gradient, second axis towards the limb side). Drag the link radius, or switch to a dish with two clusters.',
  takeaway:'The outline answers “which nodes belong” — it is not a Markov blanket.',
  notes:'T4 / T5 detection: single-linkage at r_link = 1.6 (hysteresis 1.3×) with at least 3 cells; alpha hull for the outline; body frame from the principal axis, sign from the slope of the gradient channel c6 (audit: this sign agrees with the true head→tail direction in 99–100 % of frames), e2 = rot90(e1). The three boundaries are different objects: the outline is geometric; a Markov blanket is statistical (sensory + active states); the interface (where an intervention couples in) is found in Act 4.',
  sources:[{what:'Dish O1 frames: package-v3 run_01105 (t = 36), merge dish run_00702 (t = 30; two bodies at offset (6, 0))',file:'testbed_blind_v3/runs/run_01105_O1.npz, run_00702_O1.npz'},{what:'Detection (r_link 1.6, m_min 3) and body frame',file:'t5_blind_control/code/t5mon/geom.py',sec:'components(), body_frame()'},{what:'Audit of body frame sign (99–100 %)',file:'testbed_v3/audit_t4/AUDIT_T4.md',sec:'A1'}],
  setup(c){
    const D=DATA.c31;c.state.D=D;c.state.step=1;c.state.r=1.6;c.state.which='single';const sz=Demo.arenaSize(2,0);
    c.pa=c.panel({size:sz,fov:6,title:'O1 dish'});const w=document.createElement('div');w.className='pw';c.vis.appendChild(w);el('div',{class:'ptitle'},w,'Side box');c.sb=makeCanvas(w,430,330);boundariesIcons(c.sb,430,330);
    const seg=el('div',{class:'seg',id:'steps31'},c.ctrls);['1 points','2 links','3 connected group','4 outline + ID','5 body frame'].forEach((nm,i)=>{const b=el('button',{},seg,nm);b.onclick=()=>{c.state.step=i+1;seg.querySelectorAll('button').forEach((x,j)=>x.classList.toggle('on',j===i));Demo.redraw();};if(i===0)b.classList.add('on');});
    const lab=el('label',{},c.ctrls,'link radius <input type="range" min="0.8" max="3.0" step="0.1" value="1.6" id="r31"> <b id="rv31">1.6</b>');lab.querySelector('input').oninput=function(){c.state.r=+this.value;document.getElementById('rv31').textContent=(+this.value).toFixed(1);Demo.redraw();};
    const sel=el('div',{class:'seg'},c.ctrls);[['single','one dish'],['merge','dish with two clusters']].forEach(a=>{const b=el('button',{},sel,a[1]);b.onclick=()=>{c.state.which=a[0];sel.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));Demo.redraw();};if(a[0]==='single')b.classList.add('on');});
    ['single','merge'].forEach(k=>{const d=D[k];d.P=[];const a=B64.i16(d.xy,1000),l=B64.i16(d.lev6,1000);d.lev=Array.from(l);for(let i=0;i<d.n;i++)d.P.push([a[2*i],a[2*i+1]]);});},
  draw(c){
    const D=c.state.D[c.state.which],P=D.P,p=c.pa,r=c.state.r,st=c.state.step;let cx=0,cy=0;P.forEach(q=>{cx+=q[0];cy+=q[1];});cx/=P.length;cy/=P.length;p.cx=cx;p.cy=cy;p.fov=c.state.which==='merge'?9.5:6;p.scale=Math.min(p.w,p.h)/(2*p.fov);p.clear();p.scaleBar();
    const comp=components(P,r),sizes=new Array(comp.n).fill(0);comp.lab.forEach(l=>sizes[l]++);const org=sizes.map((s,i)=>s>=3?i:-1).filter(i=>i>=0);
    let nl=0;if(st>=2){for(let i=0;i<P.length;i++)for(let j=i+1;j<P.length;j++)if(dist(P[i],P[j])<r){p.line(P[i],P[j],{color:'#444',w:1.6});nl++;}}
    // outline per organism
    if(st>=4){org.forEach(o=>{const idx=P.map((q,i)=>i).filter(i=>comp.lab[i]===o);const sub=idx.map(i=>P[i]);const E=alphaEdges(sub,1.5);E.forEach(e=>p.line(sub[e[0]],sub[e[1]],{color:C.ink,w:3.2}));
      const m=sub.reduce((a,q)=>[a[0]+q[0]/sub.length,a[1]+q[1]/sub.length],[0,0]);p.label('organism #'+(org.indexOf(o)+1)+' · '+sub.length+' cells',m[0],Math.max(...sub.map(q=>q[1]))+1.1,{align:'center',size:13,bold:true,world:true,bg:true});});}
    for(let i=0;i<P.length;i++){const member=sizes[comp.lab[i]]>=3;p.node({x:P[i][0],y:P[i][1],fill:st>=3?(member?'#777':'#CCCCCC'):'#777',r:0.38,label:String(D.id[i]),stroke:st>=3&&member?C.ink:'rgba(0,0,0,.35)',lw:st>=3&&member?2:1,dash:st>=3&&!member?[3,2]:null});}
    if(st>=5&&org.length){const o=org[0],idx=P.map((q,i)=>i).filter(i=>comp.lab[i]===o),sub=idx.map(i=>P[i]),l6=idx.map(i=>D.lev[i]);const bf=bodyFrameOf(sub,l6);
      const L=3.6;p.arrow(bf.c,[bf.c[0]+L*bf.e1[0],bf.c[1]+L*bf.e1[1]],{color:C.ink,w:3,head:12});p.arrow(bf.c,[bf.c[0]+2.2*bf.e2[0],bf.c[1]+2.2*bf.e2[1]],{color:C.ink,w:3,head:12});
      p.label('e1: head → tail (from the gradient)',bf.c[0]+(L+0.3)*bf.e1[0],bf.c[1]+(L+0.3)*bf.e1[1],{world:true,size:13,bold:true,bg:true,align:bf.e1[0]<0?'right':'left'});p.label('e2: limb side',bf.c[0]+2.4*bf.e2[0],bf.c[1]+2.4*bf.e2[1],{world:true,size:13,bold:true,bg:true,align:bf.e2[0]<0?'right':'left'});}
    const desc=['points: '+P.length+' tracked cells','links: '+nl+' pairs closer than '+r.toFixed(1),'connected groups: '+comp.n+' (sizes '+sizes.slice().sort((a,b)=>b-a).join(', ')+')','organisms (≥3 cells): '+org.length,'body frame of organism #1'][st-1];
    p.setSub(desc+(st>=3&&r<1.0?' — fragmenting':'')+(st>=3&&c.state.which==='merge'&&org.length===1?' — the two clusters have merged into one collective':''));
    if(c.state.which==='merge')p.setTitle('O1 dish with two clusters (package run_00702)');else p.setTitle('O1 dish (package run_01105)');}
});

/* ---------------- 3.2 ---------------- */
function stackCharts(parent,w,h,n){const arr=[];for(let i=0;i<n;i++){const cv=makeCanvas(parent,w,h);cv.style.display='block';cv.style.marginBottom='4px';arr.push(cv);}return arr;}
Demo.register({id:'3.2',act:3,title:'Layers of identity, and V_body',data:['data/c32.js'],duration:150,rate:12,truthOffered:false,
  legend:LEG.mat.concat(LEG.band).concat([{color:C.sa,label:'state a'},{color:C.sb,label:'state b'}]),
  caption:'The frozen T5 monitor reads one dish and keeps four layers apart: <b>material</b> (who is in the collective), <b>geometry</b> (size, cohesion, shape), <b>pattern</b> (the channel patterns) and <b>state</b> (which collective memory). <b>V_body</b> is true while material <i>and</i> geometry stay inside their natural bands since the start; the state is reported separately.',
  takeaway:'Same body, different state: identity has layers.',
  notes:'Definitions as implemented in t5_blind_control/code/t5mon/monitor.py (AUDIT_T5 A2): material = 1 − Jaccard of the id set to the first frame (only losses/arrivals leave its band, so a cut leaves it flat); geometry = worst of cohesion bridge ≤ 1.40, shape change ≤ 4.9 % / 6.6 %, 24 cells in one linked component; pattern = largest standardized deviation of 14 state-independent channel-pattern features from the dish\'s own baseline, bound 4.83; state = two-state Gaussian posterior (S+ = a, S− = b). V_body is cumulative (latches at the first violation). The T4 lesson: folding the state into identity marks switched bodies as “broken”. Exemplars: undisturbed and cut = package runs 00266/00263 (body 2700); light switch = T5 held-out seed 6007 controller (O1 frames regenerated with the live server\'s own noise stream; the monitor reproduces the logged verdicts in all 164 frames).',
  audit:'AUDIT_T5 A2: material is the id set only — a cut moves cells but loses none, so only geometry (and V_body) react; storyboard wording “material and geometry leave their bands” was corrected accordingly.',
  sources:[{what:'Monitor traces on three exemplars (frozen T5 monitor, MONITOR_CONFIG.json)',file:'demo_v1/data/c32.js',sec:'built by build/build_ch3.py'},{what:'Monitor implementation (material / geometry / pattern / state, V_body)',file:'t5_blind_control/code/t5mon/monitor.py',sec:'lines 19–63 (see AUDIT_T5 A2)'},{what:'Bounds',file:'t5_blind_control/MONITOR_CONFIG.json',sec:'bounds'},{what:'Cut and undisturbed runs',file:'testbed_blind_v3/runs/run_00263, run_00266'},{what:'Light-switch run',file:'t5_blind_control/episodes_heldout/ep_00988.json (seed 6007 controller)'}],
  setup(c){
    const D=DATA.c32;c.state.D=D;c.state.ex='undisturbed';const sz=Math.min(Demo.arenaSize(2,0),520);
    const sel=el('div',{class:'seg',id:'ex32'},c.ctrls);const names={undisturbed:'Undisturbed',cut:'Cut',light:'Light switch'};
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
    const pl={undisturbed:[{t:110,text:'Every layer stays inside its natural band.',anchor:()=>here(1,0.7,40)}],
      cut:[{t:(firstV||51),text:'SPLIT: geometry leaves its band (two collectives) → V_body is false. Material stays flat: nobody was lost.',anchor:()=>here(1,0.34,30)}],
      light:[{t:(sw||94)+6,text:'Material and geometry stay flat → V_body stays true. The pattern is pushed out of its band during the pulse, and the state changes.',anchor:()=>here(3,0.6,40)}]}[k];
    def.pauses=pl;Demo.buildTicks();Demo.t=Math.min(Demo.t,def.duration);Demo.hideCallout();Demo.playing=false;Demo.seek(0);
    Demo.setLegend(LEG.mat.concat(LEG.band).concat([{color:C.sa,label:'state a'},{color:C.sb,label:'state b'}]));
    document.getElementById('caption').innerHTML=def.caption;},
  draw(c,tcur){
    const D=c.state.D,k=c.state.ex,e=D[k],tr=e.tr,t=tr.t;let i=0;while(i+1<t.length&&t[i+1]<=tcur+1e-9)i++;const p=c.pa;
    const xy=e.XY[i],n=xy.length/2;let cx=0,cy=0;for(let j=0;j<n;j++){cx+=xy[2*j];cy+=xy[2*j+1];}p.cx=cx/n;p.cy=cy/n;p.clear();p.scaleBar();
    if(k==='light'){e.acts.forEach(a=>{const ph=lightWindow(tr.t[i],a.t,a.t+a.dur,a.ramp);drawLight(p,a.xy,a.r,ph);});}
    for(let j=0;j<n;j++)p.node({x:xy[2*j],y:xy[2*j+1],fill:'#777',r:0.38});
    if(k==='cut'&&tcur>=50)p.label('cut at t = 50',p.w/2,18,{align:'center',size:13,bold:true,color:'#C0392B'});
    if(k==='light')p.label('light at the body centre (pulses at t = 20 and 33)',p.w/2,18,{align:'center',size:12.5,color:C.mute});
    p.setTitle({undisturbed:'Undisturbed dish (untreated twin, body 2700)',cut:'Dish after a cut (body 2700)',light:'Light switch (held-out dish, seed 6007)'}[k]);p.setSub('t = '+tr.t[i].toFixed(0)+' tu · '+tr.ncomp[i]+' linked group(s)');
    const B=D.bounds;const mk=(cv,title,ys,o)=>{const ch=new Chart(cv,{w:590,h:c.chH,xlim:[0,t[t.length-1]],ylim:o.ylim,yticks:o.yticks,m:{l:44,r:10,t:18,b:o.last?22:6},title:title,xlabel:o.last?'time (tu)':null,yfmt:o.yfmt});ch.clear();if(o.band)ch.hband(o.band[0],o.band[1],C.band);ch.axes();
      if(o.hl!=null)ch.hline(o.hl,{color:'#999',dash:[4,3],label:o.hlab});if(k==='cut')ch.vline(50,{color:'#C0392B',dash:[3,3]});if(k==='light'){ch.vline(20,{color:'#999',dash:[3,3]});}
      const xs=t.slice(0,i+1),yy=ys.slice(0,i+1).map(v=>Math.min(v,o.ylim[1]));if(o.state)ch.segColor(xs,yy,(j)=>yy[j]>0.5?C.sa:C.sb,3.2);else ch.line(xs,yy,{color:o.color,w:2.2,dash:o.dash});
      ch.vline(tr.t[i],{color:'#222',w:1});return ch;};
    mk(c.cvs[0],'Material: 1 − Jaccard to baseline members',tr.material,{ylim:[0,1.05],yticks:[0,0.5,1],band:[0,0.02],color:'#777',hl:0.02,hlab:''});
    mk(c.cvs[1],'Geometry: worst bound ratio (≤ 1 = inside the band)',tr.geometry,{ylim:[0,3],yticks:[0,1,2,3],band:[0,1],color:'#222'});
    mk(c.cvs[2],'Pattern: standardized deviation / bound',tr.pattern,{ylim:[0,3],yticks:[0,1,2,3],band:[0,1],color:'#222',dash:[6,4]});
    mk(c.cvs[3],'State: posterior of state a',tr.p_plus,{ylim:[0,1.02],yticks:[0,0.5,1],state:true,last:true,hl:0.5});
    const V=tr.V[i],st=tr.state[i];c.state.badges.innerHTML=badge('V_body '+(V?'true':'false'),V?'ok':'bad')+badge('material '+(tr.mat_ok[i]?'inside band':'outside'),tr.mat_ok[i]?'ok':'bad')+badge('geometry '+(tr.geo_ok[i]?'inside band':'outside'),tr.geo_ok[i]?'ok':'bad')+badge('State: '+(st==='S+'?'a':st==='S-'?'b':'in transition'),'neu')+(tr.ev[i].length?badge('event '+tr.ev[i].join(','),'bad'):'');
  }
});

/* ---------------- 3.3 ---------------- */
Demo.register({id:'3.3',act:3,title:'Ship of Theseus',data:['data/c33.js'],duration:2800,rate:100,truthOffered:false,legend:LEG.rho.concat([{cls:'ring',label:'newly inserted node (flash)'}]).slice(0,3).concat([{color:'#fff',label:'newly inserted node: bright halo for 3 tu'},{cls:'solid',color:'#222',label:'thick outline = original cell'}]),
  caption:'Serial replacement (one random cell swapped for a naive newcomer every 100 tu; 24 swaps, noise-free engine; truth view, nodes shaded by their hidden memory ρ). The newcomer adopts the collective state within about 2 tu; after the last swap no original cell is left.',
  takeaway:'The collective memory outlives every original cell.',
  notes:'Protocol of IDENTITY_EVENTS_V3 (job_serial, seed 0), regenerated deterministically at 1 tu resolution. Newcomers start undecided (ρ = ½, no secretion) and read only their neighbours\' ligand fraction, so they inherit the state at once. The body\'s shape is not repaired by the structure module (G1 repairs a single swap 17/24 times, but not serial replacement: 0/4 complete): this is the structure result, not a memory result. Playback slows near the first three swaps.',
  sources:[{what:'Serial replacement, seed 0: 24 swaps × 100 tu + 400 tu settle',file:'testbed_v3/IDENTITY_EVENTS_V3.md',sec:'Serial replacement (Ship of Theseus for the memory)'},{what:'Regenerated frames (deterministic, noise-free)',file:'demo_v1/data/c33.js',sec:'build/build_ch3.py (testbed_v3/code/h4.py job_serial protocol)'},{what:'Newcomer adopts the state in 2 tu (24/24)',file:'testbed_v3/IDENTITY_EVENTS_V3.md',sec:'Memory outcomes'}],
  setup(c){
    const D=DATA.c33;c.state.X=B64.i16(D.X,1000);c.state.R=B64.i16(D.rho,20000);c.state.I=B64.i16(D.ids,1);c.state.D=D;const sz=Math.min(Demo.arenaSize(2,0),560);
    c.pa=c.panel({size:sz,fov:9,title:'Serial replacement (truth view)'});const w=document.createElement('div');w.className='pw';c.vis.appendChild(w);el('div',{class:'ptitle'},w,'Identity traces');c.cvH=sz;c.cv=makeCanvas(w,560,sz);
    c.state.type=(i)=>D.tmplType[D.perm0[i]];D.speedAt=(t)=>{for(const r of D.reps.slice(0,3)){if(t>=r[0]-1&&t<=r[0]+5)return 0.04;}return 1;};},
  speedAt(c,t){return c.state.D.speedAt(t);},
  draw(c,t){
    const D=c.state.D,k=Math.min(Math.round(t),D.T-1),N=24,p=c.pa;const qx=[],qy=[];for(let i=0;i<N;i++){qx.push(c.state.X[(k*N+i)*2]);qy.push(c.state.X[(k*N+i)*2+1]);}const med=v=>v.slice().sort((a,b)=>a-b)[N>>1];p.cx=med(qx);p.cy=med(qy);{const ds=qx.map((x,i)=>Math.hypot(x-p.cx,qy[i]-p.cy)).sort((a,b)=>a-b);p.fov=Math.max(9,Math.min(30,ds[Math.floor(N*0.8)]+2));p.scale=Math.min(p.w,p.h)/(2*p.fov);}
    p.clear();p.scaleBar();let flash=-1;D.reps.forEach(r=>{if(t>=r[0]&&t<r[0]+3)flash=r[1];});
    for(let i=0;i<N;i++){const id=c.state.I[k*N+i],orig=id<24,fl=(i===flash);p.node({x:c.state.X[(k*N+i)*2],y:c.state.X[(k*N+i)*2+1],fill:rhoColor(c.state.R[k*N+i]),r:0.4,stroke:orig?C.ink:'rgba(0,0,0,.4)',lw:orig?2.4:1,hl:fl});}
    if(flash>=0){const q=p.w2p(c.state.X[(k*N+flash)*2],c.state.X[(k*N+flash)*2+1]);p.ctx.save();p.ctx.strokeStyle='#fff';p.ctx.lineWidth=5;p.ctx.beginPath();p.ctx.arc(q[0],q[1],0.4*p.scale+10,0,6.3);p.ctx.stroke();p.ctx.strokeStyle=C.ink;p.ctx.lineWidth=1.5;p.ctx.stroke();p.ctx.restore();}
    p.label('original nodes remaining: '+D.orig[k]+' / 24',p.w/2,20,{align:'center',size:16,bold:true});p.setSub('t = '+t.toFixed(0)+' tu · swaps so far: '+D.reps.filter(r=>r[0]<=t).length+' / 24 · linked groups: '+D.nc[k]);
    const g=c.cv,ch=new Chart(g,{w:560,h:c.cvH,xlim:[0,D.T],ylim:[0,1.08],yticks:[0,0.5,1],m:{l:46,r:12,t:24,b:28},xlabel:'time (tu)',title:'identity layers over time'});ch.clear();ch.axes();
    const xs=[],mat=[],rho=[],geo=[];for(let j=0;j<=k;j+=5){xs.push(j);mat.push(D.orig[j]/24);rho.push(D.rho_mean[j]);geo.push(D.geo[j]<=1?1:0);}
    ch.line(xs,mat,{color:'#777',w:3});ch.line(xs,rho,{color:C.sa,w:3});ch.line(xs,geo,{color:'#222',w:2.2,dash:[6,4]});ch.vline(t,{color:'#222',w:1});
    ch.text('material: fraction of original cells',ch.X(1900),ch.Y(0.06),{align:'right',color:'#555',bold:true});ch.text('state: mean ρ (a)',ch.X(2790),ch.Y(0.82),{align:'right',color:'#1f7fb5',bold:true});ch.text('geometry inside its natural band (1 = yes, 0 = no)',ch.X(2790),ch.Y(1.04),{align:'right',color:'#222',size:12});},
  pauses:[{t:3,text:'First replacement: the newcomer adopts the collective state within ~2 tu.',side:'left',anchor:c=>{const D=c.state.D,i=D.reps[0][1],k=3;return {panel:c.pa,x:c.state.X[(k*24+i)*2]-c.pa.cx,y:c.state.X[(k*24+i)*2+1]-c.pa.cy};}},
          {t:2301,text:'No original node left.',side:'left',anchor:c=>({panel:c.pa,x:0,y:-3.9})},
          {t:2800,text:'The memory persists; the body\'s shape does not.',side:'left',anchor:c=>({panel:c.pa,x:0,y:3.9})}]
});

/* ---------------- 3.4 ---------------- */
Demo.register({id:'3.4',act:3,title:'Discovering the states blind',data:['data/c34.js'],duration:0,truthOffered:true,
  legend:[{color:'#777',label:'T4 blind label 0'},{color:'#222',label:'blind label 2'},{color:'#fff',label:'rare label 1 (hollow)'},{cls:'solid',color:'#888',label:'× = out of distribution'}],
  caption:'Each dot is one natural dish at one time (260 dishes × 8 frames), placed by two of the blind analyst\'s descriptors: the reporter left-right dipole and the memory-ligand difference. Marker shapes are the labels T4 invented without being told anything; press T to recolour by the true collective state (agreement 99–100 %, AUDIT_T4 A4).',
  takeaway:'Without being told, the blind pipeline found the two collective states.',
  notes:'T4 labelled the two big clusters 0 and 2 and a small third cluster 1 (4 % of dishes). Truth: label 0 = state b (978/978 frames), label 2 = state a (972/972); the rare label 1 holds both states (a 43, b 47 frames) — the audit showed it is a body-specific structural variant, not a third collective state. T4 called the two states “mirror images”; the audit corrected this: the same body, only the reporter row and the ligand levels differ (inset).',
  audit:'Corrects T4: “mirror-image organisations” → one chiral body, reporter row moved (AUDIT_T4 A4).',
  sources:[{what:'Descriptors c0_dq_sens and c4_mean − c5_mean, T4 label per frame (O1, 260 natural dishes × 8 frames)',file:'t4_blind_identity/outputs/run_*.json.gz',sec:'levels.O1.frames[].organisms[].desc, C3.label'},{what:'True state (hidden tier)',file:'testbed_v3/data/blind_v2_hidden/run_*.json',sec:'meta.state'},{what:'Agreement 99–100 %; mirror image corrected',file:'testbed_v3/audit_t4/AUDIT_T4.md',sec:'A4'}],
  setup(c){
    const D=DATA.c34;c.state.D=D;const w=document.createElement('div');w.className='pw';c.vis.appendChild(w);el('div',{class:'ptitle'},w,'T4\'s blind descriptors');c.sc=makeCanvas(w,640,560);
    const w2=document.createElement('div');w2.className='pw';c.vis.appendChild(w2);el('div',{class:'ptitle'},w2,'Same body, two states (from 1.4)');
    c.inset=new Panel(w2,{size:340,fov:5.4,title:''});c.inset.wrap=w2;c.panels.push(c.inset);c.inset.noBubble=true;w2.querySelector('.ptitle').remove();el('div',{class:'ptitle'},w2,'');
    c.state.tbl=el('div',{style:'font-size:13.5px;max-width:340px;margin-top:6px;line-height:1.35'},w2,'');},
  draw(c,t,truth){
    const D=c.state.D,ch=new Chart(c.sc,{w:640,h:560,xlim:[-0.25,0.25],ylim:[-1,1],m:{l:56,r:14,t:26,b:46},xticks:[-0.2,-0.1,0,0.1,0.2],yticks:[-1,-0.5,0,0.5,1],title:'natural dishes (O1)',xfmt:v=>v.toFixed(1),yfmt:v=>v.toFixed(1)});ch.clear();ch.axes();
    const g=ch.c;g.save();g.font='13px '+FONT;g.fillStyle=C.ink;g.textAlign='center';g.fillText('reporter left–right dipole (c0)',ch.X(0),ch.h-8);g.translate(14,ch.Y(0));g.rotate(-Math.PI/2);g.fillText('memory-ligand difference (c4 − c5)',0,0);g.restore();
    for(let i=0;i<D.x.length;i++){const L=D.lab[i],px=ch.X(D.x[i]),py=ch.Y(D.y[i]);const col=truth?(D.truth[i]?C.sa:C.sb):(L===0?'#777':L===2?'#222':L===1?'#fff':'#999');g.save();g.fillStyle=col;g.strokeStyle=truth?'rgba(0,0,0,.45)':'#222';g.lineWidth=L===1?1.8:0.8;
      if(L===-1){g.strokeStyle=truth?col:'#999';g.lineWidth=1.6;g.beginPath();g.moveTo(px-3.5,py-3.5);g.lineTo(px+3.5,py+3.5);g.moveTo(px+3.5,py-3.5);g.lineTo(px-3.5,py+3.5);g.stroke();}
      else if(L===1){g.beginPath();g.rect(px-3.5,py-3.5,7,7);g.fill();g.stroke();}else if(L===2){g.beginPath();g.moveTo(px,py-4.5);g.lineTo(px+4.2,py+3.2);g.lineTo(px-4.2,py+3.2);g.closePath();g.fill();g.stroke();}else{g.beginPath();g.arc(px,py,3.4,0,6.3);g.fill();g.stroke();}g.restore();}
    ch.text('label 2',ch.X(0.15),ch.Y(0.9),{align:'center',bold:true});ch.text('label 0',ch.X(-0.15),ch.Y(-0.9),{align:'center',bold:true});
    Demo.setLegend(truth?[{color:C.sa,label:'true state a'},{color:C.sb,label:'true state b'},{cls:'solid',color:'#888',label:'shapes = T4 blind labels (● 0, ▲ 2, ■ rare 1, × out of distribution)'}]:[{color:'#777',label:'● label 0'},{color:'#222',label:'▲ label 2'},{color:'#fff',label:'■ rare label 1'},{cls:'solid',color:'#888',label:'× out of distribution'}]);
    // inset: clone pair overlay of body 2100
    const p=c.inset;p.clear();p.scaleBar();const B=decodeBody();const na=bodyNodes(B,10,'a',{ring:true}),nb=bodyNodes(B,10,'b',{ring:true});
    na.forEach(n=>p.node({x:n.x,y:n.y,fill:TYPEC[n.type],ring:n.ring,r:0.38}));nb.forEach(n=>{const q=p.w2p(n.x,n.y),cc=p.ctx;cc.save();cc.strokeStyle=C.sb;cc.lineWidth=2.2;cc.setLineDash([4,3]);cc.beginPath();cc.arc(q[0],q[1],0.6*p.scale,0,6.3);cc.stroke();cc.restore();});
    const a=D.agree;c.state.tbl.innerHTML='<b>T4 called them mirror images. The audit: one body</b> — positions coincide exactly (filled = state a, dashed = state b); only the reporter row and ligand levels differ.<br><br>Common labels vs truth: label 0 → b '+a['0'].n+'/'+a['0'].n+'; label 2 → a '+a['2'].n+'/'+a['2'].n+'. Rare label 1: both states ('+Math.round(a['1'].frac_true_a*a['1'].n)+' a, '+(a['1'].n-Math.round(a['1'].frac_true_a*a['1'].n))+' b).';
  },
  views:null
});

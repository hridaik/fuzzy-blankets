/* Act 4 - Control (chapters 4.1 - 4.4) */
'use strict';
function packedNodes(X,R,k,N,types,mode,xoff){const nodes=[];for(let i=0;i<N;i++){const rho=R?R[k*N+i]:0.5;nodes.push({x:X[(k*N+i)*2],y:X[(k*N+i)*2+1],type:types?types[i]:1,rho:rho,fill:mode==='rho'?rhoColor(rho):TYPEC[types[i]]});}return nodes;}
const GREYS=(d,lo,hi)=>{const u=Math.max(0,Math.min(1,(d-lo)/(hi-lo)));const g=Math.round(238-205*u);return 'rgb('+g+','+g+','+g+')';};
const DOSELEG=[{color:'#EEEEEE',label:'1× (cheapest place)'},{color:'#9C9C9C',label:'~3×'},{color:'#353535',label:'5× or more'}];
/* ---------------- 4.1 ---------------- */
const MECH41={L1:'migration gain (cells move faster)',L2:'structural-signal secretion',L3:'memory-ligand A secretion — pushes b → a only',L4:'memory-ligand B secretion — pushes a → b only',L5:'receptor gain (scales the sensed field)'};
Demo.register({id:'4.1',act:4,title:'Finding the knob',data:['data/c41.js'],duration:100,rate:7,truthOffered:false,
  legend:LEG.rho.concat(LEG.light),
  caption:'Five lights, same disc at the body centre, same duration (10 tu) and dose (300), applied to one development dish in state a (top) and to its clone in state b (bottom); nodes are shaded by their <b>hidden</b> memory ρ. Only two lights change the collective state, and each only in one direction; the others do nothing visible or damage the body.',
  takeaway:'Two of five lights flip the collective state — each in only one direction.',
  notes:'Dose = amplitude 5 × duration 10 × 6 cells = 300 for every light. Row a and row b are the same body (dev seed 5001; the b row is its clone in state b), re-simulated deterministically from the dish state at t = 20 (the B1 screening protocol of T5, now with hidden ρ). Badges are computed from the hidden truth with the declared rule: damage = more than one linked group or a cell displaced > 2 units vs the untreated twin; pattern only = secreted structural codes change by > 0.1 without damage; flipped = mean ρ ends on the other side. At one fifth of this dose L2 changes only pattern (B1: amplitude 1, 1 group). L5 at this dose makes the engine itself diverge (positions blow up): damage.',
  audit:'AUDIT_T5 A5: L3 = memory-ligand-A secretion (b→a), L4 = memory-ligand-B secretion (a→b); L1 = migration, L2 = structural secretion, L5 = receptor gain.',
  sources:[{what:'Five-light screening at the body centre (amp 5, 10 tu), both start states, hidden effects vs untreated twin',file:'demo_v1/data/c41.js',sec:'build/build_ch4a.py (T5 B1 protocol, seed 5001)'},{what:'True mechanism of L1–L5 and one-directionality of L3/L4',file:'testbed_v3/audit_t5/AUDIT_T5.md',sec:'A5'},{what:'T5 sysid B1 classification',file:'t5_blind_control/SYSID.md',sec:'B1'}],
  setup(c){
    const D=DATA.c41;c.state.D=D;c.state.reveal=false;const s=Math.min(Demo.arenaSize(5,0),250);
    c.state.panels={};['a','b'].forEach(st=>{const row=el('div',{style:'display:flex;gap:10px;justify-content:center;align-items:flex-start;width:100%'},c.vis);const lab=el('div',{style:'width:70px;font-weight:700;font-size:15px;padding-top:30px;text-align:right'},row,'state '+st);
      c.state.panels[st]=D.rows[st].clips.map((cl,i)=>{const w=el('div',{class:'pw'},row);const p=new Panel(w,{size:s,fov:6.5,title:cl.label});p.wrap=w;c.panels.push(p);p.noBubble=false;cl.XX=B64.i16(cl.X,1000);cl.RR=B64.i16(cl.rho,20000);return p;});});
    const b=el('button',{class:'btn'},c.ctrls,'Reveal what the lights do');b.onclick=()=>{c.state.reveal=!c.state.reveal;b.classList.toggle('on',c.state.reveal);Demo.redraw();};},
  draw(c,t){
    const D=c.state.D,k=Math.max(0,Math.min(D.params.T-1,Math.floor(t)));const done=t>=14;
    ['a','b'].forEach(st=>{D.rows[st].clips.forEach((cl,i)=>{const p=c.state.panels[st][i],types=D.rows[st].types;p.clear();p.scaleBar();
      const ph=lightWindow(t+1,0,10,2.5);drawLight(p,cl.disc,1.5,ph);const nodes=packedNodes(cl.XX,cl.RR,k,24,types,'rho');nodes.forEach(n=>p.node({x:n.x,y:n.y,fill:n.fill,r:0.4}));
      const vk=cl.verdict==='state flipped'?'ok':(cl.verdict==='no effect'?'neu':'bad');p.setSub((done?badge(cl.verdict,vk):'<span class="badge neu">…</span>')+(c.state.reveal?'<div style="max-width:'+p.w+'px;font-size:12px;margin-top:3px">'+MECH41[cl.label]+'</div>':''));});});}
});

/* ---------------- 4.2 ---------------- */
Demo.register({id:'4.2',act:4,title:'Where and how long to push',data:['data/c42map.js','data/c42clips.js'],duration:120,rate:9,truthOffered:true,
  legend:TYPELEG.concat(DOSELEG),
  caption:'Left: the body (faint node colours = structural types) with the places T5 tested, discs shaded by the dose they needed relative to the body centre (blind map, 4 development dishes); press T for the true threshold map of all 24 places. Right: dose against pulse duration. Below: equal dose, two places — the centre switches the memory, the tail end relaxes back.',
  takeaway:'Where you push matters more than how hard — and pushes shorter than ~5 time units never work.',
  notes:'T5\'s “head” (+p) disc sits on the TAIL end of the body and its “tail” disc on the head end: its body axis e1 points head→tail (audit). Relative doses (dose* = amplitude × duration × cells at 20–40 tu, same dish): centre 1×, side 1.2×, head end ("T5 tail") 1.8×, tail end ("T5 head") 4.0×. True per-place thresholds (SWITCH_V3, 26.7-tu pulses): best place 233, median 260, worst corner 1,387; threshold amplitude falls with the kernel connectivity of the lit disc (Spearman −0.98). No threshold exists for pulses shorter than l*/g ≈ 3.8 tu (bounded drive); T5 measured: 2 tu never, 5 tu needs 3–4× the dose. The mini-clips are a deterministic re-simulation of dev dish 5004 at equal dose (centre 7 cells, tail end 6 cells, same total dose).',
  audit:'Corrects T5\'s naming: its “head” disc is the tail end of the body, its “tail” disc the head end. Magnitudes (1×/1.2×/1.8×/4×) agree with the true place thresholds (1×/1.1×/1.6×/3.4×).',
  sources:[{what:'T5 blind dose map: dose* geometric means by location and duration (4 dishes)',file:'t5_blind_control/logs/b2_results.jsonl',sec:'dose_star; SYSID.md B2'},{what:'T5 discs located in the true body frame; true per-place thresholds; connectivity rule',file:'testbed_v3/audit_t5/data/a4_location.json',sec:'AUDIT_T5 A4'},{what:'True duration curve at the body centre (noise-free bisection, 3 held-out dishes)',file:'testbed_v3/audit_t5/data/a4b_duration.json',sec:'AUDIT_T5 A4'},{what:'Equal-dose mini-clips (re-simulated)',file:'demo_v1/data/c42clips.js',sec:'build/build_ch4a.py'}],
  setup(c){
    const M=DATA.c42map,K=DATA.c42clips;c.state.M=M;c.state.K=K;c.state.XS=M.template.xy;const sz=Math.min(Demo.arenaSize(2,0),560);
    const top=el('div',{style:'display:flex;gap:14px;flex-wrap:wrap;justify-content:center;width:100%'},c.vis);
    const pw=el('div',{class:'pw'},top);c.pm=new Panel(pw,{size:sz,fov:5.2,title:'Blind dose map (T5)',cx:0.2});c.pm.wrap=pw;c.panels.push(c.pm);
    const right=el('div',{class:'pw'},top);el('div',{class:'ptitle'},right,'Dose vs pulse duration (body centre unless stated)');c.cv=makeCanvas(right,600,Math.round(sz*0.52));
    const row=el('div',{style:'display:flex;gap:14px;justify-content:center;margin-top:6px'},right);
    ['centre','tail_end'].forEach(k=>{const w=el('div',{class:'pw'},row);const p=new Panel(w,{size:Math.round(sz*0.44),fov:6.2,title:k==='centre'?'Equal dose at the body centre':'Equal dose at the tail end'});p.wrap=w;p.id=k;c.panels.push(p);c['p_'+k]=p;K.clips[k].XX=B64.i16(K.clips[k].X,1000);K.clips[k].RR=B64.i16(K.clips[k].rho,20000);});
    c.cvH=Math.round(sz*0.52);},
  draw(c,t,truth){
    const M=c.state.M,K=c.state.K,p=c.pm;p.clear();p.scaleBar();const XS=c.state.XS;
    XS.forEach((q,i)=>p.node({x:q[0],y:q[1],fill:TYPEC[M.template.type.length?({head:1,trunk:2,limb:3,tail:4})[M.template.type[i]]:1],r:0.42,alpha:0.45}));
    if(!truth){const names={C:'centre',side:'side',tail:'T5 “tail” (p = −3)',head:'T5 “head” (p = +3)'};const rel=M.blind_rel_same_dish;const lp={C:[0,-2.15],side:[0,3.45],tail:[-3,-2.15],head:[3.1,-2.15]};
      ['C','side','tail','head'].forEach(k=>{const q=M.blind_centres[k],d=rel[k];const g=p.ctx,pp=p.w2p(q[0],q[1]);g.save();g.fillStyle=GREYS(d,1,5);g.globalAlpha=0.55;g.beginPath();g.arc(pp[0],pp[1],1.5*p.scale,0,6.3);g.fill();g.globalAlpha=1;g.strokeStyle=C.ink;g.setLineDash([6,4]);g.lineWidth=1.6;g.stroke();g.restore();
        p.label(names[k]+'  '+d.toFixed(1)+'×',lp[k][0],lp[k][1],{align:'center',bold:true,size:13,world:true,bg:true});});
      p.setTitle('Blind dose map (T5; relative dose, same dish)');p.setSub('Audit: T5\'s +p axis points to the tail — its “head” disc sits on the tail end.');}
    else{const T=M.true['16g'];const best=Math.min(...T.map(r=>r.dose));T.forEach(r=>{const d=r.dose/best,pp=p.w2p(r.xy[0],r.xy[1]),g=p.ctx;g.save();g.fillStyle=GREYS(d,1,6);g.globalAlpha=0.85;g.beginPath();g.arc(pp[0],pp[1],0.5*p.scale,0,6.3);g.fill();g.globalAlpha=1;g.strokeStyle=C.ink;g.lineWidth=1;g.stroke();g.restore();p.label(d.toFixed(1),pp[0],pp[1],{align:'center',size:11.5,bold:true,color:d>2.8?'#fff':C.ink});});
      p.setTitle('True threshold map (26.7-tu pulse, disc r = 1.5 on each place)');p.setSub('dose relative to the cheapest place (233); corners and tips cost 3–6×');}
    // chart: dose vs duration, log-log
    const durs=[2,5,10,20,40],ch=new Chart(c.cv,{w:600,h:c.cvH,xlim:[Math.log10(1.6),Math.log10(60)],ylim:[1.6,3.5],m:{l:52,r:12,t:22,b:36},xticks:durs.map(Math.log10),yticks:[2,2.5,3,3.5],xfmt:v=>String(Math.round(Math.pow(10,v))),yfmt:v=>String(Math.round(Math.pow(10,v))),title:'dose = amplitude × duration × cells',xlabel:'pulse duration (tu)'});ch.clear();
    const wall=Math.log10(3.8);ch.c.save();ch.c.fillStyle='rgba(192,57,43,.10)';ch.c.fillRect(ch.m.l,ch.m.t,ch.X(wall)-ch.m.l,ch.h-ch.m.t-ch.m.b);ch.c.restore();ch.axes();ch.vline(wall,{color:'#C0392B',dash:[5,3],label:'wall ≈ 3.8 tu'});
    const col={C:'#222',side:'#777',tail:'#999',head:'#444'},dash={C:null,side:null,tail:[4,3],head:[2,3]};
    ['C','side','tail','head'].forEach(k=>{const xs=[],ys=[];[10,20,40].forEach(d=>{const v=M.blind_dose[k+'|'+d+'.0'];if(v){xs.push(Math.log10(d));ys.push(Math.log10(v));}});if(k==='C'&&M.blind_dose['C|5.0']){xs.unshift(Math.log10(5));ys.unshift(Math.log10(M.blind_dose['C|5.0']));}ch.line(xs,ys,{color:col[k],w:2.4,dash:dash[k]});xs.forEach((x,i)=>ch.dot(x,ys[i],{color:col[k],r:3.5}));
      ch.text({C:'centre',side:'side',tail:'T5 “tail”',head:'T5 “head”'}[k],ch.X(xs[xs.length-1])+6,ch.Y(ys[ys.length-1]),{size:11.5,color:col[k],bold:true});});
    if(M.duration_true){const rows={};Object.values(M.duration_true).forEach(d=>d.rows.forEach(r=>{if(r.dose){(rows[r.dur]=rows[r.dur]||[]).push(r.dose);}}));const ds=Object.keys(rows).map(Number).sort((a,b)=>a-b),gm=ds.map(d=>Math.log10(Math.exp(rows[d].reduce((s,v)=>s+Math.log(v),0)/rows[d].length)));
      ch.line(ds.map(Math.log10),gm,{color:'#C0392B',w:2.2,dash:[6,4]});ch.text('true centre threshold (noise-free)',ch.X(Math.log10(3.0)),ch.Y(3.42),{size:11.5,color:'#C0392B',bold:true});}
    ch.text('no switch at any dose',ch.m.l+6,ch.Y(1.78),{size:11.5,color:'#C0392B'});
    // mini-clips
    const k=Math.max(0,Math.min(K.clips.centre.XX.length/48-1,Math.floor(t)));
    ['centre','tail_end'].forEach(key=>{const cl=K.clips[key],pp=c['p_'+key];pp.clear();pp.scaleBar();const ph=lightWindow(t+1,0,K.dur,K.ramp);drawLight(pp,cl.disc,1.5,ph);
      packedNodes(cl.XX,cl.RR,k,24,K.types,'rho').forEach(n=>pp.node({x:n.x,y:n.y,fill:n.fill,r:0.4}));pp.setSub('dose '+K.dose.toFixed(0)+' · '+cl.cells+' cells'+(t>=100?' · '+(cl.end_other?'<b>switched</b>':'<b>relaxed back</b>'):''));});
  }
});

/* ---------------- 4.3 ---------------- */
Demo.register({id:'4.3',act:4,title:'The switch',data:['data/c43.js'],duration:163,rate:14,truthOffered:true,
  legend:TYPELEG.concat(LEG.light).concat([{color:C.sa,label:'monitor reads state a'},{color:C.sb,label:'state b'}]),
  caption:'One held-out dish (seed 6007), four copies that share every random event (CRN twins): the closed-loop controller, the same dose at a random location, the whole body at the same dose, and the untreated twin. The brief controller light at the body centre flips the collective’s memory for good while no node moves; press T to shade nodes by the hidden memory ρ.',
  takeaway:'A brief, local light flips the collective\'s memory permanently — no node moves.',
  notes:'Panels: controller (episode 988), random location at the controller\'s dose (991), whole body at the controller\'s dose (994, “dose-matched”), untreated twin (989). State bars and V_body badges are the frozen T5 monitor\'s own verdicts; the geometry trace is its worst bound ratio (inside the band ≤ 1). The controller reads the state S+ (= a), pulses at the body centre (r = 1.5, 10 tu, amplitude 1.6, then ×1.1), commits when the excursion passes 0.62 and waits. Truth overlay: node shading by hidden ρ shows the flip spreading out from the lit disc.',
  sources:[{what:'Four arms of held-out dish seed 6007: hidden state per tu, monitor verdicts, actions',file:'t5_blind_control/episodes_heldout/ep_00988…00994.json + testbed_v3/live_sealed_t5/episode_00988…00994/hidden.npz',sec:'logs/heldout_summary.jsonl'},{what:'Controller protocol',file:'t5_blind_control/CONTROLLER.md'},{what:'Arms and dose matching',file:'t5_blind_control/EVALUATION.md',sec:'Headline table'}],
  setup(c){
    const D=DATA.c43;c.state.D=D;c.state.types=D.types;const s=Math.min(Demo.arenaSize(4,0),330);const row=el('div',{style:'display:flex;gap:10px;justify-content:center;flex-wrap:wrap;width:100%'},c.vis);
    c.state.names={ctrl:'Controller',random:'Same dose, random location',whole_dm:'Whole body, same dose',twin:'Untreated CRN twin'};c.state.cols={};
    ['ctrl','random','whole_dm','twin'].forEach(a=>{const arm=D.arms[a];arm.XX=B64.i16(arm.X,1000);arm.RR=B64.i16(arm.rho,20000);const w=el('div',{class:'pw'},row);const p=new Panel(w,{size:s,fov:6,title:c.state.names[a]});p.wrap=w;c.panels.push(p);
      const info=el('div',{style:'min-height:28px;text-align:center'},w);const sb=makeCanvas(w,s,34);const gb=makeCanvas(w,s,44);c.state.cols[a]={p:p,info:info,sb:sb,gb:gb};});
    // pause schedule from the data
    const ct=D.arms.ctrl,commit=ct.decisions.find(d=>d.action==='commit'),rho=ct.RR,N=24;const mean=k=>{let m=0;for(let i=0;i<N;i++)m+=rho[k*N+i];return m/N;};
    let cross=null;for(let k=1;k<ct.T;k++){if(mean(k)<0.5){cross=k;break;}}const tp=(arm)=>{const R=D.arms[arm].RR;let bk=0,bv=0;for(let k=0;k<D.arms[arm].T;k++){let m=0;for(let i=0;i<N;i++)m+=R[k*N+i];m/=N;const dv=Math.abs(m-mean(0));if(dv>bv){bv=dv;bk=k;}}return bk;};
    const first=ct.acts[0],lastEnd=ct.acts[ct.acts.length-1].t+ct.acts[ct.acts.length-1].dur;
    const P=[{t:first.t,text:'All four identical: shared noise (CRN twins).',anchor:()=>({panel:c.state.cols.twin.p,x:0,y:2.2})},
      {t:first.t+3,text:'Light at the body centre.',anchor:()=>({panel:c.state.cols.ctrl.p,x:first.xy[0],y:first.xy[1]})},
      {t:first.t+7,text:'No node moves — the geometry trace stays flat.',anchor:()=>({px:pageAnchor(c.state.cols.ctrl.gb,c.state.cols.ctrl.gb.clientWidth*0.2,19)})},
      {t:commit?commit.t:46,text:'Tipping point passed — light off.',anchor:()=>({panel:c.state.cols.ctrl.p,x:first.xy[0],y:first.xy[1]})},
      {t:Math.max((cross||70)+4,(commit?commit.t:46)+4),text:'After release the collective finishes the switch by itself.',anchor:()=>({panel:c.state.cols.ctrl.p,x:-1.5,y:1.5})},
      {t:Math.max(tp('random'),(commit?commit.t:46)+6),text:'Same dose elsewhere: a small excursion, then back.',anchor:()=>({panel:c.state.cols.random.p,x:D.arms.random.acts[0].xy[0],y:D.arms.random.acts[0].xy[1]})},
      {t:Math.max(tp('random'),(commit?commit.t:46)+6)+0.5,text:'Whole body at the same dose: spread thin, nothing.',anchor:()=>({panel:c.state.cols.whole_dm.p,x:0,y:2.4})},
      {t:ct.T-1,text:'Held through the release window.',anchor:()=>({panel:c.state.cols.ctrl.p,x:0,y:-2.2})}];
    P.sort((a,b)=>a.t-b.t);c.def.pauses=P;Demo.byId['4.3'].pauses=P;},
  draw(c,t,truth){
    const D=c.state.D,N=24;['ctrl','random','whole_dm','twin'].forEach(a=>{const arm=D.arms[a],col=c.state.cols[a],p=col.p,k=Math.max(0,Math.min(arm.T-1,Math.floor(t)));p.clear();p.scaleBar();
      arm.acts.forEach(ac=>{const ph=lightWindow(t,ac.t,ac.t+ac.dur,ac.ramp);if(ac.whole){if(ph>0.001){const g=p.ctx;g.save();g.fillStyle='rgba(255,255,255,'+(0.35*ph)+')';g.fillRect(0,0,p.w,p.h);g.strokeStyle=C.ink;g.lineWidth=2;g.setLineDash([8,5]);g.strokeRect(2,2,p.w-4,p.h-4);g.restore();}}else drawLight(p,ac.xy,ac.r,ph);});
      packedNodes(arm.XX,arm.RR,k,N,D.types,truth?'rho':'type').forEach(n=>p.node({x:n.x,y:n.y,fill:n.fill,r:0.4}));
      const dose=arm.acts.filter(ac=>ac.t<=t+1e-9).reduce((s,ac)=>s+ac.dose,0);const V=arm.V[k],st=arm.state[k];
      col.info.innerHTML=badge('V_body '+(V?'true':'false'),V?'ok':'bad')+badge('dose so far '+dose.toFixed(0),'neu')+badge('state '+(st==='S+'?'a':st==='S-'?'b':'…'),'neu');
      const g=col.sb.getContext('2d'),dpr=1,w=col.sb.width,h=col.sb.height;g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,w,h);g.fillStyle='#fff';g.fillRect(0,0,w,h);for(let j=0;j<=k;j++){const s=arm.state[j];g.fillStyle=s==='S+'?C.sa:s==='S-'?C.sb:'#BBB';g.fillRect(Math.floor(j/arm.T*w),18,Math.ceil(w/arm.T)+1,h-20);}g.strokeStyle='#999';g.strokeRect(0.5,17.5,w-1,h-19);g.fillStyle=C.ink;g.font='11.5px '+FONT;g.textBaseline='top';g.fillText('monitor state over time',2,2);
      const gc=col.gb.getContext('2d'),gw=col.gb.width,gh=col.gb.height;gc.setTransform(1,0,0,1,0,0);gc.clearRect(0,0,gw,gh);gc.fillStyle='#fff';gc.fillRect(0,0,gw,gh);const gy0=18,gh2=gh-22;gc.fillStyle=C.band;gc.fillRect(0,gy0+gh2/2,gw,gh2/2);gc.strokeStyle='#222';gc.lineWidth=1.8;gc.beginPath();for(let j=0;j<=k;j++){const x=j/arm.T*gw,y=gy0+gh2-Math.min(arm.geo[j],2)/2*gh2;j?gc.lineTo(x,y):gc.moveTo(x,y);}gc.stroke();gc.fillStyle=C.ink;gc.font='11.5px '+FONT;gc.textBaseline='top';gc.fillText('geometry trace (grey band = inside)',2,2);});
  }
});

/* ---------------- 4.4 ---------------- */
Demo.register({id:'4.4',act:4,title:'Held-out results — and one failure',data:['data/c44stats.js','data/c44worst.js'],duration:330,rate:28,truthOffered:false,
  legend:TYPELEG.concat(LEG.rho.slice(0,1)).slice(0,4).concat([{color:C.sa,label:'hidden memory → a'},{color:C.sb,label:'→ b'}]),
  caption:'60 held-out dishes: the controller succeeds in 93 % with the body intact, far better than random placement at the same dose and 3.7× cheaper than lighting everything, though a well-tuned fixed pulse does just as well. The dot plot shows each dish\'s dose relative to the true minimum. One failure (bottom right): the controller committed too early.',
  takeaway:'93 % success with the body intact; far better than random placement and 3.7× cheaper than lighting everything — and a well-tuned fixed pulse does just as well.',
  notes:'Success = state change held ≥ 120 tu after the last action, last 40 tu sure, V_body_conservative true (T5 rule). Audited truth (AUDIT_T5 A1): the 4 monitor misses are one natural cohesion false alarm (dish 6040: true body fine) and one late random-arm switch; true success ctrl 95 % (57/60 switched, 3 true failures). Regret = dose used / true minimal dose for the same protocol (A3). The worst controller episode is seed 6026: the commit rule fired at progress 0.63 when the collective was still on the start side (mean ρ 0.56), the response relapsed and un-commit only triggered 60 tu later.',
  audit:'Uses audited values: true success 95 % for the controller (monitor 93 %); the single V_body miss is a monitor false alarm (AUDIT_T5 A1/A2).',
  sources:[{what:'Success (dish-clustered 95 % CI) and dose by arm, n = 60 dishes',file:'t5_blind_control/logs/heldout_eval.json',sec:'table'},{what:'Regret: dose used / true minimal dose (per dish, controller and fixed pulse)',file:'testbed_v3/audit_t5/REGRET_AND_MAPS.json',sec:'AUDIT_T5 A3'},{what:'Worst controller episode (seed 6026)',file:'testbed_v3/live_sealed_t5/episode_01121/hidden.npz + t5_blind_control/episodes_heldout/ep_01121.json'}],
  setup(c){
    const S=DATA.c44stats,W=DATA.c44worst;c.state.S=S;c.state.W=W;const sz=Math.min(Demo.arenaSize(2,0),420);const top=el('div',{style:'display:flex;gap:14px;flex-wrap:wrap;justify-content:center;width:100%'},c.vis);
    const l=el('div',{class:'pw'},top);el('div',{class:'ptitle'},l,'Success and dose by arm (60 held-out dishes)');c.cvA=makeCanvas(l,640,Math.round(sz*0.62));c.cvH=Math.round(sz*0.62);
    el('div',{class:'ptitle',style:'margin-top:8px'},l,'Regret: dose used / true minimal dose (each dot = one dish)');c.cvB=makeCanvas(l,640,Math.round(sz*0.45));c.cvH2=Math.round(sz*0.45);
    const w=el('div',{class:'pw'},top);c.pw=new Panel(w,{size:sz+60,fov:6.5,title:'Worst controller episode (seed 6026)'});c.pw.wrap=w;c.panels.push(c.pw);W.arm.XX=B64.i16(W.arm.X,1000);W.arm.RR=B64.i16(W.arm.rho,20000);
    c.state.st=makeCanvas(w,sz+60,36);c.state.st.style.marginTop='4px';
    const un=W.arm.decisions.find(d=>d.action==='uncommit'),cm=W.arm.decisions.find(d=>d.action==='commit');
    c.def.pauses=[{t:(cm?cm.t:46)+2,text:'Commit fired while the collective was still on the start side.',anchor:()=>({panel:c.pw,x:W.arm.acts[0].xy[0],y:W.arm.acts[0].xy[1]})},{t:(un?un.t:104)+3,text:'Committed too early: the collective relaxed back.',anchor:()=>({panel:c.pw,x:0,y:-2.4})}];Demo.byId['4.4'].pauses=c.def.pauses;},
  draw(c,t){
    const S=c.state.S,W=c.state.W,ch=new Chart(c.cvA,{w:640,h:c.cvH,xlim:[0,1.3],ylim:[0,S.arms.length],m:{l:190,r:130,t:22,b:26},xticks:[0,0.25,0.5,0.75,1],yticks:[],title:'success rate (bars, 95 % CI) · mean dose per dish (right)'});ch.clear();ch.axes();
    const g=ch.c,rowH=(ch.h-ch.m.t-ch.m.b)/S.arms.length;S.arms.forEach((a,i)=>{const yc=ch.m.t+rowH*(i+0.5),x0=ch.X(0),x1=ch.X(a.success);g.fillStyle=a.name==='Controller'?'#222':'#8a8a8a';g.fillRect(x0,yc-rowH*0.28,x1-x0,rowH*0.56);g.strokeStyle='#C0392B';g.lineWidth=2;g.beginPath();g.moveTo(ch.X(a.ci[0]),yc);g.lineTo(ch.X(a.ci[1]),yc);g.moveTo(ch.X(a.ci[0]),yc-6);g.lineTo(ch.X(a.ci[0]),yc+6);g.moveTo(ch.X(a.ci[1]),yc-6);g.lineTo(ch.X(a.ci[1]),yc+6);g.stroke();
      g.fillStyle=C.ink;g.font=(a.name==='Controller'?'700 ':'')+'13px '+FONT;g.textAlign='right';g.textBaseline='middle';g.fillText(a.name,ch.m.l-8,yc);g.textAlign='left';g.fillText((a.success*100).toFixed(0)+' %',ch.X(1.0)+30,yc-8);g.fillStyle=C.mute;g.font='12px '+FONT;g.fillText('dose '+a.dose.toFixed(0),ch.X(1.0)+30,yc+8);});
    const R=c.cvB,rc=new Chart(R,{w:640,h:c.cvH2,xlim:[Math.log10(0.3),Math.log10(12)],ylim:[0,2],m:{l:110,r:20,t:22,b:30},xticks:[0.5,1,2,5,10].map(Math.log10),yticks:[],xfmt:v=>String(+Math.pow(10,v).toFixed(1))+'×',title:'regret = dose used / true minimal dose (1× = exactly the minimum)'});rc.clear();rc.axes();rc.vline(0,{color:'#999',dash:[4,3]});
    [['controller',S.regret.ctrl,0.5,C.ink],['fixed pulse',S.regret.fixed,1.5,'#777']].forEach(a=>{const v=a[1];rc.text(a[0],rc.m.l-8,rc.Y(a[2]),{align:'right',size:13,bold:true});v.forEach((x,i)=>{if(x>0)rc.dot(Math.log10(x),a[2]+((i*0.37)%0.5-0.25)*0.7,{color:a[3],r:3.2,stroke:'rgba(255,255,255,.8)'});});const md=v.slice().sort((p,q)=>p-q)[Math.floor(v.length/2)];rc.vline(Math.log10(md),{color:a[3],w:2});rc.text('median '+md.toFixed(2)+'×',rc.X(Math.log10(md))+4,rc.Y(a[2])-22,{size:11.5,color:a[3],bold:true});});
    // worst clip
    const arm=W.arm,k=Math.max(0,Math.min(arm.T-1,Math.floor(t))),p=c.pw;p.clear();p.scaleBar();arm.acts.forEach(ac=>drawLight(p,ac.xy,ac.r,lightWindow(t,ac.t,ac.t+ac.dur,ac.ramp)));packedNodes(arm.XX,arm.RR,k,24,W.types,'rho').forEach(n=>p.node({x:n.x,y:n.y,fill:n.fill,r:0.4}));
    const V=arm.V[k];p.setSub('t = '+t.toFixed(0)+' tu · '+badge('V_body '+(V?'true':'false'),V?'ok':'bad')+badge('failure: time limit, never held','bad'));
    const gs=c.state.st.getContext('2d'),w=c.state.st.width,h=c.state.st.height;gs.setTransform(1,0,0,1,0,0);gs.fillStyle='#fff';gs.fillRect(0,0,w,h);for(let j=0;j<=k;j++){const s=arm.state[j];gs.fillStyle=s==='S+'?C.sa:s==='S-'?C.sb:'#BBB';gs.fillRect(Math.floor(j/arm.T*w),18,Math.ceil(w/arm.T)+1,h-20);}gs.strokeStyle='#999';gs.strokeRect(0.5,17.5,w-1,h-19);gs.fillStyle=C.ink;gs.font='11.5px '+FONT;gs.textBaseline='top';gs.fillText('monitor state over time (blue = a, purple = b)',2,2);
  }
});

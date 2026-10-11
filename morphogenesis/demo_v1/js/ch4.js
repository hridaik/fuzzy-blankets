/* Act 4 - Control (4.1 - 4.5) */
'use strict';
function packedNodes(X,R,k,N,types,mode,xoff){const nodes=[];for(let i=0;i<N;i++){const rho=R?R[k*N+i]:0.5;nodes.push({x:X[(k*N+i)*2],y:X[(k*N+i)*2+1],type:types?types[i]:1,rho:rho,fill:mode==='rho'?rhoColor(rho):TYPEC[types[i]]});}return nodes;}
const GREYS=(d,lo,hi)=>{const u=Math.max(0,Math.min(1,(d-lo)/(hi-lo)));const g=Math.round(238-205*u);return 'rgb('+g+','+g+','+g+')';};
const DOSELEG=[{color:'#EEEEEE',label:'least light'},{color:'#9C9C9C',label:'about 3 times more'},{color:'#353535',label:'5 times more or beyond'}];
/* ---------------- 4.1 ---------------- */
const MECH41={L1:'makes cells move faster',L2:'changes the body signals',L3:'adds blue signal: pink → blue only',L4:'adds pink signal: blue → pink only',L5:'makes cells sense more strongly'};
const VERD41={'state flipped':['flips the state','ok'],'no effect':['no flip','neu'],'damage':['changes the body','bad']};
Demo.register({id:'4.1',act:4,title:COPY['4.1'].title,data:['data/c41.js'],duration:100,rate:7,truthOffered:false,
  legend:LEG.rho.concat(LEG.light),
  caption:COPY['4.1'].caption,takeaway:COPY['4.1'].takeaway,
  notes:'Dose = amplitude 5 x duration 10 x 6 cells = 300 for every light. Row a and row b are the same body (dev seed 5001; b is its clone in state b), re-simulated deterministically from t = 20 (T5 B1 protocol, now with hidden rho). Badges use the declared rule: damage = more than one linked group or a cell displaced > 2 units vs the untreated twin; flipped = mean rho ends on the other side. L5 at this dose makes the engine itself diverge. Truth (AUDIT_T5 A5): L1 migration gain, L2 structural secretion, L3 memory-ligand-A secretion (pushes b → a only), L4 memory-ligand-B secretion (a → b only), L5 receptor gain. Display names: Light n = Ln; blue/pink state = state a/b.',
  audit:'AUDIT_T5 A5.',
  sources:[{what:'Five-light screening at the body centre (amp 5, 10 tu), both start states',file:'demo_v1/data/c41.js',sec:'build/build_ch4a.py (T5 B1 protocol, seed 5001)'},{what:'True mechanism of L1–L5 and one-directionality of L3/L4',file:'testbed_v3/audit_t5/AUDIT_T5.md',sec:'A5'}],
  setup(c){
    const D=DATA.c41;c.state.D=D;c.state.reveal=false;const s=Math.min(Demo.arenaSize(5,0),250);
    c.state.panels={};['a','b'].forEach((st,ri)=>{const row=el('div',{style:'display:flex;gap:10px;justify-content:center;align-items:flex-start;width:100%'},c.vis);const lab=el('div',{style:'width:110px;font-weight:700;font-size:15px;padding-top:30px;text-align:right'},row,COPY['4.1'].rows[ri]);
      c.state.panels[st]=D.rows[st].clips.map((cl,i)=>{const w=el('div',{class:'pw'},row);const p=new Panel(w,{size:s,fov:6.5,title:'Light '+cl.label.slice(1)});p.wrap=w;c.panels.push(p);p.noBubble=false;cl.XX=B64.i16(cl.X,1000);cl.RR=B64.i16(cl.rho,20000);return p;});});
    const b=el('button',{class:'btn'},c.ctrls,COPY['4.1'].button);b.onclick=()=>{c.state.reveal=!c.state.reveal;b.classList.toggle('on',c.state.reveal);Demo.redraw();};
    const fa=D.rows.a.clips.findIndex(x=>x.verdict==='state flipped'),fb=D.rows.b.clips.findIndex(x=>x.verdict==='state flipped');const ot=D.rows.a.clips.findIndex(x=>x.verdict==='no effect');
    Demo.byId['4.1'].pauses=[{t:14,text:COPY['4.1'].callouts[0],side:'top',anchor:cc=>({panel:cc.state.panels.a[fa],x:0,y:0})},{t:15,text:COPY['4.1'].callouts[1],side:'top',anchor:cc=>({panel:cc.state.panels.b[1],x:0,y:0})}];Demo.buildTicks();},
  draw(c,t){
    const D=c.state.D,k=Math.max(0,Math.min(D.params.T-1,Math.floor(t)));const done=t>=14;
    ['a','b'].forEach(st=>{D.rows[st].clips.forEach((cl,i)=>{const p=c.state.panels[st][i],types=D.rows[st].types;p.clear();p.scaleBar();
      const ph=lightWindow(t+1,0,10,2.5);drawLight(p,cl.disc,1.5,ph);const nodes=packedNodes(cl.XX,cl.RR,k,24,types,'rho');nodes.forEach(n=>p.node({x:n.x,y:n.y,fill:n.fill,r:0.4}));
      const v=VERD41[cl.verdict]||[cl.verdict,'neu'];p.setSub((done?badge(v[0],v[1]):'<span class="badge neu">…</span>')+(c.state.reveal?'<div style="max-width:'+p.w+'px;font-size:12px;margin-top:3px">'+MECH41[cl.label]+'</div>':''));});});}
});

/* ---------------- 4.2 ---------------- */
Demo.register({id:'4.2',act:4,title:COPY['4.2'].title,data:['data/c42map.js','data/c42clips.js'],duration:120,rate:9,truthOffered:true,
  legend:LEG.types.concat(DOSELEG),
  caption:COPY['4.2'].caption,takeaway:COPY['4.2'].takeaway,
  notes:'T5’s “head” (+p) disc sits on the TAIL end of the body and its “tail” disc on the head end: its body axis e1 points head → tail (AUDIT_T5 A4). Relative doses (amplitude x duration x cells at 20–40 tu, same dish): middle 1x, side 1.2x, head end (“T5 tail”) 1.8x, tail end (“T5 head”) 4.0x. True per-place thresholds (SWITCH_V3, 26.7-tu pulses): best place 233, median 260, worst corner 1,387; threshold amplitude falls with the kernel connectivity of the lit disc (Spearman −0.98). No threshold for pulses shorter than l*/g ≈ 3.8 tu; T5 measured: 2 tu never, 5 tu needs 3–4x the dose. Mini-clips: deterministic re-simulation of dev dish 5004 at equal dose (middle 7 cells, tail end 6 cells).',
  audit:'AUDIT_T5 A4: T5’s “head” disc is the true tail end, its “tail” disc the true head end.',
  sources:[{what:'T5 blind dose map (4 dishes)',file:'t5_blind_control/logs/b2_results.jsonl',sec:'dose_star; SYSID.md B2'},{what:'True body-frame location of the discs; true thresholds; connectivity rule',file:'testbed_v3/audit_t5/data/a4_location.json',sec:'AUDIT_T5 A4'},{what:'True duration curve',file:'testbed_v3/audit_t5/data/a4b_duration.json'},{what:'Equal-dose mini-clips',file:'demo_v1/data/c42clips.js',sec:'build/build_ch4a.py'}],
  setup(c){
    const M=DATA.c42map,K=DATA.c42clips;c.state.M=M;c.state.K=K;c.state.XS=M.template.xy;const sz=Math.min(Demo.arenaSize(2,0),560);
    const top=el('div',{style:'display:flex;gap:14px;flex-wrap:wrap;justify-content:center;width:100%'},c.vis);
    const pw=el('div',{class:'pw'},top);c.pm=new Panel(pw,{size:sz,fov:5.2,title:'How much light was needed',cx:0.2});c.pm.wrap=pw;c.panels.push(c.pm);
    const right=el('div',{class:'pw'},top);el('div',{class:'ptitle'},right,'Light needed against how long it stays on');c.cv=makeCanvas(right,600,Math.round(sz*0.52));
    const row=el('div',{style:'display:flex;gap:14px;justify-content:center;margin-top:6px'},right);
    ['centre','tail_end'].forEach(k=>{const w=el('div',{class:'pw'},row);const p=new Panel(w,{size:Math.round(sz*0.44),fov:6.2,title:k==='centre'?COPY['4.2'].clips[0]:COPY['4.2'].clips[1]});p.wrap=w;p.id=k;c.panels.push(p);c['p_'+k]=p;K.clips[k].XX=B64.i16(K.clips[k].X,1000);K.clips[k].RR=B64.i16(K.clips[k].rho,20000);});
    c.cvH=Math.round(sz*0.52);},
  draw(c,t,truth){
    const M=c.state.M,K=c.state.K,p=c.pm;p.clear();p.scaleBar();const XS=c.state.XS;
    XS.forEach((q,i)=>p.node({x:q[0],y:q[1],fill:TYPEC[M.template.type.length?({head:1,trunk:2,limb:3,tail:4})[M.template.type[i]]:1],r:0.42,alpha:0.45}));
    if(!truth){const names={C:'Middle',side:'Side',tail:'Head end',head:'Tail end'};const rel=M.blind_rel_same_dish;const lp={C:[0,-2.15],side:[0,3.45],tail:[-3,-2.15],head:[3.1,-2.15]};
      ['C','side','tail','head'].forEach(k=>{const q=M.blind_centres[k],d=rel[k];const g=p.ctx,pp=p.w2p(q[0],q[1]);g.save();g.fillStyle=GREYS(d,1,5);g.globalAlpha=0.55;g.beginPath();g.arc(pp[0],pp[1],1.5*p.scale,0,6.3);g.fill();g.globalAlpha=1;g.strokeStyle=C.ink;g.setLineDash([6,4]);g.lineWidth=1.6;g.stroke();g.restore();
        p.label(names[k]+'  '+d.toFixed(1)+'×',lp[k][0],lp[k][1],{align:'center',bold:true,size:13,world:true,bg:true});});
      p.setTitle('How much light was needed');p.setSub('');}
    else{const T=M.true['16g'];const best=Math.min(...T.map(r=>r.dose));T.forEach(r=>{const d=r.dose/best,pp=p.w2p(r.xy[0],r.xy[1]),g=p.ctx;g.save();g.fillStyle=GREYS(d,1,6);g.globalAlpha=0.85;g.beginPath();g.arc(pp[0],pp[1],0.5*p.scale,0,6.3);g.fill();g.globalAlpha=1;g.strokeStyle=C.ink;g.lineWidth=1;g.stroke();g.restore();p.label(d.toFixed(1),pp[0],pp[1],{align:'center',size:11.5,bold:true,color:d>2.8?'#fff':C.ink});});
      p.setTitle('True light needed at each place (hidden truth)');p.setSub('relative to the cheapest place');}
    // chart: dose vs duration, log-log
    const durs=[2,5,10,20,40],ch=new Chart(c.cv,{w:600,h:c.cvH,xlim:[Math.log10(1.6),Math.log10(60)],ylim:[1.6,3.5],m:{l:52,r:12,t:22,b:36},xticks:durs.map(Math.log10),yticks:[2,2.5,3,3.5],xfmt:v=>String(Math.round(Math.pow(10,v))),yfmt:v=>String(Math.round(Math.pow(10,v))),xlabel:'time units the light is on'});ch.clear();
    const wall=Math.log10(3.8);ch.c.save();ch.c.fillStyle='rgba(192,57,43,.10)';ch.c.fillRect(ch.m.l,ch.m.t,ch.X(wall)-ch.m.l,ch.h-ch.m.t-ch.m.b);ch.c.restore();ch.axes();ch.vline(wall,{color:'#C0392B',dash:[5,3],label:'shorter flashes never work'});
    const col={C:'#222',side:'#777',tail:'#999',head:'#444'},dash={C:null,side:null,tail:[4,3],head:[2,3]};
    ['C','side','tail','head'].forEach(k=>{const xs=[],ys=[];[10,20,40].forEach(d=>{const v=M.blind_dose[k+'|'+d+'.0'];if(v){xs.push(Math.log10(d));ys.push(Math.log10(v));}});if(k==='C'&&M.blind_dose['C|5.0']){xs.unshift(Math.log10(5));ys.unshift(Math.log10(M.blind_dose['C|5.0']));}ch.line(xs,ys,{color:col[k],w:2.4,dash:dash[k]});xs.forEach((x,i)=>ch.dot(x,ys[i],{color:col[k],r:3.5}));
      ch.text({C:'Middle',side:'Side',tail:'Head end',head:'Tail end'}[k],ch.X(xs[xs.length-1])+6,ch.Y(ys[ys.length-1]),{size:11.5,color:col[k],bold:true});});
    if(M.duration_true){const rows={};Object.values(M.duration_true).forEach(d=>d.rows.forEach(r=>{if(r.dose){(rows[r.dur]=rows[r.dur]||[]).push(r.dose);}}));const ds=Object.keys(rows).map(Number).sort((a,b)=>a-b),gm=ds.map(d=>Math.log10(Math.exp(rows[d].reduce((s,v)=>s+Math.log(v),0)/rows[d].length)));
      ch.line(ds.map(Math.log10),gm,{color:'#C0392B',w:2.2,dash:[6,4]});ch.text('true minimum, middle',ch.X(Math.log10(3.0)),ch.Y(3.42),{size:11.5,color:'#C0392B',bold:true});}
    ch.text('no switch at any strength',ch.m.l+6,ch.Y(1.78),{size:11.5,color:'#C0392B'});
    // mini-clips
    const k=Math.max(0,Math.min(K.clips.centre.XX.length/48-1,Math.floor(t)));
    ['centre','tail_end'].forEach(key=>{const cl=K.clips[key],pp=c['p_'+key];pp.clear();pp.scaleBar();const ph=lightWindow(t+1,0,K.dur,K.ramp);drawLight(pp,cl.disc,1.5,ph);
      packedNodes(cl.XX,cl.RR,k,24,K.types,'rho').forEach(n=>pp.node({x:n.x,y:n.y,fill:n.fill,r:0.4}));pp.setSub(t>=100?(cl.end_other?'<b>switched</b>':'<b>fell back</b>'):'');});
  }
,
  pauses:[{t:3,text:COPY['4.2'].callouts[0],side:'left',anchor:c=>({panel:c.pm,x:c.state.M.blind_centres.C[0],y:c.state.M.blind_centres.C[1]})},
          {t:50,text:COPY['4.2'].callouts[1],side:'left',anchor:c=>({panel:c.pm,x:c.state.M.blind_centres.head[0],y:c.state.M.blind_centres.head[1]})},
          {t:110,text:COPY['4.2'].callouts[2],side:'left',anchor:c=>({px:pageAnchor(c.cv,52+(Math.log10(3.8)-Math.log10(1.6))/(Math.log10(60)-Math.log10(1.6))*(600-52-12),60)})}]
});

/* ---------------- 4.3 (new) ---------------- */
function fitMap(pts,w,h,pad){let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;pts.forEach(p=>{x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);});
  const s=Math.min((w-2*pad)/(x1-x0),(h-2*pad)/(y1-y0));const cx=(x0+x1)/2,cy=(y0+y1)/2;return {s:s,f:p=>[w/2+(p[0]-cx)*s,h/2-(p[1]-cy)*s]};}
function cellDot(g,q,r,fill,o){o=o||{};g.save();g.fillStyle=fill;g.strokeStyle='rgba(0,0,0,.45)';g.lineWidth=1;g.beginPath();g.arc(q[0],q[1],r,0,6.3);g.fill();g.stroke();if(o.hl){g.strokeStyle=C.ink;g.lineWidth=3;g.beginPath();g.arc(q[0],q[1],r+6,0,6.3);g.stroke();}g.restore();}
function arrowPx(g,a,b,w,col,dash){g.save();g.strokeStyle=col||C.ink;g.fillStyle=col||C.ink;g.lineWidth=w;if(dash)g.setLineDash(dash);g.beginPath();g.moveTo(a[0],a[1]);g.lineTo(b[0],b[1]);g.stroke();g.setLineDash([]);const an=Math.atan2(b[1]-a[1],b[0]-a[0]),h=Math.max(8,w*2.2);g.beginPath();g.moveTo(b[0],b[1]);g.lineTo(b[0]-h*Math.cos(an-.4),b[1]-h*Math.sin(an-.4));g.lineTo(b[0]-h*Math.cos(an+.4),b[1]-h*Math.sin(an+.4));g.closePath();g.fill();g.restore();}
function wrapBlock(g,txt,x,y,w,lh){wrapText(g,txt,w).forEach((ln,i)=>g.fillText(ln,x,y+i*lh));}
Demo.register({id:'4.3',act:4,title:COPY['4.3'].title,data:['data/body2100.js'],duration:0,truthOffered:false,
  legend:LEG.types.concat(LEG.light),
  caption:COPY['4.3'].caption,takeaway:COPY['4.3'].takeaway,
  notes:'Outline = alpha hull of the member set (geometric; found in Act 3). Blanket = a cell’s sensory + active states; inside the organism the memory module is separated from the body module: structure never reads the memory ligands (bit-identical under any memory intervention, MEMORY_V3 H0). Interface = where an intervention couples in; arrow width = sum over lit cells of exp(−distance) for each unlit cell (kernel coupling across the disc edge), same scale in both discs. Middle disc = template position (0,0), tail-end disc = (3,0) (the disc T5 called “head”), r = 1.5; cell positions are a settled frame of body 2100 mapped to the template by a rigid fit of the believed places (AUDIT_T5 A4: connectivity vs threshold Spearman −0.98).',
  sources:[{what:'Body frame (positions, places) used for all three panels',file:'testbed_v3/data/raw_v4/natural/a_cal_2100.pkl',sec:'frame 3000'},{what:'Coupling rule and its link to the dose map',file:'testbed_v3/audit_t5/AUDIT_T5.md',sec:'A4'}],
  setup(c){
    const B=decodeBody();const P=B.pos(30);const A=[],Q=[];for(let i=0;i<24;i++){A.push(B.tmplXY[B.place[i]]);Q.push(P[i]);}
    const f=kabsch2(A,Q);c.state.B=B;c.state.P=P;c.state.f=f;
    const row=el('div',{style:'display:flex;gap:16px;justify-content:center;flex-wrap:wrap;width:100%'},c.vis);const W=400,H=440;c.state.cv=[];
    COPY['4.3'].panels.forEach((pn,i)=>{const w=el('div',{class:'pw',style:'max-width:'+W+'px'},row);el('div',{class:'ptitle'},w,pn[0]);const cv=makeCanvas(w,W,H);c.state.cv.push(cv);const tx=el('div',{style:'font-size:14.5px;line-height:1.35;margin-top:6px;max-width:'+W+'px'},w,pn[1]);});
  },
  draw(c){
    const B=c.state.B,P=c.state.P,f=c.state.f,W=400,H=440,d=Math.min(window.devicePixelRatio||1,2);
    const prep=(cv)=>{cv.width=W*d;cv.height=H*d;cv.style.width=W+'px';cv.style.height=H+'px';const g=cv.getContext('2d');g.setTransform(d,0,0,d,0,0);g.fillStyle='#EDEDE8';g.fillRect(0,0,W,H);return g;};
    // (a) outline
    {const g=prep(c.state.cv[0]);const m=fitMap(P,W,H,50);P.forEach((p,i)=>cellDot(g,m.f(p),0.4*m.s,TYPEC[B.types[i]]));
      const E=alphaEdges(P,1.5);g.strokeStyle=C.ink;g.lineWidth=3.4;g.beginPath();E.forEach(e=>{const a=m.f(P[e[0]]),b=m.f(P[e[1]]);g.moveTo(a[0],a[1]);g.lineTo(b[0],b[1]);});g.stroke();}
    // (b) blanket
    {const g=prep(c.state.cv[1]);const sub=P.map(p=>p);const m=fitMap(P,W,H*0.62,40);const sel=11;
      P.forEach((p,i)=>cellDot(g,m.f(p),0.4*m.s,i===sel?TYPEC[B.types[i]]:'#CFCFCA',{hl:i===sel}));
      const q=m.f(P[sel]);const ins=P.map((p,i)=>i).filter(i=>i!==sel&&dist(P[i],P[sel])<2.2).slice(0,3);
      ins.forEach(i=>{const a=m.f(P[i]),u=[q[0]-a[0],q[1]-a[1]],L=Math.hypot(u[0],u[1]);arrowPx(g,[a[0]+u[0]/L*0.5*m.s,a[1]+u[1]/L*0.5*m.s],[q[0]-u[0]/L*0.62*m.s,q[1]-u[1]/L*0.62*m.s],3,'#555');});
      [[-1,-1],[1,-1],[0,1]].forEach(v=>{const L=Math.hypot(v[0],v[1]);arrowPx(g,[q[0]+v[0]/L*0.75*m.s,q[1]+v[1]/L*0.75*m.s],[q[0]+v[0]/L*1.45*m.s,q[1]+v[1]/L*1.45*m.s],3,C.ink);});
      g.fillStyle=C.ink;g.font='700 13px '+FONT;g.textAlign='left';g.fillText('senses (in)',q[0]-0.95*m.s*2.1-6,q[1]-0.2*m.s);g.fillText('actions (out)',q[0]+1.6*m.s,q[1]+1.5*m.s);
      const by=H*0.66,bh=64,bw=170;const bx=[18,W-18-bw];
      [['body signals and shape',bx[0]],['memory signals',bx[1]]].forEach(b=>{g.fillStyle='#fff';g.strokeStyle=C.ink;g.lineWidth=2;g.beginPath();g.roundRect(b[1],by,bw,bh,8);g.fill();g.stroke();g.fillStyle=C.ink;g.font='700 14px '+FONT;g.textAlign='center';g.textBaseline='middle';wrapText(g,b[0],bw-16).forEach((ln,i,arr)=>g.fillText(ln,b[1]+bw/2,by+bh/2+(i-(arr.length-1)/2)*18));});
      arrowPx(g,[bx[1]-4,by+bh/2],[bx[0]+bw+6,by+bh/2],3.2,'#777',[7,5]);const mx=(bx[0]+bw+bx[1])/2;g.strokeStyle='#C0392B';g.lineWidth=5;g.beginPath();g.moveTo(mx-14,by+bh/2-14);g.lineTo(mx+14,by+bh/2+14);g.moveTo(mx+14,by+bh/2-14);g.lineTo(mx-14,by+bh/2+14);g.stroke();
      g.fillStyle=C.ink;g.font='700 14px '+FONT;g.textAlign='center';g.textBaseline='top';wrapBlock(g,'the body never listens to the memory',W/2,by+bh+14,W-40,18);}
    // (c) interface
    {const g=prep(c.state.cv[2]);const discs=[{ctr:f([0,0]),big:true},{ctr:f([3,0]),big:false}];const R=1.5;
      const coup=(ctr)=>P.map((p,j)=>{if(dist(p,ctr)<R)return -1;let s=0;P.forEach(q=>{if(dist(q,ctr)<R)s+=Math.exp(-dist(p,q));});return s;});
      const cs=discs.map(d=>coup(d.ctr));const cmax=Math.max(...cs.flat());
      const draw1=(g,ox,oy,w,h,d,cp,scaleW)=>{const m=fitMap(P,w,h,34);const F=p=>{const q=m.f(p);return [q[0]+ox,q[1]+oy];};
        P.forEach((p,i)=>cellDot(g,F(p),0.4*m.s,dist(p,d.ctr)<R?'#F4F4F4':TYPEC[B.types[i]]));
        const cq=F(d.ctr);g.save();g.fillStyle='rgba(255,255,255,.38)';g.strokeStyle=C.ink;g.setLineDash([6,4]);g.lineWidth=1.8;g.beginPath();g.arc(cq[0],cq[1],R*m.s,0,6.3);g.fill();g.stroke();g.restore();
        P.forEach((p,j)=>{const cj=cp[j];if(cj<0.04*cmax)return;const u=[p[0]-d.ctr[0],p[1]-d.ctr[1]],L=Math.hypot(u[0],u[1]);const a=F([d.ctr[0]+u[0]/L*R,d.ctr[1]+u[1]/L*R]),b=F([p[0]-u[0]/L*0.45,p[1]-u[1]/L*0.45]);arrowPx(g,a,b,Math.max(1,cj/cmax*9*scaleW),C.ink);});};
      draw1(g,0,0,W,H*0.6,discs[0],cs[0],1);g.fillStyle='#EDEDE8';
      draw1(g,W*0.2,H*0.62,W*0.6,H*0.36,discs[1],cs[1],0.8);
      g.fillStyle=C.ink;g.font='700 13px '+FONT;g.textAlign='left';g.textBaseline='top';g.fillText('thicker arrow = more contact',10,H*0.6-4);}
  }
});

/* ---------------- 4.3 ---------------- */
Demo.register({id:'4.4',act:4,title:COPY['4.4'].title,data:['data/c43.js'],duration:163,rate:14,truthOffered:true,
  legend:LEG.types.concat(LEG.light).concat([{color:C.sa,label:'blue state'},{color:C.sb,label:'pink state'}]),
  caption:COPY['4.4'].caption,takeaway:COPY['4.4'].takeaway,hint:COPY['4.4'].hint,
  notes:'Panels: controller (episode 988), random location at the controller’s dose (991), whole body at the controller’s dose (994, “dose-matched”), untreated twin (989) = held-out dish seed 6007, CRN twins. State bars and same-body badges are the frozen T5 monitor’s own verdicts (V_body); the shape trace is its worst bound ratio (inside the band ≤ 1). The controller reads S+ (= blue state), pulses at the body centre (r = 1.5, 10 tu, amplitude 1.6, then x1.1), commits when the excursion passes 0.62 and waits. Truth overlay: node shading by hidden rho shows the flip spreading out from the lit disc.',
  sources:[{what:'Four arms of held-out dish seed 6007',file:'t5_blind_control/episodes_heldout/ep_00988…00994.json + testbed_v3/live_sealed_t5/episode_00988…00994/hidden.npz',sec:'logs/heldout_summary.jsonl'},{what:'Controller protocol',file:'t5_blind_control/CONTROLLER.md'},{what:'Arms and dose matching',file:'t5_blind_control/EVALUATION.md',sec:'Headline table'}],
  setup(c){
    const D=DATA.c43;c.state.D=D;c.state.types=D.types;const s=Math.min(Demo.arenaSize(4,0),330);const row=el('div',{style:'display:flex;gap:10px;justify-content:center;flex-wrap:wrap;width:100%'},c.vis);
    c.state.names={ctrl:'Controller',random:'Random spot',whole_dm:'Whole body',twin:'No light'};c.state.cols={};
    ['ctrl','random','whole_dm','twin'].forEach(a=>{const arm=D.arms[a];arm.XX=B64.i16(arm.X,1000);arm.RR=B64.i16(arm.rho,20000);const w=el('div',{class:'pw'},row);const p=new Panel(w,{size:s,fov:6,title:c.state.names[a]});p.wrap=w;c.panels.push(p);
      const info=el('div',{style:'min-height:28px;text-align:center'},w);const sb=makeCanvas(w,s,34);const gb=makeCanvas(w,s,44);c.state.cols[a]={p:p,info:info,sb:sb,gb:gb};});
    // pause schedule from the data
    const ct=D.arms.ctrl,commit=ct.decisions.find(d=>d.action==='commit'),rho=ct.RR,N=24;const mean=k=>{let m=0;for(let i=0;i<N;i++)m+=rho[k*N+i];return m/N;};
    let cross=null;for(let k=1;k<ct.T;k++){if(mean(k)<0.5){cross=k;break;}}const tp=(arm)=>{const R=D.arms[arm].RR;let bk=0,bv=0;for(let k=0;k<D.arms[arm].T;k++){let m=0;for(let i=0;i<N;i++)m+=R[k*N+i];m/=N;const dv=Math.abs(m-mean(0));if(dv>bv){bv=dv;bk=k;}}return bk;};
    const first=ct.acts[0],lastEnd=ct.acts[ct.acts.length-1].t+ct.acts[ct.acts.length-1].dur;
    const K=COPY['4.4'].callouts,cm=commit?commit.t:46,tA=Math.max((cross||70)+4,cm+4),tR=Math.max(tp('random'),tA+16);
    const P=[{t:first.t,text:K[0],anchor:()=>({panel:c.state.cols.twin.p,x:0,y:2.2})},
      {t:first.t+3,text:K[1],anchor:()=>({panel:c.state.cols.ctrl.p,x:first.xy[0],y:first.xy[1]})},
      {t:first.t+7,text:K[2],anchor:()=>({px:pageAnchor(c.state.cols.ctrl.gb,c.state.cols.ctrl.gb.clientWidth*0.2,19)})},
      {t:cm,text:K[3],anchor:()=>({panel:c.state.cols.ctrl.p,x:first.xy[0],y:first.xy[1]})},
      {t:tA,text:K[4],anchor:()=>({panel:c.state.cols.ctrl.p,x:-1.5,y:1.5})},
      {t:tA+8,text:K[5],anchor:()=>({panel:c.state.cols.ctrl.p,x:0,y:-2.2})},
      {t:tR,text:K[6],anchor:()=>({panel:c.state.cols.random.p,x:D.arms.random.acts[0].xy[0],y:D.arms.random.acts[0].xy[1]})},
      {t:Math.min(tR+0.5,ct.T-1),text:K[7],anchor:()=>({panel:c.state.cols.whole_dm.p,x:0,y:2.4})}];
    P.sort((a,b)=>a.t-b.t);c.def.pauses=P;Demo.byId['4.4'].pauses=P;},
  draw(c,t,truth){
    const D=c.state.D,N=24;['ctrl','random','whole_dm','twin'].forEach(a=>{const arm=D.arms[a],col=c.state.cols[a],p=col.p,k=Math.max(0,Math.min(arm.T-1,Math.floor(t)));p.clear();p.scaleBar();
      arm.acts.forEach(ac=>{const ph=lightWindow(t,ac.t,ac.t+ac.dur,ac.ramp);if(ac.whole){if(ph>0.001){const g=p.ctx;g.save();g.fillStyle='rgba(255,255,255,'+(0.35*ph)+')';g.fillRect(0,0,p.w,p.h);g.strokeStyle=C.ink;g.lineWidth=2;g.setLineDash([8,5]);g.strokeRect(2,2,p.w-4,p.h-4);g.restore();}}else drawLight(p,ac.xy,ac.r,ph);});
      packedNodes(arm.XX,arm.RR,k,N,D.types,truth?'rho':'type').forEach(n=>p.node({x:n.x,y:n.y,fill:n.fill,r:0.4}));
      const dose=arm.acts.filter(ac=>ac.t<=t+1e-9).reduce((s,ac)=>s+ac.dose,0);const V=arm.V[k],st=arm.state[k];
      col.info.innerHTML=badge('same-body check '+(V?'passes':'fails'),V?'ok':'bad')+badge('light so far '+dose.toFixed(0),'neu')+badge(st==='S+'?'blue state':st==='S-'?'pink state':'changing','neu');
      const g=col.sb.getContext('2d'),dpr=1,w=col.sb.width,h=col.sb.height;g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,w,h);g.fillStyle='#fff';g.fillRect(0,0,w,h);for(let j=0;j<=k;j++){const s=arm.state[j];g.fillStyle=s==='S+'?C.sa:s==='S-'?C.sb:'#BBB';g.fillRect(Math.floor(j/arm.T*w),18,Math.ceil(w/arm.T)+1,h-20);}g.strokeStyle='#999';g.strokeRect(0.5,17.5,w-1,h-19);g.fillStyle=C.ink;g.font='11.5px '+FONT;g.textBaseline='top';g.fillText('group state over time',2,2);
      const gc=col.gb.getContext('2d'),gw=col.gb.width,gh=col.gb.height;gc.setTransform(1,0,0,1,0,0);gc.clearRect(0,0,gw,gh);gc.fillStyle='#fff';gc.fillRect(0,0,gw,gh);const gy0=18,gh2=gh-22;gc.fillStyle=C.band;gc.fillRect(0,gy0+gh2/2,gw,gh2/2);gc.strokeStyle='#222';gc.lineWidth=1.8;gc.beginPath();for(let j=0;j<=k;j++){const x=j/arm.T*gw,y=gy0+gh2-Math.min(arm.geo[j],2)/2*gh2;j?gc.lineTo(x,y):gc.moveTo(x,y);}gc.stroke();gc.fillStyle=C.ink;gc.font='11.5px '+FONT;gc.textBaseline='top';gc.fillText('shape (grey band = normal range)',2,2);});
  }
});


/* ---------------- 4.4 ---------------- */
Demo.register({id:'4.5',act:4,title:COPY['4.5'].title,data:['data/c44stats.js','data/c44worst.js'],duration:330,rate:28,truthOffered:false,
  legend:LEG.types.concat([{color:C.sa,label:'hidden memory: blue'},{color:C.sb,label:'hidden memory: pink'}]),
  caption:COPY['4.5'].caption,takeaway:COPY['4.5'].takeaway,
  notes:'Bars = success as scored from outside (monitor rule: state change held >= 120 tu after the last action, last 40 tu sure, V_body_conservative true); diamonds = audited truth (AUDIT_T5 A1: controller 57/60 = 95 %, random 5/60). Regret = dose used / true minimal dose of the same protocol (A3), noisy medians: controller 1.12, tuned flash 1.54, whole body bright 2.86. Light used relative to the controller: whole body bright 3.7x. The 4 monitor misses for the controller include one cohesion false alarm (dish 6040). Failure clip: seed 6026 (episode 1121): the commit rule fired at progress 0.63 while the collective was still on the start side (mean rho 0.56); the response relapsed and un-commit came 60 tu later.',
  audit:'Audited values used for the diamonds and the line under the chart (AUDIT_T5 A1, A3).',
  sources:[{what:'Success (dish-clustered 95 % CI) and dose by arm, n = 60 dishes',file:'t5_blind_control/logs/heldout_eval.json',sec:'table'},{what:'True success per arm; regret per dish',file:'testbed_v3/audit_t5/data/a1_tables.json; REGRET_AND_MAPS.json',sec:'AUDIT_T5 A1, A3'},{what:'Failure clip (seed 6026)',file:'testbed_v3/live_sealed_t5/episode_01121/hidden.npz + t5_blind_control/episodes_heldout/ep_01121.json'}],
  setup(c){
    const S=DATA.c44stats,W=DATA.c44worst;c.state.S=S;c.state.W=W;const sz=Math.min(Demo.arenaSize(2,0),420);const top=el('div',{style:'display:flex;gap:14px;flex-wrap:wrap;justify-content:center;width:100%'},c.vis);
    const l=el('div',{class:'pw'},top);el('div',{class:'ptitle'},l,'Share of dishes that switched and stayed switched');c.cvA=makeCanvas(l,640,Math.round(sz*0.72));c.cvH=Math.round(sz*0.72);
    el('div',{class:'ptitle',style:'margin-top:8px'},l,'Light used compared with the true minimum (each dot = one dish)');c.cvB=makeCanvas(l,640,Math.round(sz*0.55));c.cvH2=Math.round(sz*0.55);
    const w=el('div',{class:'pw'},top);c.pw=new Panel(w,{size:sz+60,fov:6.5,title:''});c.pw.wrap=w;c.panels.push(c.pw);W.arm.XX=B64.i16(W.arm.X,1000);W.arm.RR=B64.i16(W.arm.rho,20000);
    c.state.st=makeCanvas(w,sz+60,36);c.state.st.style.marginTop='4px';el('div',{style:'font-size:14px;max-width:640px;margin-top:8px;line-height:1.35'},l,COPY['4.5'].line);
    const un=W.arm.decisions.find(d=>d.action==='uncommit'),cm=W.arm.decisions.find(d=>d.action==='commit');
    const X0=ch=>0;const rowY=i=>22+((c.cvH-22-26)/6)*(i+0.5);
    c.def.pauses=[{t:0,text:COPY['4.5'].callouts[0],side:'right',anchor:()=>({px:pageAnchor(c.cvA,c.cvA.clientWidth*0.45,rowY(0))})},
      {t:0.5,text:COPY['4.5'].callouts[1],side:'right',anchor:()=>({px:pageAnchor(c.cvA,c.cvA.clientWidth*0.2,rowY(4))})},
      {t:1,text:COPY['4.5'].callouts[2],side:'right',anchor:()=>({px:pageAnchor(c.cvA,c.cvA.clientWidth*0.6,rowY(2))})},
      {t:1.5,text:COPY['4.5'].callouts[3],side:'right',anchor:()=>({px:pageAnchor(c.cvA,c.cvA.clientWidth*0.55,rowY(1))})},
      {t:(un?un.t:104)+3,text:COPY['4.5'].failure,anchor:()=>({panel:c.pw,x:0,y:-2.4})}];Demo.byId['4.5'].pauses=c.def.pauses;},
  draw(c,t){
    const S=c.state.S,W=c.state.W,ch=new Chart(c.cvA,{w:640,h:c.cvH,xlim:[0,1.3],ylim:[0,S.arms.length],m:{l:200,r:130,t:22,b:26},xticks:[0,0.25,0.5,0.75,1],yticks:[],xfmt:v=>Math.round(v*100)+'%'});ch.clear();ch.axes();
    const g=ch.c,rowH=(ch.h-ch.m.t-ch.m.b)/S.arms.length,base=S.arms[0].dose;S.arms.forEach((a,i)=>{const yc=ch.m.t+rowH*(i+0.5),x0=ch.X(0),x1=ch.X(a.success);g.fillStyle=i===0?'#222':'#8a8a8a';g.fillRect(x0,yc-rowH*0.28,Math.max(x1-x0,0),rowH*0.56);g.strokeStyle='#C0392B';g.lineWidth=2;g.beginPath();g.moveTo(ch.X(a.ci[0]),yc);g.lineTo(ch.X(a.ci[1]),yc);g.moveTo(ch.X(a.ci[0]),yc-6);g.lineTo(ch.X(a.ci[0]),yc+6);g.moveTo(ch.X(a.ci[1]),yc-6);g.lineTo(ch.X(a.ci[1]),yc+6);g.stroke();
      g.fillStyle='#fff';g.strokeStyle=C.ink;g.lineWidth=2;g.beginPath();const dx=ch.X(a.true_success),dy=yc;g.moveTo(dx,dy-8);g.lineTo(dx+8,dy);g.lineTo(dx,dy+8);g.lineTo(dx-8,dy);g.closePath();g.fill();g.stroke();
      g.fillStyle=C.ink;g.font=(i===0?'700 ':'')+'13px '+FONT;g.textAlign='right';g.textBaseline='middle';g.fillText(COPY['4.5'].labels[i],ch.m.l-8,yc);g.textAlign='left';g.fillText(Math.round(a.success*100)+' %',ch.X(1.0)+30,yc-8);g.fillStyle=C.mute;g.font='12px '+FONT;g.fillText(a.dose>0?'light '+(a.dose/base).toFixed(1)+'×':'no light',ch.X(1.0)+30,yc+8);});
    g.fillStyle=C.mute;g.font='12px '+FONT;g.textAlign='left';g.textBaseline='top';g.fillText('bar: scored from outside · red: 95 % range · ◇: checked against the hidden truth',ch.m.l,3);
    const R=c.cvB,rc=new Chart(R,{w:640,h:c.cvH2,xlim:[Math.log10(0.3),Math.log10(12)],ylim:[0,3],m:{l:200,r:20,t:14,b:30},xticks:[0.5,1,2,5,10].map(Math.log10),yticks:[],xfmt:v=>String(+Math.pow(10,v).toFixed(1))+'×'});rc.clear();rc.axes();rc.vline(0,{color:'#999',dash:[4,3]});
    [['Controller',S.regret.ctrl,0.5,C.ink,S.medians.ctrl.median],['One flash, tuned in advance',S.regret.fixed,1.5,'#777',S.medians.fixed.median],['Whole body, bright',S.regret.whole,2.5,'#999',S.medians.whole.median]].forEach(a=>{const v=a[1];rc.text(a[0],rc.m.l-8,rc.Y(a[2]),{align:'right',size:13,bold:true});v.forEach((x,i)=>{if(x>0)rc.dot(Math.log10(x),a[2]+((i*0.37)%0.5-0.25)*0.7,{color:a[3],r:3.2,stroke:'rgba(255,255,255,.8)'});});const md=a[4];rc.vline(Math.log10(md),{color:a[3],w:2});rc.text('median '+md.toFixed(2)+'×',rc.X(Math.log10(md))+4,rc.Y(a[2])-20,{size:11.5,color:a[3],bold:true});});
    // worst clip
    const arm=W.arm,k=Math.max(0,Math.min(arm.T-1,Math.floor(t))),p=c.pw;p.clear();p.scaleBar();arm.acts.forEach(ac=>drawLight(p,ac.xy,ac.r,lightWindow(t,ac.t,ac.t+ac.dur,ac.ramp)));packedNodes(arm.XX,arm.RR,k,24,W.types,'rho').forEach(n=>p.node({x:n.x,y:n.y,fill:n.fill,r:0.4}));
    const V=arm.V[k];p.setSub('time '+t.toFixed(0)+' · '+badge('same-body check '+(V?'passes':'fails'),V?'ok':'bad'));
    const gs=c.state.st.getContext('2d'),w=c.state.st.width,h=c.state.st.height;gs.setTransform(1,0,0,1,0,0);gs.fillStyle='#fff';gs.fillRect(0,0,w,h);for(let j=0;j<=k;j++){const s=arm.state[j];gs.fillStyle=s==='S+'?C.sa:s==='S-'?C.sb:'#BBB';gs.fillRect(Math.floor(j/arm.T*w),18,Math.ceil(w/arm.T)+1,h-20);}gs.strokeStyle='#999';gs.strokeRect(0.5,17.5,w-1,h-19);gs.fillStyle=C.ink;gs.font='11.5px '+FONT;gs.textBaseline='top';gs.fillText('group state over time (blue / pink)',2,2);
  }
});

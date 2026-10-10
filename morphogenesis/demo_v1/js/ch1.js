/* Act 1 - The organism (chapters 1.1 - 1.5) */
'use strict';
/* decoded view of the v3 natural body (body 2100, window t=3000..3059 of the package run, states a and b are bit-identical clones in position) */
function decodeBody(){
  const d=DATA.body2100;if(d._dec)return d._dec;const T=d.T,N=24;
  const o={T:T,N:N,X:B64.i16(d.X,1000),C:B64.i16(d.C,1000),types:d.types,place:d.place,tmplXY:d.tmplXY,tmplType:d.tmplType};
  ['a','b'].forEach(s=>{const e=d[s];o[s]={rho:B64.i16(e.rho,20000),D:B64.i16(e.D,20000),E:B64.i16(e.E,20000),f:B64.i16(e.f,20000),q:B64.u8(e.q),L:B64.i16(e.L,2000)};});
  o.pos=(k)=>{const a=[];for(let i=0;i<N;i++)a.push([o.X[(k*N+i)*2],o.X[(k*N+i)*2+1]]);return a;};
  d._dec=o;return o;}
function interpPos(B,t){const k0=Math.max(0,Math.min(Math.floor(t),B.T-1)),k1=Math.min(k0+1,B.T-1),u=Math.min(1,t-k0),a=[];
  for(let i=0;i<B.N;i++){const j0=(k0*B.N+i)*2,j1=(k1*B.N+i)*2;a.push([lerp(B.X[j0],B.X[j1],u),lerp(B.X[j0+1],B.X[j1+1],u)]);}return a;}
function bodyNodes(B,t,st,o){o=o||{};const P=interpPos(B,t),k=Math.min(Math.round(t),B.T-1),S=B[st];const nodes=[];
  for(let i=0;i<B.N;i++){const rho=S.rho[k*B.N+i],e=S.E[k*B.N+i];
    nodes.push({x:P[i][0],y:P[i][1],i:i,type:B.types[i],rho:rho,e:e,fill:o.mode==='rho'?rhoColor(rho):TYPEC[B.types[i]],ring:o.ring?e>0.5:false});}
  return nodes;}
/* kernel-weighted field of per-node values */
function fieldVals(nodes,vals,x,y){let s=0;for(let j=0;j<nodes.length;j++){s+=vals[j]*Math.exp(-Math.hypot(x-nodes[j].x,y-nodes[j].y));}return s;}
function drawBodyField(p,nodes,kind,B,st,k){
  const N=nodes.length,S=B[st];
  if(kind==='mem'){const dA=[],dB=[];for(let i=0;i<N;i++){dA.push(S.D[(k*N+i)*2]);dB.push(S.D[(k*N+i)*2+1]);}
    p.field((x,y)=>{const A=fieldVals(nodes,dA,x,y),Bv=fieldVals(nodes,dB,x,y),f=(A+5e-4)/(A+Bv+1e-3);const c=rhoRGB(f);const a=Math.min(1,(A+Bv)/1.6)*0.85;return [c[0],c[1],c[2],a];});}
  else if(kind==='rep'){const e=nodes.map(n=>n.e);p.field((x,y)=>{const v=Math.min(1,fieldVals(nodes,e,x,y)/2.6);const c=mixrgb('#FFFFFF',C.rep,v);return [c[0],c[1],c[2],0.15+0.8*v];});}
  else{const ch=kind==='grad'?[0]:[1,2,3];const v=nodes.map((n,i)=>ch.reduce((s,c)=>s+B.C[(k*N+i)*4+c],0));const mx=kind==='grad'?3.2:2.3;
    p.field((x,y)=>{const u=Math.min(1,fieldVals(nodes,v,x,y)/ (mx*1.0));const g=Math.round(250-200*u);return [g,g,g,0.15+0.8*u];});}
}
function chipsTypes(note){return LEG.types.concat(note?[]:[]);}
const TYPELEG=[{color:C.head,label:'head'},{color:C.trunk,label:'trunk'},{color:C.limb,label:'limb'},{color:C.tail,label:'tail'}];

/* ---------------- 1.1 ---------------- */
Demo.register({id:'1.1',act:1,title:COPY['1.1'].title,
  legend:LEG.types,
  data:['data/body2100.js','data/oracle8.js'],duration:64,rate:5.3,
  caption:COPY['1.1'].caption,takeaway:COPY['1.1'].takeaway,
  notes:'Friston, Levin, Sengupta &amp; Pezzulo 2015 (morphogenesis as active inference). Left panel = the Octave oracle of the published 8-cell model (canonical developmental clock T_dev = 32 bins, seed 0, bins 1–64; its 4 cell types are mapped to the head…tail colours by body position, front → back). Right panel = natural dish with body id 2100 (package run_00011), 60 tu starting at t = 3000 after settling. Both clips are played on a common timeline (left in bins, right in tu). Our continuous-time engine is faithful to the original scheme; identity is categorical (belief over places).',
  sources:[{what:'Left clip: Octave oracle positions, bins 1–64, 8-cell model',file:'m2a_audit_and_library/data/part0/direct_primary_0000.mat',sec:'positions; types from target_s grouping in vanilla8_N32_seed0.mat'},
           {what:'Right clip: v3 natural dish body 2100, state a, t = 3000–3059 tu',file:'testbed_v3/data/raw_v4/natural/a_cal_2100.pkl',sec:'frames[3000:3060]; = package run_00011'},
           {what:'Model description',file:'testbed_v3/ENGINE_SPEC_V3.md',sec:'Model as implemented'}],
  setup(c){
    const sz=Demo.arenaSize(2,0);const O=DATA.oracle8,B=decodeBody();c.state.O=O;c.state.B=B;c.state.Xo=B64.i16(O.X,1000);
    c.pl=c.panel({size:sz,fov:3.4,title:'',id:'L'});c.pr=c.panel({size:sz,fov:5.6,title:COPY['1.1'].right,id:'R'});c.pr.tEl.style.maxWidth=sz+'px';c.pl.tEl.style.minHeight='1.2em';},
  draw(c,t){
    const O=c.state.O,B=c.state.B,Xo=c.state.Xo,nb=O.T;const b=Math.max(0,Math.min(nb-1,t)),b0=Math.floor(b),b1=Math.min(b0+1,nb-1),u=b-b0;
    c.pl.clear();c.pl.scaleBar();
    for(let i=0;i<8;i++){const x=lerp(Xo[(b0*8+i)*2],Xo[(b1*8+i)*2],u),y=lerp(Xo[(b0*8+i)*2+1],Xo[(b1*8+i)*2+1],u);c.pl.node({x:x,y:y,fill:TYPEC[O.types[i]],r:0.28});}
    const tt=t*(B.T-1)/nb;c.pr.clear();c.pr.scaleBar();const nodes=bodyNodes(B,tt,'a');nodes.forEach(n=>c.pr.node({x:n.x,y:n.y,fill:n.fill,r:0.40}));},
  pauses:[{t:0,text:COPY['1.1'].callouts[0],side:'top',anchor:c=>({panel:c.pl,x:0,y:0})},
          {t:8,text:COPY['1.1'].callouts[1],side:'top',anchor:c=>({panel:c.pl,x:0.5,y:0.3})},
          {t:60,text:COPY['1.1'].callouts[2],side:'top',anchor:c=>({panel:c.pl,x:0,y:0.5})},
          {t:64,text:COPY['1.1'].callouts[3],side:'top',anchor:c=>({panel:c.pr,x:0,y:0})}]
});

/* ---------------- 1.2 ---------------- */
function gauge(g,cx,cy,r,rho,label){ // semi-circular dial from b (left, purple) to a (right, blue)
  g.save();g.lineWidth=14;for(let k=0;k<40;k++){const a0=Math.PI+(k/40)*Math.PI,a1=Math.PI+((k+1)/40)*Math.PI;g.strokeStyle=rhoColor(k/39);g.beginPath();g.arc(cx,cy,r,a0,a1+0.01);g.stroke();}
  const a=Math.PI+(1-(1-rho))*Math.PI*0+rho*Math.PI;g.strokeStyle=C.ink;g.lineWidth=3;g.beginPath();g.moveTo(cx,cy);g.lineTo(cx+(r-18)*Math.cos(a),cy+(r-18)*Math.sin(a));g.stroke();g.fillStyle=C.ink;g.beginPath();g.arc(cx,cy,5,0,6.3);g.fill();
  g.font='12px '+FONT;g.textAlign='center';g.fillText('pink',cx-r,cy+16);g.fillText('blue',cx+r,cy+16);g.font='700 12px '+FONT;g.fillText(label,cx,cy+34);g.restore();}
function box(g,x,y,w,h,title,col){g.save();g.fillStyle='#fff';g.strokeStyle=C.ink;g.lineWidth=2;g.beginPath();g.roundRect(x,y,w,h,8);g.fill();g.stroke();g.fillStyle=C.ink;g.font='700 13.5px '+FONT;g.textAlign='left';g.textBaseline='top';g.fillText(title,x+10,y+8);g.restore();}
function barrow(g,x,y,w,v,col,label){g.save();g.fillStyle='#eee';g.fillRect(x,y,w,9);g.fillStyle=col;g.fillRect(x,y,w*Math.max(0,Math.min(1,v)),9);g.fillStyle=C.ink;g.font='11.5px '+FONT;g.textAlign='left';g.textBaseline='middle';g.fillText(label,x+w+6,y+5);g.restore();}
Demo.register({id:'1.2',act:1,title:COPY['1.2'].title,
  legend:LEG.types.concat([{color:C.sa,label:'leaning blue'},{color:C.sb,label:'leaning pink'}]),data:['data/body2100.js'],duration:60,rate:4,
  caption:COPY['1.2'].caption,takeaway:COPY['1.2'].takeaway,
  notes:'Blanket = sensory + active states of a node; interior = hidden beliefs (24-place belief vector q, memory logit l with rho = sigma(l)); exterior = other cells and the experimenter. The beliefs are never observable in the experiments: they appear here from the hidden tier. Movement arrows are scaled x40 for visibility (real speeds are about 0.01–0.03 units per tu). The sensory memory input is the paracrine fraction f = A/(A+B) over neighbours only (j != i). Secretion bars: ch0 = head-to-tail gradient, ch1–ch3 = body (structural) codes; A/B = memory ligands; e = reporter.',
  sources:[{what:'Per-node beliefs q (24 places), memory logit l (rho = sigma(l)), ligand levels (dA,dB), reporter e, paracrine fraction f',file:'testbed_v3/data/raw_v4/natural/a_cal_2100.pkl',sec:'frames[3000:3060]: MU, L, D, E, C, X'},
           {what:'Blanket vocabulary and model equations',file:'testbed_v3/ENGINE_SPEC_V3.md',sec:'Model as implemented'}],
  setup(c){
    const B=decodeBody();c.state.B=B;c.state.sel=11;const sz=Demo.arenaSize(2,0);
    c.pa=c.panel({size:sz,fov:5.6,title:'Our organism',id:'arena'});
    const w=document.createElement('div');w.className='pw';c.vis.appendChild(w);const tt=el('div',{class:'ptitle'},w,'');c.state.dtitle=tt;
    c.dcv=makeCanvas(w,500,sz);c.dp=new Panel(document.createElement('div'),{w:500,h:sz,fov:Math.min(500,sz)/2});c.dp.canvas=c.dcv;c.dp.setSize(500,sz);c.dp.fov=Math.min(500,sz)/2;c.dp.scale=1;c.dp.wrap=w;c.dp.avoidAll=true;c.panels.push(c.dp);
    c.pa.onclick=(wp)=>{const k=Math.min(Math.round(Demo.t*(B.T-1)/60),B.T-1),P=B.pos(k);let b=-1,bd=1e9;P.forEach((p,i)=>{const d=Math.hypot(p[0]-wp[0],p[1]-wp[1]);if(d<bd){bd=d;b=i;}});if(bd<1){c.state.sel=b;Demo.redraw();}};},
  draw(c,t){
    const B=c.state.B,k=Math.min(Math.round(t*(B.T-1)/60),B.T-1),tt=t*(B.T-1)/60,S=B.a,N=24,sel=c.state.sel;const nodes=bodyNodes(B,tt,'a',{mode:'rho'});
    const p=c.pa;p.clear();p.scaleBar();
    nodes.forEach(n=>{n.fill=TYPEC[n.type];n.hl=n.i===sel;});
    nodes.forEach(n=>p.node(n));
    const P0=B.pos(Math.max(0,k-1)),P1=B.pos(Math.min(B.T-1,k+1));const s=nodes[sel];
    const vx=(P1[sel][0]-P0[sel][0])/2*40,vy=(P1[sel][1]-P0[sel][1])/2*40;p.arrow([s.x,s.y],[s.x+vx,s.y+vy],{color:C.ink,w:2.5,head:10});
    nodes.forEach(n=>{if(n.i!==sel&&Math.hypot(n.x-s.x,n.y-s.y)<2.2){p.line([s.x,s.y],[n.x,n.y],{color:'rgba(0,0,0,.25)',w:1,dash:[3,3]});}});
    p.label('movement (drawn 40 times longer)',s.x+vx+0.2,s.y+vy+0.2,{size:12,world:true});
    const g=c.dcv.getContext('2d'),W=500,H=c.dcv.height/c.dp.dpr;g.setTransform(c.dp.dpr,0,0,c.dp.dpr,0,0);g.clearRect(0,0,W,H);g.fillStyle='#fff';g.fillRect(0,0,W,H);
    const bw=226,bh=(H-40)/2-10,x0=10,x1=W-10-bw,y0=14,y1=y0+bh+36;c.state.boxes={ext:[x0,y0,bw,bh],sen:[x1,y0,bw,bh],int:[x1,y1,bw,bh],act:[x0,y1,bw,bh]};
    box(g,x0,y0,bw,bh,'EVERYTHING ELSE');box(g,x1,y0,bw,bh,'SENSES');box(g,x1,y1,bw,bh,'INSIDE (hidden)');box(g,x0,y1,bw,bh,'ACTIONS');
    const ar=(ax,ay,bx,by)=>{g.save();g.strokeStyle=C.ink;g.fillStyle=C.ink;g.lineWidth=2.4;g.beginPath();g.moveTo(ax,ay);g.lineTo(bx,by);g.stroke();const a=Math.atan2(by-ay,bx-ax);g.beginPath();g.moveTo(bx,by);g.lineTo(bx-10*Math.cos(a-.4),by-10*Math.sin(a-.4));g.lineTo(bx-10*Math.cos(a+.4),by-10*Math.sin(a+.4));g.fill();g.restore();};
    ar(x0+bw,y0+bh/2,x1,y0+bh/2);ar(x1+bw/2,y0+bh,x1+bw/2,y1);ar(x1,y1+bh/2,x0+bw,y1+bh/2);ar(x0+bw/2,y1,x0+bw/2,y0+bh);
    g.font='12.5px '+FONT;g.fillStyle=C.ink;g.textAlign='left';g.textBaseline='top';
    const nb=nodes.filter(n=>n.i!==sel&&Math.hypot(n.x-s.x,n.y-s.y)<2.2).length;
    g.fillText('other cells within reach: '+nb,x0+10,y0+34);g.fillText('and the experimenter\'s tools',x0+10,y0+54);
    const fv=S.f[k*N+sel];g.fillText('body signals from neighbours',x1+10,y0+34);
    g.fillText('blue and pink signal from neighbours:',x1+10,y0+78);
    g.fillStyle='#eee';g.fillRect(x1+10,y0+98,bw-20,14);for(let u=0;u<bw-20;u++){g.fillStyle=rhoColor(u/(bw-20));g.fillRect(x1+10+u,y0+98,1,14);}g.fillStyle=C.ink;g.fillRect(x1+10+fv*(bw-21)-1.5,y0+93,3,24);g.font='11.5px '+FONT;g.fillText('share of blue signal: '+fv.toFixed(2),x1+10,y0+122);g.fillText('(pink ←  → blue)',x1+10,y0+138);
    const qa=S.q;const bx=x1+10,by=y1+bh-26,bwid=(bw-20)/24;
    let am=0,av=0;for(let j=0;j<24;j++){const v=qa[(k*N+sel)*24+j]/255;if(v>av){av=v;am=j;}}
    for(let j=0;j<24;j++){const v=qa[(k*N+sel)*24+j]/255;g.fillStyle=j===am?TYPEC[B.tmplType[am]]:'#bbb';g.fillRect(bx+j*bwid,by-v*60,bwid-1,Math.max(v*60,0.5));}
    g.fillStyle=C.ink;g.textAlign='left';g.textBaseline='top';g.font='11px '+FONT;g.fillText('guess about its position: '+TYPENAME[B.tmplType[am]]+' ('+av.toFixed(2)+')',bx,by+3);
    gauge(g,x1+bw/2,y1+86,48,S.rho[k*N+sel],'guess about group state: '+(S.rho[k*N+sel]>=0.5?'blue ':'pink ')+(S.rho[k*N+sel]>=0.5?S.rho[k*N+sel]:1-S.rho[k*N+sel]).toFixed(2));
    const Cc=B.C,e=S.E[k*N+sel],dA=S.D[(k*N+sel)*2],dB=S.D[(k*N+sel)*2+1];let yy=y1+34;g.fillStyle=C.ink;g.textAlign='left';g.textBaseline='top';g.font='12.5px '+FONT;g.fillText('moves (arrow on the body)',x0+10,yy);yy+=24;
    g.fillText('releases body signals',x0+10,yy);yy+=18;const bn=['head-to-tail','body 1','body 2','body 3'];for(let j=0;j<4;j++){barrow(g,x0+10,yy,100,Cc[(k*N+sel)*4+j]/2.6,'#888',bn[j]);yy+=14;}
    yy+=6;g.fillStyle=C.ink;g.fillText('releases memory signals',x0+10,yy);yy+=18;barrow(g,x0+10,yy,100,dA,C.sa,'blue '+dA.toFixed(2));yy+=14;barrow(g,x0+10,yy,100,dB,C.sb,'pink '+dB.toFixed(2));yy+=20;
    g.fillStyle=C.ink;g.fillText('lights its yellow marker',x0+10,yy);yy+=18;barrow(g,x0+10,yy,100,e,C.rep,'marker '+e.toFixed(2));
    c.state.dtitle.textContent='Cell '+sel+' ('+TYPENAME[nodes[sel].type]+' cell)';
  },
  pauses:[{t:0,text:COPY['1.2'].callouts[0],side:'right',anchor:c=>({panel:c.dp,x:c.state.boxes.int[0]+c.state.boxes.int[2]/2-250,y:c.dp.h/2-(c.state.boxes.int[1]+30)})},
          {t:20,text:COPY['1.2'].callouts[1],side:'right',anchor:c=>({panel:c.dp,x:c.state.boxes.act[0]+c.state.boxes.act[2]-250,y:c.dp.h/2-(c.state.boxes.act[1]+30)})},
          {t:40,text:COPY['1.2'].callouts[2],side:'right',anchor:c=>({panel:c.dp,x:c.state.boxes.ext[0]+c.state.boxes.ext[2]-250,y:c.dp.h/2-(c.state.boxes.ext[1]+30)})}]
});

/* ---------------- 1.3 ---------------- */
Demo.register({id:'1.3',act:1,title:COPY['1.3'].title,legend:LEG.types,data:['data/body2100.js'],duration:0,truthOffered:false,
  caption:COPY['1.3'].caption,takeaway:COPY['1.3'].takeaway,
  notes:'Package labels: c1–c3 are the three body signals (hidden: structural codes ch2, ch1, ch3), c6 is the head-to-tail signal (ch0), c4/c5 are the memory ligands A/B (shown as the A-fraction = blue share), c0 is the reporter (yellow marker). Structure never reads memory; memory never feeds structure (bit-identical under any memory intervention, MEMORY_V3 H0).',
  sources:[{what:'Field values come from per-node secretion levels (C, dA/dB, e) with the model\'s exponential kernel; displayed field = kernel-weighted sum (A/(A+B) for memory)',file:'testbed_v3/data/raw_v4/natural/a_cal_2100.pkl',sec:'frame 3000'},
           {what:'T4 decoupling (structure bit-identical under memory interventions)',file:'testbed_v3/MEMORY_V3.md',sec:'H0'},{what:'Package-label mapping c0–c6',file:'testbed_v3/audit_t4/AUDIT_T4.md',sec:'Unsealed mapping'}],
  setup(c){
    const B=decodeBody();c.state.B=B;c.state.mode=0;c.state.nodes=bodyNodes(B,0,'a',{ring:false});const sz=Demo.arenaSize(2,0);
    c.pa=c.panel({size:sz,fov:5.6,title:'',id:'arena'});
    const w=document.createElement('div');w.className='pw';c.vis.appendChild(w);c.ms=makeCanvas(w,420,sz);
    const bar=document.createElement('div');bar.className='seg';bar.id='sel13';
    COPY['1.3'].buttons.forEach((nm,i)=>{const b=document.createElement('button');b.textContent=nm;b.onclick=()=>{Demo.showView(i);};bar.appendChild(b);});c.ctrls.appendChild(bar);},
  views:[0,1,2,3].map(i=>({apply(c){c.state.mode=i;document.querySelectorAll('#sel13 button').forEach((b,j)=>b.classList.toggle('on',j===i));
      Demo.setLegend(i===2?[{color:C.sa,label:'more blue signal'},{color:C.mid,label:'equal'},{color:C.sb,label:'more pink signal'},{color:'#fff',label:'faint = little signal'}]:(i===3?[{cls:'ring',label:'cells with the marker on'},{color:C.rep,label:'marker glow'}]:LEG.types.concat([{color:'#888',label:'grey = signal strength'}])));},
    side:'left',anchor:c=>({panel:c.pa,x:(i===3?-0.3:i===2?0:0),y:(i===3?1.5:0.2)}),
    text:COPY['1.3'].texts[i]})),
  draw(c,t){
    const B=c.state.B,mode=c.state.mode,nodes=c.state.nodes,p=c.pa;p.clear();const kinds=['type','grad','mem','rep'];drawBodyField(p,nodes,kinds[mode],B,'a',0);p.scaleBar();
    nodes.forEach(n=>{const m={x:n.x,y:n.y,fill:TYPEC[n.type],r:0.4,ring:mode===3&&n.e>0.5};p.node(m);});
    const g=c.ms.getContext('2d'),dpr=Math.min(window.devicePixelRatio||1,2);c.ms.width=420*dpr;c.ms.height=p.h*dpr;c.ms.style.width='420px';c.ms.style.height=p.h+'px';g.setTransform(dpr,0,0,dpr,0,0);g.fillStyle='#fff';g.fillRect(0,0,420,p.h);
    const small=[['body signal 1','struct',2],['body signal 2','struct',1],['body signal 3','struct',3],['head-to-tail signal','struct',0],['memory signals (blue share)','mem',0],['yellow marker','rep',0]];const mw=190,mh=Math.floor((p.h-20)/3)-10;
    small.forEach((s,i)=>{const col=i%2,row=Math.floor(i/2),x0=14+col*(mw+12),y0=10+row*(mh+30);
      const sp=new Panel(document.createElement('div'),{w:mw,h:mh,fov:mh/2/ (mh/ (2*3.6))});
      const q=sp;q.ctx=g;q.dpr=dpr;q.w=mw;q.h=mh;q.scale=mh/7.2;q.cx=0;q.cy=0;
      g.save();g.translate(x0,y0);g.beginPath();g.rect(0,0,mw,mh);g.clip();g.fillStyle='#fff';g.fillRect(0,0,mw,mh);
      const nds=c.state.nodes;const kind=s[1];
      if(kind==='mem')drawBodyField(q,nds,'mem',B,'a',0);else if(kind==='rep')drawBodyField(q,nds,'rep',B,'a',0);else{const vals=nds.map((n,j)=>B.C[j*4+s[2]]);const mx=s[2]===0?3.2:1.2;q.field((x,y)=>{const u=Math.min(1,fieldVals(nds,vals,x,y)/mx);const gg=Math.round(250-200*u);return [gg,gg,gg,0.15+0.8*u];},70);}
      nds.forEach(n=>{const pp=q.w2p(n.x,n.y);g.fillStyle=TYPEC[n.type];g.beginPath();g.arc(pp[0],pp[1],mh/7.2*0.28,0,6.3);g.fill();});
      g.restore();g.fillStyle=C.ink;g.font='12.5px '+FONT;g.textAlign='left';g.textBaseline='top';g.fillText(s[0],x0,y0+mh+4);});
  },
  init(c){}
});

/* ---------------- 1.4 ---------------- */
Demo.register({id:'1.4',act:1,title:COPY['1.4'].title,truthOffered:false,
  legend:LEG.types.concat([{color:C.sa,label:'blue state'},{color:C.sb,label:'pink state'},{cls:'ring',label:'yellow marker'}]),data:['data/body2100.js'],duration:60,rate:4,
  caption:COPY['1.4'].caption,takeaway:COPY['1.4'].takeaway,
  notes:'The T4 analysis called the two states “mirror images”; the audit corrected this: the body (positions, types, place beliefs) is bit-identical in both states (130 clone pairs, max |dX| = 0.0); only the memory ligands, the memory belief and the reporter row (+y limb row in state a, −y trunk row in state b) differ. Clone pair of body 2100 (a = package run_00011, b = run_00133), t = 3000–3059 tu.',
  sources:[{what:'Clone pair of body 2100: state a / state b, t = 3000–3059 tu; max |dX| = 0.0',file:'testbed_v3/data/raw_v4/natural/{a,b}_cal_2100.pkl'},{what:'Audit: the two states are the same chiral body, reporter row moved (not mirror images)',file:'testbed_v3/audit_t4/AUDIT_T4.md',sec:'A4 “Is mirror image accurate? No.”'}],
  audit:'Corrects the T4 claim “mirror-image organisations”.',
  setup(c){
    const B=decodeBody();c.state.B=B;c.state.overlay=false;const sz=Demo.arenaSize(2,0);
    c.pa=c.panel({size:sz,fov:5.6,title:'Blue state',id:'a'});c.pb=c.panel({size:sz,fov:5.6,title:'Pink state',id:'b'});
    const lab=el('label',{},c.ctrls);const cb=el('input',{type:'checkbox'},lab);lab.appendChild(document.createTextNode(' Overlay'));cb.onchange=()=>{c.state.overlay=cb.checked;c.pb.wrap.style.display=cb.checked?'none':'';c.pa.setTitle(cb.checked?'Blue state (filled) and pink state (dashed ring)':'Blue state');Demo.redraw();};},
  draw(c,t,truth){
    const B=c.state.B,k=Math.min(Math.round(t),B.T-1),mk=(st)=>bodyNodes(B,t,st,{ring:true,mode:'type'});
    const one=(p,st,nodes)=>{p.clear();drawBodyField(p,nodes,'mem',B,st,k);p.scaleBar();nodes.forEach(n=>p.node({x:n.x,y:n.y,fill:n.fill,ring:n.ring,r:0.4}));};
    const na=mk('a'),nb=mk('b');one(c.pa,'a',na);
    if(c.state.overlay){nb.forEach(n=>{const q=c.pa.w2p(n.x,n.y),g=c.pa.ctx;g.save();g.strokeStyle=C.sb;g.lineWidth=2.4;g.setLineDash([4,3]);g.beginPath();g.arc(q[0],q[1],0.62*c.pa.scale,0,6.3);g.stroke();g.restore();});
      let m=0;for(let i=0;i<24;i++)m=Math.max(m,Math.hypot(na[i].x-nb[i].x,na[i].y-nb[i].y));c.pa.setSub('largest position difference: '+m.toFixed(3)+' cell-widths');}
    else{one(c.pb,'b',nb);c.pa.setSub('');c.pb.setSub('');}
  },
  pauses:[{t:15,text:COPY['1.4'].callouts[0],side:'top',anchor:c=>({panel:c.pa,x:-2.2,y:-1.6})},
          {t:40,text:COPY['1.4'].callouts[1],side:'top',anchor:c=>({panel:c.pa,x:0.2,y:1.6})}]
});

/* ---------------- 1.5 ---------------- */
Demo.register({id:'1.5',act:1,title:COPY['1.5'].title,truthOffered:false,
  legend:LEG.rho,data:['data/mem15.js'],duration:600,rate:40,
  caption:COPY['1.5'].caption,takeaway:COPY['1.5'].takeaway,
  notes:'Noise sigma_h = 0.7 (declared; the testbed default is 0.4, where nothing flips in 20,000 tu). Clip chosen by a pre-declared rule: the lowest seed (0,1,2,…) in which the group of 4 first changes sign between 150 and 450 tu and the full body never does. The lifetime plot is the measured lifetime of N-cell groups at sigma_h = 0.7 (12 replicates each).',
  sources:[{what:'Regenerated clip: N = 1, 4, 24 cells at sigma_h = 0.7, deterministic (seed in file); group = the N places nearest to place 10 cut from the settled body',file:'demo_v1/data/mem15.js',sec:'built by demo_v1/build/build_mem15.py (code/h2d.py protocol)'},
           {what:'Quorum lifetimes (sigma_h = 0.7): N=2 238 tu, 4 742, 8 2,173, 12 5,852; N=24 0/12 in 10^4 tu',file:'testbed_v3/MEMORY_V3.md',sec:'(d) Quorum curve'}],
  setup(c){
    const D=DATA.mem15;c.state.D=D;const sz=Demo.arenaSize(3,0);const s3=Math.min(sz,360);
    c.p1=c.panel({size:s3,fov:5.6,title:'A single cell',id:'p1'});c.p4=c.panel({size:s3,fov:5.6,title:'A group of four',id:'p4'});c.p24=c.panel({size:s3,fov:5.6,title:'The whole organism',id:'p24'});
    const row2=el('div',{style:'display:flex;gap:14px;flex-wrap:wrap;justify-content:center;width:100%'},c.vis);
    c.pw1=el('div',{class:'pw'},row2);el('div',{class:'ptitle'},c.pw1,'Memory over time (1 = blue, 0 = pink)');c.cv1=makeCanvas(c.pw1,520,250);
    c.pw2=el('div',{class:'pw'},row2);el('div',{class:'ptitle'},c.pw2,'How long a group keeps its state');c.cv2=makeCanvas(c.pw2,430,250);
    c.state.rho={};['n1','n4','n24'].forEach(k=>{c.state.rho[k]=B64.i16(D[k].rho,20000);});c.state.X={};['n1','n4','n24'].forEach(k=>{c.state.X[k]=B64.i16(D[k].X,1000);});c.state.nf=D.nf;},
  draw(c,t){
    const D=c.state.D,nf=D.nf,k=Math.min(Math.round(t/D.dt),nf-1);
    const dr=(p,key,n,tpl)=>{p.clear();p.scaleBar();const X=c.state.X[key],R=c.state.rho[key];for(let i=0;i<n;i++)p.node({x:X[(k*n+i)*2],y:X[(k*n+i)*2+1],fill:rhoColor(R[k*n+i]),r:0.4});p.setSub('');};
    dr(c.p1,'n1',1);dr(c.p4,'n4',4);dr(c.p24,'n24',24);
    const ch=new Chart(c.cv1,{w:520,h:250,xlim:[0,D.T],ylim:[0,1],xlabel:'time units',yticks:[0,.5,1]});ch.clear();ch.hline(.5,{dash:[4,3],color:'#999'});ch.axes();
    const xs=[];for(let i=0;i<=k;i++)xs.push(i*D.dt);const mean=(key,n)=>{const R=c.state.rho[key],o=[];for(let i=0;i<=k;i++){let m=0;for(let j=0;j<n;j++)m+=R[i*n+j];o.push(m/n);}return o;};
    ch.line(xs,mean('n1',1),{color:'#777',w:2});ch.line(xs,mean('n4',4),{color:C.trunk,w:2});ch.line(xs,mean('n24',24),{color:C.ink,w:2.5});
    ch.text('single cell',ch.X(D.T)-8,ch.Y(0.08),{align:'right',color:'#777',size:12});ch.text('group of four',ch.X(D.T)-8,ch.Y(0.3),{align:'right',color:C.trunk,size:12});ch.text('whole organism',ch.X(D.T)-8,ch.Y(0.95),{align:'right',color:C.ink,size:12});
    const q=new Chart(c.cv2,{w:430,h:250,xlim:[0,26],ylim:[1.5,4.2],xticks:[2,4,8,12,24],yticks:[2,3,4],yfmt:v=>'10^'+v,xlabel:'cells in the group'});q.clear();q.axes();
    q.c.save();q.c.font='12px '+FONT;q.c.fillStyle=C.mute;q.c.textAlign='left';q.c.textBaseline='top';q.c.fillText('time units until the state is lost (log scale)',q.m.l+4,3);q.c.restore();
    const tab=[[2,238],[4,742],[8,2173],[12,5852]];q.line(tab.map(a=>a[0]),tab.map(a=>Math.log10(a[1])),{color:C.trunk,w:2});tab.forEach(a=>{q.dot(a[0],Math.log10(a[1]),{color:C.trunk,r:5});q.text(String(a[1]),q.X(a[0])+6,q.Y(Math.log10(a[1]))+12,{size:11.5});});
    q.dot(24,4.0,{color:C.ink,r:5});q.text('never lost in the test',q.X(24)-6,q.Y(4.0)+14,{align:'right',size:11.5});},
  pauses:[{t:90,text:COPY['1.5'].callouts[0],side:'top',anchor:c=>({panel:c.p1,x:0,y:0})},
          {t:270,text:COPY['1.5'].callouts[1],side:'top',anchor:c=>({panel:c.p4,x:0,y:0})},
          {t:600,text:COPY['1.5'].callouts[2],side:'top',anchor:c=>({panel:c.p24,x:0,y:2.2})}]
});

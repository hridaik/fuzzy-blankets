/* Act 2 - The experiment (chapters 2.1, 2.2, 2.3) */
'use strict';
function lightWindow(t,ton,toff,ramp){const up=Math.max(0,Math.min(1,(t-ton)/ramp)),dn=Math.max(0,Math.min(1,(toff-t)/ramp)),x=Math.min(up,dn);return 0.5*(1-Math.cos(Math.PI*x));}
function drawLight(p,xy,r,ph){if(ph<=0.001)return;p.disc(xy[0],xy[1],r,{alpha:0.35*ph,glow:ph});}
/* outlines drawn from a grouping (the blind analysis' own organism labels): points + labels, or a label mask */
function groupOutlinePts(p,xy,lab,opt){opt=opt||{};const g={};for(let i=0;i<lab.length;i++){if(lab[i]<0)continue;(g[lab[i]]=g[lab[i]]||[]).push([xy[2*i],xy[2*i+1]]);}
  Object.keys(g).forEach(k=>{const sub=g[k];if(sub.length<3)return;pointOutline(p,sub,C.ink,opt.w||3.2,1.5);const top=Math.max(...sub.map(q=>q[1])),cx=sub.reduce((a,q)=>a+q[0],0)/sub.length;
    if(!opt.nolabel)p.label('organism '+(+k+1),cx,top+1.15,{align:'center',size:13,bold:true,world:true,bg:true});});}
function groupOutlineMask(p,maskB64cache,N,half,opt){opt=opt||{};const m=maskB64cache;maskOutline(p,m,N,half,C.ink,opt.w||3);
  const cs={};const h=2*half/N;for(let i=0;i<N;i++)for(let j=0;j<N;j++){const v=m[i*N+j];if(!v)continue;const o=cs[v]||(cs[v]={x:0,y:0,n:0,top:-1e9});o.x+=-half+(j+.5)*h;o.y+=half-(i+.5)*h;o.n++;o.top=Math.max(o.top,half-i*h);}
  Object.keys(cs).forEach(v=>{const o=cs[v];if(!opt.nolabel)p.label('organism '+v,o.x/o.n,o.top+1.15,{align:'center',size:13,bold:true,world:true,bg:true});});}
function drawnTag(p){const c=p.ctx;c.save();c.font='italic 12.5px '+FONT;c.fillStyle='rgba(255,255,255,.88)';const t=COPY['3.1'].drawn,w=c.measureText(t).width;c.fillRect(6,6,w+10,19);c.fillStyle=C.ink;c.textAlign='left';c.textBaseline='middle';c.fillText(t,11,16);c.restore();}
/* ---------------- 2.1 ---------------- */
function drawToolbox(cv,w,h){
  const g=cv.getContext('2d'),d=Math.min(window.devicePixelRatio||1,2);cv.width=w*d;cv.height=h*d;cv.style.width=w+'px';cv.style.height=h+'px';g.setTransform(d,0,0,d,0,0);g.fillStyle='#fff';g.fillRect(0,0,w,h);
  g.textBaseline='middle';
  const dish=(x,y,r,fn)=>{g.save();g.fillStyle='#fff';g.strokeStyle=C.ink;g.lineWidth=1.6;g.beginPath();g.arc(x,y,r,0,6.3);g.fill();g.stroke();g.beginPath();g.arc(x,y,r-1,0,6.3);g.clip();fn&&fn();g.restore();};
  const dots=(x,y)=>{g.fillStyle='#777';[[-7,-3],[0,-5],[7,-3],[-4,4],[4,4]].forEach(a=>{g.beginPath();g.arc(x+a[0],y+a[1],3.4,0,6.3);g.fill();});};
  const tools=COPY['2.1'].tools,rowH=(h-20)/5;
  tools.forEach((t,i)=>{const y=10+rowH*(i+0.5),x=40;
    if(i===0){dish(x,y,22,()=>{});dots(x,y);g.save();g.strokeStyle=C.ink;g.setLineDash([4,3]);g.lineWidth=1.5;g.fillStyle='rgba(255,230,120,.45)';g.beginPath();g.arc(x+7,y-3,10,0,6.3);g.fill();g.stroke();g.restore();}
    else if(i===1){dish(x,y,22,()=>{g.fillStyle='rgba(120,160,200,.30)';g.fillRect(0,0,200,900);});dots(x,y);}
    else if(i===2){dish(x,y,22,()=>{const gr=g.createRadialGradient(x+6,y-4,1,x+6,y-4,18);gr.addColorStop(0,'rgba(80,80,80,.55)');gr.addColorStop(1,'rgba(80,80,80,0)');g.fillStyle=gr;g.fillRect(0,0,300,900);});dots(x,y);g.strokeStyle=C.ink;g.lineWidth=2;g.beginPath();g.moveTo(x+6,y-4);g.lineTo(x+26,y-30);g.stroke();}
    else if(i===3){dish(x,y,22,()=>{});dots(x,y);g.strokeStyle=C.ink;g.lineWidth=2.2;g.beginPath();g.moveTo(x,y-26);g.lineTo(x+12,y-4);g.moveTo(x+26,y-26);g.lineTo(x+14,y-4);g.stroke();g.fillStyle=C.ink;g.beginPath();g.arc(x+13,y-2,3,0,6.3);g.fill();}
    else{dish(x,y,22,()=>{});dots(x,y);g.strokeStyle=C.ink;g.lineWidth=2;g.setLineDash([5,3]);g.beginPath();g.moveTo(x-18,y+17);g.lineTo(x+18,y-17);g.stroke();g.setLineDash([]);}
    g.fillStyle=C.ink;g.textAlign='left';g.font='700 16px '+FONT;g.fillText(t[0],86,y-rowH*0.28);g.font='14px '+FONT;g.fillStyle='#333';wrapText(g,t[1],w-100).forEach((ln,j)=>g.fillText(ln,86,y-rowH*0.28+22+j*18));});
}
Demo.register({id:'2.1',act:2,title:COPY['2.1'].title,legend:LEG.light,data:['data/c21.js'],duration:0,
  caption:COPY['2.1'].caption,takeaway:COPY['2.1'].takeaway,
  notes:'The loops are real package-v3 runs (observable tier only, tracked cells): undisturbed natural dish run_00011; x-cut run_00263; dish fusion run_00640 (two clusters brought together); a light pulse run_01105 (the white dashed disc). The light channel number carries no meaning for the observer. Exemplar rule: lowest run id of each category. Tool names in the model: Light = L1–L5, Bath = reagents R1–R6, Pipette, Tweezers (displace one cell), Surgery (cut, replace, fuse).',
  sources:[{what:'Dish, toolbox and thumbnails: package-v3 O1 tracks',file:'testbed_blind_v3/runs/run_00011, run_00263, run_00640, run_01105 (_O1.npz)',sec:'catalog.csv, treatments.json'},{what:'Operation vocabulary',file:'testbed_blind_v3/DATA_DICTIONARY.md',sec:'Treatments'},{what:'Live API (calls, masks, budgets)',file:'testbed_v3/live/CLIENT_API.md'}],
  setup(c){
    const D=DATA.c21;const sz=Math.min(Demo.arenaSize(2,0),600);const top=el('div',{style:'display:flex;gap:14px;flex-wrap:wrap;justify-content:center;width:100%'},c.vis);
    const pw=document.createElement('div');pw.className='pw';top.appendChild(pw);c.pa=new Panel(pw,{size:sz,fov:9,title:'One dish'});c.pa.wrap=pw;c.panels.push(c.pa);
    const tw=el('div',{class:'pw'},top);el('div',{class:'ptitle'},tw,'The tools');const tcv=makeCanvas(tw,470,sz);drawToolbox(tcv,470,sz);
    const row=el('div',{style:'display:flex;gap:14px;flex-wrap:wrap;justify-content:center;width:100%;margin-top:6px'},c.vis);
    const names={Undisturbed:'Untouched',Cut:'Cut',Fusion:'Merge two organisms','Light pulse':'Light'};
    c.th=D.thumbs.map(t=>{const w=el('div',{class:'pw'},row);const p=new Panel(w,{size:200,fov:t.tag==='Fusion'?9:6.5,title:names[t.tag]});p.wrap=w;p.noBubble=true;
      const xy=t.xy.map(s=>B64.i16(s,1000));let cx=0,cy=0,m=0;xy.forEach(a=>{for(let i=0;i<a.length;i+=2){cx+=a[i];cy+=a[i+1];m++;}});p.cx=cx/m;p.cy=cy/m;return {p:p,t:t,xy:xy};});
    c.state.D=D;c.state.dish=B64.i16(D.dish.xy,1000);
    const t0=performance.now();Demo.tickers.push((ts)=>{const f=Math.max(0,Math.floor((ts-t0)/160));c.th.forEach(o=>{const n=o.t.ts.length,k=f%(n+6);const kk=Math.min(k,n-1);const t=o.t.ts[kk];o.p.clear();const a=o.xy[kk];const m=a.length/2;for(let i=0;i<m;i++)o.p.node({x:a[2*i],y:a[2*i+1],fill:'#777',r:0.4});
        if(o.t.light){const L=o.t.light;drawLight(o.p,L.xy,L.r,lightWindow(t,L.t_on,L.t_off,L.ramp));}
        if(o.t.onset!=null&&t>=o.t.onset)o.p.label('cut',100,188,{align:'center',size:12,color:'#222'});o.p.setSub('time '+t);});});
  },
  draw(c){
    const p=c.pa,a=c.state.dish,m=a.length/2;p.cx=0;p.cy=0;p.clear();
    const g=p.ctx;g.save();g.strokeStyle='#999';g.lineWidth=2;g.setLineDash([3,5]);const q=p.w2p(0,0);g.beginPath();g.arc(q[0],q[1],8.6*p.scale,0,6.3);g.stroke();g.restore();p.label('edge of the dish',p.w/2,p.h/2-8.6*p.scale-8,{align:'center',size:12,color:'#999'});p.scaleBar();
    for(let i=0;i<m;i++)p.node({x:a[2*i],y:a[2*i+1],fill:'#777',r:0.4});
    p.label('24 cells at a random spot and angle',p.w/2,p.h-40,{align:'center',size:13});}
});

/* ---------------- 2.2 (new) ---------------- */
const TOOLS22=['cut','pull','replace','merge','light','bath'];
Demo.register({id:'2.2',act:2,title:COPY['2.2'].title,data:['data/c22b.js'],duration:40,rate:3.5,truthOffered:false,
  legend:LEG.types.concat([{color:'#999',label:'undecided (newcomer)'}]),
  caption:COPY['2.2'].caption,takeaway:COPY['2.2'].takeaway,
  notes:'Truth view (true cell types from the hidden tier; a cell with no clear belief about its place is grey). Clips are existing package-v3 runs with their observed positions: Cut = run_00283 (x-cut, vector length 7.0 at t = 50; the dashed line separates the 12 moved cells from the rest just before the cut); Pull out a cell = run_00515 (tweezers, cell 5 displaced by 8.0 at t = 50); Replace a cell = run_00953 (first of its replacements, t = 50, newcomer id 24); Merge = run_00640 (dish fusion of two 24-cell organisms); Light = run_01105 (disc, t_on 40, t_off 66.7, ramp 5); Bath = run_01924 (reagent R6, amplitude 0.3, t_on 40, t_off 90, ramp 5). All times in time units. Marker rules: dashed black line = cut, tweezer icon = moved cell, flash + number = newcomer with its new id, lit disc = light, tinted dish = bath, dashed outlines + double arrow = two organisms placed together.',
  sources:[{what:'Cut, pull out, replace, merge, light, bath clips (observed positions + hidden cell types)',file:'testbed_blind_v3/runs/run_00283, run_00515, run_00953, run_00640, run_01105, run_01924 (_O1.npz); testbed_v3/data/blind_v3_hidden/*_hid.npz',sec:'treatments.json, catalog.csv'},{what:'Operation parameters (vector lengths 7.0 and 8.0; times)',file:'testbed_v3/data/blind_v3_hidden/*.json',sec:'events'},{what:'Build script',file:'demo_v1/build/build_c22b.py'}],
  setup(c){
    const D=DATA.c22b;c.state.D=D;c.state.tool='cut';const sz=Math.min(Demo.arenaSize(1,0),640);
    const sel=el('div',{class:'seg',id:'sel22'},c.ctrls);COPY['2.2'].buttons.forEach((nm,i)=>{const b=el('button',{},sel,nm);b.onclick=()=>this.pick(c,TOOLS22[i]);if(i===0)b.classList.add('on');});
    c.pa=c.panel({size:sz,fov:8,title:'',id:'arena'});
    TOOLS22.forEach(k=>{const cl=D[k];cl.XY=cl.frames.map(f=>B64.i16(f.xy,1000));
      // fixed view per clip
      let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;cl.XY.forEach(a=>{for(let i=0;i<a.length;i+=2){x0=Math.min(x0,a[i]);x1=Math.max(x1,a[i]);y0=Math.min(y0,a[i+1]);y1=Math.max(y1,a[i+1]);}});cl.view={cx:(x0+x1)/2,cy:(y0+y1)/2,fov:Math.max(7,Math.max(x1-x0,y1-y0)/2+2.2)};});
    c.state.pick=(k)=>this.pick(c,k);this.pick(c,'cut',true);},
  variants:TOOLS22.map(k=>({name:k,apply(c){c.state.pick(k);}})),
  clipT(c,k){const cl=c.state.D[k];return cl.ts;},
  pick(c,k,first){
    const D=c.state.D,cl=D[k],i=TOOLS22.indexOf(k);c.state.tool=k;document.querySelectorAll('#sel22 button').forEach((b,j)=>b.classList.toggle('on',j===i));
    const def=Demo.byId['2.2'];def.duration=cl.ts[cl.ts.length-1]-cl.ts[0];def.rate=def.duration/13;
    const t0=cl.ts[0];let tp,anchor;
    if(k==='cut'){tp=cl.onset+1-t0;anchor=()=>({panel:c.pa,x:(cl.line[0][0]+cl.line[1][0])/2-c.pa.cx,y:(cl.line[0][1]+cl.line[1][1])/2-c.pa.cy});}
    else if(k==='pull'){tp=cl.onset+1-t0;anchor=()=>{const f=cl.frames[tp],a=cl.XY[tp],j=f.ids.indexOf(cl.cell);return {panel:c.pa,x:a[2*j]-c.pa.cx,y:a[2*j+1]-c.pa.cy};};}
    else if(k==='replace'){tp=cl.onset+1-t0;anchor=()=>{const f=cl.frames[tp],a=cl.XY[tp],j=f.ids.indexOf(cl.new);return {panel:c.pa,x:a[2*j]-c.pa.cx,y:a[2*j+1]-c.pa.cy};};}
    else if(k==='merge'){tp=3;anchor=()=>({panel:c.pa,x:0,y:0});}
    else if(k==='light'){tp=cl.t_on+6-t0;anchor=()=>({panel:c.pa,x:cl.disc[0]-c.pa.cx,y:cl.disc[1]-c.pa.cy});}
    else{tp=cl.t_on+8-t0;anchor=()=>({panel:c.pa,x:c.pa.fov*0.55,y:c.pa.fov*0.75});}
    def.pauses=[{t:tp,text:COPY['2.2'].texts[i],side:'right',anchor:anchor}];
    c.pa.cx=cl.view.cx;c.pa.cy=cl.view.cy;c.pa.fov=cl.view.fov;c.pa.scale=Math.min(c.pa.w,c.pa.h)/(2*c.pa.fov);
    Demo.buildTicks();Demo.hideCallout();Demo.playing=false;Demo.seek(0);Demo.updPlay();
    Demo.setLegend(LEG.types.concat([{color:'#999',label:'undecided (newcomer)'}]).concat(k==='light'?LEG.light:[]));
    if(first===undefined&&Demo.cur&&Demo.cur.id==='2.2'){/* show the callout at once for the picked tool */Demo.seekPause(0);}
  },
  draw(c,t){
    const k=c.state.tool,D=c.state.D,cl=D[k],p=c.pa;const fi=Math.max(0,Math.min(cl.frames.length-1,Math.round(t))),T=cl.ts[fi];const ids=cl.frames[fi].ids,xy=cl.XY[fi],typ=cl.frames[fi].typ;
    p.clear();
    if(k==='bath'){const ph=lightWindow(T,cl.t_on,cl.t_off,cl.ramp);const g=p.ctx;g.save();g.fillStyle='rgba(86,140,190,'+(0.42*ph)+')';g.fillRect(0,0,p.w,p.h);g.strokeStyle='rgba(30,70,120,'+(0.9*ph)+')';g.lineWidth=5;g.strokeRect(3,3,p.w-6,p.h-6);g.restore();}
    p.scaleBar();
    if(k==='light'){drawLight(p,cl.disc,cl.r,lightWindow(T,cl.t_on,cl.t_off,cl.ramp));}
    if(k==='cut'){const ph=Math.max(0,Math.min(1,1-(T-cl.onset-8)/6));if(T>=cl.onset-12){p.line(cl.line[0],cl.line[1],{color:C.ink,w:3,dash:[9,6],alpha:Math.min(1,ph)});}}
    for(let j=0;j<ids.length;j++){const id=ids[j];let fill=typ[j]?TYPEC[typ[j]]:'#999';const n={x:xy[2*j],y:xy[2*j+1],fill:fill,r:0.4};
      if(k==='replace'&&id===cl.new){n.dash=[3,2];n.lw=2;}p.node(n);}
    if(k==='pull'){const j=ids.indexOf(cl.cell);const pj=[xy[2*j],xy[2*j+1]];
      if(T>=cl.onset-3&&T<cl.onset+4){const j0=cl.frames[Math.max(0,Math.round(cl.onset-1-cl.ts[0]))].ids.indexOf(cl.cell),a0=cl.XY[Math.max(0,Math.round(cl.onset-1-cl.ts[0]))];
        if(T>=cl.onset){p.arrow([a0[2*j0],a0[2*j0+1]],pj,{color:C.ink,w:2,dash:[6,4],head:10});tweezers(p,pj[0],pj[1]+0.15,1.0);}else tweezers(p,a0[2*j0],a0[2*j0+1]+0.15,1.0);}}
    if(k==='replace'){const j=ids.indexOf(cl.new);if(T>=cl.onset-0.01){const u=(T-cl.onset);if(u<6){flashAt(p,xy[2*j],xy[2*j+1],Math.min(1,u/3),0.4);}
        p.label('new #'+cl.new,xy[2*j],xy[2*j+1]+0.95,{align:'center',size:12.5,bold:true,world:true,bg:true});}}
    if(k==='merge'){const g={0:[],1:[]};ids.forEach((id,j)=>g[id<24?0:1].push([xy[2*j],xy[2*j+1]]));const cen=[0,1].map(q=>[g[q].reduce((a,b)=>a+b[0],0)/g[q].length,g[q].reduce((a,b)=>a+b[1],0)/g[q].length]);
      [0,1].forEach(q=>{const E=alphaEdges(g[q],1.5);E.forEach(e=>p.line(g[q][e[0]],g[q][e[1]],{color:C.ink,w:2.6,dash:[7,5]}));});
      const mid=[(cen[0][0]+cen[1][0])/2,(cen[0][1]+cen[1][1])/2],dx=cen[1][0]-cen[0][0],dy=cen[1][1]-cen[0][1],L=Math.hypot(dx,dy)||1,ux=dx/L,uy=dy/L,nx=-uy,ny=ux,off=3.9;
      p.arrow([mid[0]+nx*off-ux*1.0,mid[1]+ny*off-uy*1.0],[mid[0]+nx*off+ux*1.0,mid[1]+ny*off+uy*1.0],{color:C.ink,w:2.6,head:11});p.arrow([mid[0]+nx*off+ux*1.0,mid[1]+ny*off+uy*1.0],[mid[0]+nx*off-ux*1.0,mid[1]+ny*off-uy*1.0],{color:C.ink,w:2.6,head:11});}
    p.setSub('time '+(T-cl.ts[0]).toFixed(0));
  }
});

/* ---------------- 2.3 (was 2.2) ---------------- */
Demo.register({id:'2.3',act:2,title:COPY['2.3'].title,truthOffered:true,
  legend:[{color:'#777',label:'tracked cell'},{cls:'dash',label:'light (white disc, dashed edge)'},{color:'#444',label:'microscope image (false colour)'}],data:['data/c22.js','data/c23o.js'],duration:30,rate:3,
  caption:COPY['2.3'].caption,takeaway:COPY['2.3'].takeaway,
  notes:'Package-v3 run_01105 (a light pulse that truly switches the collective). O1: permanent ids, 3 % level noise, position noise 0.02. O2: same points, ids removed, rows shuffled. O3a: three fluorescence channels (c6, c2, c0), smooth (blob width about 1.4 units) so single cells are not resolved. O3c: a sharp cell-marker channel. The hidden panel shows the true memory rho per cell (colour), the believed place (number) and the reporter (ring): none of it is observable. “show outline” draws the grouping that the blind analysis (T4) code produces from each view: O1/O2 single-linkage groups (r_link 1.6, at least 3 cells, forward tracker), O3a foreground pixels of the smoothed c6 field, O3c spots from T5’s detector (gaussian smoothing + local maxima) linked by the same rule. Images are drawn with +y up (rows are stored bottom-up in the files).',
  sources:[{what:'Observables O1, O2, O3a, O3c for t = 36–66',file:'testbed_blind_v3/runs/run_01105_*.npz'},{what:'Hidden tier (rho, place beliefs, reporter) for the fifth panel',file:'testbed_v3/data/blind_v3_hidden/run_01105_hid.npz'},{what:'Observation levels',file:'testbed_blind_v3/DATA_DICTIONARY.md',sec:'Observation levels'},{what:'Per-view outlines (blind pipelines’ grouping code)',file:'demo_v1/data/c23o.js',sec:'build/build_c31.py run_01105 36 66 c23o'}],
  setup(c){
    const D=DATA.c22,G=DATA.c23o;c.state.D=D;c.state.G=G;c.state.outline=false;const sz=Math.min(Demo.arenaSize(5,0),400);const f=9;const T=COPY['2.3'].panels;
    c.p1=c.panel({size:sz,fov:f,title:T[0]});c.p2=c.panel({size:sz,fov:f,title:T[1]});c.p3=c.panel({size:sz,fov:f,title:T[2]});c.p4=c.panel({size:sz,fov:f,title:T[3]});c.p5=c.panel({size:sz,fov:f,title:T[4]});
    c.state.O1=D.O1.xy.map(s=>B64.i16(s,1000));c.state.O2=D.O2.map(s=>B64.i16(s,1000));c.state.ia=D.O3a.map(s=>null);c.state.ic=D.O3c.map(s=>null);
    c.state.H={X:D.hid.X.map(s=>B64.i16(s,1000)),rho:D.hid.rho.map(s=>B64.i16(s,20000)),e:D.hid.e.map(s=>B64.i16(s,20000))};
    c.state.G1=G.O1.xy.map(s=>B64.i16(s,1000));c.state.G2=G.O2.xy.map(s=>B64.i16(s,1000));c.state.Ma=G.O3a.lab.map(s=>B64.u8(s));c.state.Gc=G.O3c.xy.map(s=>B64.i16(s,1000));
    const lab=el('label',{},c.ctrls);const cb=el('input',{type:'checkbox'},lab);lab.appendChild(document.createTextNode(' '+COPY['2.3'].outline));cb.onchange=()=>{c.state.outline=cb.checked;Demo.redraw();};
    c.pauseAnch=[c.p1,c.p2,c.p3,c.p4,c.p5];
    Demo.byId['2.3'].pauses=COPY['2.3'].callouts.map((tx,i)=>({t:i*6,text:tx,side:'top',anchor:cc=>({panel:cc.pauseAnch[i],x:0,y:i===4?0.5:-0.5})}));Demo.buildTicks();},
  draw(c,t,truth){
    const D=c.state.D,G=c.state.G,k=Math.max(0,Math.min(D.ts.length-1,Math.round(t))),tt=D.ts[k],L=D.light,ph=lightWindow(tt,L.t_on,L.t_off,L.ramp),f=D.fovA,ol=c.state.outline;
    const dots=(p,xy,ids)=>{p.clear();p.scaleBar();for(let i=0;i<xy.length/2;i++)p.node({x:xy[2*i],y:xy[2*i+1],fill:'#777',r:0.4,label:ids?String(ids[i]):null});drawLight(p,L.xy,L.r,ph);};
    dots(c.p1,c.state.O1[k],D.O1.id[k]);dots(c.p2,c.state.O2[k],null);
    const crop=(p,cv,half,px)=>{p.clear('#000');const g=p.ctx;const s0=(half-p.fov)/(2*half)*px,sw=2*p.fov/(2*half)*px;g.save();g.imageSmoothingEnabled=true;g.drawImage(cv,s0,s0,sw,sw,0,0,p.w,p.h);g.restore();p.scaleBar();};
    if(!c.state.ia[k])c.state.ia[k]=img64(D.O3a[k],64,64,3);if(!c.state.ic[k])c.state.ic[k]=img64(D.O3c[k],128,128,1);
    crop(c.p3,c.state.ia[k],12,64);drawLight(c.p3,L.xy,L.r,ph);crop(c.p4,c.state.ic[k],10,128);drawLight(c.p4,L.xy,L.r,ph);
    if(ol){groupOutlinePts(c.p1,c.state.G1[k],G.O1.lab[k]);groupOutlinePts(c.p2,c.state.G2[k],G.O2.lab[k]);groupOutlineMask(c.p3,c.state.Ma[k],64,12);
      // O3c: spots linked by the same rule
      const sp=c.state.Gc[k],lb=G.O3c.lab[k];for(let i=0;i<lb.length;i++){const q=c.p4.w2p(sp[2*i],sp[2*i+1]);c.p4.ctx.save();c.p4.ctx.strokeStyle='#fff';c.p4.ctx.lineWidth=1.6;c.p4.ctx.beginPath();c.p4.ctx.arc(q[0],q[1],5,0,6.3);c.p4.ctx.stroke();c.p4.ctx.restore();}
      groupOutlinePts(c.p4,sp,lb,{w:3});[c.p1,c.p2,c.p3,c.p4].forEach(drawnTag);}
    const p=c.p5;p.clear(truth?'#fff':'#ECECE6');p.scaleBar();const X=c.state.H.X[k],R=c.state.H.rho[k],E=c.state.H.e[k];
    if(truth){for(let i=0;i<24;i++)p.node({x:X[2*i],y:X[2*i+1],fill:rhoColor(R[i]),ring:E[i]>0.5,r:0.4,label:String(D.hid.place[k][i]),lc:C.ink,stroke:TYPEC[D.hid.tmplType[D.hid.place[k][i]]],lw:3});drawLight(p,L.xy,L.r,ph);
      p.setSub('memory (colour), believed position (number, outline = its cell type), yellow marker (ring)');}
    else{const g=p.ctx;g.save();g.fillStyle='#777';g.font='700 15px '+FONT;g.textAlign='center';['guesses about position','memory of each cell','the body plan','the cells\' types'].forEach((s,i)=>g.fillText(s,p.w/2,p.h/2-30+i*24));g.restore();p.setSub('hidden from an observer (press T)');}
    c.p5.wrap.classList.toggle('dim',!truth);
    c.p1.setSub('time '+tt);
    Demo.setLegend(truth?[{color:'#777',label:'tracked cell'},{cls:'dash',label:'light'}].concat(LEG.rho).concat(LEG.reporter):[{color:'#777',label:'tracked cell'},{cls:'dash',label:'light (white disc, dashed edge)'},{color:'#444',label:'microscope image (false colour)'}]);
  },
  onTruth(c,on){if(c.p5)c.p5.setSub('');}
});
function img64(b64,w,h,ch,gray){return imgCanvas(b64,w,h,ch);}

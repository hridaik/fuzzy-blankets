/* app.js - navigation, playback, scripted pause points + callouts, truth toggle, notes, sources, key-frame export. */
'use strict';
const Demo = {
  chapters:[], byId:{}, cur:null, c:null, t:0, playing:false, speed:1, truth:false, presenter:false, pauseIdx:-1, lastTs:0, activePause:null, notesOn:false,
  register(def){this.chapters.push(def);this.byId[def.id]=def;},
  ACTS:(()=>{const o={};Object.keys(COPY.acts).forEach(k=>o[k]=(k==='A'?'':'Act '+k+' · ')+COPY.acts[k]);return o;})(),
  start(){
    this.buildSide();
    document.getElementById('bSide').onclick=()=>document.body.classList.toggle('side-collapsed');
    document.getElementById('bPlay').onclick=()=>this.toggle();
    document.getElementById('bRestart').onclick=()=>{this.hideCallout();this.seek(0);this.playing=false;this.updPlay();};
    document.getElementById('bT').onclick=()=>this.toggleTruth();
    document.getElementById('bNotes').onclick=()=>this.toggleNotes();
    document.getElementById('bPres').onclick=()=>this.togglePresenter();
    document.getElementById('bExport').onclick=()=>this.exportKeyFrames();
    document.getElementById('srcToggle').onclick=()=>{const s=document.getElementById('sources');s.style.display=s.style.display==='block'?'none':'block';};
    document.querySelectorAll('#speeds button').forEach(b=>b.onclick=()=>{this.speed=+b.dataset.s;document.querySelectorAll('#speeds button').forEach(x=>x.classList.toggle('on',x===b));});
    const sc=document.getElementById('scrub');
    sc.oninput=()=>{this.hideCallout();this.playing=false;this.updPlay();this.seek(sc.value/1000*this.c.def.duration,true);};
    window.addEventListener('keydown',e=>this.key(e));
    window.addEventListener('hashchange',()=>this.fromHash());
    window.addEventListener('resize',()=>{clearTimeout(this._rz);this._rz=setTimeout(()=>this.go(this.cur.id,true,true),200);});
    requestAnimationFrame(ts=>this.loop(ts));
    this.fromHash();
  },
  fromHash(){const h=(location.hash||'').replace('#','');const id=this.byId[h]?h:'1.1';if(!this.cur||this.cur.id!==id)this.go(id,false);},
  buildSide(){
    const s=document.getElementById('side');let h='<h1>A group memory that can be switched</h1>';let act=null;
    this.chapters.forEach(ch=>{if(ch.act!==act){act=ch.act;h+='<div class="act">'+this.ACTS[act]+'</div>';}h+='<a href="#'+ch.id+'" data-id="'+ch.id+'"><span class="no">'+ch.id+'</span>'+ch.title+'</a>';});
    s.innerHTML=h;
  },
  key(e){
    if(e.target&&['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName)&&e.key!==' '&&!e.key.startsWith('Arrow'))return;
    if(e.target&&e.target.tagName==='INPUT'&&e.target.type==='range'&&(e.key==='ArrowLeft'||e.key==='ArrowRight'))return;
    if(e.key==='ArrowRight'){this.step(1);e.preventDefault();}
    else if(e.key==='ArrowLeft'){this.step(-1);e.preventDefault();}
    else if(e.key===' '){this.toggle();e.preventDefault();}
    else if(e.key==='f'||e.key==='F')this.togglePresenter();
    else if(e.key==='n'||e.key==='N')this.toggleNotes();
    else if(e.key==='t'||e.key==='T')this.toggleTruth();
  },
  step(d){const i=this.chapters.indexOf(this.cur)+d;if(i>=0&&i<this.chapters.length)location.hash='#'+this.chapters[i].id;},
  toast(m){const t=document.getElementById('toast');t.textContent=m;t.style.display='block';clearTimeout(this._tt);this._tt=setTimeout(()=>t.style.display='none',1800);},
  /* ----- chapter load ----- */
  async go(id,keepT,resized){
    const def=this.byId[id];if(!def)return;const prevT=keepT?this.t:0;
    this.cur=def;this.tickers=[];this.playing=false;this.hideCallout();this.activePause=null;this.pauseIdx=-1;
    document.querySelectorAll('#side a').forEach(a=>a.classList.toggle('cur',a.dataset.id===id));
    document.getElementById('title').innerHTML='<small>'+this.ACTS[def.act]+' · '+def.id+'</small>'+def.title;
    document.getElementById('caption').innerHTML=def.caption||'';document.getElementById('takeaway').textContent=def.takeaway||'';document.getElementById('hint').textContent=def.hint||'';document.getElementById('sources').style.display='none';
    const vis=document.getElementById('vis'),ctrls=document.getElementById('ctrls'),leg=document.getElementById('legend');vis.innerHTML='';ctrls.innerHTML='';vis.style.padding='0';
    leg.innerHTML=(def.legend||[]).map(chipHTML).join('');
    this.buildSources(def);document.getElementById('notes').innerHTML='<h4>Speaker notes</h4>'+(def.notes||'—');
    document.getElementById('bT').style.display=def.truthOffered?'':'none';
    if(!def.truthOffered&&this.truth){this.truth=false;document.body.classList.remove('truth');document.getElementById('bT').classList.remove('on');}
    document.getElementById('bExport').title='save PNGs of the scripted pause points of this chapter';
    const c={def:def,vis:vis,ctrls:ctrls,panels:[],state:{},Demo:this,
      panel(o){const p=new Panel(vis,o);c.panels.push(p);return p;},
      union(){let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;c.panels.forEach(p=>{const r=p.rect();x0=Math.min(x0,r.x);y0=Math.min(y0,r.y);x1=Math.max(x1,r.x+r.w);y1=Math.max(y1,r.y+r.h);});return {x:x0,y:y0,w:x1-x0,h:y1-y0};}};
    this.c=c;
    try{
      for(const s of (def.data||[]))await loadScript(s);
      def.setup(c);
    }catch(err){vis.innerHTML='<div class="ph">Chapter could not be built: '+err.message+'</div>';console.error(err);}
    this.buildTicks();
    this.t=Math.min(prevT,def.duration||0);this.truthApply();this.redraw();this.updPlay();
    if(!keepT&&def.duration&&(def.pauses||[]).length&&def.pauses[0].t===0){setTimeout(()=>{if(this.cur===def&&!this.playing){this.showPause(0);this.updPlay();}},30);}
  },
  buildSources(def){
    const s=document.getElementById('sources');s.innerHTML='<b>Sources</b><ol style="margin:4px 0 0 18px;padding:0">'+(def.sources||[]).map(x=>'<li>'+x.what+' — <code>'+x.file+'</code>'+(x.sec?' ('+x.sec+')':'')+'</li>').join('')+'</ol>'+(def.audit?'<div style="margin-top:4px"><b>Audit note:</b> '+def.audit+'</div>':'');
    document.getElementById('srcShort').textContent='';
  },
  buildTicks(){
    const def=this.cur,tk=document.getElementById('ticks'),sc=document.getElementById('scrub');tk.innerHTML='';
    const has=def.duration>0;sc.disabled=!has;document.getElementById('bPlay').disabled=!has;document.getElementById('bRestart').disabled=!has;
    if(has)(def.pauses||[]).forEach((p,i)=>{const e=document.createElement('i');e.style.left=(p.t/def.duration*100)+'%';e.title='pause '+(i+1);tk.appendChild(e);});
  },
  /* ----- playback ----- */
  rate(){const d=this.cur;return (d.rate||(d.duration/16))*this.speed*(d.speedAt&&this.c?d.speedAt(this.c,this.t):1);},
  toggle(){
    if(!this.cur.duration)return;
    if(this.t>=this.cur.duration-1e-6){this.seek(0);}
    this.hideCallout();this.playing=!this.playing;this.updPlay();this.lastTs=0;
  },
  updPlay(){const b=document.getElementById('bPlay');const atPause=this.activePause!=null;b.textContent=this.playing?'❚❚ Pause':(atPause?'▶ Continue':'▶ Play');},
  tickers:[],
  loop(ts){
    this.tickers.forEach(f=>{try{f(ts);}catch(e){console.error(e);}});
    if(this.playing&&this.cur&&this.cur.duration){
      if(!this.lastTs)this.lastTs=ts;const dt=Math.min((ts-this.lastTs)/1000,0.1);this.lastTs=ts;
      const t0=this.t;let t1=t0+dt*this.rate();const ps=this.cur.pauses||[];
      for(let i=0;i<ps.length;i++){if(ps[i].t>t0+1e-9&&ps[i].t<=t1+1e-9){t1=ps[i].t;this.t=t1;this.playing=false;this.redraw();this.showPause(i);this.updPlay();break;}}
      if(this.playing){this.t=t1;if(this.t>=this.cur.duration){this.t=this.cur.duration;this.playing=false;this.updPlay();}this.redraw();}
    }else this.lastTs=0;
    requestAnimationFrame(ts=>this.loop(ts));
  },
  seek(t,fromScrub){this.t=Math.max(0,Math.min(t,this.cur.duration||0));if(!fromScrub)this.hideCallout();this.redraw();},
  seekPause(i){const p=this.cur.pauses[i];this.playing=false;this.t=p.t;this.redraw();this.showPause(i);this.updPlay();},
  redraw(){
    const def=this.cur,c=this.c;if(!def||!c)return;try{def.draw&&def.draw(c,this.t,this.truth);}catch(err){console.error(err);}
    document.getElementById('tlabel').textContent=def.duration?(def.unit==='step'?('callout '+((this.activePause==null?0:this.activePause)+1)+' of '+((def.pauses||[]).length||1)):('time '+this.t.toFixed(0)+' of '+Math.round(def.duration)+' time units')):'';
    if(def.duration)document.getElementById('scrub').value=Math.round(this.t/def.duration*1000);
    if(this.activePause!=null&&this.c){/* keep bubble in place */}
  },
  /* ----- callouts ----- */
  showPause(i){
    const p=this.cur.pauses[i];this.activePause=i;const c=this.c;const bub=document.getElementById('bubble'),svg=document.getElementById('leader');
    bub.innerHTML=p.text+'<small>space = continue</small>';bub.style.display='block';
    let a=null;try{a=p.anchor?p.anchor(c):null;}catch(e){console.error(e);}
    const U=c.union(),sw=document.getElementById('stagewrap').getBoundingClientRect();
    const minPw=Math.min(...c.panels.map(pp=>pp.w));bub.style.maxWidth=(minPw<400?210:250)+'px';const bw=Math.min(minPw<400?210:250,bub.offsetWidth||250),bh=bub.offsetHeight||60;let ap=a?(a.panel?a.panel.anchor(a.x,a.y):a.px):[U.x+U.w/2,U.y+U.h/2];
    const avoid=this.avoidRects(c);const W=sw.width,Hh=sw.height;const cands=[];
    const addP=(r)=>{const m=10;[r.x+m,r.x+r.w-bw-m,r.x+(r.w-bw)/2].forEach(x=>[r.y+m,r.y+r.h-bh-m,r.y+(r.h-bh)/2].forEach(y=>cands.push({x:x,y:y})));};
    if(p.side==='top')cands.push({x:ap[0]-bw/2,y:U.y-bh-28});
    cands.push({x:U.x-bw-14,y:ap[1]-bh/2},{x:U.x+U.w+14,y:ap[1]-bh/2});
    c.panels.forEach(pp=>{if(!pp.noBubble)addP(pp.rect());});
    cands.push({x:ap[0]-bw/2,y:U.y-bh-28},{x:ap[0]-bw/2,y:U.y+U.h+6});
    const hit=(r,q)=>!(r.x+bw<=q.x||q.x+q.w<=r.x||r.y+bh<=q.y||q.y+q.h<=r.y);
    let best=null,bd=1e9;
    const lgb=document.getElementById('ctrls').getBoundingClientRect();const minY=Math.max(2,lgb.bottom-sw.top+2);
    cands.forEach(cd=>{if(cd.x<2||cd.x+bw>W-2||cd.y<minY)return;if(avoid.some(q=>hit(cd,q)))return;const d=Math.hypot(cd.x+bw/2-ap[0],cd.y+bh/2-ap[1])+(p.side==='left'&&cd.x>ap[0]?200:0)+(p.side==='right'&&cd.x<ap[0]?200:0);if(d<bd){bd=d;best=cd;}});
    if(!best)best={x:Math.max(2,Math.min(ap[0]-bw/2,W-bw-2)),y:Math.max(minY,U.y-bh-28)};
    let x=best.x,y=best.y;if(p.offset){x+=p.offset[0];y+=p.offset[1];}
    bub.style.left=x+'px';bub.style.top=y+'px';bub.style.maxWidth=bw+'px';
    // leader line from the bubble edge point nearest to the anchor
    const bx=Math.max(x,Math.min(ap[0],x+bw)),by=Math.max(y,Math.min(ap[1],y+bh));
    svg.innerHTML=a?('<line x1="'+bx+'" y1="'+by+'" x2="'+ap[0]+'" y2="'+ap[1]+'" stroke="#222" stroke-width="1.4"/><circle cx="'+ap[0]+'" cy="'+ap[1]+'" r="4.5" fill="#FFFBE6" stroke="#222" stroke-width="1.5"/>'):'';
    this._bubble={x:x,y:y,w:bw,h:bh,ap:ap,text:p.text};
  },
  showView(i){const v=this.cur.views[i];this.activeView=i;if(v.apply)v.apply(this.c);this.redraw();const c=this.c;const bub=document.getElementById('bubble'),svg=document.getElementById('leader');this.cur.pauses=this.cur.pauses||[];
    const fake={text:v.text,anchor:v.anchor,side:v.side};const save=this.cur.pauses;this.cur.pauses=[fake];this.showPause(0);this.cur.pauses=save;this.activePause=null;},
  avoidRects(c){const out=[];const sw=document.getElementById('stagewrap').getBoundingClientRect();c.panels.forEach(p=>{const r=p.rect();if(p.avoidAll){out.push({x:r.x,y:r.y,w:r.w,h:r.h});return;}
      out.push({x:r.x+8,y:r.y+r.h-34,w:Math.min(r.w-8,p.scale+190),h:30});
      (p._nodes||[]).forEach(n=>{const q=p.w2p(n[0],n[1]),k=r.w/p.w,rr=(n[2]*p.scale+4)*k;out.push({x:r.x+q[0]*k-rr,y:r.y+q[1]*(r.h/p.h)-rr,w:2*rr,h:2*rr});});});(c.extraAvoid?c.extraAvoid():[]).forEach(q=>out.push(q));document.querySelectorAll('#vis canvas[data-avoid]').forEach(k=>{const r=k.getBoundingClientRect();out.push({x:r.left-sw.left,y:r.top-sw.top,w:r.width,h:r.height});});return out;},
  hideCallout(){this.activePause=null;document.getElementById('bubble').style.display='none';document.getElementById('leader').innerHTML='';this._bubble=null;},
  /* ----- modes ----- */
  toggleTruth(){if(!this.cur.truthOffered){this.toast('No hidden-truth view in this chapter');return;}this.truth=!this.truth;this.truthApply();this.redraw();},
  truthApply(){document.body.classList.toggle('truth',this.truth&&!!this.cur.truthOffered);document.getElementById('bT').classList.toggle('on',this.truth);
    if(this.cur.onTruth)try{this.cur.onTruth(this.c,this.truth);}catch(e){console.error(e);}},
  toggleNotes(){this.notesOn=!this.notesOn;document.getElementById('notes').style.display=this.notesOn?'block':'none';document.getElementById('bNotes').classList.toggle('on',this.notesOn);},
  togglePresenter(){this.presenter=!this.presenter;document.body.classList.toggle('presenter',this.presenter);document.getElementById('bPres').classList.toggle('on',this.presenter);setTimeout(()=>this.go(this.cur.id,true),50);},
  arenaSize(n,sidePad){ // size of one panel when n panels share a row
    const sc=document.getElementById('scroll'),main=sc.clientWidth-32-(sidePad||0)*2;
    const maxH=Math.max(520,sc.clientHeight-150);let s=Math.floor((main-14*(n-1))/n);return Math.max(n>4?190:(n>2?300:520),Math.min(s,n>2?640:Math.min(maxH,760)));},
  setLegend(items){document.getElementById('legend').innerHTML=(items||[]).map(chipHTML).join('');this.cur._legend=items;},
  /* ----- export ----- */
  compose(){
    const sw=document.getElementById('stagewrap'),r0=sw.getBoundingClientRect(),W=Math.round(r0.width),c=this.c;const def=this.cur;
    const capH=170;const H=Math.round(r0.height)+capH;const cv=document.createElement('canvas');const d=1;cv.width=W;cv.height=H;const g=cv.getContext('2d');
    g.fillStyle=C.bg;g.fillRect(0,0,W,H);
    // legend row
    g.font='13px '+FONT;g.textBaseline='middle';let lx=8;const ly=14;
    (def._legend||def.legend||[]).forEach(it=>{const col=it.color||'#999';g.fillStyle=it.cls==='ring'?'transparent':col;if(it.cls==='ring'){g.strokeStyle=C.rep;g.lineWidth=3;g.beginPath();g.arc(lx+7,ly,6,0,6.3);g.stroke();g.strokeStyle=C.ink;g.lineWidth=1;g.beginPath();g.arc(lx+7,ly,8,0,6.3);g.stroke();}
      else if(it.cls==='dash'||it.cls==='solid'){g.strokeStyle=it.color||C.ink;g.lineWidth=2;g.setLineDash(it.cls==='dash'?[4,3]:[]);g.beginPath();g.moveTo(lx,ly);g.lineTo(lx+16,ly);g.stroke();g.setLineDash([]);}
      else if(it.cls==='band'){g.fillStyle=C.band;g.fillRect(lx,ly-6,14,12);}
      else{g.beginPath();g.arc(lx+7,ly,7,0,6.3);g.fill();g.strokeStyle='rgba(0,0,0,.4)';g.lineWidth=1;g.stroke();}
      g.fillStyle=C.ink;g.textAlign='left';g.fillText(it.label,lx+20,ly);lx+=22+g.measureText(it.label).width+14;});
    // panels
    const pr=document.querySelectorAll('#vis .pw');
    pr.forEach(w=>{const t=w.querySelector('.ptitle'),cvs=w.querySelectorAll('canvas'),sub=w.querySelector('.psub');
      if(t){const r=t.getBoundingClientRect();g.fillStyle=C.ink;g.font='700 14px '+FONT;g.textAlign='center';g.fillText(t.textContent,r.left-r0.left+r.width/2,r.top-r0.top+r.height/2);}
      cvs.forEach(k=>{const r=k.getBoundingClientRect();if(r.width<2||!k.width)return;g.drawImage(k,r.left-r0.left,r.top-r0.top,r.width,r.height);});
      if(sub&&sub.textContent){const r=sub.getBoundingClientRect();g.fillStyle=C.mute;g.font='13px '+FONT;g.textAlign='center';g.fillText(sub.textContent,r.left-r0.left+r.width/2,r.top-r0.top+r.height/2);}});
    document.querySelectorAll('#vis .tcap').forEach(tc=>{g.textBaseline='top';Array.from(tc.children).forEach((ch,i)=>{const r=ch.getBoundingClientRect();g.fillStyle=C.ink;g.font=(i%2===0?'700 ':'')+'14.5px '+FONT;g.textAlign=i%2===0?'right':'left';wrapText(g,ch.textContent,r.width).forEach((ln,j)=>g.fillText(ln,(i%2===0?r.right:r.left)-r0.left,r.top-r0.top+j*19));});});
    document.querySelectorAll('#vis canvas').forEach(k=>{if(k.closest('.pw'))return;const r=k.getBoundingClientRect();if(r.width<2||!k.width)return;g.drawImage(k,r.left-r0.left,r.top-r0.top,r.width,r.height);});
    // bubble
    if(this._bubble){const b=this._bubble;g.strokeStyle=C.ink;g.lineWidth=1.4;g.beginPath();const bx=Math.max(b.x,Math.min(b.ap[0],b.x+b.w)),by=Math.max(b.y,Math.min(b.ap[1],b.y+b.h));g.moveTo(bx,by);g.lineTo(b.ap[0],b.ap[1]);g.stroke();
      g.fillStyle='#FFFBE6';g.beginPath();g.arc(b.ap[0],b.ap[1],4.5,0,6.3);g.fill();g.stroke();
      g.fillStyle='#FFFBE6';g.strokeStyle=C.ink;g.lineWidth=1.5;g.beginPath();g.roundRect(b.x,b.y,b.w,b.h,8);g.fill();g.stroke();
      g.fillStyle=C.ink;g.font='15px '+FONT;g.textAlign='left';g.textBaseline='top';const plain=b.text.replace(/<[^>]+>/g,'');wrapText(g,plain,b.w-22).forEach((ln,i)=>g.fillText(ln,b.x+11,b.y+8+i*19.5));}
    // caption + takeaway
    g.fillStyle=C.ink;g.textBaseline='top';g.textAlign='left';let y=Math.round(r0.height)+10;g.font='16.5px '+FONT;
    wrapText(g,(def.caption||'').replace(/<[^>]+>/g,''),W-24).forEach(ln=>{g.fillText(ln,12,y);y+=23;});
    if(def.hint){g.font='15px '+FONT;wrapText(g,def.hint,W-24).forEach(ln=>{g.fillText(ln,12,y);y+=21;});}g.font='700 18px '+FONT;wrapText(g,def.takeaway||'',W-24).forEach(ln=>{g.fillText(ln,12,y+4);y+=26;});
    g.font='12px '+FONT;g.fillStyle=C.mute;g.fillText('Chapter '+def.id+' · '+def.title+'  ·  contains hidden information',12,H-16);
    return cv;
  },
  async exportKeyFrames(){
    const def=this.cur;const saved=this.t;const out=[];
    const save=(cv,name)=>new Promise(res=>cv.toBlob(b=>{const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();res();},60);},'image/png'));
    const base=def.id.replace('.','_');
    const runPauses=async(tag)=>{const ps=def.pauses||[];for(let i=0;i<ps.length;i++){this.seekPause(i);await new Promise(r=>setTimeout(r,80));const cv=this.compose();const nm=base+(tag?'_'+tag:'')+'_pause'+(i+1)+'.png';out.push(nm);await save(cv,nm);}};
    if(def.variants){for(const v of def.variants){v.apply(this.c);await new Promise(r=>setTimeout(r,80));await runPauses(v.name);}this.hideCallout();}
    else if(def.duration&&(def.pauses||[]).length){await runPauses('');this.hideCallout();this.seek(saved);}
    else if(def.views){for(let i=0;i<def.views.length;i++){this.showView(i);await new Promise(r=>setTimeout(r,80));const cv=this.compose();const nm=base+'_view'+(i+1)+'.png';out.push(nm);await save(cv,nm);}this.hideCallout();}
    else{const cv=this.compose();out.push(base+'_frame.png');await save(cv,base+'_frame.png');}
    this.toast('Saved '+out.length+' PNG(s) of chapter '+def.id);this.exported=out;return out;
  }
};
if(!CanvasRenderingContext2D.prototype.roundRect){CanvasRenderingContext2D.prototype.roundRect=function(x,y,w,h,r){this.moveTo(x+r,y);this.arcTo(x+w,y,x+w,y+h,r);this.arcTo(x+w,y+h,x,y+h,r);this.arcTo(x,y+h,x,y,r);this.arcTo(x,y,x+w,y,r);this.closePath();};}

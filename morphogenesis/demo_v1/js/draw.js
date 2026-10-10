/* draw.js - colour language, data decoding, Panel (canvas arena), geometry helpers, charts.  CONTAINS HIDDEN INFORMATION (via data files). */
'use strict';
const C = {head:'#D55E00', trunk:'#0072B2', limb:'#009E73', tail:'#E69F00', sa:'#56B4E9', sb:'#CC79A7', rep:'#F0E442',
  ink:'#222', mid:'#DDDDDD', band:'#E8E8E8', bg:'#FAFAF7', mute:'#666', ok:'#1b6b3a', bad:'#9b1c1c', grey:'#777'};
const TYPEC = [null, C.head, C.trunk, C.limb, C.tail];          // v3 types 1..4 = head, trunk, limb, tail
const TYPENAME = [null, 'head', 'middle', 'side', 'tail'];
const FONT = 'system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif';
function hex2rgb(h){h=h.replace('#','');return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)];}
function mixc(a,b,u){const A=hex2rgb(a),B=hex2rgb(b);return 'rgb('+A.map((v,i)=>Math.round(v+(B[i]-v)*u)).join(',')+')';}
function mixrgb(a,b,u){const A=hex2rgb(a),B=hex2rgb(b);return A.map((v,i)=>v+(B[i]-v)*u);}
/* memory colour: rho = P(state a). rho=1 -> state-a colour, rho=0 -> state-b colour, 0.5 -> #DDDDDD */
function rhoColor(r){r=Math.max(0,Math.min(1,r));return r>=.5?mixc(C.mid,C.sa,(r-.5)*2):mixc(C.mid,C.sb,(.5-r)*2);}
function rhoRGB(r){r=Math.max(0,Math.min(1,r));return r>=.5?mixrgb(C.mid,C.sa,(r-.5)*2):mixrgb(C.mid,C.sb,(.5-r)*2);}
/* ---------- data decoding ---------- */
const B64 = {
  raw(s){const b=atob(s),n=b.length,u=new Uint8Array(n);for(let i=0;i<n;i++)u[i]=b.charCodeAt(i);return u;},
  i16(s,scale){const u=B64.raw(s);const a=new Int16Array(u.buffer,u.byteOffset,u.length>>1);const o=new Float32Array(a.length);const k=1/(scale||1);for(let i=0;i<a.length;i++)o[i]=a[i]*k;return o;},
  u8(s){return B64.raw(s);}
};
window.DATA = window.DATA || {};
const loadedScripts = {};
function loadScript(src){
  if(loadedScripts[src]) return loadedScripts[src];
  loadedScripts[src] = new Promise((res,rej)=>{const s=document.createElement('script');s.src=src;s.onload=res;s.onerror=()=>rej(new Error('cannot load '+src));document.head.appendChild(s);});
  return loadedScripts[src];
}
/* ---------- geometry ---------- */
function dist(a,b){return Math.hypot(a[0]-b[0],a[1]-b[1]);}
function components(P,r){const n=P.length,lab=new Array(n).fill(-1);let c=0;
  for(let i=0;i<n;i++){if(lab[i]>=0)continue;const st=[i];lab[i]=c;while(st.length){const u=st.pop();for(let j=0;j<n;j++)if(lab[j]<0&&dist(P[u],P[j])<r){lab[j]=c;st.push(j);}}c++;}
  return {lab,n:c};}
function delaunay(P){ // Bowyer-Watson, returns triangles (index triples)
  const n=P.length;let minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9;P.forEach(p=>{minx=Math.min(minx,p[0]);maxx=Math.max(maxx,p[0]);miny=Math.min(miny,p[1]);maxy=Math.max(maxy,p[1]);});
  const dm=Math.max(maxx-minx,maxy-miny)*20+10,mx=(minx+maxx)/2,my=(miny+maxy)/2;
  const V=P.concat([[mx-dm,my-dm],[mx,my+dm],[mx+dm,my-dm]]);let T=[[n,n+1,n+2]];
  const cc=t=>{const [a,b,c]=t.map(i=>V[i]);const d=2*(a[0]*(b[1]-c[1])+b[0]*(c[1]-a[1])+c[0]*(a[1]-b[1]));
    const ux=((a[0]**2+a[1]**2)*(b[1]-c[1])+(b[0]**2+b[1]**2)*(c[1]-a[1])+(c[0]**2+c[1]**2)*(a[1]-b[1]))/d;
    const uy=((a[0]**2+a[1]**2)*(c[0]-b[0])+(b[0]**2+b[1]**2)*(a[0]-c[0])+(c[0]**2+c[1]**2)*(b[0]-a[0]))/d;return [ux,uy,Math.hypot(a[0]-ux,a[1]-uy)];};
  for(let i=0;i<n;i++){const p=V[i];const bad=[],keep=[];T.forEach(t=>{const c=cc(t);(Math.hypot(p[0]-c[0],p[1]-c[1])<c[2]-1e-12?bad:keep).push(t);});
    const E={};bad.forEach(t=>{[[t[0],t[1]],[t[1],t[2]],[t[2],t[0]]].forEach(e=>{const k=Math.min(e[0],e[1])+'_'+Math.max(e[0],e[1]);E[k]=(E[k]||0)+1;E[k+'e']=e;});});
    T=keep;Object.keys(E).forEach(k=>{if(!k.endsWith('e')&&E[k]===1){const e=E[k+'e'];T.push([e[0],e[1],i]);}});}
  return T.filter(t=>t.every(i=>i<n));}
function circumR(P,t){const [a,b,c]=t.map(i=>P[i]);const A=dist(b,c),B=dist(a,c),Cc=dist(a,b);const s=(A+B+Cc)/2;const area=Math.sqrt(Math.max(s*(s-A)*(s-B)*(s-Cc),1e-12));return A*B*Cc/(4*area);}
function alphaEdges(P,alpha){ // boundary edges of the alpha shape
  const T=delaunay(P).filter(t=>circumR(P,t)<alpha);const E={};
  T.forEach(t=>[[t[0],t[1]],[t[1],t[2]],[t[2],t[0]]].forEach(e=>{const k=Math.min(e[0],e[1])+'_'+Math.max(e[0],e[1]);if(!E[k])E[k]={e:e,c:0};E[k].c++;}));
  return Object.values(E).filter(o=>o.c===1).map(o=>o.e);}
function mstMax(P){const n=P.length;if(n<2)return 0;const used=new Array(n).fill(false),d=new Array(n).fill(1e9);d[0]=0;let mx=0;
  for(let k=0;k<n;k++){let u=-1;for(let i=0;i<n;i++)if(!used[i]&&(u<0||d[i]<d[u]))u=i;used[u]=true;mx=Math.max(mx,d[u]);for(let j=0;j<n;j++)if(!used[j])d[j]=Math.min(d[j],dist(P[u],P[j]));}
  return mx;}
function lerp(a,b,u){return a+(b-a)*u;}
function frameAt(arr,t,dt){ // linear interpolation index helper: returns [i0,i1,u]
  const x=Math.max(0,t/dt);const i0=Math.min(Math.floor(x),arr-1);const i1=Math.min(i0+1,arr-1);return [i0,i1,Math.min(1,x-i0)];}
/* ---------- text ---------- */
function wrapText(ctx,text,maxw){const words=text.split(' '),lines=[];let cur='';words.forEach(w=>{const t=cur?cur+' '+w:w;if(ctx.measureText(t).width>maxw&&cur){lines.push(cur);cur=w;}else cur=t;});if(cur)lines.push(cur);return lines;}
/* ---------- Panel: one square (or rectangular) arena canvas ---------- */
class Panel{
  constructor(parent,o){
    o=o||{};this.w=o.w||o.size||560;this.h=o.h||o.size||560;this.fov=o.fov||6;this.cx=o.cx||0;this.cy=o.cy||0;this.title=o.title||'';this.sub=o.sub||'';this.id=o.id||'';
    this.wrap=document.createElement('div');this.wrap.className='pw';
    this.tEl=document.createElement('div');this.tEl.className='ptitle';this.tEl.textContent=this.title;this.wrap.appendChild(this.tEl);
    this.canvas=document.createElement('canvas');this.wrap.appendChild(this.canvas);
    this.sEl=document.createElement('div');this.sEl.className='psub';this.sEl.innerHTML=this.sub;this.wrap.appendChild(this.sEl);
    this.tag=document.createElement('div');this.tag.className='truthtag';this.tag.textContent='TRUTH';this.wrap.appendChild(this.tag);
    parent.appendChild(this.wrap);this.setSize(this.w,this.h);this.onclick=null;
    this.canvas.addEventListener('click',e=>{if(this.onclick){const r=this.canvas.getBoundingClientRect();const px=(e.clientX-r.left)*(this.w/r.width),py=(e.clientY-r.top)*(this.h/r.height);this.onclick(this.p2w(px,py),px,py,e);}});
  }
  setSize(w,h){this.w=w;this.h=h;const d=Math.min(window.devicePixelRatio||1,2);this.dpr=d;this.canvas.width=Math.round(w*d);this.canvas.height=Math.round(h*d);this.canvas.style.width=w+'px';this.canvas.style.height=h+'px';
    this.ctx=this.canvas.getContext('2d');this.ctx.setTransform(d,0,0,d,0,0);this.scale=Math.min(w,h)/(2*this.fov);}
  setTitle(t){this.title=t;this.tEl.textContent=t;}
  setSub(h){this.sub=h;this.sEl.innerHTML=h;}
  w2p(x,y){return [(x-this.cx)*this.scale+this.w/2,this.h/2-(y-this.cy)*this.scale];}
  p2w(px,py){return [(px-this.w/2)/this.scale+this.cx,-(py-this.h/2)/this.scale+this.cy];}
  clear(bg){this._nodes=[];const c=this.ctx;c.save();c.setTransform(this.dpr,0,0,this.dpr,0,0);c.fillStyle=bg||'#EDEDE8';c.fillRect(0,0,this.w,this.h);c.restore();}
  /* page coordinates of a world point relative to #stagewrap */
  anchor(x,y){const sw=document.getElementById('stagewrap').getBoundingClientRect(),r=this.canvas.getBoundingClientRect();const p=this.w2p(x,y);
    return [r.left-sw.left+p[0]*(r.width/this.w),r.top-sw.top+p[1]*(r.height/this.h)];}
  rect(){const sw=document.getElementById('stagewrap').getBoundingClientRect(),r=this.canvas.getBoundingClientRect();return {x:r.left-sw.left,y:r.top-sw.top,w:r.width,h:r.height};}
  scaleBar(){const c=this.ctx,L=this.scale,x0=14,y0=this.h-16;c.save();c.strokeStyle=C.ink;c.fillStyle=C.ink;c.lineWidth=2;c.beginPath();c.moveTo(x0,y0);c.lineTo(x0+L,y0);c.moveTo(x0,y0-4);c.lineTo(x0,y0+4);c.moveTo(x0+L,y0-4);c.lineTo(x0+L,y0+4);c.stroke();
    c.font='12px '+FONT;c.textBaseline='bottom';c.fillText('1 cell-width',x0+L+8,y0+5);c.restore();}
  label(txt,x,y,o){o=o||{};const c=this.ctx;if(o.world){const q=this.w2p(x,y);x=q[0];y=q[1];}c.save();c.font=(o.bold?'700 ':'')+(o.size||13)+'px '+FONT;c.fillStyle=o.color||C.ink;c.textAlign=o.align||'left';c.textBaseline=o.base||'middle';
    if(o.bg){const w=c.measureText(txt).width;c.fillStyle='rgba(255,255,255,.85)';c.fillRect((o.align==='center'?x-w/2:o.align==='right'?x-w:x)-3,y-9,w+6,18);c.fillStyle=o.color||C.ink;}
    c.fillText(txt,x,y);c.restore();}
  /* node: n = {x,y,fill,ring,r,stroke,dash,label,alpha} (world coordinates) */
  node(n,o){o=o||{};const c=this.ctx,p=this.w2p(n.x,n.y),r=(n.r||0.40)*this.scale;(this._nodes||(this._nodes=[])).push([n.x,n.y,(n.r||0.40)+(n.ring?0.16:0)]);c.save();
    if(n.alpha!=null)c.globalAlpha=n.alpha;
    c.shadowColor='rgba(0,0,0,.28)';c.shadowBlur=7;c.shadowOffsetY=2;c.fillStyle=n.fill||'#999';c.beginPath();c.arc(p[0],p[1],r,0,6.2832);c.fill();
    c.shadowColor='transparent';c.lineWidth=n.lw||1;c.strokeStyle=n.stroke||'rgba(0,0,0,.45)';if(n.dash)c.setLineDash(n.dash);c.stroke();c.setLineDash([]);
    if(n.ring){c.lineWidth=3.2;c.strokeStyle=C.rep;c.beginPath();c.arc(p[0],p[1],r+3.2,0,6.2832);c.stroke();c.lineWidth=1;c.strokeStyle=C.ink;c.beginPath();c.arc(p[0],p[1],r+5,0,6.2832);c.stroke();c.beginPath();c.arc(p[0],p[1],r+1.6,0,6.2832);c.stroke();}
    if(n.label!=null){c.fillStyle=n.lc||'#fff';c.font='700 '+Math.max(10,Math.round(r*0.8))+'px '+FONT;c.textAlign='center';c.textBaseline='middle';c.fillText(n.label,p[0],p[1]+1);}
    if(n.hl){c.lineWidth=3;c.strokeStyle=C.ink;c.beginPath();c.arc(p[0],p[1],r+8,0,6.2832);c.stroke();}
    c.restore();}
  line(a,b,o){o=o||{};const c=this.ctx,p=this.w2p(a[0],a[1]),q=this.w2p(b[0],b[1]);c.save();c.strokeStyle=o.color||C.ink;c.lineWidth=o.w||1.5;if(o.dash)c.setLineDash(o.dash);if(o.alpha!=null)c.globalAlpha=o.alpha;c.beginPath();c.moveTo(p[0],p[1]);c.lineTo(q[0],q[1]);c.stroke();c.restore();}
  arrow(a,b,o){o=o||{};this.line(a,b,o);const c=this.ctx,p=this.w2p(a[0],a[1]),q=this.w2p(b[0],b[1]);const ang=Math.atan2(q[1]-p[1],q[0]-p[0]),h=o.head||9;c.save();c.fillStyle=o.color||C.ink;if(o.alpha!=null)c.globalAlpha=o.alpha;c.beginPath();c.moveTo(q[0],q[1]);c.lineTo(q[0]-h*Math.cos(ang-.4),q[1]-h*Math.sin(ang-.4));c.lineTo(q[0]-h*Math.cos(ang+.4),q[1]-h*Math.sin(ang+.4));c.closePath();c.fill();c.restore();}
  disc(x,y,r,o){o=o||{};const c=this.ctx,p=this.w2p(x,y);c.save();if(o.glow){const g=c.createRadialGradient(p[0],p[1],r*this.scale*.6,p[0],p[1],r*this.scale*1.6);g.addColorStop(0,'rgba(255,255,255,'+(o.glow*0.55)+')');g.addColorStop(1,'rgba(255,255,255,0)');c.fillStyle=g;c.beginPath();c.arc(p[0],p[1],r*this.scale*1.6,0,6.2832);c.fill();}
    c.fillStyle='rgba(255,255,255,'+(o.alpha==null?.35:o.alpha)+')';c.beginPath();c.arc(p[0],p[1],r*this.scale,0,6.2832);c.fill();c.strokeStyle=C.ink;c.lineWidth=1.6;c.setLineDash([6,4]);c.stroke();c.restore();}
  poly(pts,o){o=o||{};const c=this.ctx;c.save();c.strokeStyle=o.color||C.ink;c.lineWidth=o.w||2;if(o.dash)c.setLineDash(o.dash);c.beginPath();pts.forEach((q,i)=>{const p=this.w2p(q[0],q[1]);i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]);});if(o.close)c.closePath();if(o.fill){c.fillStyle=o.fill;c.fill();}c.stroke();c.restore();}
  /* field image: fn(x,y)->[r,g,b,a(0..1)] on an nx x ny grid */
  field(fn,res){res=res||110;const k=this.__fc||(this.__fc=document.createElement('canvas'));k.width=res;k.height=res;const cx=k.getContext('2d'),im=cx.createImageData(res,res);
    for(let j=0;j<res;j++)for(let i=0;i<res;i++){const w=this.p2w((i+.5)/res*this.w,(j+.5)/res*this.h);const v=fn(w[0],w[1]);const o=(j*res+i)*4;im.data[o]=v[0];im.data[o+1]=v[1];im.data[o+2]=v[2];im.data[o+3]=Math.round(255*v[3]);}
    cx.putImageData(im,0,0);const c=this.ctx;c.save();c.imageSmoothingEnabled=true;c.drawImage(k,0,0,this.w,this.h);c.restore();}
}
/* ---------- legend chips ---------- */
function chipHTML(it){
  const sty=it.color&&!it.cls?'background:'+it.color:(it.color?'background:'+it.color:'');
  return '<span class="chip"><i class="'+(it.cls||'')+'" style="'+sty+'"></i>'+it.label+'</span>';}
const LEG = {
  types:[{color:C.head,label:'head cell'},{color:C.trunk,label:'middle cell'},{color:C.limb,label:'side cell'},{color:C.tail,label:'tail cell'}],
  state:[{color:C.sa,label:'blue state'},{color:C.sb,label:'pink state'}],
  rho:[{color:C.sa,label:'hidden memory: blue'},{color:C.mid,label:'undecided'},{color:C.sb,label:'hidden memory: pink'}],
  reporter:[{cls:'ring',label:'yellow marker'}],
  light:[{color:'rgba(255,255,255,.35)',cls:'dash',label:'light (white disc, dashed edge)'}],
  band:[{cls:'band',label:'normal range (grey band)'}]
};
/* ---------- charts on canvas ---------- */
class Chart{
  constructor(canvas,o){this.cv=canvas;this.o=o;const d=Math.min(window.devicePixelRatio||1,2);this.d=d;canvas.width=Math.round(o.w*d);canvas.height=Math.round(o.h*d);canvas.style.width=o.w+'px';canvas.style.height=o.h+'px';this.c=canvas.getContext('2d');this.c.setTransform(d,0,0,d,0,0);
    this.m=o.m||{l:46,r:12,t:22,b:30};this.xl=o.xlim;this.yl=o.ylim;this.w=o.w;this.h=o.h;}
  X(x){return this.m.l+(x-this.xl[0])/(this.xl[1]-this.xl[0])*(this.w-this.m.l-this.m.r);}
  Y(y){return this.h-this.m.b-(y-this.yl[0])/(this.yl[1]-this.yl[0])*(this.h-this.m.t-this.m.b);}
  clear(){const c=this.c;c.fillStyle='#fff';c.fillRect(0,0,this.w,this.h);}
  axes(){const c=this.c,o=this.o;c.save();c.strokeStyle='#999';c.lineWidth=1;c.fillStyle=C.ink;c.font='12px '+FONT;
    c.beginPath();c.moveTo(this.m.l,this.m.t);c.lineTo(this.m.l,this.h-this.m.b);c.lineTo(this.w-this.m.r,this.h-this.m.b);c.stroke();
    const xt=o.xticks||this.ticks(this.xl),yt=o.yticks||this.ticks(this.yl);c.textAlign='center';c.textBaseline='top';xt.forEach(v=>{const x=this.X(v);c.beginPath();c.moveTo(x,this.h-this.m.b);c.lineTo(x,this.h-this.m.b+4);c.stroke();c.fillText(o.xfmt?o.xfmt(v):String(v),x,this.h-this.m.b+5);});
    c.textAlign='right';c.textBaseline='middle';yt.forEach(v=>{const y=this.Y(v);c.beginPath();c.moveTo(this.m.l-4,y);c.lineTo(this.m.l,y);c.stroke();c.fillText(o.yfmt?o.yfmt(v):String(v),this.m.l-6,y);});
    if(o.title){c.textAlign='left';c.textBaseline='top';c.font='700 13px '+FONT;c.fillText(o.title,this.m.l,3);}
    if(o.xlabel){c.textAlign='right';c.textBaseline='bottom';c.font='12px '+FONT;c.fillStyle=C.mute;c.fillText(o.xlabel,this.w-this.m.r-26,this.h-this.m.b-4);}
    c.restore();}
  ticks(l){const s=l[1]-l[0],st=Math.pow(10,Math.floor(Math.log10(s/4)));const m=[1,2,5,10].map(k=>k*st).find(v=>s/v<=6)||st*10;const r=[];for(let v=Math.ceil(l[0]/m)*m;v<=l[1]+1e-9;v+=m)r.push(+v.toFixed(6));return r;}
  band(xs,lo,hi,col){const c=this.c;c.save();c.fillStyle=col||C.band;c.beginPath();xs.forEach((x,i)=>{const p=[this.X(x),this.Y(hi[i])];i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]);});for(let i=xs.length-1;i>=0;i--)c.lineTo(this.X(xs[i]),this.Y(lo[i]));c.closePath();c.fill();c.restore();}
  hband(lo,hi,col){const c=this.c;c.save();c.fillStyle=col||C.band;c.fillRect(this.m.l,this.Y(hi),this.w-this.m.l-this.m.r,this.Y(lo)-this.Y(hi));c.restore();}
  line(xs,ys,o){o=o||{};const c=this.c;c.save();c.strokeStyle=o.color||C.ink;c.lineWidth=o.w||2;if(o.dash)c.setLineDash(o.dash);c.beginPath();let st=false;
    xs.forEach((x,i)=>{const y=ys[i];if(y==null||isNaN(y)){st=false;return;}const px=this.X(x),py=this.Y(y);if(!st){c.moveTo(px,py);st=true;}else c.lineTo(px,py);});c.stroke();c.restore();}
  segColor(xs,ys,colfn,w){const c=this.c;c.save();c.lineWidth=w||3;for(let i=1;i<xs.length;i++){if(ys[i]==null||ys[i-1]==null)continue;c.strokeStyle=colfn(i);c.beginPath();c.moveTo(this.X(xs[i-1]),this.Y(ys[i-1]));c.lineTo(this.X(xs[i]),this.Y(ys[i]));c.stroke();}c.restore();}
  vline(x,o){o=o||{};const c=this.c;c.save();c.strokeStyle=o.color||'#C0392B';c.lineWidth=o.w||1.5;if(o.dash)c.setLineDash(o.dash);c.beginPath();c.moveTo(this.X(x),this.m.t);c.lineTo(this.X(x),this.h-this.m.b);c.stroke();if(o.label){c.fillStyle=o.color||'#C0392B';c.font='12px '+FONT;c.textAlign='left';c.textBaseline='top';c.fillText(o.label,this.X(x)+4,this.m.t+2);}c.restore();}
  hline(y,o){o=o||{};const c=this.c;c.save();c.strokeStyle=o.color||'#999';c.lineWidth=o.w||1;if(o.dash)c.setLineDash(o.dash);c.beginPath();c.moveTo(this.m.l,this.Y(y));c.lineTo(this.w-this.m.r,this.Y(y));c.stroke();if(o.label){c.fillStyle=o.color||'#666';c.font='12px '+FONT;c.textAlign='right';c.textBaseline='bottom';c.fillText(o.label,this.w-this.m.r-2,this.Y(y)-1);}c.restore();}
  dot(x,y,o){o=o||{};const c=this.c;c.save();c.fillStyle=o.color||C.ink;c.strokeStyle=o.stroke||'#fff';c.lineWidth=1.2;c.beginPath();c.arc(this.X(x),this.Y(y),o.r||4,0,6.2832);c.fill();c.stroke();c.restore();}
  text(t,x,y,o){o=o||{};const c=this.c;c.save();c.font=(o.bold?'700 ':'')+(o.size||12)+'px '+FONT;c.fillStyle=o.color||C.ink;c.textAlign=o.align||'left';c.textBaseline=o.base||'middle';c.fillText(t,x,y);c.restore();}
}
function makeCanvas(parent,w,h,cls){const cv=document.createElement('canvas');cv.width=w;cv.height=h;cv.style.width=w+'px';cv.style.height=h+'px';cv.dataset.avoid='1';if(cls)cv.className=cls;parent.appendChild(cv);cv.style.background='#fff';cv.style.border='1px solid #D9D9D2';cv.style.borderRadius='6px';return cv;}
function el(tag,attrs,parent,html){const e=document.createElement(tag);if(attrs)Object.keys(attrs).forEach(k=>e.setAttribute(k,attrs[k]));if(html!=null)e.innerHTML=html;if(parent)parent.appendChild(e);return e;}
function badge(text,kind){return '<span class="badge '+kind+'">'+(kind==='ok'?'✔ ':kind==='bad'?'✘ ':'')+text+'</span>';}

/* ---------- extra drawing helpers (revision) ---------- */
/* outline of a label mask (N x N, rows top = +y, window [-half,half]^2) drawn on a Panel: edges between differing labels */
function maskOutline(p,mask,N,half,col,w){const c=p.ctx,h=2*half/N;c.save();c.strokeStyle=col||C.ink;c.lineWidth=w||2.4;c.lineCap='round';c.beginPath();
  const X=j=>-half+j*h,Y=i=>half-i*h;
  for(let i=0;i<N;i++)for(let j=0;j<N;j++){const v=mask[i*N+j];if(!v)continue;
    if(j+1>=N||mask[i*N+j+1]!==v){const a=p.w2p(X(j+1),Y(i)),b=p.w2p(X(j+1),Y(i+1));c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);}
    if(j===0||mask[i*N+j-1]!==v){const a=p.w2p(X(j),Y(i)),b=p.w2p(X(j),Y(i+1));c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);}
    if(i===0||mask[(i-1)*N+j]!==v){const a=p.w2p(X(j),Y(i)),b=p.w2p(X(j+1),Y(i));c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);}
    if(i+1>=N||mask[(i+1)*N+j]!==v){const a=p.w2p(X(j),Y(i+1)),b=p.w2p(X(j+1),Y(i+1));c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);}}
  c.stroke();c.restore();}
/* outline of a point set: alpha-hull edges (the member set of a grouping) */
function pointOutline(p,pts,col,w,alpha){const E=alphaEdges(pts,alpha||1.5);E.forEach(e=>p.line(pts[e[0]],pts[e[1]],{color:col||C.ink,w:w||3}));}
/* tweezers icon at world point (tip at the cell) */
function tweezers(p,x,y,s){const c=p.ctx,q=p.w2p(x,y);s=s||1;c.save();c.translate(q[0],q[1]);c.scale(s,s);c.strokeStyle=C.ink;c.fillStyle=C.ink;c.lineWidth=3.2;c.lineCap='round';c.beginPath();c.moveTo(-26,-46);c.lineTo(-6,-4);c.moveTo(26,-46);c.lineTo(6,-4);c.stroke();
  c.lineWidth=1.4;c.strokeStyle='#fff';c.beginPath();c.moveTo(-26,-46);c.lineTo(-6,-4);c.moveTo(26,-46);c.lineTo(6,-4);c.stroke();
  c.fillStyle=C.ink;c.beginPath();c.arc(-6,-4,3.6,0,6.3);c.arc(6,-4,3.6,0,6.3);c.fill();c.restore();}
/* flash around a world point (newcomer) */
function flashAt(p,x,y,u,r){const c=p.ctx,q=p.w2p(x,y),R=(r||0.4)*p.scale;c.save();for(let k=0;k<8;k++){const a=k*Math.PI/4+0.4,r0=R+4+u*4,r1=R+10+u*16;c.strokeStyle=C.ink;c.lineWidth=3;c.beginPath();c.moveTo(q[0]+r0*Math.cos(a),q[1]+r0*Math.sin(a));c.lineTo(q[0]+r1*Math.cos(a),q[1]+r1*Math.sin(a));c.stroke();
    c.strokeStyle='#fff';c.lineWidth=1.2;c.stroke();}
  c.strokeStyle='#fff';c.lineWidth=5;c.beginPath();c.arc(q[0],q[1],R+3,0,6.3);c.stroke();c.strokeStyle=C.ink;c.lineWidth=1.5;c.stroke();c.restore();}
/* flip an RGB/grey base64 image into a canvas (rows already top=+y) */
function imgCanvas(b64,w,h,ch){const u=B64.u8(b64);const cv=document.createElement('canvas');cv.width=w;cv.height=h;const g=cv.getContext('2d'),im=g.createImageData(w,h);
  for(let i=0;i<w*h;i++){if(ch===3){im.data[4*i]=u[3*i];im.data[4*i+1]=u[3*i+1];im.data[4*i+2]=u[3*i+2];}else{const v=u[i];im.data[4*i]=v;im.data[4*i+1]=v;im.data[4*i+2]=v;}im.data[4*i+3]=255;}
  g.putImageData(im,0,0);return cv;}
/* Kabsch (2D rigid, no reflection): map points A -> B, returns function */
function kabsch2(A,B){const n=A.length;let ax=0,ay=0,bx=0,by=0;A.forEach(p=>{ax+=p[0]/n;ay+=p[1]/n;});B.forEach(p=>{bx+=p[0]/n;by+=p[1]/n;});let sxx=0,sxy=0;
  for(let i=0;i<n;i++){const a=[A[i][0]-ax,A[i][1]-ay],b=[B[i][0]-bx,B[i][1]-by];sxx+=a[0]*b[0]+a[1]*b[1];sxy+=a[0]*b[1]-a[1]*b[0];}
  const th=Math.atan2(sxy,sxx),c=Math.cos(th),s=Math.sin(th);return p=>{const x=p[0]-ax,y=p[1]-ay;return [c*x-s*y+bx,s*x+c*y+by];};}

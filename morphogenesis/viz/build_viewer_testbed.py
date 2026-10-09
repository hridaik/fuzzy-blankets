"""Testbed viewer (T1/T2): self-contained HTML, inline JS, no network. Reads the continuous-time engine's rollouts.

build_html(rollouts, out_path, title, audit=False, banner=...)
  rollouts: list of dicts (one arena panel each, all driven by one slider = synced compare mode)
    label    : str
    t        : (T,)            times
    X        : (T,n,2)         positions
    types    : (T,n) int 1..4  cell type from secretion (OBSERVABLE: derived from what an outside observer sees)
    ligand   : optional dict(ch=<index into C>, kappa=<float>, C=(T,n) secretion of that signal)  -> heatmap computed client-side
    events   : optional list of dict(t0,t1,cells=[...],label=str)  -> drawn as a highlighted disc (the intervention) in both tiers
    series   : optional dict name->(T,)  OBSERVABLE time series (e.g. rms speed)
    AUDIT-only fields (physically absent from OBSERVABLE builds; `audit=True` required to embed):
    target   : (T,n,2)         template positions aligned to the body (overlay)
    planB    : (T,n)           plan-B belief per cell (ring colour)
    role     : (T,n) int       argmax place belief
    audit_series : dict name->(T,)   free energy, mean plan-B belief, ...
"""
import json, os
import numpy as np

MAX_FRAMES = 240
PALETTE = {1: "#d62728", 2: "#1f77b4", 3: "#2ca02c", 4: "#e6a800"}

def _r(a, nd=3):
    return np.round(np.asarray(a, float), nd).tolist()

def _sub(T):
    stride = max(1, int(np.ceil(T / MAX_FRAMES)))
    return np.arange(0, T, stride), stride

def to_json(r, audit):
    T = len(r["t"]); idx, stride = _sub(T)
    d = dict(label=r["label"] + (f" [downsampled x{stride}]" if stride > 1 else ""), t=_r(np.asarray(r["t"])[idx], 2),
             X=_r(np.asarray(r["X"])[idx], 3), types=np.asarray(r["types"])[idx].astype(int).tolist())
    if r.get("ligand") is not None:
        L = r["ligand"]; d["ligand"] = dict(kappa=float(L["kappa"]), C=_r(np.asarray(L["C"])[idx], 3))
    if r.get("events"):
        d["events"] = r["events"]
    if r.get("img") is not None:          # O3 image panel: (T,H,W) uint8 (already normalised), arena window fov
        im = np.asarray(r["img"])[idx]; d["img"] = dict(h=int(im.shape[1]), w=int(im.shape[2]), fov=float(r.get("fov", 12.0)), data=im.reshape(len(idx), -1).astype(int).tolist())
    if r.get("series"):
        d["series"] = {k: _r(np.asarray(v)[idx], 4) for k, v in r["series"].items()}
    if audit:
        if r.get("target") is not None: d["target"] = _r(np.asarray(r["target"])[idx], 3)
        if r.get("planB") is not None: d["planB"] = _r(np.asarray(r["planB"])[idx], 3)
        if r.get("role") is not None: d["role"] = np.asarray(r["role"])[idx].astype(int).tolist()
        if r.get("audit_series"): d["audit_series"] = {k: _r(np.asarray(v)[idx], 4) for k, v in r["audit_series"].items()}
    return d

TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><title>__TITLE__</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#fafafa;color:#222}
header{padding:8px 14px;background:#fff;border-bottom:1px solid #ddd}
.banner{padding:6px 14px;font-weight:600}
.audit{background:#fde2e2;color:#8a1c1c}.obs{background:#e2f0e2;color:#1c5a1c}
#panels{display:flex;flex-wrap:wrap;gap:10px;padding:10px}
.panel{background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px}
.panel h4{margin:2px 4px;font-size:13px}
canvas{display:block}
#ctrl{padding:6px 14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
#ctrl input[type=range]{width:360px}
label{font-size:13px}
.note{font-size:12px;color:#555;padding:0 14px 8px}
</style></head><body>
<header><b>__TITLE__</b> &nbsp; <span style="color:#666">__SUB__</span></header>
<div class="banner __BCLASS__">__BANNER__</div>
<div id="ctrl"><button id="play">play</button><button id="step">step</button>
<input id="sl" type="range" min="0" max="0" value="0"><span id="tl"></span>
<label>speed <input id="sp" type="range" min="1" max="12" value="4"></label>
<label><input type="checkbox" id="lig" checked> memory-ligand heatmap</label>
<label><input type="checkbox" id="trail"> trails</label>
<label id="auditlbl" style="display:none"><input type="checkbox" id="tgt" checked> target overlay</label>
<label id="auditlbl2" style="display:none"><input type="checkbox" id="pb" checked> plan-B ring</label></div>
<div id="panels"></div><div class="note">Colours: head=red, trunk=blue, limb=green, tail=gold (cell type from secretion). Dashed disc = intervention region (when active). Heatmap: concentration of the memory signal (client-computed from per-cell secretion).</div>
<script type="application/json" id="data">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const AUDIT=D.audit, R=D.rollouts, PAL={1:"#d62728",2:"#1f77b4",3:"#2ca02c",4:"#e6a800"};
let cur=0, playing=false, T=Math.min(...R.map(r=>r.t.length));
const sl=document.getElementById('sl'); sl.max=T-1;
if(AUDIT){document.getElementById('auditlbl').style.display='';document.getElementById('auditlbl2').style.display='';}
// common bounds over all rollouts (so panels are comparable)
let xs=[],ys=[];R.forEach(r=>r.X.forEach((f,k)=>f.forEach((p,i)=>{if(r.types[k][i]>0){xs.push(p[0]);ys.push(p[1]);}})));
const pad=2.5; let x0=Math.min(...xs)-pad,x1=Math.max(...xs)+pad,y0=Math.min(...ys)-pad,y1=Math.max(...ys)+pad;
const W=420, Hh=Math.max(260, Math.min(520, W*(y1-y0)/(x1-x0))), sc=Math.min(W/(x1-x0),Hh/(y1-y0));
const tx=x=>(x-x0)*sc, ty=y=>Hh-(y-y0)*sc;
const panels=document.getElementById('panels');
R.forEach((r,k)=>{const d=document.createElement('div');d.className='panel';d.innerHTML='<h4>'+r.label+'</h4><canvas id="a'+k+'" width="'+W+'" height="'+Hh+'"></canvas><canvas id="s'+k+'" width="'+W+'" height="90"></canvas>';panels.appendChild(d);});
function heat(ctx,r,f){ if(!r.ligand||!document.getElementById('lig').checked) return;
 const g=24, cw=W/g, ch=Hh/g, X=r.X[f], C=r.ligand.C[f], ka=r.ligand.kappa; let mx=1e-9, v=[];
 for(let i=0;i<g;i++)for(let j=0;j<g;j++){const px=x0+(j+.5)*cw/sc, py=y1-(i+.5)*ch/sc; let s=0; for(let c=0;c<X.length;c++){const dx=px-X[c][0],dy=py-X[c][1]; s+=C[c]*Math.exp(-ka*Math.sqrt(dx*dx+dy*dy));} v.push(s); if(s>mx)mx=s;}
 let q=0; for(let i=0;i<g;i++)for(let j=0;j<g;j++){ctx.fillStyle='rgba(120,60,200,'+(0.45*Math.min(1,v[q++]/Math.max(mx,1.0)))+')';ctx.fillRect(j*cw,i*ch,cw+1,ch+1);} }
function draw(){
 R.forEach((r,k)=>{const c=document.getElementById('a'+k),ctx=c.getContext('2d');ctx.clearRect(0,0,W,Hh);ctx.fillStyle='#fff';ctx.fillRect(0,0,W,Hh);
  if(r.img){const im=r.img,fr=r.img.data[cur],id=ctx.createImageData(im.w,im.h);for(let q=0;q<fr.length;q++){id.data[4*q]=fr[q];id.data[4*q+1]=fr[q];id.data[4*q+2]=fr[q];id.data[4*q+3]=255;}const cv=document.createElement('canvas');cv.width=im.w;cv.height=im.h;cv.getContext('2d').putImageData(id,0,0);ctx.imageSmoothingEnabled=false;ctx.drawImage(cv,0,0,W,Hh);}
  else heat(ctx,r,cur);
  if(document.getElementById('trail').checked){ctx.strokeStyle='rgba(0,0,0,0.18)';for(let i=0;i<r.X[0].length;i++){ctx.beginPath();for(let f=Math.max(0,cur-40);f<=cur;f++){const p=r.X[f][i];f==Math.max(0,cur-40)?ctx.moveTo(tx(p[0]),ty(p[1])):ctx.lineTo(tx(p[0]),ty(p[1]));}ctx.stroke();}}
  if(AUDIT&&r.target&&document.getElementById('tgt').checked){ctx.strokeStyle='#888';r.target[cur].forEach(p=>{ctx.beginPath();ctx.arc(tx(p[0]),ty(p[1]),3,0,6.3);ctx.stroke();});}
  if(r.events){r.events.forEach(e=>{if(r.t[cur]>=e.t0&&r.t[cur]<e.t1){ctx.setLineDash([5,4]);ctx.strokeStyle='#000';const cs=e.cells;ctx.beginPath();let cx=0,cy=0;cs.forEach(i=>{cx+=r.X[cur][i][0];cy+=r.X[cur][i][1];});cx/=cs.length;cy/=cs.length;let rr=0;cs.forEach(i=>{rr=Math.max(rr,Math.hypot(r.X[cur][i][0]-cx,r.X[cur][i][1]-cy));});ctx.arc(tx(cx),ty(cy),(rr+0.7)*sc,0,6.3);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#000';ctx.font='11px sans-serif';ctx.fillText(e.label,tx(cx)-20,ty(cy)-(rr+0.9)*sc);}});}
  if(!r.img) r.X[cur].forEach((p,i)=>{if(r.types[cur][i]==0) return; ctx.beginPath();ctx.arc(tx(p[0]),ty(p[1]),7,0,6.3);ctx.fillStyle=PAL[r.types[cur][i]]||'#999';ctx.fill();
   if(AUDIT&&r.planB&&document.getElementById('pb').checked){const b=r.planB[cur][i];ctx.lineWidth=3;ctx.strokeStyle='rgb('+Math.round(255*b)+','+Math.round(120)+','+Math.round(255*(1-b))+')';ctx.stroke();ctx.lineWidth=1;}
   else{ctx.strokeStyle='#333';ctx.stroke();}});
  const sc2=document.getElementById('s'+k),c2=sc2.getContext('2d');c2.clearRect(0,0,W,90);c2.fillStyle='#fff';c2.fillRect(0,0,W,90);
  const ser=Object.assign({},r.series||{}); if(AUDIT&&r.audit_series)Object.assign(ser,r.audit_series);
  const cols=['#444','#b22','#26a','#2a2'];let ci=0;c2.font='10px sans-serif';
  Object.keys(ser).forEach(name=>{const v=ser[name];const mn=Math.min(...v),mx=Math.max(...v)+1e-12;c2.strokeStyle=cols[ci%4];c2.beginPath();v.forEach((y,f)=>{const X=f/(v.length-1)*(W-4)+2,Y=80-(y-mn)/(mx-mn)*66;f?c2.lineTo(X,Y):c2.moveTo(X,Y);});c2.stroke();c2.fillStyle=cols[ci%4];c2.fillText(name+' ['+mn.toPrecision(3)+','+mx.toPrecision(3)+']',4,10+11*ci);ci++;});
  c2.strokeStyle='#000';const xx=cur/(T-1)*(W-4)+2;c2.beginPath();c2.moveTo(xx,0);c2.lineTo(xx,90);c2.stroke();});
 document.getElementById('tl').textContent=' t = '+R[0].t[cur]+'  (frame '+cur+'/'+(T-1)+')'; sl.value=cur;}
document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'pause':'play';};
document.getElementById('step').onclick=()=>{cur=(cur+1)%T;draw();};
sl.oninput=()=>{cur=+sl.value;draw();};
['lig','trail','tgt','pb'].forEach(id=>{const e=document.getElementById(id);if(e)e.onchange=draw;});
(function loop(){let last=0;function f(ts){const sp=+document.getElementById('sp').value;if(playing&&ts-last>(260/sp)){cur=(cur+1)%T;draw();last=ts;}requestAnimationFrame(f);}requestAnimationFrame(f);})();
draw();
</script></body></html>"""

def build_html(rollouts, out_path, title, audit=False, banner=None, sub=""):
    data = dict(audit=bool(audit), rollouts=[to_json(r, audit) for r in rollouts])
    banner = banner or ("AUDIT BUILD — contains hidden-tier overlays (template, plan belief). Not for blind analysis." if audit else "OBSERVABLE BUILD — only what an outside observer sees (positions, cell colours, secreted signal).")
    html = (TEMPLATE.replace("__TITLE__", title).replace("__SUB__", sub).replace("__BANNER__", banner)
            .replace("__BCLASS__", "audit" if audit else "obs").replace("__DATA__", json.dumps(data)))
    assert "__DATA__" not in html and "__TITLE__" not in html
    if len(html) > 16e6: raise RuntimeError("viewer too large")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w").write(html)
    return out_path

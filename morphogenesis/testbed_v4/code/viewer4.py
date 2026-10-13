"""Viewer exemplars v4: self-contained HTML (canvas). AUDIT build = hidden truth (rho, ubar, tail axes, intact flag, lit set); OBSERVABLE build = package data only (tracked cells coloured by an O1 column + O3c cell-marker image)."""
import sys, os, json, base64
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from lib4 import *
OUT = os.path.join(HERE, '..', 'viewer'); os.makedirs(OUT, exist_ok=True)
def _r(a, n=3): return np.round(np.asarray(a, float), n).tolist()
def axes_of(X, MU):
    q = np.exp(MU - MU.max(1, keepdims=True)); q /= q.sum(1, keepdims=True); pl = q.argmax(1); sel = np.isin(pl, TM.body)
    if sel.sum() < 4 or len(set(pl.tolist())) < 20: return None
    T = TM.Xs[:, pl[sel]].T; Y = X[sel]; mt, my = T.mean(0), Y.mean(0); U, S, Vt = np.linalg.svd((T - mt).T @ (Y - my)); d = np.sign(np.linalg.det(Vt.T @ U.T)); R = Vt.T @ np.diag([1, d]) @ U.T
    head = R @ (TM.Xs[:, TM.head] - mt) + my; hinge = R @ (TM.hinge - mt) + my; tc = X[np.isin(pl, TM.tail)].mean(0); return head, hinge, tc
def audit_roll(label, dish, variant, state, T, every, light=None, noise=False, seed=0, gamma=None, burn=0.0, post=None, note=''):
    """light = dict(centre, dur, amp). returns a panel dict with hidden truth per frame"""
    e = get_engine(dish, variant, noise=noise, gamma_on=False, gamma=gamma if gamma is not None else gamma0()); arr, perm = settled(dish, variant, state); st = tuple(jnp.array(a) for a in arr); key = jax.random.PRNGKey(50_000 + seed); step0 = 0
    if noise and burn > 0: st = run_plain(e, st, 0.0, burn, key); step0 = int(round(burn / DT))
    t0 = burn if noise else 0.0; base = nbr_matrix(np.array(st[0])); lit = np.zeros(24, bool); ctl = zero_ctl(e); ton = toff = -1e9; ramp = 1.0
    if light:
        lit = lit_cells(perm, light['centre']); col = 1 if state == 'a' else 0; uM = np.zeros((24, 2)); uM[lit, col] = light['amp']; c = list(ctl); c[3] = jnp.array(uM); ctl = tuple(c); ton, toff, ramp = t0, t0 + light['dur'], min(5.0, light['dur'] / 4)
    per = int(round(every / DT)); nst = int(round(T / DT / per)) * per
    fin, tr = e.run_ctl(st, t0, DT, nst, key, ctl, ton, toff, ramp, step0=step0, save_every=per)
    frames = [tuple(np.array(a) for a in st)] + [tuple(np.array(a[k]) for a in tr) for k in range(len(tr[0]))]; tt = [0.0] + [every * (k + 1) for k in range(len(tr[0]))]
    P = dict(label=label, note=note, t=tt, X=[], rho=[], ubar=[], angle=[], jac=[], intact=[], ncomp=[], head=[], hinge=[], tailc=[], lit=lit.astype(int).tolist(), lit_on=[t0 - t0, light['dur'] if light else 0.0], perm=perm.tolist(), types=TM.types[0][perm].tolist(), place=[])
    for f in frames:
        X, C, MU, L, D, E, U = f; fs = frame_stats(X, MU, L, base); ax = axes_of(X, MU); P['X'].append(_r(X)); P['rho'].append(_r(1 / (1 + np.exp(-L)), 3)); P['ubar'].append(_r(U, 2)); P['angle'].append(None if fs['angle'] != fs['angle'] else round(float(fs['angle']), 2))
        P['jac'].append(round(fs['jac'], 4)); P['ncomp'].append(fs['ncomp']); P['intact'].append(bool(fs['ncomp'] == 1 and fs['fill_ok'] and fs['jac'] >= tauJ()))
        P['head'].append(_r(ax[0]) if ax else None); P['hinge'].append(_r(ax[1]) if ax else None); P['tailc'].append(_r(ax[2]) if ax else None); P['place'].append(np.array(jax.nn.softmax(jnp.array(MU), 1)).argmax(1).tolist())
    return P
HTML = """<!doctype html><html><head><meta charset=utf-8><title>__TITLE__</title><style>
body{font-family:system-ui,sans-serif;margin:0;background:#fafafa;color:#222}header{padding:8px 14px;background:#fff;border-bottom:1px solid #ccc}
.ban{padding:5px 14px;font-weight:600}.aud{background:#f6e3c6;color:#7a4a00}.obs{background:#e2f0e2;color:#1c5a1c}#ctl{padding:6px 14px;background:#fff;border-bottom:1px solid #eee}
.row{display:flex;flex-wrap:wrap;gap:10px;padding:8px 14px}.pan{background:#fff;border:1px solid #ccc;padding:4px}.pan b{font-size:12px}canvas{display:block}.note{padding:4px 14px 14px;font-size:12px;color:#555;max-width:1200px}
</style></head><body><header><b>__TITLE__</b> &nbsp; <span style=color:#555>__SUB__</span></header><div class="ban __BC__">__BANNER__</div>
<div id=ctl><button id=play>play</button> <input id=sl type=range min=0 max=0 value=0 style="width:480px"> <span id=tl></span> &nbsp; <span id=cmode></span></div>
<div class=row id=pans></div><div class=note id=info></div>
<script id=data type=application/json>__DATA__</script><script>
const D=JSON.parse(document.getElementById('data').textContent);const AUD=D.build==='audit';let cur=0,playing=false;const P=D.panels;
const NF=Math.max(...P.map(p=>p.t.length));const sl=document.getElementById('sl');sl.max=NF-1;
const holder=document.getElementById('pans');P.forEach((p,i)=>{const d=document.createElement('div');d.className='pan';d.innerHTML='<b>'+p.label+'</b><canvas id=c'+i+' width=360 height=300></canvas><canvas id=s'+i+' width=360 height=110></canvas>';holder.appendChild(d);});
let col=0;if(!AUD){const s=document.createElement('select');for(let j=0;j<7;j++)s.add(new Option('colour by column '+j,j));s.onchange=()=>{col=+s.value;draw();};document.getElementById('cmode').appendChild(s);}
const allx=[].concat(...P.map(p=>[].concat(...p.X.map(f=>f.map(c=>c[0])))));const ally=[].concat(...P.map(p=>[].concat(...p.X.map(f=>f.map(c=>c[1])))));
function colormap(v){const r=Math.round(255*v),b=Math.round(255*(1-v));return 'rgb('+r+',60,'+b+')';}
function frame(p,k){return Math.min(k,p.t.length-1);}
function draw(){const k0=cur;document.getElementById('tl').textContent='frame '+k0;
 P.forEach((p,i)=>{const k=frame(p,k0);const c=document.getElementById('c'+i).getContext('2d');c.clearRect(0,0,360,300);const X=p.X[k];
  const mx=X.reduce((a,b)=>a+b[0],0)/X.length,my=X.reduce((a,b)=>a+b[1],0)/X.length;const sc=24,ox=180-mx*sc,oy=150+my*sc;const px=x=>ox+x*sc,py=y=>oy-y*sc;
  c.strokeStyle='#bbb';c.lineWidth=1;for(let a=0;a<X.length;a++)for(let b=a+1;b<X.length;b++){const dx=X[a][0]-X[b][0],dy=X[a][1]-X[b][1];if(dx*dx+dy*dy<1.6*1.6){c.beginPath();c.moveTo(px(X[a][0]),py(X[a][1]));c.lineTo(px(X[b][0]),py(X[b][1]));c.stroke();}}
  if(AUD&&p.head[k]&&p.hinge[k]&&p.tailc[k]){c.lineWidth=2;c.strokeStyle='#2a7';c.beginPath();c.moveTo(px(p.head[k][0]),py(p.head[k][1]));c.lineTo(px(p.hinge[k][0]),py(p.hinge[k][1]));c.stroke();c.strokeStyle='#c4a';c.beginPath();c.moveTo(px(p.hinge[k][0]),py(p.hinge[k][1]));c.lineTo(px(p.tailc[k][0]),py(p.tailc[k][1]));c.stroke();}
  X.forEach((x,j)=>{c.beginPath();c.arc(px(x[0]),py(x[1]),8,0,6.283);if(AUD){c.fillStyle=colormap(p.rho[k][j]);c.fill();const u=Math.min(1,p.ubar[k][j]/Math.max(1e-9,D.ubar_scale));if(u>0.02){c.lineWidth=3;c.strokeStyle='rgba(255,140,0,'+(0.25+0.75*u)+')';c.stroke();}
    const tp=D.build==='audit'&&p.lit[j]&&p.t[k]>=p.lit_on[0]&&p.t[k]<=p.lit_on[1]+8;if(tp){c.lineWidth=1.5;c.strokeStyle='#000';c.setLineDash([2,2]);c.beginPath();c.arc(px(x[0]),py(x[1]),11,0,6.283);c.stroke();c.setLineDash([]);}}
   else{const v=p.lv?p.lv[k][j][col]:0.5;const lo=Math.min(...p.lv[k].map(r=>r[col])),hi=Math.max(...p.lv[k].map(r=>r[col]));c.fillStyle=colormap((v-lo)/Math.max(1e-9,hi-lo));c.fill();}});
  c.fillStyle='#000';c.font='11px system-ui';if(AUD){const a=p.angle[k];c.fillText('t='+p.t[k].toFixed(1)+'  tail angle '+(a===null?'n/a':a.toFixed(1)+'°')+'  intact '+(p.intact[k]?'yes':'NO')+'  min nbr J '+p.jac[k].toFixed(3),6,14);c.fillText('fill rho; orange ring ubar; dashed lit; green body axis, purple tail',6,292);}else c.fillText('t='+p.t[k].toFixed(1),6,14);
  const s=document.getElementById('s'+i).getContext('2d');s.clearRect(0,0,360,110);s.strokeStyle='#ccc';s.strokeRect(30,6,320,90);const T=p.t.length;
  function line(arr,lo,hi,colr){s.beginPath();s.strokeStyle=colr;arr.forEach((v,q)=>{if(v===null)return;const x=30+320*q/(T-1),y=96-90*(v-lo)/(hi-lo);if(q==0)s.moveTo(x,y);else s.lineTo(x,y);});s.stroke();}
  if(AUD){const mr=p.rho.map(r=>r.reduce((a,b)=>a+b,0)/r.length);line(mr,0,1,'#37a');line(p.angle.map(a=>a===null?null:(a+30)/60),0,1,'#c4a');line(p.intact.map(v=>v?1:0),-0.05,1.05,'#2a7');s.fillStyle='#37a';s.fillText('mean rho',34,18);s.fillStyle='#c4a';s.fillText('tail angle (-30..30)',100,18);s.fillStyle='#2a7';s.fillText('intact',210,18);}
  else{const m=p.lv.map(r=>r.reduce((a,b)=>a+b[col],0)/r.length);const lo=Math.min(...m),hi=Math.max(...m);line(m,lo,hi+1e-9,'#37a');s.fillStyle='#37a';s.fillText('mean of selected column',34,18);}
  const x=30+320*k/(T-1);s.strokeStyle='#000';s.beginPath();s.moveTo(x,6);s.lineTo(x,96);s.stroke();});}
sl.oninput=()=>{cur=+sl.value;draw();};document.getElementById('play').onclick=()=>{playing=!playing;if(playing)tick();};function tick(){if(!playing)return;cur=(cur+1)%NF;sl.value=cur;draw();setTimeout(tick,60);}
document.getElementById('info').textContent=D.info;draw();</script></body></html>"""
def emit(name, title, sub, panels, build='audit', info='', ubar_scale=3.0):
    banner = 'AUDIT BUILD - hidden truth shown (rho, light damage, tail axes, intact flag). Not for blind sessions.' if build == 'audit' else 'OBSERVABLE BUILD - package data only (tracked cells, no analysis, no hidden quantities).'
    d = dict(build=build, panels=panels, info=info, ubar_scale=ubar_scale); html = HTML.replace('__TITLE__', title).replace('__SUB__', sub).replace('__BANNER__', banner).replace('__BC__', 'aud' if build == 'audit' else 'obs').replace('__DATA__', json.dumps(d))
    p = os.path.join(OUT, f'{name}_{build}.html'); open(p, 'w').write(html); print(p, round(len(html) / 1e6, 2), 'MB'); return p

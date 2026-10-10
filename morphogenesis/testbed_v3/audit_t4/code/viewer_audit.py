"""A10 audit viewer (SEALED, AUDIT build). Truth panel (left) vs analyst overlays (right), synced; timeline strips of analyst labels at four levels vs the true state.
Exemplar rule (declared before looking): lowest run id in each category."""
import sys, json, pickle, collections; sys.path.insert(0, '.')
from lib import *
A5 = {x['run']: x for x in json.load(open(os.path.join(AUD, 'data', 'a5_changes.json')))}
def pick():
    runs = sorted(CATD); out = collections.OrderedDict()
    sw = [r for r in runs if META[r]['family'] == 'switch' and META[r]['kind'] == 'on' and META[r]['level'] == 1.4 and META[r]['state'] == 'a' and A5.get(r, {}).get('switched')]; out['state_switch'] = sw[0]
    tw = [r for r in runs if CATD[r]['arm'] == 'untreated_control' and META[r]['family'] == 'stress' and t4out(r)['levels']['O1']['frames'][-1]['organisms'][0]['C3']['label'] == -1]; out['twin_drift'] = tw[0]
    rare = [r for r in runs if META[r]['family'] == 'natural' and collections.Counter(x['organisms'][0]['C3']['label'] for x in t4out(r)['levels']['O1']['frames'] if x['organisms']).most_common(1)[0][0] == 1]; out['rare_type_dish'] = rare[0]
    out['surgery_split'] = [r for r in runs if META[r]['family'] == 'stress' and META[r]['scn'] == 'cutx' and CATD[r]['arm'] == 'treated'][0]
    out['decoy_light'] = [r for r in runs if META[r]['family'] == 'decoy' and META[r]['kind'] == 'sec' and META[r]['state'] == 'a'][0]
    out['natural_dish'] = [r for r in runs if META[r]['family'] == 'natural' and META[r]['state'] == 'a' and r != out['rare_type_dish']][0]    # amended: must differ from the rare-type exemplar (same dish was lowest id in both categories)
    return out
def page_data(run):
    frs, hidden = raw(run); tr = pickle.load(open(os.path.join(AUD, 'data', 'truth', run + '.pkl'), 'rb')); G = tr['groups']['all']; t = [round(x, 3) for x in tr['t']]
    ids = [fr['cell_id'][fr['alive']].tolist() for fr in frs]; X = [np.round(fr['X'][fr['alive']], 3).tolist() for fr in frs]; rh = [np.round(rho(fr['L'][fr['alive']]), 3).tolist() for fr in frs]; ty = [np.argmax(np.stack([np.abs(fr['C'][fr['alive']][:, 1:4] - c).sum(1) for c in np.array([[1, 1, 0], [1, 0, 1], [1, 0, 0]])], 1), 1).tolist() for fr in frs]
    pc = pickle.load(open(os.path.join(AUD, 'data', 'truth', run + '.pkl'), 'rb'))['per_cell']
    out = dict(run=run, cat=CATD[run]['condition'] + '/' + CATD[run]['arm'], t=t, ids=ids, X=X, rho=rh, ty=ty, truth=[dict(mean_rho=g['mean_rho'], dL=g.get('dL'), complete=bool(g.get('orbit_ok', False)), e1=g.get('e1'), e2=g.get('e2'), c=g['centroid'], ncomp=g['ncomp']) for g in G], ops=[round(e['t'] - 1e4 - 100.0, 1) for e in hidden['events'] if e['kind'] in ('cut', 'extrude', 'replace', 'fuse')], onset=onset_abs(run))
    o = t4out(run); lev = {}
    for lv in ('O1', 'O2', 'O3a', 'O3b'):
        fr = o['levels'][lv]['frames']; lev[lv] = [dict(t=round(f['t'], 3), orgs=[dict(c=x['centroid'], e1=x['e1'], e2=x['e2'], n=x['n'], members=x['members'][:60] if lv == 'O1' else [], label=x['C3']['label'], post=round(x['C3']['posterior'], 3), ood=x['C3']['ood'], V=x['V_running'], Vc=x['V_conservative_running'], unres=x['unresolved'], sgn=x['sign_conf']) for x in f['organisms']], ev=[e['type'] for e in f['events']]) for f in fr]
    out['an'] = lev; return out
HTML = """<!doctype html><html><head><meta charset=utf-8><title>AUDIT __TITLE__</title><style>body{font-family:system-ui;margin:0;background:#fafafa}header{padding:8px 14px;background:#fff;border-bottom:1px solid #ccc}.ban{background:#fde2e2;color:#8a1c1c;font-weight:600;padding:5px 14px}#ctl{padding:6px 14px}canvas{background:#fff;border:1px solid #ccc;margin:6px}.row{display:flex;flex-wrap:wrap}.note{font-size:12px;color:#444;padding:4px 14px}</style></head><body>
<header><b>__TITLE__</b> &nbsp; <span style=color:#555>__SUB__</span></header><div class=ban>AUDIT BUILD - SEALED - contains hidden truth next to the analyst overlays. Not for any blind session.</div>
<div id=ctl><button id=play>play</button> <input id=sl type=range min=0 max=0 value=0 style="width:520px"> <span id=tl></span> speed <input id=sp type=range min=1 max=12 value=5></div>
<div class=row><canvas id=ct width=470 height=380></canvas><canvas id=ca width=470 height=380></canvas></div><div class=row><canvas id=cs width=960 height=150></canvas></div>
<div class=note>Left: TRUTH (true positions; fill = true memory state, red = first state (mean rho &gt; 1/2), blue = second; border = structural type: red head, blue trunk, green limb, gold tail; green arrow = true e1 head-&gt;tail, orange arrow = true e2 (structural limb side)). Right: ANALYST O1 (same cells; fill = analyst state label; arrows = analyst e1 (green) / e2 (orange); text = label, posterior, V, events). Bottom: label strips of the analyst at O1/O2/O3a/O3b over the true mean-rho strip; vertical bars = hidden operation times.</div>
<script id=data type=application/json>__DATA__</script><script>
const D=JSON.parse(document.getElementById('data').textContent);const N=D.t.length;const sl=document.getElementById('sl');sl.max=N-1;let cur=0,playing=false;
let xs=[],ys=[];D.X.forEach(f=>f.forEach(p=>{xs.push(p[0]);ys.push(p[1])}));const pad=2,x0=Math.min(...xs)-pad,x1=Math.max(...xs)+pad,y0=Math.min(...ys)-pad,y1=Math.max(...ys)+pad;const W=470,H=380,sc=Math.min(W/(x1-x0),H/(y1-y0));const tx=x=>(x-x0)*sc,ty=y=>H-(y-y0)*sc;
const TY={0:'#1f77b4',1:'#2ca02c',2:'#d62728'};const LP=['#e07b00','#1f77b4','#2ca02c','#9467bd','#8c564b'];const LC=l=>l==-1?'#888':(l==-2?'#ccc':LP[l%5]);
function arrow(c,x,y,dx,dy,col,len){c.strokeStyle=col;c.lineWidth=2;c.beginPath();c.moveTo(tx(x),ty(y));c.lineTo(tx(x)+dx*len,ty(y)-dy*len);c.stroke();}
function anFrame(lv,t){const L=D.an[lv];let b=0,bd=1e9;L.forEach((f,i)=>{const d=Math.abs(f.t-t);if(d<bd){bd=d;b=i}});return L[b];}
function draw(){const t=D.t[cur];const a=document.getElementById('ct').getContext('2d'),b=document.getElementById('ca').getContext('2d');[a,b].forEach(c=>c.clearRect(0,0,W,H));
 const X=D.X[cur],R=D.rho[cur],T=D.ty[cur],ids=D.ids[cur];X.forEach((p,i)=>{a.beginPath();a.arc(tx(p[0]),ty(p[1]),7,0,6.3);a.fillStyle=R[i]>0.5?'#e45':'#37c';a.fill();a.lineWidth=3;a.strokeStyle=TY[T[i]];a.stroke();});
 const tr=D.truth[cur];if(tr.e1){arrow(a,tr.c[0],tr.c[1],tr.e1[0],tr.e1[1],'#0a0',50);arrow(a,tr.c[0],tr.c[1],tr.e2[0],tr.e2[1],'#e80',50);}
 a.fillStyle='#000';a.font='12px sans-serif';a.fillText('t='+t+'  true mean rho='+tr.mean_rho.toFixed(2)+'  typed dist='+(tr.dL==null?'-':tr.dL.toFixed(2))+'  comps='+tr.ncomp,6,14);D.ops.forEach(o=>{if(Math.abs(o-t)<1e-6+ (D.t[1]-D.t[0])/2) a.fillText('OPERATION',6,30)});
 const f=anFrame('O1',t);const lab={};f.orgs.forEach(o=>o.members.forEach(m=>lab[m]=o));X.forEach((p,i)=>{const o=lab[ids[i]];b.beginPath();b.arc(tx(p[0]),ty(p[1]),7,0,6.3);b.fillStyle=o?LC(o.label):'#fff';b.fill();b.lineWidth=1;b.strokeStyle='#333';b.stroke();});
 f.orgs.forEach((o,k)=>{arrow(b,o.c[0],o.c[1],o.e1[0],o.e1[1],'#0a0',50);arrow(b,o.c[0],o.c[1],o.e2[0],o.e2[1],'#e80',50);b.fillStyle='#000';b.font='12px sans-serif';b.fillText('org '+k+' label '+o.label+' post '+o.post+' V='+(o.V?1:0)+' Vc='+(o.Vc?1:0)+(o.unres?' UNRESOLVED':''),6,14+16*k);});b.fillText('O1 events: '+(f.ev.join(',')||'none'),6,H-8);
 const s=document.getElementById('cs').getContext('2d');s.clearRect(0,0,960,150);const t0=D.t[0],t1=D.t[N-1],X1=tt=>40+(tt-t0)/(t1-t0+1e-9)*900;s.font='11px sans-serif';
 s.fillStyle='#000';s.fillText('true state',2,16);D.truth.forEach((g,i)=>{s.fillStyle=g.mean_rho>0.5?'#e45':'#37c';s.fillRect(X1(D.t[i]),6,Math.max(2,900/N),14)});
 ['O1','O2','O3a','O3b'].forEach((lv,r)=>{s.fillStyle='#000';s.fillText(lv,2,38+r*22);D.an[lv].forEach(f=>{const o=f.orgs[0];s.fillStyle=o?LC(o.label):'#fff';s.fillRect(X1(f.t),28+r*22,Math.max(2,900/D.an[lv].length),14)})});
 s.strokeStyle='#000';D.ops.concat(D.onset!=null?[D.onset]:[]).forEach(o=>{s.beginPath();s.moveTo(X1(o),0);s.lineTo(X1(o),135);s.stroke()});s.strokeStyle='#f0f';s.beginPath();s.moveTo(X1(t),0);s.lineTo(X1(t),135);s.stroke();
 document.getElementById('tl').textContent=' t = '+t+' ('+cur+'/'+(N-1)+')';sl.value=cur;}
sl.oninput=()=>{cur=+sl.value;draw()};document.getElementById('play').onclick=()=>{playing=!playing};(function loop(){let last=0;function f(ts){if(playing&&ts-last>260/+document.getElementById('sp').value){cur=(cur+1)%N;draw();last=ts}requestAnimationFrame(f)}requestAnimationFrame(f)})();draw();</script></body></html>"""
def main():
    P = pick(); json.dump(P, open(os.path.join(AUD, 'data', 'exemplars.json'), 'w'), indent=1); print(P)
    for name, run in P.items():
        d = page_data(run); h = HTML.replace('__TITLE__', f'{name} ({run}, {d["cat"]})').replace('__SUB__', 'truth vs analyst; exemplar rule: lowest run id in the category').replace('__DATA__', json.dumps(d))
        open(os.path.join(AUD, 'viewer', f'{name}.html'), 'w').write(h)
if __name__ == "__main__": main()

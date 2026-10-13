"""Safe-window plot (AUDIT build): switch threshold and damage-onset amplitude versus duration, median dish (lines) and the 40-dish population (bands). Self-contained SVG."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, '..', 'data'); OUT = os.path.join(HERE, '..', 'viewer')
G = 4 * 0.05 * np.sqrt(6.0); DMS = [4, 8, 16, 32]
w = json.load(open(f'{D}/v4_window.json')); gap = json.load(open(f'{D}/v5_gap_L0.json')) if os.path.exists(f'{D}/v5_gap_L0.json') else None
W = {}
if gap:
    for k, v in gap['W'].items():
        dish, c, dm = k.split('|'); W.setdefault((c, int(dm)), []).append(v)
curves = []
for c, col in (('middle', '#2a7'), ('tail_end', '#c4a')):
    thr = [next(r['thr'] for r in w if r['centre'] == c and r['dm'] == dm) for dm in DMS]; ud = [next(r['u_d'] for r in w if r['centre'] == c and r['dm'] == dm) for dm in DMS]
    band = None
    if gap and (c, 4) in W: band = dict(thr=[[min(v[0] for v in W[(c, dm)]), max(v[0] for v in W[(c, dm)])] for dm in DMS], ud=[[min(v[1] for v in W[(c, dm)]), max(v[1] for v in W[(c, dm)])] for dm in DMS])
    curves.append(dict(c=c, col=col, thr=thr, ud=ud, band=band))
html = """<!doctype html><html><head><meta charset=utf-8><title>Safe window</title><style>body{font-family:system-ui,sans-serif;margin:0;background:#fafafa}header{padding:8px 14px;background:#fff;border-bottom:1px solid #ccc}.ban{background:#f6e3c6;color:#7a4a00;font-weight:600;padding:5px 14px}.note{padding:8px 14px;font-size:12px;color:#444;max-width:900px}</style></head><body>
<header><b>v4 - the safe window: switch threshold vs damage onset</b> <span style=color:#555>median dish (lines), 40 dishes (bands)</span></header><div class=ban>AUDIT BUILD - hidden truth (damage onset is not observable in the package)</div>
<svg id=s width=820 height=520></svg><div class=note id=n></div><script>
const C=__C__,DMS=[4,8,16,32],G=__G__;const s=document.getElementById('s');const X0=70,X1=780,Y0=470,Y1=30;
const lx=d=>X0+(X1-X0)*(Math.log(d)-Math.log(4/G*0.8))/(Math.log(32/G*1.25)-Math.log(4/G*0.8));const lo=0.3,hi=400;const ly=a=>Y0-(Y0-Y1)*(Math.log(a)-Math.log(lo))/(Math.log(hi)-Math.log(lo));
let h='';[0.3,1,3,10,30,100,300].forEach(a=>{h+=`<line x1=${X0} x2=${X1} y1=${ly(a)} y2=${ly(a)} stroke=#ddd /><text x=${X0-8} y=${ly(a)+4} text-anchor=end font-size=11>${a}</text>`;});
DMS.forEach(d=>{h+=`<line x1=${lx(d/G)} x2=${lx(d/G)} y1=${Y0} y2=${Y1} stroke=#eee /><text x=${lx(d/G)} y=${Y0+16} text-anchor=middle font-size=11>${d}/g = ${(d/G).toFixed(1)} tu</text>`;});
h+=`<text x=${(X0+X1)/2} y=${Y0+38} text-anchor=middle font-size=12>pulse duration</text><text transform="rotate(-90) translate(-${(Y0+Y1)/2},16)" text-anchor=middle font-size=12>amplitude (log)</text>`;
function band(arr,col,op){const up=arr.map((v,i)=>`${lx(DMS[i]/G)},${ly(v[1])}`),dn=arr.map((v,i)=>`${lx(DMS[i]/G)},${ly(v[0])}`).reverse();return `<polygon points="${up.concat(dn).join(' ')}" fill=${col} fill-opacity=${op} stroke=none />`;}
function line(arr,col,dash,w){return `<polyline points="${arr.map((v,i)=>lx(DMS[i]/G)+','+ly(v)).join(' ')}" fill=none stroke=${col} stroke-width=${w} stroke-dasharray="${dash}" />`+arr.map((v,i)=>`<circle cx=${lx(DMS[i]/G)} cy=${ly(v)} r=3.5 fill=${col} />`).join('');}
C.forEach(c=>{if(c.band){h+=band(c.band.thr,c.col,0.12);h+=band(c.band.ud,c.col,0.12);}h+=line(c.thr,c.col,'',2.5);h+=line(c.ud,c.col,'6 4',2.5);});
let y=40;C.forEach(c=>{h+=`<text x=${X0+20} y=${y} font-size=12 fill=${c.col}>${c.c}: solid = switch threshold, dashed = damage onset</text>`;y+=16;});s.innerHTML=h;
document.getElementById('n').innerHTML='Between the solid and the dashed line of one disc is the safe window (amplitudes that switch without tearing the body). Middle disc: window open at every duration (ratio 2.4-3.0 at the median dish). Tail-end disc: the dashed line lies BELOW the solid line - no safe window at the median dish at any duration. Shaded bands: range over 40 dishes (kappa_g and the per-dish damage factor move both lines).';</script></body></html>"""
html = html.replace('__C__', json.dumps(curves)).replace('__G__', repr(float(G))); open(f'{OUT}/safe_window_audit.html', 'w').write(html); print('written', len(html))

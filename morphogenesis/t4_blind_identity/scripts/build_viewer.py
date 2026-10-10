"""Build the self-contained HTML viewer (inline JS/CSS/data, no network). usage: build_viewer.py OUTDIR CACHE_TAGS(comma) VIEWDIR SPLITSEL
Exemplar rule (declared before looking at results): per category (opaque condition label), rank runs of the NON-twin arm
('treated', or 'untreated' for N0) by the pipeline-internal score S = mean over frames and founder organisms (level O1) of the fraction of
the 5 envelope axes that pass; pick the median-rank, the best (max S), the worst (min S) and two random picks (seed 20260101)."""
import sys, os, json, base64, pickle, collections, html; sys.path.insert(0, '.')
import numpy as np
from scipy.spatial import Delaunay
from t4 import io, summ
OUT, TAGS, VIEW, SEL = sys.argv[1:5]
TAGS = TAGS.split(',')
SEED = 20260101
os.makedirs(VIEW, exist_ok=True)
cat = {r['run']: r for r in io.catalog()}

def cache(run, lv):
    for t in TAGS:
        p = f'cache/{t}/{run}_{lv}.pkl'
        if os.path.exists(p): return pickle.load(open(p, 'rb'))

def alpha_edges(P, alpha=1.7):
    P = np.asarray(P, float)
    if len(P) < 3: return []
    try: tri = Delaunay(P)
    except Exception: return []
    cnt = collections.Counter()
    for s in tri.simplices:
        a, b, c = P[s]
        la, lb, lc = np.linalg.norm(b - c), np.linalg.norm(a - c), np.linalg.norm(a - b)
        area = abs((b - a)[0] * (c - a)[1] - (b - a)[1] * (c - a)[0]) / 2
        if area < 1e-9: continue
        if la * lb * lc / (4 * area) < alpha:
            for e in ((s[0], s[1]), (s[1], s[2]), (s[0], s[2])): cnt[tuple(sorted(e))] += 1
    return [[round(P[i][0], 2), round(P[i][1], 2), round(P[j][0], 2), round(P[j][1], 2)] for (i, j), n in cnt.items() if n == 1]

def score(out):
    L = out['levels']['O1']; vals = []
    for oid in summ.founders(L):
        for f in L['frames']:
            for o in f['organisms']:
                if str(o['id']) == oid: vals.append(np.mean(list(o['axis_pass'].values())))
    return float(np.mean(vals)) if vals else 0.0

def panel(run, title, with_img=True):
    r = cat[run]; out = summ.load_out(f'{OUT}/{run}.json.gz'); env = json.load(open('calibration/envelope.json'))
    raw = io.point_frames(run, 'O1'); raw2 = io.point_frames(run, 'O2')
    C = {lv: cache(run, lv) for lv in ('O1', 'O2', 'O3b')}
    ts = [f['t'] for f in raw]
    lv_data = {}
    for lv in ('O1', 'O2', 'O3b'):
        L = out['levels'][lv]; b = env[lv]['bounds']; fr = []
        for f in L['frames']:
            orgs = []
            cf = C[lv]['frames'][f['k']]
            for o in f['organisms']:
                co = next(x for x in cf['orgs'] if x['org'] == o['id'])
                if lv in ('O1', 'O2'):
                    idm = dict(zip(cf['cells']['ids'], cf['cells']['xy'])); P = [idm[c] for c in co['members'] if c in idm]
                else:
                    P = co['_pseudo']['xy']
                info = L['organisms'][str(o['id'])]
                orgs.append(dict(id=o['id'], n=o['n'], c=o['centroid'], e1=o['e1'], sc=o['sign_conf'], hull=alpha_edges(P),
                                 V=o['V_running'], Vc=o['V_conservative_running'], post=o['C3']['posterior'], st=o['C3']['label'], unres=o['unresolved'],
                                 j=o['C1']['J_init'], shr=o['C2']['shape_dev'] / b['shape'], par=o['C2']['pattern_dev'] / b['pattern']))
            fr.append(dict(t=f['t'], orgs=orgs, ev=[dict(type=e['type'], cell=e.get('cell', -1)) for e in f['events']]))
        lv_data[lv] = fr
    frames = []
    t3 = [f['t'] for f in out['levels']['O3b']['frames']]
    for k, f in enumerate(raw):
        cells = [[round(x, 2), round(y, 2)] + [round(v, 2) for v in l] for (x, y), l in zip(f['xy'], f['lev'])]
        i3 = int(np.searchsorted(t3, f['t'] + 1e-6, side='right') - 1); i3 = max(i3, 0)
        frames.append(dict(t=f['t'], cells=cells, ii=i3, lv={'O1': lv_data['O1'][k], 'O2': lv_data['O2'][k], 'O3b': lv_data['O3b'][i3]}))
    D = dict(title=title, frames=frames, cellch=io.CHANNELS['O1'], levels=['O1', 'O2', 'O3b'], fov=r['fov'], onset=r['onset'])
    if with_img:
        tt, im = io.image_frames(run, 'O3b'); mx = np.array([np.quantile(im[:, c], 0.999) for c in range(4)]) + 1e-6
        D['img'] = []
        for k in range(len(tt)):
            rgb = np.stack([np.clip(im[k, 2] / mx[2], 0, 1), np.clip(im[k, 1] / mx[1], 0, 1), np.clip(im[k, 0] / mx[0], 0, 1)], -1)
            rgb = (255 * rgb[::-1] ** 0.6).astype(np.uint8)      # flip so row 0 is y=-fov in the image array -> top is +y
            D['img'].append(base64.b64encode(rgb.tobytes()).decode())
    return D

LEG = ('<b>Mapping (declared):</b> cell fill RGB = (c3, c1, c2) levels (O2 has no c4/c5); white ring = c0 &gt; 0.5; ring colour at O1 = cyan if c4&gt;c5 else magenta. '
       'Image panel (O3b): R=c0, G=c2, B=c6 (gamma 0.6). White arrow = body-frame e1 (signed by observable asymmetry, opacity = sign confidence), dashed = e2. '
       'Coloured outline = alpha hull of the organism; #id = organism id. Timeline ticks: red SPLIT, violet MERGE, orange EXTRUSION, green ARRIVAL, pink LOSS, blue BIRTH. '
       'Traces: C1 = Jaccard to the initial member set; C2 = max(shape,pattern) deviation divided by envelope bound (orange line = 1/3 of axis range, bound at 1.0 maps to 1/3); C3 = filtered state posterior. '
       'State colours: S0 blue, S1 orange, S2 green, S3 violet; OOD = grey. V = strict envelope continuation so far; V_cons additionally requires no SPLIT/MERGE/UNRESOLVED.')

def write(name, panels, title, meta, aw=300, start=0):
    h = open('t4/viewer_template.html').read()
    pw = (aw * (2 if panels[0].get('img') else 1) + 24)
    data = dict(panels=panels, aw=aw, meta=meta, legend=LEG, start=start)
    h = h.replace('__TITLE__', html.escape(title)).replace('__PW__', str(pw)).replace('__DATA__', json.dumps(data, separators=(',', ':')))
    open(os.path.join(VIEW, name), 'w').write(h)

runs = [r for r in cat.values() if (r['split'] == 'development') == (SEL == 'development') and os.path.exists(f"{OUT}/{r['run']}.json.gz")]
cats = collections.defaultdict(list)
for r in runs:
    if r['arm'] in ('untreated', 'treated'): cats[r['condition']].append(r)
rng = np.random.default_rng(SEED); index = []
for c, rs in sorted(cats.items()):
    sc = {r['run']: score(summ.load_out(f"{OUT}/{r['run']}.json.gz")) for r in rs}
    order = sorted(rs, key=lambda r: (sc[r['run']], r['run']))
    pick = collections.OrderedDict()
    pick['worst'] = order[0]; pick['median'] = order[len(order) // 2]; pick['best'] = order[-1]
    rest = [r for r in rs if r not in pick.values()]
    for j, i in enumerate(rng.permutation(len(rest))[:2]): pick[f'random{j + 1}'] = rest[i]
    for role, r in pick.items():
        name = f"{c}_{role}_{r['run']}.html"
        D = panel(r['run'], f"{c} / {role} / {r['run']} ({r['arm']})", True)
        onset = f"onset {r['onset']}" if r['onset'] is not None else 'natural'
        write(name, [D], f"{c} {role} {r['run']}", f"{r['arm']} body {r['body_id']} {onset} score={sc[r['run']]:.3f}", 300, start=0)
        index.append((c, role, r['run'], name, sc[r['run']], r['arm']))
# triplet compare pages (P*): the treated exemplar group
comp = []
for c, role, run, name, s_, arm in index:
    r = cat[run]
    if c.startswith('P') and role in ('median', 'worst', 'best'):
        g = [x for x in cat.values() if x['group'] == r['group']]
        arms = {x['arm']: x['run'] for x in g}
        if len(arms) == 3 and all(os.path.exists(f"{OUT}/{v}.json.gz") for v in arms.values()):
            Ds = [panel(arms[a], f"{lab} {arms[a]}", False) for a, lab in (('treated', 'EVENT'), ('untreated_control', 'TWIN'), ('sham_treated', 'SHAM'))]
            nm = f"compare_{c}_{role}_{r['group']}.html"
            write(nm, Ds, f"compare {c} {role} {r['group']}", f"synced event / twin / sham, onset {r['onset']}", 260)
            comp.append((c, role, r['group'], nm))
# index
rows = ''.join(f'<tr><td>{c}</td><td>{role}</td><td><a href="{n}">{run}</a></td><td>{arm}</td><td>{s:.3f}</td></tr>' for c, role, run, n, s, arm in index)
crow = ''.join(f'<tr><td>{c}</td><td>{role}</td><td><a href="{n}">{g}</a></td></tr>' for c, role, g, n in comp)
open(os.path.join(VIEW, f'index_{SEL}.html' if False else 'index.html'), 'w').write(f"""<!doctype html><meta charset=utf-8><title>T4 viewer index</title>
<style>body{{background:#0f1115;color:#e6e6e6;font:14px system-ui;margin:16px}}a{{color:#4ea1ff}}td,th{{padding:2px 10px;text-align:left}}</style>
<h1>T4 blind identity - exemplar viewer ({SEL})</h1><p>Exemplar rule (declared in advance): per category (opaque condition label) the median-rank, best and worst run by the pipeline-internal envelope-pass score, plus two random picks (numpy default_rng seed {SEED}). Self-contained pages, no network.</p>
<h2>Single-run pages</h2><table><tr><th>category</th><th>role</th><th>run</th><th>arm</th><th>score</th></tr>{rows}</table>
<h2>Triplet compare pages (event / twin / sham, synced)</h2><table><tr><th>category</th><th>role</th><th>group</th></tr>{crow}</table>""")
print(len(index), 'single pages;', len(comp), 'compare pages')

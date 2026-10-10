"""Part F: which observables lead the detected state change. usage: analysis_anticipation.py OUTDIR development|heldout RESULT.json THRESH.json
development: derives noise scales and false-alarm thresholds from change-free dev runs and writes THRESH.json; heldout: reads it (frozen)."""
import sys, json, os, collections; sys.path.insert(0, '.')
import numpy as np
from t4 import io, summ
OUT, SEL, RES, THR = sys.argv[1:5]
LEVELS = ['O1', 'O2', 'O3a', 'O3b']
rng = np.random.default_rng(23)
cat = [r for r in io.catalog() if r['condition'] != 'N0' and (r['split'] == 'development') == (SEL == 'development')]
FA = 0.05; NSHIFT = 200; BASE = 3

def dtclass(r): return 'dt%g' % r['frame_interval']

def series(out, lv):
    """founder lineages -> dict(name -> (t array, desc matrix, names, change list))"""
    L = out['levels'][lv]; res = []
    for oid in summ.founders(L):
        fr = [(f['t'], o) for f in L['frames'] for o in f['organisms'] if str(o['id']) == oid]
        names = list(fr[0][1]['desc'].keys())
        X = np.array([[o['desc'][n] if o['desc'][n] is not None else np.nan for n in names] for _, o in fr])
        res.append((np.array([t for t, _ in fr]), X, names, L['organisms'][oid]['state_changes']))
    return res

def scores(t, X, sigma):
    base = np.nanmedian(X[:BASE], 0)
    return np.abs(X - base) / sigma

data = collections.defaultdict(list)   # (lv) -> list of (run row, series tuple)
for r in cat:
    p = f"{OUT}/{r['run']}.json.gz"
    if not os.path.exists(p): continue
    o = summ.load_out(p)
    for lv in LEVELS:
        for s in series(o, lv): data[lv].append((r, s))

if SEL == 'development':
    thr = {}
    for lv in LEVELS:
        thr[lv] = {}
        for cls in sorted({dtclass(r) for r, _ in data[lv]}):
            runs = [(r, s) for r, s in data[lv] if dtclass(r) == cls]
            # noise scale: robust sd of frame-to-frame differences before onset (label-free)
            diffs = []
            for r, (t, X, names, ch) in runs:
                pre = t < (r['onset'] if r['onset'] is not None else -1) if r['onset'] is not None else np.zeros(len(t), bool)
                if pre.sum() >= 3: diffs.append(np.diff(X[pre], axis=0))
            if not diffs: continue
            D_ = np.concatenate(diffs); sigma = np.maximum(1.4826 * np.nanmedian(np.abs(D_ - np.nanmedian(D_, 0)), 0), 1e-4)
            # false-alarm thresholds: change-free runs (no detected state change, no flagged events) -> (1-FA) quantile of the run maximum
            mx = []
            for r, (t, X, names, ch) in runs:
                if r['arm'] in ('untreated_control', 'sham_treated') and not ch:
                    mx.append(np.nanmax(scores(t, X, sigma), 0))
            theta = np.nanquantile(np.array(mx), 1 - FA, axis=0) if len(mx) >= 10 else np.full(len(sigma), 6.0)
            thr[lv][cls] = dict(names=runs[0][1][2], sigma=sigma.tolist(), theta=np.maximum(theta, 3.0).tolist(), n_ref_runs=len(mx))
    json.dump(thr, open(THR, 'w'))
thr = json.load(open(THR))

def boot_ci(vals, clusters, f=np.mean, B=1000):
    vals = np.asarray(vals, float); cl = np.asarray(clusters); u = np.unique(cl)
    if len(vals) == 0: return [np.nan] * 3
    idx = {c: np.where(cl == c)[0] for c in u}; bs = []
    for _ in range(B):
        ch = rng.choice(u, len(u)); bs.append(f(np.concatenate([vals[idx[c]] for c in ch])))
    return [float(f(vals)), float(np.quantile(bs, .025)), float(np.quantile(bs, .975))]

res = {}
for lv in LEVELS:
    per = collections.defaultdict(lambda: dict(lead=[], hit=[], null_hit=[], cl=[], crossed=[]))
    nchg = 0
    for r, (t, X, names, ch) in data[lv]:
        cls = dtclass(r)
        if cls not in thr[lv] or not ch: continue
        tc = ch[0]['t']; k0 = int(np.searchsorted(t, tc))
        if k0 <= BASE: continue                       # change detected inside the baseline: cannot assess anticipation
        nchg += 1
        sg = np.array(thr[lv][cls]['sigma']); th = np.array(thr[lv][cls]['theta'])
        S = scores(t, X, sg)
        cluster = r['group'] if r['condition'].startswith('P') else r['body_id']
        for j, n in enumerate(thr[lv][cls]['names']):
            cross = np.where(S[BASE:, j] > th[j])[0]
            tj = t[BASE + cross[0]] if len(cross) else np.nan
            per[n]['crossed'].append(float(len(cross) > 0 and tj <= tc))
            lead = tc - tj if len(cross) else np.nan
            per[n]['lead'].append(lead); per[n]['hit'].append(float(np.isfinite(lead) and lead > 0)); per[n]['cl'].append(cluster)
            # time-shift null: circularly shift the detected change time within the run (post-baseline)
            nh = []
            for _ in range(NSHIFT):
                kk = int(rng.integers(BASE + 1, len(t))); tcs = t[kk]
                c2 = np.where(S[BASE:, j] > th[j])[0]
                nh.append(float(len(c2) > 0 and tcs - t[BASE + c2[0]] > 0))
            per[n]['null_hit'].append(float(np.mean(nh)))
    tab = {}
    for n, d in per.items():
        hit = np.array(d['hit']); nh = np.array(d['null_hit']); leads = np.array(d['lead'])
        fin = np.isfinite(leads) & (leads > 0)
        tab[n] = dict(n_change_runs=len(hit), hit_rate=boot_ci(hit, d['cl']), null_hit_rate=float(nh.mean()), skill=boot_ci(hit - nh, d['cl']),
                      median_lead_time=(boot_ci(leads[fin], np.array(d['cl'])[fin], np.median) if fin.sum() >= 3 else None))
    res[lv] = dict(n_change_runs=nchg, features=tab)
    top = sorted(tab.items(), key=lambda kv: -kv[1]['skill'][0])[:5]
    print(lv, 'change runs', nchg, [(k, round(v['skill'][0], 2), v['median_lead_time'] and round(v['median_lead_time'][0], 1)) for k, v in top])
json.dump(res, open(RES, 'w'), indent=1)

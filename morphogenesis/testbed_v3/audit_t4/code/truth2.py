"""True geometric and pattern deviation series per run (noise-free hidden levels, true body frame), relative to the first frame."""
import sys, os, pickle, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
CH = ['c0', 'c1', 'c2', 'c3', 'dA', 'dB', 'e']; GROUPS = dict(structural=['c0', 'c1', 'c2', 'c3'], memory=['dA', 'dB'], reporter=['e'])
def tr_of(run): return pickle.load(open(os.path.join(AUD, 'data', 'truth', run + '.pkl'), 'rb'))
def shape(X): c = np.cov((X - X.mean(0)).T); w = np.sort(np.linalg.eigvalsh(c))[::-1]; return np.sqrt(np.maximum(w, 1e-12))
def pattern_vec(fr, idx, e1, e2):
    X = fr['X'][idx]; c = X - X.mean(0); u = c @ e1; v = c @ e2; lev = np.concatenate([fr['C'][idx], fr['D'][idx], fr['E'][idx][:, None]], 1); out = {}
    for j, ch in enumerate(CH):
        y = lev[:, j]; out[ch] = np.array([y.mean(), np.polyfit(u, y, 1)[0] if u.std() > 1e-6 else 0.0, np.polyfit(v, y, 1)[0] if v.std() > 1e-6 else 0.0, y[u > np.median(u)].mean() - y[u <= np.median(u)].mean()])
    return out
def series(run):
    """returns dict: t, n, mst, ncomp, shape_dev, pattern_dev{structural,memory,reporter} for the single-body whole dish (frames where >= 12 cells)"""
    frs, hidden = raw(run); tr = tr_of(run); G = tr['groups']['all']; out = dict(t=[], n=[], mst=[], ncomp=[], shape_dev=[], **{f'pat_{g}': [] for g in GROUPS}); ref = None; refs = None
    for fr, g in zip(frs, G):
        idx = np.where(fr['alive'])[0]; X = fr['X'][idx]; out['t'].append(fr['t']); out['n'].append(g['n']); out['mst'].append(g['mst_max']); out['ncomp'].append(g['ncomp'])
        if 'e1' not in g: [out[k].append(np.nan) for k in out if k.startswith('pat_') or k == 'shape_dev']; continue
        s = shape(X); pv = pattern_vec(fr, idx, np.array(g['e1']), np.array(g['e2']))
        if ref is None: ref = s; refs = pv
        out['shape_dev'].append(float(np.hypot(*np.log(s / ref)))); 
        for gname, chs in GROUPS.items(): out[f'pat_{gname}'].append(float(np.sqrt(sum(((pv[c] - refs[c]) ** 2).sum() for c in chs))))
    return {k: np.array(v) for k, v in out.items()}
def job(run):
    p = os.path.join(AUD, 'data', 'truth2', run + '.pkl'); os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p): pickle.dump(series(run), open(p, 'wb'))
    return run
if __name__ == "__main__":
    from par import run_jobs; import time; t0 = time.time(); run_jobs(job, [(r['run'],) for r in CAT], workers=8, label='truth2'); print('wall', time.time() - t0)

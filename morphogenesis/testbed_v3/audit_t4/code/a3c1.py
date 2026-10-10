"""A3 C1: analyst material Jaccard (J_init) vs the true material Jaccard of the largest true component."""
import sys, json, pickle, collections; sys.path.insert(0, '.')
from lib import *
from world3 import component_labels
def big_ids(pc):
    ids = np.array(pc['id']); X = np.array(pc['X']); lab = component_labels(X, CFG['r_link']); cnt = np.bincount(lab); k = int(cnt.argmax()); return set(ids[lab == k].tolist())
R = collections.defaultdict(list)
for r in CAT:
    run = r['run']; fam = META[run]['family']; grp = 'natural' if fam == 'natural' else ('ops_' + r['arm'] if fam == 'stress' else 'light/device')
    if fam == 'stress' and META[run]['scn'].startswith('fuse'): continue                                 # two founders; skip in this simple comparison
    tr = pickle.load(open(os.path.join(AUD, 'data', 'truth', run + '.pkl'), 'rb')); S = [big_ids(pc) for pc in tr['per_cell']]; S0 = S[0]; Jt = {round(t, 3): len(s & S0) / len(s | S0) for t, s in zip(tr['t'], S)}
    out = t4out(run)
    for lv in ('O1', 'O2', 'O3a', 'O3b'):
        for f in out['levels'][lv]['frames']:
            if not f['organisms']: continue
            o = max(f['organisms'], key=lambda o: o['n'] if o['n'] else o['n_pixels']); jt = Jt.get(round(f['t'], 3))
            if jt is None: continue
            R[(lv, grp)].append((o['C1']['J_init'], jt))
res = {}
for (lv, grp), v in sorted(R.items()):
    v = np.array(v); e = np.abs(v[:, 0] - v[:, 1]); res[f'{lv}|{grp}'] = dict(frames=len(v), mean_abs_err=float(e.mean()), p95_abs_err=float(np.quantile(e, .95)), corr=float(np.corrcoef(v[:, 0], v[:, 1])[0, 1]) if v[:, 1].std() > 1e-9 and v[:, 0].std() > 1e-9 else None, frac_true_below_0p8=float((v[:, 1] < 0.8).mean()), frac_analyst_below_0p8=float((v[:, 0] < 0.8).mean()))
    print(lv, grp, {k: (round(x, 3) if isinstance(x, float) else x) for k, x in res[f'{lv}|{grp}'].items()})
json.dump(res, open(os.path.join(AUD, 'data', 'a3_c1.json'), 'w'), indent=1)

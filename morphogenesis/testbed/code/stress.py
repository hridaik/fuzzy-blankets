"""T3.4 IDENTITY-STRESS dataset: Part I events at declared placements, each run as (event, matched no-event twin, sham), CRN-matched (same key, noise stream, hidden pose).
Scenarios (declared): replace1 (one cell replaced at t=50, uniformly random cell), replace6 (six cells replaced, one every 40, from t=50), extrude (one random cell pulled 8 units outward at t=50),
cut (random body-fixed arena line through the centroid, fragments separated by 7 units at t=50), fuse_LL / fuse_LR (two bodies 9 units apart, from t=0; twin = same bodies 40 units apart)."""
import sys, json, os, pickle; sys.path.insert(0, '.')
from par import run_jobs
T_TOTAL = 300.0; T_EVENT = 50.0
SCN = ['replace1', 'replace6', 'extrude', 'cut', 'fuse_LL', 'fuse_LR']

def make_actions(scn, ex, rng):
    import numpy as np
    w = ex.w; al = np.where(w.alive)[0]; X = w.X; c = X[al].mean(0)
    if scn == 'replace1': i = int(rng.choice(al)); return [dict(type='surgery', op='replace', pos=X[i].tolist(), t=T_EVENT)]
    if scn == 'replace6': idx = rng.choice(al, 6, replace=False); return [dict(type='surgery', op='replace', pos=X[i].tolist(), t=T_EVENT + 40.0 * k) for k, i in enumerate(idx)]
    if scn == 'extrude':
        i = int(rng.choice(al)); u = X[i] - c; u = u / (np.linalg.norm(u) + 1e-9); return [dict(type='tweezers', pos=X[i].tolist(), vec=(8.0 * u).tolist(), t=T_EVENT)]
    if scn == 'cut':
        ang = rng.uniform(0, np.pi); nrm = [float(np.cos(ang)), float(np.sin(ang))]; d = float(np.array(nrm) @ c)
        return [dict(type='surgery', op='cut', normal=nrm, d=d, vec=[7.0 * nrm[0], 7.0 * nrm[1]], t=T_EVENT)]
    return []

def build(scn, kind, seed, arm):
    from interface import Experiment, np
    from world import fuse
    if scn.startswith('fuse'):
        kb = 'L' if scn == 'fuse_LL' else 'R'
        a = Experiment('L', seed=seed, noise=0.02); b = Experiment(kb, seed=seed + 500, noise=0.02)
        a.w = fuse(a.w, b.w, [9.0, 0.0] if arm == 'event' else [40.0, 0.0]); return a, []
    ex = Experiment(kind, seed=seed, noise=0.02); rng = np.random.default_rng(seed * 7 + 3); return ex, make_actions(scn, ex, rng)

def job(scn, kind, seed):
    out = {}
    for arm in ('event', 'twin', 'sham'):
        ex, actions = build(scn, kind, seed, arm if arm == 'event' else 'twin')
        ex.t0 = ex.w.time; ex._observe()
        ex.run(T_TOTAL, [] if arm == 'twin' else actions, sham=(arm == 'sham'))
        out[arm] = dict(frames=ex.obs, hidden=ex.hidden(), pose=ex.hidden_pose)
    p = f'../data/stress_raw/{scn}_{kind}_{seed:03d}.pkl'; os.makedirs('../data/stress_raw', exist_ok=True); pickle.dump(out, open(p, 'wb')); return p

if __name__ == "__main__":
    args = [(s, k, seed) for s in SCN for k in (('L', 'R') if not s.startswith('fuse') else ('L',)) for seed in range(300, 306)]
    res = run_jobs(job, args, workers=8, label='stress'); json.dump(res, open('../data/stress_manifest_raw.json', 'w'))

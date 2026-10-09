"""S3 forward ladder: families x patterns x durations x amplitude ladder, deterministic, at the S1 operating point. Outcome classes L/R/DEFECT/OTHER."""
import sys, json; sys.path.insert(0, '.')
from par import run_jobs
DURS = (20.0, 80.0); RAMP = 5.0; REL = 150.0
FAMS = ['sec0', 'sec1', 'sec2', 'sec3', 'rg0', 'rg1', 'rg2', 'rg3', 'mig']
BASE = dict(sec=1.0, rg=0.3, mig=0.5)
LAD = (0.25, 0.5, 1, 2, 4, 8)

def job(fam, pat, dur, sign, lad, direction='LR'):
    from s3common import np, jax, jnp, setup, adult, masks, classify_state, T_ON
    t, eng = setup(); n, nc = t.n, t.nc
    fin, perm = adult(t, eng, 0, mirror=(direction == 'RL')); M = masks(t, perm)[pat]
    ext = np.zeros((n, nc)); rg = np.zeros((n, nc)); mig = np.zeros(n); fb = np.zeros((n, n))
    kind, ch = (fam[:3], int(fam[3])) if fam.startswith('sec') else ((fam[:2], int(fam[2])) if fam.startswith('rg') else ('mig', 0))
    A = sign * lad * BASE[{'sec': 'sec', 'rg': 'rg', 'mig': 'mig'}[kind]]
    if kind == 'sec': ext[:, ch] = A * M
    elif kind == 'rg': rg[:, ch] = A * M
    else: mig[:] = A * M
    amps = tuple(jnp.array(a) for a in (ext, rg, mig, fb))
    ns = int((dur + REL) / eng.dt)
    out = eng.run_ctl(fin, T_ON, eng.dt, ns, jax.random.PRNGKey(0), amps, T_ON, T_ON + dur, RAMP)
    cls, info = classify_state(t, eng, out)
    return dict(fam=fam, pat=pat, dur=dur, sign=sign, lad=lad, direction=direction, cls=cls, n_lit=int((M != 0).sum()), **{k: info.get(k) for k in ('dL', 'dR', 'reason', 'ncomp', 'extruded')})

if __name__ == "__main__":
    pats = ['disc_head', 'disc_trunkP', 'disc_trunkM', 'disc_tail', 'disc_mid', 'two_discs', 'half_plus', 'half_minus']
    args = [(f, p, d, s, l) for f in FAMS for p in pats for d in DURS for s in (1, -1) for l in LAD]
    res = run_jobs(job, args, workers=8, label='ladder'); json.dump(res, open('../data/s3_ladder.json', 'w'))
    from collections import Counter
    print(Counter(r['cls'] for r in res))

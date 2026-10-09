"""S4 fallback: optogenetic FATE-BIAS light channel. In illuminated cells a transient term b*w(t) is added to d mu/dt for all slots of one declared type
(T2 or T3), smooth raised-cosine ramps. Illumination: the 8 body-row cells (rect x in [-1.5,0.5] of the body frame); sides are defined by current type.
Patterns: 'T3side->T2' (cells currently type 3 biased toward type-2 slots), 'T2side->T3', 'both' (paired). Both directions L->R and R->L (the swap rule is the same)."""
import sys, json; sys.path.insert(0, '.')
from par import run_jobs
RAMP = 5.0; REL = 300.0
BS = (0.02, 0.05, 0.1, 0.2, 0.4, 0.8)

def make_fb(t, fin, pat, b, dirn):
    from s3common import np
    from asm import cell_types, type_vector
    X = np.array(fin[0]); ct = cell_types(np.array(fin[1]).T); n = t.n
    c = X - X.mean(0); w, v = np.linalg.eigh(c.T @ c); ax = v[:, 1]            # long axis in arena coordinates
    u = c @ ax; rect = (u > -1.5) & (u < 0.5) | (u > -0.5) & (u < 1.5)          # either sign convention of the axis: cover rows near the middle (8 cells)
    # exact: the 8 body-row cells are those with type in {2,3}
    rows = (ct == 2) | (ct == 3)
    ty = type_vector(t); fb = np.zeros((n, t.n)); lit = np.zeros(n)
    slots2 = np.where(ty == 2)[0]; slots3 = np.where(ty == 3)[0]
    side3 = rows & (ct == 3); side2 = rows & (ct == 2)
    if pat in ('T3side->T2', 'both'): fb[np.ix_(np.where(side3)[0], slots2)] = b; lit[side3] = 1
    if pat in ('T2side->T3', 'both'): fb[np.ix_(np.where(side2)[0], slots3)] = b; lit[side2] = 1
    return fb, lit

def job(pat, dur, b, dirn):
    from s3common import np, jax, jnp, setup, adult, classify_state, T_ON
    t, eng = setup(); n, nc = t.n, t.nc
    fin, perm = adult(t, eng, 0, mirror=(dirn == 'RL'))
    fb, lit = make_fb(t, fin, pat, b, dirn)
    amps = (jnp.zeros((n, nc)), jnp.zeros((n, nc)), jnp.zeros(n), jnp.array(fb))
    out = eng.run_ctl(fin, T_ON, eng.dt, int((dur + REL) / eng.dt), jax.random.PRNGKey(0), amps, T_ON, T_ON + dur, RAMP)
    cls, info = classify_state(t, eng, out)
    return dict(pat=pat, dur=dur, b=b, dir=dirn, cls=cls, n_lit=int(lit.sum()), dose=float(b * dur * lit.sum()), **{k: info.get(k) for k in ('dL', 'dR', 'reason', 'ncomp', 'extruded', 'min_orbit_maxbel')})

def bisect_job(pat, dur, lo, hi, dirn, iters=6):
    want = 'R' if dirn == 'LR' else 'L'; tr = []
    for _ in range(iters):
        mid = (lo * hi) ** 0.5; r = job(pat, dur, mid, dirn); tr.append((mid, r['cls']))
        if r['cls'] == want: hi = mid
        else: lo = mid
    return dict(pat=pat, dur=dur, dir=dirn, lo=lo, hi=hi, trace=tr)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == 'ladder':
        args = [(p, d, b, dr) for p in ('T3side->T2', 'T2side->T3', 'both') for d in (20.0, 80.0) for b in BS for dr in ('LR', 'RL')]
        res = run_jobs(job, args, workers=8, label='s4ladder'); json.dump(res, open('../data/s4_ladder.json', 'w'))
        from collections import Counter; print(Counter((r['pat'], r['dir'], r['cls']) for r in res))

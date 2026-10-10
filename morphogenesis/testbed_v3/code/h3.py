"""H3 switch: memory-secretion light, white-box lit set (cells whose place lies within R_DISC of the centre place, body frame), deterministic bisection + noise success.
Declared: durations 1/g, 4/g, 16/g; ramp = min(5, dur/4) (raised cosine); release 20/g; amplitudes ladder 0.25*2^k then 5 bisection steps."""
import sys, json, time; sys.path.insert(0, '.')
from an3 import *
from theory3 import G_
DT = 0.0125; R_DISC = 1.5; G = G_; DURS = [1 / G, 4 / G, 16 / G]; REL = 20 / G; SAVE = 0.25
_c = {}
def get(state, noise=None, sig_h=0.0, k=0):
    key = (state, noise, sig_h, k)
    if key not in _c:
        from world3 import settled3
        arr, perm = settled3(state, k); tm = make_template2()
        P = Params3(sig_x=noise, sig_c=noise, sig_mu=noise, sig_d=noise, sig_e=noise, sig_h=sig_h) if noise else Params3(); eng = make_engine3(tm, P); eng.dt = DT
        _c[key] = (eng, tuple(jnp.array(a) for a in arr), perm, tm)
    return _c[key]
def lit_set(tm, perm, centre, r=R_DISC):
    return np.ones(24, bool) if centre < 0 else (np.linalg.norm(tm.Xs[:, perm].T - tm.Xs[:, centre][None], axis=1) <= r + 1e-9)
def connectivity(tm, perm, lit):
    X = tm.Xs[:, perm].T; D = np.linalg.norm(X[:, None] - X[None], axis=-1); w = np.exp(-D); np.fill_diagonal(w, 0); return float(w[np.ix_(lit, ~lit)].sum())
def trial(state, centre, dur, amp, noise=None, sig_h=0.0, seed=0, burn=0.0, sham_twin=True, release=None, lit_override=None, extra_release=0.0):
    eng, st0, perm, tm = get(state, noise, sig_h); n = 24; col = 1 if state == 'a' else 0                     # a -> b pushes B (column 1); b -> a pushes A (column 0)
    lit = lit_set(tm, perm, centre) if lit_override is None else lit_override; uM = np.zeros((n, 2)); uM[lit, col] = amp
    ctl = zero_ctl(n)[:3] + (jnp.array(uM),) + zero_ctl(n)[4:]; zero = zero_ctl(n); key = jax.random.PRNGKey(seed); ramp = min(5.0, dur / 4); rel = REL if release is None else release
    st = st0; step0 = 0
    if burn > 0: st = run_plain(eng, st, 0.0, burn, key); step0 = int(round(burn / DT)); 
    t0 = burn; per = int(round(SAVE / DT)); T = dur + rel + extra_release; nst = int(round(T / DT / per)) * per
    fin, tr = eng.run_ctl(st, t0, DT, nst, key, ctl, t0, t0 + dur, ramp, step0=step0, save_every=per)
    tw = eng.run_ctl(st, t0, DT, nst, key, zero, t0, t0 + dur, ramp, step0=step0, save_every=per) if sham_twin else None
    rho = 1 / (1 + np.exp(-np.array(tr[3]))); mr = rho.mean(1); tt = SAVE * (1 + np.arange(len(mr))); other = (mr < 0.5) if state == 'a' else (mr > 0.5)
    # persistence: other side for the final 20/g of the release (and at the end)
    nrel = int(round(rel / SAVE)); persists = bool(other[-nrel:].all())
    cross = float(tt[np.argmax(other)]) if other.any() else None
    E = np.array(tr[5]); Sp, Sm = eng.Sp, eng.Sm; MUt = np.array(tr[2]); Qt = np.exp(MUt - MUt.max(2, keepdims=True)); Qt /= Qt.sum(2, keepdims=True)
    Wp = Qt[:, :, Sp].sum(2); Wm = Qt[:, :, Sm].sum(2)                                   # belief mass of each cell on the +y / -y body-row places (current assignment, robust to twin exchanges)
    ep = (E * Wp).sum(1) / Wp.sum(1); em = (E * Wm).sum(1) / Wm.sum(1); rep_other = (em > ep) if state == 'a' else (ep > em)
    flip = float(tt[np.argmax(rep_other)]) if rep_other.any() else None; nrep = int(round((10 / G) / SAVE)); rep_end = bool(rep_other[-nrep:].all())   # reporter lags rho by ~2 tu: scored over the second half of the release (last 10/g)
    ident = None
    if tw is not None: ident = max(float(jnp.abs(tr[i] - tw[1][i]).max()) for i in range(3))                    # structure x, c, mu vs sham twin
    s = summarize3(eng, fin); sw = bool(persists and rep_end and s['orbit_complete'] and s['label'] == 'L' and (ident == 0.0 if ident is not None else True))
    return dict(state=state, centre=centre, dur=dur, amp=float(amp), n_lit=int(lit.sum()), dose=float(amp * dur * lit.sum()), switch=sw, persists=persists, rep_end=rep_end, complete=bool(s['orbit_complete'] and s['label'] == 'L'), struct_diff=ident,
                t_cross=cross, t_rep_flip=flip, lag=(None if cross is None or flip is None else flip - cross), mean_rho_end=float(mr[-1]), rho_min_during=float(mr.min() if state == 'a' else mr.max()))
def bisect(state, centre, dur, a0=0.25, amax=2000.0, nb=5, **kw):
    lo, hi, a = 0.0, None, a0; calls = 0
    while a <= amax:
        r = trial(state, centre, dur, a, **kw); calls += 1
        if r['switch']: hi = a; break
        lo = a; a *= 2
    if hi is None: return dict(state=state, centre=centre, dur=dur, thr=None, bracket_lo=lo, calls=calls, last=r)
    for _ in range(nb):
        mid = 0.5 * (lo + hi); r = trial(state, centre, dur, mid, **kw); calls += 1
        if r['switch']: hi = mid
        else: lo = mid
    r = trial(state, centre, dur, hi, **kw); n_lit = r['n_lit']
    return dict(state=state, centre=centre, dur=dur, thr=hi, lo=lo, n_lit=n_lit, dose=float(hi * dur * n_lit), lag=r['lag'], t_cross=r['t_cross'], t_rep_flip=r['t_rep_flip'], calls=calls, struct_diff=r['struct_diff'])
def job_bis(state, centre, dur): return bisect(state, centre, dur)
if __name__ == "__main__":
    from par import run_jobs; t0 = time.time(); cen = list(range(24)) + [-1]
    res = run_jobs(job_bis, [(s, c, d) for s in 'ab' for d in DURS for c in cen], workers=8, label='H3bis'); json.dump(res, open('../data/h3_bisect.json', 'w'))
    print('wall', time.time() - t0)

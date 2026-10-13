"""V4 damage calibration + safe window. Damage trial = memory-secretion light (a->b / b->a push) at gamma>0 with noise; ORGANISM INTACT checked from light on to 300 tu after the light ends."""
import sys, json, time
from lib4 import *
MED = median_dish(); POST = 300.0
def classify(S, tau):
    """first failing frame mode: split (>1 component, none singleton-only), extrusion (singleton component), wrong_place (fill incomplete), drift (Jaccard below tau only)"""
    ok = intact_series(S, tau); 
    if ok.all(): return None, None
    i = int(np.argmax(~ok)); 
    if S['ncomp'][i] > 1:
        return ('extrusion' if S.get('min_comp_size', [2] * len(ok))[i] == 1 else 'split'), float(S['t'][i])
    if not S['fill_ok'][i]: return 'wrong_place', float(S['t'][i])
    return 'drift', float(S['t'][i])
def damage_trial(dish, variant, state, centre, dur, amp, seed, gamma, tau, noise=True, light_post=POST):
    S = switch_trial(dish, variant, state, centre, dur, amp, noise=noise, seed=seed, gamma=gamma, post=light_post, save=1.0, burn=100.0)
    # component sizes for mode classification
    X = np.asarray(S['fin'][0])
    return S
def _frames_minsize(tr_X):
    out = []
    for X in tr_X:
        A = nbr_matrix(X); n, lab = connected_components(csr_matrix(A), directed=False); out.append(np.bincount(lab).min() if n > 1 else 99)
    return np.array(out)
def job_damage(variant, kg, state, centre, dur, amp, seed, gamma, tau):
    d = dict(seed=-1, kappa_g=kg, g=4 * R_ * kg, gamma_factor=1.0)
    e = get_engine(d, variant, noise=True, gamma_on=False, gamma=gamma); arr, perm = settled(d, variant, state); st = tuple(jnp.array(a) for a in arr); key = jax.random.PRNGKey(50_000 + seed); burn = 100.0
    st = run_plain(e, st, 0.0, burn, key); step0 = int(round(burn / DT)); base = nbr_matrix(np.array(st[0])); lit = lit_cells(perm, centre); col = 1 if state == 'a' else 0
    uM = np.zeros((24, 2)); uM[lit, col] = amp; ctl = list(zero_ctl(e)); ctl[3] = jnp.array(uM); ctl = tuple(ctl); ramp = min(5.0, dur / 4)
    per = int(round(1.0 / DT)); nst = int(round((dur + POST) / DT / per)) * per
    fin, tr = e.run_ctl(st, burn, DT, nst, key, ctl, burn, burn + dur, ramp, step0=step0, save_every=per)
    S = series_stats(tr, base); S['t'] = 1.0 + np.arange(nst // per); X = np.asarray(tr[0]); ok = intact_series(S, tau); mode = None; tfail = None
    if not ok.all():
        i = int(np.argmax(~ok)); tfail = float(S['t'][i]); A = nbr_matrix(X[i]); n, lab = connected_components(csr_matrix(A), directed=False)
        if n > 1: mode = 'extrusion' if np.bincount(lab).min() == 1 else 'split'
        elif not S['fill_ok'][i]: mode = 'wrong_place'
        else: mode = 'drift'
    rho_end = float(S['mean_rho'][-1]); sw = bool((rho_end < 0.5) if state == 'a' else (rho_end > 0.5))
    return dict(fail=bool(not ok.all()), mode=mode, t_fail=tfail, min_jac=float(S['jac'].min()), switched=sw, ncomp_max=int(S['ncomp'].max()), fill_all=bool(S['fill_ok'].all()))
def damage_fraction(variant, kg, state, centre, dur, amp, gamma, tau, seeds=range(10), workers=8):
    from par4 import run_jobs
    res = run_jobs(job_damage, [(variant, kg, state, centre, dur, amp, s, gamma, tau) for s in seeds], workers=workers, label=f'dmg a={amp:.2f}')
    return float(np.mean([r['fail'] for r in res])), res
def damage_onset(variant, kg, state, centre, dur, gamma, tau, a_lo, a_hi, tol=0.04, workers=8, log=None):
    """smallest amplitude with fail fraction >= 0.5, assuming monotone; bracket [a_lo, a_hi] expanded by x2 if needed. returns (u_d, history)"""
    hist = []
    def f(a):
        fr, res = damage_fraction(variant, kg, state, centre, dur, a, gamma, tau, workers=workers); hist.append((a, fr)); 
        if log: print('   amp', round(a, 3), 'frac', fr, flush=True)
        return fr
    lo, hi = a_lo, a_hi
    while f(lo) >= 0.5 and lo > 1e-3: hi = lo; lo /= 2
    while f(hi) < 0.5 and hi < 1e5: lo = hi; hi *= 2
    while (hi - lo) / hi > tol:
        mid = np.sqrt(lo * hi); 
        if f(mid) >= 0.5: hi = mid
        else: lo = mid
    return hi, hist

"""v4 shared library: dish engines, settled states, frame statistics (hidden truth), switch trial."""
import os, sys, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from an4 import *
from dish import *
from scipy.sparse.csgraph import connected_components
from scipy.sparse import csr_matrix
DT = 0.0125; DATA = os.path.join(HERE, '..', 'data'); ADULTS = os.path.join(DATA, 'adults'); os.makedirs(ADULTS, exist_ok=True)
TM = make_template4(THETA)
GAMMA0_FILE = os.path.join(DATA, 'gamma0.json'); THR_FILE = os.path.join(DATA, 'intact_threshold.json')

def gamma0():
    return json.load(open(GAMMA0_FILE))['gamma0'] if os.path.exists(GAMMA0_FILE) else 0.0
def tauJ():
    return json.load(open(THR_FILE))['tau_J'] if os.path.exists(THR_FILE) else None

_eng = {}
def get_engine(dish, variant, noise=False, N=None, gamma_on=True, tm=None, gamma=None):
    """engine for a dish (dict from dish.py) and variant ('phi0','phi04','phi08' or a phi_max float). noise: structure+memory noise at the declared levels"""
    tm = tm or TM; phi = VARIANTS[variant] if isinstance(variant, str) else float(variant); alpha = alpha_for(phi, tm)
    gam = gamma0() * dish['gamma_factor'] if gamma_on else 0.0
    if gamma is not None: gam = float(gamma) * dish['gamma_factor']
    key = (round(dish['g'], 9), round(gam, 9), round(alpha, 9), noise, N, id(tm))
    if key not in _eng:
        P = Params4(g=dish['g'], alpha=alpha, gamma=gam, **(dict(sig_h=SIG_H, **NOISE) if noise else {})); e = make_engine4(tm, P, N=N); e.dt = DT; _eng[key] = e
    return _eng[key]

def lstar_for(dish, variant):
    from theory4 import lstar
    phi = VARIANTS[variant] if isinstance(variant, str) else float(variant); a = alpha_for(phi); D = D_k(TM).mean()
    return lstar(dish['g'], c=a * BETA_E * D)

def settled(dish, variant, state, k=0, T=1500.0):
    """deterministic settled adult (no noise, gamma irrelevant at u=0), cached"""
    phi = VARIANTS[variant] if isinstance(variant, str) else float(variant)
    tag = f"{state}_{k}_g{dish['g']:.5f}_p{phi:.3f}_th{THETA:.0f}"; p = os.path.join(ADULTS, hashlib.md5(tag.encode()).hexdigest()[:12] + '.npz')
    if os.path.exists(p): z = np.load(p); return tuple(z[f'a{i}'] for i in range(7)), z['perm']
    e = get_engine(dish, variant, gamma_on=False); st, perm = seeded_start4(TM, k, state, lstar=lstar_for(dish, variant)); fin = run_plain(e, st, 0, T, jax.random.PRNGKey(0))
    arr = tuple(np.array(a) for a in fin); np.savez(p, perm=perm, **{f'a{i}': a for i, a in enumerate(arr)}); return arr, perm

# ------------------------------------------------------------------ frame statistics
def nbr_matrix(X, r=1.6):
    D = np.linalg.norm(X[:, None] - X[None], axis=-1); return (D <= r) & ~np.eye(len(X), dtype=bool)

def frame_stats(X, MU, L, base_nbr, alive=None):
    """hidden truth for one frame (all cells alive). returns dict(angle, ncomp, fill_ok, min_bel, jac, mean_rho)"""
    q = np.exp(MU - MU.max(1, keepdims=True)); q /= q.sum(1, keepdims=True); ok, mb = place_fill(TM, q); pl = q.argmax(1)
    A = nbr_matrix(X); nc = connected_components(csr_matrix(A), directed=False)[0]
    inter = (A & base_nbr).sum(1); uni = (A | base_nbr).sum(1); jac = float(np.where(uni > 0, inter / np.maximum(uni, 1), 1.0).mean())
    ang = tail_angle(TM, X, pl) if len(set(pl.tolist())) >= 20 else np.nan
    return dict(angle=ang, ncomp=int(nc), fill_ok=ok, min_bel=mb, jac=jac, mean_rho=float((1 / (1 + np.exp(-L))).mean()))

def series_stats(tr, base_nbr):
    """tr = tuple of stacked states (T, ...) -> dict of arrays"""
    X, MU, L = np.asarray(tr[0]), np.asarray(tr[2]), np.asarray(tr[3]); rows = [frame_stats(X[i], MU[i], L[i], base_nbr) for i in range(len(X))]
    out = {k: np.array([r[k] for r in rows]) for k in rows[0]}; out['rho_cells'] = 1 / (1 + np.exp(-L)); return out

def intact_series(S, tau=None):
    tau = tauJ() if tau is None else tau
    ok = (S['ncomp'] == 1) & S['fill_ok']
    if tau is not None: ok = ok & (S['jac'] >= tau)
    return ok

# ------------------------------------------------------------------ switch trial
XC = float(TM.Xs[0].mean())
CENTRES = {'middle': np.array([XC, 0.0]), 'limb_side': np.array([XC, 1.5]), 'head_end': np.array([float(TM.Xs[0].min()), 0.0]), 'tail_end': np.array([float(TM.Xs[0].max()), 0.0]), 'whole': None}
R_DISC = 1.5
def lit_cells(perm, centre, r=R_DISC):
    c = CENTRES[centre]
    if c is None: return np.ones(24, bool)
    return np.linalg.norm(TM.Xs[:, perm].T - c[None], axis=1) <= r + 1e-9

def ref_angles(dish, variant):
    out = {}
    for s in 'ab':
        arr, perm = settled(dish, variant, s); pl = np.array(jax.nn.softmax(jnp.array(arr[2]), axis=1)).argmax(1); out[s] = tail_angle(TM, arr[0], pl)
    return out

def switch_trial(dish, variant, state, centre, dur, amp, noise=False, seed=0, burn=100.0, release_f=20.0, save=0.25, gamma_on=False, return_series=False, lit_override=None, sham=False, gamma=None, post=None, light='mem'):
    """memory-secretion light a->b (state 'a': pushes dB) or b->a. Frozen scoring (COMPUTE_PLAN): see score_switch."""
    g = dish['g']; e = get_engine(dish, variant, noise=noise, gamma_on=gamma_on, gamma=gamma); arr, perm = settled(dish, variant, state)
    st = tuple(jnp.array(a) for a in arr); key = jax.random.PRNGKey(50_000 + seed); step0 = 0
    if noise and burn > 0: st = run_plain(e, st, 0.0, burn, key); step0 = int(round(burn / DT))
    t0 = burn if noise else 0.0
    base = nbr_matrix(np.array(st[0]))
    lit = lit_cells(perm, centre) if lit_override is None else lit_override; col = 1 if state == 'a' else 0
    uM = np.zeros((24, 2)); uM[lit, col] = 0.0 if sham else amp
    ctl = list(zero_ctl(e)); ctl[3] = jnp.array(uM); ctl = tuple(ctl); ramp = min(5.0, dur / 4); rel = release_f / g if post is None else post
    per = int(round(save / DT)); nst = int(round((dur + rel) / DT / per)) * per
    fin, tr = e.run_ctl(st, t0, DT, nst, key, ctl, t0, t0 + dur, ramp, step0=step0, save_every=per)
    S = series_stats(tr, base); S['t'] = save * (1 + np.arange(nst // per)); S['lit'] = lit; S['n_lit'] = int(lit.sum()); S['dur'] = dur; S['rel'] = rel; S['fin'] = [np.array(a) for a in fin]
    return S

def score_switch(S, state, ref, tau=None):
    """frozen switch scoring. ref = settled tail angle of the TARGET state in this dish/variant. returns dict(switch, ...)."""
    t = S['t']; dur, rel = S['dur'], S['rel']; mr = S['mean_rho']; other = (mr < 0.5) if state == 'a' else (mr > 0.5)
    last = t > t[-1] - rel / 2; state_ok = bool(other[last].all())
    a_end_mask = t > t[-1] - rel / 10; ang = float(np.nanmean(S['angle'][a_end_mask])); flipped = (np.sign(ang) == np.sign(ref)) and abs(ang - ref) <= 0.2 * abs(ref)
    intact = intact_series(S); intact_all = bool(intact.all())
    tcross = float(t[np.argmax(other)]) if other.any() else None
    a0 = S['angle'][0]; sgn = np.sign(ref); fl = (np.sign(S['angle']) == sgn) & ~np.isnan(S['angle']); tflip = float(t[np.argmax(fl)]) if fl.any() else None
    rc = S['rho_cells']; cross_cells = [float(t[np.argmax((rc[:, i] < 0.5) if state == 'a' else (rc[:, i] > 0.5))]) if ((rc[:, i] < 0.5) if state == 'a' else (rc[:, i] > 0.5)).any() else None for i in range(24)]
    return dict(switch=bool(state_ok and flipped and intact_all), state_ok=state_ok, shape_ok=bool(flipped), intact=intact_all, angle_end=ang, ref=float(ref), t_cross=tcross, t_flip=tflip,
                lag=(None if tcross is None or tflip is None else tflip - tcross), min_jac=float(S['jac'].min()), max_nbr_loss=float(1 - S['jac'].min()), min_ncomp_ok=bool((S['ncomp'] == 1).all()), fill_ok=bool(S['fill_ok'].all()), cell_cross=cross_cells)

def bisect_switch(dish, variant, state, centre, dur, a0=0.25, amax=4000.0, nb=5, noise=False, seed=0, ref=None, **kw):
    ref = ref_angles(dish, variant)['b' if state == 'a' else 'a'] if ref is None else ref
    def trial(a):
        S = switch_trial(dish, variant, state, centre, dur, a, noise=noise, seed=seed, **kw); r = score_switch(S, state, ref); r['n_lit'] = S['n_lit']; return r
    lo, hi, a, calls, hi_r, last = 0.0, None, a0, 0, None, None
    while a <= amax:
        r = trial(a); calls += 1; last = r
        if r['switch']: hi, hi_r = a, r; break
        lo = a; a *= 2
    if hi is None: return dict(state=state, centre=centre, dur=dur, thr=None, bracket_lo=lo, calls=calls, last={k: v for k, v in last.items() if k != 'cell_cross'}, n_lit=last['n_lit'])
    for _ in range(nb):
        mid = 0.5 * (lo + hi); r = trial(mid); calls += 1
        if r['switch']: hi, hi_r = mid, r
        else: lo = mid
    return dict(state=state, centre=centre, dur=dur, thr=hi, lo=lo, n_lit=hi_r['n_lit'], dose=float(hi * dur * hi_r['n_lit']), calls=calls, **{k: v for k, v in hi_r.items() if k not in ('n_lit',)})

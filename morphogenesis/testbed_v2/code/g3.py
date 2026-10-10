"""G3 switch: white-box light-gated memory secretion on a disc of template radius R_DISC around place k (cells whose PLACE lies within R_DISC of the centre, body frame).
Deterministic trial: settled adult -> forcing (raised-cosine ramps, ramp 5) for `dur` -> release 2000 tu.  Sham twin = same code, amp 0."""
import sys, json, time; sys.path.insert(0, '.')
from an2 import *
from g2cfg import FULL, DT
R_DISC = 1.5; RAMP = 5.0; RELEASE = 2000.0; MOVE_TOL = 0.3
_cache = {}; _sham = {}
def setup(form, cfg=None, k=0):
    key = (form, k, tuple(sorted((cfg or FULL).items())))
    if key not in _cache:
        from world2 import settled_adult
        arr, perm = settled_adult(form, k, cfg=cfg); tm = make_template2(); eng = make_engine2(tm, Params2(**(cfg or FULL))); eng.dt = DT
        _cache[key] = (eng, tuple(jnp.array(a) for a in arr), perm, tm)
    return _cache[key]
def disc_cells(tm, perm, centre_place, r=R_DISC):
    return np.linalg.norm(tm.Xs[:, perm].T - tm.Xs[:, centre_place][None], axis=1) <= r + 1e-9
def trial(form, centre, dur, amp, cfg=None, k=0, save=2.0, full_release=True, lit_override=None):
    """returns dict with end form, completeness, max displacement vs sham twin, persistence, rho/type-flip times"""
    eng, st0, perm, tm = setup(form, cfg, k); n = 24; tgt = 5 if form == 'L' else 4            # L->R pushes mR (index 5); R->L pushes mL (index 4)
    lit = (np.ones(n, bool) if centre < 0 else disc_cells(tm, perm, centre)) if lit_override is None else lit_override
    ext = np.zeros((n, NL)); ext[lit, tgt] = amp; amps = (jnp.array(ext), jnp.zeros((n, NL)), jnp.zeros(n), jnp.zeros((n, 24)), jnp.ones(n))
    zero = (jnp.zeros((n, NL)), jnp.zeros((n, NL)), jnp.zeros(n), jnp.zeros((n, 24)), jnp.ones(n)); key = jax.random.PRNGKey(0); dt = DT
    per = int(round(save / dt)); T1 = dur + 200.0; n1 = int(round(T1 / dt / per)) * per
    fin, tr = eng.run_ctl(st0, 0.0, dt, n1, key, amps, 0.0, dur, RAMP, save_every=per)
    sk = (form, k, dur, tuple(sorted((cfg or FULL).items())))
    if sk not in _sham: _sham[sk] = eng.run_ctl(st0, 0.0, dt, n1, key, zero, 0.0, dur, RAMP, save_every=per)     # sham twin (identical code path, amp 0)
    fin0, tr0 = _sham[sk]
    disp = float(np.linalg.norm(np.array(tr[0]) - np.array(tr0[0]), axis=2).max())
    rho_t = 1 / (1 + np.exp(-np.array(tr[4]))); mean_rho = rho_t.mean(1); out = dict(centre=centre, dur=dur, amp=amp, n_lit=int(lit.sum()), max_disp=disp, form0=form)
    # flip times: rho crossing 0.5 (mean rho) and body-row type flip
    tt = save * (1 + np.arange(len(mean_rho))); cross = (mean_rho < 0.5) if form == 'L' else (mean_rho > 0.5)
    out['t_rho_cross'] = float(tt[np.argmax(cross)]) if cross.any() else None
    br = np.where((tm.CL != tm.CR).any(0))[0]; cells_br = np.where(np.isin(perm, br))[0]
    C = np.array(tr[1]); tgtC = tm.CR if form == 'L' else tm.CL; curC = tm.CL if form == 'L' else tm.CR
    dflip = np.linalg.norm(C[:, cells_br, :] - tgtC[:, perm[cells_br]].T[None], axis=2) < np.linalg.norm(C[:, cells_br, :] - curC[:, perm[cells_br]].T[None], axis=2)
    fl = dflip.all(1); out['t_type_flip'] = float(tt[np.argmax(fl)]) if fl.any() else None
    # release
    stages = [500.0, 1500.0] if full_release else [500.0]; st = fin; t = T1; k0 = n1; labels = []
    for T in stages:
        st = eng.run_ctl(st, t, dt, int(round(T / dt)), key, zero, -1e30, -1e29, 1.0, step0=k0); t += T; k0 += int(round(T / dt))
        s = summarize(eng, st, mirror_orbits=True); labels.append((s['label'], s['orbit_complete'], round(s['mean_rho'], 3)))
    out['end_labels'] = labels; end = labels[-1]; other = 'R' if form == 'L' else 'L'
    s = summarize(eng, st, mirror_orbits=True); X = np.array(st[0]); comp = max(1, 1)
    from world2 import component_labels
    ncomp = int(component_labels(X, 1.6).max() + 1); out['ncomp'] = ncomp
    rho_end = float(s['mean_rho']); out['rho_end'] = rho_end; side_ok = (rho_end < 0.5) if form == 'L' else (rho_end > 0.5)
    out['switch'] = bool(end[0] == other and end[1] and ncomp == 1 and side_ok and all(l[0] == other for l in labels))
    out['switch_moveless'] = bool(out['switch'] and disp < MOVE_TOL)
    out['whole_form_flipped_ignoring_move'] = out['switch']
    return out
AMPS = [0.5, 1, 2, 4, 8, 16, 32, 64, 128]
def scan_job(form, centre, dur, cfgname='FULL'):
    """geometric amplitude scan (stop when the body is torn: displacement > 20); if a switch is found, bisect (5 steps) between the last non-switch and the first switch amplitude"""
    import g2cfg; cfg = getattr(g2cfg, cfgname); rows = []; first = None; last_no = 0.0
    for a in AMPS:
        r = trial(form, centre, dur, a, cfg=cfg, full_release=False); r['end_labels'] = [list(x) for x in r['end_labels']]; rows.append(r)
        if r['switch']:
            first = a; break
        last_no = a
        if r['max_disp'] > 20.0: break
    thr = None
    if first is not None:
        lo, hi = last_no, first
        for _ in range(5):
            mid = 0.5 * (lo + hi) if lo > 0 else hi / 2; r = trial(form, centre, dur, mid, cfg=cfg, full_release=False); r['end_labels'] = [list(x) for x in r['end_labels']]; rows.append(r)
            if r['switch']: hi = mid
            else: lo = mid
        thr = hi
    sw = [r for r in rows if r['switch']]; mv = [r for r in sw if r['switch_moveless']]
    return dict(form=form, centre=centre, dur=dur, rows=rows, thr_any=thr, n_switch_rows=len(sw), n_moveless_switch=len(mv), min_disp_among_switch=min([r['max_disp'] for r in sw], default=None),
                max_flip_progress=max([abs(r['rho_end'] - 0.783) for r in rows]), any_type_flip=any(r['t_type_flip'] is not None for r in rows))
def probe(form, centre, dur, amp, cfgname='FULL'):
    import g2cfg; r = trial(form, centre, dur, amp, cfg=getattr(g2cfg, cfgname), full_release=False); r['end_labels'] = [list(x) for x in r['end_labels']]; return r
if __name__ == "__main__":
    from par import run_jobs
    cen = list(range(24)) + [-1]; args = [('L', c, d) for d in (10.0, 40.0, 160.0) for c in cen] + [('R', c, d) for d in (10.0, 40.0, 160.0) for c in (8, 12, 4, 0, 22, -1)]
    res = run_jobs(scan_job, args, workers=8, label='g3scan'); json.dump(res, open('../data/g3_scan.json', 'w'))
    for r in res: print(r['form'], r['centre'], r['dur'], 'thr', r['thr_any'], 'n_sw', r['n_switch_rows'], 'moveless', r['n_moveless_switch'], 'type_flip', r['any_type_flip'], 'maxprog', round(r['max_flip_progress'], 3))

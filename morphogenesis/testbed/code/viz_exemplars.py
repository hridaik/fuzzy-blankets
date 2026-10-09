"""Viewer exemplars for T1/T2 (declared exemplar rule: FIXED seeds, no outcome-based selection; seed numbers are stated in each title)."""
import sys, os, json; sys.path.insert(0, '.'); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'viz'))
from asm import *
from mem import mem_params, mem_start, wB
import build_viewer_testbed as V
OUT = os.path.join(MORPH, 'viz', 'output', 'testbed'); os.makedirs(OUT + '/audit', exist_ok=True); os.makedirs(OUT + '/observable', exist_ok=True)
entries = []

def roll(label, tmpl, eng, st, T, save_dt=2.0, t0=0.0, ext=None, key=0, aud_target=None, plan_overlay=False, lig_ch=None, kappa_m=None, events=None, step0=0):
    dt = eng.dt; per = int(round(save_dt / dt)); dt = save_dt / per
    fin, tr = eng.run(st, t0, dt, per * int(T / save_dt), jax.random.PRNGKey(key), ext, step0, save_every=per)
    X = np.concatenate([np.array(st[0])[None], np.array(tr[0])]); C = np.concatenate([np.array(st[1])[None], np.array(tr[1])])
    MU = np.concatenate([np.array(st[2])[None], np.array(tr[2])]); ZE = np.concatenate([np.array(st[3])[None], np.array(tr[3])])
    tt = t0 + save_dt * np.arange(len(X)); types = np.stack([cell_types(c.T) for c in C])
    speed = np.r_[0, np.linalg.norm(np.diff(X, axis=0), axis=2).mean(1) / save_dt]
    r = dict(label=label, t=tt, X=X, types=types, series=dict(mean_speed=speed))
    if lig_ch is not None: r['ligand'] = dict(kappa=kappa_m, C=C[:, :, lig_ch])
    if events: r['events'] = events
    p = np.array(jax.nn.softmax(jnp.array(MU), axis=2))
    r['role'] = p.argmax(2)
    if aud_target is not None: r['target'] = np.stack([aud_target(X[k], types[k], p[k]) for k in range(len(X))])
    if plan_overlay: r['planB'] = np.array(jax.nn.softmax(jnp.array(ZE), axis=2))[:, :, 1]
    r['audit_series'] = dict(free_energy=np.array([float(np.array(eng.free_energy((jnp.array(X[k]), jnp.array(C[k]), jnp.array(MU[k]), jnp.array(ZE[k]))), float).sum()) for k in range(len(X))]),
                             mean_max_belief=p.max(2).mean(1))
    if plan_overlay: r['audit_series']['mean_wB'] = r['planB'].mean(1)
    return r, fin

def aligned_target(tmpl, plan=0):
    def f(X, ty, p):                                  # template placed on the body by rigid alignment of the slot assignment (argmax belief)
        slot = p.argmax(1); T = tmpl.Xs[plan][:, slot].T
        a = T - T.mean(0); b = X - X.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        # template cells drawn at the aligned slot positions of the *occupying* cell (shows deviation from target)
        return (R @ a.T).T + X.mean(0)
    return f

def emit(name, title, rolls, sub='', obs=True, lig=False):
    for aud in (True, False):
        if not aud and not obs: continue
        rr = []
        for r in rolls:
            r2 = dict(r)
            if not lig: r2.pop('ligand', None)
            rr.append(r2)
        sub_ = 'audit' if aud else 'observable'
        p = V.build_html(rr, f'{OUT}/{sub_}/{name}.html', title, audit=aud, sub=sub)
        entries.append(dict(name=name, tier=sub_, title=title, path=os.path.relpath(p, os.path.join(MORPH, 'viz'))))

def main():
    key = jax.random.PRNGKey(0)
    # ---- T1.4 oracle vs engine (vanilla 8, positional ON, canonical clock), oracle initial beliefs of primary_0000 and primary_0003
    t8 = vanilla8(); eng8 = make_engine(t8, Params(k_mu=1.4, k_a=1.2)); eng8.dt = 0.02
    for nm in ('primary_0000', 'secondary_0005'):
        o = oracle_run(nm); T = 200
        idx = np.arange(0, T + 1, 2)
        Xo = o['pos'][:, :, idx].transpose(2, 1, 0); Co = o['sec'][:, :, idx].transpose(2, 1, 0)
        ro = dict(label=f'ORACLE (Octave spm_ADEM) {nm}', t=idx.astype(float), X=Xo, types=np.stack([cell_types(c.T) for c in Co]), series=dict(mean_speed=np.r_[0, np.linalg.norm(np.diff(Xo, axis=0), axis=2).mean(1) / 2]),
                  target=np.stack([t8.Xs[0].T] * len(idx)))
        st = eng8.init_from_mu(o['v0'].T)
        re_, _ = roll(f'ENGINE (continuous-time, k_mu 1.4, k_a 1.2) {nm}', t8, eng8, st, float(T), aud_target=lambda X, ty, p: t8.Xs[0].T)
        emit(f't14_oracle_vs_engine_{nm}', f'T1.4 oracle vs engine, {nm}', [ro, re_], sub='Same initial beliefs; time axis: 1 engine unit ~ 1 SPM bin. Target overlay (AUDIT) = template positions.')
    # ---- T2a assembly: positional ON vs OFF (vanilla8, draw 0) 
    pOff = Params(k_mu=1.4, k_a=1.2, pos_on=False, pi_a_x=0.0); engOff = make_engine(t8, pOff); engOff.dt = 0.02
    st = eng8.init_from_mu(np.random.default_rng(0).standard_normal((8, 8)) / 8); r_on, _ = roll('positional channel ON (draw 0)', t8, eng8, st, 300.0, aud_target=lambda X, ty, p: t8.Xs[0].T)
    stO = engOff.init_from_mu(np.random.default_rng(0).standard_normal((8, 8)) / 8); r_off, _ = roll('positional channel OFF (relational, draw 0)', t8, engOff, stO, 300.0, aud_target=aligned_target(t8))
    emit('t2a_vanilla8_pos_on_vs_off', 'T2a vanilla 8-cell: positional ON vs OFF', [r_on, r_off], sub='OFF fails: 0/50 assembled (FAILED: undifferentiated cluster). Fixed seed 0.')
    # ---- compact body A: near-uniform start (fails) vs seeded start (assembles), relational
    tA = make_body('A'); P = tb_params(); engA = make_engine(tA, P); engA.dt, engA.rho = auto_dt(engA, tA)
    stu = engA.init_from_mu(np.random.default_rng(0).standard_normal((24, 24)) / 8); r_u, _ = roll('A: near-uniform beliefs (seed 0) - fails', tA, engA, stu, 400.0, save_dt=4.0, aud_target=aligned_target(tA))
    r_s, _ = roll('A: seeded start, jitter 0.3 (seed 0) - assembles', tA, engA, seeded_start(tA, 0, jit_x=0.3), 400.0, save_dt=4.0, aud_target=aligned_target(tA))
    emit('t2a_bodyA_nearuniform_vs_seeded', 'T2a 24-cell body A, relational: near-uniform vs seeded start', [r_u, r_s])
    # ---- T2c adults A and B (K=1 templates), natural noise ensemble members under noise
    tB = make_body('B'); engB = make_engine(tB, P); engB.dt, engB.rho = auto_dt(engB, tB)
    r_A, _ = roll('plan A adult (seed 0)', tA, engA, seeded_start(tA, 0, jit_x=0.3), 300.0, save_dt=4.0, aud_target=aligned_target(tA))
    r_B, _ = roll('plan B adult (seed 0) [K=1 template]', tB, engB, seeded_start(tB, 0, jit_x=0.3), 300.0, save_dt=4.0, aud_target=aligned_target(tB))
    emit('t2c_adults_A_and_B', 'T2c plan A and plan B adults (separate K=1 models)', [r_A, r_B], sub='A and B are each stable ONLY as separate K=1 templates; in the mixture (memory) model B is not stable (see t2c_memory_B_decays).')
    # ---- T2c memory model: B-start decays to A (negative result)
    km, ma, pim = 1.0, 0.5, 20.0
    tAB = make_body('AB', kappa_m=km, mem_amp=ma); Pm, _ = mem_params(pi_m=pim, pi_zeta=0.001, kappa_m=km, bias=1.0, mem_amp=ma); engm = make_engine(tAB, Pm); engm.dt, engm.rho = auto_dt(engm, tAB)
    for plan, nmx in ((0, 'A start'), (1, 'B start')):
        pass
    stA, _ = mem_start(tAB, 0); stB_, _ = mem_start(tAB, 1)
    r1, _ = roll('memory model, A start (kappa_m 1, a 0.5, pi_m 20)', tAB, engm, stA, 240.0, save_dt=4.0, t0=1e4, lig_ch=4, kappa_m=km, plan_overlay=True)
    r2, _ = roll('memory model, B start: plan-B belief decays (NEGATIVE)', tAB, engm, stB_, 240.0, save_dt=4.0, t0=1e4, lig_ch=4, kappa_m=km, plan_overlay=True)
    emit('t2c_memory_B_decays', 'T2c memory model: A start vs B start (no bistability found)', [r1, r2], lig=True)
    # ---- T2d mirror forms and pulses (chiral body)
    import chiral as CH
    tc, engc = CH.mk(); stL = CH.start(tc, 0, False); stR = CH.start(tc, 0, True)
    rL, _ = roll('chiral form L (seed 0)', tc, engc, stL, 200.0, save_dt=4.0, aud_target=aligned_target(tc)); rR, _ = roll('chiral form R = mirror image (seed 0)', tc, engc, stR, 200.0, save_dt=4.0, aud_target=aligned_target(tc))
    emit('t2d_mirror_forms', 'T2d chiral body: both mirror forms are stable', [rL, rR])
    n, nc = tc.n, tc.nc; rng = np.random.default_rng(777); perm = rng.permutation(n); c0 = tc.Xs[0][:, 0]; disc = np.where(np.linalg.norm(tc.Xs[0][:, perm].T - c0, axis=1) <= 1.6)[0]
    settle = engc.run_final(stL, 0.0, engc.dt, int(100 / engc.dt), key, None, 0); ev = [dict(t0=1e4, t1=1e4 + 20, cells=[int(i) for i in disc], label='pulse')]
    rr = []
    for lab, amp in (('sham (amp 0)', 0.0), ('head-tip pulse amp 1 (no effect)', 1.0), ('head-tip pulse amp 4 (body disrupted)', 4.0)):
        a = np.zeros((n, nc)); a[disc, 3] = amp
        r, _ = roll(lab, tc, engc, settle, 200.0, save_dt=4.0, t0=1e4, ext=(jnp.array(a), 1e4, 1e4 + 20), aud_target=aligned_target(tc), events=ev if amp > 0 else None); rr.append(r)
    emit('t2d_pulse_vs_sham', 'T2d disc pulse (head tip, signal 4, 20 time units): sham vs sub-threshold vs disruptive', rr, sub='No identity-preserving mirror switch was found (see CHIRALITY.md). Same dose family, same seed (CRN).')
    # ---- natural ensemble exemplars under noise
    from exports import load_tier
    man = json.load(open(os.path.join(TB, 'data', 'natural', 'manifest.json')))
    rr = []
    for kind in ('A', 'B', 'chiral'):
        d = load_tier(os.path.join(TB, 'data', 'natural', f'{kind}_train_00'), 'obs'); h = load_tier(os.path.join(TB, 'data', 'natural', f'{kind}_train_00'), 'hid', audit=True)
        rr.append(dict(label=f'natural ensemble {kind}, member train_00 (sigma {man["sigma"]})', t=d['t'], X=d['X'], types=d['types'], series=dict(mean_speed=np.r_[0, np.linalg.norm(np.diff(d['X'], axis=0), axis=2).mean(1) / 5]),
                       role=h['role'], audit_series=dict(free_energy=h['free_energy'].sum(1))))
    emit('natural_ensemble_noise', 'Natural (unperturbed) ensemble under operating noise', rr)
    json.dump(entries, open(os.path.join(OUT, 'entries.json'), 'w'), indent=1)
    print(len(entries), 'viewer files')

if __name__ == '__main__': main()

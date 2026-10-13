"""V2 coupled memory at the median-coupling dish. modes: theory | lstar | bath | dur"""
import sys, json, time
from lib4 import *
from theory4 import *
MED = median_dish()
def theory_row(variant, dish=MED):
    phi = VARIANTS[variant]; a = alpha_for(phi); D = D_k(TM); Wm = float(W_of(TM).mean()); c = a * BETA_E * D.mean(); g = dish['g']
    return dict(variant=variant, phi_max=phi, alpha=a, g=g, D_k=D.tolist(), D_mean=float(D.mean()), D_max=float(D.max()), phi_bar=float(c / g), g_eff=float(g + c), phi_cells=phi_cells(TM, g, a).tolist(),
                lstar_pred=float(lstar(g, c=c)), lstar_phi0=float(lstar(g)), W_mean=Wm, Bc_pred=Bc(Wm, g, c), Bc_pred_phi0=Bc(Wm, g, 0.0), lock_pred=(Bc(Wm, g, c) is None))
def job_lstar(variant, state, seed=0):
    arr, perm = settled(MED, variant, state, seed); L = arr[3]; e = get_engine(MED, variant, gamma_on=False); st = tuple(jnp.array(a) for a in arr)
    d = e.diagnostics(st); pl = np.array(jax.nn.softmax(jnp.array(arr[2]), 1)).argmax(1)
    return dict(variant=variant, state=state, seed=seed, mean_l=float(L.mean()), sd_l=float(L.std()), min_l=float(L.min()), max_l=float(L.max()), l_cells_by_place={int(p): float(l) for p, l in zip(pl, L)}, angle=float(tail_angle(TM, arr[0], pl)),
                Delta_mean=float(np.array(d['Delta']).mean()), Delta_by_place={int(p): float(x) for p, x in zip(pl, np.array(d['Delta']))})
def job_bath(variant, Bmax=1.2, nstep=48, hold=80.0, extra_phi=None):
    key_v = variant if extra_phi is None else extra_phi
    e = get_engine(MED, key_v, gamma_on=False); arr, perm = settled(MED, key_v, 'a'); st = tuple(jnp.array(a) for a in arr)
    sched = list(np.linspace(0, Bmax, nstep + 1)) + list(np.linspace(Bmax, 0, nstep + 1)[1:]) + list(np.linspace(0, -Bmax, nstep + 1)[1:]) + list(np.linspace(-Bmax, 0, nstep + 1)[1:])
    rows = []; t = 0.0; step0 = 0; key = jax.random.PRNGKey(0)
    for s in sched:
        ctl = list(zero_ctl(e)); ctl[10] = jnp.array([max(-s, 0.0), max(s, 0.0)]); ctl = tuple(ctl)
        st = e.run_ctl(st, t, DT, int(hold / DT), key, ctl, -1e30, 1e30, 1.0, step0=step0); t += hold; step0 += int(hold / DT)
        L = np.array(st[3]); rho = 1 / (1 + np.exp(-L)); pl = np.array(jax.nn.softmax(jnp.array(np.array(st[2])), 1)).argmax(1)
        rows.append((float(s), float(rho.mean()), float(L.mean()), float((rho > 0.5).mean()), float(tail_angle(TM, np.array(st[0]), pl)) if len(set(pl.tolist())) > 20 else float('nan')))
    return dict(variant=variant, extra_phi=extra_phi, rows=rows)
def job_dur(variant, state, seed, T=10000.0, chunk=10.0):
    e = get_engine(MED, variant, noise=True, gamma_on=False); arr, perm = settled(MED, variant, state); st = tuple(jnp.array(a) for a in arr)
    key = jax.random.PRNGKey(9000 + seed + (0 if state == 'a' else 100)); k = int(round(chunk / DT)); st = run_plain(e, st, 0.0, 100.0, key); step = int(100 / DT); t = 100.0
    base = nbr_matrix(np.array(st[0])); rows = []; tsw = None
    for c in range(int(T / chunk)):
        st = run_plain(e, st, t, chunk, key, step0=step); t += chunk; step += k
        f = frame_stats(np.array(st[0]), np.array(st[2]), np.array(st[3]), base); rows.append((f['angle'], f['ncomp'], f['fill_ok'], f['min_bel'], f['jac'], f['mean_rho']))
        if tsw is None and ((f['mean_rho'] < 0.5) if state == 'a' else (f['mean_rho'] > 0.5)): tsw = t - 100.0
    R = np.array(rows, float); return dict(variant=variant, state=state, seed=seed, t_switch=tsw, mean_rho_min=float(R[:, 5].min()), mean_rho_max=float(R[:, 5].max()), angle_mean=float(np.nanmean(R[:, 0])), angle_sd=float(np.nanstd(R[:, 0])),
        max_ncomp=int(R[:, 1].max()), fill_all=bool(R[:, 2].all()), min_bel=float(R[:, 3].min()), jac=R[:, 4].tolist())
if __name__ == "__main__":
    from par4 import run_jobs; mode = sys.argv[1]; t0 = time.time(); V = list(VARIANTS)
    if mode == 'theory':
        json.dump([theory_row(v) for v in V], open('../data/v2_theory.json', 'w'), indent=1)
        for v in V:
            r = theory_row(v); print({k: (round(x, 4) if isinstance(x, float) else x) for k, x in r.items() if k not in ('D_k', 'phi_cells')})
    elif mode == 'lstar':
        res = run_jobs(job_lstar, [(v, s) for v in V for s in 'ab'], label='V2b'); json.dump(res, open('../data/v2_lstar.json', 'w'))
        for r in res: print(r['variant'], r['state'], round(r['mean_l'], 4), round(r['sd_l'], 4), round(r['angle'], 2))
    elif mode == 'bath':
        res = run_jobs(job_bath, [(v,) for v in V], label='V2c', workers=3); json.dump(res, open('../data/v2_bath.json', 'w'))
    elif mode == 'dur':
        res = run_jobs(job_dur, [(v, s, k) for v in V for s in 'ab' for k in range(10)], label='V2d'); json.dump(res, open('../data/v2_dur.json', 'w'))
        for r in res: print(r['variant'], r['state'], r['seed'], r['t_switch'], round(r['mean_rho_min'], 3), round(r['mean_rho_max'], 3), r['max_ncomp'], r['fill_all'], round(r['min_bel'], 3), round(min(r['jac']), 3))
    print('wall', time.time() - t0)

"""H2 memory theory (a)-(e)."""
import sys, json, time; sys.path.insert(0, '.')
from an3 import *
from theory3 import *
DT = 0.0125
NOISE = dict(sig_x=.02, sig_c=.02, sig_mu=.02, sig_d=.02, sig_e=.02)
def mk(N=None, **kw):
    tm = make_template2(); e = make_engine3(tm, Params3(**kw), N=N); e.dt = DT; return tm, e
def subst(st, idxs): return tuple(a[jnp.array(idxs)] for a in st)

def job_isolated(N, l0, T=120.0, dist=40.0):
    tm, e = mk(N); st, perm = seeded_start3(tm, 0, 'a'); X = np.zeros((N, 2)); X[:, 0] = dist * np.arange(N)
    L = np.full(N, float(l0)); rho = 1 / (1 + np.exp(-L)); st = (jnp.array(X), st[1][:N], st[2][:N], jnp.array(L), jnp.array(np.stack([rho, 1 - rho], 1)), st[5][:N])
    ts, ls = [], []
    for k in range(int(T / 1.0)):
        st = run_plain(e, st, k * 1.0, 1.0, jax.random.PRNGKey(0), step0=k * 80); ts.append(k + 1.0); ls.append(np.array(st[3]))
    ts = np.array(ts); ls = np.array(ls)[:, 0]; m = (np.abs(ls) < 0.5) & (np.abs(ls) > 0.01)
    rate = float(-np.polyfit(ts[m], np.log(np.abs(ls[m])), 1)[0]); return dict(N=N, l0=l0, rate=rate, pred=0.1, l_final=float(ls[-1]), n_fit=int(m.sum()))

def job_body(state, seed, T=1500.0):
    tm, e = mk(); st, perm = seeded_start3(tm, seed, state, lstar=1.0 if state == 'a' else 1.0); fin = run_plain(e, st, 0, T, jax.random.PRNGKey(0)); s = summarize3(e, fin)
    L = np.array(fin[3]); W = W_of(tm)[perm]; d = e.diagnostics(fin)
    return dict(state=state, seed=seed, mean_l=float(L.mean()), std_l=float(L.std()), min_l=float(L.min()), max_l=float(L.max()), pred=lstar(), corr_l_W=float(np.corrcoef(L, W)[0, 1]),
                f_mean=float(np.array(d['f']).mean()), label=s['label'], estar_on_row=float(np.array(d['estar'])[np.isin(perm, e.Sp)].mean()), estar_off_row=float(np.array(d['estar'])[np.isin(perm, e.Sm)].mean()), l_cells=L.tolist(), W_cells=W.tolist(), l_edge_centre=None)

def job_bath(Bmax=1.2, nstep=48, hold=80.0, seed=0):
    """quasi-static bath sweep: s = signed bath (s > 0: B_B = s ; s < 0: B_A = -s). 0 -> +Bmax -> 0 -> -Bmax -> 0, from state a. returns rows (s, mean rho, mean l, frac cells rho>0.5)"""
    tm, e = mk(); st, perm = seeded_start3(tm, seed, 'a', lstar=2.29); fin = run_plain(e, st, 0, 300, jax.random.PRNGKey(0)); st = fin
    n = 24; sched = list(np.linspace(0, Bmax, nstep + 1)) + list(np.linspace(Bmax, 0, nstep + 1)[1:]) + list(np.linspace(0, -Bmax, nstep + 1)[1:]) + list(np.linspace(-Bmax, 0, nstep + 1)[1:])
    rows = []; t = 300.0; step0 = int(300 / DT)
    for s in sched:
        mb = jnp.array([max(-s, 0.0), max(s, 0.0)]); ctl = zero_ctl(n)[:10] + (mb,)
        st = e.run_ctl(st, t, DT, int(hold / DT), jax.random.PRNGKey(0), ctl, -1e30, 1e30, 1.0, step0=step0); t += hold; step0 += int(hold / DT)
        L = np.array(st[3]); rho = 1 / (1 + np.exp(-L)); rows.append((float(s), float(rho.mean()), float(L.mean()), float((rho > 0.5).mean())))
    return rows

def job_sigpilot(sh, state='a', T=4000.0, burn=1000.0):
    tm, e = mk(sig_h=sh, **NOISE); st, perm = seeded_start3(tm, 0, state, lstar=2.29); key = jax.random.PRNGKey(5); st = run_plain(e, st, 0, burn, key); Ls = []; k0 = int(burn / DT)
    for i in range(int((T - burn) / 5)): st = run_plain(e, st, burn + 5 * i, 5.0, key, step0=k0 + i * 400); Ls.append(np.array(st[3]))
    Ls = np.array(Ls); return dict(sig_h=sh, median_std=float(np.median(Ls.std(0))), min_std=float(Ls.std(0).min()), mean_l=float(Ls.mean()), min_l=float(Ls.min()), mean_l_traj_min=float(Ls.mean(1).min()), label=summarize3(e, st)['label'])

if __name__ == "__main__":
    from par import run_jobs; mode = sys.argv[1]; t0 = time.time()
    if mode == 'abc':
        ra = run_jobs(job_isolated, [(1, 3.0), (1, -3.0), (2, 3.0), (2, -3.0)], workers=4, label='H2a'); json.dump(ra, open('../data/h2a.json', 'w'))
        for r in ra: print('T1', r)
        rb = run_jobs(job_body, [('a', 0), ('b', 0), ('a', 1), ('b', 1)], workers=4, label='H2b'); json.dump(rb, open('../data/h2b.json', 'w'))
        for r in rb: print('T2', {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k not in ('l_cells', 'W_cells')})
        rc = run_jobs(job_bath, [()], workers=1, label='H2c'); json.dump(rc[0], open('../data/h2c.json', 'w'))
        for row in rc[0][::4]: print('T3', [round(x, 3) for x in row])
    elif mode == 'dur': pass
    elif mode == 'pilot':
        rp = run_jobs(job_sigpilot, [(s,) for s in (0.2, 0.3, 0.4, 0.5, 0.7)], workers=5, label='sig'); json.dump(rp, open('../data/h2_sigh_pilot.json', 'w'))
        for r in rp: print(r)
    print('wall', time.time() - t0)

SIG_H = 0.4
def job_dur(state, seed, T=20000.0, chunk=500.0):
    tm, e = mk(sig_h=SIG_H, **NOISE); st, perm = seeded_start3(tm, seed, state, lstar=2.29); key = jax.random.PRNGKey(2000 + seed + (0 if state == 'a' else 100)); k = int(round(chunk / DT)); log = []; tsw = None; tbad = None
    for c in range(int(T / chunk)):
        st = run_plain(e, st, c * chunk, chunk, key, step0=c * k); s = summarize3(e, st); ml = s['mean_l']
        log.append((c * chunk + chunk, s['label'], round(s['dL'], 3), s['orbit_complete'], round(ml, 3), round(s['std_l'], 3)))
        if tsw is None and ((ml < 0) if state == 'a' else (ml > 0)): tsw = c * chunk + chunk
        if tbad is None and not (s['label'] == 'L' and s['orbit_complete']): tbad = c * chunk + chunk
    return dict(state=state, seed=seed, t_switch=tsw, t_struct_bad=tbad, final=log[-1], min_mean_l=min(l[4] for l in log) if state == 'a' else max(l[4] for l in log), log=log)
if __name__ == "__main__" and sys.argv[1] == 'dur':
    from par import run_jobs; t0 = time.time(); res = run_jobs(job_dur, [(s_, k) for s_ in 'ab' for k in range(10)], workers=7, label='H2e'); json.dump(res, open('../data/h2e_durability.json', 'w'))
    for x in res: print(x['state'], x['seed'], 'switch', x['t_switch'], 'struct_bad', x['t_struct_bad'], x['final'], x['min_mean_l'])
    print('wall', time.time() - t0)

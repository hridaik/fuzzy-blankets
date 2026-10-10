"""G1 (b) orbit-filtered rate and (c) durability.  Operating point G1: beta=4, k_mu=0.2, pi_c=e^1, pi_lam=e^3."""
import sys, json, time; sys.path.insert(0,'.')
OP = dict(beta_E=4.0, k_mu=0.2, pi_c=float(2.718281828459045), pi_lam=float(20.085536923187668))
DT = 0.0125
def rates_filtered():
    from an2 import np, jax, make_engine2, make_template2, Params2, seeded_start2, run_plain, orbits
    P = Params2(fix_rho=1.0, **OP); eng = make_engine2(make_template2(), P); eng.dt = DT
    st, perm = seeded_start2(eng.tm, 0, 'L'); fin = run_plain(eng, st, 0, 800, jax.random.PRNGKey(0))
    J = np.array(eng.jac_flat(fin)); w, V = np.linalg.eig(J); orb = orbits(eng.tm, OP['pi_c'], OP['pi_lam'])
    cnt = np.bincount(orb); pair_places = np.where(cnt[orb] > 1)[0]; pair_cells = np.where(np.isin(perm, pair_places))[0]
    S = 24; off = 24 * 2 + 24 * 4 + 24 * 2; out = []
    for i in np.argsort(np.abs(w.real)):
        if abs(w[i]) < 1e-6: continue
        v = V[:, i]; xs = v[:48].reshape(24, 2); mu = v[off:off + 576].reshape(24, 24)
        m = np.linalg.norm(xs, axis=1) + np.linalg.norm(mu, axis=1); frac = float(m[pair_cells].sum() / m.sum())
        out.append((float(-w[i].real), frac))
    nonorb = [r for r, f in out if f < 0.5]
    return dict(n_pair_cells=len(pair_cells), slowest_all=out[0][0], slowest_orbit_exchange=[r for r, f in out if f >= 0.5][:4], slowest_non_orbit=nonorb[0], first_10=out[:10])

def dur_job(seed, T=20000.0, chunk=500.0, smu=0.02):
    from an2 import np, jax, make_engine2, make_template2, Params2, seeded_start2, run_plain, summarize
    P = Params2(fix_rho=1.0, sig_x=0.02, sig_c=0.02, sig_mu=smu, **OP); eng = make_engine2(make_template2(), P); eng.dt = DT
    st, perm = seeded_start2(eng.tm, seed, 'L'); key = jax.random.PRNGKey(1000 + seed); k = int(round(chunk / DT)); log = []; t_diss = None
    for c in range(int(T / chunk)):
        st = run_plain(eng, st, c * chunk, chunk, key, step0=c * k)
        s = summarize(eng, st, pis=(OP['pi_c'], OP['pi_lam']))
        log.append((c * chunk + chunk, s['label'], round(s['dL'], 3), s['orbit_complete'], round(s['min_orbit_bel'], 3)))
        if t_diss is None and not (s['label'] == 'L' and s['orbit_complete']): t_diss = c * chunk + chunk
    return dict(seed=seed, t_dissolve=t_diss, final=log[-1], max_dL=max(l[2] for l in log), log=log)

if __name__ == "__main__":
    from par import run_jobs
    r = rates_filtered(); print(json.dumps(r)); json.dump(r, open('../data/g1_rates.json', 'w'))
    t0 = time.time(); res = run_jobs(dur_job, [(s,) for s in range(10)] , workers=8, label='g1dur'); json.dump(res, open('../data/g1_durability.json', 'w'))
    for x in res: print(x['seed'], x['t_dissolve'], x['final'], x['max_dL'])
    print('wall', time.time() - t0)

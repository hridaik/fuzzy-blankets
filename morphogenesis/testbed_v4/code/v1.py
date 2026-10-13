"""V1 shapes: alpha=0, gamma=0, rho clamped. 16 seeded completions at rho=1,0; durability 5 seeds x 5000 tu; 11-value sweep."""
import sys, json, time
from lib4 import *
MED = median_dish()
def clamp_ctl(e, rho):
    c = list(zero_ctl(e)); c[12] = jnp.full(24, float(rho)); return tuple(c)
def job_complete(k, rho, theta=THETA):
    tm = make_template4(theta); e = make_engine4(tm, Params4(g=MED['g'])); e.dt = DT
    st, perm = seeded_start4(tm, k, 'a' if rho >= 0.5 else 'b'); fin = run_plain(e, st, 0, 600, jax.random.PRNGKey(0), ctl=clamp_ctl(e, rho))
    X, MU, C = np.array(fin[0]), np.array(fin[2]), np.array(fin[1]); q = np.array(jax.nn.softmax(jnp.array(MU), 1)); ok, mb = place_fill(tm, q)
    ang = tail_angle(tm, X, q.argmax(1)); A = nbr_matrix(X); nc = connected_components(csr_matrix(A), directed=False)[0]
    return dict(k=k, rho=rho, theta=theta, complete=bool(ok and mb >= 0.9), orbit_ok=bool(ok), min_bel=mb, angle=ang, ncomp=int(nc), dA=typed_dist(tm, X, C, 'a'), dB=typed_dist(tm, X, C, 'b'))
def job_durable(seed, rho, T=5000.0, chunk=10.0, theta=THETA):
    tm = make_template4(theta); P = Params4(g=MED['g'], sig_x=.02, sig_c=.02, sig_mu=.02, sig_h=SIG_H, sig_d=.02, sig_e=.02); e = make_engine4(tm, P); e.dt = DT
    st, perm = seeded_start4(tm, seed, 'a' if rho >= 0.5 else 'b'); ctl = clamp_ctl(e, rho)
    key = jax.random.PRNGKey(7000 + seed + int(100 * rho)); t = 0.0; rows = []; step = 0; k = int(round(chunk / DT)); base = None
    st = run_plain(e, st, 0.0, 200.0, key, ctl=ctl); step = int(200 / DT); base = nbr_matrix(np.array(st[0])); t = 200.0
    for c in range(int(T / chunk)):
        st = run_plain(e, st, t, chunk, key, step0=step, ctl=ctl); t += chunk; step += k
        X, MU = np.array(st[0]), np.array(st[2]);
        q = np.exp(MU - MU.max(1, keepdims=True)); q /= q.sum(1, keepdims=True); ok, mb = place_fill(tm, q); A = nbr_matrix(X); nc = connected_components(csr_matrix(A), directed=False)[0]
        inter = (A & base).sum(1); uni = (A | base).sum(1); jac = float(np.where(uni > 0, inter / np.maximum(uni, 1), 1.0).mean())
        rows.append((t - 200.0, tail_angle(tm, X, q.argmax(1)), int(nc), bool(ok), mb, jac))
    R = np.array(rows, float); return dict(seed=seed, rho=rho, theta=theta, angle_mean=float(R[:, 1].mean()), angle_sd=float(R[:, 1].std()), angle_min=float(R[:, 1].min()), angle_max=float(R[:, 1].max()), max_ncomp=int(R[:, 2].max()),
                                           fill_all=bool(R[:, 3].all()), min_bel=float(R[:, 4].min()), min_jac=float(R[:, 5].min()), jac_p1=float(np.percentile(R[:, 5], 1)), rows_every_100=R[::10].tolist())
def job_sweep(rho, start, T=1500.0, theta=THETA):
    tm = make_template4(theta); e = make_engine4(tm, Params4(g=MED['g'])); e.dt = DT; st, perm = seeded_start4(tm, 0, start)
    fin = run_plain(e, st, 0, T, jax.random.PRNGKey(0), ctl=clamp_ctl(e, rho)); X, MU = np.array(fin[0]), np.array(fin[2]); q = np.array(jax.nn.softmax(jnp.array(MU), 1)); ok, mb = place_fill(tm, q)
    return dict(rho=rho, start=start, angle=tail_angle(tm, X, q.argmax(1)), orbit_ok=bool(ok), min_bel=mb)
if __name__ == "__main__":
    from par4 import run_jobs; t0 = time.time(); theta = float(sys.argv[1]) if len(sys.argv) > 1 else THETA; tag = f"th{theta:.0f}"
    rc = run_jobs(job_complete, [(k, r, theta) for r in (1.0, 0.0) for k in range(16)], label='V1c'); json.dump(rc, open(f'../data/v1_complete_{tag}.json', 'w'))
    for r in (1.0, 0.0):
        x = [a for a in rc if a['rho'] == r]; print('rho', r, 'complete', sum(a['complete'] for a in x), '/16 min_bel', min(a['min_bel'] for a in x), 'angle', np.mean([a['angle'] for a in x]), np.std([a['angle'] for a in x]))
    rd = run_jobs(job_durable, [(s, r, 5000.0, 10.0, theta) for r in (1.0, 0.0) for s in range(5)], label='V1d'); json.dump(rd, open(f'../data/v1_durable_{tag}.json', 'w'))
    for a in rd: print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in a.items() if k != 'rows_every_100'})
    rs = run_jobs(job_sweep, [(r, s, 1500.0, theta) for r in np.linspace(0, 1, 11) for s in 'ab'], label='V1s'); json.dump(rs, open(f'../data/v1_sweep_{tag}.json', 'w'))
    for a in rs: print('sweep', a)
    print('wall', time.time() - t0)

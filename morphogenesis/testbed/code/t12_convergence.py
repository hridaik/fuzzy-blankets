"""T1.2: halve dt three (here six) times; trajectories and fixed points must converge; report observed order.
Deterministic RK4; vanilla 8-cell, positional channel ON, oracle initial beliefs of primary_0000, calibrated (k_mu,k_a)."""
import sys, time; sys.path.insert(0, '.')
from common import *

KMU, KA = 1.4, 1.2

def main():
    t = vanilla8(); key = jax.random.PRNGKey(0); o = oracle_run('primary_0000')
    eng = make_engine(t, Params(k_mu=KMU, k_a=KA)); st = eng.init_from_mu(o['v0'].T)
    out = dict(k_mu=KMU, k_a=KA, trajectory={}, fixed_point={})
    dts = [0.08, 0.04, 0.02, 0.01, 0.005, 0.0025, 0.00125]
    # trajectory convergence at T=40 (transient: ramp, differentiation), max-abs state difference to dt=0.00125
    res = {}
    for dt in dts:
        fin = eng.run_final(st, 0.0, dt, int(round(40.0 / dt)), key, None, 0)
        res[dt] = np.concatenate([np.array(a).ravel() for a in fin[:3]])
    ref = res[dts[-1]]
    errs = {dt: float(np.abs(res[dt] - ref).max()) for dt in dts[:-1]}
    ks = sorted(errs, reverse=True)
    out['trajectory'] = dict(T=40.0, err_vs_finest={str(k): errs[k] for k in ks},
                             observed_order={f'{a}->{b}': float(np.log2(errs[a] / errs[b])) for a, b in zip(ks[:-1], ks[1:]) if np.isfinite(errs[a]) and errs[b] > 0})
    # fixed point convergence: integrate to t=400 with each stable dt and compare to the reference phenotype (oracle) and between dts
    ref_p = json.load(open(M2A + '/sealed/reference_phenotype_v2.json')); rp, rs = np.array(ref_p['pos']), np.array(ref_p['sec'])
    fp = {}
    for dt in (0.04, 0.02, 0.01, 0.005):
        fin = eng.run_final(st, 0.0, dt, int(round(400.0 / dt)), key, None, 0)
        X, C, MU, _ = [np.array(a) for a in fin]
        r = max(float(jnp.abs(a).max()) for a in eng.drift(fin, 1e9, jnp.zeros((8, 4))))
        fp[str(dt)] = dict(d_pair_to_oracle_reference=d_pair(X.T, C.T, rp, rs), drift_residual=r, state=np.concatenate([X.ravel(), C.ravel(), MU.ravel()]))
    base = fp['0.005']['state']
    for k, v in fp.items(): v['max_abs_diff_to_dt0.005'] = float(np.abs(v.pop('state') - base).max())
    out['fixed_point'] = fp
    # stability limit: spectral radius of the adult Jacobian vs RK4 limit 2.78/rho
    fin = eng.run_final(st, 0.0, 0.02, int(400 / 0.02), key, None, 0)
    ev = np.linalg.eigvals(np.array(eng.jac_flat(fin, 1e9))); rho = float(np.abs(ev).max())
    out['stability'] = dict(spectral_radius=rho, rk4_dt_limit=2.78 / rho, dt_used=0.02)
    json.dump(out, open(os.path.join(TB, 'data', 't12_convergence.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))

main()

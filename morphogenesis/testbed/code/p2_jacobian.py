"""P2 support: Jacobian eigenvalues at converged adult states of plan A and plan B (separate K=1 models, testbed operating point)."""
import sys, json; sys.path.insert(0, '.')
from asm import *
out = {}
for kind in ('A', 'B', 'chiral'):
    t = make_body(kind); eng = make_engine(t, tb_params()); eng.dt, eng.rho = auto_dt(eng, t)
    fin = eng.run_final(seeded_start(t, 0, jit_x=0.3), 0.0, eng.dt, int(600 / eng.dt), jax.random.PRNGKey(0), None, 0)
    r = analyse(eng, t, fin, 0)
    ev = np.linalg.eigvals(np.array(eng.jac_flat(fin, 1e4)))
    zero = (np.abs(ev) < 1e-7).sum(); nz = ev[np.abs(ev) > 1e-7]
    out[kind] = dict(d_tmpl=r['d_tmpl'], min_orbit_maxbel=r['min_orbit_maxbel'], max_belief_min=r['min_maxbel'], orbit_complete=r['orbit_complete'], type_ok=r['type_ok'], max_re_nonzero=float(nz.real.max()), n_unstable=int((ev.real > 1e-6).sum()),
                     slowest_rates=sorted(nz.real)[-3:], n_neutral=int(zero), rho=eng.rho, dt=eng.dt)
    print(kind, {k: (np.round(v, 4).tolist() if isinstance(v, (float, list)) else v) for k, v in out[kind].items()})
json.dump(out, open('../data/p2_jacobian.json', 'w'), indent=1)

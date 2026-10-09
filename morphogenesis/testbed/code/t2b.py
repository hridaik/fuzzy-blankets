"""T2b crisp roles: sweep sensory precision (log pi_s) and prior precision (log pi_prior) on compact body A, relational (positional OFF),
seeded start (jitter 0.3), 6 draws per cell of the grid."""
import sys, json; sys.path.insert(0,'.')
from par import run_jobs
def job(ls, lp, k):
    from asm import Params, np, make_engine, analyse, make_body, auto_dt, seeded_start, jax
    ps = float(np.exp(ls)); t = make_body('A')
    P = Params(k_mu=1.4, k_a=0.4, pi_prior=float(np.exp(lp)), pi_a_x=0.0, pi_a_c=0.0, pos_on=False, pi_x=ps, pi_c=ps, pi_l=ps, pi_ref=ps, pi_act=1.5 * ps / np.e)
    eng = make_engine(t, P); eng.dt, eng.rho = auto_dt(eng, t)
    fin = eng.run_final(seeded_start(t, k, jit_x=0.3), 0.0, eng.dt, int(400 / eng.dt), jax.random.PRNGKey(0), None, 0)
    r = analyse(eng, t, fin, 0); r.update(ls=ls, lp=lp, k=k, dt=eng.dt, rho=eng.rho); return r
if __name__ == "__main__":
    args = [(ls, lp, k) for ls in (2, 3, 4) for lp in (-2, -4, -6, -8, -10) for k in range(6)]
    res = run_jobs(job, args, workers=8, label='t2b'); json.dump(res, open('../data/t2b_results.json', 'w'))
    import numpy as np
    print('ls lp | success/6 | median d | min over draws of min orbit belief | #(min orbit belief>0.95) | dt')
    for ls in (2, 3, 4):
        for lp in (-2, -4, -6, -8, -10):
            r = [x for x in res if x['ls'] == ls and x['lp'] == lp]
            print(ls, lp, sum(x['success'] for x in r), round(float(np.median([x['d_tmpl'] for x in r])), 3), round(min(x['min_orbit_maxbel'] for x in r), 3), sum(x['min_orbit_maxbel'] > 0.95 for x in r), round(r[0]['dt'], 4))

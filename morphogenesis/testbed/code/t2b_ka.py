"""T2b companion: same sweep for body B (K=1) so that the operating point can be chosen for both plans."""
import sys, json; sys.path.insert(0,'.')
from par import run_jobs
def job(ls, lp, k, ka=0.4, kind='B'):
    from asm import Params, np, make_engine, analyse, make_body, auto_dt, seeded_start, jax
    ps = float(np.exp(ls)); t = make_body(kind)
    P = Params(k_mu=1.4, k_a=ka, pi_prior=float(np.exp(lp)), pi_a_x=0.0, pi_a_c=0.0, pos_on=False, pi_x=ps, pi_c=ps, pi_l=ps, pi_ref=ps, pi_act=1.5 * ps / np.e)
    eng = make_engine(t, P); eng.dt, eng.rho = auto_dt(eng, t)
    fin = eng.run_final(seeded_start(t, k, jit_x=0.3), 0.0, eng.dt, int(400 / eng.dt), jax.random.PRNGKey(0), None, 0)
    r = analyse(eng, t, fin, 0); r.update(ls=ls, lp=lp, k=k, dt=eng.dt, kind=kind, ka=ka); return r
if __name__ == "__main__":
    args = [(ls, lp, k, 1.2, kd) for kd in ('A', 'B') for ls in (2, 3) for lp in (-8, -10) for k in range(6)]
    res = run_jobs(job, args, workers=8, label='t2bB'); json.dump(res, open('../data/t2b_ka1.2_results.json', 'w'))
    import numpy as np
    for kd in ('A', 'B'):
      for ls in (2, 3):
        for lp in (-8, -10):
            r = [x for x in res if x['ls'] == ls and x['lp'] == lp and x['kind'] == kd]
            print('ka1.2 '+kd, ls, lp, 'success', sum(x['success'] for x in r), '/6 median d', round(float(np.median([x['d_tmpl'] for x in r])), 3), 'min orbit belief', round(min(x['min_orbit_maxbel'] for x in r), 3))

"""T2a: assembly with the positional channel OFF. 50 draws per condition; success = type-constrained permutation- and rigid-invariant
distance to the template < 0.4, shape stationary, orbit-complete (see asm.py)."""
import sys, json; sys.path.insert(0,'.')
from par import run_jobs

def job(cond, k):
    from asm import (tb_params, Params, np, make_engine, analyse, vanilla8, make_body, multiscale, auto_dt, seeded_start, jax, jnp, type_vector, cell_types, TAU_ASM)
    if cond.startswith('v8'):
        t = vanilla8(); base = dict(k_mu=1.4, k_a=1.2, pos_on=False, pi_a_x=0.0)
        if cond == 'v8_off': P = Params(**base); x0r = 0.0
        elif cond == 'v8_F1_disperse': P = Params(**base); x0r = 3.0
        elif cond == 'v8_F2_disperse_multiscale': t = multiscale(t, (1.0, 0.25)); P = Params(**base); x0r = 3.0
        elif cond == 'v8_pos_on_control': P = Params(k_mu=1.4, k_a=1.2); x0r = 0.0
        eng = make_engine(t, P); eng.dt = 0.01 if 'multiscale' in cond else 0.02
        n = 8; MU0 = np.random.default_rng(k).standard_normal((n, n)) / 8; st = eng.init_from_mu(MU0)
        if x0r > 0:
            rr = np.random.default_rng(10000 + k); r = x0r * np.sqrt(rr.uniform(size=n)); a = rr.uniform(0, 2 * np.pi, n)
            st = (jnp.asarray(np.stack([r * np.cos(a), r * np.sin(a)], 1)),) + tuple(st[1:])
        fin = eng.run_final(st, 0.0, eng.dt, int(600 / eng.dt), jax.random.PRNGKey(0), None, 0)
        ref = t if cond != 'v8_F2_disperse_multiscale' else vanilla8()
        res = analyse(eng, t, fin, 0, cell_types(vanilla8().Cs[0]))
    else:
        t = make_body('A'); P = tb_params()
        eng = make_engine(t, P); eng.dt, eng.rho = auto_dt(eng, t)
        n = 24
        if cond == 'A24_off_nearuniform':
            st = eng.init_from_mu(np.random.default_rng(k).standard_normal((n, n)) / 8)
        elif cond.startswith('A24_seeded'):
            jx = {'A24_seeded_j0.3': 0.3, 'A24_seeded_j0.6': 0.6}[cond]; st = seeded_start(t, k, jit_x=jx)
        fin = eng.run_final(st, 0.0, eng.dt, int(400 / eng.dt), jax.random.PRNGKey(0), None, 0)
        res = analyse(eng, t, fin, 0)
    res['cond'] = cond; res['k'] = k
    return res

if __name__ == "__main__":
    conds = ['v8_pos_on_control', 'v8_off', 'v8_F1_disperse', 'v8_F2_disperse_multiscale', 'A24_off_nearuniform', 'A24_seeded_j0.3', 'A24_seeded_j0.6']
    args = [(c, k) for c in conds for k in range(50)]
    res = run_jobs(job, args, workers=8, label='t2a')
    json.dump(res, open('../data/t2a_results.json', 'w'))
    for c in conds:
        r = [x for x in res if x['cond'] == c]
        print(c, 'success', sum(x['success'] for x in r), '/', len(r), 'median d', round(float(np.median([x['d_tmpl'] for x in r])), 3) if (np:=__import__('numpy')) else '',
              'orbit-complete', sum(x['orbit_complete'] for x in r), 'median |cs|', round(float(np.median([x['centroid_speed'] for x in r])), 4), 'median |rot|', round(float(np.median(np.abs([x['rot_rate'] for x in r]))), 3))

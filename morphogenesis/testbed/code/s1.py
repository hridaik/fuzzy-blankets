"""S1 plasticity operating point. Settings: log pi_prior x sigma_mu. Relational chiral body, log pi_s = 2, k_mu 1.4, k_a 0.4."""
import sys, json; sys.path.insert(0, '.')
from par import run_jobs

def mkP(lp, smu, sig=0.0, ps=2.0):
    import os
    from asm import tb_params, np
    return tb_params(nat_grad=bool(os.environ.get('S1_NG')), pi_prior=float(np.exp(lp)), sig_x=sig, sig_c=sig, sig_mu=smu, **({} if ps == 2.0 else dict(pi_x=float(np.exp(ps)), pi_c=float(np.exp(ps)), pi_l=float(np.exp(ps)), pi_ref=float(np.exp(ps)), pi_act=1.5 * float(np.exp(ps)) / np.e)))

def forms_job(lp, smu, k, mirror, T=400.0, ls=2.0):
    """(a),(b): deterministic seeded start of L or R (sigma_mu irrelevant to the deterministic fixed point; kept 0 here)"""
    from asm import np, jax, make_engine, auto_dt, analyse
    import chiral as CH
    t = __import__('asm').make_body('chiral'); eng = make_engine(t, mkP(lp, 0.0, ps=ls)); eng.dt, eng.rho = auto_dt(eng, t, safety=0.5)
    fin = eng.run_final(CH.start(t, k, mirror), 0.0, eng.dt, int(T / eng.dt), jax.random.PRNGKey(0), None, 0)
    lab, dL, dR = CH.classify(t, np.array(fin[0]), np.array(fin[1])); r = analyse(eng, t, fin, 0)
    want = 'R' if mirror else 'L'
    return dict(lp=lp, ls=ls, dt=eng.dt, k=k, start=want, label=lab, ok=bool(lab == want and r['orbit_complete'] and r['shape_speed'] < 1e-3), min_orbit_maxbel=r['min_orbit_maxbel'], d=min(dL, dR), shape_speed=r['shape_speed'])

def rate_job(lp, ps=2.0, T=400.0, safety=0.5):
    """(c) slowest non-neutral belief rate at converged L (deterministic)"""
    from asm import np, jax, jnp, make_engine, auto_dt
    import chiral as CH
    t = __import__('asm').make_body('chiral'); P = mkP(lp, 0.0, ps=ps); eng = make_engine(t, P); eng.dt, eng.rho = auto_dt(eng, t, safety=safety)
    fin = eng.run_final(CH.start(t, 0, False), 0.0, eng.dt, int(T / eng.dt), jax.random.PRNGKey(0), None, 0)
    r = jac_rates(eng, fin, P); r.update(lp=lp, ls=ps, dt=eng.dt); return r

def jac_rates(eng, fin, P):
    from asm import np, jnp
    n, nc = eng.n, eng.nc
    J = np.array(eng.jac_flat(fin, 1e4)); m = n * (2 + nc + n); J = J[:m, :m]       # drop zeta block (K=1)
    ev = np.linalg.eigvals(J)
    shift = -P.k_mu * P.pi_prior
    keep = ev[(np.abs(ev) > 1e-8) & (np.abs(ev - shift) > 1e-8 * max(1, abs(shift)) + 1e-9)]   # drop 3 rigid zero modes and the n decoupled logit-mean modes
    r = keep.real
    stable = np.sort(r[r < 0])
    return dict(slowest_nonneutral=float(stable[-1]) if len(stable) else None, n_unstable=int((r > 1e-9).sum()), max_re=float(r.max()), n_dropped=int(len(ev) - len(keep)),
                belief_mode_slowest5=[float(x) for x in stable[-5:]], rho=float(np.abs(ev).max()))

def switch_job(lp, smu, k, T=3000.0, sig=0.02, tag=''):
    """(d) spontaneous L<->R switching / tearing at operating noise: long noisy run from L (k even) or R (k odd), classified every 20 time units"""
    from asm import np, jax, jnp, make_engine, auto_dt, analyse
    import chiral as CH
    t = __import__('asm').make_body('chiral'); P = mkP(lp, smu, sig); eng = make_engine(t, P); eng.dt, eng.rho = auto_dt(make_engine(t, mkP(lp, 0.0)), t)
    per = int(round(20.0 / eng.dt)); dt = 20.0 / per
    mirror = bool(k % 2); st = CH.start(t, k // 2, mirror)
    fin, tr = eng.run(st, 0.0, dt, per * int(T / 20), jax.random.PRNGKey(900 + k), None, 0, save_every=per)
    X = np.array(tr[0]); C = np.array(tr[1]); labs = [CH.classify(t, X[j], C[j])[0] for j in range(0, len(X))]
    start = 'R' if mirror else 'L'
    flips = sum(1 for a, b in zip(labs[:-1], labs[1:]) if a in 'LR' and b in 'LR' and a != b)
    tear = sum(1 for l in labs if l == 'defect')
    return dict(lp=lp, smu=smu, k=k, start=start, T=T, n_frames=len(labs), n_defect_frames=tear, n_LR_flips=flips, frac_in_start=float(np.mean([l == start for l in labs])), final=labs[-1])

import os
LPS = (-2, -4, -6, -7, -8) if os.environ.get('S1_NG') else (-6, -7, -8)
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == 'forms':
        args = [(lp, 0.0, k, m) for lp in LPS for k in range(8) for m in (False, True)]
        res = run_jobs(forms_job, args, workers=8, label='s1forms'); json.dump(res, open('../data/s1_forms%s.json' % ('_ng' if os.environ.get('S1_NG') else ''), 'w'))
        for lp in LPS:
            r = [x for x in res if x['lp'] == lp]; print('lp', lp, 'success', sum(x['ok'] for x in r), '/16 min orbit belief', round(min(x['min_orbit_maxbel'] for x in r), 3), 'median', round(float(sorted(x['min_orbit_maxbel'] for x in r)[8]), 3))
    elif mode == 'rates':
        res = run_jobs(rate_job, [(lp,) for lp in LPS], workers=4, label='s1rates'); json.dump(res, open('../data/s1_rates%s.json' % ('_ng' if os.environ.get('S1_NG') else ''), 'w'))
        for lp, r in zip(LPS, res): print('lp', lp, r)
    elif mode == 'switch':
        smus = [float(x) for x in sys.argv[2].split(',')]
        args = [(lp, sm, k) for lp in (-8,) for sm in smus for k in range(8)]
        res = run_jobs(switch_job, args, workers=8, label='s1switch'); json.dump(res, open('../data/s1_switch_%s.json' % sys.argv[2].replace(',', '_'), 'w'))
        for lp in (-8,):
            for sm in smus:
                r = [x for x in res if x['lp'] == lp and x['smu'] == sm]; print('lp', lp, 'smu', sm, 'flips', sum(x['n_LR_flips'] for x in r), 'defect frames', sum(x['n_defect_frames'] for x in r), '/', sum(x['n_frames'] for x in r), 'frac in start', round(float(sum(x['frac_in_start'] for x in r) / len(r)), 3))

    if mode == 'grid':
        LS = (3.0, 4.0, 5.0); LP = (-5, -6, -7, -8)
        args = [(lp, 0.0, k, m, 400.0, ls) for ls in LS for lp in LP for k in range(8) for m in (False, True)]
        res = run_jobs(forms_job, args, workers=8, label='s1grid'); json.dump(res, open('../data/s1_grid_forms.json', 'w'))
        rr = run_jobs(rate_job, [(lp, ls) for ls in LS for lp in LP], workers=8, label='s1gridrates'); json.dump(rr, open('../data/s1_grid_rates.json', 'w'))
        for ls in LS:
            for lp in LP:
                r = [x for x in res if x['ls'] == ls and x['lp'] == lp]; q = [x for x in rr if x['ls'] == ls and x['lp'] == lp][0]
                print('ls', ls, 'lp', lp, 'success', sum(x['ok'] for x in r), '/16 minorbit', round(min(x['min_orbit_maxbel'] for x in r), 3), 'rate', q['slowest_nonneutral'], 'n_unst', q['n_unstable'], 'dt', round(r[0]['dt'], 4))

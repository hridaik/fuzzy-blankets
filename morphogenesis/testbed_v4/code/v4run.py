import sys, json, time
from lib4 import *
from v4cal import onset
TAU = tauJ(); MED = median_dish(); G = MED['g']
def job_ud(gamma, centre, dm, kg, guess, state='a', variant='phi04'):
    ud, hist, modes = onset(variant, kg, state, centre, dm / G, gamma, TAU, guess)
    return dict(gamma=gamma, centre=centre, dm=dm, kg=kg, u_d=ud, hist=hist, modes=modes)

def job_window(centre, dm, variant='phi04', state='a'):
    from v4 import job_damage
    d = median_dish(); gam = gamma0(); b = bisect_switch(d, variant, state, centre, dm / G)
    ud, hist, modes = onset(variant, KG_MED, state, centre, dm / G, gam, TAU, (b['thr'] or 1.0) * 2.5)
    mc = {}; frs = []
    if ud:
        for s in range(10):
            r = job_damage(variant, KG_MED, state, centre, dm / G, 1.5 * ud, s, gam, TAU); frs.append(r['fail'])
            if r['fail']: mc[r['mode']] = mc.get(r['mode'], 0) + 1
    return dict(centre=centre, dm=dm, dur=dm / G, thr=b['thr'], n_lit=b['n_lit'], u_d=ud, hist=hist, onset_modes=modes, mode_counts=mc, frac_fail_1p5=float(np.mean(frs)) if frs else None)
if __name__ == "__main__":
    from par4 import run_jobs; mode = sys.argv[1]; t0 = time.time()
    if mode == 'grid':
        gs = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 9.0]
        res = run_jobs(job_ud, [(g_, 'middle', 16, KG_MED, 4.0 / g_) for g_ in gs], label='gamma-grid'); json.dump(res, open('../data/v4_gamma_grid.json', 'w'))
        for r in res: print(r['gamma'], r['u_d'], r['gamma'] * r['u_d'] if r['u_d'] else None, r['hist'])
    print('wall', time.time() - t0)
    if mode == 'verify':
        g0 = gamma0(); res = run_jobs(job_ud, [(g0, 'middle', 16, KG_MED, 2.9)], workers=1, label='verify'); json.dump(res, open('../data/v4_gamma_verify.json', 'w')); print(res[0]['u_d'], res[0]['hist'])
    if mode == 'window':
        from v4 import job_damage
        res = run_jobs(job_window, [(c, dm) for c in ('middle', 'tail_end') for dm in (4, 8, 16, 32)], label='window'); json.dump(res, open('../data/v4_window.json', 'w'))
        for r in res: print(r['centre'], r['dm'], 'thr', r['thr'], 'u_d', r['u_d'], 'ratio', None if not r['u_d'] else r['u_d'] / r['thr'], 'modes', r['mode_counts'])

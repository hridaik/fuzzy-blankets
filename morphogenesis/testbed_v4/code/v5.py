"""V5 adaptivity gap. Per dish (population draw): exact switch threshold on the grid {4 centres} x {4,8,16,32}/g_med (a->b, primary variant, frozen scoring);
damage onset u_d = chi(kappa_g, centre, dur) / (gamma_0 * gamma_factor_dish)  [chi = gamma*u_d is the exact onset in gamma-units, computed with the exact procedure on a kappa_g grid, interpolated in log kappa_g;
validated against exact per-dish onset on held-out dishes]. Declared deviation: damage onset for the 40 dishes is not searched per dish."""
import sys, json, time
from lib4 import *
from v4cal import onset
CENTRES4 = ['middle', 'limb_side', 'head_end', 'tail_end']; DM = [4, 8, 16, 32]; G_MED = 4 * R_ * KG_MED
LEVELS = [dict(kg=KG_RANGE, gf=GF_RANGE), dict(kg=(1.2, 5.0), gf=(0.5, 2.0)), dict(kg=(1.1, 7.0), gf=(1 / 3, 3.0))]     # widening 1 = as specified; widening 2 declared before computing
def dishes(level, n=40, base=100): return [sample_dish(base + i, LEVELS[level]['kg'], LEVELS[level]['gf']) for i in range(n)]
def job_thr(level, i, centre, dm):
    d = dishes(level)[i]; r = bisect_switch(d, 'phi04', 'a', centre, dm / G_MED); r.update(dish=i, level=level, kg=d['kappa_g'], gf=d['gamma_factor'], g=d['g'], dm=dm); r.pop('cell_cross', None); return r
def job_chi(kg, centre, dm, guess=3.7):
    gam = gamma0(); ud, hist, modes = onset('phi04', kg, 'a', centre, dm / G_MED, gam, tauJ(), guess / gam)
    return dict(kg=kg, centre=centre, dm=dm, u_d=ud, chi=(None if ud is None else ud * gam), hist=hist)
def job_exact_dish(level, i, centre, dm, guess):
    d = dishes(level)[i]; gam = gamma0() * d['gamma_factor']; ud, hist, modes = onset('phi04', d['kappa_g'], 'a', centre, dm / G_MED, gam, tauJ(), guess)
    return dict(level=level, dish=i, kg=d['kappa_g'], gf=d['gamma_factor'], centre=centre, dm=dm, u_d_exact=ud, hist=hist)
def chi_table(rows):
    """returns f(kg, centre, dm) log-linear interpolation of chi in log kappa_g"""
    T = {}
    for r in rows: T.setdefault((r['centre'], r['dm']), []).append((np.log(r['kg']), np.log(r['chi'])))
    def f(kg, centre, dm):
        p = sorted(T[(centre, dm)]); x = np.array([a for a, b in p]); y = np.array([b for a, b in p]); return float(np.exp(np.interp(np.log(kg), x, y)))
    return f
def gap(thr_rows, chi, level, centres=None):
    """thr_rows: results of job_thr (switch thresholds); builds window per dish & grid point and evaluates policies"""
    gam = gamma0(); ds = dishes(level); n = len(ds); W = {}
    for r in thr_rows:
        r.setdefault('dm', int(round(r['dur'] * G_MED)))
        d = ds[r['dish']]; ud = chi(d['kappa_g'], r['centre'], r['dm']) / (gam * d['gamma_factor']); W[(r['dish'], r['centre'], r['dm'])] = (r['thr'], ud, r['dose'], r['n_lit'])
    # (a) best fixed policy: (centre, dm, amp) maximising fraction of dishes with thr <= amp < u_d
    centres = centres or sorted({r['centre'] for r in thr_rows}, key=CENTRES4.index)
    best = (0, None); cand_amps = sorted({v[0] * f for v in W.values() for f in (1.0001,)} | {v[1] * 0.9999 for v in W.values()})
    for c in centres:
        for dm in DM:
            for a in cand_amps:
                frac = np.mean([(W[(i, c, dm)][0] is not None and W[(i, c, dm)][0] <= a < W[(i, c, dm)][1]) for i in range(n)])
                if frac > best[0]: best = (frac, (c, dm, float(a)))
    # (b) per-dish oracle
    orc = []; doses = []
    for i in range(n):
        ok = [(W[(i, c, dm)][2], c, dm) for c in centres for dm in DM if W[(i, c, dm)][0] < W[(i, c, dm)][1]]
        orc.append(bool(ok)); doses.append(min(ok)[0] if ok else None)
    ds_ = np.array([x for x in doses if x is not None])
    # per-condition window ratios and threshold spread
    spread = {f'{c}_{dm}': dict(thr_min=float(min(W[(i, c, dm)][0] for i in range(n))), thr_max=float(max(W[(i, c, dm)][0] for i in range(n))), ratio=float(max(W[(i, c, dm)][0] for i in range(n)) / min(W[(i, c, dm)][0] for i in range(n))),
                                 frac_window=float(np.mean([W[(i, c, dm)][0] < W[(i, c, dm)][1] for i in range(n)]))) for c in centres for dm in DM}
    return dict(centres=centres, best_fixed_frac=float(best[0]), best_fixed_policy=best[1], oracle_frac=float(np.mean(orc)), oracle_doses=doses, dose_spread_ratio=float(ds_.max() / ds_.min()) if len(ds_) else None, dose_cv=float(ds_.std() / ds_.mean()) if len(ds_) else None,
                dose_min=float(ds_.min()) if len(ds_) else None, dose_median=float(np.median(ds_)) if len(ds_) else None, dose_max=float(ds_.max()) if len(ds_) else None, per_condition=spread, W={f'{k[0]}|{k[1]}|{k[2]}': v for k, v in W.items()})
if __name__ == "__main__":
    from par4 import run_jobs; mode = sys.argv[1]; level = int(sys.argv[2]) if len(sys.argv) > 2 else 0; t0 = time.time()
    if mode in ('thr', 'thr_mid'):
        cs = CENTRES4 if mode == 'thr' else ['middle']
        res = run_jobs(job_thr, [(level, i, c, dm) for i in range(40) for c in cs for dm in DM], label=f'V5thr{level}'); json.dump(res, open(f'../data/v5_thr_L{level}.json', 'w'))
    elif mode in ('chi', 'chi_mid'):
        kgs = {0: [1.5, 2.0, KG_MED, 3.2, 4.0], 1: [1.2, 1.5, 2.0, KG_MED, 3.2, 4.0, 5.0], 2: [1.1, 1.5, 2.0, KG_MED, 3.2, 4.0, 5.5, 7.0]}[level]; cs = CENTRES4 if mode == 'chi' else ['middle']
        res = run_jobs(job_chi, [(k, c, dm) for k in kgs for c in cs for dm in DM], label='V5chi'); json.dump(res, open(f'../data/v5_chi_L{level}.json', 'w'))
    elif mode == 'validate':
        ds = dishes(0); chi = chi_table(json.load(open('../data/v5_chi_L0.json'))); gam = gamma0()
        order = sorted(range(40), key=lambda i: ds[i]['gamma_factor']); kord = sorted(range(40), key=lambda i: ds[i]['kappa_g']); rng = np.random.default_rng(5); pick = sorted({order[0], order[-1], kord[0], kord[-1]} | set(int(x) for x in rng.choice(40, 6, replace=False)))[:8]
        jobs = [(0, i, 'middle', dm, chi(ds[i]['kappa_g'], 'middle', dm) / (gam * ds[i]['gamma_factor'])) for i in pick for dm in (8, 16)]
        res = run_jobs(job_exact_dish, jobs, label='V5val')
        for r, j in zip(res, jobs): r['u_d_pred'] = j[4]; r['rel_err'] = None if r['u_d_exact'] is None else r['u_d_exact'] / j[4] - 1
        json.dump(res, open('../data/v5_validate.json', 'w')); print([(r['dish'], r['dm'], round(r['kg'], 2), round(r['gf'], 2), round(r['u_d_pred'], 3), None if r['u_d_exact'] is None else round(r['u_d_exact'], 3), None if r['rel_err'] is None else round(r['rel_err'], 3)) for r in res])
    elif mode == 'gap':
        thr = json.load(open(f'../data/v5_thr_L{level}.json')); chi = chi_table(json.load(open(f'../data/v5_chi_L{level}.json'))); out = gap(thr, chi, level); json.dump(out, open(f'../data/v5_gap_L{level}.json', 'w'), indent=1)
        print({k: v for k, v in out.items() if k not in ('W', 'per_condition', 'oracle_doses')})
        for k, v in out['per_condition'].items(): print(k, {a: round(b, 3) for a, b in v.items()})
    print('wall', time.time() - t0)

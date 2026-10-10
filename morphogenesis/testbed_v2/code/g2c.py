"""G2(e) durability: 10 seeds x 20,000 tu per form with full noise incl. sigma_h = 1.0."""
import sys, json, time; sys.path.insert(0,'.')
SIG_H = 1.0
def dur_job(form, seed, T=20000.0, chunk=500.0):
    from world2 import new_adult2, describe2, np
    w = new_adult2(form, k=seed, capacity=24, noise=0.02, sig_h=SIG_H, key=100 + seed); w.time = 0.0; w.step_count = 0
    log = []; switched = None; t_bad = None; lstd = []
    near = np.isin(w.perm0, np.where(np.array(__import__('g2cfg').mean_field(w.tm, __import__('g2cfg').FULL)['Gmorph_per_place']) >= 0.5)[0])
    for c in range(int(T / chunk)):
        w.run(chunk); d = describe2(w); L = w.L[near]
        log.append((c * chunk + chunk, d['shape'], round(d['dL'], 3), round(d['dR'], 3), d['orbit_ok'], round(float(w.rho()[near].mean()), 3), round(float(L.min()), 2), round(float(L.max()), 2)))
        if switched is None and d['shape'] not in (form, 'DEFECT', 'other') : switched = c * chunk + chunk
        if t_bad is None and d['shape'] != form: t_bad = c * chunk + chunk
    return dict(form=form, seed=seed, t_switch=switched, t_first_nonform=t_bad, final=log[-1], n_nonform_checkpoints=sum(1 for l in log if l[1] != form), min_rho_near=min(l[5] for l in log) if form == 'L' else None, log=log)
if __name__ == "__main__":
    from par import run_jobs
    t0 = time.time(); res = run_jobs(dur_job, [(f, s) for f in 'LR' for s in range(10)], workers=7, label='g2dur'); json.dump(res, open('../data/g2_durability.json', 'w'))
    for x in res: print(x['form'], x['seed'], 'switch', x['t_switch'], 'nonform', x['t_first_nonform'], x['n_nonform_checkpoints'], x['final'])
    print('wall', time.time() - t0)

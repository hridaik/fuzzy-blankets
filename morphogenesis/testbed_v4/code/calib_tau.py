"""Calibrate and freeze the ORGANISM INTACT neighbour-preservation threshold tau_J.
natural runs: pooled 10-tu frames (V2d primary variant + 16 population dishes x 2 states x 3000 tu, noise on);
clean switch runs: per-run MINIMUM of the mean Jaccard over the run (deterministic, gamma = 0, at 1x and 2x threshold, primary variant, all dishes/conditions).
tau_J = min( P1(natural pooled), P1(clean per-run minima) ). Frozen into data/intact_threshold.json."""
import sys, json, time
from lib4 import *
def job_pop(seed, state, T=6000.0, chunk=1.0):
    d = sample_dish(seed); e = get_engine(d, 'phi04', noise=True, gamma_on=False); arr, perm = settled(d, 'phi04', state); st = tuple(jnp.array(a) for a in arr); key = jax.random.PRNGKey(31_000 + seed + (0 if state == 'a' else 500))
    st = run_plain(e, st, 0.0, 100.0, key); step = int(100 / DT); t = 100.0; base = nbr_matrix(np.array(st[0])); k = int(round(chunk / DT)); jac = []; sw = False
    for c in range(int(T / chunk)):
        st = run_plain(e, st, t, chunk, key, step0=step); t += chunk; step += k; f = frame_stats(np.array(st[0]), np.array(st[2]), np.array(st[3]), base); jac.append(f['jac'])
        if (f['mean_rho'] < 0.5) == (state == 'a'): sw = True
    return dict(seed=seed, state=state, kg=d['kappa_g'], jac=jac, switched=sw)
if __name__ == "__main__":
    from par4 import run_jobs; t0 = time.time()
    pop = run_jobs(job_pop, [(s, st) for s in range(16) for st in 'ab'], label='pop'); json.dump(pop, open('../data/natural_pop.json', 'w'))
    W = 330   # window = longest test window (light + 300 tu); statistic = min Jaccard within a window (1-tu frames)
    nat = np.array([min(r['jac'][w:w + W]) for r in pop for w in range(0, len(r['jac']) - W + 1, W)])
    pre = json.load(open('../data/v3_prelim.json')); clean = []
    for r in pre:
        if r['variant'] != 'phi04' or r['thr'] is None: continue
        clean += [r['min_jac'], r['min_jac_2x']]
    clean = np.array(clean); pn = float(np.percentile(nat, 1)); pc = float(np.percentile(clean, 1)); tau = min(pn, pc)
    out = dict(tau_J=tau, statistic='min over a 330-tu window of the mean neighbour Jaccard; P1 over windows', P1_natural=pn, P1_clean=pc, n_natural_windows=int(len(nat)), n_clean_runs=int(len(clean)), natural_min=float(nat.min()), natural_median=float(np.median(nat)),
               clean_min=float(clean.min()), n_pop_switched=int(sum(r['switched'] for r in pop)))
    json.dump(out, open('../data/intact_threshold.json', 'w'), indent=1); print(out); print('wall', time.time() - t0)

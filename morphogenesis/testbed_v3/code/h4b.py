"""H4b: attenuated self-sensing for PLACE inference (perception ignores the self term of s^lam and pi_c; action unchanged). Bounded run."""
import sys, json, time; sys.path.insert(0, '.')
from world3 import *
CFG = dict(place_self_attenuation=True)
def job_seeded(k):
    tm = make_template2(); eng = make_engine3(tm, Params3(**CFG)); eng.dt = DT; st, perm = seeded_start3(tm, k, 'a'); fin = run_plain(eng, st, 0, 600, jax.random.PRNGKey(0)); s = summarize3(eng, fin)
    s['ok'] = bool(s['label'] == 'L' and s['orbit_complete'] and s['min_orbit_bel'] >= 0.9); return s
def job_dur(seed, T=20000.0, chunk=500.0):
    tm = make_template2(); eng = make_engine3(tm, Params3(sig_x=.02, sig_c=.02, sig_mu=.02, sig_h=0.4, sig_d=.02, sig_e=.02, **CFG)); eng.dt = DT; st, perm = seeded_start3(tm, seed, 'a'); key = jax.random.PRNGKey(1000 + seed); k = int(round(chunk / DT)); log = []; tdis = None
    for c in range(int(T / chunk)):
        st = run_plain(eng, st, c * chunk, chunk, key, step0=c * k); s = summarize3(eng, st); log.append((c * chunk + chunk, s['label'], round(s['dL'], 3), s['orbit_complete'], round(s['min_orbit_bel'], 3)))
        if tdis is None and not (s['label'] == 'L' and s['orbit_complete']): tdis = c * chunk + chunk
    return dict(seed=seed, t_dissolve=tdis, final=log[-1], max_dL=max(l[2] for l in log))
def job_replace(i, T=400.0):
    w = new_adult3('a', capacity=24, noise=0.0, key=i, cfg=CFG); place = int(w.perm0[i]); w.replace(i, seed=i); w.run(T); d = describe3(w)
    return dict(cell=i, place=place, type=int(w.tm.types[0][place]), after=d, repaired=bool(d['shape'] == 'L'))
if __name__ == "__main__":
    from par import run_jobs; t0 = time.time()
    r1 = run_jobs(job_seeded, [(k,) for k in range(16)], workers=8, label='h4b_seed'); json.dump(r1, open('../data/h4b_seeded.json', 'w')); print('seeded ok', sum(x['ok'] for x in r1), '/16 min orbit bel', min(x['min_orbit_bel'] for x in r1), 'max dL', max(x['dL'] for x in r1), flush=True)
    r3 = run_jobs(job_replace, [(i,) for i in range(24)], workers=8, label='h4b_rep'); json.dump(r3, open('../data/h4b_replace.json', 'w')); print('replacement repaired', sum(x['repaired'] for x in r3), '/24', flush=True)
    r2 = run_jobs(job_dur, [(s,) for s in range(3)], workers=3, label='h4b_dur'); json.dump(r2, open('../data/h4b_durability.json', 'w'))
    for x in r2: print('dur', x['seed'], x['t_dissolve'], x['final'], x['max_dL'])
    print('wall', time.time() - t0)

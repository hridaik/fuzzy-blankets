"""H1: structure re-check at the v2 G1 point (memory module present but structure-independent). 16 seeded starts (deterministic) + 3 seeds x 20,000 tu (noise)."""
import sys, json, time; sys.path.insert(0, '.')
from an3 import *
DT = 0.0125
def dur_job(seed, T=20000.0, chunk=500.0, sig_h=0.5):
    from an3 import np, jax, make_template2, make_engine3, Params3, seeded_start3, run_plain, summarize3
    tm = make_template2(); eng = make_engine3(tm, Params3(sig_x=.02, sig_c=.02, sig_mu=.02, sig_h=sig_h, sig_d=.02, sig_e=.02)); eng.dt = DT
    st, perm = seeded_start3(tm, seed, 'a'); key = jax.random.PRNGKey(1000 + seed); k = int(round(chunk / DT)); log = []; tdis = None
    for c in range(int(T / chunk)):
        st = run_plain(eng, st, c * chunk, chunk, key, step0=c * k); s = summarize3(eng, st)
        log.append((c * chunk + chunk, s['label'], round(s['dL'], 3), s['orbit_complete'], round(s['min_orbit_bel'], 3), round(s['mean_rho'], 3)))
        if tdis is None and not (s['label'] == 'L' and s['orbit_complete']): tdis = c * chunk + chunk
    return dict(seed=seed, t_dissolve=tdis, final=log[-1], max_dL=max(l[2] for l in log), log=log)
if __name__ == "__main__":
    tm = make_template2(); eng = make_engine3(tm, Params3()); eng.dt = DT; rows = []
    for k in range(16):
        st, perm = seeded_start3(tm, k, 'a'); fin = run_plain(eng, st, 0, 600, jax.random.PRNGKey(0)); s = summarize3(eng, fin); s['ok'] = bool(s['label'] == 'L' and s['orbit_complete'] and s['min_orbit_bel'] >= 0.9); rows.append(s)
    print('seeded complete', sum(r['ok'] for r in rows), '/16  min orbit belief', min(r['min_orbit_bel'] for r in rows), 'max dL', max(r['dL'] for r in rows), flush=True)
    json.dump(rows, open('../data/h1_seeded.json', 'w'))
    from par import run_jobs
    t0 = time.time(); res = run_jobs(dur_job, [(s,) for s in range(3)], workers=3, label='h1dur'); json.dump(res, open('../data/h1_durability.json', 'w'))
    for x in res: print(x['seed'], x['t_dissolve'], x['final'], x['max_dL'])
    print('wall', time.time() - t0)

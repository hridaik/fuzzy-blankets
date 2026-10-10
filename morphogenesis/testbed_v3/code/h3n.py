"""H3 noise: success at 1.2x threshold (10 seeds) for the 3 most / 3 least effective centres per (state, duration in {4/g, 16/g}); matched-dose wrong-location; sham."""
import sys, json, time; sys.path.insert(0, '.')
from h3 import *
SIG_H = 0.4; NZ = 0.02
def job_noise(state, dur, centre, amp, seed, lit_override_centre=None):
    eng, st0, perm, tm = get(state, NZ, SIG_H); lit = None
    if lit_override_centre is not None:                                   # wrong location: same number of lit cells, nearest to the far centre
        n_lit = int(lit_set(tm, perm, centre).sum()); X = tm.Xs[:, perm].T; d = np.linalg.norm(X - tm.Xs[:, lit_override_centre][None], axis=1); lit = np.zeros(24, bool); lit[np.argsort(d)[:n_lit]] = True
    r = trial(state, centre, dur, amp, noise=NZ, sig_h=SIG_H, seed=seed, burn=100.0, lit_override=lit); r['wrong_location'] = lit_override_centre; r['seed'] = seed; return r
def job_sham(state, dur, seed):
    eng, st0, perm, tm = get(state, NZ, SIG_H); n = 24; zero = zero_ctl(n); key = jax.random.PRNGKey(seed); st = run_plain(eng, st0, 0.0, 100.0, key); step0 = int(round(100.0 / DT)); k = int(round((dur + REL) / DT))
    a = eng.run_ctl(st, 100.0, DT, k, key, zero, 100.0, 100.0 + dur, 1.0, step0=step0); uM = np.zeros((n, 2)); b = eng.run_ctl(st, 100.0, DT, k, key, zero[:3] + (jnp.array(uM),) + zero[4:], 100.0, 100.0 + dur, 1.0, step0=step0)
    return dict(state=state, dur=dur, seed=seed, max_diff=max(float(jnp.abs(x - y).max()) for x, y in zip(a, b)))
if __name__ == "__main__":
    from par import run_jobs; t0 = time.time(); B = json.load(open('../data/h3_bisect.json')); args = []; sel = {}
    for st in 'ab':
        for d in DURS[1:]:
            cs = sorted([x for x in B if x['state'] == st and abs(x['dur'] - d) < 1e-6 and x['centre'] >= 0 and x['thr'] is not None], key=lambda x: x['dose']); best = cs[:3]; worst = cs[-3:]; sel[f'{st}_{d:.3f}'] = dict(best=[x['centre'] for x in best], worst=[x['centre'] for x in worst])
            tm = make_template2(); perm = __import__('world3').settled3(st, 0)[1]
            for grp, name in ((best, 'best'), (worst, 'worst')):
                for x in grp:
                    for s in range(10): args.append((st, d, x['centre'], 1.2 * x['thr'], s, None))
            for x in best:                                                                   # wrong location: the farthest centre (same lit-cell count, same amp, same duration)
                far = int(np.argmax(np.linalg.norm(tm.Xs - tm.Xs[:, [x['centre']]], axis=0)))
                for s in range(10): args.append((st, d, x['centre'], 1.2 * x['thr'], s, far))
    res = run_jobs(job_noise, args, workers=8, label='H3noise'); json.dump(dict(sel=sel, rows=res), open('../data/h3_noise.json', 'w'))
    sh = run_jobs(job_sham, [(st, d, s) for st in 'ab' for d in DURS[1:] for s in range(3)], workers=8, label='H3sham'); json.dump(sh, open('../data/h3_sham.json', 'w')); print('sham max diff', max(x['max_diff'] for x in sh))
    print('wall', time.time() - t0)

"""A3: true minimal switching dose per held-out dish and protocol (deterministic noise-free bisection from the dish state at the first-action time;
noisy 50 % threshold from 10 CRN keys). Constants: FROZEN_AUDIT_CONFIG.json. Usage: python regret.py [seed ...] (default all 60 dishes; resumable)."""
import sys, os, json, time, glob, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import jax
AUD = os.path.abspath(os.path.join(HERE, '..')); OUT = os.path.join(AUD, 'data', 'regret'); os.makedirs(OUT, exist_ok=True)
CFG = json.load(open(os.path.join(AUD, 'FROZEN_AUDIT_CONFIG.json')))
KEYS = CFG['regret']['noisy']['crn_keys']
def load_heldout():
    R = [json.loads(l) for l in open(os.path.join(T5, 'logs', 'heldout_summary.jsonl'))]
    by = {}
    for r in R:
        by.setdefault(r['seed'], {})[r['arm']] = r
    return by
def ep_actions(eid): return json.load(open(os.path.join(T5, 'episodes_heldout', f'ep_{eid:05d}.json')))['actions']
def to_acts(al, scale=1.0, whole=False, only_first=False):
    A = [dict(a) for a in al][:1] if only_first else [dict(a) for a in al]
    out = []
    for a in A:
        m = {'type': 'all'} if whole else a['mask']
        out.append(mk_action(a['label'], m, a['amp'] * scale, a['t'], a['dur'], a['ramp']))
    return out
def mean_rho(w): al = w.alive; return float((1 / (1 + np.exp(-w.L[al]))).mean())
def run_to(ex, s0, acts, T_end_rel):
    restore(ex, s0); T = T_end_rel - 20.0
    n = int(round(T / 0.5)); ex.run_sched(n * 0.5, acts, sham=False, obs_times=[]); return mean_rho(ex.w)
def switched(ex, s0, acts, T_end_rel, start):
    m = run_to(ex, s0, acts, T_end_rel); return (m < 0.5) if start == 'a' else (m > 0.5)
def make_noisefree(seed, s0, start):
    ex = Experiment4(start, seed=seed, noise=0.0, sig_h=0.0, private=dict(PRIV), form_seed=seed); ex.t0 = s0['time'] - 20.0; return ex
def det_threshold(ex, s0, al, start, whole=False, only_first=False, extra=100.0):
    """smallest common scale s of the protocol's amplitudes that switches (noise-free)"""
    t_end = max(a['t'] + a['dur'] for a in (al[:1] if only_first else al)) + extra
    f = lambda s: switched(ex, s0, to_acts(al, s, whole, only_first), t_end, start)
    lo, hi = None, None; s = 1.0
    if f(s):
        hi = s
        while True:
            s /= 2
            if s < 0.01: return dict(s=0.01, bracket='below'), t_end
            if f(s): hi = s
            else: lo = s; break
    else:
        lo = s
        while True:
            s *= 2
            if s > 64: return dict(s=None, bracket='none_to_64'), t_end
            if f(s): hi = s; break
            else: lo = s
    for _ in range(9):
        m = float(np.sqrt(lo * hi))
        if f(m): hi = m
        else: lo = m
    return dict(s=hi, lo=lo, bracket='ok'), t_end
def noisy_threshold(exn, s0, al, start, s_det, whole=False, only_first=False, t_end=None):
    out = []
    for k in KEYS:
        exn.w.key = jax.random.PRNGKey(k)
        f = lambda s: switched(exn, s0, to_acts(al, s, whole, only_first), t_end, start)
        lo, hi = 0.6 * s_det, 1.5 * s_det
        for _ in range(5):
            m = float(np.sqrt(lo * hi))
            if f(m): hi = m
            else: lo = m
        out.append(float(np.sqrt(lo * hi)))
    return out
def do_dish(seed):
    fp = os.path.join(OUT, f'seed_{seed}.json')
    if os.path.exists(fp): return
    t0 = time.time(); by = load_heldout()[seed]; start = state_of(seed)
    ctrl_al = ep_actions(by['ctrl']['episode']); rnd_al = ep_actions(by['random']['episode']); fix_al = ep_actions(by['fixed']['episode'])
    ex = make_dish(seed); ex.run_sched(20.0, [], sham=False, obs_times=[]); s0 = snap(ex)
    exnf = make_noisefree(seed, s0, start)
    # noisy copy of the same dish (same engine/params): reuse ex with other keys
    res = dict(seed=seed, start=start, n_pulses_ctrl=len(ctrl_al), ctrl_dose=by['ctrl']['dose'], fixed_dose=by['fixed']['dose'], whole_dose=by['whole']['dose'], whole_dm_dose=by['whole_dm']['dose'], random_dose=by['random']['dose'], mean_rho_t20=mean_rho(ex.w))
    prot = dict(ctrl_train=(ctrl_al, False, False), ctrl_single=(ctrl_al, False, True), fixed=(fix_al, False, False), whole_train=(ctrl_al, True, False), random_train=(rnd_al, False, False))
    cells = {k: [] for k in prot}
    for k, (al, wh, of) in prot.items():
        A = to_acts(al, 1.0, wh, of)
        # nominal dose per unit scale = sum amp*dur*cells (cells as logged by the server at the call time)
        cl = [a['cells'] for a in (al[:1] if of else al)]; cells[k] = cl
        d, t_end = det_threshold(exnf, s0, al, start, wh, of)
        base_dose = sum(a['amp'] * a['dur'] * (24 if wh else c) for a, c in zip((al[:1] if of else al), cl))
        d.update(base_dose=base_dose, dose_min_det=(None if d['s'] is None else d['s'] * base_dose), t_end=t_end, cells=cl)
        res['det_' + k] = d
        if k in CFG['regret']['noisy']['protocols'] or k in ('ctrl_train', 'fixed', 'whole_train'):
            if d['s'] is not None and d['bracket'] == 'ok':
                th = noisy_threshold(ex, s0, al, start, d['s'], wh, of, t_end)
                d['noisy_scale_per_key'] = th; d['noisy_scale_50'] = float(np.median(th)); d['dose_min_noisy50'] = d['noisy_scale_50'] * base_dose
                d['p_switch_at_used'] = float(np.mean(np.array(th) <= 1.0))
    # reference: whole dose-matched, used-dose relative to whole threshold
    res['wall_s'] = time.time() - t0
    json.dump(res, open(fp, 'w'), default=float)
    print('done', seed, round(res['wall_s']), flush=True)
if __name__ == '__main__':
    by = load_heldout(); seeds = sorted(s for s, v in by.items() if v['ctrl']['reason'] not in ('quota_skip', 'baseline_not_clean'))
    args = [int(a) for a in sys.argv[1:]]
    if args: seeds = args
    for s in seeds: do_dish(s)

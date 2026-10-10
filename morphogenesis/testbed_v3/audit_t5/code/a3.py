"""A3 aggregation: regret = dose used / true minimal dose, per dish and arm; summaries, bootstrap CIs (dish-clustered), calibration of the noisy thresholds vs observed success."""
import sys, os, json, glob, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regret import load_heldout, CFG
AUD = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
by = load_heldout(); rows = {}
for f in sorted(glob.glob(os.path.join(AUD, 'data', 'regret', 'seed_*.json'))):
    d = json.load(open(f)); s = d['seed']; a = by[s]; r = dict(seed=s, start=d['start'], n_pulses=d['n_pulses_ctrl'], ctrl_dose=d['ctrl_dose'], fixed_dose=d['fixed_dose'], whole_dose=d['whole_dose'], whole_dm_dose=d['whole_dm_dose'], random_dose=d['random_dose'])
    for k in ('ctrl_train', 'ctrl_single', 'fixed', 'whole_train', 'random_train'):
        x = d.get('det_' + k, {}); r['det_' + k] = x.get('dose_min_det'); r['s_det_' + k] = x.get('s'); r['noisy_' + k] = x.get('dose_min_noisy50'); r['s_noisy_' + k] = x.get('noisy_scale_50'); r['p_switch_' + k] = x.get('p_switch_at_used')
        r['base_dose_' + k] = x.get('base_dose')
    # regret per arm
    def reg(used, key, which): m = r[which + '_' + key]; return (used / m) if m else None
    for which in ('det', 'noisy'):
        r['regret_ctrl_' + which] = reg(r['ctrl_dose'], 'ctrl_train', which); r['regret_ctrl_single_' + which] = reg(r['ctrl_dose'], 'ctrl_single', which); r['regret_fixed_' + which] = reg(r['fixed_dose'], 'fixed', which)
        r['regret_whole_' + which] = reg(r['whole_dose'], 'whole_train', which); r['regret_whole_dm_' + which] = reg(r['whole_dm_dose'], 'whole_train', which); r['regret_random_' + which] = reg(r['random_dose'], 'random_train', which)
    r['success'] = {k: bool(a[k]['success']) for k in ('ctrl', 'fixed', 'whole', 'whole_dm', 'random')}
    rows[s] = r
def boot(v, n=5000, seed=12345):
    v = np.array([x for x in v if x is not None]); rng = np.random.default_rng(seed); m = [np.median(v[rng.integers(0, len(v), len(v))]) for _ in range(n)]; return float(np.median(v)), float(np.quantile(m, .025)), float(np.quantile(m, .975))
S = dict(n_dishes=len(rows))
for arm in ('ctrl', 'ctrl_single', 'fixed', 'whole', 'whole_dm', 'random'):
    for which in ('det', 'noisy'):
        v = [r['regret_' + arm + '_' + which] for r in rows.values() if r['regret_' + arm + '_' + which] is not None]
        if len(v) >= 3:
            q = np.quantile(v, [.1, .25, .5, .75, .9]); S[f'regret_{arm}_{which}'] = dict(n=len(v), median=float(q[2]), q10=float(q[0]), q25=float(q[1]), q75=float(q[3]), q90=float(q[4]), median_ci95=boot(v)[1:], geo_mean=float(np.exp(np.mean(np.log(v)))), frac_below_1=float(np.mean(np.array(v) < 1)), frac_above_2=float(np.mean(np.array(v) > 2)))
# calibration: expected success from the noisy thresholds (fraction of 10 CRN keys switching at the dose used) vs observed
cal = {}
for arm, key in (('ctrl', 'ctrl_train'), ('fixed', 'fixed'), ('whole', 'whole_train')):
    p = [r['p_switch_' + key] for r in rows.values() if r['p_switch_' + key] is not None]
    if p: cal[arm] = dict(n=len(p), mean_p_switch_at_used=float(np.mean(p)), observed_success=float(np.mean([r['success'][arm] for r in rows.values()])))
S['calibration'] = cal
# deterministic vs noisy threshold relation
rat = [r['s_noisy_ctrl_train'] / r['s_det_ctrl_train'] for r in rows.values() if r['s_noisy_ctrl_train'] and r['s_det_ctrl_train']]
if rat: S['noisy50_over_det_scale_ctrl_train'] = dict(median=float(np.median(rat)), q10=float(np.quantile(rat, .1)), q90=float(np.quantile(rat, .9)))
# by direction
for st in ('a', 'b'):
    v = [r['regret_ctrl_noisy'] for r in rows.values() if r['start'] == st and r['regret_ctrl_noisy']]
    if v: S['regret_ctrl_noisy_start_' + st] = dict(n=len(v), median=float(np.median(v)))
# the 3 failures
S['failures'] = {s: dict(regret_ctrl_noisy=rows[s]['regret_ctrl_noisy'], regret_ctrl_det=rows[s]['regret_ctrl_det'], p_switch=rows[s]['p_switch_ctrl_train'], s_det=rows[s]['s_det_ctrl_train'], s_noisy=rows[s]['s_noisy_ctrl_train']) for s in (6026, 6027, 6042, 6040) if s in rows}
json.dump(dict(summary=S, per_dish=rows), open(os.path.join(AUD, 'data', 'a3_regret.json'), 'w'), indent=1, default=float)
print(json.dumps(S, indent=1, default=float)[:6000])

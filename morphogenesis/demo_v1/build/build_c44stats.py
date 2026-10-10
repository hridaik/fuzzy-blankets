"""Chapter 4.4 numbers: held-out success/dose (heldout_eval.json) + regret per dish from the audit (data/regret/seed_*.json)."""
import sys, glob; sys.path.insert(0, '.')
from common import *
E = json.load(open(f'{T5}/logs/heldout_eval.json'))['table']
order = [('Controller', 'ctrl'), ('Fixed pulse', 'fixed'), ('Whole body (same amplitude)', 'whole'), ('Whole body (dose-matched)', 'whole_dm'), ('Random location', 'random'), ('Twin / sham (no light)', 'twin')]
arms = [dict(name=n, key=k, success=E[k]['success'][0], ci=[E[k]['success'][1], E[k]['success'][2]], dose=E[k]['dose_all'][0], dose_ci=[E[k]['dose_all'][1], E[k]['dose_all'][2]]) for n, k in order]
A1 = json.load(open(f'{AUD5}/data/a1_tables.json')); TS = A1['true_success_rates']
for a in arms: a['true_success'] = TS[a['key']]
reg = dict(ctrl=[], fixed=[], whole=[]); n = 0
for f in sorted(glob.glob(f'{AUD5}/data/regret/seed_*.json')):
    d = json.load(open(f)); n += 1
    for key, prot, used in (('ctrl', 'ctrl_train', 'ctrl_dose'), ('fixed', 'fixed', 'fixed_dose'), ('whole', 'whole_train', 'whole_dose')):
        x = d.get('det_' + prot, {}); dm = x.get('dose_min_noisy50') or x.get('dose_min_det')
        if dm: reg[key].append(d[used] / dm)
RS = json.load(open(f'{AUD5}/REGRET_AND_MAPS.json'))['regret']['summary']
write_js('c44stats', dict(medians=dict(ctrl=RS['regret_ctrl_noisy'], fixed=RS['regret_fixed_noisy'], whole=RS['regret_whole_noisy']), arms=arms, regret=reg, n_regret_dishes=n, note='regret = dose used / true minimal dose (noisy 50 % threshold of the same protocol, A3); partial if n < 60'))
print('regret dishes', n, {k: len(v) for k, v in reg.items()})

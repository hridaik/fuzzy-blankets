import sys, json; sys.path.insert(0, '.')
from h3 import *
B = json.load(open('../data/h3_bisect.json')); out = []
for st in 'ab':
    for c, d in ((10, 4 / G), (22, 4 / G), (8, 16 / G), (22, 16 / G)):
        thr = [x for x in B if x['state'] == st and x['centre'] == c and abs(x['dur'] - d) < 1e-6][0]['thr']; r = trial(st, c, d, 1.2 * thr, extra_release=2000.0, sham_twin=True)
        out.append(dict(state=st, centre=c, dur=d, amp=1.2 * thr, switch=r['switch'], mean_rho_end=r['mean_rho_end'], struct_diff=r['struct_diff'])); print(out[-1], flush=True)
json.dump(out, open('../data/h3_persist.json', 'w'))

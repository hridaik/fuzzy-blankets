import sys, json; sys.path.insert(0, '.')
import s4
from par import run_jobs
def job(pat, dur, b, dirn, rel):
    s4.REL = rel; return dict(s4.job(pat, dur, b, dirn), rel=rel)
if __name__ == "__main__":
    args = [('both', 40.0, b, 'LR', rel) for b in (0.2, 0.3, 0.6) for rel in (800.0, 3000.0, 6000.0)] + [('both', 20.0, b, 'LR', 3000.0) for b in (0.4, 0.6, 0.8)]
    res = run_jobs(job, args, workers=8, label='s4long'); json.dump(res, open('../data/s4_long.json', 'w'))
    for r in res: print(r['dur'], r['b'], 'release', r['rel'], r['cls'], r['reason'], 'dL', r['dL'] and round(r['dL'], 2), 'dR', r['dR'] and round(r['dR'], 2), 'orb', r['min_orbit_maxbel'] and round(r['min_orbit_maxbel'], 2))

import sys, json; sys.path.insert(0, '.')
import s4
from par import run_jobs
def job(pat, dur, b, dirn, rel):
    s4.REL = rel; return dict(s4.job(pat, dur, b, dirn), rel=rel)
if __name__ == "__main__":
    args = [('both', d, b, 'LR', 800.0) for d in (40.0, 80.0, 160.0, 320.0) for b in (0.06, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6)]
    res = run_jobs(job, args, workers=8, label='s4ref'); json.dump(res, open('../data/s4_refine.json', 'w'))
    for r in res: print(r['dur'], r['b'], r['cls'], r['reason'], 'dL', r['dL'] and round(r['dL'], 2), 'dR', r['dR'] and round(r['dR'], 2), 'orb', r['min_orbit_maxbel'] and round(r['min_orbit_maxbel'], 2))

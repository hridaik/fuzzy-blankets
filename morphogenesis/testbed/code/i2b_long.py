import sys, json; sys.path.insert(0, '.')
import i2
from par import run_jobs
if __name__ == "__main__":
    res = run_jobs(i2.job_serial, [(s, 400.0) for s in range(2)], workers=2, label='i2b400'); json.dump(res, open('../data/i2b_serial_interval400.json', 'w'))
    for r in res: print(r['seed'], r['final']['shape'], r['final']['slots_once'], r['final']['n_components'], r['all_new'], [t[1] for t in r['traj']])

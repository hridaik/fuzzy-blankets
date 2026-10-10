import sys, json, time; sys.path.insert(0, '.')
from par import run_jobs
import numpy as np
from theory3 import G_
t0 = time.time(); mode = sys.argv[1]
if __name__ == '__main__':
    if mode == 'natural':
        args = [(st, s, 'cal') for st in 'ab' for s in range(100, 200)] + [(st, s, 'val') for st in 'ab' for s in range(400, 430)]
        run_jobs(__import__('gen3').job_natural, args, workers=8, label='nat')
    elif mode == 'stress':
        scns = ['replace3', 'extrude', 'cutx', 'cuty']; args = [(sc, st, 700 + s) for sc in scns for st in 'ab' for s in range(3)]
        fus = ['fuse|a|6.0,0.0', 'fuse|a|0.0,3.0', 'fuse|b|6.0,0.0', 'fuse|b|5.0,0.0', 'fuse|b|0.0,3.0']; args += [(sc, 'a', 700 + s) for sc in fus for s in range(3)]
        run_jobs(__import__('gen3').job_stress, args, workers=8, label='stress')
    elif mode == 'switch':
        B = json.load(open('../data/h3_bisect.json')); DURS = [4 / G_, 16 / G_]; cen = [8, 10, 5, 12, 21, 22]; args = []; Xs = __import__('engine3').make_template2().Xs; i = 0
        for st in 'ab':
            for d in DURS:
                for c in cen:
                    thr = [x for x in B if x['state'] == st and abs(x['dur'] - d) < 1e-6 and x['centre'] == c][0]['thr']; far = int(np.argmax(np.linalg.norm(Xs - Xs[:, [c]], axis=0)))
                    for lev in (0.7, 1.0, 1.4): i += 1; args.append((st, c, d, lev, 'on', 600 + i, thr, far))
                    i += 1; args.append((st, c, d, 1.4, 'wrong', 600 + i, thr, far)); i += 1; args.append((st, c, d, 1.0, 'sham', 600 + i, thr, far))
        run_jobs(__import__('gen3').job_switch, args, workers=8, label='switch')
    elif mode == 'decoy':
        args = [(st, k, 800 + j) for st in 'ab' for j, k in enumerate(['sec', 'rg', 'mig', 'mbath_low', 'mbath_high', 'mpipette', 'pipette', 'bath'])]
        run_jobs(__import__('gen3').job_decoy, args, workers=8, label='decoy')
    print('wall', mode, time.time() - t0)
    
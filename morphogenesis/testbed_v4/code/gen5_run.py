import sys, time, json
from gen5 import *
from par4 import run_jobs
def pick_dishes():
    ks = [(s, sample_dish(s)['kappa_g']) for s in range(100, 700)]
    return [min(ks, key=lambda x: abs(x[1] - t))[0] for t in (1.6, KG_MED, 3.7)]
if __name__ == "__main__":
    fam = sys.argv[1]; t0 = time.time()
    if fam == 'natural':
        args = [(s, 'a' if (s * 7919) % 2 == 0 else 'b', 'cal') for s in range(2000, 2024)] + [(s, 'a' if s % 2 == 0 else 'b', 'val') for s in range(3000, 3008)]
        run_jobs(job_natural, args, label='natural')
    elif fam == 'stress':
        scn1 = ['replace3', 'extrude', 'cutx', 'cuty']; scn2 = ['fuse|a|6.0,0.0', 'fuse|b|6.0,0.0', 'fuse|b|5.0,0.0', 'fuse|b|0.0,3.0']
        args = [(sc, st, 4000 + k) for sc in scn1 for st in 'ab' for k in range(3)] + [(sc, 'a', 4100 + k) for sc in scn2 for k in range(3)]
        run_jobs(job_stress, args, label='stress')
    elif fam == 'damage':
        ds = pick_dishes(); print('damage dishes', ds, [round(sample_dish(s)['kappa_g'], 2) for s in ds]); json.dump(ds, open('../data/package_dishes.json', 'w'))
        args = [(s, L, 'middle', 16) for s in ds for L in ('MA', 'MB', 'SEC', 'RG', 'MIG')] + [(s, 'MB', 'tail_end', 16) for s in ds]
        run_jobs(job_damage, args, label='damage')
    elif fam == 'switch':
        ds = json.load(open('../data/package_dishes.json')); args = [(s, st, c, dm) for s in ds for st in 'ab' for c in ('middle', 'limb_side', 'tail_end') for dm in (4, 16)]
        run_jobs(job_switch, args, label='switch')
    print(fam, 'wall', time.time() - t0)

import sys, os, time, json
from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'm0c_port_completion', 'code'))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)


def check_stationary(mat, thr=1.0e-3, window=32):
    import numpy as np
    pos = mat['positions']; sec = mat['secretion']
    dx = np.linalg.norm(np.diff(pos, axis=1), axis=0)
    ds = np.linalg.norm(np.diff(sec, axis=1), axis=0)
    below = (dx < thr) & (ds < thr)
    for i in range(len(below) - window + 1):
        if below[i:i + window].all():
            return i + 1
    return None


def _job(seed):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'm0c_port_completion', 'code'))
    from fallback_engine import run
    t0 = time.time()
    mat, elapsed = run({'L': 2}, n_bins=512, noise_seed=seed,
                        out_mat=os.path.join(DATA_DIR, f'pilot_ind{seed}_N512.mat'))
    stat_bin = check_stationary(mat)
    return {'seed': seed, 'elapsed': elapsed, 'stationary_at': stat_bin}


if __name__ == '__main__':
    seeds = list(range(8))
    results = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_job, s): s for s in seeds}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"seed {r['seed']}: elapsed={r['elapsed']:.1f}s stationary_at={r['stationary_at']}")
    with open(os.path.join(DATA_DIR, 'pilot_results.json'), 'w') as f:
        json.dump(results, f, indent=2)

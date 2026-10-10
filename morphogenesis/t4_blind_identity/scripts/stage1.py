"""Run online per-run processing for a list of runs / levels; pickle results to cache/."""
import sys, os, pickle, time; sys.path.insert(0, '.')
from multiprocessing import Pool
from t4 import io, pipeline

def work(a):
    run, level, fov, tag = a
    p = f'cache/{tag}/{run}_{level}.pkl'
    if os.path.exists(p): return p
    geo = pipeline.load_geometry()
    res = pipeline.process(run, level, geo, fov)
    pickle.dump(res, open(p, 'wb'))
    return p

if __name__ == '__main__':
    split = sys.argv[1]; tag = sys.argv[2]; levels = sys.argv[3].split(',')
    cat = io.catalog()
    rows = [r for r in cat if (r['split'] == 'development') == (split == 'development')]
    if split.startswith('only:'):
        rows = [r for r in cat if r['run'] in split[5:].split(',')]
    os.makedirs(f'cache/{tag}', exist_ok=True)
    jobs = [(r['run'], L, r['fov'], tag) for r in rows for L in levels]
    t0 = time.time()
    with Pool(8) as P:
        for i, _ in enumerate(P.imap_unordered(work, jobs, chunksize=4)):
            if i % 200 == 0: print(i, len(jobs), round(time.time() - t0), flush=True)
    print('done', time.time() - t0)

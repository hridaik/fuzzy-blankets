"""process-parallel job runner (JAX CPU, one thread per worker)"""
import os, sys, time, multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

def _init():
    os.environ['XLA_FLAGS'] = '--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1'
    os.environ['OMP_NUM_THREADS'] = '1'
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_jobs(func, arglist, workers=8, label=''):
    """func: top-level function (picklable); arglist: list of tuples. Returns results in order."""
    t0 = time.time(); res = [None] * len(arglist)
    ctx = mp.get_context('spawn')
    with ProcessPoolExecutor(workers, mp_context=ctx, initializer=_init) as ex:
        futs = [ex.submit(func, *a) for a in arglist]
        for i, f in enumerate(futs):
            res[i] = f.result()
            if (i + 1) % max(1, len(futs) // 10) == 0: print(f'[{label}] {i+1}/{len(futs)} {time.time()-t0:.0f}s', flush=True)
    return res

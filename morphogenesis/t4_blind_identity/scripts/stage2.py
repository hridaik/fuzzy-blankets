"""Apply frozen calibration to stage-1 cache and write per-run outputs. usage: stage2.py CACHE_TAG OUTDIR [run,run,...]"""
import sys, os, pickle, time; sys.path.insert(0, '.')
from multiprocessing import Pool
from t4 import io, outputs

TAG, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3].split(',') if len(sys.argv) > 3 else None
HASH = open('FROZEN_HASH.txt').read().strip() if os.path.exists('FROZEN_HASH.txt') else 'DEV-UNFROZEN'
CAL = None

def work(row):
    global CAL
    if CAL is None: CAL = outputs.Calib()
    recs = {lv: pickle.load(open(f"cache/{TAG}/{row['run']}_{lv}.pkl", 'rb')) for lv in ('O1', 'O2', 'O3a', 'O3b')}
    outputs.write_run(row, recs, CAL, OUT, HASH)
    return row['run']

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    rows = [r for r in io.catalog() if os.path.exists(f"cache/{TAG}/{r['run']}_O1.pkl")]
    if ONLY: rows = [r for r in rows if r['run'] in ONLY]
    t0 = time.time()
    with Pool(8) as P:
        for i, _ in enumerate(P.imap_unordered(work, rows, chunksize=2)):
            if i % 50 == 0: print(i, len(rows), round(time.time() - t0), flush=True)
    print('done', time.time() - t0)

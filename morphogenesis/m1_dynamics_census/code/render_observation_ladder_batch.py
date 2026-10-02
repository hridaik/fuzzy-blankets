"""Part G: batch-render O2-O4 for a directory of rollout .mat files, at
every FRAME_STRIDE-th frame, saving compressed .npz per rollout. Storage is
tracked live and the run stops (reporting) if projected total would exceed
the 50GB cap.
"""
import glob
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from observation_ladder import render_all, FRAME_STRIDE, RENDERER_VERSION

CAP_BYTES = 50 * 1024 ** 3


def render_directory(mat_glob, out_dir, run_id_fn=None):
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(mat_glob))
    files = [f for f in files if "manifest" not in f and "_vinit" not in f]
    total_bytes = 0
    n_done = 0
    t0 = time.time()
    for fpath in files:
        run_id = run_id_fn(fpath) if run_id_fn else os.path.basename(fpath).replace(".mat", "")
        out_path = os.path.join(out_dir, f"{run_id}.npz")
        if os.path.exists(out_path):
            total_bytes += os.path.getsize(out_path)
            n_done += 1
            continue
        try:
            import scipy.io as sio
            d = sio.loadmat(fpath)
            n_bins = d["positions"].shape[1]
        except Exception as e:
            print(f"SKIP {fpath}: {e}")
            continue
        frames = list(range(0, n_bins, FRAME_STRIDE))
        out = render_all(fpath, run_id, frames)
        np.savez_compressed(out_path, **out)
        sz = os.path.getsize(out_path)
        total_bytes += sz
        n_done += 1
        if n_done % 20 == 0:
            print(f"  [{n_done}/{len(files)}] {run_id}: {sz} bytes, running total {total_bytes/1e9:.3f} GB", flush=True)
        if total_bytes > CAP_BYTES:
            print(f"STOPPING: projected storage exceeds 50GB cap at {n_done}/{len(files)} files")
            return total_bytes, n_done, False
    elapsed = time.time() - t0
    print(f"Rendered {n_done}/{len(files)} rollouts, {total_bytes/1e9:.3f} GB, {elapsed:.1f}s")
    return total_bytes, n_done, True


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("mat_glob")
    ap.add_argument("out_dir")
    args = ap.parse_args()
    total, n, ok = render_directory(args.mat_glob, args.out_dir)
    print(json.dumps({"total_bytes": total, "n_rendered": n, "under_cap": ok,
                       "renderer_version": RENDERER_VERSION}))

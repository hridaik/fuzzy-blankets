"""Part 0 compute: 0.2 direct-Octave cross-check, 0.1a designed controls,
0.3c long continuation, noise-seed control. 8-way parallel."""
import json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.dirname(__file__))
from m2a_common import *
from fallback_engine import run

OUT = os.path.join(DATA, "part0"); os.makedirs(OUT, exist_ok=True)

def perm_v0(perm):
    v = np.zeros((8, 8))
    for i, p in enumerate(perm): v[p, i] = 6.0
    return v

PERMS = {"identity": list(range(8)), "reverse": list(range(7, -1, -1)),
         "random": list(np.random.default_rng(777).permutation(8))}

def job(spec):
    kind = spec["kind"]; t0 = time.time()
    if kind == "direct":
        v0file = ""
        if spec["v0"] is not None:
            v0file = os.path.join(OUT, spec["name"] + "_v0.mat"); sio.savemat(v0file, {"v0": spec["v0"]})
        out = os.path.join(OUT, spec["name"] + ".mat")
        octave(f"direct_morph(2,{spec['N']},{spec['seed']},'{v0file}','{out}');")
    else:
        out = os.path.join(OUT, spec["name"] + ".mat")
        run({"L": 2}, initial_state=spec["v0"], n_bins=spec["N"], noise_seed=spec["seed"], out_mat=out)
        vi = out.replace(".mat", "_vinit.mat")
        if os.path.exists(vi): os.remove(vi)
    return {"name": spec["name"], "elapsed": time.time() - t0}

if __name__ == "__main__":
    specs = []
    for i in (0, 1):
        specs.append(dict(kind="direct", name=f"direct_primary_{i:04d}", N=512, seed=i, v0=None))
    specs.append(dict(kind="direct", name="direct_secondary_0000", N=512, seed=0, v0=secondary_v0(0)))
    for nm, p in PERMS.items():
        specs.append(dict(kind="engine", name=f"perm_{nm}", N=512, seed=0, v0=perm_v0(p)))
    # noise-seed control: primary_0000's v0 with other noise seeds
    v0p0 = draw_v0_octave(0)
    for s in (1001, 1002):
        specs.append(dict(kind="engine", name=f"noiseseed_primary0000_s{s}", N=512, seed=s, v0=v0p0))
    # long continuations (plain N=2048, i.e. the M1 cascade horizon)
    specs.append(dict(kind="engine", name="long_primary_0000_N2048", N=2048, seed=0, v0=None))
    specs.append(dict(kind="engine", name="long_primary_0001_N2048", N=2048, seed=1, v0=None))
    specs.append(dict(kind="engine", name="long_secondary_0000_N2048", N=2048, seed=0, v0=secondary_v0(0)))
    json.dump({"perms": {k: [int(x) for x in v] for k, v in PERMS.items()}},
              open(os.path.join(OUT, "perms.json"), "w"))
    t0 = time.time(); res = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(job, specs):
            res.append(r); print(r, flush=True)
    json.dump({"wall_s": time.time() - t0, "jobs": res}, open(os.path.join(OUT, "part0_jobs.json"), "w"), indent=1)

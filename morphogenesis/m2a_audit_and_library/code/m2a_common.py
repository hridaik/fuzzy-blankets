"""Shared helpers for M2a. Engine = m0c fallback engine (imported unmodified)
plus M2a's own Octave scripts in oracle/ (generalised setup, Part 0.2 script)."""
import hashlib, json, os, subprocess, sys, time
import numpy as np
import scipy.io as sio

HERE = os.path.dirname(os.path.abspath(__file__))
M2A = os.path.dirname(HERE)
MORPH = os.path.dirname(M2A)
M0C_CODE = os.path.join(MORPH, "m0c_port_completion", "code")
M1 = os.path.join(MORPH, "m1_dynamics_census")
M1_CODE = os.path.join(M1, "code")
SPM12 = os.path.join(MORPH, "m0b_reference_port", "sources", "spm12")
M0B_ORACLE = os.path.join(MORPH, "m0b_reference_port", "oracle")
M1_ORACLE = os.path.join(M1, "oracle")
M2A_ORACLE = os.path.join(M2A, "oracle")
DATA = os.path.join(M2A, "data")
SEALED = os.path.join(M2A, "sealed")
for p in (M0C_CODE, M1_CODE):
    if p not in sys.path:
        sys.path.insert(0, p)

STAT_THR, STAT_WIN = 1.0e-3, 32  # M1 frozen (THRESHOLDS.md)


def octave(script, timeout=7200):
    pre = "source $(conda info --base)/etc/profile.d/conda.sh && conda activate octave-dem && "
    paths = (f"addpath('{SPM12}'); addpath('{SPM12}/toolbox/DEM'); "
             f"addpath('{M0B_ORACLE}'); addpath('{M1_ORACLE}'); addpath('{M2A_ORACLE}'); ")
    t0 = time.time()
    r = subprocess.run(["bash", "-c", pre + f'octave --no-gui --eval "{paths}{script}"'],
                       capture_output=True, text=True, timeout=timeout, cwd=M2A)
    if r.returncode != 0:
        raise RuntimeError(f"octave failed: {r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    return r.stdout, time.time() - t0


def engine_hash(extra_files=()):
    h = hashlib.sha256()
    for f in [os.path.join(SPM12, "spm_ADEM.m"), os.path.join(M0B_ORACLE, "dem_setup.m"),
              os.path.join(M0B_ORACLE, "run_and_export.m"),
              os.path.join(M0B_ORACLE, "dem_morphogenesis_Gg.m"),
              os.path.join(M0B_ORACLE, "dem_morphogenesis_Mg.m"), *extra_files]:
        h.update(open(f, "rb").read())
    return h.hexdigest()[:16]


def is_stationary(mat, thr=STAT_THR, window=STAT_WIN):
    pos, sec = np.asarray(mat["positions"]), np.asarray(mat["secretion"])
    dx = np.linalg.norm(np.diff(pos, axis=1), axis=0)
    ds = np.linalg.norm(np.diff(sec, axis=1), axis=0)
    below = (dx < thr) & (ds < thr)
    for i in range(len(below) - window + 1):
        if below[i:i + window].all():
            return True, i + 1
    return False, None


def draw_v0_octave(seed, n=8):
    """The primary-individual initial beliefs: Octave randn('seed',s); randn(n,n)/8."""
    out = os.path.join(DATA, "tmp_v0_%d.mat" % seed)
    octave(f"rand('seed',{seed}); randn('seed',{seed}); v0=randn({n},{n})/8; save('-v7','{out}','v0');")
    v = sio.loadmat(out)["v0"]
    os.remove(out)
    return v


def secondary_v0(idx):
    return np.random.default_rng(100000 + idx).standard_normal((8, 8)) * np.exp(2.0)


def template():
    from analysis import P_X, P_S
    return P_X, P_S


def softmax_cols(v):
    e = np.exp(v - v.max(axis=0, keepdims=True))
    return e / e.sum(axis=0, keepdims=True)

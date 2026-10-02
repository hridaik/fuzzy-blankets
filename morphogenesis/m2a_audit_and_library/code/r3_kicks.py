"""R3: kicks K1-K4 (M1's magnitudes) as CONTINUATIONS at b_adult = 320 (no ramp reset). Individuals primary 0-4; 20 kick seeds per
type/magnitude (K2 is deterministic -> 1 seed). Matched unperturbed twin = null continuation (R2 UNP_ADULT / exact fixed point)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
M1_NN = 1.0806                      # M1's MEAN_NN_SPACING (template units); magnitudes kept IDENTICAL to M1
NIND3, NSEED, H3 = 5, 20, 400
KINDS = ["K1_s0.5", "K1_s1.5", "K2", "K3", "K4"]

def make_kick(kind, ind_idx, seed, pos, sec):
    """pos (2,8), sec (4,8): pre-kick adult state. Returns kick dict for oracle + log."""
    rng = np.random.default_rng(700000 + 1000 * ind_idx + seed)
    if kind.startswith("K1"):
        sig = (0.5 if kind.endswith("0.5") else 1.5) * M1_NN
        d = rng.normal(scale=sig, size=pos.shape); return dict(type="pos", dpos=d), dict(sigma=sig)
    if kind == "K2":
        return dict(type="sec", sec=np.tile(sec.mean(axis=1, keepdims=True), (1, sec.shape[1]))), {}
    if kind == "K3":
        return dict(type="belief", v=rng.standard_normal((8, 8)) / 8.0), {}
    if kind == "K4":
        cell = int(rng.integers(8)); dr = rng.standard_normal(2); dr /= np.linalg.norm(dr)
        d = np.zeros_like(pos); d[:, cell] = 3.0 * M1_NN * dr; return dict(type="pos", dpos=d), dict(cell=cell)
    raise ValueError(kind)

def job(ind_idx, kind, seed):
    ind = Ind("primary", ind_idx); A = path("census", f"{ind.name}_A")
    m = load(A); pos, sec, _ = state(m)
    kick, log = make_kick(kind, ind_idx, seed, pos, sec)
    out = path("r3", f"{ind.name}_{kind}_s{seed:02d}")
    sim(out, H3, ind, cont=A, kick=kick, meta=dict(stage="R3", kick=kind, seed=seed, **log))
    return out

if __name__ == "__main__":
    tasks = []
    for i in range(NIND3):
        for k in KINDS:
            for s in (range(1) if k == "K2" else range(NSEED)): tasks.append((job, (i, k, s)))
    print(len(tasks), "kick runs"); run_tasks(tasks, label="R3")

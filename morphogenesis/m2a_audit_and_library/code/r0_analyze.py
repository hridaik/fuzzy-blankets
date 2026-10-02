import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from m2a_sim import *
from part0_offline import X, S_
from analysis import d_target
D = DATA + "/r0/"; H = 1100
s = load(D + "single.mat"); R = {"splits": {}, "ablation": {}}
KEYS = ("positions", "secretion", "v_expect", "pred_err_1", "pred_err_2", "free_energy_J")
for b0 in (64, 300, 320, 1000):
    A, B = load(D + f"split{b0}_A.mat"), load(D + f"split{b0}_B.mat")
    r = {}
    for k in KEYS:
        a, b, c = A[k], B[k], s[k]
        if c.ndim == 1 or c.shape[0] == 1: cat = np.concatenate([a.ravel(), b.ravel()]); r[k] = float(np.abs(cat - c.ravel()).max())
        else: cat = np.hstack([a, b]); r[k] = float(np.abs(cat - c).max())
    R["splits"][b0] = r
for ab in ("Ahist", "pu", "qu_hi", "qa", "qv0"):
    B = load(D + f"abl_{ab}.mat"); n = B["positions"].shape[1]
    d = np.abs(B["positions"] - s["positions"][:, 300:300 + n]).max(0)
    R["ablation"][ab] = dict(max_pos_dev=float(d.max()), first_bin_dev=int(np.nonzero(d > 1e-12)[0][0]) if (d > 1e-12).any() else None)
# R0.1
c = load(D + "clock512.mat"); cen = sio.loadmat(M1 + "/data/census/primary_0000_N512.mat")
R["clock512_vs_census_maxabs_pos"] = float(np.abs(c["positions"] - cen["positions"]).max())
R["clock512_d_target_512"] = float(d_target(X(c, -1), S_(c, -1))[0]); R["census_d_target"] = float(d_target(X(cen, -1), S_(cen, -1))[0])
# adult fixed point
sp = np.maximum(np.linalg.norm(np.diff(s["positions"], axis=1), axis=0), np.linalg.norm(np.diff(s["secretion"], axis=1), axis=0))
R["speed_at"] = {b: float(sp[b - 1]) for b in (100, 200, 300, 320, 400, 600, 1000)}
R["dtarget_at"] = {b: float(d_target(X(s, b - 1), S_(s, b - 1))[0]) for b in (32, 64, 128, 320, 1100)}
# null continuation from b=320: drift vs state at 320 (within the continuation)
B = load(D + "split320_B.mat"); A = load(D + "split320_A.mat")
R["null_continuation_320"] = dict(max_drift_pos=float(np.abs(B["positions"] - A["positions"][:, -1:]).max()), max_drift_sec=float(np.abs(B["secretion"] - A["secretion"][:, -1:]).max()),
                                  max_drift_v=float(np.abs(B["v_expect"] - A["v_expect"][:, -1:]).max()), final_speed=float(sp[-1]))
json.dump(R, open(D + "r0_results.json", "w"), indent=1); print(json.dumps(R, indent=1))

"""Collect all Part 0 results into data/part0/part0_results.json (consumed by the AUDIT_M1.md writer)."""
import json, os, sys
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.dirname(__file__))
from part0_offline import *
from analysis import d_target
P = DATA + "/part0/"
J = lambda n: json.load(open(P + n))

def L(n): return sio.loadmat(P + n + ".mat")

def main():
    R = {}
    # 0.2
    cc = []
    for nm, (k, i) in {"direct_primary_0000": ("primary", 0), "direct_primary_0001": ("primary", 1), "direct_secondary_0000": ("secondary", 0)}.items():
        a, b = L(nm), cen(k, i)
        v0 = draw_v0_octave(i) if k == "primary" else secondary_v0(i)
        cc.append(dict(id=f"{k}_{i:04d}", max_abs_pos=float(np.abs(a["positions"] - b["positions"]).max()),
                       max_abs_sec=float(np.abs(a["secretion"] - b["secretion"]).max()),
                       max_abs_v=float(np.abs(a["v_expect"] - b["v_expect"]).max()),
                       v0_match=float(np.abs(a["v_initial"] - v0).max())))
    R["crosscheck_0_2"] = cc
    # noise-seed control
    b = cen("primary", 0)
    R["noise_seed_control"] = [dict(seed=s, max_abs_pos=float(np.abs(L(f"noiseseed_primary0000_s{s}")["positions"] - b["positions"]).max())) for s in (1001, 1002)]
    # designed controls
    perms = J("perms.json")["perms"]; dc = []
    for nm, p in perms.items():
        a = L("perm_" + nm); d, rm, ft, mm = d_target(X(a, -1), S_(a, -1))
        pb = softmax_cols(V(a, -1))
        dc.append(dict(name=nm, designed=p, hungarian_role_map=[int(x) for x in rm], argmax_belief_map=[int(x) for x in pb.argmax(0)],
                       equal=[int(x) for x in rm] == p, d_target=float(d), bin0_dev_from_P=float(np.abs(X(a, 0) - P_X[:, p]).max()),
                       dpair_to_census_end=float(hung(X(a, -1), X(cen("primary", 0), -1)))))
    R["designed_controls"] = dc
    # 0.3c
    lc = {}
    for tag, files in (("plain_N2048", ["long_primary_0000_N2048", "long_primary_0001_N2048", "long_secondary_0000_N2048"]),
                       ("abs_ramp_N2048", ["longabs_primary_0000_N2048", "longabs_primary_0001_N2048", "longabs_secondary_0000_N2048"])):
        rows = []
        for f in files:
            if not os.path.exists(P + f + ".mat"): continue
            m = L(f)
            rows.append(dict(file=f, stationary=is_stationary(m), d_target={b: float(d_target(X(m, b - 1), S_(m, b - 1))[0]) for b in (246, 512, 1024, 2048)},
                             drift_last_512=float(np.abs(X(m, -1) - X(m, -513)).max())))
        lc[tag] = rows
    R["long_runs"] = lc
    # frozen ramp
    fr = []
    for nm in ("primary0000_s0617", "primary0000_s0865", "secondary0000_s0617", "primary0001_s0617"):
        m = L("frozen_" + nm); x, s = m["positions"], m["secretion"]
        v = np.maximum(np.linalg.norm(np.diff(x, axis=1), axis=0), np.linalg.norm(np.diff(s, axis=1), axis=0))
        fr.append(dict(run=nm, m1_criterion=is_stationary(m), d_target=float(d_target(X(m, -1), S_(m, -1))[0]),
                       vel=[float(v[b]) for b in (50, 100, 150, 200, 300, 500)]))
    R["frozen_ramp"] = fr
    R["frozen_ramp_pairwise_end"] = dict(
        p0_vs_s0=float(hung(X(L("frozen_primary0000_s0617"), -1), X(L("frozen_secondary0000_s0617"), -1))),
        p0_vs_p1=float(hung(X(L("frozen_primary0000_s0617"), -1), X(L("frozen_primary0001_s0617"), -1))))
    json.dump(R, open(P + "part0_results.json", "w"), indent=1)
    print("collected")

if __name__ == "__main__":
    main()

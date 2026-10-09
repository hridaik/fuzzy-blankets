"""D1 analysis: eigen-structure of the one-bin map Jacobians. State blocks: v (0:64) beliefs, vdot (64:128) belief velocity, a (128:176) action [pos 16 + secretion 32],
Aprev (176:224) previous action. 'Observable' = action blocks (the only state components that are positions/secretion); 'hidden' = beliefs and their higher order."""
import sys, os, json
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
BL = dict(beliefs=slice(0, 64), belief_vel=slice(64, 128), act_pos=slice(128, 144), act_sec=slice(144, 176), prev_pos=slice(176, 192), prev_sec=slice(192, 224))
def eig(J):
    w, V = np.linalg.eig(J); o = np.argsort(-np.abs(w)); return w[o], V[:, o]
def blockfrac(v):
    p = np.abs(v) ** 2; p = p / p.sum()
    return {k: float(p[s].sum()) for k, s in BL.items()}
def analyze(name):
    d = sio.loadmat(path("d1", f"J_{name}")); J = d["J"]; out = dict(name=name, steps=[float(x) for x in np.ravel(d["steps"])], resid=float(np.abs(d["residual"]).max()))
    ws = []; 
    for i in range(J.shape[2]):
        w, V = eig(J[:, :, i]); ws.append((w, V))
    out["jac_diff_rel"] = float(np.linalg.norm(J[:, :, 0] - J[:, :, 1]) / np.linalg.norm(J[:, :, 1]))
    w, V = ws[1]; w0 = ws[0][0]
    out["max_abs_mu"] = [float(np.abs(a).max()) for a, _ in ws]
    out["n_unstable"] = [int((np.abs(a) > 1 + 1e-9).sum()) for a, _ in ws]
    out["top_agree_max_dmu"] = float(np.max(np.abs(w[:10] - w0[:10])))
    modes = []
    for k in range(8):
        f = blockfrac(V[:, k]); obs = f["act_pos"] + f["act_sec"] + f["prev_pos"] + f["prev_sec"]
        modes.append(dict(rank=k, mu=[float(w[k].real), float(w[k].imag)], abs=float(abs(w[k])), rate=float(np.log(abs(w[k]))), tau_bins=float(-1 / np.log(abs(w[k]))) if abs(w[k]) < 1 else None, observable_frac=float(obs), hidden_frac=float(1 - obs), blocks=f))
    out["modes"] = modes
    out["real_negative_near_-1"] = [dict(mu=complex(x).real, abs=abs(x)) for x in w if abs(x.imag) < 1e-6 and x.real < -0.8][:5]
    return out, J, ws
if __name__ == "__main__":
    res = {}
    for n in ["class0", "class1", "dhcycle_a", "dhcycle_b"]:
        res[n], J, ws = analyze(n)
    Ja = sio.loadmat(path("d1", "J_dhcycle_a"))["J"][:, :, 1]; Jb = sio.loadmat(path("d1", "J_dhcycle_b"))["J"][:, :, 1]
    for lab, M in (("monodromy_BA", Jb @ Ja), ("monodromy_AB", Ja @ Jb)):
        w, V = eig(M); res[lab] = dict(max_abs=float(abs(w[0])), top=[[float(x.real), float(x.imag)] for x in w[:6]], n_unstable=int((np.abs(w) > 1 + 1e-9).sum()),
            floquet_per_bin_rate=[float(np.log(abs(x)) / 2) for x in w[:6]], near_plus1=[float(abs(x - 1)) for x in w[:3]],
            top_blocks=blockfrac(V[:, 0]))
    wa = eig(Ja)[0]; wb = eig(Jb)[0]
    res["dhcycle_one_bin_eigs_negative_real"] = dict(a=[float(x.real) for x in wa if abs(x.imag) < 1e-6 and x.real < -0.5], b=[float(x.real) for x in wb if abs(x.imag) < 1e-6 and x.real < -0.5])
    json.dump(res, open(path("d1", "d1_summary.json").replace(".mat", ".json"), "w"), indent=1)
    for n, r in res.items():
        if "modes" in r:
            print(n, "max|mu| %s unstable %s Jdiff %.2e top-agree %.2e resid %.1e" % (r["max_abs_mu"], r["n_unstable"], r["jac_diff_rel"], r["top_agree_max_dmu"], r["resid"]))
            for m in r["modes"][:6]: print("  ", m["rank"], np.round(m["mu"], 5), "rate %.4f" % m["rate"], "obs %.2f" % m["observable_frac"], {k: round(v, 2) for k, v in m["blocks"].items() if v > 0.05})
        else: print(n, json.dumps(r)[:600])

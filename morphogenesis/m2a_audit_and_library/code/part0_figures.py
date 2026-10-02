import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from part0_offline import *
BLUE, ORANGE, GREY = "#2a6fbb", "#d9822b", "#8a8f98"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
ids = [("primary", i) for i in range(6)] + [("secondary", i) for i in range(4)]
M = [cen(k, i) for k, i in ids]
fine = json.load(open(DATA + "/part0/offline_3a_fine.json"))
fig, ax = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
b = np.arange(512)
ax[0].semilogy(b, np.maximum(fine["max"], 1e-13), color=BLUE, lw=2)
ax[0].axhline(0.25, color=GREY, ls="--", lw=1); ax[0].text(300, 0.3, "tau_pair = 0.25", color="#555")
ax[0].axhline(1e-3, color=GREY, ls=":", lw=1); ax[0].text(300, 1.3e-3, "1e-3", color="#555")
ax[0].set(xlabel="bin", ylabel="max pairwise permutation-invariant distance\n(10 individuals, 45 pairs)", title="Individuals merge by bin ~126 (<1e-3), floor ~1e-12")
for (k, i), m in zip(ids, M):
    x, s = m["positions"], m["secretion"]
    v = np.maximum(np.linalg.norm(np.diff(x, axis=1), axis=0), np.linalg.norm(np.diff(s, axis=1), axis=0))
    ax[1].semilogy(np.arange(1, 512), v, color=BLUE, lw=1, alpha=0.6)
rs = 2 / 512 * np.exp(-2 * np.arange(1, 512) / 512)
ax[1].semilogy(np.arange(1, 512), rs, color=ORANGE, lw=2); ax[1].text(330, 1.2e-3, "ramp rate ds/dbin", color=ORANGE)
fr = sio.loadmat(DATA + "/part0/frozen_primary0000_s0617.mat"); x, s = fr["positions"], fr["secretion"]
v = np.maximum(np.linalg.norm(np.diff(x, axis=1), axis=0), np.linalg.norm(np.diff(s, axis=1), axis=0))
ax[1].semilogy(np.arange(1, 512), np.maximum(v, 1e-16), color="#222", lw=2); ax[1].text(120, 3e-9, "ramp frozen at s=0.617", color="#222")
ax[1].axhline(1e-3, color=GREY, ls=":"); ax[1].set_ylim(1e-12, 1)
ax[1].text(200, 0.02, "10 census individuals (blue)", color=BLUE)
ax[1].set(xlabel="bin", ylabel="per-bin speed (M1 stationarity metric)", title="Bin 246 follows the ramp; frozen ramp stops by bin ~35")
fig.savefig("figures/part0_merge_and_stationarity.png", dpi=130)

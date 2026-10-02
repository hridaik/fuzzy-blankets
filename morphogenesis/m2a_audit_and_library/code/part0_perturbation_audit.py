"""Part 0.1c: did M1's perturbations take effect? Per individual x perturbation x timing."""
import json, os, sys
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.dirname(__file__))
from m2a_common import *
from analysis import d_pair

TAU_EFF = 0.05   # DECLARED before analysis: perturbation "took effect" if max over window of
                 # per-cell index-wise position deviation (RMS over cells) from the matched unperturbed twin >= 0.05
                 # template units (= 0.2 x tau_pos; ~50x the stationarity velocity threshold per bin)
W, OFF_SHORT = 332, 64

def xs(m, N=None):
    return m["positions"].reshape(8, 2, -1)      # cell, xy, bin

def dev_series(a, b):
    n = min(a.shape[-1], b.shape[-1])
    return np.sqrt(((a[..., :n] - b[..., :n]) ** 2).sum(1).mean(0))   # RMS over cells of cell-wise Euclid dev... per bin

def end_pair(a, b):
    xa, xb = a["positions"][:, -1].reshape(8, 2).T, b["positions"][:, -1].reshape(8, 2).T
    sa, sb = a["secretion"][:, -1].reshape(4, 8, order="F"), b["secretion"][:, -1].reshape(4, 8, order="F")
    return d_pair(xa, sa, xb, sb), float(np.linalg.norm(xa - xb, axis=0).mean())

def main():
    rows = []
    for i in range(20):
        cen = sio.loadmat(f"{M1}/data/census/primary_{i:04d}_N512.mat")
        tw_f = sio.loadmat(f"{DATA}/twins/primary_{i:04d}_UNPERT_FRESH_N1024.mat")
        tw_a = sio.loadmat(f"{DATA}/twins/primary_{i:04d}_UNPERT_ADULT_N1024.mat")
        for kind in ("DH", "DT", "AN"):
            sus = sio.loadmat(f"{M1}/data/withdrawal/primary_{i:04d}_{kind}_SUSTAINED_N1024.mat") \
                if os.path.exists(f"{M1}/data/withdrawal/primary_{i:04d}_{kind}_SUSTAINED_N1024.mat") else \
                sio.loadmat(f"{M1}/data/withdrawal/primary_{i:04d}_{kind}_SUSTAINED_N512.mat")
            sd, sd_idx = end_pair(sus, cen)
            sdev = float(dev_series(xs(sus), xs(cen)).max())
            for timing in ("DEV-SHORT", "DEV-LONG", "ADULT"):
                w = sio.loadmat(f"{M1}/data/withdrawal/primary_{i:04d}_{kind}_{timing}_N1024.mat")
                tw = tw_a if timing == "ADULT" else tw_f
                off = OFF_SHORT if timing == "DEV-SHORT" else W
                ser = dev_series(xs(w), xs(tw))
                win_max = float(ser[: off + 8].max())
                post_end = float(ser[-1])
                ed, ed_idx = end_pair(w, tw)
                rows.append(dict(ind=i, kind=kind, timing=timing, sustained_vs_unpert_dpair=sd, sustained_vs_unpert_idx=sd_idx,
                                 sustained_max_dev=sdev, window_max_dev=win_max, took_effect=bool(win_max >= TAU_EFF),
                                 end_vs_twin_dpair=ed, end_vs_twin_idx=float(ed_idx), final_dev=post_end))
    # AN vs DH identity check
    ident = []
    for i in range(20):
        for timing in ("DEV-SHORT", "DEV-LONG", "ADULT", "SUSTAINED"):
            f = lambda k: sio.loadmat(f"{M1}/data/withdrawal/primary_{i:04d}_{k}_{timing}_N{512 if timing=='SUSTAINED' else 1024}.mat")
            try:
                a, b = f("AN"), f("DH")
                ident.append(float(np.abs(a["positions"] - b["positions"]).max()))
            except Exception as e:
                ident.append(None)
    # sham check
    sham = []
    for i in range(20):
        for timing in ("DEV-SHORT", "DEV-LONG", "ADULT"):
            s = sio.loadmat(f"{M1}/data/sham/primary_{i:04d}_sham_{timing}_N1024.mat")
            tw = sio.loadmat(f"{DATA}/twins/primary_{i:04d}_UNPERT_{'ADULT' if timing=='ADULT' else 'FRESH'}_N1024.mat")
            off = OFF_SHORT if timing == "DEV-SHORT" else W
            ser = dev_series(xs(s), xs(tw)); ed, _ = end_pair(s, tw)
            sham.append(dict(ind=i, timing=timing, window_max_dev=float(ser[: off + 8].max()), took_effect=bool(ser[: off + 8].max() >= TAU_EFF), end_dpair=ed))
    json.dump(dict(rows=rows, an_vs_dh_max_abs_diff=ident, sham=sham, tau_eff=TAU_EFF), open(f"{DATA}/part0/offline_1c.json", "w"), indent=1)
    print("done")

if __name__ == "__main__":
    main()

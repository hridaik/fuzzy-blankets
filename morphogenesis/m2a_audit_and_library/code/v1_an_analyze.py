import sys, os, json, collections
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, scipy.io as sio
from m2a_common import *
from analysis import d_pair
from part0_perturbation_audit import dev_series, xs, end_pair
from r2_analyze import wilson
O = DATA + "/v1_an/"; rows = []
for i in range(20):
    cen = sio.loadmat(f"{M1}/data/census/primary_{i:04d}_N512.mat"); sus = sio.loadmat(O + f"primary_{i:04d}_ANfix_SUSTAINED.mat"); c = i % 8
    sd, sdi = end_pair(sus, cen); smax = float(dev_series(xs(sus), xs(cen)).max())
    for t in ("DEV-SHORT", "DEV-LONG", "ADULT"):
        w = sio.loadmat(O + f"primary_{i:04d}_ANfix_{t}.mat"); tw = sio.loadmat(f"{DATA}/twins/primary_{i:04d}_UNPERT_{'ADULT' if t=='ADULT' else 'FRESH'}_N1024.mat")
        off = 64 if t == "DEV-SHORT" else 332; ser = dev_series(xs(w), xs(tw)); ed, edi = end_pair(w, tw)
        pw = w["positions"][:, -1].reshape(8, 2); pt = tw["positions"][:, -1].reshape(8, 2)
        rows.append(dict(ind=i, timing=t, window_max=float(ser[:off + 8].max()), took=bool(ser[:off + 8].max() >= 0.05), d_pair_twin=ed, relabelled=bool(edi > 0.05),
                         target_changed=bool(np.linalg.norm(pw[c] - pt[c]) > 0.05), sust_dpair_to_unpert=sd, sust_maxdev=smax))
json.dump(rows, open(DATA + "/v1_an/v1_an_results.json", "w"))
for t in ("DEV-SHORT", "DEV-LONG", "ADULT"):
    v = [r for r in rows if r["timing"] == t]
    print(t, "took", sum(r["took"] for r in v), "/20; window max min/med/max", np.round([min(r["window_max"] for r in v), np.median([r["window_max"] for r in v]), max(r["window_max"] for r in v)], 3),
          "end d_pair max", f"{max(r['d_pair_twin'] for r in v):.1e}", "relabelled", sum(r["relabelled"] for r in v), wilson(sum(r["relabelled"] for r in v), 20), "target cell changed", sum(r["target_changed"] for r in v))
sd = [r["sust_dpair_to_unpert"] for r in rows[::3]]; print("sustained AN vs unperturbed d_pair min/med/max", np.round([min(sd), np.median(sd), max(sd)], 3), "(tau_pair v1 0.25) >=0.25:", sum(x >= 0.25 for x in sd))

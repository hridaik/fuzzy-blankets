import sys, os, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *
from scipy.stats import chi2
import r4_noise as R4
tau = json.load(open(os.path.join(SEALED, "thresholds_v2.json")))["tau_pair"]
def pois(k, T, a=0.05):
    lo = 0 if k == 0 else chi2.ppf(a / 2, 2 * k) / 2; hi = chi2.ppf(1 - a / 2, 2 * (k + 1)) / 2
    return [lo / T, hi / T]
out = {}
STEP = 5
for lvl in R4.LEVELS:
    sw = 0; cls = 0; T = 0; rms = []; per = []
    for i in range(4):
        m = load(path("r4", f"primary_{i:04d}_LONG_{lvl}")); n = m["positions"].shape[1]
        slots = []; dmax = 0; trans = 0
        for b in range(0, n, STEP):
            p, s, _ = state(m, b); sl, _ = slot_assignment(p, s); slots.append(sl)
            d = d_pair_pos(p, s, *load_ref()) ; dmax = max(dmax, d); trans += d >= tau
        slots = np.array(slots); ch = int((np.abs(np.diff(slots, axis=0)).sum(1) > 0).sum())
        P = m["positions"].reshape(8, 2, -1)[:, :, 100:]; rms.append(float(np.sqrt((P.std(axis=2) ** 2).mean())))
        per.append(dict(ind=i, bins=n, role_switch_events=ch, samples_with_shape_outside_tau=int(trans), max_dpair_to_ref=float(dmax), rms_fluct=rms[-1], distinct_assignments=len({tuple(r) for r in slots})))
        sw += ch; cls += trans; T += n
    out[lvl] = dict(total_bins=T, role_switches=sw, rate_per_1000=1000 * sw / T, rate_ci=[1000 * x for x in pois(sw, T)], shape_outside_samples=cls, per_ind=per)
    print(lvl, {k: v for k, v in out[lvl].items() if k != "per_ind"})
    for q in per: print("   ", q)
json.dump(out, open(os.path.join(DATA, "v2", "reanalysis_c_long.json"), "w"), indent=1)

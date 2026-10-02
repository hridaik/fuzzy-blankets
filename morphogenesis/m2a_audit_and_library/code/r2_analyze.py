"""R2 analysis: v2 taxonomy (SHAPE x ROLES x TARGETED-CELL FATE), took-effect check, Wilson intervals, relabelling-rate comparison."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *
import r2_withdrawal as R2

def wilson(k, n, z=1.96):
    if n == 0: return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(float(c - h), 3), round(float(c + h), 3)]

def end_state(m, kind):
    pos, sec, _ = state(m); return pos, sec

def end_states_cycle(m):
    return [state(m, -1)[:2], state(m, -2)[:2]]

def analyse(tau, ref_dev=0.05):
    W = R2.W_bins(); rows = []
    for i in range(R2.NIND):
        ind = Ind("primary", i); c = AN_CELL(i)
        U = {"FRESH": load(path("r2", f"{ind.name}_UNP_FRESH")), "ADULT": load(path("r2", f"{ind.name}_UNP_ADULT"))}
        S = {k: load(path("r2", f"{ind.name}_SUST_{k}")) for k in ("DH", "DT", "AN")}
        for kind in ("DH", "DT", "AN", "SHAM_DH", "SHAM_AN"):
            for timing in ("DEV-SHORT", "DEV-LONG", "ADULT"):
                p = path("r2", f"{ind.name}_{kind}_{timing}")
                if not os.path.exists(p): continue
                mP = load(p); twin = U["ADULT" if timing == "ADULT" else "FRESH"]
                off = {"DEV-SHORT": R2.SHORT_OFF, "DEV-LONG": W, "ADULT": W}[timing]
                dev = window_dev(mP, twin, 0, off)
                took = float(dev[: off + 8].max())
                off_abs = 0 if timing != "ADULT" else B_ADULT
                st = stationarity(mP, offset=off_abs)
                Pend = state(mP, -1)[:2]; Uend = state(twin, -1)[:2]
                skey = {"DH": "DH", "DT": "DT", "AN": "AN", "SHAM_DH": None, "SHAM_AN": None}[kind]
                Send = None
                if skey:
                    mS = S[skey]; stS = stationarity(mS)
                    Send = state(mS, -1)[:2]
                shape = shape_outcome(Pend, Uend, Send, tau, nonconv=(st["kind"] is None))
                # sustained twin in a 2-cycle: compare with the nearer phase
                if skey and stationarity(S[skey])["kind"] == "CYCLE2" and shape["shape"] != "NONCONVERGED":
                    ph = end_states_cycle(S[skey]); dS = min(d_pair_pos(*Pend, *q) for q in ph); dUS = d_pair_pos(*Uend, *ph[0])
                    shape = shape_outcome(Pend, Uend, ph[int(np.argmin([d_pair_pos(*Pend, *q) for q in ph]))], tau)
                tgt = c if kind in ("AN", "SHAM_AN") else None
                ro = roles(Pend[0], Pend[1], Uend[0], Uend[1], target=tgt) if st["kind"] is not None else dict(relabelled=None)
                rows.append(dict(ind=i, kind=kind, timing=timing, took_effect=took >= ref_dev, window_max_dev=took, stationary=st, **shape, **ro))
    json.dump(rows, open(os.path.join(DATA, "v2", "r2_results.json"), "w"), indent=0)
    return rows

if __name__ == "__main__":
    tau = float(json.load(open(os.path.join(SEALED, "thresholds_v2.json")))["tau_pair"])
    rows = analyse(tau); print(len(rows), "rows")

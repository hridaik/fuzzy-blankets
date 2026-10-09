"""D5: edge tracking toward the saddle on the basin boundary (class 0 | class 1), for the D4 SHAPE-SWITCH direction global_l4 (global ligand-4 secretion pulse, class-0 base).
State pair (xa: class-0 side, xb: switch side) = full 224-dim continuation states just after the pulse at the 1 % bracket of the D4 threshold. Loop: (i) bisect the interpolation
parameter lam between xa and xb (NB steps; a trial is classified by running CLS bins and testing d_pair to the class-0 reference < THR); (ii) advance the two bracketing states by T bins;
repeat. Cap 200 simulation runs. Reports the edge configuration, roles, beliefs, and (afterwards) the Jacobian eigenvalues at the final edge state."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *
from m2a_common import octave
from m2a_sim import jacobian
CAP = 200; NB = 7; NB0 = 12; T = 8; CLS = 20; THR = 0.25; S0 = 8
IND = Ind("primary", 0); BASE = path("census", "primary_0000_A")
RUNS = [0]; D = os.path.join(DATA, "v2", "d5")
def pth(n): os.makedirs(D, exist_ok=True); return os.path.join(D, n + ".mat")
def run(name, N, cont, events=None):
    RUNS[0] += 1; return sim(pth(name), N, IND, cont=cont, events=events, meta=dict(stage="D5", run=RUNS[0]))
def mix(fa, fb, lam, out):
    octave(f"m2a_mix('{fa}','{fb}',{lam!r},'{out}');"); return out
def cls(f, tag):
    o = run(f"cls_{tag}", CLS, f); m = load(o); m["n"] = 8; pos, sec, _ = state(m)
    return "B" if d_pair_pos(pos, sec, *load_ref()) >= THR else "A"
def vec(m, b=-1):
    pos, sec, v = state(m, b); return np.concatenate([pos.ravel(), sec.ravel(), v.ravel()])
def main():
    r = json.load(open(os.path.join(DATA, "v2", "d4", "dir_global_l4.json"))); hi_a = r["switch"]
    lo_a = max(float(a) for a, v in r["evals"].items() if v["label"] != "SHAPE-SWITCH" and float(a) < hi_a); b0 = int(np.ravel(load(BASE)["b_end"])[0])
    ev = lambda a: [dict(type="sec", cells=list(range(8)), ch=4, amp=a, onset=b0 + 2, w=4)]
    xa = run("xa0", S0, BASE, ev(lo_a)); xb = run("xb0", S0, BASE, ev(hi_a)); hist = []; k = 0
    prev = None
    while RUNS[0] + (NB0 if k == 0 else NB) + 2 <= CAP:
        la, lb = 0.0, 1.0; fa, fb = xa, xb
        for i in range(NB0 if k == 0 else NB):
            lam = 0.5 * (la + lb); mf = mix(xa, xb, lam, pth(f"mix_{k}_{i}"))
            if cls(mf, f"{k}_{i}") == "A": la = lam; fa = mf
            else: lb = lam; fb = mf
        # advance the bracketing pair
        na = run(f"adv_a_{k}", T, fa); nb = run(f"adv_b_{k}", T, fb)
        ma, mb = load(na), load(nb); ma["n"] = mb["n"] = 8; pos, sec, v = state(ma); sl, _ = slot_assignment(pos, sec)
        rec = dict(hop=k, runs=RUNS[0], bin=int(np.ravel(ma["b_end"])[0]), lam=[la, lb], gap_after=float(np.linalg.norm(vec(ma) - vec(mb))),
                   speed_last=float(np.linalg.norm(vec(ma, -1) - vec(ma, -2))), pos=pos.tolist(), sec=sec.tolist(), slots=sl.tolist(),
                   belief_argmax=state(ma)[2].argmax(0).tolist(), belief_max=state(ma)[2].max(0).tolist(), d_ref0=float(d_pair_pos(pos, sec, *load_ref())),
                   d_ref1=float(d_pair_pos(pos, sec, *state(load(path("census", "secondary_0005_A")))[:2])))
        v_now = vec(ma); rec["step_change"] = None if prev is None else float(np.linalg.norm(v_now - prev)); prev = v_now; hist.append(rec)
        json.dump(dict(lo_a=lo_a, hi_a=hi_a, hist=hist), open(os.path.join(D, "edge_hist.json"), "w"))
        print(k, rec["runs"], "gap %.3g speed %.3g d0 %.3f d1 %.3f chg %s" % (rec["gap_after"], rec["speed_last"], rec["d_ref0"], rec["d_ref1"], rec["step_change"]), flush=True)
        xa, xb = na, nb; k += 1
    # Jacobian at the final edge state (midpoint of the final bracket)
    mid = mix(xa, xb, 0.5, pth("edge_final"))
    jacobian(pth("J_edge"), mid, steps=(1e-4, 1e-6))
if __name__ == "__main__": main()

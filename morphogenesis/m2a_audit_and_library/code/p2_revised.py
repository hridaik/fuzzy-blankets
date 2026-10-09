"""REVISED, symmetry-reduced Part 2 library (redirect item 5). Protocol v2; every run is a CONTINUATION from a saved base state with its own unperturbed twin.
Bases (one individual each): C0 = class-0 adult (primary_0000, b=320); C1 = class-1 adult (secondary_0005, b=320);
D16/D32/D64/D128 = primary_0000's developmental states at 0.5, 1, 2, 4 x T_dev. Pulses are indexed by ROLE x ACTUATOR CHANNEL, POSITIVE sign, amplitude 0.03
(declared from the kept amplitude pilot: POS and SEC meet the < 5 % sign-reversal/x2 linearity criterion; GAIN does not (7.3 % sign error) and is kept at the smallest tested
amplitude, flagged). Role r = the cell that holds slot r in the individual's ADULT role map (for D-bases: the cell that WILL hold it; for C1: slot label from the Hungarian match).
Channels: POS x, POS y, SEC l1..l4, GAIN l1..l4 = 10 per cell. Window 192 bins, onset base+2, pulse width 4.
Linearity subset (declared): roles {0, 3, 5} x 10 channels x {sign -1, amplitude x2} on bases C0, C1, D32.
Verification individual: primary_0001 (relabelled; class 0), C0 base, all 80 role x channel pulses."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *
AMP = 0.03; W = 192; LAG = 2; PW = 4
CH = [("pos", 1), ("pos", 2)] + [("sec", k) for k in (1, 2, 3, 4)] + [("gain", k) for k in (1, 2, 3, 4)]
CHN = [f"pos{k}" if t == "pos" else f"{t}{k}" for t, k in CH]
DEV = {"D16": 16, "D32": 32, "D64": 64, "D128": 128}
LIN_ROLES = (0, 3, 5); LIN_BASES = ("C0", "C1", "D32")
def ind_of(base, verif=False):
    if verif: return Ind("primary", 1)
    return Ind("secondary", 5) if base == "C1" else Ind("primary", 0)
def base_file(base, verif=False):
    if verif: return path("census", "primary_0001_A")
    if base == "C0": return path("census", "primary_0000_A")
    if base == "C1": return path("census", "secondary_0005_A")
    return path("p2rbase", base)
def b_of(base): return B_ADULT if base in ("C0", "C1") else DEV[base]
def make_dev_bases():
    ind = Ind("primary", 0); prev = None; t = 0
    for nm, b in DEV.items():
        sim(path("p2rbase", nm), b - t, ind, cont=prev, meta=dict(stage="P2R-base", base=nm)); prev = path("p2rbase", nm); t = b
def cells_by_role(verif=False):
    """role -> cell index, from the ADULT state of the individual (C1: its own adult state)."""
    out = {}
    for key, f in (("C0", path("census", "primary_0000_A")), ("C1", path("census", "secondary_0005_A")), ("V", path("census", "primary_0001_A"))):
        pos, sec, _ = state(load(f)); sl, _ = slot_assignment(pos, sec); out[key] = {int(s): int(c) for c, s in enumerate(sl)}
    return out
def run_id(base, role, ch, mode, verif=False): return f"{'V_' if verif else ''}{base}_r{role}_{CHN[ch]}_{mode}"
def job(base, role, ch, mode, verif=False):
    """mode: p (positive, amp), n (sign -1), x2 (amp x2)"""
    ind = ind_of(base, verif); cr = cells_by_role()["V" if verif else ("C1" if base == "C1" else "C0")]
    sign, mult = {"p": (1, 1), "n": (-1, 1), "x2": (1, 2)}[mode]; typ, k = CH[ch]
    ev = [dict(type=typ, cells=[cr[role]], ch=k, amp=sign * mult * AMP, onset=b_of(base) + LAG, w=PW)]
    out = path("p2r", run_id(base, role, ch, mode, verif))
    sim(out, W, ind, cont=base_file(base, verif), events=ev, meta=dict(stage="P2R", base=base, role=role, channel=CHN[ch], mode=mode, cell=cr[role], verif=verif))
    return out
def twin(base, verif=False):
    ind = ind_of(base, verif); sim(path("p2r", f"{'V_' if verif else ''}{base}_TWIN"), W, ind, cont=base_file(base, verif), meta=dict(stage="P2R", base=base, twin=True, verif=verif))
def tasks():
    T = []
    for b in ("C0", "C1", *DEV): T.append((twin, (b,)))
    T.append((twin, ("C0", True)))
    for b in ("C0", "C1", *DEV):
        for r in range(8):
            for c in range(10): T.append((job, (b, r, c, "p")))
    for r in range(8):
        for c in range(10): T.append((job, ("C0", r, c, "p", True)))
    for b in LIN_BASES:
        for r in LIN_ROLES:
            for c in range(10):
                for m in ("n", "x2"): T.append((job, (b, r, c, m)))
    return T
if __name__ == "__main__":
    make_dev_bases(); T = tasks(); print(len(T), "runs"); run_tasks(T, workers=int(sys.argv[1]) if len(sys.argv) > 1 else 8, label="P2R")

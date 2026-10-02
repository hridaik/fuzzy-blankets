"""R4 (extension, FLAGGED): process-noise conditions. Levels from R0.3. (a) long adult runs: 4 individuals x 3 levels, L=6000 bins from
b_adult (>= 50 x contraction time constant ~9 bins -> 450; 6000 chosen to measure rare role switching); (b) reduced R2: 10 individuals
x 3 levels, ADULT timing, DH and SHAM_DH with the matched noisy twin (same noise realisation)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
import r2_withdrawal as R2
LEVELS = {"L1": 10.6, "L2": 8.4, "L3": 6.0}      # ln G(1).V
LONG = 6000

def nseed(ind, lvl, kind): return 1000 * (1 + ind) + 10 * list(LEVELS).index(lvl) + kind   # kind 0 = long, 1 = reduced R2

def t_long(i, lvl):
    ind = Ind("primary", i); A = path("census", f"{ind.name}_A")
    sim(path("r4", f"{ind.name}_LONG_{lvl}"), LONG, ind, cont=A, GV1=float(np.exp(LEVELS[lvl])), noise_seed=nseed(i, lvl, 0), noise_horizon=B_ADULT + LONG,
        meta=dict(stage="R4", noise=lvl, kind="spontaneous"))

def t_red(i, lvl, kind):
    ind = Ind("primary", i); A = path("census", f"{ind.name}_A"); W = R2.W_bins(); H = W + R2.H_AFTER
    ev = None if kind == "UNP" else R2.events(kind, i, B_ADULT, B_ADULT + W)
    sim(path("r4", f"{ind.name}_RED_{lvl}_{kind}"), H, ind, cont=A, events=ev, GV1=float(np.exp(LEVELS[lvl])), noise_seed=nseed(i, lvl, 1), noise_horizon=B_ADULT + H,
        meta=dict(stage="R4", noise=lvl, pert=kind, timing="ADULT"))

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "long": run_tasks([(t_long, (i, l)) for i in range(4) for l in LEVELS], label="R4-long")
    else: run_tasks([(t_red, (i, l, k)) for i in range(10) for l in LEVELS for k in ("UNP", "DH", "SHAM_DH")], label="R4-red")

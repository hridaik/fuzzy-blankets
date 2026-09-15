"""Stage 6.11B item 8: individual vs. collective/set authority, at each of
the five trigger states, with higher-budget common-random-number rollouts.
Compares: old Stage-6.11 selected set, matched random set, top-K individual,
greedy marginal, beam search -- and computes synergy Gamma(S) = A_S -
sum_j A_j for each. No MCTS.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(CODE_DIR))
import common_611  # noqa: E402,F401

from common_611 import DATA_DIR, L_BOX, dump_json  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402
from intervention_api_611 import near_exterior  # noqa: E402
from blind_pool_611 import nearest_M_pool  # noqa: E402
from authority_v2_611 import (authority_set, synergy, select_actuators_v2,  # noqa: E402
                                greedy_marginal_search, beam_search)

M_PROBE = 12
TAU = D = 4
N_ROLLOUTS = 15
K_MAX = 6           # disclosed reduction from the primary K<=8 cap, for this standalone
                     # method-comparison pass's compute budget (branch_adjudication_611.py's
                     # own repaired branches still use K_MAX=8)
BEAM_WIDTH = 2


def old_set_for(mf, r, z, interior, target_heading, seed):
    from branch_adjudication_611 import old_select_actuators
    return old_select_actuators(mf, r, z, interior, target_heading, seed_offset=seed)["B_C"]


def main():
    trigger_states = json.load(open(AUDIT_DIR / "trigger_states_611.json"))
    mf = ROC.make_flock()
    results = {}
    for seed_str, trig in trigger_states.items():
        seed = int(seed_str)
        print(f"[authority_method_comparison] seed {seed} ...", flush=True)
        r = np.array(trig["r"]); z = np.array(trig["z"], dtype=int)
        interior = np.array(trig["interior_v1"], dtype=int)
        h_star = trig["target_heading"]
        blind_pool = nearest_M_pool(interior, r, L_BOX, M_PROBE)
        base = 7_000_000 + seed

        old_S = old_set_for(mf, r, z, interior, h_star, seed=seed * 1000)
        rng = np.random.default_rng(base)
        rand_S = sorted(int(x) for x in rng.choice(blind_pool, size=min(len(old_S) or K_MAX, len(blind_pool)),
                                                     replace=False)) if blind_pool else []
        topk = select_actuators_v2(mf, r, z, interior, blind_pool, h_star, tau=TAU, d=D, n_rollouts=N_ROLLOUTS,
                                     k_max=K_MAX, seed=base + 1)
        greedy = greedy_marginal_search(mf, r, z, interior, blind_pool, h_star, tau=TAU, d=D, n_rollouts=N_ROLLOUTS,
                                          k_max=K_MAX, seed=base + 2)
        beam = beam_search(mf, r, z, interior, blind_pool, h_star, tau=TAU, d=D, n_rollouts=N_ROLLOUTS,
                             k_max=K_MAX, beam_width=BEAM_WIDTH, seed=base + 3)

        sets = dict(old_selected=old_S, matched_random=rand_S, top_k_individual=topk["S"],
                     greedy_marginal=greedy["S"], beam_search=beam["S"])
        set_eval = {}
        for name, S in sets.items():
            if not S:
                set_eval[name] = dict(S=[], A=None, note="empty set")
                continue
            res = authority_set(mf, r, z, interior, S, h_star, tau=TAU, d=D, n_rollouts=N_ROLLOUTS, seed=base + 4)
            set_eval[name] = dict(S=S, A=res["A"], ci=(res["ci_lo"], res["ci_hi"]), se=res["se"])

        syn = {}
        for name, S in sets.items():
            if 1 < len(S) <= 4:   # synergy on a manageable subset per the task brief
                syn[name] = synergy(mf, r, z, interior, S, h_star, tau=TAU, d=D, n_rollouts=N_ROLLOUTS, seed=base + 5)

        results[seed] = dict(t0=trig["t0"], target_heading=h_star, blind_pool_size=len(blind_pool),
                                sets=set_eval, synergy=syn, greedy_trace=greedy["trace"], beam_trace=beam["trace"])
        print(f"  -> {json.dumps({k: v['A'] for k, v in set_eval.items()}, default=str)}", flush=True)

    dump_json(results, AUDIT_DIR / "authority_method_comparison_611.json")
    print("[authority_method_comparison] done")


if __name__ == "__main__":
    main()

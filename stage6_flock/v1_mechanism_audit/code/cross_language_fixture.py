"""Part A4: deterministic cross-language validation fixture.

MATLAB/Octave are still unavailable in this environment (this session
confirmed: `which matlab octave octave-cli` returns nothing, and
`apt-get install octave` is blocked -- interactive sudo password required,
no non-interactive privilege escalation available). This is documented as a
persisting gap, not silently worked around.

Instead, this script emits a small, fully-specified, deterministic fixture
that a collaborator WITH Octave/MATLAB access can run directly against the
verbatim upstream files in `upstream/` (never modified) and diff against the
`expected_*` fields below (all computed here from the already-validated
Python port -- see PORT_VALIDATION.md's 28 passing tests). Two parts:
  (1) A single-bird decision step (likelihood/EFE/policy-posterior/transition),
      small enough to hand-check every intermediate matrix.
  (2) A small (nn=9, 3x3 lattice) heading-history tensor for the Fiedler
      pipeline (getMarkovBlanketOfFlock.m), with exact expected adjacency,
      Laplacian, first three eigenvalues, and Fiedler partition (flagging
      that the eigenvector itself is only comparable up to a global sign).
"""
from __future__ import annotations

import json
import numpy as np

from common import ROOT, AUDIT_DIR, dump_json
from flock_sim.model import ModelParams, neighbor_R, neighbor_likelihood, transition_matrix
from flock_sim.active_inference import build_model, compute_G, policy_posterior, sample_categorical_rows
from flock_sim.lattice import Lattice
from flock_sim.spectral import build_adjacency, compute_fiedler, classify


def part1_single_bird_decision():
    """Bird i=44 (an interior 10x10 bird, 1-based MATLAB index 45) with a fully
    specified heading and 8 fully specified neighbor headings."""
    params = ModelParams()
    lattice = Lattice(nn=100, nh=8)
    pm = build_model(params)
    i = 44
    z = np.zeros(100, dtype=int)
    # Fully specify i and its 8 neighbors (order: top,down,left,right,topleft,
    # downright,downleft,topright per lattice.py slot convention); everyone
    # else is irrelevant to bird i's own G (verified structurally elsewhere in
    # this audit) but must still be given SOME value to run the full-population
    # step function, so all others are also fixed (heading 0) for determinism.
    neighbor_headings = {  # slot -> heading
        0: 1,  # top -> down
        1: 2,  # down -> left
        2: 3,  # left -> right
        3: 0,  # right -> up
        4: 1,  # topleft -> down
        5: 2,  # downright -> left
        6: 0,  # downleft -> up
        7: 3,  # topright -> right
    }
    nbr_ids = lattice.neighbor_ids[i]
    nbr_slots = lattice.neighbor_slot[i]
    for slot_id, heading in neighbor_headings.items():
        pos = np.where(nbr_slots == slot_id)[0]
        if len(pos):
            z[nbr_ids[pos[0]]] = heading
    z[i] = 2  # bird i's own current heading (should be irrelevant -- see PORT_VALIDATION.md section 1)

    G = compute_G(pm, lattice, z)
    ut = policy_posterior(pm, G)
    Bu = pm.Bu

    # RNG draw #1 (action choice): explicit uniform value, deterministic.
    u1 = 0.37
    cdf1 = np.cumsum(ut[i])
    action = int(np.searchsorted(cdf1, u1, side="right"))
    action = min(action, params.nu - 1)

    # RNG draw #2 (next heading given action): explicit uniform value.
    u2 = 0.81
    cdf2 = np.cumsum(Bu[:, action])
    next_heading = int(np.searchsorted(cdf2, u2, side="right"))
    next_heading = min(next_heading, params.nu - 1)

    return dict(
        bird_index_0based=i, bird_index_1based_matlab=i + 1,
        neighbor_ids_0based={int(k): int(v) for k, v in zip(nbr_ids.tolist(), z[nbr_ids].tolist())},
        own_current_heading=int(z[i]),
        params=dict(nu=params.nu, vm=params.vm, ca=params.ca, fc=params.fc,
                    beta=params.beta, precB=params.precB, precC=params.precC,
                    alpha=params.alpha, spm_beta=params.spm_beta, n_iter=params.n_iter),
        expected_G_row=G[i].tolist(),
        expected_policy_posterior_ut_row=ut[i].tolist(),
        rng_draw_1_action_choice=u1,
        expected_action=action,
        rng_draw_2_next_heading=u2,
        expected_next_heading=next_heading,
        note=("expected_G_row/ut_row use the port's convention G = ambiguity + risk, "
              "policy posterior = spm_softmax(W*G) with W self-tuned (alpha=8, spm_beta=4, "
              "n_iter=4, lambda=0), matching active_inference_bird_control_t.m."),
    )


def part2_fiedler_fixture():
    """3x3 lattice (nn=9), TW=3 fully-specified heading history."""
    nn = 9
    TW = 3
    # z_window[t, bird]: hand-specified so that birds {0,1,2,3} agree often
    # (a "core" block) and birds {5,6,7,8} agree on a different heading
    # (an "exterior" block), bird 4 mixed -- deliberately NOT symmetric so the
    # Fiedler split is unambiguous.
    z_window = np.array([
        [0, 0, 0, 0, 1, 2, 2, 2, 2],
        [0, 0, 0, 1, 1, 2, 2, 2, 3],
        [0, 0, 1, 0, 2, 2, 2, 3, 2],
    ], dtype=int)
    assert z_window.shape == (TW, nn)

    A = build_adjacency(z_window)
    L, eigvals, fiedler_raw, fiedler_norm, l1, l2, l3, gap, ncomp = compute_fiedler(A)
    core1, core2, boundary, active, sensory, labels = classify(A, fiedler_norm)

    return dict(
        nn=nn, TW=TW, z_window=z_window.tolist(),
        expected_adjacency=A.tolist(),
        expected_laplacian=L.tolist(),
        expected_eigvals_ascending=eigvals.tolist(),
        expected_lambda1=float(l1), expected_lambda2=float(l2), expected_lambda3=float(l3),
        expected_eigengap=float(gap), expected_n_components=int(ncomp),
        expected_fiedler_vector_maxabs_normalized_UP_TO_GLOBAL_SIGN=fiedler_norm.tolist(),
        expected_core1_nodes_0based=core1.tolist(), expected_core2_nodes_0based=core2.tolist(),
        expected_boundary_nodes_0based=boundary.tolist(),
        note=("Fiedler vector sign is solver-dependent (LAPACK/Octave `eig` convention); "
              "a collaborator's Octave run may return the sign-flipped vector -- compare "
              "|fiedler_norm - expected| and |fiedler_norm + expected|, whichever is ~0, "
              "per METHODS_AUDIT.md section 10."),
    )


OCTAVE_HARNESS = '''% Cross-language validation harness for stage6_flock (Part A4).
% Run with: octave --no-gui run_fixture.m   (from this directory)
% Requires the verbatim upstream files on the path: addpath('../../../upstream')
% This harness only exercises getMarkovBlanketOfFlock.m (part 2 of the fixture,
% cross_language_fixture.json) since that function is self-contained and does
% not require the full active-inference MDP toolbox that
% active_inference_bird_control.m depends on (part 1 requires SPM12, not
% included here and not verified to be installable in this environment --
% documented as a further, separate gap).
addpath('../../../upstream');
fixture = jsondecode(fileread('cross_language_fixture.json'));
p2 = fixture.part2_fiedler_pipeline;
z_window = p2.z_window;  % (TW, nn), 0-based headings as computed by Python

% getMarkovBlanketOfFlock expects 1-based bird headings starting at 1, and a
% (nt, nn) `sts`-like matrix; the Python fixture already stores 0-based
% headings, so add 1 before calling the upstream function if it assumes
% 1-based category labels (check getMarkovBlanketOfFlock.m's own indexing --
% it operates on equality z_i(t)==z_j(t), which is invariant to a uniform
% +1 shift, so either convention gives the identical adjacency A).
tsign = 1; TW = p2.TW;
[fiedler_vec, A, core1_nodes, core2_nodes, boundary_nodes] = ...
    getMarkovBlanketOfFlock(z_window, tsign, TW);

fprintf('Octave adjacency matches Python (expected all zeros):\\n');
disp(A - cell2mat(p2.expected_adjacency));
fprintf('Octave core1_nodes (1-based): '); disp(core1_nodes);
fprintf('Python expected_core1_nodes_0based (+1 for comparison): ');
disp(p2.expected_core1_nodes_0based + 1);
'''


def main():
    p1 = part1_single_bird_decision()
    p2 = part2_fiedler_fixture()
    out = dict(part1_single_bird_decision=p1, part2_fiedler_pipeline=p2)
    dump_json(out, AUDIT_DIR / "data" / "cross_language_fixture.json")

    harness_dir = AUDIT_DIR / "code" / "octave_fixture"
    harness_dir.mkdir(parents=True, exist_ok=True)
    (harness_dir / "run_fixture.m").write_text(OCTAVE_HARNESS)
    dump_json(out, harness_dir / "cross_language_fixture.json")

    print("Part 1 (single-bird decision):")
    print(f"  expected G row: {p1['expected_G_row']}")
    print(f"  expected policy posterior: {p1['expected_policy_posterior_ut_row']}")
    print(f"  expected action: {p1['expected_action']}, expected next heading: {p1['expected_next_heading']}")
    print("Part 2 (Fiedler pipeline, nn=9):")
    print(f"  lambda1,2,3 = {p2['expected_lambda1']:.4f}, {p2['expected_lambda2']:.4f}, {p2['expected_lambda3']:.4f}")
    print(f"  core1={p2['expected_core1_nodes_0based']} core2={p2['expected_core2_nodes_0based']} "
          f"boundary={p2['expected_boundary_nodes_0based']}")
    print(f"\nOctave harness written to {harness_dir / 'run_fixture.m'}")
    print("MATLAB/Octave still unavailable in this environment (apt-get install octave "
          "blocked: sudo requires an interactive password, no non-interactive privilege "
          "escalation path found). Fixture is ready for a collaborator to run.")


if __name__ == "__main__":
    main()

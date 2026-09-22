# Next-step recommendations

Scoped to what this pass actually found, not a restatement of the full
original task brief. No controller redesign is recommended or implied
here (out of scope per spec §16).

## 1. Close Task D: exact v2 replay

Step 2 disclosed (`identity_validation.md` gap #3) that its field-direction
anchor comparison used v1's centroid as a proxy for v2's, because a full
`LineageTrackerV2` replay of all 5 seeds was out of that pass's time
budget. This remains open. It is a bounded, well-specified task (replay a
single existing tracker class frame-by-frame against already-recorded
trajectories — no new simulation) and should be done before leaning
further on the field-direction readout's anchor-robustness claims for
seeds 502/503.

## 2. Task E: apply `ForwardMaterialTrace611` to Step 1's actual counterfactual branches

Everything in this pass and in Step 2 traces the REAL recorded
trajectories. Step 1's causal adjudication (the duration-vs-selection
finding for seed 503, the abstention findings for 501/502) was computed on
FRESH-CRN counterfactual re-simulations from each seed's trigger state —
a different set of trajectories. Both `seed_501_identity.md` and
`seed_503_identity.md` (Step 2) flag this as an unreconciled gap. Applying
the same frozen forward-trace rule to those counterfactual branches
directly is necessary before any claim like "seed 503's duration effect
was real" can be squared with "seed 503's target physically split" — they
might be findings about different objects, or the split might not even
occur on the counterfactual branches (their own trajectories diverge from
the real run at the point of re-simulation).

## 3. Task F: paired causal re-adjudication, seed 501 first

Highest scientific priority, per the original task brief and this pass's
own findings: seed 501 is the one seed with a real, identity-valid,
persistent physical turn in this pass's evidence. The next step is Task
F §10.1 exactly as specified — no-forcing / historical-schedule-replay /
duration-matched-random branches, from the exact t0=30 trigger state,
using common random numbers verified to actually align (spec's explicit
warning: same seed is not sufficient if intervention changes the number
or order of RNG calls — this must be checked, not assumed, before
comparing branches). This is a genuinely separate undertaking from
identity work: it requires the simulator, not just replay of recorded
data, and its own stop conditions (CRN pairing invalid, historical actions
insufficient to replay the schedule) may bind. Recommend running it as its
own dedicated pass rather than folding it into further identity work.

## 4. A validated split/merge threshold

This pass characterized seed 503's t=47 event in detail (daughter
distance, persistence, non-re-fusion) but explicitly declined to freeze a
numeric physical-split criterion, per spec §6's instruction not to invent
one to fit a single seed. If future work needs a `confirmed_physical_split`
category (not just `likely`), it should be calibrated the same way the
primary Jaccard threshold was: on independent uncontrolled or synthetic
data with known ground truth, BEFORE being applied to seed 503 or any
other control seed's outcome.

## 5. Seeds 500, 502, 504

Not touched by this pass. Step 1 and Step 2's existing characterizations
stand. If Task F's counterfactual-branch work (item 3 above) is done for
501/503 first, the same machinery should extend to these three
relatively cheaply — recommend doing all four remaining Task-F branch
analyses (500, 502, 503, 504) in the same pass as 501 rather than one at a
time, since the CRN-validity and trigger-state-reproduction groundwork is
shared.

## 6. Visualization (spec §12)

Not attempted. The existing `interactive_demo/v2` tab 6 already has v1 and
`ForwardMaterialTrace611` panels (from Step 1/Step 2). Extending it with
the daughter-split view from this pass (`seed503_split_forensics.json`
already has the per-step data needed) and, later, synchronized paired-
branch playback (once Task F produces branches to play) is a reasonable
follow-on, but has no scientific content of its own — recommend doing it
after Task F, once there are real paired branches worth visualizing
side-by-side, rather than before.

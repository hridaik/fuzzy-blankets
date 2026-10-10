# DATASETS_V2.md — NOT DONE (gated)

The specification allows G5 (natural ensembles for L and R, identity-stress dataset, SWITCH dataset, observation levels O1–O3 with two O3 variants, blind package v2) **only after G1–G3 pass**. G3 failed (SWITCH.md: 0 switches in 560 trials) and G1 (b) narrowly failed, so none of these was produced. No `testbed_blind_v2/` exists.

What exists that G5 would reuse (built and tested):
* `code/interface2.py`: experimenter interface (hidden rigid pose, opaque private light-channel mapping to secretion of any of the 6 ligands incl. the 2 memory ligands, receptor gain, migration, pipette/bath, sham with identical RNG consumption — verified bit-identical), observation renderers O1 (tracked cells), O2 (unlabelled clouds), O3 (images) over all 6 secreted ligands with a channel permutation, and the choice of reporter subset (O3 without memory ligands = reporters among the 4 morphological ligands; O3 with one memory ligand = add its permuted index).
* Natural ensembles: the stationary dynamics are measured in G2(e) (σ_h = 1 gives hidden l_i fluctuations; positions/types decorrelate on the v1-like scale); a decorrelation pilot was NOT run.
* NOT built: leak-check extension to the forbidden words (memory, handedness, chirality, situs, slot, belief, plan, fate, template, mirror), DATA_DICTIONARY, split manifest, linear-noise stationary covariance at the L/R fixed points (its Jacobian is available from `eng.jac_flat`; the noise covariance is not computed).
Because the only actuator-relevant hidden effect found is a belief change in the 14–18 cells without morphological evidence (SWITCH.md), a SWITCH dataset with "below / at / above threshold" runs cannot be constructed: there is no threshold.

# Code provenance — historical claims/formulas → source

All entries verified by reading the cited file at the commit recorded in
`README.md`. Where a document (e.g. `METHODS_AUDIT_6_11.md`) already
performed this mapping with `file:line` citations and a verified worked
example, this table cites that document rather than re-deriving the same
mapping — re-deriving it would not add evidence, only duplicate work
already checked field-for-field against production output.

| claim / formula | source file : function/line | actually used online? |
|---|---|---|
| Candidate detection `C_t` (weighted Louvain on torus-distance×heading-agreement) | `stage6_9_translating_collective/code/detect_69.py:52-61`, called from `run_online_control_611.py:167` | yes, every step |
| Lineage update / branching softmax (`score=0.6·dice+0.4·R_F`, temp=4.0, `RETENTION_MIN=0.30`) | `code/lineage_611.py:39-201` | yes, every step |
| `dominant_interior` = argmax hypothesis prob, no margin/entropy gate | `code/run_online_control_611.py:104-107` | yes |
| Predictive boundary `B̂pred` (relational logistic-regression model, greedy forward selection) | `code/predictive_boundary_611.py:121-336` | yes, refreshed every 12 real steps |
| Causal probe `B̂causal` (paired-CRN one-step state intervention, bootstrap CI, τ=0) | `code/intervention_api_611.py:27-94`, `code/probing_611.py:66-75` | yes, refreshed every 8 real steps; **never consumed by actuator selection** (`LINEAGE_FORENSICS_6_11.md` §7) |
| Authority `Â_t` (one-shot-forced τ=4 paired-CRN rollout, top-K no abstention) | `code/intervention_api_611.py:97-149`, `code/control_authority_611.py:23-36` | yes, refreshed every 8 real steps |
| `near_exterior` candidate pool (true R, oracle) | `code/intervention_api_611.py:152-168`, called `run_online_control_611.py:226` | yes — the firewall violation, `METHODS_AUDIT_6_11.md` §2 |
| Actuation: forced heading on actuator set, held until next refresh | `code/run_online_control_611.py:243,276`; `moving_flock_611.py` `step`/`step_cached` | yes |
| Qualification trigger (persistence≥30, size-fraction∈[0.05,0.50] over ≥80% of last 30, cumulative displacement≥3.0R) | `run_online_control_611.py:184-199` (exact condition transcribed, `LINEAGE_FORENSICS_6_11.md` §5) | yes; `thingness_611.py`'s full gate (C,G,L,D,Q) is **dead code**, never invoked by any driver script |
| Original 5-seed labels ("3/5 turned") | `RESULTS_6_11.md` (frozen, not re-derived here) | historical, not re-validated |
| ID-independent rescoring / withdrawal of 501, 502 | `audit/branch_adjudication_611.py`, narrated in `FIVE_SEED_CAUSAL_ADJUDICATION.md` | see `rescoring_provenance.md` |
| v2 comparator tracker (duplicate-coalescing + explicit death state) | `audit/lineage_v2_611.py` (docstring + `RETENTION_MIN_SOFT=0.10`, `R_F_MIN_TRANSPORT=0.50`) | audit-only; never wired into the online production loop |
| Global MAP over branching histories (source of cross-branch overtakes, incl. seed 500 t=20→21) | `code/lineage_611.py:161-167` (branch softmax) + `run_online_control_611.py:104-107` (bare argmax readout) | yes — this IS the production mechanism, not a bug introduced by any audit tool |
| Blind nearest-20 candidate pool, 100% recall | `audit/blind_pool_611.py` (`nearest_M_pool`), results in `audit/BLIND_POOL_AUDIT.md` §2 | **audit-only**; never substituted into the production online loop |
| Repaired authority `A_S(τ,d)`, top-K with abstention (`ci_lo>0`) | `audit/authority_v2_611.py:33-51,92-106` | audit-only |
| Intervention-duration mismatch (estimator forces once, controller holds 8 steps) | `METHODS_AUDIT_6_11.md` §1.5, quantified `audit/AUTHORITY_AND_SET_EFFECT_AUDIT.md` | confirmed defect in production run |
| Forced top-K, no abstention (old) | `code/control_authority_611.py:23-36` (plain sort, no floor) | yes, production |
| True interaction radius `R` used in candidate pool | `code/intervention_api_611.py:152-168` (`mf.R`) | yes, production — firewall violation |
| Seed 503 matched-random-exterior comparator | `audit/branch_adjudication_611.py` branch `matched_random_blind_exterior` (`branch_adjudication_611.py:228-233`) | audit-only, run once per seed for comparison |

## Formulas recovered exactly (handoff had corrupted/truncated versions)

- **`R_retain` (this audit's "R_old")**: `|prev ∩ cand| / |prev|`
  (`lineage_611.py:56-60`, cited `METHODS_AUDIT_6_11.md` §1.2, item 1).
- **`R_purity` (this audit's "R_new")**: `|prev ∩ cand| / |cand|` (same
  citation).
- **`R_F`**: `similarity(d_transport, d_norm)` where `d_transport` is the
  post-bulk-alignment field distance (`identity_69.estimate_translation`)
  and `d_norm` is a fixed-at-birth normalizer (field distance to an
  independent random same-size subset) — `lineage_611.py:107-110`,
  `identity_69.py:100-102`.
- **Branch score**: `0.6·dice(prev,cand) + 0.4·R_F`, softmax temperature
  4.0 (`lineage_611.py:151,161-163`).
- **`A_j` (old, one-shot authority)**: `E[H*_{t+τ}|do] − E[H*_{t+τ}|base]`,
  forced only at step 0 of a τ-step rollout (`intervention_api_611.py:97-149`).
- **`A_S(τ,d)` (repaired, 6.11B)**: same expectation-difference form, but
  forced for `d` consecutive steps of a τ-step rollout, `d=τ=4` used as the
  primary repaired setting (`audit/authority_v2_611.py:33-51`,
  `branch_adjudication_611.py:39-46`'s comment explains why `d=4` not `d=8`
  was chosen — a disclosed compute-budget simplification, not a silent
  substitution).
- **Field-direction (ID-independent) readout**: see `rescoring_provenance.md`
  for the exact formula and citation (`branch_adjudication_611.py:164-178`).

## Not actually used vs. present-but-inactive vs. added later

- `thingness_611.py` (spatial connectivity / thingness gate, `n_components`,
  `Q`, `D`, `passes_gate`): **present, unit-tested, never invoked by any
  driver script** (`LINEAGE_FORENSICS_6_11.md` §5, confirmed by grep across
  `code/*.py` in that pass). Not used in the reported Stage 6.11 result at
  all, despite being described in its own docstring as "the scientific
  object gate."
- `lineage_v2_611.py`, `authority_v2_611.py`, `blind_pool_611.py`,
  `branch_adjudication_611.py`: **all added later**, as part of the 6.11B
  audit pass, never wired into `run_online_control_611.py`'s production
  loop. The original 500–504 labels in `RESULTS_6_11.md` were produced
  without any of this code existing.

# Stage 6.12 — Final Findings

**Scope reminder**: 9 states (6 development, 3 holdout), full 4×6 K,d grid
(24 cells), 3 random sets × 2 physics streams/cell in Phase A (1,296
intervention rollouts), one frozen search budget (K=4,d=8) for Phase B/C
(15-set development search, 6-set + S* holdout confirmation on 5 fresh
streams), 3-state pool sensitivity check. This is a heavily
compute-reduced run of the task brief's design — see `README.md`'s
reduction table. Every finding below should be read at that precision, not
as a definitive closure of the underlying question.

## 1. Does sustained random exterior forcing generally move valid flocks?

**Not demonstrably, at the tested budgets and precision.** Pooled across
all 216 (state,K,d) cells, `G_sus` = +0.0011 (90% CI [-0.0083, +0.0107]) —
indistinguishable from zero. Individual budget cells range from about
-0.025 to +0.041 in mean effect (`READINESS_MAP.md`), with no consistent
sign pattern and no budget that stands out as reliably positive across
states. This is a materially different (more negative) finding than Stage
6.11's seed-501/503/504 cases, which DID show demonstrable positive
schedule effects for specific historical trajectories — Stage 6.12 samples
fresh, generic states rather than the hand-picked seeds 500–504, and finds
the generic answer is much weaker.

## 2. Does actuator identity explain reproducible outcome variance?

**Weakly and inconsistently, before holdout confirmation; not after.**
Between-set variance in Phase A is generally small relative to the
per-cell noise, with the largest values clustering at short-duration,
larger-K budgets (`K8_d1`: 0.022, `K2_d4`: 0.017). At the frozen K=4,d=8
budget specifically, this signal did NOT survive held-out confirmation
(see Q4).

## 3. At which K,d budgets is selectivity largest?

Development-only between-set variance is largest at `K8_d1` and `K2_d4`
(`READINESS_MAP.md`), but **this stage only ran the full search-and-confirm
pipeline (Phase B/C) at one frozen budget (K=4,d=8)**, chosen ex ante, not
from this observation — per the task brief's own prohibition on searching
development data for a favorable budget before running holdout
confirmation. We therefore cannot say whether `K8_d1` or `K2_d4`'s larger
development-only variance would survive confirmation; that is an open
question for a follow-up run (`NEXT_STAGE_RECOMMENDATIONS.md`).

## 4. Does best-found intervention outperform random intervention on held-out physics streams?

**No, not reliably, at K=4,d=8.** `G_sel` (mean holdout `S_star` J - median
random holdout J) is small in both directions across all 9 states: dev
mean +0.0045 (5/6 positive, but one state at -0.106 — a development set
that reversed sharply on holdout); holdout mean +0.0010 (2/3 positive, one
at -0.017). No state showed the large, clean separation (`best_found >>
random`) that would indicate genuine selective addressability
(`SELECTIVITY_ANALYSIS.md`).

## 5. How often does identity remain valid?

**Very often.** Phase A identity-valid fraction was 0.94–1.00 in every
cell; pooled across 1,296 rollouts, only 17 (1.3%) actually drove `V` to 0.
Every Phase-C holdout evaluation of `S_star` (45 rollouts: 9 states × 5
streams) remained identity-valid (`IDENTITY_AND_DISRUPTION.md`). **Identity
failure does not explain the near-zero behavioral effect sizes above** —
the target survives forcing; it mostly just doesn't move much.

## 6. Where do split/loss/disruption occur?

Splits are common as ADVISORY flags (34.4% of rollouts) but rarely
downgrade strict validity — `ForwardMaterialTrace611` continues on the
larger daughter by absolute retained count. True loss/unresolved events are
rare (~1.7% combined). No budget or state stood out as substantially more
disruption-prone than others in this sample (`IDENTITY_AND_DISRUPTION.md`).
Target size drifted upward on average (+25%, 32.4→40.5 mean birds), an
artifact of the split-continuation rule, not evidence of successful
recruitment (`COLLATERAL_ANALYSIS.md`).

## 7. Is there evidence for the hypothesized inert → selective → generic/saturated budget progression?

**No.** `READINESS_MAP.md`'s by-budget table shows no monotone trend in
either `G_sus` or between-set variance as `K` or `d` increase; if anything
the pattern is closer to flat-with-noise than to any of the three named
regimes emerging cleanly at any point in the grid. This null result is
itself informative — it argues against assuming the hypothesized
progression exists in this system at this operating point without further,
higher-precision evidence.

## 8. How frequent are selectively addressable states in untouched holdout worlds?

**Zero of 3, on the primary frozen budget, at this precision** — no holdout
state showed a `G_sel` large enough to distinguish from the noise floor
implied by `N_HOLDOUT_STREAMS=5`. Given the small holdout sample (n=3),
this cannot be read as "selectivity never occurs in holdout worlds," only
as "no holdout state in this small sample showed it at this budget and
precision."

## 9. What observable/geometric properties distinguish selective states and successful actuator sets?

The clearest (exploratory) signal is `MECHANISM_ANALYSIS.md`'s finding that
successful rollouts (`J>0.3`, 34/1,296 = 2.6%) have roughly 10× more
sustained actuator-target contact (cumulative contact edges, unique
coverage) than unsuccessful ones, while INITIAL (`t0`) actuator-target
distance is only weakly different between the two groups. This suggests
sustained-contact persistence during forcing, not static nearest-neighbour
distance at selection time, is the more relevant property — a lead for the
next authority estimator, not a validated rule (never used to filter this
stage's own actuator-set sampling).

## 10. Does modest physics knowledge improve the intervention landscape?

**No large sensitivity detected**, on a small predeclared 3-state check
comparing the primary position-only nearest-20 pool against the
physics-assisted true-R oracle pool at K=4,d=8: neither pool consistently
outperformed the other, and the one state with a large effect size showed
the same qualitative pattern (strong negative) in both pools
(`PHYSICS_POOL_SENSITIVITY.md`). This reinforces Q9's contact-persistence
lead over a "better withheld-radius pool" explanation.

## 11. What does this imply for the next learned authority/control architecture?

**Do not yet build or tune a learned authority estimator against this
intervention class and operating point.** The prerequisite finding this
stage was designed to establish — "does a nontrivial actuator-selection
problem exist here?" — did not receive a clear "yes" at the precision
achieved. The honest reading is closest to **Endpoint C (little
controllability) shading into Endpoint B (weak/inconsistent generic
susceptibility)**, not Endpoint A. This is provisional, not definitive: the
Monte Carlo budget here is far below the task brief's nominal design, and
a full-precision re-run of this exact pipeline (same code, larger
`N_SETS`/`N_STREAMS`/state counts) is the single highest-value next step
before any control-architecture decision is made — see
`NEXT_STAGE_RECOMMENDATIONS.md`.

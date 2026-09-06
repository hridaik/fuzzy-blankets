# Figure index

Every figure is generated programmatically by `figN.py` from `core.py`/`part_*.py`
outputs, with underlying numeric data saved alongside in `data/`. Palette: interior
{1,2,3}=blue `#0072B2`, boundary {4,5}=orange `#E69F00`, exterior {6,7,8}=bluish-green
`#009E73` (Okabe-Ito colorblind-safe set), consistent across all panels.

| Figure | Claim it demonstrates | Data file |
|---|---|---|
| **Fig 1** — Benchmark anatomy | Shows the three graphs under test (base, ε-perturbed, ambiguity) on identical node coordinates, so the reader can see exactly what structural question each one poses. | `fig1_data.npz` |
| **Fig 2** — Boundary complexity vs. leakage | For fixed I={1,2,3}, the Pareto frontier over all 32 candidate boundaries is exactly ∅→{4}→{4,5} at ε=0 and ∅→{4}→{4,5}→{4,5,6} at ε=1 — verified programmatically, not hand-labelled. | `fig2_data.csv` |
| **Fig 3** — Exact blanket → graded (ε sweep) | The exact CMI and the weak-leak Hessian approximation ½L_H agree almost everywhere but diverge as ε→1; 2L/L_H→1 only as ε→0, shown explicitly rather than asserted. | `fig3_data.csv` |
| **Fig 4** — Observer/representation dependence | The *same* generating system yields different apparent blanket quality (0, 0.0033, 0.0219 nats) depending only on which node is hidden — a representation effect, not a change in the underlying physics. | `fig4_data.csv` |
| **Fig 5** — Finite-sample inference (4 panels) | Raw plug-in CMI is upward-biased at small n (panel A); the exact Wishart bias correction removes this bias with only its geometric std remaining (panel B); the analytic bias formula β_pqr(n) tracks the empirical raw bias (panel C); and the confidence-certified boundary-recovery probability grows with n but is *not* guaranteed even at moderate n (panel D). | `part_c_bias_table.csv`, `part_e_selection_table.csv` |
| **Fig 6** — Graded membership as selection stability | m_k(δ) — the frequency a node appears in the certified minimal boundary — stabilizes as n grows, but is explicitly a statistical-selection-stability statistic, not an intrinsic property of a node; note the non-monotonic/rising behavior for node 6 at ε=1, δ≤0.025 (reflecting the {4,5,6} minimal blanket becoming easier to certify with more data), which was not forced to be monotone. | `part_f_membership_raw.csv` |
| **Fig 7** — Structural ambiguity ≠ sampling uncertainty | All 9 minimum separators of the ambiguity graph achieve *exact* L=0 with infinite data; this is a structural non-identifiability, and the per-node occurrence count (panel B) must not be read as ranking node "correctness." | `fig7_data.csv` |
| **Fig 8** — Static blanket vs. finite-time dynamics | Three logically distinct objects, plotted side by side: (A) finite-horizon predictive permeability P_τ is nonzero for finite τ even at q=0; (B) the direct dynamical coupling J₃₆/J₆₃ grows linearly with q; (C) the *instantaneous* blanket leakage stays exactly 0 for every q. Conflating any pair of these would be a benchmark-design error. | `fig8_data.csv` |
| **Contact sheet** | One-page thumbnail grid of all 8 figures for rapid visual QC. | — |

All figures were checked against the corresponding numerical tables before being
accepted (see `benchmark_stage2_report.md` for the assertion results); none of the
plotting ranges were adjusted to hide an unexpected result — unexpected results
(the ε=1, δ=0.05 tie in Fig 2/5D; the imperfect bootstrap coverage visible if Fig 5
panel widths are cross-referenced against `part_d_coverage_table.csv`) are reported
in the main text, not edited out of the figures.

# OPEN_QUESTIONS.md (M2a, Part 0 only)

1. **AN re-run approval** (AUDIT_M1.md): re-run the 80 AN runs with a real single-cell target? Until then M1's AN rows should be treated as DH replicates.
2. **Ramp protocol for Parts 1–2.** The census phenotype is the fixed point at s(t=1)=0.865, reached by ramp tracking. Freeze the ramp at 0.865 (autonomous fixed point; linear-response operator well defined) or use the absolute-bin ramp (closer to M1, but "return to stationarity" is then ramp-limited)? PROVISIONAL recommendation: frozen for S_FP, absolute-bin for S_DEV.
3. **Zero process noise.** `G(1).V=exp(16)` makes the engine deterministic. Keep it (matches published code) or add declared process noise so the blind package has intrinsic variability? Changes what the blind analysis can learn.
4. **Role assignment as an outcome.** Role relabelling after perturbation is common (155/180 withdrawal, 58/60 sham) and invisible to d_pair. Should Part 1 classes include it? (I would add it.)
5. **M1 kick/ADULT protocol** restarts the ramp at s≈0 and uses one distinct base state across individuals. Whether to keep this for comparability or replace with in-run, ramp-continuous kicks (needs the state restored with abs ramp).
6. **Residual near-miss 0.05–0.10 beyond belief-weighting** (0.5) not analysed. PROVISIONAL.
7. Why Part 0's absolute-ramp d_target (0.277 at bin 2048) is still above M1's per-cell threshold was not tested at larger N (ramp saturates at s→1). NOT DONE.
8. 16-cell cost and early-stopping behaviour not piloted. NOT DONE.
9. Viewer exemplars for the Part 0 controls (Part 4) NOT DONE; only static figure `figures/part0_merge_and_stationarity.png`.

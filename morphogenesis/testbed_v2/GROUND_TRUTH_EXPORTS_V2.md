# GROUND_TRUTH_EXPORTS_V2.md — partially available; full export NOT DONE (gated with G5)

Available now (white-box, in code):
* `engine2.diagnostics(state)`: per-cell q (24 places), ρ, Δ_i (evidence for L over R), E_ik(L), E_ik(R) — i.e. the "per-frame q, rho, energies" requested.
* World2 frames (`World2.run(save_every=...)`) store x, c, d (the two memory ligands), μ, l, alive, cell_id; the event log lives in `World2.events` (remove / insert / replace / extrude / cut / fuse, with permanent unique ids); `Experiment2.hidden()` returns events, hidden pose, dose, private actuator map.
* Influence/Jacobian: `eng.jac_flat(state)` gives the full Jacobian (autodiff) at any state; used for the G1 rate analysis. Per-pair influence-norm export (v1's `influence_norms`) was NOT ported.
NOT done: file export (obs/hid npz tiers with the audit-gated loader), linear-noise stationary covariance and its condition number (the L and R fixed points are non-degenerate: the Jacobian has 3 rigid zero modes + 24 neutral logit-mean modes only — the l block and d block are stable), because G5 is gated.

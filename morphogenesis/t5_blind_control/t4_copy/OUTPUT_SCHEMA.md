# OUTPUT SCHEMA (Part H)

One file per run: `outputs/<run>.json.gz` (gzip JSON, 513 files: 340 development + 173 held-out, all produced by the frozen code; `config_hash` = `FROZEN_HASH.txt` = sha256 87dafdfc57bc...bea2e). `outputs/GLOBAL_SUMMARY.json` holds the global tables. Time `t` is the observation time of the frame; `k` the frame index of that level's own record (O3 frames are every 2nd frame in P* runs).

```
run, condition, arm, split, group, body_id, onset, frame_interval, config_hash
levels: { "O1" | "O2" | "O3a" | "O3b": {
   level, channels,                                  # channel names = O1 column names (c0..c6) in file order
   summary: { n_frames, n_organisms_total, n_founders, frac_founders_V, frac_founders_V_conservative,
              events:{TYPE:{n, first_t}}, state_change_times:[...], first_state_change_t }     # see issue B1 for state_change_times
   organisms: { "<id>": { origin: founder|split_child|birth, parent, born_k, last_k, alive_at_end,
                          V, V_conservative,                                      # whole-run verdicts (strict / conservative)
                          flags:{TYPE:count}, unresolved_any,
                          axis_first_fail_k:{material,count,cohesion,shape,pattern}, axis_fail_any:{...},   # per-axis verdicts before collapsing
                          state_changes:[{k,t,frm,to}]  (change-detection times; frm/to = state label, -1 = out of distribution),
                          state_first, state_last } },
   frames: [ { k, t, n_free,                                   # n_free = observed points not in any organism (O1/O2)
       organisms: [ { id, members, n, n_pixels,                # members: O1 cell ids; O2 tracker ids; O3: [] (cells not resolvable; n_pixels = foreground pixels)
                      centroid:[x,y], e1:[x,y], e2:[x,y],      # body frame: e1 signed major axis, e2 = rot90(e1)
                      axis_conf, sign_conf, sign_src,          # axis_conf = 1 - lambda_min/lambda_max; sign_conf in [0,1]; sign_src = observable | field_asym | continuity | weak | none
                      unresolved,                              # identity flagged UNRESOLVED at this frame
                      C1:{J_init, D_init, J_prev},             # material layer (O3: pixel-overlap proxy)
                      C2:{n, n_dev, mst_max, ncomp, shape_dev, pattern_dev, procr_rot?, procr_refl?},   # structural layer (procr_* only O1/O2)
                      axis_pass:{material,count,cohesion,shape,pattern},      # per-axis envelope verdicts this frame
                      V_running, V_conservative_running,       # causal: still inside the envelope since birth (and no SPLIT/MERGE/UNRESOLVED so far)
                      C3:{label, posterior, ood},              # label: 0..k-1 state, -1 out of distribution, -2 organism < 12 cells
                      desc:{...} } ],                          # all body-frame descriptors (46 at O1) of the raw frame
       events: [ {type, org, t, k, ...} ] } ] } }              # SPLIT, SPLIT_CHILD, MERGE, END_MERGED, EXTRUSION(cell), ARRIVAL(cell,new), LOSS(cell), BIRTH, END
```
Event types and geometric definitions: TRACKING.md. Flags are reported alongside identity and never counted as continuity or success. Organism ids are internal (stable within a run, not comparable across levels). Change-detection: `organisms.<id>.state_changes` (declared latency in STATES.md).
Definitions of V (strict) and V_conservative (no SPLIT/MERGE/UNRESOLVED): IDENTITY_LAYERS.md.
`outputs/GLOBAL_SUMMARY.json`: `states` (number of states per level with evidence 1 vs k for every descriptor family, online-estimator performance), `leakage` (dev and held-out tables), `directed_influence`, `anticipation`, `natural_validity`, `tracking_consistency`, `frozen_code_sha256`.
Every primary output at frame k uses frames <= k only (test: `tests/test_t4.py::test_causality_stage1_and_stage2`); `V`, `V_conservative`, `alive_at_end` and the `organisms` dict are end-of-run summaries (offline by definition); they are not used by any per-frame field.

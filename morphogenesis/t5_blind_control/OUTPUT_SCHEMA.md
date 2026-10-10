# OUTPUT_SCHEMA
Per episode (all arms), file `episodes/ep_<id>.json` (development) or `episodes_heldout/ep_<id>.json` (held-out); `<id>` = the environment's episode id (match to the hidden logs).
```
episode, seed, pool, sham(bool), sham_of(episode id|null), tag (H_ctrl/H_twin/H_sham/H_random/H_fixed/H_whole/H_whole_dm | b1.. dev tags)
requests: [{t, level:'O1'}]            every observe call (all at O1; one per frame)
actions:  [{t, label, mask{type,xy,radius}, body_frame[p,q], radius, amp, dur, ramp, accepted, dose, cells, reason}]
frames:   per observation: t, xy, lev(c0,c4,c5,c6), ids, state(S+/S-/TRANS), state_sure, p_plus, p_conf, u[c4-c5, c0 dipole] (10-tu median),
          n, mst_max, s1, s2, ncomp, events[], centroid, e1, sign_conf, material_J, material_ok, geometry_ok, pattern_ok, geometry_warn,
          pat_dz, s1_rel, s2_rel, V_body, V_body_conservative, V_body_now
decisions: [{t, action in plan/act/escalate/commit/uncommit/abort/none, reason, amp?}]   controller only
summary:  success, reason, n_pulses, dose, t_first_action, t_last_end, t_success, time_to_success, V_body, V_body_conservative, events, end_state, budget at end
budget:   final environment budget block
```
`logs/heldout_summary.jsonl`: one row per (dish, arm) with success, dose, cells, V_body, V_body_conservative, events, end_state, u_end, episode id; `logs/heldout_eval.json`: all tables. Development sysid: `logs/b1_results.jsonl`, `logs/b2_results.jsonl`, `logs/b3_dev*.jsonl`. Frozen hashes: `MONITOR_HASH.txt` (monitor only), `FROZEN_HASH.txt` (monitor + rig + controller + run script + both configs).
Success definition, hold, and limits: CONTROLLER.md.

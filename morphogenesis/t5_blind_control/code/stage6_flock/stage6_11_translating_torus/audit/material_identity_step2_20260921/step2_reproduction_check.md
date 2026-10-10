# Step-2 preliminary: reproducing Step-1 findings (task §2)

Before implementing anything new, the task requires confirming Step-1's
findings reproduce from the checked-out repository state. Checked directly
(commands run interactively, outputs quoted verbatim):

## Material-retention time series, seeds 500–504

`../evidence_recovery_20260921/data/material_retention_seed{500..504}.csv`
exist, are non-empty, and were re-read (not re-generated) for this task —
confirmed readable, correct row counts (107/76/76/81/93 for 500/501/502/503/504)
matching `../evidence_recovery_20260921/README.md`'s reported figures.

## Known zero-overlap transitions

Re-queried directly from the existing CSVs (not re-derived):
- seed 500: t=4(~1 boundary), 21, 39 — confirmed.
- seed 501: t=32 — confirmed (inside control window 30–52).
- seed 502: t=32, 52, 68 — confirmed.
- seed 503: **t=35, t=47** — confirmed. **t=47 (i.e. the t=46→47 transition)
  is present and flagged, exactly matching this task's corrected
  observation.**
- seed 504: none — confirmed (cleanest lineage of the five).

## Seed 503 around t=46→47, explicit confirmation

```
$ python3 -c "... material_retention_seed503.csv rows 40-50 ..."
46 control 11 37 1.0 0.8918918918918919 0.8918918918918919 False False
47 control 29 31 0.0 0.0 0.0 True True
48 control 29 31 1.0 1.0 1.0 False False
```
`map_hid` switches 11→29 exactly at t=47, `R_old_displayed=R_new_displayed=
jaccard_displayed=0.0`, `overlap_zero_displayed=True`,
`flagged_unusual_transition_lineage_forensics=True`. **This is the transition
the task's corrected observation refers to, and it reproduces exactly.**

## Target/control/release timing, all seeds

Re-read from `interactive_demo/v2/data/tab6_translation.json`'s `events`
lists (unchanged since Step 1):

| seed | qualify t | release t | end t |
|---|---|---|---|
| 500 | 61 | 84 | 108 |
| 501 | 30 | 53 | 77 |
| 502 | 30 | 53 | 77 |
| 503 | 35 | 58 | 82 |
| 504 | 47 | 70 | 94 |

Matches Step 1 exactly.

## Candidate sets at relevant frames

Verified via `seed503_t46_t47_forensics.py` (this task's own script, §3):
the real, unmodified `detect_69.propose` was re-run against the recorded
`(r,z)` for seed 503 at t=46 and t=47 and produces a candidate list
consistent with `../evidence_recovery_20260921/../lineage_forensics_611__seed503__candidates.csv`'s
already-recorded per-candidate scores (14 candidates at t=47, matching
sizes `[45,41,39,36,32,31,28,28,25,24,24,18,16,12]` against that CSV's
`cand_idx` rows) — **no discrepancy found.**

## Conclusion

**All checked Step-1 findings reproduce from the current repository state.**
No stop condition triggered. Proceeding to §3 (seed 503 deep forensics).

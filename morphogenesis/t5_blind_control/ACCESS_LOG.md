# ACCESS LOG (T5)
Allowed: testbed_blind_v3/, t4_blind_identity/, live client + CLIENT_API.md, ../stage6_flock/, ../core.py, ../benchmark.py.
- `ls testbed_blind_v3 t4_blind_identity` (names only)
- `ls -d ../stage6_flock ../core.py ../benchmark.py` (existence only)
No forbidden file opened so far.
- Read: data_v3/DATA_DICTIONARY.md, live/CLIENT_API.md, live/live_client.py, LEAK_CHECK.md, heads of split_manifest/catalog/treatments/ess_observable; t4 README, METHODS, OPEN_QUESTIONS.
- Copied allowed material into t4_copy/, data_v3/, live/, code/ (core.py, benchmark.py, stage6_flock/). Not read in full yet.
- `find / -name ready.json` (filename search only) listed 4 stale/foreign files (3 under /tmp/pytest-of-hkhurana/, 1 under another Claude session's scratchpad). NOT opened, NOT used: they were not issued to this task, and may point at a server whose provenance/held-out lock state I cannot verify.
- No forbidden file opened.
STATUS: blocked on Part 0 live smoke test - no rig server / ready.json was provided for this task.
- Read rig/ready.json via live_client only (user-provided). Sealed dir not touched.
- smoke test run (code/smoke.py), 1 dev episode
- Part A: reading natural dev runs O1 (calibration bodies 2100-2105, validation 2106-2111); package heldout natural dishes (2400-2405) featurised too but NOT to be used until post-freeze
- A5: MONITOR_CONFIG.json frozen 2026-10-10T04:49:17+02:00 (identical numeric content to draft used in B1/B2 sysid; code unchanged)
- dev panel seeds for B3 tuning: S+ 5012 5013 5014 5016 5017 5022 ; S- 5006 5007 5008 5009 5011 5015 (dev pool only)
- B3 dev: ctrl_v0 aborted on a 95%-level geometry_warn (spurious natural fluctuation, 1 of 3 dishes): abort rule changed to hard envelope only. v0 results kept in logs/b3_dev_v0_warnabort.jsonl
- B4: CONTROLLER_CONFIG.json + FROZEN_HASH.txt written 2026-10-10T05:50:05+02:00; held-out run next (single run)
- PART C launched 2026-10-10T05:51:59+02:00: freeze(hash) called by run_heldout.py; single run
- PART C finished 2026-10-10T06:49:40+02:00; evaluate.py is reporting-only
- final: docs written; episodes_dry removed (dry-run, development pool); no forbidden access

# ACCESS_LOG
Paths read/listed outside the workspace (all within the allowed set):
- morphogenesis/testbed_blind_v2/ (directory listing; DATA_DICTIONARY.md, LEAK_CHECK.md, head of split_manifest.json, catalog.csv, treatments.json)
- stage6_flock/ (top-level directory listing of names only; no status/closure file opened)
- core.py, benchmark.py (copied; to be read from workspace copies)
Copied into workspace: data/ (full package), flock_code/ (core.py, benchmark.py, stage6_flock/**/*.py excluding data/ and upstream/).
No forbidden file opened. Note: the first shell listing of stage6_flock showed names of status/synthesis .md files; none were opened or copied.
- Removed copied final_translating_flock_closure/ (name matches *closure*; never opened).

## Update at completion
Reads of workspace copies (no outside reads after the first listing): `flock_code/core.py`, `flock_code/benchmark.py` (plug_in_L region), `flock_code/stage6_flock/stage6_8_dynamic_interactions/code/louvain.py` (copied verbatim to `t4/louvain.py`), `.../tracker.py` (first 70 lines), grep listings of function names across `flock_code/`.
Data read: `data/DATA_DICTIONARY.md`, `LEAK_CHECK.md` (package files, included in the copy), `catalog.csv`, `split_manifest.json`, `treatments.json`, `runs/*.npz` (development runs during development; held-out runs only by the frozen pipeline after the freeze).
Outside-workspace reads: only the first listing/`du` of `morphogenesis/testbed_blind_v2/` and a top-level `ls` of `stage6_flock/` (names of status/closure documents were visible in the listing; none was opened). `git status` output at session start listed untracked sibling directories by name (testbed_v2, testbed_v3, testbed_blind_v1/PIPELINE_TEST_ONLY.md) - names only, nothing opened.
**No forbidden file was opened.** Held-out outputs were first viewed after `FROZEN_CONFIG.json` and `FROZEN_HASH.txt` were written; code hash verified unchanged at the end (`post_freeze/verify_hash.py`: MATCH).

# LEAK_CHECK.md

Scanner `code/leak_check.py` (kept outside the package), run over **every file** in this package (2488 files; extensions: none: 1, .json: 2, .jsonl: 1, .md: 2, .npz: 2482).

Checks: (1) every text file against a list of forbidden strings (vocabulary of the cells' internal workings, derived quantities, reference-shape wording, literature and software references, treatment mnemonics); the list is kept outside the package so as not to put those words in it; 45 patterns, case-insensitive; (2) manifest and split-file keys against a strict whitelist; (3) all labels against the opaque-label patterns; (4) array names in every `.npz` against a whitelist; (5) every position frame (891,632 frames) compared with the reference arrays, permutation-invariantly, tolerance 1e-4; (6) file extensions.

**Result: PASS — no findings.**

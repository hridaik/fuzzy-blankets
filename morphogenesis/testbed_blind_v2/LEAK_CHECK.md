# LEAK_CHECK.md — automated scan of testbed_blind_v2

Scanned 2056 files (4 text, 2052 npz) with `code/leak_check3.py`.

**Forbidden vocabulary (regex, case-insensitive):** `memory`, `handed`, `chiral`, `situs`, `lateral`, `reporter`, `slot`, `belief`, `\bplans?\b`, `\bfate`, `template`, `mirror`, `state[ _-]?[ab]\b`, `\bstates?\b`, `mechanism`, `enantio`, `latent`, `hidden`, `posterior`, `softmax`, `logit`, `zeta`, `orbit`, `\brole`, `\bmu\b`, `receptor`, `\bgain\b`, `migration`, `\bbias`, `precision`, `free.?energy`, `attractor`, `ground.?truth`, `jacobian`, `ratiometric`, `paracrine`, `quorum`, `toggle`, `\bL-form`, `\bR-form`

**Allowed array keys:** {"O1": ["cell_id", "frame_ptr", "level", "t", "xy"], "O2": ["frame_ptr", "level", "t", "xy"], "O3a": ["image", "t"], "O3b": ["image", "t"]}

**Structural checks:** opaque condition/arm labels only; O2 rows shuffled relative to O1 and carrying no ids; cluster pose randomised across runs (centroid sd per axis 1.68 units).

**Result: PASS — 0 findings**


Not checkable automatically: whether the numerical data themselves allow the observer to infer withheld facts (the later blind analyses test that).
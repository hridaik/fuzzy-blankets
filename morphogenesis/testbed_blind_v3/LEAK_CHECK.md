# LEAK_CHECK.md — automated scan of testbed_blind_v3

Scanned 1450 files (5 text, 1445 npz) with `code/leak_check4.py`.

**Forbidden vocabulary (regex, case-insensitive):** `memory`, `handed`, `chiral`, `situs`, `lateral`, `reporter`, `slot`, `belief`, `\bplans?\b`, `\bfate`, `template`, `mirror`, `state[ _-]?[ab]\b`, `\bstates?\b`, `mechanism`, `enantio`, `latent`, `hidden`, `posterior`, `softmax`, `logit`, `zeta`, `orbit`, `\brole`, `\bmu\b`, `receptor`, `\bgain\b`, `migration`, `\bbias`, `precision`, `free.?energy`, `attractor`, `ground.?truth`, `jacobian`, `ratiometric`, `paracrine`, `quorum`, `toggle`, `\bL-form`, `\bR-form`, `ligand`, `clone`, `limb`, `axial`, `kernel`, `bistab`, `hysteres`, `switch`, `twin-exchange`, `rare type`, `body plan`, `structural`, `\\bgradient`

**Allowed array keys:** {"O1": ["cell_id", "frame_ptr", "level", "t", "xy"], "O2": ["frame_ptr", "level", "t", "xy"], "O3a": ["image", "t"], "O3b": ["image", "t"], "O3c": ["image", "scale", "t"]}

**Structural checks:** opaque condition/arm labels only; O2 rows shuffled relative to O1 and carrying no ids; cluster pose randomised across runs (centroid sd per axis 1.81 units).

**Result: PASS — 0 findings**


Not checkable automatically: whether the numerical data themselves allow the observer to infer withheld facts (the later blind analyses test that).
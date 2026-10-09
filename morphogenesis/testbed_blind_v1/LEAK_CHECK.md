# LEAK_CHECK.md — automated scan of testbed_blind_v1

Scanned 2225 files (4 text, 2220 npz) with `code/leak_check_v1.py`.

**Forbidden vocabulary (regex, case-insensitive):** `slot`, `belief`, `\bplans?\b`, `template`, `mechanism`, `chiral`, `situs`, `fate`, `mirror`, `enantio`, `handed`, `latent`, `hidden`, `posterior`, `softmax`, `logit`, `zeta`, `orbit`, `\brole`, `\bmu\b`, `receptor`, `\bgain\b`, `migration`, `tweezer`, `pipette`, `surgery`, `\bbias`, `precision`, `free.?energy`, `attractor`, `\bL-form`, `\bR-form`, `ground.?truth`, `perm(uted)? channel`, `jacobian`

**Allowed array keys:** {"O1": ["cell_id", "frame_ptr", "level", "t", "xy"], "O2": ["frame_ptr", "level", "t", "xy"], "O3": ["image", "t"]}

**Structural checks:** opaque labels only (`S1/S2`, `N0`, `P1–P6`); O2 files carry no ids and rows are shuffled relative to O1; cluster pose randomised across runs (centroid sd per axis 1.65 units).

**Result: PASS — 0 findings**


Not checkable automatically: whether the numerical data themselves allow the observer to infer withheld facts (that is what the later blind analyses test); the package-wide level order and the identity of the two reporter channels are withheld.
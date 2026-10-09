# OPEN_QUESTIONS.md (M2a, after the redirect; protocol v2)

Items 1–9 of the v1-era list are resolved or superseded: AN re-run done (WITHDRAWAL_V2, REANALYSIS a); ramp protocol decided (absolute-bin clock, PROTOCOL_V2); zero noise kept as canonical with a flagged noise extension (NOISE.md); role assignment is part of the outcome taxonomy; viewer built.

## Decisions for you
1. **Proposed status entry** (README.md): apply or edit. Not applied.
2. **Is class 1 a "defect" for the programme's purposes?** The headline "no durable shape change without an organisational defect" depends on class 1 being a defect (duplicated role, vacant role, undifferentiated cell). That is my classification from the argmax-slot and belief-maximum audit (REANALYSIS e), not a property read from the model. If you consider an 8-cell body with a duplicated role a legitimate alternative shape, the answer to the first headline question flips to "yes, rarely".
3. **Package scope.** The package contains canonical zero-noise data plus flagged noisy segments (NL1–NL3) and 60 16-cell segments. Say whether the noisy/16-cell segments should stay in the first blind release or be a separate package.
4. **Hold-out design.** Hold-outs are by individual (30 of 150), by condition (23) and by region centre (4). Region centres are discs of one radius that overlap neighbours; if a stricter spatial hold-out is wanted the discs should be thinned.

## Open scientific questions (NOT DONE unless stated)
5. **D2 (period-2 cycle: model or scheme).** UNRESOLVED. The engine cannot be sub-stepped (diverges for any perturbation, positions ~1e32 at 2 sub-steps), so the finer-integration test was not run. Evidence available: the Jacobian has an eigenvalue −1.54 at the sustained-DH cycle point and the monodromy radius 0.823 (SKELETON.md); this shows the cycle is a period-doubling of the discrete one-bin map, which is what a scheme artefact would also look like. A different integrator for the same model is the only decisive test.
6. **Mechanism of the 29 non-monotone D4 windows** (MINIMAL_PERTURBATIONS.md). Not investigated; the displacement class used a 4-point grid and probably misses more.
7. **D4 from class 1** (minimal interventions from the defective body) and **above the brackets** (displacement > 10, pulses > 50): not run. The six SHAPE-SWITCH thresholds are all for class 0 → class 1; no reverse (class 1 → class 0) threshold by bisection, although the D3 DT loop repairs class 1 (HYSTERESIS.md).
8. **D3 class-1 DH down-sweep** was not run (INFERRED from the class-0 chain after the collapse at ε = 0.05).
9. **Why role 7 / the tail end is privileged** (MINIMAL_PERTURBATIONS.md): described, not explained. The D1 modes are 96–100 % belief-carried; no mode-to-role map was computed.
10. **Hysteresis in the class-0 DH/DT loops ends with permuted roles and unchanged shape**: is that a fate memory (a durable role change in the sense of the programme) or an artefact of the matching procedure on a body with near-degenerate slots? Roles were assigned by the Hungarian slot match; no independent check.
11. **Fate of the single anomalous cell:** the answer in README rests on 20 individuals collapsing to 8 role cases (one mature state). Other base states (class 1) were not tested.
12. **Viewer pages were never opened** (no browser or node in the session): structure and file builds are checked; rendering is not.
13. **Noise:** one realisation per (individual, level); DH-ADULT relabelling flips from 0/20 noise-free to 10/10 at 1 % noise. Unknown how the D4 thresholds move under noise.

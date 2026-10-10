# OPEN QUESTIONS and deviations

## Deviations from the brief (declared)
1. **Calibration/validation inside development.** The manifest labels the 60 natural validation dishes (bodies 400-429) held-out. All thresholds were calibrated on even-`body_id` development natural dishes and validated on odd-`body_id` ones; the 60 manifest validation dishes were used once, after the freeze, and are reported as a third check (natural-validity table).
2. **Anticipation thresholds used twin/sham development runs** (change-free ones) to set a 5 % false-alarm level; they are not natural dishes and not intervention outcomes, but strictly the brief asks for natural calibration only. Natural dishes (8 frames at 100 time units) cannot calibrate fast-run noise. Effect: the F analysis is negative anyway.
3. **Observation-model constants (blob width, mass per cell) were fitted against O1** on development calibration dishes (allowed as "consistency with O1 where both exist"; the O3 segmentation accuracies are reported against O1 on the same kind of dishes, and again on held-out).
4. Sign of the O3 axis uses the empirical relation "c6 centroid minus c2 centroid points along the O1/O2 c6-gradient axis" learned on calibration dishes; it fails when that relation changes (operation runs 89-91 % agreement).
5. Exemplar viewer pages for held-out runs were chosen by the pre-declared rule after the frozen run; the rule uses only a pipeline-internal score.

## Issues found after the freeze (kept as-is; both versions retained)
- B1 repeated OOD change records; B2 sham-match criterion sensitivity; G3 `exceeds_null` flag uninformative (EVENTS_AND_PAIRS.md, INFOTHEORY.md). Corrective reporting scripts live in `post_freeze/` (not part of the frozen hash).
- Group labels in `consistency_*.json` ("light_dev") also contain device and held-out T/X runs.

## Open scientific questions
- Natural dishes come in two mirror-image organisations. Is the label the same body in either orientation, or two distinct organisations? Only reflection-sensitive descriptors separate them; do any interventions flip a body between the two (transition counts of +1 to +2 per treated founder in P runs say states change, but into OOD/other states, not necessarily the mirror partner)?
- The rare organisation (4 % of dishes, wider, c4 ~ c5 pattern) also comes as a mirror pair; O1 and O3 cannot establish k = 4. More natural dishes with the rare type are needed.
- Untreated twins in development drift out of the natural state model late in long runs (25-50 %), but held-out twins mostly do not (0-17 %). Is the drift body-specific, or an effect of the first frames being observed earlier in the dish's life than natural dishes ("after a settling period")? The paired design absorbs it, but the absolute C3 verdicts for long runs should not be over-read.
- Is the lack of anticipation (Part F) a property of the system (changes are abrupt) or of the estimator (the 100-unit median window removes sub-window leads)? A fast-run null from natural dishes is impossible with 8 frames at 100 units.
- O3: cell-level identity is unrecoverable at the quoted resolution; is there a variant with finer fields? Count bias near the window edge is uncorrected.
- Directed influence between groups at lag 100 is absent; at the native time scale of the fast runs it cannot be calibrated on natural data.
- Louvain on the influence matrix produced only two communities and never a boundary group; the notion of a "boundary" in this system may not be channel-based at all.

# GAPS — what the demo does not (or only partly) deliver
CONTAINS HIDDEN INFORMATION.

| # | item | status |
|---|---|---|
| 1 | **1.1 oracle clip**: the m0c traces (`vanilla8_N512/N1024`) use a slow clock (t = bin/N) and have barely assembled at bin 64; the canonical-clock Octave oracle trace `m2a_audit_and_library/data/part0/direct_primary_0000.mat` (T_dev = 32, seed 0) is used instead, bins 1–64. | deviation, flagged in the chapter's Source box |
| 2 | **Arena size ≥ 520 px** is met for single- and two-panel chapters (1.1–1.4, 2.1, 3.1–3.3 partly); in multi-panel chapters (1.5, 2.2, 4.1, 4.3, 5.1) panels are 190–400 px so that they fit side by side. Presenter mode (F) enlarges them; no click-to-enlarge was built. | partial |
| 3 | **3.2 callout text corrected**: the storyboard says the cut makes “material and geometry leave their bands”. T5's material axis is the id set only (AUDIT_T5 A2), so a cut leaves it flat and only geometry (and V_body) react; the callout says so. The light-switch callout says the pattern leaves its band *during the pulse* (peak 1.4× its bound) and returns. | corrected to the data |
| 4 | **4.1 “pattern only” badge** is not shown at the single common dose (amp 5): L2 already splits the body at that dose; at amplitude 1 L2 is pattern-only (A5, cited in the notes). L5 diverges numerically (positions blow up) at amp 5. | data-driven |
| 5 | **4.2 naming**: T5's “head” disc is physically the TAIL end of the body (AUDIT_T5 A4); the demo labels discs with T5's names and states the correction. | audit correction |
| 6 | **5.1 flock clip**: the stage-6.9 translation pilot of the *specified* model (it does not pass the translation gate), drawn with the tracked collective highlighted; no flock clip from `interactive_demo` exists for the control experiments (those are lattice flocks). | placeholder-level |
| 7 | **3.4 inset** reuses the 1.4 overlay at a fixed frame (not interactive). | simplification |
| 8 | **Export key frames** composes the canvases, legend, callout, caption and takeaway; HTML-only controls (sliders, buttons) are not drawn into the PNGs. | by design |
| 9 | Truth overlay (T) exists in 2.2, 3.4, 4.2, 4.3 only (where the storyboard offers it). | by design |

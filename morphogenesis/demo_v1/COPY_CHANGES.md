# COPY_CHANGES — deviations from the supplied copy, and labels the copy did not supply
**CONTAINS HIDDEN INFORMATION — never give this folder to a blind session.**
All supplied captions, callouts, takeaways, button labels and table cells are in `js/copy.js` and are rendered verbatim (checked by `build/test_demo.py`, which lists any caption/takeaway/callout that differs).

## Cells changed or flagged
- **5.1, Bird flock, "Does the change last?"**: supplied "no" → shown "not tested". TRANSLATING_FLOCK_FINAL_SYNTHESIS records late-release alignment but gives no persistence verdict (§7 only covers identity and target loss). All other cells were checked against that synthesis, VANILLA_CLOSURE.md (§b, §c, §g) and AUDIT_T5 and are kept as supplied.
- **3.2 cut callout** ("Cells leave and the shape breaks…") is verbatim, but in the data a cut moves 12 cells away without losing any, so the "which cells" trace stays flat (AUDIT_T5 A2). Kept as supplied; flagged here.
- **4.4 callout order**: the eight callouts appear in playback time order; "It stays switched" (6) comes after the finish (5) and before the two comparison arms (7, 8).
- **4.5**: the copy mixes bases (95 percent = audited truth; 7 percent = scored from outside). Bars show the outside score, diamonds the audited truth. Callouts are verbatim.
- **1.1**: left panel has no title (none supplied). Pauses: start 0, "~8" at 8, "end" at bin 60 of 64, right callout at 64.
- **1.3**: no caption supplied, so none is shown; each button's text appears as the callout.
- **5.2 / A / B / C**: no caption or takeaway supplied for 5.2 caption, A takeaway, B, C → empty. The old line "These are predictions of the model…" was removed from the screen (kept in notes).

## Labels not in the supplied copy (needed by the layout; plain words only)
- Panel titles: "Our organism" (1.2), "One dish", "The tools" (2.1), "How much light was needed", "Light needed against how long it stays on" (4.2), "True light needed at each place (hidden truth)", "Untouched organism", "After a cut", "Light switch" (3.2), "Controller / Random spot / Whole body / No light" (4.4), "A single cell", "A group of four", "The whole organism" (1.5), thumbnails "Untouched, Cut, Merge two organisms, Light" (2.1).
- Diagram labels in 1.2 (EVERYTHING ELSE, SENSES, INSIDE (hidden), ACTIONS and their bar labels), 1.3 mini-map names, 4.3 arrow labels ("senses (in)", "actions (out)", "thicker arrow = more contact"), 2.2 marker label ("new #n"), 3.1 stepper buttons ("Points, Links, Groups, Outline, Head-to-tail axis"), 3.3 axis names, 3.4 axis names, Appendix A diagram labels.
- 4.1 reveal text per light: "makes cells move faster", "changes the body signals", "adds blue signal: pink → blue only", "adds pink signal: blue → pink only", "makes cells sense more strongly"; verdict badges "flips the state / no flip / changes the body". Row labels are supplied.
- 4.5 chart headings: "Share of dishes that switched and stayed switched", "Light used compared with the true minimum"; chart key line "bar: scored from outside · red: 95 % range · ◇: checked against the hidden truth".
- 5.2 sub-heading "Next steps".
- Appendix B definitions and Appendix C text were written by me (one-liners).
- Type names on screen: trunk → "middle", limb → "side" (copy uses head, middle, side, tail).

## Chapter-specific choices
- **3.1** uses cut run `run_00283` because the glow image fails to split there; in the 6 cut runs of this kind the glow image splits at once in 4 and has trouble in 2 (notes, Sources).
- **2.3** images were already drawn +y up; 3.1/2.3 outlines use the same orientation.

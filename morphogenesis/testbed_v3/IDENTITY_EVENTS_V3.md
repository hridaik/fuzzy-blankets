# IDENTITY_EVENTS_V3.md — gate H4 (v2 protocols with memory outcomes) and H4b

Labels: ESTABLISHED / PROVISIONAL / NOT DONE. Code `code/h4.py`, `h4b.py`; data `data/h4a_replace.json`, `h4b_serial.json`, `h4c_extrude.json`, `h4d_cut.json`, `h4e_fuse.json`, `h4e2_fuse_noisy.json`, `h4b_seeded.json`. Deterministic unless noise is stated (σ = 0.02 on structure/d/e, σ_h = 0.4). Starting body in state a; one body per condition unless stated. Newcomer = naive cell (place logits N(0,1/8), secretions 0, l = 0, e = 0).

## Structure outcomes (structure module = v2 G1; memory cannot influence it)
| event | v3 | v2 | v1 |
|---|---|---|---|
| single replacement (24 cells, 400 tu) | **17/24 end as complete L** (7 DEFECT); by type: tail 8/8, trunk 3/4, head 4/8, limb 2/4 | 14/24 | 9/24 |
| serial replacement (4 seeds, one per 100 tu, then 400 tu) | **0/4 complete** (3–6 components) | 0/4 | 0/4 |
| extrusion (24 cells, 8 units, 300 tu) | rejoins 23/24; **14 L / 8 DEFECT / 2 other** | 15/24 L | 13/24 |
The structure rows differ from v2 because v2's memory coupling (π_ψ terms) is gone; the G1 structure module alone repairs 17/24 single replacements (the G1(d) target of 20/24 is still missed) and still fails serial replacement. H4b below tests whether attenuated place sensing improves this.

## Memory outcomes
* **Newcomer adopts the group state: 24/24.** Replacement at any of the 24 cells: the newcomer (ρ = ½, no secretion) reaches ρ > ½ within **2 tu** (all 24 runs) and ρ > 0.9 in a median of 10 tu, then sits at the group fixed point ρ = 0.908 (l = 2.29) whether or not its place was repaired — the ratiometric sensing reads the neighbours only, so a cell with any neighbours inherits the state at once.
* **Serial replacement (Ship of Theseus for the memory):** after all 24 cells have been replaced (24 unique new ids in each of 4 seeds) the body is structurally defective (0/4), **yet all 24 cells carry state a: ρ = 0.908, fraction in a = 1.00 in 4/4 seeds.** The memory outlives every original cell while the body shape does not.
* **Extruded cell:** keeps the group state in 24/24 (ρ 0.908 in the 23 that rejoin; 0.902 for the one that did not rejoin within 1.6 units — it stays inside the paracrine range of the body, so its evidence persists).
* **Cut** (separation 7; fragments: x-cut 12 + 12 (head/tail), ±y-cut 11 + 13): deterministic: **each fragment keeps ρ = 0.91 for the whole 1,500 tu** in both cuts; x-cut fragments stay compact and drift apart slowly (min separation 27 at 1,500 tu); the ±y fragments interpenetrate and each splits into 2–3 pieces (structure lost), memory unchanged. **Under noise** (σ_h = 0.4, 3 seeds × 2 cuts, 1,500 tu): all 12 fragments keep their state (mean ρ 0.86–0.92 throughout); fragments of 11–13 cells are predicted to outlive 10³ tu at σ_h = 0.4 from the quorum curve (MEMORY_V3.md: τ ≈ 5.9·10³ at σ_h = 0.7 for 12 cells; the fragments are below the noise-limited regime at 0.4). The decay of a small piece (2–8 cells) was characterised only in MEMORY_V3.md (quorum table), not as a cut event.
* **Fusion** (bodies overlapping along the body axis at centre offsets 6.0 and 5.0, side by side at 3.0, 2.0 (near-complete overlap); a+a and a+b, all combinations deterministic; a+b also under noise, 8 seeds per offset; 2,500 tu; CRN seeds now independent — an earlier batch re-used one noise stream for all seeds and is kept in `data/superseded/`):
 | a+b offset | deterministic outcome | noisy outcomes (8 seeds, fraction of cells in a at 2,500 tu) |
 |---|---|---|
 | (7.2, 0) just touching | both bodies keep their state (ρ 0.91 / 0.16); wall persists | – |
 | (6.0, 0) | wall persists; the a body loses part of its cells (mean ρ 0.91 → 0.67, 38 % of all cells in a at 2,500 tu), the b body stays b | **8/8 mixed** (0.40–0.60): wall persists |
 | (5.0, 0) | a wins by 800 tu (fraction a 0.85) | mixed 7/8 (0.60–0.92), a wins 1/8 (at 1,500 tu) |
 | (0, 3.0) | wall persists (0.56 a) | a 1/8, b 3/8, **mixed 4/8** |
 | (0, 2.0) | **b wins within 200 tu** (all cells ρ = 0.09) | **consensus in 50–400 tu in 8/8**: a 5/8, b 3/8 |
 a+a at all offsets: state a throughout. **Which state wins, if any:** none systematically — the state labels are symmetric by construction; the winner at strong overlap is set by the geometry of the particular interpenetration (a: 5/8, b: 3/8; b in the deterministic case). **Speed:** consensus takes 50–400 tu at overlap 2.0, ≳ 10³ tu or never at 5–6. **Domain wall:** persists for the whole 2,500 tu whenever the bodies remain spatially distinct (offset ≥ 5 and side-by-side 3.0 in about half of the noisy runs); it is erased when the bodies interpenetrate (offset 2.0). The fused structure ends as `fragment` (3–7 components) in all fusions — the G1 structure module does not merge two bodies into one — so "which state wins" is a statement about cells, not about a single body.

## H4b — attenuated self-sensing for PLACE inference (bounded; **NOT ADOPTED**)
Variant (`Params3.place_self_attenuation`): perception energies use only the paracrine part of s^λ (j = i term removed) and π_c = 0; action unchanged. Seeded start (16 draws, 600 tu, ρ fixed state a): **0/16 complete**, minimum orbit belief 1.0 but typed distance up to 47.7 (the body disperses: without the self term the cell's perception no longer anchors its own code and the action gradient is inconsistent with the percept). Adoption rule (completeness and durability preserved, repair improved) fails at the first criterion, so durability and replacement reruns were not run. **Keep v2 G1.** (Not a general statement about attenuation of place inference — only about this one variant with action unchanged.)

"""Evidence-recovery audit, Step 1 (2026-09-21). READ-ONLY DERIVATION.

Does not re-simulate anything, does not touch the tracker, controller, or
world dynamics. Reads the already-existing, already-verified per-step
forensic CSVs produced by
`stage6_11_translating_torus/audit/lineage_forensics_611.py`
(`audit/lineage_forensics_611__seed{500..504}__hypotheses.csv`), which that
script's own header/README documents as a byte-for-byte-verified replay of
the real `lineage_611.LineageTracker611` against the recorded production
trajectory (`consistency_mismatches: 0`, all 5 seeds -- see
`audit/lineage_forensics_611__summary.json` and
`audit/LINEAGE_FORENSICS_6_11.md` for that verification).

Those CSVs already carry, per step, the tracker's own
`R_retain_step = |I_{t-1} ∩ I_t| / |I_{t-1}|`   (== R_old in this audit's terms)
`R_purity_step = |I_{t-1} ∩ I_t| / |I_t|`       (== R_new in this audit's terms)
(`lineage_611.py:56-60`, cited in `METHODS_AUDIT_6_11.md` §1.2). This script
adds nothing to the tracker's own logic -- it only:
  1. cross-checks R_retain_step/R_purity_step against the raw recorded
     interior membership lists in `data/viz_bundle_611__seed{n}.json`
     wherever that ground truth is available (t and t-1 present as frames),
  2. derives the Jaccard overlap J = |I_{t-1} ∩ I_t| / |I_{t-1} ∪ I_t| and
     the raw retained/lost/gained counts, which the existing CSVs do not
     carry directly,
  3. writes one combined, provenance-stamped CSV per seed.

Every derived quantity is traceable to:
  - source file: audit/lineage_forensics_611__seed{n}__hypotheses.csv
    (upstream) and data/viz_bundle_611__seed{n}.json (cross-check ground
    truth), both already existing, unmodified, and cited by path,
  - function: lineage_611.LineageTracker611.update (R_retain/R_purity
    definitions) and this script's `jaccard_from_retain_purity` (Jaccard
    derivation) / `crosscheck_from_frames` (independent recomputation from
    raw interior lists where both t-1 and t frames are stored),
  - seed and time step: explicit columns,
  - commit: recorded in the output JSON manifest below.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parents[2]          # stage6_11_translating_torus/audit
STAGE_DIR = AUDIT_DIR.parent                              # stage6_11_translating_torus
OUT_DIR = Path(__file__).resolve().parents[1]              # .../evidence_recovery_20260921
DATA_OUT = OUT_DIR / "data"

SEEDS = [500, 501, 502, 503, 504]


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=STAGE_DIR, text=True
        ).strip()
    except Exception as e:  # pragma: no cover - provenance best-effort
        return f"UNKNOWN ({e})"


def load_hypotheses_csv(seed: int) -> list[dict]:
    path = AUDIT_DIR / f"lineage_forensics_611__seed{seed}__hypotheses.csv"
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def load_viz_frames(seed: int) -> dict[int, dict]:
    path = STAGE_DIR / "data" / f"viz_bundle_611__seed{seed}.json"
    d = json.load(open(path))
    return {f["t"]: f for f in d["frames"]}


def load_transitions(seed: int) -> dict:
    path = AUDIT_DIR / f"lineage_forensics_611__seed{seed}__transitions.json"
    return json.load(open(path))


def derive_seed(seed: int) -> tuple[list[dict], dict]:
    """Two DIFFERENT quantities are computed per step, and NOT collapsed
    into one, because they answer different questions and disagree exactly
    at cross-branch MAP-argmax-switch points (LINEAGE_FORENSICS_6_11.md
    §1.1):

    - `*_displayed`: R_old/R_new/Jaccard computed directly from the raw
      recorded interior member-ID lists in `viz_bundle_611__seed{n}.json`,
      frame t-1 vs frame t. This is ground truth for "what the algorithm's
      OUTPUT (the exposed MAP pointer / displayed interior) actually did,"
      i.e. what a visual replay or the interactive demo shows.
    - `*_branch_internal`: the tracker's own `R_retain_step`/`R_purity_step`
      fields from `lineage_forensics_611__seed{n}__hypotheses.csv`
      (ultimately `lineage_611.py:56-60`), describing continuity of the
      SPECIFIC hypothesis branch that ends up as MAP at step t, relative to
      ITS OWN parent at t-1 -- which is not necessarily the branch that was
      displayed as MAP at t-1.

    Where these disagree (found below, seeds 500/501/502/503, always at a
    `flagged_unusual_transition_lineage_forensics` step): the branch-internal
    number is high (that lineage thread was, on its own terms, a good
    continuation) while the displayed-to-displayed overlap is zero (the
    thread that WINS the MAP argmax this step is a DIFFERENT thread than
    the one that was displayed last step) -- i.e. this is an independent,
    frame-level confirmation of the cross-branch-MAP-overtake mechanism
    LINEAGE_FORENSICS_6_11.md §1.1 already diagnosed by inspecting the
    tracker's internal hypothesis tree, obtained here purely from the
    recorded input/output frames with no tracker internals at all.
    """
    rows = load_hypotheses_csv(seed)
    frames = load_viz_frames(seed)
    transitions = load_transitions(seed)
    flagged_t = {e["t"] for e in transitions["transitions"]}

    out_rows = []
    prev_map_size = None
    disagreements = []

    for row in rows:
        t = int(row["t"])
        map_size = int(row["map_size"])
        r_retain = row["R_retain_step"]
        r_purity = row["R_purity_step"]
        r_retain_f = float(r_retain) if r_retain not in ("", "None") else None
        r_purity_f = float(r_purity) if r_purity not in ("", "None") else None

        branch_overlap = None
        prev_size_used = prev_map_size
        if r_retain_f is not None and prev_map_size not in (None, 0):
            branch_overlap = round(r_retain_f * prev_map_size)

        # PRIMARY: displayed-interior-to-displayed-interior, from raw
        # recorded frames -- no tracker internals used at all.
        disp_overlap = disp_jaccard = disp_retained = disp_lost = disp_gained = None
        if (t - 1) in frames and t in frames:
            i_prev = set(frames[t - 1]["interior"])
            i_cur = set(frames[t]["interior"])
            disp_overlap = len(i_prev & i_cur)
            union = len(i_prev | i_cur)
            disp_jaccard = disp_overlap / union if union > 0 else None
            disp_retained = disp_overlap
            disp_lost = len(i_prev) - disp_overlap
            disp_gained = len(i_cur) - disp_overlap

        if branch_overlap is not None and disp_overlap is not None and branch_overlap != disp_overlap:
            disagreements.append(dict(t=t, branch_internal_overlap=branch_overlap,
                                       displayed_overlap=disp_overlap,
                                       flagged_by_lineage_forensics=(t in flagged_t)))

        out_rows.append(dict(
            seed=seed, t=t, phase=row["phase"], map_hid=row["map_hid"],
            map_prob=row["map_prob"], map_size=map_size,
            prev_map_size=prev_size_used,
            R_old_displayed=(disp_retained / (prev_size_used) if disp_retained is not None and prev_size_used else None),
            R_new_displayed=(disp_retained / map_size if disp_retained is not None and map_size else None),
            jaccard_displayed=disp_jaccard,
            n_retained_displayed=disp_retained, n_lost_displayed=disp_lost, n_gained_displayed=disp_gained,
            overlap_zero_displayed=(disp_overlap == 0) if disp_overlap is not None else None,
            R_old_branch_internal=r_retain_f, R_new_branch_internal=r_purity_f,
            branch_internal_overlap=branch_overlap,
            displayed_vs_branch_internal_disagree=(branch_overlap is not None and disp_overlap is not None and branch_overlap != disp_overlap),
            flagged_unusual_transition_lineage_forensics=(t in flagged_t),
            n_live_hypotheses=row["n_live_hypotheses"],
            n_components=row["n_components"],
            coalesced_map_matches_map=row["coalesced_map_matches_map"],
        ))
        prev_map_size = map_size

    summary = dict(
        seed=seed,
        n_rows=len(out_rows),
        n_displayed_vs_branch_internal_disagreements=len(disagreements),
        disagreements=disagreements,
        flagged_transitions_t=sorted(flagged_t),
    )
    return out_rows, summary


def write_csv(rows: list[dict], path: Path):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    manifest = dict(
        purpose="Material-retention (R_old/R_new/Jaccard) derivation for stage 6.11 evidence-recovery audit",
        git_commit=git_commit(),
        invocation=" ".join(sys.argv),
        upstream_sources=[
            "audit/lineage_forensics_611__seed{500..504}__hypotheses.csv (R_retain_step/R_purity_step, from the real, verified lineage_611.LineageTracker611 replay)",
            "data/viz_bundle_611__seed{500..504}.json (raw recorded interior membership, cross-check ground truth)",
            "audit/lineage_forensics_611__seed{500..504}__transitions.json (existing flagged-transition set)",
        ],
        seeds=SEEDS,
        note="No lineage, controller, or world-dynamics code was modified or re-run. This script only re-expresses already-verified quantities and adds Jaccard/retained/lost/gained, which the upstream CSVs do not carry directly.",
    )
    all_summaries = []
    for seed in SEEDS:
        rows, summary = derive_seed(seed)
        write_csv(rows, DATA_OUT / f"material_retention_seed{seed}.csv")
        all_summaries.append(summary)
        print(f"seed {seed}: {summary['n_rows']} rows, "
              f"{summary['n_displayed_vs_branch_internal_disagreements']} displayed-vs-branch-internal "
              f"disagreements (all should coincide with flagged unusual transitions)")
    manifest["seed_summaries"] = all_summaries
    json.dump(manifest, open(DATA_OUT / "material_retention_manifest.json", "w"), indent=2)
    print("wrote manifest:", DATA_OUT / "material_retention_manifest.json")


if __name__ == "__main__":
    main()

"""Stage 6.9 -> interactive_demo/data/stage6_9_bundle.json.

VISUALIZATION EXPORT ONLY — no new scientific statistic. Selects a
representative episode by the same rule R1 used for Stage 6.8, replays the
frozen moving-flock simulator deterministically at that seed to recover
positions/headings (which the gate run did not persist), and re-derives the
tracked collective with the same deterministic detector the gate used. Every
per-frame identity metric is asserted against the frozen gate file.

Two datasets are exported:

  spec    R = 0.9, v = 0.28  — the SPECIFIED model. Its gate FAILED (0/40).
                               This is the default view.
  offspec R = 1.6, v = 0.5   — the superseded, over-connected model whose gate
                               passed. Exported only as a labelled diagnostic
                               contrast; never the default, and never a
                               Stage 6.9 result.
"""
from __future__ import annotations

import numpy as np

from common_69 import (ModelParams, load_json, dump_json, DATA_DIR, N_BIRDS, L_BOX,
                       R_RADIUS, V_SPEED, R_RADIUS_SUPERSEDED, V_SPEED_SUPERSEDED,
                       BETA, RHO, OMEGA, UV4)
from moving_flock import MovingFlock
from identity_69 import torus_delta
import detect_69 as det

DEMO_DATA = DATA_DIR.parents[1] / "interactive_demo" / "data"
MAX_FRAMES = 170


def pick_representative(cands, metrics):
    """Rule R1 — identical to Stage 6.8's exporter."""
    X = np.array([[fn(c) for _, fn in metrics] for c in cands], dtype=float)
    med = np.median(X, axis=0)
    mad = np.median(np.abs(X - med), axis=0)
    scale = np.where(mad > 0, mad, np.inf)
    score = (np.abs(X - med) / scale).sum(axis=1)
    order = sorted(range(len(cands)), key=lambda i: (score[i], cands[i]["seed"]))
    table = [dict(seed=cands[i]["seed"], score=float(score[i]),
                  metrics={metrics[m][0]: float(X[i, m]) for m in range(len(metrics))})
             for i in order]
    return cands[order[0]], dict(metric_names=[m for m, _ in metrics],
                                 median=[float(v) for v in med],
                                 mad=[float(v) for v in mad], ranked=table)


METRICS = [
    ("R_M_final", lambda e: e["R_M_final"]),
    ("mean_R_F", lambda e: e["mean_R_F"]),
    ("mean_n_components", lambda e: e["mean_n_components"]),
    ("mean_D_deform", lambda e: e["mean_D_deform"]),
]


def build(gate_file, R, v, only_passing, label, stride=1):
    gate = load_json(DATA_DIR / gate_file)
    pool = [e for e in gate["episodes"] if e.get("tracked")]
    if only_passing:
        pool = [e for e in pool if e["passes"]]
    ep, sel = pick_representative(pool, METRICS)

    mf = MovingFlock(N=N_BIRDS, L=L_BOX, R=R, v=v,
                     params=ModelParams(beta=BETA, precB=RHO, precC=OMEGA))
    res = mf.run(nt=ep["t_end"] + 2, seed=ep["seed"])

    tracker, frames = None, []
    for k, rec in enumerate(ep["records"][:MAX_FRAMES]):
        t = rec["t"]
        zw = res.z_hist[max(0, t - det.W_AFFINITY + 1):t + 1]
        cands = det.propose(res.r_hist[t], zw, mf.L)
        if tracker is None:
            tracker = det.TranslatingTracker(mf.L)
            tracker.start(cands[0], res.r_hist[t], res.z_hist[t], t)
        elif not tracker.update(cands, res.r_hist[t], res.z_hist[t], t):
            break
        got = tracker.records[-1]
        # integrity: the re-derived track must equal the frozen gate record
        assert abs(got["R_M"] - rec["R_M"]) < 1e-9 and got["size"] == rec["size"], \
            f"6.9 replay diverged from {gate_file} at t={t}"
        # The tracker must still step every frame (its state is sequential);
        # only the EXPORT is thinned, and only for the long diagnostic run.
        if k % stride:
            continue
        mem = sorted(int(x) for x in tracker.state.members)
        c = np.asarray(got["centroid"])
        rel = torus_delta(res.r_hist[t][mem], c, mf.L)
        frames.append(dict(
            t=int(t), members=mem, size=int(got["size"]),
            R_M=float(got["R_M"]), R_F=float(got.get("R_F", float("nan"))),
            D_deform=float(got.get("D_deform", float("nan"))),
            n_components=int(got.get("n_components", 1)),
            centroid=[round(float(x), 3) for x in c],
            x=[round(float(q), 2) for q in res.r_hist[t][:, 0]],
            y=[round(float(q), 2) for q in res.r_hist[t][:, 1]],
            h=[int(q) for q in res.z_hist[t]],
            rel=[[round(float(a), 2), round(float(b), 2)] for a, b in rel],
        ))

    for i, f in enumerate(frames):
        f["idx"] = i
    cen = np.array([f["centroid"] for f in frames])
    d = (np.diff(cen, axis=0) + mf.L / 2) % mf.L - mf.L / 2
    path = float(np.linalg.norm(d, axis=1).sum()) / mf.R
    net = float(np.linalg.norm((cen[-1] - cen[0] + mf.L / 2) % mf.L - mf.L / 2)) / mf.R
    for i, f in enumerate(frames):
        f["path_R"] = round(float(np.linalg.norm(d[:i], axis=1).sum() / mf.R), 2) if i else 0.0

    return dict(
        label=label, seed=int(ep["seed"]), R=R, v=v, L=mf.L, N=mf.N,
        origin=frames[0]["members"], frames=frames,
        gate_passes=bool(gate["gate_passes"]), pass_rate=gate["pass_rate"],
        n_episodes=len(gate["episodes"]),
        criteria=gate["criteria"],
        rates={k: gate["rate_" + k] for k in ("T1", "T2", "T3", "T4", "T5")},
        episode=dict(duration=ep["duration"], R_M_final=ep["R_M_final"],
                     mean_R_F=ep["mean_R_F"], mean_D_deform=ep["mean_D_deform"],
                     mean_n_components=ep["mean_n_components"],
                     displacement_radii=ep["displacement_radii"],
                     path_radii=round(path, 1), net_radii=round(net, 1),
                     passes=bool(ep["passes"])),
        selection=dict(chosen_seed=int(ep["seed"]), candidates=len(pool),
                       only_gate_passing=only_passing, **sel),
    )


def main():
    out = dict(
        provenance=dict(
            stage="6.9",
            replay_note=("Positions and headings were not persisted by the gate run. They are "
                         "regenerated by a deterministic replay of the frozen simulator at the "
                         "same seed, and the re-derived track is asserted equal to the frozen "
                         "gate record frame by frame. No new statistic is computed."),
            selection_rule=("R1: minimise sum_m |x_m - median_m| / MAD_m over "
                            "R_M, R_F, component count and D_deform; ties to the lowest seed."),
            sources=["translation_gate__R0.9_v0.28.json",
                     "translation_gate__R1.6_v0.5__SUPERSEDED.json"],
        ),
        spec=build("translation_gate__R0.9_v0.28.json", R_RADIUS, V_SPEED,
                   only_passing=False, label="Specified model"),
        # The diagnostic run is 160 frames; every 2nd is exported (the tracker
        # still steps every frame -- only the export is thinned) to keep the
        # single-file demo a reasonable size. The specified model is exported
        # at full resolution.
        offspec=build("translation_gate__R1.6_v0.5__SUPERSEDED.json",
                      R_RADIUS_SUPERSEDED, V_SPEED_SUPERSEDED,
                      only_passing=True, label="Off-spec diagnostic", stride=2),
    )
    out["offspec"]["warning"] = "Off-spec diagnostic — not a Stage 6.9 result"
    DEMO_DATA.mkdir(parents=True, exist_ok=True)
    dump_json(out, DEMO_DATA / "stage6_9_bundle.json")
    kb = (DEMO_DATA / "stage6_9_bundle.json").stat().st_size / 1024
    print(f"wrote {DEMO_DATA/'stage6_9_bundle.json'} ({kb:.0f} KB)")
    for k in ("spec", "offspec"):
        b = out[k]
        print(f"  {k:8s} seed {b['seed']:3d}  frames {len(b['frames']):3d}  "
              f"R_M {b['episode']['R_M_final']:.2f}  R_F {b['episode']['mean_R_F']:.2f}  "
              f"comps {b['episode']['mean_n_components']:.2f}  "
              f"D_def {b['episode']['mean_D_deform']:.3f}  path {b['episode']['path_radii']}R")


if __name__ == "__main__":
    main()

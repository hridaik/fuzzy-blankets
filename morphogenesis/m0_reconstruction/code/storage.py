"""Tiered storage: OBSERVABLE (blind-analysis-safe) vs HIDDEN (full state).

See DATA_SCHEMA.md. Directories are physically separate
(data/golden_traces/<run_id>/observable/, .../hidden/). The loader refuses
hidden-tier access unless audit=True is passed explicitly.
"""
import hashlib
import json
import os
import numpy as np


def _hash_array(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def save_run(root: str, run_id: str, trace: dict, config: dict,
             intervention_log: list, probe_points: np.ndarray = None):
    obs_dir = os.path.join(root, run_id, "observable")
    hid_dir = os.path.join(root, run_id, "hidden")
    os.makedirs(obs_dir, exist_ok=True)
    os.makedirs(hid_dir, exist_ok=True)

    # OBSERVABLE tier: positions, secreted signal, ligand at probe points,
    # opaque intervention log only.
    np.save(os.path.join(obs_dir, "positions.npy"), trace["a_x"])
    np.save(os.path.join(obs_dir, "secretion.npy"), trace["a_s"])
    if probe_points is not None:
        from field import field_concentration
        ligand = np.stack([
            field_concentration(trace["a_x"][i], trace["a_s"][i], probe_points)
            for i in range(len(trace["t"]))
        ])
        np.save(os.path.join(obs_dir, "ligand_at_probes.npy"), ligand)
        np.save(os.path.join(obs_dir, "probe_points.npy"), probe_points)
    with open(os.path.join(obs_dir, "intervention_log.json"), "w") as f:
        json.dump([{"id": e["id"], "cells": e["cells"], "bins": e["bins"],
                    "dose": e.get("dose")} for e in intervention_log], f, indent=2)

    # HIDDEN tier: internal expectations, prediction errors, free energy,
    # precisions, target template, generative-model params, field law,
    # sealed opaque-ID -> implementation mapping.
    np.save(os.path.join(hid_dir, "v_expectations.npy"), trace["v"])
    np.save(os.path.join(hid_dir, "softmax_p.npy"), trace["p"])
    np.save(os.path.join(hid_dir, "eps_x.npy"), trace["eps_x"])
    np.save(os.path.join(hid_dir, "eps_s.npy"), trace["eps_s"])
    np.save(os.path.join(hid_dir, "eps_c.npy"), trace["eps_c"])
    np.save(os.path.join(hid_dir, "free_energy.npy"), trace["free_energy"])
    with open(os.path.join(hid_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2, default=str)
    with open(os.path.join(hid_dir, "intervention_mapping.json"), "w") as f:
        json.dump(intervention_log, f, indent=2, default=str)

    manifest = {
        "run_id": run_id,
        "content_hashes": {
            "positions": _hash_array(trace["a_x"]),
            "secretion": _hash_array(trace["a_s"]),
            "v_expectations": _hash_array(trace["v"]),
        },
    }
    with open(os.path.join(root, run_id, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def load_observable(root: str, run_id: str):
    obs_dir = os.path.join(root, run_id, "observable")
    out = {}
    for name in ("positions", "secretion", "ligand_at_probes", "probe_points"):
        p = os.path.join(obs_dir, f"{name}.npy")
        if os.path.exists(p):
            out[name] = np.load(p)
    with open(os.path.join(obs_dir, "intervention_log.json")) as f:
        out["intervention_log"] = json.load(f)
    return out


def load_hidden(root: str, run_id: str, audit: bool = False):
    if not audit:
        raise PermissionError(
            "Hidden-tier access requires audit=True. This tier exposes "
            "internal expectations, prediction errors, target template, and "
            "the intervention ID -> implementation mapping; blinded analyses "
            "must use load_observable() only."
        )
    hid_dir = os.path.join(root, run_id, "hidden")
    out = {}
    for name in ("v_expectations", "softmax_p", "eps_x", "eps_s", "eps_c", "free_energy"):
        out[name] = np.load(os.path.join(hid_dir, f"{name}.npy"))
    with open(os.path.join(hid_dir, "config.json")) as f:
        out["config"] = json.load(f)
    with open(os.path.join(hid_dir, "intervention_mapping.json")) as f:
        out["intervention_mapping"] = json.load(f)
    return out

"""Tiered storage: OBSERVABLE vs HIDDEN, physically separate directories,
audit-gated hidden-tier loader. Re-implements the schema design first used
in morphogenesis/m0_reconstruction/DATA_SCHEMA.md (schema/design reused;
that stage's deprecated SOLVER is NOT imported here, per this stage's ground
rules). Every rollout records which engine produced it (Part D requirement).
"""
import hashlib
import json
import os
import numpy as np


def _hash_array(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def save_rollout(root: str, run_id: str, rollout: dict, config: dict,
                  intervention_log: list, engine: str, validation_status: str,
                  probe_points: np.ndarray = None):
    """rollout must have: positions (2n,N) or (N,2,n), secretion (mn,N)/(N,m,n),
    and hidden-tier fields (v_expect, free_energy, pred_err_1, pred_err_2, ...).
    engine: 'octave_oracle' | 'python_port' | 'fallback_octave_subprocess'
    validation_status: 'validated' | 'unvalidated' | 'partial'
    """
    obs_dir = os.path.join(root, run_id, "observable")
    hid_dir = os.path.join(root, run_id, "hidden")
    os.makedirs(obs_dir, exist_ok=True)
    os.makedirs(hid_dir, exist_ok=True)

    np.save(os.path.join(obs_dir, "positions.npy"), rollout["positions"])
    np.save(os.path.join(obs_dir, "secretion.npy"), rollout["secretion"])
    if probe_points is not None and "ligand_at_probes" in rollout:
        np.save(os.path.join(obs_dir, "ligand_at_probes.npy"), rollout["ligand_at_probes"])
        np.save(os.path.join(obs_dir, "probe_points.npy"), probe_points)
    with open(os.path.join(obs_dir, "intervention_log.json"), "w") as f:
        json.dump([{"id": e["id"], "cells": e.get("cells"), "bins": e.get("bins"),
                    "dose": e.get("dose")} for e in intervention_log], f, indent=2)
    with open(os.path.join(obs_dir, "engine_and_validation.json"), "w") as f:
        json.dump({"engine": engine, "validation_status": validation_status}, f, indent=2)

    for key in ("v_expect", "free_energy", "pred_err_1", "pred_err_2",
                "target_x", "target_s", "target_c"):
        if key in rollout:
            np.save(os.path.join(hid_dir, f"{key}.npy"), rollout[key])
    with open(os.path.join(hid_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2, default=str)
    with open(os.path.join(hid_dir, "intervention_mapping.json"), "w") as f:
        json.dump(intervention_log, f, indent=2, default=str)

    manifest = {
        "run_id": run_id,
        "engine": engine,
        "validation_status": validation_status,
        "content_hashes": {
            "positions": _hash_array(rollout["positions"]),
            "secretion": _hash_array(rollout["secretion"]),
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
    with open(os.path.join(obs_dir, "engine_and_validation.json")) as f:
        out.update(json.load(f))
    return out


def load_hidden(root: str, run_id: str, audit: bool = False):
    if not audit:
        raise PermissionError(
            "Hidden-tier access requires audit=True. This tier exposes "
            "internal expectations, prediction errors, free energy, the "
            "target template, and the intervention ID -> implementation "
            "mapping; blinded analyses must use load_observable() only."
        )
    hid_dir = os.path.join(root, run_id, "hidden")
    out = {}
    for fn in os.listdir(hid_dir):
        if fn.endswith(".npy"):
            out[fn[:-4]] = np.load(os.path.join(hid_dir, fn))
    with open(os.path.join(hid_dir, "config.json")) as f:
        out["config"] = json.load(f)
    with open(os.path.join(hid_dir, "intervention_mapping.json")) as f:
        out["intervention_mapping"] = json.load(f)
    return out

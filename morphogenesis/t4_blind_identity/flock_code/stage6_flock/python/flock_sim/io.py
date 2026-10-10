"""Snapshot save/load and config hashing for provenance."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .model import ModelParams


def hash_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_snapshot(path: str | Path, z_hist_window: np.ndarray, meta: dict) -> None:
    path = Path(path)
    np.savez_compressed(path, z_hist_window=z_hist_window, meta=json.dumps(meta))


def load_snapshot(path: str | Path) -> tuple[np.ndarray, dict]:
    data = np.load(path, allow_pickle=False)
    meta = json.loads(str(data["meta"]))
    return data["z_hist_window"], meta


def params_to_dict(p: ModelParams) -> dict:
    return asdict(p)

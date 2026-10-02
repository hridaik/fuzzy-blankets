"""Part G: deterministic, versioned observation-ladder renderer.
Generates O1 (pass-through), O2 (unlabelled point clouds), O3a/O3b (images),
O4 (ligand maps) from a stored rollout (.mat, engine output). Every
rendering choice is an OBSERVER MODEL CHOICE -- documented in
OBSERVATION_LADDER.md, not treated as ground truth.

Deterministic: given the same rollout + frame index + RENDERER_VERSION, the
same output is produced (all randomness -- O2's per-frame permutation, O3's
noise -- is seeded from a declared function of (run_id, frame_idx)).
"""
import hashlib
import os
import sys
import numpy as np
import scipy.io as sio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                 "m0b_reference_port", "code"))
from model import field_concentration  # noqa: E402

RENDERER_VERSION = "m1-obsladder-v1"

# --- declared rendering parameters (OBSERVATION_LADDER.md restates these) ---
IMG_SIZE = 96
FOV_HALF_WIDTH = 4.0  # field of view: [-4,4] x [-4,4] in template units,
# declared to comfortably enclose every run's cell excursions (template
# spans roughly [-2.75,2.75] x [-1,1]; kicks/withdrawal can push cells
# further -- checked empirically against Part C's K1-sigma1.5/K4 kicks,
# see OBSERVATION_LADDER.md)
BLOB_SIGMA_PX = 2.5  # Gaussian blob sigma, in PIXELS
NOISE_SNR_DB = 10.0  # declared additive-Gaussian + Poisson-like noise level
LIGAND_GRID_N = 32   # O4 grid resolution (per axis)
FRAME_STRIDE = 8      # store every 8th frame, per the ground rules


def _rng_for(run_id: str, frame_idx: int, salt: str) -> np.random.Generator:
    h = hashlib.sha256(f"{RENDERER_VERSION}|{run_id}|{frame_idx}|{salt}".encode()).digest()
    seed = int.from_bytes(h[:8], "little")
    return np.random.default_rng(seed)


def load_rollout_frame(mat_path: str, frame_idx: int, n_cells: int = 8):
    d = sio.loadmat(mat_path)
    pos = d["positions"]  # (2n, N)
    sec = d["secretion"]  # (4n, N)
    a_x = pos[:, frame_idx].reshape(2, n_cells, order="F")
    a_s = sec[:, frame_idx].reshape(4, n_cells, order="F")
    return a_x, a_s


# --- O2: unlabelled point clouds ---
def render_O2(a_x, a_s, run_id, frame_idx):
    """Per-frame random permutation of cell order, seeded deterministically.
    No persistent cell IDs anywhere in the output."""
    rng = _rng_for(run_id, frame_idx, "O2")
    n = a_x.shape[1]
    perm = rng.permutation(n)
    return a_x[:, perm].astype(np.float16), a_s[:, perm].astype(np.float16)


# --- O3a/O3b: images ---
def _to_pixel(x1, x2):
    px = (x1 + FOV_HALF_WIDTH) / (2 * FOV_HALF_WIDTH) * IMG_SIZE
    py = (x2 + FOV_HALF_WIDTH) / (2 * FOV_HALF_WIDTH) * IMG_SIZE
    return px, py


def _render_channels(a_x, a_s, channel_idx, run_id, frame_idx, salt):
    """channel_idx: list of secretion-row indices (0..3) to render as image channels."""
    n_ch = len(channel_idx)
    img = np.zeros((IMG_SIZE, IMG_SIZE, n_ch), dtype=np.float32)
    yy, xx = np.mgrid[0:IMG_SIZE, 0:IMG_SIZE]
    n_cells = a_x.shape[1]
    for c in range(n_cells):
        px, py = _to_pixel(a_x[0, c], a_x[1, c])
        blob = np.exp(-((xx - px) ** 2 + (yy - py) ** 2) / (2 * BLOB_SIGMA_PX ** 2))
        for ci, ch in enumerate(channel_idx):
            img[:, :, ci] += blob * a_s[ch, c]

    img = img / (img.max() + 1e-9)  # normalize to [0,1] per frame (declared choice)

    rng = _rng_for(run_id, frame_idx, salt)
    signal_power = np.mean(img ** 2)
    noise_power = signal_power / (10 ** (NOISE_SNR_DB / 10))
    gauss_noise = rng.normal(scale=np.sqrt(max(noise_power, 1e-12)), size=img.shape)
    poisson_like = rng.poisson(lam=np.clip(img, 0, None) * 20.0) / 20.0 - img
    noisy = np.clip(img + gauss_noise + 0.3 * poisson_like, 0, 1)
    return (noisy * 255).astype(np.uint8)


def render_O3a(a_x, a_s, run_id, frame_idx):
    """4 channels = all 4 secreted levels (including the trivial existence
    channel, per the engine's own P.s row 0 -- declared, see
    OBSERVATION_LADDER.md)."""
    return _render_channels(a_x, a_s, [0, 1, 2, 3], run_id, frame_idx, "O3a")


def render_O3b(a_x, a_s, run_id, frame_idx):
    """2 channels = signals 2 and 3 (P.s rows 1,2 -- the paper's convention,
    excluding the trivial existence row and signal 4), mimicking 2 reporters."""
    return _render_channels(a_x, a_s, [1, 2], run_id, frame_idx, "O3b")


# --- O4: ligand concentration maps ---
def render_O4(a_x, a_s):
    """4 ligand maps on a LIGAND_GRID_N x LIGAND_GRID_N grid, using the
    engine's own field law (model.field_concentration, m0b-validated,
    unmodified). No cell positions in the output."""
    lin = np.linspace(-FOV_HALF_WIDTH, FOV_HALF_WIDTH, LIGAND_GRID_N)
    gx, gy = np.meshgrid(lin, lin)
    probe = np.stack([gx.ravel(), gy.ravel()])
    c = field_concentration(a_x, a_s, probe)  # (4, LIGAND_GRID_N^2)
    maps = c.reshape(4, LIGAND_GRID_N, LIGAND_GRID_N)
    return maps.astype(np.float16)


def render_all(mat_path, run_id, frame_indices):
    """Renders O2, O3a, O3b, O4 for the given frame indices (should already
    be FRAME_STRIDE-subsampled by the caller). Returns dict of stacked
    arrays ready to np.savez_compressed."""
    d = sio.loadmat(mat_path)
    pos = d["positions"]; sec = d["secretion"]
    n_cells = pos.shape[0] // 2
    O2_x, O2_s, O3a, O3b, O4 = [], [], [], [], []
    for fi in frame_indices:
        a_x = pos[:, fi].reshape(2, n_cells, order="F")
        a_s = sec[:, fi].reshape(4, n_cells, order="F")
        ox, os_ = render_O2(a_x, a_s, run_id, fi)
        O2_x.append(ox); O2_s.append(os_)
        O3a.append(render_O3a(a_x, a_s, run_id, fi))
        O3b.append(render_O3b(a_x, a_s, run_id, fi))
        O4.append(render_O4(a_x, a_s))
    return {
        "O2_positions": np.stack(O2_x), "O2_secretion": np.stack(O2_s),
        "O3a": np.stack(O3a), "O3b": np.stack(O3b), "O4": np.stack(O4),
        "frame_indices": np.array(frame_indices), "renderer_version": RENDERER_VERSION,
    }


def estimate_storage_bytes(n_frames_per_run: int, n_runs: int) -> int:
    per_frame = (
        8 * 2 * 2 +  # O2 positions, float16, 8 cells x 2 coords
        8 * 4 * 2 +  # O2 secretion, float16, 8 cells x 4 channels
        IMG_SIZE * IMG_SIZE * 4 * 1 +  # O3a uint8
        IMG_SIZE * IMG_SIZE * 2 * 1 +  # O3b uint8
        LIGAND_GRID_N * LIGAND_GRID_N * 4 * 2  # O4 float16
    )
    return per_frame * n_frames_per_run * n_runs

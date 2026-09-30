"""Part D: Python-driven Octave engine, subprocess-based (no oct2py
dependency needed/available; subprocess calling the same `octave-dem` conda
env used throughout this programme is simpler and has zero extra
dependencies). Exposes the same run() interface the (incomplete) Python
port would expose, so later stages can swap engines without changing
caller code.

run(config, initial_state, noise_seed, interventions, n_bins) -> rollout,
saved via storage.save_rollout() in the m0b/m0 blinded tiered schema, with
engine='fallback_octave_subprocess' recorded on every rollout.
"""
import json
import os
import subprocess
import tempfile
import time
import numpy as np
import scipy.io as sio

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPM12 = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "sources", "spm12")
SPM12_DEM = os.path.join(SPM12, "toolbox", "DEM")
M0B_ORACLE = os.path.join(REPO_ROOT, "..", "m0b_reference_port", "oracle")
LOCAL_ORACLE = os.path.join(REPO_ROOT, "oracle")

OCTAVE_ENV_ACTIVATE = (
    "source $(conda info --base)/etc/profile.d/conda.sh && conda activate octave-dem"
)


def _octave_eval(script: str, timeout=1800):
    cmd = f'{OCTAVE_ENV_ACTIVATE} && octave --no-gui --eval "{script}"'
    t0 = time.time()
    result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True,
                             timeout=timeout, cwd=REPO_ROOT)
    elapsed = time.time() - t0
    if result.returncode != 0:
        raise RuntimeError(f"Octave failed (exit {result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result.stdout, elapsed


def run(config: dict, initial_state=None, noise_seed: int = 0,
        interventions: dict = None, n_bins: int = 32, out_mat: str = None):
    """config: {'L': 2|4, 'v_override': array|None}
    interventions: {'kind': str, 'params': dict} or None
    Returns: (mat_dict, elapsed_seconds)
    """
    if out_mat is None:
        fd, out_mat = tempfile.mkstemp(suffix=".mat", dir=os.path.join(REPO_ROOT, "data", "oracle_traces"))
        os.close(fd)

    L = config.get("L", 2)
    v_override = initial_state

    if interventions is None or interventions.get("kind", "none") == "none":
        # plain oracle path (m0b's run_and_export), no perturbation machinery
        v_arg = "[]"
        if v_override is not None:
            mat_v = out_mat.replace(".mat", "_vinit.mat")
            sio.savemat(mat_v, {"v0": v_override})
            v_arg = f"cell2mat(struct2cell(load('{mat_v}')))"
        script = (
            f"addpath('{SPM12}'); addpath('{SPM12_DEM}'); addpath('{M0B_ORACLE}'); "
            f"run_and_export({L}, {n_bins}, {noise_seed}, '{out_mat}', {v_arg});"
        )
    else:
        kind = interventions["kind"]
        params = dict(interventions.get("params", {}))
        params.pop("v_override", None)
        params_str = "struct(" + ",".join(
            f"'{k}',{_octave_literal(v)}" for k, v in params.items()) + ")" \
            if params else "struct()"
        script = (
            f"addpath('{SPM12}'); addpath('{SPM12_DEM}'); addpath('{M0B_ORACLE}'); "
            f"addpath('{LOCAL_ORACLE}'); "
            f"params = {params_str}; params.kind='{kind}'; "
            f"run_perturbed('{kind}', params, {n_bins}, {noise_seed}, '{out_mat}');"
        )

    stdout, elapsed = _octave_eval(script)
    mat = sio.loadmat(out_mat)
    return mat, elapsed


def _octave_literal(v):
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return f"'{v}'"
    if isinstance(v, (list, tuple)):
        return "[" + " ".join(str(x) for x in v) + "]"
    if v is None:
        return "[]"
    return repr(v)


def mat_to_rollout(mat: dict) -> dict:
    return {
        "positions": mat["positions"],
        "secretion": mat["secretion"],
        "v_expect": mat["v_expect"],
        "free_energy": mat["free_energy_J"],
        "pred_err_1": mat["pred_err_1"],
        "pred_err_2": mat["pred_err_2"],
        "target_x": mat["target_x"],
        "target_s": mat["target_s"],
        "target_c": mat["target_c"],
    }

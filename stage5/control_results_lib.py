"""Shared loader for control_sweep.py output, used by fig4-fig9."""
import os, json
import numpy as np


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INDEX_PATH = os.path.join(DATA_DIR, "control_results.jsonl")
RESULT_DIR = os.path.join(DATA_DIR, "control_results")


def load_all():
    recs = {}
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                recs[rec["key"]] = rec  # later lines overwrite (keeps latest rerun)
    return recs


def key(formulation, phenotype_only, T, rho_z=1.0, lambda_org=0.0, n_knots=12):
    mode = "phen" if phenotype_only else "coord"
    return f"F{formulation}_{mode}_T{T}_rho{rho_z}_lam{lambda_org}_k{n_knots}"


def find(recs, formulation, phenotype_only, T, rho_z=1.0, lambda_org=0.0, n_knots=12):
    """control_sweep's baseline stage used int-literal horizons (T=1,2,4 -> 'T1') while
    the rho_z/lambda_org stages used float literals (T=1.0,2.0 -> 'T1.0'), so the same
    logical config can appear under two different key strings. Try both."""
    for Tval in (T, float(T)):
        k = key(formulation, phenotype_only, Tval, rho_z, lambda_org, n_knots)
        if k in recs:
            return recs[k]
    return None


def load_traj(rec):
    npz_path = rec["npz"]
    d = np.load(npz_path)
    return d

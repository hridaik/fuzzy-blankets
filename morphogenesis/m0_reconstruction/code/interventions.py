"""Intervention hooks.

Per DISCREPANCIES.md section 6, only ONE perturbation from the task prompt's
list has source-code grounding: Pio-Lopez's "high identity expectation in k
cells" (LPioL/active_inference_morphopsy, commit bd378a4). All others
(high/low sensory precision, rescue, and the four Friston-2015 perturbations)
are NOT implemented here because no source code for them was found -- see
DISCREPANCIES.md sections 6-7. Do not add speculative implementations.

Each intervention is a parameterised, logged operation on specified cells /
channels / bins, per Task C's requirement. It returns a new v (does not
mutate initial condition construction elsewhere), and logs an OPAQUE
intervention ID + parameters to the HIDDEN tier (DATA_SCHEMA.md) -- the
OBSERVABLE tier only ever sees the opaque ID.
"""
import numpy as np


def high_identity_expectation_v0(n: int, k: int, rows=(3, 4), value=np.exp(6),
                                   base_scale=1.0 / 8, seed=0):
    """Builds an initial v (n x n) with `value` written into `rows` for the
    first k columns (cells), matching the morphopsy variant files' structure
    (MODEL_SPEC.md sec 6). Base entries are small random draws (documented
    deviation: the original files hard-code one frozen numeric draw; here we
    draw fresh so the base condition is reproducible from a declared seed
    rather than an unverifiable magic matrix -- DISCREPANCIES.md sec 4).
    """
    rng = np.random.default_rng(seed)
    v = rng.standard_normal((n, n)) * base_scale
    for r in rows:
        v[r, :k] = value
    return v


INTERVENTION_REGISTRY = {
    "high_identity_expectation": high_identity_expectation_v0,
}


def make_opaque_id(name: str, params: dict) -> str:
    import hashlib
    import json
    payload = json.dumps({"name": name, "params": params}, sort_keys=True)
    return "ivn_" + hashlib.sha256(payload.encode()).hexdigest()[:16]

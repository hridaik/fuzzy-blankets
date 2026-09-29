"""CLI driver: run a configuration and save a tiered trace.

Usage: python run.py <config_name> [--n_bins N] [--seed S] [--k K] [--out DIR]
Configs: vanilla8, high_identity_k<k>  (k in 1..6, per available morphopsy variants)
"""
import argparse
import os
import numpy as np

from template import decode_template
from field import field_concentration
from generative import Mg
from solver import run as solver_run, N_BINS_DEFAULT
from interventions import high_identity_expectation_v0, make_opaque_id
from storage import save_run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ROOT = os.path.join(ROOT, "data", "golden_traces")


def build_initial(config: str, n: int, seed: int):
    if config == "vanilla8":
        rng = np.random.default_rng(seed)
        v0 = rng.standard_normal((n, n)) / 8.0
        return v0, []
    if config.startswith("high_identity_k"):
        k = int(config.replace("high_identity_k", ""))
        v0 = high_identity_expectation_v0(n, k, seed=seed)
        opid = make_opaque_id("high_identity_expectation", {"k": k, "seed": seed})
        log = [{"id": opid, "cells": list(range(k)), "bins": [0],
                "dose": {"rows": [3, 4], "value": "exp(6)"}}]
        return v0, log
    raise ValueError(f"unknown config {config}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--n_bins", type=int, default=N_BINS_DEFAULT)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=DATA_ROOT)
    args = ap.parse_args()

    P_x, P_s, n, m = decode_template()
    P_c = field_concentration(P_x, P_s)

    v0, intervention_log = build_initial(args.config, n, args.seed)
    g_x0, g_s0, _, _ = Mg(v0, P_x, P_s, P_c, t=1.0 / args.n_bins)
    a_x0, a_s0 = g_x0, g_s0

    trace = solver_run(v0, a_x0, a_s0, P_x, P_s, P_c, n_bins=args.n_bins)

    probe_lin = np.linspace(-2, 2, 9)
    gx, gy = np.meshgrid(probe_lin, probe_lin)
    probe_points = np.stack([gx.ravel(), gy.ravel()])

    run_id = f"{args.config}_seed{args.seed}_n{args.n_bins}"
    manifest = save_run(args.out, run_id, trace,
                         config=dict(vars(args), n_cells=n, m_signals=m),
                         intervention_log=intervention_log,
                         probe_points=probe_points)
    print(f"saved {run_id}: {manifest['content_hashes']}")


if __name__ == "__main__":
    main()

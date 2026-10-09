# HYSTERESIS.md — D3: quasi-static continuation up and down (protocol v2)

Code `code/d3_hysteresis.py`, `code/d3_analyze.py`, `code/d3_md.py`; data `data/v2/d3/`, `data/v2/d3_*.json`, `data/v2/d3_summary.json`. Every step is a **continuation of the full state** (beliefs, velocities, actions, absolute-bin clock T_dev = 32): a raised-cosine change of the parameter over 4 bins, then settle in segments of 192 bins (≤ 4, i.e. ≤ 768 bins) until the declared state-based stationarity (FIXED / CYCLE2) holds. Steps: DH/DT ε = 0.05 up to 0.5, then 0.1 to 1 (declared cut, COMPUTE_PLAN update 3), then back down; precision multiplier φ = ln F in steps of 0.5 from 0 to 6 and back (V = exp(3+φ)). Starts: class 0 = primary_0000 adult (b = 320), class 1 = secondary_0005 adult. Zero process noise.

Families: **DH_ε**: sensed long-axis position s = (1−ε)x + εx²; **DT_ε**: s = (1−ε)x − εx²; **PREC**: global sensory-precision multiplier. The class-1 DH chain was run up to ε = 0.5 only (see below); the class-1 DT chain was run in full.

"Attractor" is reported by its stationarity type, role map and the distances to the class-0 and class-1 reference shapes. Under ε > 0 the *sensed* mapping is distorted, so d to the references at intermediate ε measures how far the body has been pushed, not a class label; class labels are meaningful at ε = 0 and for PREC.

## Answers (ESTABLISHED unless marked)
| Family, start | Up vs down at the same parameter | Baseline after the loop vs start |
|---|---|---|
| **PREC, class 0** | **no hysteresis** (12/12 levels identical in kind, roles, shape) | identical (d 1e-8, same roles) |
| **PREC, class 1** | **no hysteresis** (12/12); roles permute at φ = 1 on the way up and permute back on the way down, i.e. reversible | identical; class 1 retained |
| **DH_ε, class 0** | **hysteresis**: of 15 compared levels, role maps differ at 7, shape differs (> 1e-3) at 3 (ε = 0.15, 0.2, 0.35), attractor type differs at 2 (ε = 0.35: CYCLE2 up / FIXED down; ε = 0.9: not stationary up / FIXED down) | **shape identical, roles permuted** (`01234567` → `06435127`, a 5-cycle of roles) |
| **DT_ε, class 0** | **hysteresis**: role maps differ at 14/15 levels, shape differs at 5, attractor type differs at 2 | **shape identical, roles permuted** (`01234567` → `01324567`, a swap of roles 2 and 3) |
| **DH_ε, class 1** | collapses at the first step: at ε = 0.05 the class-1 body is on the class-0 trajectory (d to the class-0 chain ≤ 4e-10 at every step to ε = 0.5, same attractor kinds) | down-sweep NOT RUN; if the merge is exact it ends as the class-0 chain (**INFERRED, PROVISIONAL**) |
| **DT_ε, class 1** | stays class-1-like to ε ≈ 0.2, then diverges; merges with the class-0 chain at ε = 1.0 (identical d values) | **class 0**: d to class-0 reference 0.000, to class-1 reference 0.411 — **the loop repairs class 1 into class 0** |

* **Does baseline differ from the start?** From class 0: **yes in roles, no in shape** — a quasi-static DH or DT loop leaves a mature class-0 body in the same shape with a permuted role map (DH 5-cycle, DT 2-cycle); PREC leaves everything unchanged. From class 1: DT (and, if the inferred merge holds, DH) leaves a **different shape (class 0)**; PREC does not.
* **Hysteresis in any parameter family?** Yes, in DH_ε and DT_ε (path-dependent attractors and roles; critical slowing — settle times up to 708 bins — and non-stationary steps near the transitions); none in the precision multiplier.
* **Durable shape change without an organisational defect?** From class 0, no: the loops return class 0. The only durable shape change found here is **class 1 → class 0** (a defective form repaired by a DT ε ramp). Class 0 → class 1 (a defect) occurs only for very large impulsive perturbations (MINIMAL_PERTURBATIONS.md).
* **Period-2 cycles** occur in the scans at DH ε = 0.35 (up; amplitude 0.62) and ε = 1.0 (up; 0.30) and at DT ε = 0.3 (down; 0.25); never in PREC. They are isolated windows, not a single onset: ε = 0.3 and 0.4 (DH) are FIXED. (D2 in SKELETON.md.)
* Caveats: a step is "quasi-static" relative to the 9-bin contraction time but not near transitions, where relaxation times diverge; steps flagged NONCONV (DH 0.9 up, DT 0.3 up, DT 0.2 down) did not settle in 768 bins and their roles are those at the end of the last segment. Class-0 and class-1 starts are each one individual (mature bodies are identical up to relabelling).

## Full tables (every step; attractor, roles, shape distances)
#### DH_ε from class 0 (s = (1−ε)x + εx²)

| step | dir | level | attractor | settle bin | roles (slot of cell 0..7) | d to class-0 ref | d to class-1 ref | cycle amp |
|---|---|---|---|---|---|---|---|---|
| 0 | up | 0 | FIXED | 1 | 01234567 | 0.000 | 0.411 |  |
| 1 | up | 0.05 | FIXED | 89 | 01234567 | 0.062 | 0.429 |  |
| 2 | up | 0.1 | FIXED | 108 | 01234567 | 0.137 | 0.475 |  |
| 3 | up | 0.15 | FIXED | 145 | 01234567 | 0.241 | 0.555 |  |
| 4 | up | 0.2 | FIXED | 265 | 01234567 | 0.425 | 0.717 |  |
| 5 | up | 0.25 | FIXED | 360 | 21435067 | 0.905 | 1.208 |  |
| 6 | up | 0.3 | FIXED | 199 | 21435067 | 0.817 | 1.069 |  |
| 7 | up | 0.35 | CYCLE2 | 341 | 21435067 | 0.764 | 1.009 | 0.616 |
| 8 | up | 0.4 | FIXED | 236 | 21435760 | 0.782 | 1.056 |  |
| 9 | up | 0.45 | FIXED | 77 | 01435762 | 0.728 | 0.972 |  |
| 10 | up | 0.5 | FIXED | 75 | 01435762 | 0.690 | 0.907 |  |
| 11 | up | 0.6 | FIXED | 90 | 01435762 | 0.651 | 0.823 |  |
| 12 | up | 0.7 | FIXED | 94 | 01435762 | 0.635 | 0.772 |  |
| 13 | up | 0.8 | FIXED | 97 | 01435762 | 0.638 | 0.737 |  |
| 14 | up | 0.9 | NONCONV (4 × 192 bins) | - | 06435721 | 0.678 | 0.654 |  |
| 15 | up | 1 | CYCLE2 | 150 | 06435721 | 0.744 | 1.005 | 0.297 |
| 16 | down | 0.9 | FIXED | 280 | 06435721 | 0.678 | 0.654 |  |
| 17 | down | 0.8 | FIXED | 434 | 01435762 | 0.638 | 0.737 |  |
| 18 | down | 0.7 | FIXED | 94 | 01435762 | 0.635 | 0.772 |  |
| 19 | down | 0.6 | FIXED | 91 | 01435762 | 0.651 | 0.823 |  |
| 20 | down | 0.5 | FIXED | 84 | 01435762 | 0.690 | 0.907 |  |
| 21 | down | 0.45 | FIXED | 71 | 01435762 | 0.728 | 0.972 |  |
| 22 | down | 0.4 | FIXED | 83 | 21435760 | 0.782 | 1.056 |  |
| 23 | down | 0.35 | FIXED | 97 | 21435760 | 0.853 | 1.182 |  |
| 24 | down | 0.3 | FIXED | 236 | 21435067 | 0.817 | 1.090 |  |
| 25 | down | 0.25 | FIXED | 346 | 21435760 | 0.905 | 1.208 |  |
| 26 | down | 0.2 | FIXED | 101 | 21435760 | 0.815 | 1.132 |  |
| 27 | down | 0.15 | FIXED | 638 | 20435167 | 0.665 | 0.999 |  |
| 28 | down | 0.1 | FIXED | 217 | 06435127 | 0.137 | 0.475 |  |
| 29 | down | 0.05 | FIXED | 94 | 06435127 | 0.062 | 0.429 |  |
| 30 | down | 0 | FIXED | 82 | 06435127 | 0.000 | 0.411 |  |

#### DT_ε from class 0 (s = (1−ε)x − εx²)

| step | dir | level | attractor | settle bin | roles (slot of cell 0..7) | d to class-0 ref | d to class-1 ref | cycle amp |
|---|---|---|---|---|---|---|---|---|
| 0 | up | 0 | FIXED | 1 | 01234567 | 0.000 | 0.411 |  |
| 1 | up | 0.05 | FIXED | 64 | 01234567 | 0.056 | 0.386 |  |
| 2 | up | 0.1 | FIXED | 92 | 01234567 | 0.119 | 0.406 |  |
| 3 | up | 0.15 | FIXED | 114 | 01234567 | 0.194 | 0.454 |  |
| 4 | up | 0.2 | FIXED | 200 | 01234567 | 0.291 | 0.526 |  |
| 5 | up | 0.25 | FIXED | 708 | 61034527 | 0.713 | 0.605 |  |
| 6 | up | 0.3 | NONCONV (4 × 192 bins) | - | 61034527 | 0.567 | 0.482 |  |
| 7 | up | 0.35 | FIXED | 224 | 61034527 | 0.570 | 0.472 |  |
| 8 | up | 0.4 | FIXED | 133 | 01634527 | 0.538 | 0.747 |  |
| 9 | up | 0.45 | FIXED | 92 | 01634527 | 0.767 | 0.990 |  |
| 10 | up | 0.5 | FIXED | 80 | 01234567 | 0.724 | 0.968 |  |
| 11 | up | 0.6 | FIXED | 148 | 01234567 | 0.440 | 0.674 |  |
| 12 | up | 0.7 | FIXED | 111 | 01234567 | 0.481 | 0.708 |  |
| 13 | up | 0.8 | FIXED | 175 | 01234567 | 0.502 | 0.729 |  |
| 14 | up | 0.9 | FIXED | 117 | 31024567 | 0.410 | 0.629 |  |
| 15 | up | 1 | FIXED | 75 | 31024567 | 0.431 | 0.660 |  |
| 16 | down | 0.9 | FIXED | 79 | 31024567 | 0.410 | 0.629 |  |
| 17 | down | 0.8 | FIXED | 84 | 01324567 | 0.397 | 0.637 |  |
| 18 | down | 0.7 | FIXED | 88 | 01324567 | 0.400 | 0.642 |  |
| 19 | down | 0.6 | FIXED | 90 | 01324567 | 0.416 | 0.649 |  |
| 20 | down | 0.5 | FIXED | 134 | 01324567 | 0.493 | 0.658 |  |
| 21 | down | 0.45 | FIXED | 215 | 01364527 | 0.767 | 0.990 |  |
| 22 | down | 0.4 | FIXED | 118 | 01364527 | 0.538 | 0.747 |  |
| 23 | down | 0.35 | FIXED | 197 | 61304527 | 0.570 | 0.472 |  |
| 24 | down | 0.3 | CYCLE2 | 723 | 61304527 | 0.579 | 0.491 | 0.250 |
| 25 | down | 0.25 | FIXED | 435 | 61304527 | 0.713 | 0.605 |  |
| 26 | down | 0.2 | NONCONV (4 × 192 bins) | - | 01324567 | 0.291 | 0.526 |  |
| 27 | down | 0.15 | FIXED | 126 | 01324567 | 0.194 | 0.454 |  |
| 28 | down | 0.1 | FIXED | 101 | 01324567 | 0.119 | 0.406 |  |
| 29 | down | 0.05 | FIXED | 83 | 01324567 | 0.056 | 0.386 |  |
| 30 | down | 0 | FIXED | 62 | 01324567 | 0.000 | 0.411 |  |

#### DH_ε from class 1 (up-sweep to ε = 0.5 only)

| step | dir | level | attractor | settle bin | roles (slot of cell 0..7) | d to class-0 ref | d to class-1 ref | cycle amp |
|---|---|---|---|---|---|---|---|---|
| 0 | up | 0 | FIXED | 1 | 02167354 | 0.411 | 0.000 |  |
| 1 | up | 0.05 | FIXED | 141 | 02716354 | 0.062 | 0.429 |  |
| 2 | up | 0.1 | FIXED | 108 | 02716354 | 0.137 | 0.475 |  |
| 3 | up | 0.15 | FIXED | 145 | 02716354 | 0.241 | 0.555 |  |
| 4 | up | 0.2 | FIXED | 265 | 02716354 | 0.425 | 0.717 |  |
| 5 | up | 0.25 | FIXED | 360 | 24716305 | 0.905 | 1.208 |  |
| 6 | up | 0.3 | FIXED | 199 | 24716305 | 0.817 | 1.069 |  |
| 7 | up | 0.35 | CYCLE2 | 341 | 24716305 | 0.764 | 1.009 | 0.616 |
| 8 | up | 0.4 | FIXED | 236 | 24016375 | 0.782 | 1.056 |  |
| 9 | up | 0.45 | FIXED | 77 | 04216375 | 0.728 | 0.972 |  |
| 10 | up | 0.5 | FIXED | 75 | 04216375 | 0.690 | 0.907 |  |

#### DT_ε from class 1

| step | dir | level | attractor | settle bin | roles (slot of cell 0..7) | d to class-0 ref | d to class-1 ref | cycle amp |
|---|---|---|---|---|---|---|---|---|
| 0 | up | 0 | FIXED | 1 | 02167354 | 0.411 | 0.000 |  |
| 1 | up | 0.05 | FIXED | 119 | 02167354 | 0.459 | 0.078 |  |
| 2 | up | 0.1 | NONCONV (4 × 192 bins) | - | 07162354 | 0.539 | 0.233 |  |
| 3 | up | 0.15 | NONCONV (4 × 192 bins) | - | 02167354 | 0.688 | 0.384 |  |
| 4 | up | 0.2 | FIXED | 298 | 02167354 | 0.774 | 0.469 |  |
| 5 | up | 0.25 | NONCONV (4 × 192 bins) | - | 32760154 | 0.943 | 0.647 |  |
| 6 | up | 0.3 | CYCLE2 | 537 | 32160754 | 0.848 | 0.543 | 0.463 |
| 7 | up | 0.35 | CYCLE2 | 236 | 32160754 | 0.795 | 0.484 | 0.604 |
| 8 | up | 0.4 | FIXED | 201 | 32160754 | 0.724 | 0.421 |  |
| 9 | up | 0.45 | FIXED | 128 | 70162354 | 0.787 | 0.403 |  |
| 10 | up | 0.5 | FIXED | 83 | 02176354 | 0.786 | 0.385 |  |
| 11 | up | 0.6 | FIXED | 99 | 02176354 | 0.791 | 0.405 |  |
| 12 | up | 0.7 | FIXED | 116 | 02176354 | 0.820 | 0.446 |  |
| 13 | up | 0.8 | FIXED | 136 | 02176354 | 0.853 | 0.488 |  |
| 14 | up | 0.9 | FIXED | 161 | 02176354 | 0.880 | 0.527 |  |
| 15 | up | 1 | FIXED | 454 | 34160257 | 0.431 | 0.660 |  |
| 16 | down | 0.9 | FIXED | 79 | 34160257 | 0.410 | 0.639 |  |
| 17 | down | 0.8 | FIXED | 84 | 04163257 | 0.397 | 0.645 |  |
| 18 | down | 0.7 | FIXED | 88 | 04163257 | 0.400 | 0.645 |  |
| 19 | down | 0.6 | FIXED | 90 | 04163257 | 0.416 | 0.653 |  |
| 20 | down | 0.5 | FIXED | 134 | 04163257 | 0.493 | 0.686 |  |
| 21 | down | 0.45 | FIXED | 215 | 02163457 | 0.767 | 1.005 |  |
| 22 | down | 0.4 | FIXED | 118 | 02163457 | 0.538 | 0.742 |  |
| 23 | down | 0.35 | FIXED | 196 | 42163057 | 0.570 | 0.513 |  |
| 24 | down | 0.3 | CYCLE2 | 729 | 42163057 | 0.579 | 0.541 | 0.250 |
| 25 | down | 0.25 | FIXED | 438 | 42163057 | 0.713 | 0.628 |  |
| 26 | down | 0.2 | NONCONV (4 × 192 bins) | - | 04163257 | 0.291 | 0.526 |  |
| 27 | down | 0.15 | FIXED | 126 | 04163257 | 0.194 | 0.454 |  |
| 28 | down | 0.1 | FIXED | 101 | 04163257 | 0.119 | 0.406 |  |
| 29 | down | 0.05 | FIXED | 83 | 04163257 | 0.056 | 0.386 |  |
| 30 | down | 0 | FIXED | 62 | 04163257 | 0.000 | 0.411 |  |

#### Sensory-precision multiplier φ = ln F from class 0 (V = exp(3+φ))

| step | dir | level | attractor | settle bin | roles (slot of cell 0..7) | d to class-0 ref | d to class-1 ref | cycle amp |
|---|---|---|---|---|---|---|---|---|
| 0 | up | 0 | FIXED | 1 | 01234567 | 0.000 | 0.411 |  |
| 1 | up | 0.5 | FIXED | 76 | 01234567 | 0.040 | 0.405 |  |
| 2 | up | 1 | FIXED | 100 | 01234567 | 0.071 | 0.404 |  |
| 3 | up | 1.5 | FIXED | 93 | 01234567 | 0.092 | 0.409 |  |
| 4 | up | 2 | FIXED | 61 | 01234567 | 0.108 | 0.418 |  |
| 5 | up | 2.5 | FIXED | 55 | 01234567 | 0.120 | 0.424 |  |
| 6 | up | 3 | FIXED | 62 | 01234567 | 0.128 | 0.428 |  |
| 7 | up | 3.5 | FIXED | 64 | 01234567 | 0.133 | 0.430 |  |
| 8 | up | 4 | FIXED | 72 | 01234567 | 0.134 | 0.430 |  |
| 9 | up | 4.5 | FIXED | 96 | 01234567 | 0.135 | 0.429 |  |
| 10 | up | 5 | FIXED | 110 | 01234567 | 0.135 | 0.428 |  |
| 11 | up | 5.5 | FIXED | 155 | 01234567 | 0.135 | 0.427 |  |
| 12 | up | 6 | FIXED | 169 | 01234567 | 0.134 | 0.426 |  |
| 13 | down | 5.5 | FIXED | 172 | 01234567 | 0.135 | 0.427 |  |
| 14 | down | 5 | FIXED | 120 | 01234567 | 0.135 | 0.428 |  |
| 15 | down | 4.5 | FIXED | 88 | 01234567 | 0.135 | 0.429 |  |
| 16 | down | 4 | FIXED | 78 | 01234567 | 0.134 | 0.430 |  |
| 17 | down | 3.5 | FIXED | 61 | 01234567 | 0.133 | 0.430 |  |
| 18 | down | 3 | FIXED | 64 | 01234567 | 0.128 | 0.428 |  |
| 19 | down | 2.5 | FIXED | 60 | 01234567 | 0.120 | 0.424 |  |
| 20 | down | 2 | FIXED | 56 | 01234567 | 0.108 | 0.418 |  |
| 21 | down | 1.5 | FIXED | 88 | 01234567 | 0.092 | 0.409 |  |
| 22 | down | 1 | FIXED | 106 | 01234567 | 0.071 | 0.404 |  |
| 23 | down | 0.5 | FIXED | 88 | 01234567 | 0.040 | 0.405 |  |
| 24 | down | 0 | FIXED | 69 | 01234567 | 0.000 | 0.411 |  |

#### Sensory-precision multiplier from class 1

| step | dir | level | attractor | settle bin | roles (slot of cell 0..7) | d to class-0 ref | d to class-1 ref | cycle amp |
|---|---|---|---|---|---|---|---|---|
| 0 | up | 0 | FIXED | 1 | 02167354 | 0.411 | 0.000 |  |
| 1 | up | 0.5 | FIXED | 141 | 02167354 | 0.418 | 0.037 |  |
| 2 | up | 1 | FIXED | 345 | 02716354 | 0.424 | 0.112 |  |
| 3 | up | 1.5 | FIXED | 116 | 02716354 | 0.342 | 0.137 |  |
| 4 | up | 2 | FIXED | 119 | 02716354 | 0.343 | 0.156 |  |
| 5 | up | 2.5 | FIXED | 103 | 02716354 | 0.340 | 0.168 |  |
| 6 | up | 3 | FIXED | 75 | 02716354 | 0.336 | 0.178 |  |
| 7 | up | 3.5 | FIXED | 71 | 02716354 | 0.332 | 0.185 |  |
| 8 | up | 4 | FIXED | 72 | 02716354 | 0.330 | 0.192 |  |
| 9 | up | 4.5 | FIXED | 78 | 02716354 | 0.331 | 0.196 |  |
| 10 | up | 5 | FIXED | 104 | 02716354 | 0.332 | 0.199 |  |
| 11 | up | 5.5 | FIXED | 92 | 02716354 | 0.334 | 0.201 |  |
| 12 | up | 6 | FIXED | 82 | 02716354 | 0.335 | 0.202 |  |
| 13 | down | 5.5 | FIXED | 84 | 02716354 | 0.334 | 0.201 |  |
| 14 | down | 5 | FIXED | 104 | 02716354 | 0.332 | 0.199 |  |
| 15 | down | 4.5 | FIXED | 81 | 02716354 | 0.331 | 0.196 |  |
| 16 | down | 4 | FIXED | 73 | 02716354 | 0.330 | 0.192 |  |
| 17 | down | 3.5 | FIXED | 72 | 02716354 | 0.332 | 0.185 |  |
| 18 | down | 3 | FIXED | 72 | 02716354 | 0.336 | 0.178 |  |
| 19 | down | 2.5 | FIXED | 97 | 02716354 | 0.340 | 0.168 |  |
| 20 | down | 2 | FIXED | 125 | 02716354 | 0.343 | 0.156 |  |
| 21 | down | 1.5 | FIXED | 116 | 02716354 | 0.342 | 0.137 |  |
| 22 | down | 1 | FIXED | 202 | 02716354 | 0.424 | 0.112 |  |
| 23 | down | 0.5 | FIXED | 352 | 02167354 | 0.418 | 0.037 |  |
| 24 | down | 0 | FIXED | 92 | 02167354 | 0.411 | 0.000 |  |

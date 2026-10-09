# GENERALIZATION.md — Part 1 under protocol v2 (canonical clock, T_dev = 32; zero process noise)

Code: `code/p1_generalization.py` (runs), `code/p1_analyze.py` (analysis); numbers: `data/v2/p1_results.json`. Classification uses the v2 taxonomy: class 0 = within tau_pair = 0.170 of the empirical reference phenotype, class 1 = within tau_pair of the class-1 exemplar (secondary_0005), otherwise "other". Roles = slot assignment (Hungarian) to the reference. Wilson intervals are not given where n = 10 individuals per cell would make them uninformative; counts are shown. The individual is the unit of replication; mature bodies of different individuals are identical up to relabelling, so the family tables describe mostly one body.

## 1.1 Sixteen-cell census (30 individuals, randn(16,16)/8; 320 + 192 bins) — ESTABLISHED for n = 30
| | |
|---|---|
| Stationarity (state-based, declared) | 28 FIXED, 1 CYCLE2, 1 not stationary |
| 16-cell reference NN spacing | min 0.460, mean 0.801 → tau16 = 0.25 × min NN = **0.115** (rescaled to this template, as instructed) |
| Permutation-invariant single-linkage clusters at tau16 | **10 clusters; sizes 17, 2, 2, 2, 2, 1, 1, 1, 1, 1** |
| Dominant phenotype | 17 / 30 individuals (57 %, Wilson 95 % 39–73 %) |
| Smallest distance between clusters | 0.128 (just above tau16) |
So the 16-cell model is **multi-class**, in contrast to the 8-cell body where one class holds ~97 % of individuals. 13/30 individuals are in non-dominant clusters (several with 2 members, i.e. repeated alternative forms). PROVISIONAL: the cluster boundary is close to the within-cluster spread (max within-cluster d 0.207, via single-linkage chaining), so cluster counts at 10 ± 2 depend on tau16; no 16-cell template targets, hidden tier only.

## 1.2 Other perturbation families (individuals primary 0–9) — ESTABLISHED for these 10 individuals
FR = Friston-2015 Fig. 5-style intracellular secretion sensitivity ×2 on all cells (the m0c declared interpretation). PL = Pio-Lopez-2022-style high sensory precision on all cells. Pilot (3 values, V = exp(4..6) with the 8-cell baseline exp(3)·F): **the clump-like phenotype of the paper was not reproduced at any pilot value** (d to reference only 0.07–0.13); V = exp(6) (F = exp 3) was used.

| Family × timing | n | Classes at stationarity | Notes |
|---|---|---|---|
| FR sustained | 10 | **10 "other"** (d to reference 0.784, identical across individuals) | a robust novel phenotype under sustained ×2 |
| FR DEV-LONG (0→W, then off) | 10 | 10 class 0 | returns to the reference shape |
| FR ADULT (W bins on) | 10 | 10 class 0 | **roles relabelled 10/10** with the shape unchanged (cf. DH-ADULT 0/20, AN-ADULT 6/20) |
| PL sustained | 10 | 9 class 0 (d 0.128, a persistent shift but < tau), 1 other (d 0.336) | |
| PL DEV-LONG | 10 | 10 class 0 | |
| PL ADULT | 10 | 10 class 0 | 0 relabelled |
**Reading:** neither family produces a clump-like or class-1 shape. FR is the only family that durably relabels a mature body with no shape change (10/10, one effective body), and the only one with a robust novel sustained phenotype. The PL "class 0" label at d = 0.128 is a shifted shape below the declared tau; NOT claimed as no effect.

## 1.3 High initial identity expectation (k = 2, 4 cells; 10 individuals each) — ESTABLISHED for these individuals
| k | Classes | Roles of the k seeded cells equal to the default individual's |
|---|---|---|
| 2 | 10 class 0 | 1/10 (the seeded identity does NOT fix the roles) |
| 4 | 8 class 0, **2 class 1** (individuals 5 and 9; d = 0.411 each) | 0/10 |
Initial beliefs bias the developmental trajectory (class 1 appears in 2/10 at k = 4, versus 0/50 for the default primary individuals (CENSUS_V2.md; the same seeds 0–9 are class 0 without the manipulation)) but the seeded cells do not keep their seeded roles; the result is not a stable role assignment by initial expectation. PROVISIONAL (n = 10 each; Wilson 95 % for 2/10: 6–51 %).

## Not done
Other families (Kuchling DT/DH, noise) are covered in R1–R4; no parameter sweeps of PL beyond the 3-value pilot; 16-cell perturbation experiments NOT DONE.

# METHODS_AUDIT.md — Stage 6 (flock) Phase 0

Upstream repository: https://github.com/dommai/flock_knows_what_birds_dont
Upstream commit: `06be55a45091e0883479f981e273410400bb7c3b` (branch `main`, 3 commits total:
`30daf89` initial commit, `15b3a87` add files via upload, `06be55a` update README).
Files present upstream (4 total, matches upstream README claim of "four MATLAB files"):
`flocking_AIF_simulation.m`, `active_inference_bird_control.m`,
`getMarkovBlanketOfFlock.m`, `script_execution.m`. License: GNU GPLv3 (full text in
`upstream/LICENSE`). GPLv3 permits redistribution of verbatim source, so the four
`.m` files, the upstream `README.md` (saved as `upstream/README_upstream.md`), and
`upstream/LICENSE` are committed verbatim under `stage6_flock/upstream/`, together with
`UPSTREAM_COMMIT.txt` recording the exact hash above. Nothing in the upstream code was
edited; the port lives entirely in `python/`.

This document is built **only** from reading the four `.m` files above line-by-line
(no MATLAB/Octave was available in this environment — see PORT_VALIDATION.md for how
that constrains verification). Every claim below cites the source file and, where
useful, the line region.

---

## 1. Population and lattice

- **Number of birds**: `nn = 100` by default (`flocking_AIF_simulation.m` line ~33),
  overridable via `param.nn` or implicitly via `numel(param.conf)`.
- **Lattice size**: `l = sqrt(nn)` (`buildW`, line 432; also `getMarkovBlanketOfFlock.m`
  line 32, `plotFlock` line 792). For `nn=100`, `l=10`, i.e. a 10×10 grid.
- **Indexing convention**: birds are addressed by a single linear index `i = 1..nn`,
  **column-major** ("linearly numbered by columns in a grid deployment", comment at
  line 33). This is confirmed by `plotFlock`/`showDiffusionPlot`, which recover 2-D
  coordinates via `[I,J] = ind2sub([L,L],n)` — MATLAB's `ind2sub` is column-major, so
  bird `n` sits at row `I`, column `J` where `n = I + (J-1)*L`. **Port implication**:
  when reshaping a length-100 state vector into a 10×10 lattice for display or for
  neighbor sanity checks, use `order='F'` (Fortran/column-major) reshape, not the
  NumPy default `order='C'`.
- **Boundary conditions**: `buildW` (lines 422-475) builds the up-to-8 Moore neighbors
  of site `i` using guards `mod(i,l)~=1` (has a left neighbor `i-1`), `mod(i,l)~=0`
  (has a right neighbor `i+1`), `i>l` (has a top neighbor `i-l`), `i<=(nn-l)` (has a
  bottom neighbor `i+l`), and the four diagonal combinations thereof. **There is no
  wraparound anywhere in `buildW`.** Boundary conditions are therefore **free/open**,
  not periodic/toroidal: edge birds have 5 neighbors, corner birds have 3. This is a
  point the paper does not state explicitly (it only says "coordination number M=8");
  the actual coordination number is only 8 for interior sites in this 10×10 grid,
  strictly fewer at the boundary. **This must be preserved in the port** — do not
  silently switch to a torus.
- **Neighbor layout used consistently across the codebase** (the docstring comment
  repeated in three files):
  ```
        5   1   8
        3   i   4
        7   2   6
  ```
  i.e. neighbor slot 1 = up (`i-l`... wait, see below), slot 2 = down, 3 = left,
  4 = right, 5 = up-left, 6 = down-right, 7 = down-left, 8 = up-right, **in the
  `uv` direction table** (see §3). The `buildW` construction order is actually
  `[i-1 (left), i+1 (right), i-l (top/up), i+l (bottom/down), i-l-1, i+l+1, i-l+1,
  i+l-1]` for `nh` values 1..8, i.e. `W{i}` is a length-`nn` indicator vector (not
  ordered the same way as `uv`); the actual direction semantics come from `uv` and
  `compAexceps`, not from the order of nonzeros in `W`.

## 2. State representation

Each bird has **two hidden-state factors** (`mdp.Nf = 2`):

1. **Factor 1 — heading**, `z_i ∈ {1,...,nu}`, `nu = 4` by default (`param.nu`,
   catch-default 4). The four states correspond to the cardinal directions via the
   unit-vector table `uv` in `buildA` (line 493):
   `uv = [0,1; 0,-1; -1,0; 1,0; -.7071,.7071; .7071,-.7071; -.7071,-.7071; .7071,.7071]`,
   i.e. state 1 = up `(0,1)`, 2 = down `(0,-1)`, 3 = left `(-1,0)`, 4 = right `(1,0)`,
   and (only used if `nu>4`, not the default) 5-8 are the diagonals. **Default runs use
   only the 4 cardinal directions**; the code supports an 8-direction Potts variant
   (`nu=8`) but this is not the default and is not what the paper's `q=4` Potts
   Hamiltonian (Eq. 1) describes.
2. **Factor 2 — stress/danger**, `z*_i ∈ {1,2}` where state 1 = "not in danger" /
   quiescent and state 2 = "in danger"/stressed (`mdp.s(:,1) = [st{i}.s, 2]'` when
   `any(out)` i.e. a neighbor is stressed, `flocking_AIF_simulation.m` lines 296-321).
   This factor's transition is **not** driven by the active-inference policy solver
   (its `B{2}` is the identity, line 207: `B{i}{2}(:,:,u)=eye(2)`) — instead it is set
   *exogenously* by the outer loop every timestep, based on (a) whether any of bird
   `i`'s neighbors are currently stressed (`out`), and (b) a refractory-period /
   exponential-decay rule using `T_refract` (default 10) and `tau` (default 2) — see
   §7 for the exact rule and the discrepancy vs. the paper's Eq. 9.

**Bird = active inference agent with sensory, active, and internal states** exactly as
Section A.1 states; in MDP terms "internal" ≈ posterior beliefs `mdp.X`, "sensory" ≈
observations `mdp.o`/`mdp.O`, "active" ≈ sampled action `mdp.u` / hidden state
`mdp.s`.

## 3. Observation / likelihood model (the `A` matrix, Eq. 2-4)

`buildA(i, nidx, nn, nu, vm, ca, fc)` builds, for each neighbor `nidx` of bird `i`, a
`(2*nu) × nu` matrix in two "outcome-modality" slices (`Ai(:,:,1)` = "not in danger"
modality, `Ai(:,:,2)` = "in danger" modality), later normalized by `softmaxA` (a
column-wise `spm_softmax` with two different precisions per modality). The two rows
per candidate outcome `o` (rows `2o-1`, `2o`) implement the two components of `R(i,j)`
in Eq. 4: alignment bonus `vm` (velocity matching, only on the diagonal `s==o`) and
`fc`/`ca` (flock-centering vs. collision-avoidance) depending on the relative lattice
position of the neighbor, handled by `compAexceps` (lines 524-657), which special-cases
the 8 relative positions (top/down/left/right/4 diagonals) exactly as Eq. 4's
case-split on `θ` and `η_i-ζ_j`. Confirmed exact default parameter values match the
paper: `vm=4, ca=2, fc=1` (`flocking_AIF_simulation.m` lines 53-66; paper §A.2 states
the same numbers). This is a directly-verified match.

- Likelihood factorizes over neighbors: `P(σ̃|z^i) = ∏_j P(σ^j|z^i)` (code: each
  neighbor contributes an independent `A{i}{s-1}` slice, combined via `spm_dot` over
  the neighbor-outcome dimensions inside `active_inference_bird_control.m`). Matches
  Eq. 2-3.
- Observation-precision parameters: `precAbird` (β when the *observed neighbor* is not
  in danger, default 1) and `precApred` (β when the observed neighbor is in danger,
  default 1) — **these do match the paper's stated "temperature parameters ... set
  equal to 1"** for β.

## 4. State-transition model (the `B` matrix, Eq. 5) — heading factor only

`B{i}{1}(:,:,u) = spm_softmax(repmat(ucell,1,nu), precB)` where `ucell` is a one-hot
column at position `u` (lines 199-208). This is column-wise softmax of a matrix whose
every column equals the same one-hot vector scaled by `precB` — i.e. **every column of
`B{1}(:,:,u)` is identical**, so `P(z_t=k | u_t=u)` does not depend on `z_{t-1}` at all;
the transition is a pure (softmax-noised) "jump to direction `u`" independent of the
previous heading. This exactly matches Eq. 5's `P(z_t|u_t;ρ)` (which likewise has no
`z_{t-1}` dependence) and answers the audit question **"does the action directly
determine heading, or something subtler": the action *is*, up to softmax noise
governed by `precB`, the commanded next heading** — there is no separate "turn
left/right" semantics; `u ∈ {1,2,3,4}` = {up, down, left, right} directly.

- **Discrepancy vs. paper text**: the paper's Appendix A.2 states "all the temperature
  parameters β, ρ, and ω used in the distributions were set equal to 1." The code's
  default is `precB = 15` (`flocking_AIF_simulation.m` line 81; this is `ρ` in Eq. 5's
  notation) — **not 1**. At `ρ=15` the transition is extremely concentrated (near
  one-hot / near-deterministic jump to the commanded action), whereas `ρ=1` would be
  substantially noisier. `script_execution.m` calls `flocking_AIF_simulation` with no
  parameters, so **the actual default/reported simulations almost certainly used
  `ρ=15`, not `ρ=1` as the text states.** This is flagged, not silently resolved; the
  Python port defaults to matching the *code* (`ρ=15`) since that is what actually ran,
  with the paper's stated value available as an alternate config for sensitivity
  checks.

## 5. Preference / goal-prior model (the `C` vector, and Eq. "future outcomes")

`C{i}{s-1,1} = spm_softmax(vecC, precC)` where `vecC` is `+1` at the "not-in-danger"
preferred outcome index (`o{i}(s-1,1)`, the previously *observed* — i.e. neighbor's
current — heading, used as the alignment target) and `-1` at the corresponding
"in-danger" index when a neighbor is stressed (lines 258-280). Default `precC = 3`
(paper's `ω`). **Second discrepancy vs. the "all set to 1" text**: default `precC=3 ≠
1`. Recorded, not silently changed.

For the *stress-observation* preference (`ω` in Eq. "the goal probabilities follow a
Boltzmann distribution conditioned on the state of the neighboring birds", §A.2 last
paragraph before A.3): this is a description of `C`'s role generally, not a separate
parameter; `precC` is the only relevant knob and is covered above.

## 6. Policy / action-selection rule (Eq. 6-7, and `active_inference_bird_control.m`)

- Policies `V`: `mdp.V = repmat(1:nu, T, 1)` with **`T = 2`** hardcoded in
  `flocking_AIF_simulation.m` line 158 — i.e. each policy is a *constant* action held
  for the 2-step horizon, giving exactly `Np = nu` (4, by default) candidate policies:
  "go up for the lookahead", "go down...", etc. This is a **one-step-ahead expected
  free energy comparison over the 4 cardinal actions**, not a multi-step planning
  problem, matching the paper's informal description ("infers hidden states... and acts
  to minimize prediction error") but worth stating explicitly since T=2 is not derivable
  from the manuscript text alone.
- `G(u)` (expected free energy per policy) implemented via the standard SPM active-
  inference decomposition (ambiguity term `H` + risk term `(lnC - ln qo)'qo`), consistent
  with Eq. 7's derivation (`active_inference_bird_control_t`, lines 132-178).
- Precision/policy posterior: `mdp.ut(:,t) = softmax(W(t)*G)`, with `W(t)` **self-tuned**
  via a small number (`mdp.N=4` default) of variational iterations using
  `alpha=8, beta=4, lambda=0` (standard SPM defaults, not mentioned in the paper's main
  text at all — these are generic active-inference solver hyperparameters, not part of
  the flocking-specific model described in §A.2, and are left at the SPM defaults in
  the port).
- **Action sampling is stochastic**: `a = find(rand < cumsum(mdp.P(:,t)), 1)` — the
  bird does **not** deterministically take the arg-max action; it samples from the
  posterior `P(u|·)` (line 226). This is a distinct RNG draw from the state-transition
  sampling draw described next.
- **Next-state sampling is stochastic and separate**: given the *sampled* action `a`,
  the next heading is drawn via `st(f) = find(rand < cumsum(mdp.B{f}(:,mdp.s(f,t),a)), 1)`
  (line 248-250) — i.e., even after the action is chosen, the realized next heading is
  a further categorical draw from the (noisy) `B` column for that action. **Two
  independent stochastic draws per bird per timestep** for the heading factor: (1)
  which action to commit to, (2) which heading actually results. The port must
  reproduce this two-draw structure, not collapse it into one.

## 7. Stress-state dynamics (Appendix A.3 vs. code) — outer-loop rule

Implemented **outside** the generic MDP solver, directly in
`flocking_AIF_simulation.m` lines 296-321, once per bird per timestep, *before*
calling `active_inference_bird_control`:

```
out = [neighbor.d > 1 for each of i's neighbors]   # any neighbor currently stressed?
if st{i}.d == 1:                                    # currently NOT stressed
    if t_post(i) > T_refract:
        if any(out):  s2=[s,2], D2=[0,1]  (becomes stressed; contagion)
        else:         s2=[s,1], D2=[1,0]  (stays calm)
    else:             s2=[s,1], D2=[1,0]  (still in refractory quiet period, stays calm)
                      t_post += 1
else:                                                # currently stressed (d==2)
    prob = D{i}{2}(2) * exp(-1/tau)                  # exponential decay of stress prob.
    D2 = [1-prob, prob]
    s2 = [s, 1+round(prob)]                          # rounds prob to {0,1} -> next d
```

This is a **plausible but not literal** implementation of the paper's Eq. 9 three-
regime block-matrix description (`t̄` onset, decay over mean-life `τ`, hard reset to 0
for a refractory window `T_r`, matrix form `P(z*_t|u_t; t̄,τ,T_r)`). The code instead
uses (a) a running per-bird refractory counter `t_post` that only resets when the bird
actually becomes stressed, and (b) a continuously-compounding exponential decay
`prob *= exp(-1/tau)` rather than a fixed decay-then-reset schedule keyed to an onset
time `t̄`. Both encode "decays with time-constant τ, then quiescent for `T_refract`
steps," but the **exact functional form differs from Eq. 9's tabulated matrix** (Eq. 9
is deterministic-then-deterministic within each regime; the code's decay is a smooth
geometric decay feeding a Bernoulli-ish rounding step `1+round(prob)`, which is
actually **deterministic given `prob`** — `round` on `[0,1)` snaps to 0 or 1 — so despite
appearances there is *no* additional randomness injected in this line beyond whatever
randomness produced `prob` itself, i.e., the stress-decay path is close to
deterministic decay with a hard 0.5 threshold, not a coin flip). Confirmed defaults
match the paper: `T_refract=10`, `tau=2` (paper: "we set τ=2 and Tr=10" — exact match).

Predators are injected via `param.predators`, a per-timestep `containers.Map` keyed by
bird-index string; `setStateNinitBelief` (lines 668-679) forces `st_i.d=2` (stressed)
and either uses a prescribed direction (`predators{1,t}(string(i))>0`) or samples a
random heading from `pu` for that bird at that timestep, then **skips calling
`active_inference_bird_control` entirely for that bird that step** (line 331-334:
`if isKey(predators{1,t}, string(i)); MDP{...}=mdp; continue; end`) — i.e. a "predator"
bird's action that timestep is not chosen by active inference at all; its `mdp` is
just recorded with the forced state. This is the exact mechanism the paper's "predator
appears at a random position" perturbation uses, and is architecturally the *same
hook* (skip-and-force) we should reuse for the control interventions in Phase 3,
rather than inventing a new override path.

## 8. Update schedule

- **Synchronous by default** (`asynch=0`): all `nn` birds are updated within a single
  timestep `t`, each reading `MDP{e}{b}{t-1}{i}` (previous *global* timestep) for
  history and using `sts`/state read from `st{j}` for the *current-step, in-progress*
  computation of the other factor's belief inputs — but the actual action/heading
  sample used to build `o{i}` (the neighbor observation) is deliberately the previous
  timestep's realized state (`MDP{e}{b}{t-1}{...}.s(1,T)`), so within a timestep,
  neighbor observations are read from `t-1`, not from other birds' not-yet-computed `t`
  values — i.e. genuinely synchronous / simultaneous update, no order-dependence
  within a sweep. Verified from `setStateNinitBelief`'s state read `s2ck` loop with the
  `t-1` fallbacks chained across trial/epoch boundaries at lines 244-256.
- **Asynchronous mode exists but is not the default** (`asynch=1` updates a random
  `asynchUpdtPercent`% (default 70%) subset of birds per step, the rest copy forward
  their previous `MDP` entry). Not used by `script_execution.m`. The port implements
  synchronous update as the primary path and treats asynchronous as an optional,
  clearly-labeled config toggle.
- Loop nesting: epochs (`ne`, default 1) > trials/batch (`nb`, default 1) > timesteps
  (`nt`, default 60) > birds (`nn`, default 100). Cross-trial/epoch continuity is
  handled by the fallback-chain in `setStateNinitBelief` (a trial's `t=1` reads the
  previous trial's `t=nt`). The port's `nb=1, ne=1` default makes this irrelevant for
  Experiment 1 but is documented for completeness.

## 9. Initialization

- `rng('default')` is called at the **top of `flocking_AIF_simulation.m`** (line 8) —
  this resets MATLAB's global RNG to its fixed default state (Mersenne Twister, seed 0)
  **every single time the function is called**, before any sampling happens.
  **Critical consequence**: calling `flocking_AIF_simulation()` twice in a row with the
  same `param` (as `script_execution.m`'s single call does) will, given MATLAB's
  RNG semantics, run the **exact same fixed random sequence** both times — i.e., **the
  publicly released code, run as-is via `script_execution.m`, is not stochastic across
  separate invocations of the top-level function.** The paper's reported ensembles
  (500 simulations for Fig. 2; 1000 for Fig. 3) therefore **cannot have been produced by
  looping calls to the public `flocking_AIF_simulation.m` unmodified** — some external
  seed-varying mechanism (e.g. `rng('shuffle')` before each call, or a per-simulation
  seed argument) must have been used in the authors' actual experiment driver, which is
  **not included in the 4 released files**. This is an important, explicitly-flagged
  **gap between what the released code can reproduce standalone and what the paper's
  multi-run ensemble figures required.** The Python port therefore does **not** attempt
  to bit-reproduce "the" published ensemble; it treats each simulation run as seeded by
  an explicit `numpy.random.Generator(seed=...)` supplied by the caller, varying the
  seed across replicates by our own explicit protocol (documented in PROTOCOL_V1.md).
- Initial heading `z_0 ~ Categorical(pu)`, default `pu = uniform(1/nu,...,1/nu)`
  (`param.pu` else uniform, lines 88-97; consumed in `setStateNinitBelief`'s outer
  `catch` branch, line 720: `st_i.s = find(rand < cumsum(pu), 1)`). Matches paper's
  "z_0 ∼ Cat(1/q,...,1/q)" (Eq. 5 caption).
- Initial stress state `d_0 = 1` (not stressed) for all birds absent a predator event
  (line 721: `st_i.d = 1`), initial belief `D{2}=[1,0]'`.
- `conf` parameter allows a fully prescribed initial configuration (`conf{i}.s`,
  `conf{i}.d`) bypassing random init — useful for the port's canonical-snapshot /
  reproducibility needs, and for constructing controlled restart conditions in Phase 3.

## 10. Markov-blanket / Fiedler analysis (`getMarkovBlanketOfFlock.m`)

- **Time window**: `TW` (default 5) trailing timesteps starting at `tsign`
  (`TW` is exactly the paper's `T_w`; default value 5 is **not stated anywhere in the
  main text** — the paper only says "by fixing a time window `T_w`"; **5 is the code's
  default and the only concrete value available**, so the port's default `T_w=5` is
  taken from code, not text).
- **Adjacency construction**: for every unordered pair `(i,j)` (including `i=j`, see
  below) and every `t` in `[tsign, tsign+TW-1]`, `A(i,j) += 1` iff
  `heading_i(t) == heading_j(t)`, symmetrized (`A(j,i)=A(i,j)`) (lines 36-52). This
  matches the paper's "edges denote the fact that two birds fly in the same direction,
  at least once in `T_w`" **only loosely** — the code's `A(i,j)` is actually a **count**
  of the number of *co-occurring timesteps* with equal heading (0 to `TW`), not a binary
  "at least once" indicator as the manuscript prose states. This is a real
  code/manuscript wording mismatch: the manuscript's supplementary text (§A.4) says
  edge weight = "number of times the nodes are connected (have equal direction)" — that
  *does* match the code (a genuine weighted count) — but the main-text Fig. 1 caption's
  informal description ("at least once") is looser than what's actually computed. The
  port implements the code's weighted-count version, since §A.4 and the code agree.
- **Self-loops**: the `j=i` term is included in the double loop (`for j=i:nn`), so
  `A(i,i)` accumulates `+1` for every `t` where bird `i` "agrees with itself" — which
  is every `t` in the window (a heading always equals itself) — giving **`A(i,i) = TW`
  for every bird, unconditionally**. This directly inflates the degree matrix
  `D = diag(sum(A,2))` by a constant `TW` per node relative to a self-loop-free graph.
  **This is a real, easily-missed implementation detail**: the graph Laplacian used for
  the Fiedler computation is built from a matrix with a nonzero, uniform diagonal.
  Because `L = D - A` and `A`'s diagonal exactly cancels the diagonal contribution to
  `D` from self-loops in the standard Laplacian identity (`L_ii = sum_{j≠i} A_ij`
  either way, since `D_ii = sum_j A_ij` includes `A_ii`, and `L_ii = D_ii - A_ii = sum_{j≠i}
  A_ij` regardless of `A_ii`), **the self-loops are numerically inert for `L` itself** —
  `L` is exactly the same whether or not the diagonal self-count is included. Verified
  algebraically and will be spot-checked numerically in Phase 1A. The port still
  reproduces the code's literal `A` (diagonal = `TW`) for byte-level fidelity of any
  code that inspects `A` directly (e.g. `sum(A(node,:))` in
  `information_flow_interpretation`, which **does** include the self-loop in "total
  connections" reporting — a cosmetic-only `fprintf`, not used in the actual
  classification logic).
- **Laplacian**: `L = D - A`, `D = diag(sum(A,2))` — standard (unnormalized) graph
  Laplacian, **not the symmetric-normalized Laplacian** despite the code comment
  "% normalized Laplacian" at line 54 (this comment is simply wrong / a documentation
  bug in the upstream code — `D - A` is the combinatorial Laplacian; the normalized
  Laplacian would be `I - D^{-1/2} A D^{-1/2}`). **Flagged as an upstream comment
  error**; the port implements what the code actually computes (`D-A`), not what the
  comment claims.
- **Eigendecomposition**: MATLAB `[eigenvectors, eigenvalues] = eig(full(L))` — full
  dense symmetric eigendecomposition, eigenvalues sorted ascending via `sort(eigenvals)`
  and the vector for the **2nd-smallest** eigenvalue taken as the Fiedler vector
  (`idx(2)`) (lines 58-64). Note MATLAB's `eig` on a symmetric matrix returns
  orthonormal eigenvectors but with an **arbitrary sign** per eigenvector (LAPACK
  convention, not fixed relative to any external reference) — this is exactly the
  "arbitrary sign" issue flagged in the task brief; the port must not compare raw
  Fiedler signs across time or across MATLAB vs. NumPy without re-aligning.
- **Fiedler normalization**: `fiedler_norm = fiedler_vector / max(abs(fiedler_vector))`
  — i.e. **max-abs normalization to `[-1,1]`**, not unit-L2-norm (which is what `eig`
  already gives before this rescaling). The port must apply this exact rescaling before
  thresholding, since the `0.05` absolute threshold below is calibrated to a max-abs-
  normalized vector, not a unit-norm one.
- **Community / boundary partition** (`information_flow_interpretation`, lines
  129-150):
  - `core1_nodes = find(y2 > quantile(y2, 0.8))` — **top 20%** by value (strictly
    greater than the 80th percentile).
  - `core2_nodes = find(y2 < quantile(y2, 0.2))` — **bottom 20%** (strictly less than
    the 20th percentile).
  - `boundary_nodes = find(abs(y2) < 0.05)` — **fixed absolute threshold 0.05**, not
    a percentile of `|y2|`. **This directly contradicts the paper's main-text claim**
    ("threshold α... typically set to capture nodes within the 10th-20th percentile of
    absolute Fiedler values", §A.4) — the actual code uses a **hardcoded absolute
    cutoff (0.05) on the max-abs-normalized vector**, not an adaptive percentile rule
    at all. This is one of the most important discrepancies in the whole audit: the
    manuscript's own supplementary text describes an adaptive percentile rule that the
    released code does not implement. The port implements **both**: the code's literal
    fixed-0.05 rule (default, since that is what actually produced the paper's figures)
    and an optional adaptive-percentile variant (10th-20th percentile of `|y2|`, per
    the manuscript text) as an explicitly separate, clearly-labeled config option —
    never silently substituted for the other.
  - Note the three sets (`core1`, `core2`, `boundary`) are **not guaranteed to
    partition** `{1..nn}`: a node with `y2` between the 20th and 80th percentile *and*
    `|y2| ≥ 0.05` belongs to **none** of the three sets (it is simply never classified,
    dropped from the "External" role by default in `getMarkovBlanketOfFlock.m`'s color
    map, which pre-fills `C=zeros(nn,1)` = color 0 = "internal" for every node, then
    only overwrites `core2_nodes→1` and boundary nodes → 2 or 3; **any node in neither
    core1, core2, nor boundary is left at the "internal" default color of `core1`'s
    slot,** i.e. it is silently lumped in with whichever of core1/core2 is *not*
    explicitly assigned. Re-reading the code: `C=zeros(nn,1)` (default label 0),
    `C(core1_nodes)=0` (redundant, already 0), `C(core2_nodes)=1`. So **every node not
    in `core2_nodes` or `boundary_nodes` — including nodes that are neither core1 nor
    core2 nor boundary — is labeled 0 ("internal") by default.** This means the
    colormap label "0/internal" is really "**not core2 and not boundary**", a strict
    superset of `core1_nodes`. **This is a real classification-logic subtlety the port
    must reproduce exactly** rather than "fixing," since Fig. 1D's four-color
    classification in the paper is generated by this exact code path.
  - `refclust` (optional 4th argument) lets the caller specify which set of birds
    should be labeled "internal" (`core1`) by checking `sum(ismember(core1_nodes,
    refclust)) < sum(ismember(core2_nodes,refclust))` and swapping `core1↔core2` (and
    their boundary connection-strength vectors) if `core2` overlaps `refclust` more.
    **This is the sign/orientation-alignment mechanism already built into the upstream
    code** — it is exactly the "orient the Fiedler sign so the side best overlapping
    `I_0` is the current continuation of the macro-agent" operation the task brief asks
    for in Phase 2C. The port's `align_fiedler_to_reference()` in `spectral.py`
    reimplements this exact rule (compare-and-swap by raw overlap count, not Jaccard),
    for direct fidelity to the paper's own method, with Jaccard also computed
    separately as an additional diagnostic.
  - Boundary-node role (active vs. sensory) is decided per boundary node `i` by
    comparing its total edge weight to `core1_nodes` (`conn_cluster1(i)`) vs.
    `core2_nodes` (`conn_cluster2(i)`): `conn_cluster1 >= conn_cluster2` → color 2
    ("active" in the plotted colormap `mymap` row 3 = red = active); else color 3
    ("sensory", row 4 = magenta). **Note**: the code's own comment/labels call rows
    `[internal; external; active; sensory]` but the *actual* semantics implemented are
    "core1(label0)=internal, core2(label1)=external, boundary-closer-to-core1(label2)=
    active, boundary-closer-to-core2(label3)=sensory" — i.e. "active" and "sensory" are
    not principled active-inference-theoretic roles here, just a closer-to-core1 vs.
    closer-to-core2 split of the boundary. This matches the paper's Fig. 1 caption
    description reasonably well (boundary birds split by which side they lean toward)
    but should not be over-interpreted as literally encoding the generative model's
    action/observation channels — it is purely graph-connectivity-based.
- **Disconnected graphs**: `getMarkovBlanketOfFlock.m` does **not** check graph
  connectivity anywhere. If the heading-agreement graph over the chosen window happens
  to be disconnected (plausible early in a simulation, or with a small `TW`), `L` will
  have a Laplacian eigenvalue 0 with multiplicity ≥ number of connected components, and
  `idx(2)` (the "2nd smallest") may or may not be a genuine algebraic-connectivity
  Fiedler vector — it will simply be *some* eigenvector belonging to the 2nd sorted
  eigenvalue, whose meaning is ill-defined when eigenvalue 0 is degenerate. **The
  upstream code silently proceeds regardless.** The port explicitly computes and logs
  the number of zero eigenvalues (= number of connected components) and `λ2, λ3,
  λ3−λ2` at every call, and flags (without silently discarding) any window where
  `λ2 ≈ 0` (degenerate/disconnected) per the task brief's Gate/anomaly-reporting
  requirements.

## 11. What in the paper's figures is directly reproducible from the 4 public files

- **Fig. 1A** (8-step lattice snapshots) and the underlying flocking dynamics: fully
  reproducible from `flocking_AIF_simulation.m` + `script_execution.m` (case 0, no
  predators).
- **Fig. 1B-D / getMarkovBlanketOfFlock.m outputs**: fully reproducible given a
  `sts`-like heading-history array, using the released function as-is.
- **Fig. 2 (predator destabilization, energy/stress traces over 500 simulations)** and
  **Fig. 3 (PID/synergy analysis over 1000 simulations, coarse-grained 2×2 predator
  quadrants)**: the **single-run predator mechanism** (`param.predators`, `tattacks`,
  stress propagation) is present and reproducible via `script_execution.m` case 1, but
  the **multi-run driver, the RNG-varying loop across 500/1000 simulations, the vector-
  Potts energy computation (Eq. 1) as an explicit reported time series, the 60-time-step
  ×1000-simulation PID/mutual-information pipeline (§A.5), and the 2×2 spatial coarse-
  graining of predator location are all absent from the 4 released files.** These are
  **analysis code, not simulator code**, and were evidently run with additional,
  unreleased scripts. **The port's `metrics.py`/`spectral.py`/(future) PID modules
  reimplement these analyses from the paper's explicit equations (Eq. 1, Eq. 11-12,
  §A.5) since no reference implementation exists to validate against** — this is
  flagged as a validation gap in PORT_VALIDATION.md, not hidden.
- The Potts Hamiltonian `H` (Eq. 1) itself is never explicitly computed or logged
  anywhere in the released code (the closest quantity, `compHamiltonian`/`H` in
  `flocking_AIF_simulation.m` line 783-784, computes a *different* quantity — a sum
  over birds of `(number of matching observations) - h*(final heading state index)`,
  which is **not** the Potts Hamiltonian of Eq. 1 at all, just a same-named internal
  free-energy-like bookkeeping variable used only for the diagnostic plot at line
  380-382). **This is a naming collision, not the same quantity as the paper's `H` in
  Eq. 1** — flagged explicitly so the port's own `metrics.energy()` (implementing the
  real Eq. 1 Potts Hamiltonian, `J_P * sum_{(i,j) in M} δ(z_i,z_j)`) is never confused
  with the code's `compHamiltonian`.

## 12. RNG usage inventory (every place randomness is drawn)

| Site | File:line | Purpose |
|---|---|---|
| `rng('default')` | `flocking_AIF_simulation.m:8` | resets global RNG at top of every call (see §9 caveat) |
| `rng('default')` | `getMarkovBlanketOfFlock.m:22` | resets global RNG (has no downstream random draws in this file — vestigial/defensive) |
| `randsample(nn, round(nn*0.01*pct))` | `flocking_AIF_simulation.m:190` | asynchronous-mode subset selection (not default path) |
| `find(rand < cumsum(pu),1)` | `setStateNinitBelief` via `flocking_AIF_simulation.m` (called at line 228) | initial heading sample, and predator random heading when `predators{...}(i) <= 0` |
| `find(rand < cumsum(mdp.P(:,t)),1)` | `active_inference_bird_control.m:226` | **action** sampled from posterior policy beliefs |
| `find(rand < cumsum(mdp.BB{f}/mdp.B{f}(:,s,a)),1)` | `active_inference_bird_control.m:248-250` | **next hidden state** sampled given the chosen action (heading AND, in principle, stress factor — but stress factor's `B{2}` is `eye(2)`, i.e. deterministic given its already-externally-set `mdp.s(2,:)`, so this draw is only ever non-trivial for factor 1/heading) |
| `find(rand < cumsum(mdp.pO{g}(:,t+1)),1)` | `active_inference_bird_control.m:267` | next **observation** sampled from the predictive outcome distribution |

Every bird, every timestep (after `t=1`), consumes **3 independent uniform draws**
in this order: (1) action choice, (2) next hidden state, (3) next observation — **per
outcome modality `g`** for the observation draw, and this happens **inside the generic
solver called once per bird**, so per-bird RNG consumption is not interleaved at the
population level in a single shared stream in the way a hand-vectorized Python
version might assume. **Port implication for common-random-numbers (Phase 3/4)**: to
get valid paired baseline/controlled comparisons, the Python port must consume RNG
draws for a given bird in the same relative order (action → next-state → next-
observation) *before* any override is applied, exactly as the task brief specifies,
and this order is now confirmed directly from source, not assumed.

## 12a. Minor wording note on Eq. 3's normalization

The paper's Eq. 3 writes the denominator as `sum_{k=1}^{M} exp{-beta R(i,k)}`,
summing over the neighbor index `k` (size `M`, the coordination number).
Read literally this would not normalize a likelihood over the outcome variable
`sigma^j`. The code's actual `softmaxA`/`spm_softmax` normalizes **columns** of
the `(2*nu) x nu` matrix, i.e. sums over the **outcome** dimension (size `nu`,
not `M`) for each fixed hidden state — the mathematically necessary
normalization for a proper likelihood `P(sigma^j|z^i)`. This is treated as
notational looseness in Eq. 3 (reusing the summation-bound symbol `M` where
`nu`/the outcome-alphabet size was intended), not a second implementation to
reconcile — the code's column-stochastic construction is unambiguous and is
what the port implements (`model.neighbor_likelihood`, verified
column-stochastic in `tests/test_model.py`).

## 13. Summary of confirmed discrepancies (manuscript vs. released code)

1. **Precision defaults**: paper text claims β=ρ=ω=1; code defaults are β=1 (matches),
   ρ=`precB`=15 (does not match), ω=`precC`=3 (does not match).
2. **Fiedler boundary threshold**: paper's §A.4 describes an *adaptive* 10th-20th
   percentile-of-|y2| rule; code uses a **fixed absolute** cutoff `|y2|<0.05` on a
   max-abs-normalized vector. Different rule, not just different parameterization.
3. **"Normalized Laplacian" comment**: code comment is wrong; `L=D-A` as actually
   computed is the unnormalized (combinatorial) Laplacian.
4. **Multi-run ensembles (500/1000 sims) and the PID/synergy/energy pipelines** (Fig.
   2, Fig. 3, Eq. 1's Hamiltonian) are not present in the released code; only the
   single-simulation building blocks are. `rng('default')` at the top of the
   single-run function additionally means naively looping the released function without
   modification would not even produce varying replicates.
5. **`compHamiltonian` in the code is not the Potts Hamiltonian `H` of Eq. 1** — a
   same-named but different diagnostic quantity.
6. Fig. 1 caption's informal "edge if same heading at least once in `T_w`" is looser
   than what is actually computed (a **weighted count** of agreement-timesteps, per
   §A.4 and the code).
7. Self-loops are present in the constructed adjacency `A` (diagonal = `T_w`) but are
   numerically inert for the Laplacian `L=D-A` (algebraically verified).
8. Node classification is not a strict 4-way partition; the "internal" (core1) label is
   the default fallback for any unclassified node, not an independently-computed set.

None of these discrepancies were "fixed" in the port; §14 (in PORT_VALIDATION.md) and
`configs/` record which literal-code-vs-manuscript-text choice was made as the default,
with the alternative always available as an explicit, separately-named config.

## 14. Parameter defaults table (for `configs/protocol_v1.yaml` cross-reference)

| Symbol (paper) | Code name | Default | Source |
|---|---|---|---|
| N (birds) | `nn` | 100 | `flocking_AIF_simulation.m:33` |
| L (lattice side) | `l=sqrt(nn)` | 10 | derived |
| M (coordination #) | `nh` | 8 | `flocking_AIF_simulation.m:38` |
| q (# heading states) | `nu` | 4 | `flocking_AIF_simulation.m:44` |
| v_m | `vm`/`algnmt` | 4 | `flocking_AIF_simulation.m:55` |
| c_a | `ca`/`clsavd` | 2 | `flocking_AIF_simulation.m:60` |
| f_c | `fc`/`flckcntr` | 1 | `flocking_AIF_simulation.m:65` |
| β (not-in-danger obs.) | `precAbird` | 1 | `flocking_AIF_simulation.m:71` |
| β (in-danger obs.) | `precApred` | 1 | `flocking_AIF_simulation.m:76` |
| ρ (heading transition) | `precB` | **15** | `flocking_AIF_simulation.m:81` |
| ω (preference) | `precC` | **3** | `flocking_AIF_simulation.m:86` |
| — | `pu` (init heading dist.) | uniform 1/4 | `flocking_AIF_simulation.m:96` |
| — | `asynch` | 0 (synchronous) | `flocking_AIF_simulation.m:106` |
| T_r (refractory) | `T_refract` | 10 | `flocking_AIF_simulation.m:120` |
| τ (stress mean-life) | `tau` | 2 | `flocking_AIF_simulation.m:126` |
| — | `nt` (timesteps) | 60 | `flocking_AIF_simulation.m:24` |
| — | `T` (policy length) | 2 (hardcoded) | `flocking_AIF_simulation.m:158` |
| T_w (Fiedler window) | `TW` | 5 | `getMarkovBlanketOfFlock.m:15` |
| — | boundary threshold | fixed 0.05 (abs, max-normalized) | `getMarkovBlanketOfFlock.m:134` |
| — | core percentile | 80th / 20th | `getMarkovBlanketOfFlock.m:132-133` |
| α (SPM policy precision, generic) | `alpha` | 8 | `active_inference_bird_control.m` `initialiseMDP` |
| β (SPM policy precision, generic) | `beta` | 4 | ditto |
| — | `N` (variational iters) | 4 | ditto |

---

**Gate A status**: audit complete. No MATLAB/Octave environment is available to
execute the original code directly (see PORT_VALIDATION.md for how this is handled).
Proceeding to Phase 1 (Python port) using the above as the single source of truth,
matching the *code's* actual behavior by default in every case where code and
manuscript text disagree, with the manuscript's stated alternative always available as
an explicit, separately-named config option.

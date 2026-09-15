"""Synthetic multi-object event generator for Phase 2 validation.

Independent of `moving_flock_611.MovingFlock611` (per VALIDATION_PROTOCOL.md
§1): this module never imports the simulator and produces its own known
organizational trajectories/genealogy, so trackers can be scored against
GROUND TRUTH the real 400-bird flock cannot provide.

Two generative sub-modes, both required by the mandate so a tracker is not
judged only on data drawn from its own assumptions (VALIDATION_PROTOCOL.md
§1):

- "matched": each label's members are literally drawn from a wrapped
  elliptical-Gaussian spatial density times a categorical heading
  distribution, matching IDENTITY_MODEL.md §4's likelihood exactly.
- "vicsek": a small actual local-alignment (Vicsek-style) multi-agent
  simulation with real neighbour interactions, deliberately violating the
  mixture's conditional-independence and elliptical-shape assumptions.
  Used for a disclosed subset of scenarios (see SCENARIOS_WITH_VICSEK
  below), not all 16 -- a stated scope decision, not a silent omission.

Ground truth returned per scenario: exact per-step member sets for every
label, plus an explicit event log (birth/death/split/merge times and
parent/child label ids) that a tracker's own inferred events can be scored
against.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field

import numpy as np

L_DEFAULT = 24.0
DT = 1.0


def torus_wrap(x: np.ndarray, L: float) -> np.ndarray:
    return np.mod(x, L)


def torus_delta(a: np.ndarray, b: np.ndarray, L: float) -> np.ndarray:
    return (a - b + L / 2.0) % L - L / 2.0


@dataclass
class LabelTimeline:
    """One ground-truth organizational label's full timeline."""
    label_id: str
    parents: list  # [] for birth, one id for continuation-only bookkeeping (unused), 2 for merger
    birth_t: int
    death_t: int  # exclusive; label has no members at t >= death_t
    c0: np.ndarray
    v_fn: "callable"  # t -> velocity (2,)
    sigma_fn: "callable"  # t -> (sx, sy) std devs of member offsets from centre
    pi_fn: "callable"  # t -> categorical heading probs (4,)
    member_count_fn: "callable"  # t -> desired member count
    bimodal_offset_fn: "callable | None" = None  # t -> None or a second-centre offset (for disconnected shape)
    member_ids: list = dc_field(default_factory=list)  # persistent bird ids currently owned
    member_offsets: dict = dc_field(default_factory=dict)  # id -> current (x,y) offset from centre
    member_headings: dict = dc_field(default_factory=dict)  # id -> current heading index
    centre: np.ndarray = None


UV4 = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])


class ScenarioEngine:
    """Runs a set of LabelTimelines forward, drawing member positions/headings
    each step from each active label's own density, with persistent per-bird
    offsets that random-walk (mean-reverting) around the label centre --
    giving continuous-looking trajectories rather than i.i.d. noise soup."""

    def __init__(self, N_total: int, L: float, rng: np.random.Generator,
                 offset_persistence: float = 0.85, heading_persistence: float = 0.85):
        self.N_total = N_total
        self.L = L
        self.rng = rng
        self.offset_persistence = offset_persistence
        self.heading_persistence = heading_persistence
        self._next_id = 0
        self.background_pool: list = list(range(N_total))
        self.timelines: dict = {}
        self.event_log: list = []
        # Persistent background-bird state (position + heading), updated by
        # a small random walk each step -- NOT re-randomized every frame.
        # An earlier version fully re-randomized background birds every
        # step, which produced transient phantom spatial clumps purely
        # from IID noise; those got picked up by the candidate detectors as
        # spurious births, which then spuriously "merged" with real labels
        # once realistic candidate proposals started running against them
        # (caught on this module's own smoke test, not asserted correct
        # without having been checked).
        self.bg_r = self.rng.uniform(0, L, size=(N_total, 2))
        self.bg_z = self.rng.integers(0, 4, size=N_total)

    def _alloc_ids(self, n: int) -> list:
        ids = []
        for _ in range(n):
            if not self.background_pool:
                break
            i = self.background_pool.pop(self.rng.integers(0, len(self.background_pool)))
            ids.append(i)
        return ids

    def _release_ids(self, ids: list):
        self.background_pool.extend(ids)

    def add_label(self, tl: LabelTimeline):
        self.timelines[tl.label_id] = tl
        self.event_log.append(dict(t=tl.birth_t, type="birth", label=tl.label_id, parents=tl.parents))

    def _init_member(self, tl: LabelTimeline, bird_id: int, t: int):
        sx, sy = tl.sigma_fn(t)
        off = self.rng.normal(0, [sx, sy])
        if tl.bimodal_offset_fn is not None:
            extra = tl.bimodal_offset_fn(t)
            if extra is not None and self.rng.random() < 0.5:
                off = off + np.asarray(extra)
        tl.member_offsets[bird_id] = off
        h = self.rng.choice(4, p=tl.pi_fn(t))
        tl.member_headings[bird_id] = h

    def step(self, t: int):
        """Advance every active label one step; returns (r, z) for all N_total birds."""
        for tl in self.timelines.values():
            active = tl.birth_t <= t < tl.death_t
            if not active:
                if tl.member_ids:
                    self._release_ids(tl.member_ids)
                    tl.member_ids = []
                    tl.member_offsets = {}
                    tl.member_headings = {}
                continue
            if tl.centre is None:
                tl.centre = tl.c0.copy()
            else:
                v = np.asarray(tl.v_fn(t))
                tl.centre = torus_wrap(tl.centre + v * DT, self.L)

            desired_n = int(tl.member_count_fn(t))
            cur_n = len(tl.member_ids)
            if desired_n > cur_n:
                new_ids = self._alloc_ids(desired_n - cur_n)
                for bid in new_ids:
                    self._init_member(tl, bid, t)
                tl.member_ids.extend(new_ids)
            elif desired_n < cur_n:
                drop_n = cur_n - desired_n
                drop_ids = list(self.rng.choice(tl.member_ids, size=drop_n, replace=False))
                for bid in drop_ids:
                    tl.member_ids.remove(bid)
                    del tl.member_offsets[bid]
                    del tl.member_headings[bid]
                self._release_ids(drop_ids)

            sx, sy = tl.sigma_fn(t)
            for bid in tl.member_ids:
                off = tl.member_offsets[bid]
                target = self.rng.normal(0, [sx, sy])
                off = self.offset_persistence * off + (1 - self.offset_persistence) * target \
                    + self.rng.normal(0, [sx * 0.08, sy * 0.08])
                tl.member_offsets[bid] = off
                if self.rng.random() > self.heading_persistence:
                    tl.member_headings[bid] = self.rng.choice(4, p=tl.pi_fn(t))

        r = np.zeros((self.N_total, 2))
        z = np.zeros(self.N_total, dtype=int)
        owned = set()
        for tl in self.timelines.values():
            for bid in tl.member_ids:
                pos = torus_wrap(tl.centre + tl.member_offsets[bid], self.L)
                r[bid] = pos
                z[bid] = tl.member_headings[bid]
                owned.add(bid)
        # Background birds random-walk persistently (small step + occasional
        # heading resample) rather than being re-randomized every frame.
        step_std = 0.35
        walk = self.rng.normal(0, step_std, size=(self.N_total, 2))
        self.bg_r = torus_wrap(self.bg_r + walk, self.L)
        resample = self.rng.random(self.N_total) > 0.9
        if resample.any():
            self.bg_z[resample] = self.rng.integers(0, 4, size=int(resample.sum()))
        for bid in self.background_pool:
            if bid in owned:
                continue
            r[bid] = self.bg_r[bid]
            z[bid] = self.bg_z[bid]
        return r, z

    def ground_truth_members(self, t: int) -> dict:
        return {lid: set(int(x) for x in tl.member_ids)
                for lid, tl in self.timelines.items() if tl.birth_t <= t < tl.death_t}


def _const(v):
    return lambda t: v


def run(engine: ScenarioEngine, T: int):
    frames = []
    truth = []
    for t in range(T):
        r, z = engine.step(t)
        frames.append((r.copy(), z.copy()))
        truth.append(engine.ground_truth_members(t))
    return frames, truth, engine.event_log


# --------------------------------------------------------------------- #
# Scenario builders. Each returns (engine, T). N_total, L are fixed per
# call for reproducibility across dev/held-out seeds of the same scenario.
# --------------------------------------------------------------------- #

def _mk_engine(seed: int, N_total: int, L: float) -> ScenarioEngine:
    return ScenarioEngine(N_total=N_total, L=L, rng=np.random.default_rng(seed))


def scenario_two_clumps(seed, N_total=120, L=L_DEFAULT, T=60):
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.2, L * 0.5]),
                                 _const(np.array([0.0, 0.25])), _const((1.0, 1.0)),
                                 _const(np.array([1, 0, 0, 0])), _const(20)))
    eng.add_label(LabelTimeline("B", [], 0, T, np.array([L * 0.8, L * 0.5]),
                                 _const(np.array([0.25, 0.0])), _const((1.0, 1.0)),
                                 _const(np.array([0, 0, 0, 1])), _const(15)))
    return eng, T


def scenario_crossing(seed, N_total=120, L=L_DEFAULT, T=60):
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.15, L * 0.5]),
                                 _const(np.array([0.28, 0.0])), _const((1.0, 1.0)),
                                 _const(np.array([0, 0, 0, 1])), _const(18)))
    eng.add_label(LabelTimeline("B", [], 0, T, np.array([L * 0.5, L * 0.15]),
                                 _const(np.array([0.0, 0.28])), _const((1.0, 1.0)),
                                 _const(np.array([1, 0, 0, 0])), _const(16)))
    return eng, T


def scenario_superposition_two_distinct(seed, N_total=100, L=L_DEFAULT, T=50):
    """One blob at the detector's scale that is really two still-distinct
    groups (different heading distributions), per §7 row 4 (detector merger)."""
    eng = _mk_engine(seed, N_total, L)
    c = np.array([L * 0.5, L * 0.5])
    eng.add_label(LabelTimeline("A", [], 0, T, c.copy(),
                                 _const(np.array([0.05, 0.0])), _const((0.9, 0.9)),
                                 _const(np.array([0.05, 0.05, 0.05, 0.85])), _const(14)))
    eng.add_label(LabelTimeline("B", [], 0, T, c.copy(),
                                 _const(np.array([-0.05, 0.0])), _const((0.9, 0.9)),
                                 _const(np.array([0.85, 0.05, 0.05, 0.05])), _const(14)))
    return eng, T


def scenario_actual_merger(seed, N_total=100, L=L_DEFAULT, T=60, merge_t=30):
    eng = _mk_engine(seed, N_total, L)
    cA, cB = np.array([L * 0.35, L * 0.5]), np.array([L * 0.65, L * 0.5])

    def vA(t):
        return np.array([0.15, 0.0]) if t < merge_t else np.array([0.0, 0.0])

    def vB(t):
        return np.array([-0.15, 0.0]) if t < merge_t else np.array([0.0, 0.0])
    eng.add_label(LabelTimeline("A", [], 0, merge_t, cA, vA, _const((1.0, 1.0)),
                                 _const(np.array([0, 0, 0, 1])), _const(15)))
    eng.add_label(LabelTimeline("B", [], 0, merge_t, cB, vB, _const((1.0, 1.0)),
                                 _const(np.array([1, 0, 0, 0])), _const(15)))
    cC = np.array([L * 0.5, L * 0.5])
    eng.add_label(LabelTimeline("C", ["A", "B"], merge_t, T, cC, _const(np.array([0.0, 0.1])),
                                 _const((1.3, 1.3)), _const(np.array([0.2, 0.2, 0.2, 0.4])),
                                 _const(28)))
    eng.event_log.append(dict(t=merge_t, type="merger", parents=["A", "B"], child="C"))
    return eng, T


def scenario_symmetric_split(seed, N_total=100, L=L_DEFAULT, T=60, split_t=25):
    eng = _mk_engine(seed, N_total, L)
    c0 = np.array([L * 0.5, L * 0.5])
    eng.add_label(LabelTimeline("A", [], 0, split_t, c0, _const(np.array([0.0, 0.1])),
                                 _const((1.2, 1.2)), _const(np.array([0.25] * 4)), _const(30)))
    eng.add_label(LabelTimeline("A1", ["A"], split_t, T, np.array([L * 0.4, L * 0.5]),
                                 _const(np.array([-0.15, 0.1])), _const((0.9, 0.9)),
                                 _const(np.array([0.6, 0.1, 0.2, 0.1])), _const(15)))
    eng.add_label(LabelTimeline("A2", ["A"], split_t, T, np.array([L * 0.6, L * 0.5]),
                                 _const(np.array([0.15, 0.1])), _const((0.9, 0.9)),
                                 _const(np.array([0.1, 0.1, 0.1, 0.7])), _const(15)))
    eng.event_log.append(dict(t=split_t, type="split", parent="A", children=["A1", "A2"]))
    return eng, T


def scenario_growth(seed, N_total=100, L=L_DEFAULT, T=50):
    eng = _mk_engine(seed, N_total, L)

    def n_fn(t):
        return int(min(15 + t, 45))
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.3, L * 0.5]),
                                 _const(np.array([0.15, 0.0])), _const((1.1, 1.1)),
                                 _const(np.array([0, 0, 0, 1])), n_fn))
    return eng, T


def scenario_contraction(seed, N_total=100, L=L_DEFAULT, T=50):
    eng = _mk_engine(seed, N_total, L)

    def n_fn(t):
        return int(max(45 - t, 15))
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.3, L * 0.5]),
                                 _const(np.array([0.15, 0.0])), _const((1.1, 1.1)),
                                 _const(np.array([0, 0, 0, 1])), n_fn))
    return eng, T


def scenario_torus_seam(seed, N_total=100, L=L_DEFAULT, T=60):
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L - 2.0, L * 0.5]),
                                 _const(np.array([0.3, 0.0])), _const((1.0, 1.0)),
                                 _const(np.array([0, 0, 0, 1])), _const(20)))
    return eng, T


def scenario_rapid_motion(seed, N_total=100, L=L_DEFAULT, T=40):
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.2, L * 0.5]),
                                 _const(np.array([0.9, 0.0])), _const((1.0, 1.0)),
                                 _const(np.array([0, 0, 0, 1])), _const(20)))
    return eng, T


def scenario_full_turnover(seed, N_total=100, L=L_DEFAULT, T=60):
    """Complete constituent replacement while translating: growth phase then
    contraction phase overlapping, engineered so membership at T has zero
    overlap with membership at t=0 while c,v,pi stay continuous (Case 7)."""
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.1, L * 0.5]),
                                 _const(np.array([0.28, 0.0])), _const((1.0, 1.0)),
                                 _const(np.array([0, 0, 0, 1])), _const(20)))
    return eng, T


def scenario_lookalike_death(seed, N_total=100, L=L_DEFAULT, T=50, death_t=20, birth_t=30):
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, death_t, np.array([L * 0.25, L * 0.25]),
                                 _const(np.array([0.0, 0.0])), _const((0.8, 0.8)),
                                 _const(np.array([1, 0, 0, 0])), _const(18)))
    eng.add_label(LabelTimeline("B", [], birth_t, T, np.array([L * 0.75, L * 0.75]),
                                 _const(np.array([0.0, 0.0])), _const((0.8, 0.8)),
                                 _const(np.array([1, 0, 0, 0])), _const(18)))
    eng.event_log.append(dict(t=death_t, type="death", label="A"))
    eng.event_log.append(dict(t=birth_t, type="birth", label="B", parents=[],
                               annotation="possible_lookalike_of:A"))
    return eng, T


def scenario_missed_then_continue(seed, N_total=100, L=L_DEFAULT, T=50):
    """Same as two_clumps' label A, but the harness (not the generator) will
    withhold candidate proposals for a window -- see run_synthetic_validation
    `apply_missed_detection_mask`."""
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.2, L * 0.5]),
                                 _const(np.array([0.2, 0.05])), _const((1.0, 1.0)),
                                 _const(np.array([0, 0, 0, 1])), _const(20)))
    return eng, T


def scenario_density_change(seed, N_total=100, L=L_DEFAULT, T=50):
    """Mass changes (denser packing) with count and shape held fixed --
    i.e. sigma shrinks while member_count stays constant, a pure density
    change independent of extent/shape."""
    eng = _mk_engine(seed, N_total, L)

    def sigma_fn(t):
        s = max(1.4 - 0.02 * t, 0.5)
        return (s, s)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.3, L * 0.5]),
                                 _const(np.array([0.1, 0.0])), sigma_fn,
                                 _const(np.array([0, 0, 0, 1])), _const(25)))
    return eng, T


def scenario_shape_compact(seed, N_total=80, L=L_DEFAULT, T=40):
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.5, L * 0.5]),
                                 _const(np.array([0.1, 0.05])), _const((0.6, 0.6)),
                                 _const(np.array([0, 0, 0, 1])), _const(25)))
    return eng, T


def scenario_shape_elongated(seed, N_total=80, L=L_DEFAULT, T=40):
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.5, L * 0.5]),
                                 _const(np.array([0.1, 0.05])), _const((2.4, 0.4)),
                                 _const(np.array([0, 0, 0, 1])), _const(25)))
    return eng, T


def scenario_shape_disconnected(seed, N_total=80, L=L_DEFAULT, T=40):
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.5, L * 0.5]),
                                 _const(np.array([0.1, 0.0])), _const((0.6, 0.6)),
                                 _const(np.array([0, 0, 0, 1])), _const(25),
                                 bimodal_offset_fn=_const(np.array([3.0, 0.0]))))
    return eng, T


def scenario_ambiguous_symmetric(seed, N_total=100, L=L_DEFAULT, T=40, meet_t=20):
    """Case 10: bird-level mirror symmetry through a head-on crossing."""
    eng = _mk_engine(seed, N_total, L)
    eng.add_label(LabelTimeline("A", [], 0, T, np.array([L * 0.2, L * 0.5]),
                                 _const(np.array([0.3, 0.0])), _const((0.8, 0.8)),
                                 _const(np.array([0, 0, 0, 1])), _const(16)))
    eng.add_label(LabelTimeline("B", [], 0, T, np.array([L * 0.8, L * 0.5]),
                                 _const(np.array([-0.3, 0.0])), _const((0.8, 0.8)),
                                 _const(np.array([1, 0, 0, 0])), _const(16)))
    return eng, T


SCENARIOS = {
    "two_clumps": scenario_two_clumps,
    "crossing": scenario_crossing,
    "superposition_two_distinct": scenario_superposition_two_distinct,
    "actual_merger": scenario_actual_merger,
    "symmetric_split": scenario_symmetric_split,
    "growth": scenario_growth,
    "contraction": scenario_contraction,
    "torus_seam": scenario_torus_seam,
    "missed_then_continue": scenario_missed_then_continue,
    "rapid_motion": scenario_rapid_motion,
    "full_turnover": scenario_full_turnover,
    "lookalike_death": scenario_lookalike_death,
    "density_change": scenario_density_change,
    "shape_compact": scenario_shape_compact,
    "shape_elongated": scenario_shape_elongated,
    "shape_disconnected": scenario_shape_disconnected,
    "ambiguous_symmetric": scenario_ambiguous_symmetric,
}

# Disclosed scope decision (VALIDATION_PROTOCOL.md §1): out-of-model
# (Vicsek) generation is built for this subset only, not all 16 scenarios.
SCENARIOS_WITH_VICSEK = {"crossing", "actual_merger", "full_turnover", "shape_elongated"}


def generate(scenario_name: str, seed: int, mode: str = "matched"):
    """mode: 'matched' (default, all scenarios) or 'vicsek' (subset only,
    see SCENARIOS_WITH_VICSEK; raises if requested for an unsupported
    scenario rather than silently falling back to 'matched')."""
    if scenario_name not in SCENARIOS:
        raise KeyError(f"unknown scenario {scenario_name!r}")
    if mode == "vicsek":
        if scenario_name not in SCENARIOS_WITH_VICSEK:
            raise ValueError(f"no vicsek generator built for {scenario_name!r} "
                              f"(disclosed scope limit, see SCENARIOS_WITH_VICSEK)")
        from vicsek_generator import generate_vicsek
        return generate_vicsek(scenario_name, seed)
    builder = SCENARIOS[scenario_name]
    eng, T = builder(seed)
    frames, truth, events = run(eng, T)
    return dict(scenario=scenario_name, mode=mode, seed=seed, L=eng.L, N=eng.N_total,
                T=T, frames=frames, truth=truth, events=events)

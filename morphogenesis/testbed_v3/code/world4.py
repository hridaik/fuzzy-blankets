"""Package-v3 experiment runner: 0.5-tu actuation/observation chunks and a per-run observation schedule (1 tu outside, 0.5 tu in a dense window). Subclass of Experiment3 (no change to earlier code)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world3
from world3 import *
CH4 = 0.5
world3.CHUNK = CH4
def obs_schedule(T, dense=None, base=1.0, fine=0.5):
    """sorted observation times in (0, T]: every `base` tu, and every `fine` tu inside the dense window (t_a, t_b)"""
    ts = set(np.round(np.arange(base, T + 1e-9, base), 6).tolist())
    if dense is not None: ts |= set(np.round(np.arange(max(fine, dense[0]), min(T, dense[1]) + 1e-9, fine), 6).tolist())
    return sorted(ts)
class Experiment4(Experiment3):
    def run_sched(self, T, actions=(), sham=False, obs_times=()):
        w = self.w; acts = [dict(a, amp=(0.0 if sham else a.get('amp', 0.0))) for a in actions]
        pending = sorted([a for a in acts if a['type'] in ('tweezers', 'surgery', 'kick')], key=lambda a: a['t']); cont = [a for a in acts if a['type'] not in ('tweezers', 'surgery', 'kick')]
        obs = set(round(t, 6) for t in obs_times); tend = w.time + T
        while w.time < tend - 1e-9:
            t_rel = w.time - self.t0
            for a in [a for a in pending if a['t'] <= t_rel + 1e-9]: self._instant(a, sham); pending.remove(a)
            amps = self._amps(cont, t_rel + 0.5 * CH4); w.run(CH4, ctl_extra=amps)
            if round(w.time - self.t0, 6) in obs: self._observe()

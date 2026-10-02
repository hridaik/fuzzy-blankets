"""D2: does the sustained-DH period-2 cycle survive finer integration? Continuation from the class-0 adult state with DH on,
M(1).E.dt = 1/m (integration AND embedding spacing, time unit stays one bin), m = 1, 2, 4; N = 400 m sub-bins; clock T_dev = 32 m sub-bins.
Control: m=1 reproduces the standard sustained-DH continuation; no-DH sub-stepped runs stay at the fixed point."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
def go(m, dh):
    ind = Ind("primary", 0); A = path("census", "primary_0000_A")
    ev = [dict(type="kuch", cells=list(range(8)), sign=1, onset=B_ADULT * m + 1, off=None, w=RAMP_W * m)] if dh else None
    out = path("d2", f"sub{m}_{'DH' if dh else 'NULL'}")
    if not os.path.exists(out):
        simulate(out, 400 * m, seed=0, ramp_mode="abs", ramp_ref=T_DEV * m, engine="m2a", cont_file=A, events=ev, dt=1.0 / m)
    return out
if __name__ == "__main__":
    run_tasks([(go, (m, dh)) for m in (1, 2, 4) for dh in (True, False)], workers=6, label="D2")

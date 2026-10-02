"""Pilot for W: time to stationarity under SUSTAINED DH at the canonical clock (individual primary 0)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
def go(kind):
    ind = Ind("primary", 0)
    sg = {"DH": 1, "DT": -1}[kind]
    ev = [dict(type="kuch", cells=list(range(8)), sign=sg, onset=0, off=None, w=RAMP_W)]
    sim(path("pilot", f"sustained_{kind}_p0"), 1000, ind, events=ev, meta=dict(pilot="W"))
    return kind
if __name__ == "__main__":
    run_tasks([(go, ("DH",)), (go, ("DT",))], workers=2, label="W pilot")

"""D1: Jacobians of the one-bin map (state = beliefs v, belief velocity, action, previous action; 224-dim) at the class-0 adult fixed point,
the class-1 adult fixed point, and the two phases of the sustained-DH period-2 cycle. Two central-difference step sizes."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from m2a_sim import jacobian
STEPS = (1e-4, 1e-6)
DH_EV = [dict(type="kuch", cells=list(range(8)), sign=1, onset=0, off=None, w=RAMP_W)]

def j_fixed(name, cont):
    jacobian(path("d1", f"J_{name}")[:-4] + ".mat", cont, steps=STEPS); return name

def j_cycle():
    ind = Ind("primary", 0); A = path("r2", "primary_0000_SUST_DH")
    B = sim(path("d1", "dh_cycle_b"), 1, ind, cont=A, events=DH_EV, meta=dict(stage="D1"))
    jacobian(path("d1", "J_dhcycle_a"), A, steps=STEPS, events=DH_EV)
    jacobian(path("d1", "J_dhcycle_b"), B, steps=STEPS, events=DH_EV)
    return "cycle"

if __name__ == "__main__":
    tasks = [(j_fixed, ("class0", path("census", "primary_0000_A"))), (j_fixed, ("class1", path("census", "secondary_0005_A"))), (j_cycle, ())]
    run_tasks(tasks, workers=3, label="D1")

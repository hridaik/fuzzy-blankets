"""R1: reference census under v2. 50 primary + 10 secondary at the canonical clock (T_dev=32): segment A = 320 bins (adult
state, b_adult) + continuation B = 192 bins (total 512; extended while not stationary). 10 primary at T_dev=512 (2048 bins)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *

def canon(kind, idx):
    ind = Ind(kind, idx)
    A = sim(path("census", f"{ind.name}_A"), B_ADULT, ind, meta=dict(stage="R1"))
    B = sim(path("census", f"{ind.name}_B"), 192, ind, cont=A, meta=dict(stage="R1"))
    return ind.name

def slow(idx):
    ind = Ind("primary", idx)
    sim(path("census512", f"{ind.name}"), 2048, ind, T_dev=T_DEV_SECONDARY, meta=dict(stage="R1-T512"))
    return ind.name

if __name__ == "__main__":
    tasks = [(slow, (i,)) for i in range(10)] + [(canon, ("primary", i)) for i in range(50)] + [(canon, ("secondary", i)) for i in range(10)]
    run_tasks(tasks, workers=8, label="R1")

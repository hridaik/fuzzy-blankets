import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from d5_edge import *
def go(k):
    m = mix(pth(f"adv_a_{k}"), pth(f"adv_b_{k}"), 0.5, pth(f"edge_hop{k}")); jacobian(pth(f"J_edge_hop{k}"), m, steps=(1e-4, 1e-6)); return k
if __name__ == "__main__":
    run_tasks([(go, (k,)) for k in (11, 14)], workers=2, label="D5J")

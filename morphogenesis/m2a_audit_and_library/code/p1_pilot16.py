import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
ind = Ind("primary", 900)
sim(path("pilot", "cell16_p900_A"), 64, ind, L=4, meta=dict(pilot="16-cell timing"))
m = load(path("pilot", "cell16_p900_A")); print("s/bin", float(np.ravel(m["elapsed"])[0]) / 64, "n", m["n"])

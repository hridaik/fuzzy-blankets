import sys; sys.path.insert(0,'code')
from rig import *
d=connect(); out={}
for s in range(5000,5016):
    e=Ep(d,seed=s,tag='scan',baseline_tu=4,dt=2.0); out[s]=(e.base_state,round(e.last['u'][0],2)); e.end(save=False)
print(out)

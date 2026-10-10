import sys,time,json; sys.path.insert(0,'live')
from live_client import Dish
d=Dish('rig/ready.json'); print(json.dumps(d.status(),indent=1))
r=d.reset('development'); print(r); e=r['episode']
for lv in ['O1','O2','O3a','O3b','O3c']:
    t=time.time(); o=d.observe(e,lv); print(lv,{k:(v.shape if hasattr(v,'shape') else v) for k,v in o.items() if k!='image' or True}, round(time.time()-t,3))
t=time.time(); s=d.step(e,10); print(s,'step10 wall',time.time()-t)
o=d.observe(e,'O1'); import numpy as np; c=o['xy'].mean(0); print('centroid',c)
print(d.act(e,'L1',{'type':'disc','xy':list(c),'radius':2.0},0.0 if False else 0.1,5,1))
print(d.step(e,20)); print(d.end_episode(e))

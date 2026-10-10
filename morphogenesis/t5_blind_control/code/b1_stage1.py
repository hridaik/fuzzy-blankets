import sys,json; sys.path.insert(0,'code')
from b1_lib import *
d=connect()
for seed in (5001,5002):
    for lab in ['L1','L2','L3','L4','L5']:
        for amp in (1.0,5.0,25.0):
            r=probe(d,seed,lab,0.0,0.0,1.5,amp,10.0,tag='b1_stage1'); r['stage']=1; save(r)
            print(seed,lab,amp,r['start'],'->',r['end_state'],'flip',r['flipped'],'umaxdev',round(r['umax_dev'],2),'patdz',round(r['pat_dz_max'],1),'mst',round(r['mst_max'],2),r['events'],'dose',r['dose'],flush=True)

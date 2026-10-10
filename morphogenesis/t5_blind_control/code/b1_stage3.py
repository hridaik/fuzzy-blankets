import sys,json,itertools; sys.path.insert(0,'code')
from b1_lib import *
d=connect()
SEEDS={'L3':[5002,5003,5005],'L4':[5001,5004,5010]}
for lab in ['L3','L4']:
    for p in (-2.5,-1.25,0.0,1.25,2.5):
        for q in (-1.0,0.0,1.0):
            for s in SEEDS[lab]:
                r=probe(d,s,lab,p,q,0.8,2.0,10.0,tag='b1_stage3',post=60.0); r['stage']='3'; save(r)
                print('3',lab,s,(p,q),r['cells'],r['flipped'],round(r['umax_dev'],3),flush=True)

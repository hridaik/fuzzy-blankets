import sys,json,itertools; sys.path.insert(0,'code')
from b1_lib import *
d=connect()
SEEDS={'L3':[5002,5003,5005],'L4':[5001,5004,5010]}   # L3 acts on S-, L4 on S+ (stage 1)
prods=[5,10,20,40,80,160]
for lab in ['L3','L4']:
    # (a) duration x dose-product at centre
    for dur in (2.0,5.0,10.0,30.0):
        for prod in prods:
            for s in SEEDS[lab]:
                r=probe(d,s,lab,0.0,0.0,1.5,prod/dur,dur,tag='b1_stage2a'); r['stage']='2a'; save(r)
                print('2a',lab,s,dur,prod,r['start'],'->',r['end_state'],r['flipped'],round(r['umax_dev'],2),round(r['pat_dz_max'],1),r['events'],flush=True)
    # (b) location x dose at dur 10
    for (p,q) in [(1.5,0),(-1.5,0),(0,1.5),(0,-1.5),(3,0),(-3,0)]:
        for prod in (10,20,40,80):
            for s in SEEDS[lab]:
                r=probe(d,s,lab,p,q,1.5,prod/10.0,10.0,tag='b1_stage2b'); r['stage']='2b'; save(r)
                print('2b',lab,s,(p,q),prod,r['start'],'->',r['end_state'],r['flipped'],round(r['umax_dev'],2),r['cells'],r['events'],flush=True)

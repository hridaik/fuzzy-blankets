import sys,json,os,numpy as np; sys.path.insert(0,'code')
from b1_lib import *
OUT='logs/b2_results.jsonl'
d=connect()
SEEDS={'L3':[5002,5005],'L4':[5001,5004]}
LOCS={'C':(0.0,0.0,1.5),'side':(0.0,1.5,1.5),'head':(3.0,0.0,1.5),'tail':(-3.0,0.0,1.5),'whole':None}
CONFIGS=[(loc,dur) for loc in('C','side','head','tail') for dur in(5.0,10.0,20.0,40.0)]+[('whole',10.0),('whole',40.0)]
done=set()
if os.path.exists(OUT):
    for l in open(OUT): r=json.loads(l); done.add((r['label'],r['seed'],r['loc'],r['dur']))
for lab in ('L3','L4'):
  for seed in SEEDS[lab]:
    for loc,dur in CONFIGS:
        if (lab,seed,loc,dur) in done: continue
        lo,hi=np.log(0.2),np.log(60.0 if dur<=5 else 40.0)   # lo assumed non-flipping, hi assumed flipping
        trials=[]
        for it in range(5):
            amp=float(np.exp((lo+hi)/2))
            if loc=='whole': r=probe(d,seed,lab,0,0,0,amp,dur,whole=True,tag='b2')
            else: p,q,rad=LOCS[loc]; r=probe(d,seed,lab,p,q,rad,amp,dur,tag='b2')
            dmg=bool(r['events']) or not r['V_body']
            trials.append(dict(amp=amp,flipped=r['flipped'],dose=r['dose'],cells=r['cells'],damage=dmg,umax=r['umax_dev'],episode=r['episode'],pat_dz=r['pat_dz_max']))
            if r['flipped'] and not dmg: hi=np.log(amp)
            else: lo=np.log(amp) if not dmg else lo; hi=np.log(amp) if dmg else hi
            if dmg: hi=np.log(amp)
        good=[t for t in trials if t['flipped'] and not t['damage']]
        best=min(good,key=lambda t:t['dose']) if good else None
        res=dict(label=lab,seed=seed,loc=loc,dur=dur,trials=trials,amp_star=best['amp'] if best else None,dose_star=best['dose'] if best else None,prod_star=best['amp']*dur if best else None,cells=best['cells'] if best else None,
                 n_damage=sum(t['damage'] for t in trials))
        with open(OUT,'a') as f: f.write(json.dumps(res)+'\n')
        print(lab,seed,loc,dur,'amp*',res['amp_star'],'dose*',res['dose_star'],'cells',res['cells'],'dmg',res['n_damage'],flush=True)

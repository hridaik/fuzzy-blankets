import json,numpy as np
R=[json.loads(l) for l in open('logs/b2_results.jsonl')]
rows=[]
for cf in R:
    for t in cf['trials']:
        if t['damage']: continue
        L=json.load(open(f"episodes/ep_{t['episode']:05d}.json")); F=L['frames']; a=L['actions'][0]
        tt=np.array([f['t'] for f in F]); u=np.array([f['u'][0] for f in F]); s0=np.sign(u[0]); dv=-(u-u[0])*s0
        tr=a['t']+a['dur']
        def at(x): return dv[np.argmin(abs(tt-x))]
        rows.append(dict(flip=t['flipped'],dur=a['dur'],loc=cf['loc'],d_rel=at(tr),d_p4=at(tr+4),d_p8=at(tr+8),d_m5=at(tr-5),d_p15=at(tr+15)))
print(len(rows),'trials; flipped',sum(r['flip'] for r in rows))
for key in ('d_rel','d_p4','d_p8','d_p15'):
    f=np.array([r[key] for r in rows if r['flip']]); n=np.array([r[key] for r in rows if not r['flip']])
    print(key,'flipped: min %.2f q10 %.2f | non-flipped: max %.2f q90 %.2f'%(f.min(),np.quantile(f,.1),n.max(),np.quantile(n,.9)))
# best single-threshold classifier on d_p8 and (d_p4, rising)
for key in ('d_rel','d_p4','d_p8'):
    best=max(((np.mean([(r[key]>th)==r['flip'] for r in rows]),th) for th in np.linspace(0.2,1.2,41)))
    print(key,'best threshold accuracy %.3f at %.2f'%best)
# with rise: d_p8 - d_rel
rise=lambda r:r['d_p8']-r['d_rel']
for th in(0.0,0.02,0.05):
    sel=[r for r in rows if rise(r)>th and r['d_p8']>0.5]; print('rising>%.2f & d_p8>0.5: n=%d flip frac=%.2f'%(th,len(sel),np.mean([r['flip'] for r in sel]) if sel else float('nan')))
sel=[r for r in rows if r['d_p8']>0.5]; print('d_p8>0.5 any: n',len(sel),'flip frac',np.mean([r['flip'] for r in sel]))
print('false commits among d_p8>0.7:',[ (round(r['d_rel'],2),round(r['d_p8'],2),r['flip']) for r in rows if r['d_p8']>0.6 and not r['flip']][:10])

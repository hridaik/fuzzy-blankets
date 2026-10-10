import json,numpy as np
from scipy.stats import spearmanr
R=[json.loads(l) for l in open('logs/b2_results.jsonl')]
rows=[]
for cf in R:
    if cf['prod_star'] is None: continue
    for t in cf['trials']:
        if t['flipped'] or t['damage']: continue
        ep=t['episode']; L=json.load(open(f'episodes/ep_{ep:05d}.json')); F=L['frames']; a=L['actions'][0]
        tt=np.array([f['t'] for f in F]); u=np.array([f['u'][0] for f in F]); s0=np.sign(u[0]); dv=-(u-u[0])*s0
        pk=dv.max(); tk=tt[np.argmax(dv)]; t_rel=a['t']+a['dur']
        if pk<0.15: continue
        # slowing features measured only from data up to t_rel+20 (causal for a controller that waits 20 tu)
        m=(tt>=t_rel)&(tt<=t_rel+20)
        sl=np.polyfit(tt[m],dv[m],1)[0]       # slope after release (positive = still rising, negative = recovering)
        # recovery fraction in 10 tu after release relative to value at release
        v0=dv[tt<=t_rel][-1]; v10=dv[np.argmin(abs(tt-(t_rel+10)))]
        rows.append(dict(dish=(cf['label'],cf['seed']),loc=cf['loc'],dur=cf['dur'],pk=pk,gap=np.log(cf['prod_star']/(t['amp']*a['dur'])),slope=sl,keep10=v10/max(v0,0.05),lag=tk-t_rel))
print('n sub-threshold probes',len(rows))
y=np.array([r['gap'] for r in rows]); pk=np.array([r['pk'] for r in rows]); sl=np.array([r['slope'] for r in rows]); k10=np.array([r['keep10'] for r in rows]); lag=np.array([r['lag'] for r in rows])
print('spearman(log gap-to-threshold , peak dev)',spearmanr(y,pk)[0],' , slope after release',spearmanr(y,sl)[0],' , keep10',spearmanr(y,k10)[0])
# dish-clustered leave-one-dish-out regression
dishes=sorted(set(r['dish'] for r in rows))
def cv(cols):
    X=np.c_[np.ones(len(rows)),*cols]; err=[]
    for dd in dishes:
        te=np.array([r['dish']==dd for r in rows]); b=np.linalg.lstsq(X[~te],y[~te],rcond=None)[0]; err.append(((y[te]-X[te]@b)**2).sum())
    return 1-sum(err)/((y-y.mean())**2).sum()
print('LODO R2 gap ~ peak dev            ',round(cv([np.log(pk)]),3))
print('LODO R2 gap ~ peak dev + slowing(keep10)',round(cv([np.log(pk),k10]),3))
print('LODO R2 gap ~ peak + slope        ',round(cv([np.log(pk),sl]),3))
print('LODO R2 gap ~ peak + keep10 + slope+ lag',round(cv([np.log(pk),k10,sl,lag]),3))

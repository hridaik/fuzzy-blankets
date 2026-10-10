import json,glob,numpy as np,collections
R={json.loads(l)['episode']:json.loads(l) for l in open('logs/b1_results.jsonl')}
rows=[]
for ep,r in R.items():
    if r.get('stage') not in('2a','2b'): continue
    L=json.load(open(f'episodes/ep_{ep:05d}.json')); F=L['frames']; t=np.array([f['t'] for f in F]); u=np.array([f['u'][0] for f in F])
    s0=np.sign(u[0]); dev=(u-u[0])*(-s0)*(-1)   # dev toward target = -(u-u0)*sign(u0)... target opposite sign
    dev=-(u-u[0])*s0           # positive when moving toward opposite state
    t_end=r['t_act']+r['dur']
    k=np.argmax(dev); pk=dev[k]; tk=t[k]
    if r['flipped'] or pk<0.15: continue
    # recovery: time from peak until dev falls to half of peak
    after=np.where((t>tk)&(dev<=pk/2))[0]
    th=(t[after[0]]-tk) if len(after) else np.nan
    # rate of recovery just after release: slope of log dev from t_end+5 to t_end+25
    m=(t>=t_end+3)&(t<=t_end+25)&(dev>0.02)
    tau=np.nan
    if m.sum()>5: sl=np.polyfit(t[m],np.log(dev[m]),1)[0]; tau=-1/sl if sl<0 else np.inf
    rows.append((pk,th,tau,tk-t_end,r['dur'],r['label']))
a=np.array([(x[0],x[1],x[2],x[3]) for x in rows],float)
print('n subthreshold with peak>=0.15:',len(a))
for lo,hi in [(0.15,0.3),(0.3,0.45),(0.45,0.6),(0.6,0.75),(0.75,1.0)]:
    m=(a[:,0]>=lo)&(a[:,0]<hi)
    if m.sum(): print(f'peak dev [{lo},{hi}) n={m.sum()} half-recovery tu median={np.nanmedian(a[m,1]):.1f} tau median={np.nanmedian(a[m,2]):.1f} peak-lag after release median={np.nanmedian(a[m,3]):.1f}')
ok=~np.isnan(a[:,2])&np.isfinite(a[:,2]); from scipy.stats import spearmanr
print('spearman(peak,tau)',spearmanr(a[ok,0],a[ok,2])); ok=~np.isnan(a[:,1]); print('spearman(peak,t_half)',spearmanr(a[ok,0],a[ok,1]))
# flipped: dev threshold crossing timing
fl=[(r['umax_dev']) for r in R.values() if r.get('stage') in('2a','2b') and r['flipped']]
print('flipped umax_dev min/median',min(fl),np.median(fl))

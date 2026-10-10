import sys; sys.path.insert(0,'.')
import numpy as np
from t4 import io
from t4.celltrack import CellTracker
rows=[r for r in io.catalog() if r['condition']=='N0' and r['split']=='development'][:60]
acc=[];regs={}
for r in rows:
    o1=io.point_frames(r['run'],'O1'); o2=io.point_frames(r['run'],'O2')
    ct=CellTracker(io.CHANNELS['O2'])
    # O2 rows are shuffled vs O1; map each O2 point to O1 id by nearest xy (validation ONLY; same noise-free? use nearest)
    from scipy.spatial.distance import cdist
    tr=[];
    for a,b in zip(o1,o2):
        ids,info=ct.step(b['xy'],b['lev']); regs[info['reg']]=regs.get(info['reg'],0)+1
        D=cdist(b['xy'],a['xy']); gt=a['ids'][D.argmin(1)]
        tr.append((ids,gt))
    # pairwise consistency: fraction of consecutive-frame correspondences equal to gt
    c=0;n=0
    for (i0,g0),(i1,g1) in zip(tr[:-1],tr[1:]):
        m0={g:i for i,g in zip(i0,g0)}; 
        for i,g in zip(i1,g1):
            n+=1; c+= (m0.get(g,-9)==i)
    acc.append(c/n)
print('O2 tracker correct-link fraction: mean',np.mean(acc),'min',np.min(acc),'q10',np.quantile(acc,.1)); print(regs)

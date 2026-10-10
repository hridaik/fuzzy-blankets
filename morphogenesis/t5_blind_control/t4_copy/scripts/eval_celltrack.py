import sys; sys.path.insert(0,'.')
import numpy as np
from scipy.spatial.distance import cdist
from t4 import io
from t4.celltrack import CellTracker
def eval_run(run, **kw):
    o1=io.point_frames(run,'O1'); o2=io.point_frames(run,'O2'); ct=CellTracker(io.CHANNELS['O2'],**kw)
    tr=[]; bad=[]
    for a,b in zip(o1,o2):
        ids,info=ct.step(b['xy'],b['lev']); D=cdist(b['xy'],a['xy']); gt=a['ids'][D.argmin(1)]; tr.append((ids,gt,info))
    c=n=0
    for k,((i0,g0,_),(i1,g1,inf)) in enumerate(zip(tr[:-1],tr[1:])):
        m0={g:i for i,g in zip(i0,g0)}; ck=sum(m0.get(g,-9)==i for i,g in zip(i1,g1)); c+=ck; n+=len(i1)
        if ck<len(i1): bad.append((k+1,len(i1)-ck,inf['reg']))
    return c/n, bad[:8]
if __name__=='__main__':
    for run in sys.argv[1:]: print(run, eval_run(run))

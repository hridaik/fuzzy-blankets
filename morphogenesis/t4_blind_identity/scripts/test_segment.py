import sys,time; sys.path.insert(0,'.')
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from t4 import io, segment
cat=io.catalog()
nat=[r for r in cat if r['condition']=='N0' and r['split']=='development' and r['body_id']%2==0][:6]
s_eff=float(sys.argv[1]); kappa=float(sys.argv[2])
errs=[];cnt=[];t0=time.time()
for r in nat:
    t,im=io.image_frames(r['run'],'O3a'); F=io.point_frames(r['run'],'O1')
    for k in (0,4):
        xy,a,sg=segment.segment_frame(im[k,0],r['fov'],s_eff,kappa)
        D=cdist(xy,F[k]['xy']); rr,cc=linear_sum_assignment(D)
        m=D[rr,cc]; cnt.append(len(xy)-24); errs.append(np.median(m))
print('s',s_eff,'kappa',kappa,'count err (est-true) mean',np.mean(cnt),'sd',np.std(cnt),'median match dist',np.mean(errs),'time/frame',(time.time()-t0)/12)

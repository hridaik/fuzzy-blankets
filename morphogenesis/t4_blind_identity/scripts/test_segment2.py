import sys,time; sys.path.insert(0,'.')
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from t4 import io, segment
cat=io.catalog()
nat=[r for r in cat if r['condition']=='N0' and r['split']=='development' and r['body_id']%2==0][:20]
# mass per cell calibration
ms=[]
for r in nat:
    t,im=io.image_frames(r['run'],'O3a'); F=io.point_frames(r['run'],'O1')
    X,Y=segment.grid(r['fov']); px=2*r['fov']/64; far=np.hypot(X,Y)>0.75*r['fov']
    for k in range(8):
        I=np.clip(im[k,0]-im[k,0][far].mean(),0,None); ms.append(I.sum()*px*px/24)
mpc=np.mean(ms); print('mass per cell',mpc,'sd',np.std(ms))
s=float(sys.argv[1]); it=int(sys.argv[2]); errs=[];cnt=[];t0=time.time()
for r in nat:
    t,im=io.image_frames(r['run'],'O3a'); F=io.point_frames(r['run'],'O1')
    for k in (0,3,6):
        xy,info=segment.segment_frame2(im[k,0],r['fov'],s,it,mpc)
        D=cdist(xy,F[k]['xy']); rr,cc=linear_sum_assignment(D); m=D[rr,cc]
        cnt.append(info['n']-24); errs.append(np.mean(m))
print('s',s,'it',it,'count err mean',np.mean(cnt),'sd',np.std(cnt),'mean match dist',np.mean(errs),'q90',np.quantile(errs,.9),'t/frame',(time.time()-t0)/60)

import sys, json
sys.dont_write_bytecode = True
M='/home/hkhurana/work/code/fuzzy-blankets/morphogenesis'
sys.path.insert(0, M+'/t4_blind_identity')
import numpy as np
from t4 import io, segment
from scipy.ndimage import gaussian_filter, maximum_filter
from scipy.spatial.distance import cdist
io.DATA = M+'/testbed_blind_v3'
run='run_00283'
o1=io.point_frames(run,'O1'); tm={f['t']:f for f in o1}
d=io.load(run,'O3c'); t=d['t']; print(t[:3], d['scale'], len(t))
for k in [int(np.where(t==T)[0][0]) for T in (40.,60.,100.,150.)]:
    im=d['image'][k,0].astype(float)/d['scale'][0]; g=gaussian_filter(im,1.0); pk=(g==maximum_filter(g,size=5))&(g>0.35)
    iy,ix=np.nonzero(pk); fov=10.0; h=2*fov/128
    xy=np.c_[-fov+(ix+0.5)*h,-fov+(iy+0.5)*h]
    f=tm[float(t[k])]; 
    for name,q in (('xy',xy),('flipY',xy*[1,-1])):
        D=cdist(q,f['xy']); print(t[k],name,len(q),'median nn',np.median(D.min(0)).round(2))
    print(' O1 range',f['xy'].min(0).round(1),f['xy'].max(0).round(1))
X,Y=segment.grid(12.0); print(X[0,:3],Y[:3,0])

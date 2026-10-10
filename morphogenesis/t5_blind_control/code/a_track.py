import sys,json,numpy as np; sys.path.insert(0,'code')
from scipy.spatial.distance import cdist
from scipy.ndimage import maximum_filter, gaussian_filter
from t5mon import io
from t5mon.celltrack import CellTracker
CH2=['c0','c1','c2','c3','c6']
def pf(run,level):
    d=io.load(run,level); fp=d['frame_ptr']; out=[]
    for i in range(len(fp)-1):
        s=slice(fp[i],fp[i+1]); out.append(dict(t=float(d['t'][i]),xy=d['xy'][s].astype(float),lev=d['level'][s].astype(float),ids=d['cell_id'][s].astype(int) if 'cell_id' in d.files else None))
    return out
def o2_eval(run,maxf=800):
    o1=pf(run,'O1')[:maxf]; o2=pf(run,'O2')[:maxf]; ct=CellTracker(CH2); tr=[]
    for a,b in zip(o1,o2):
        ids,_=ct.step(b['xy'],b['lev']); D=cdist(b['xy'],a['xy']); tr.append((ids,a['ids'][D.argmin(1)]))
    c=n=0; bad_frames=0
    for (i0,g0),(i1,g1) in zip(tr[:-1],tr[1:]):
        m0={g:i for i,g in zip(i0,g0)}; cc=sum(m0.get(g,-9)==i for i,g in zip(i1,g1)); c+=cc; n+=len(i1); bad_frames+= cc<len(i1)
    return c/n,bad_frames,len(tr)-1
def o3c_eval(run,nf=40):
    d=io.load(run,'O3c'); im=d['image'][:nf,0].astype(float)/d['scale'][0]; t=d['t'][:nf]
    o1=pf(run,'O1'); tmap={f['t']:f for f in o1}; res=[]
    fov=10.0; px=im.shape[-1]; h=2*fov/px
    for k in range(len(im)):
        g=gaussian_filter(im[k],1.0); pk=(g==maximum_filter(g,size=5))&(g>0.35)
        iy,ix=np.nonzero(pk); xy=np.c_[-fov+(ix+0.5)*h,-fov+(iy+0.5)*h]
        f=tmap[float(t[k])]; D=cdist(xy,f['xy'])
        err=D.min(1) if len(xy) else np.array([]); 
        # orientation check (swap axes) : pick best of xy / yx assignments for convention
        res.append((len(xy),np.median(D.min(0)) if len(xy) else np.nan,D.min(0).max() if len(xy) else np.nan))
    return np.array(res)
nat=[r['run'] for r in io.natural('development')]
cal=[r['run'] for r in io.natural('development') if int(r['body_id'])<=2105][:4]
for r in cal: print('O2 natural',r,o2_eval(r))
lt=[r for r in io.catalog() if r['condition'][:2] in('T3','T4') and r['split']=='development' and r['arm']=='treated'][:6]
for r in lt: print('O2 light',r['run'],o2_eval(r['run'],maxf=400))
for r in cal[:3]:
    a=o3c_eval(r); print('O3c natural',r,'count mean',a[:,0].mean(),'median NN err(O1 cell->nearest detection)',np.nanmedian(a[:,1]),'worst',np.nanmax(a[:,2]))

import csv, os, numpy as np
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA=os.path.join(ROOT,'data_v3')
CH7=['c0','c1','c2','c3','c4','c5','c6']
def catalog():
    return list(csv.DictReader(open(os.path.join(DATA,'catalog.csv'))))
def natural(split='development'):
    return [r for r in catalog() if r['condition']=='N0' and r['split']==split]
def load(run,level): return np.load(os.path.join(DATA,'runs',f'{run}_{level}.npz'))
def o1_frames(run, stride=1):
    d=load(run,'O1'); fp=d['frame_ptr']; out=[]
    for i in range(0,len(fp)-1,stride):
        s=slice(fp[i],fp[i+1]); out.append(dict(t=float(d['t'][i]),xy=d['xy'][s].astype(float),lev=d['level'][s].astype(float),ids=d['cell_id'][s].astype(int)))
    return out

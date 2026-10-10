import sys, json, csv
sys.dont_write_bytecode = True
M='/home/hkhurana/work/code/fuzzy-blankets/morphogenesis'
sys.path.insert(0, M+'/t4_blind_identity')
import numpy as np
from t4 import io, o3
from t4.orgtrack import OrganismTracker
from t4.pipeline import load_geometry
io.DATA = M+'/testbed_blind_v3'; geo=load_geometry()
rows=[r for r in csv.DictReader(open(io.DATA+'/catalog.csv')) if r['condition'] in ('P01','P02') and r['arm']=='treated']
H=lambda run: json.load(open(M+f'/testbed_v3/data/blind_v3_hidden/{run}.json'))
for r in rows:
    run=r['run']; fov=float(r['fov']); ts,imgs=io.image_frames(run,'O3a'); px=2*fov/64; m_px=max(3,int(round(geo['m_min']/px**2)))
    ot=OrganismTracker(io.CHANNELS['O3a'],1.0,m_px,geo['margin'],None); cnt=[]
    for k,t in enumerate(ts):
        if t<30 or t>150: continue
        fp=o3.frame_points(imgs[k],fov,geo); orgs,ev=ot.step(float(t),fp['xy'],fp['lev'],fp['ids'],lab=fp['lab'],compute_frame=False); cnt.append((t,len(orgs)))
    post=[n for t,n in cnt if t>=60]; first=next((t for t,n in cnt if t>=50 and n>=2),None)
    h=H(run); ev=h['events'][0]
    print(run,r['condition'],'vec',np.round(ev['vec'],1),'ncut',len(ev['cells']),'first2',first,'frac2',np.mean([n==2 for n in post]).round(2),set(post))

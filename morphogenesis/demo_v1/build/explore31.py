import sys, os
sys.dont_write_bytecode = True
M='/home/hkhurana/work/code/fuzzy-blankets/morphogenesis'
sys.path.insert(0, M+'/t4_blind_identity')
import numpy as np, json
from t4 import io, o3
from t4.orgtrack import OrganismTracker
from t4.pipeline import load_geometry
io.DATA = M+'/testbed_blind_v3'
geo = load_geometry()
run='run_00263'; fov=12.0
ts, imgs = io.image_frames(run,'O3a')
print(ts[:5], ts[-5:], len(ts), geo['fg_sigma_mult'])
ch=io.CHANNELS['O3a']; px=2*fov/64
m_px = max(3,int(round(geo['m_min']/px**2))); print('m_px',m_px)
ot=OrganismTracker(ch,1.0,m_px,geo['margin'],None)
for k,t in enumerate(ts):
    if t<30 or t>150: continue
    fp=o3.frame_points(imgs[k],fov,geo)
    orgs,ev=ot.step(float(t),fp['xy'],fp['lev'],fp['ids'],lab=fp['lab'],compute_frame=False)
    if int(t)%10==0 or 48<=t<=62: print(t,[ (o['org'],len(o['idx'])) for o in orgs],[e['type'] for e in ev])

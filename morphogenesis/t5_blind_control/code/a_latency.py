import sys,json,numpy as np; sys.path.insert(0,'code')
from t5mon import io
from t5mon.monitor import OnlineMonitor
cfg=json.load(open('MONITOR_CONFIG_draft.json'))
mp=np.array(cfg['state']['mean_plus']);mm=np.array(cfg['state']['mean_minus']);Si=np.linalg.inv(np.array(cfg['state']['cov']));thr=cfg['state']['trans_maha2']
lat=[];names=[]
for r in io.catalog():
    if r['condition'][:2] not in('T3','T4') or r['split']!='development' or r['arm']!='treated': continue
    m=OnlineMonitor(cfg); fr=io.o1_frames(r['run']); rows=[]
    for f in fr:
        o=m.update(f['t'],f['xy'],f['lev'],f['ids'])
        # raw (unsmoothed) pure-state test with same maha rule
        from t5mon import geom,describe
        rows.append((f['t'],o))
    # raw pure entry time: first frame after onset where raw u is within trans of opposite state and stays pure (raw) 
    t=np.array([a for a,_ in rows]); U=np.array([o['u'] for _,o in rows])
    labs=[o['state'] for _,o in rows]
    opp='S-' if labs[0]=='S+' else 'S+'
    mo=mm if opp=='S-' else mp
    # raw entry: use median-of-1 -> approximate by smoothed u shifted: compute raw u directly
    xs=[]
    prev=None
    for f in fr:
        bf=geom.body_frame(f['xy'],f['lev'],io.CH7,prev); prev=bf['e1']; d=describe.describe(f['xy'],f['lev'],io.CH7,bf,1.42); xs.append([d['c4_mean']-d['c5_mean'],d['c0_dq_sens']])
    xs=np.array(xs); d2=np.einsum('ij,jk,ik->i',xs-mo,Si,xs-mo); pure=d2<thr
    tr=next((i for i in range(len(t)) if t[i]>40 and all(pure[i:i+10])),None)
    td=next((i for i in range(len(t)) if t[i]>40 and labs[i]==opp and rows[i][1]['state_sure']),None)
    if tr is not None and td is not None: lat.append(t[td]-t[tr]); 
print('n changed runs',len(lat),'monitor latency vs raw pure entry (tu): median',np.median(lat),'max',np.max(lat),'values',sorted(lat))

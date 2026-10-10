import sys,json,csv,numpy as np; sys.path.insert(0,'code')
from t5mon import io,geom,describe
T=json.load(open('data_v3/treatments.json'))
rows=[r for r in io.catalog() if r['condition'][:2] in('T3','T4') and r['split']=='development']
names=describe.feature_names(io.CH7)
def ts(run):
    fr=io.o1_frames(run); prev=None; out=[]
    for f in fr:
        bf=geom.body_frame(f['xy'],f['lev'],io.CH7,prev); prev=bf['e1']
        d=describe.describe(f['xy'],f['lev'],io.CH7,bf,1.42); out.append((f['t'],d['c4_mean'],d['c0_dq_sens'],d['n'],d['mst_max'],d['s1'],d['s2'],len(set(f['ids']))))
    return np.array(out)
for r in sorted(rows,key=lambda r:(r['condition'],r['arm'])):
    a=ts(r['run']); t=a[:,0]; tr=T[r['run']][0]
    def at(x): i=np.argmin(abs(t-x)); return a[i]
    s0=at(35); s1=at(tr['t_off']+30 if 't_off' in tr else 100); s2=at(t[-1])
    print(r['condition'],r['arm'][:5],r['run'],'amp',tr.get('amplitude'),'dur',round(tr['t_off']-tr['t_on'],1),'c4:',round(s0[1],2),round(s1[1],2),round(s2[1],2),'dq:',round(s0[2],2),round(s2[2],2),'n',s0[3],s2[3],'mst',round(a[:,4].max(),2),'idsmax',a[:,7].max(),'end t',t[-1])

import sys,time,numpy as np; sys.path.insert(0,'code')
from t5mon import io, geom, describe
from multiprocessing import Pool
RCOH=1.42
def run_feats(run):
    fr=io.o1_frames(run,stride=2); prev=None; F=[]
    names=describe.feature_names(io.CH7)
    for f in fr:
        bf=geom.body_frame(f['xy'],f['lev'],io.CH7,prev); prev=bf['e1']
        d=describe.describe(f['xy'],f['lev'],io.CH7,bf,RCOH)
        F.append([d[n] for n in names]+[bf['sign_conf'],bf['axis_conf']])
    return run,np.array(F),[f['t'] for f in fr]
if __name__=='__main__':
    runs=[r['run'] for r in io.natural('development')]+[r['run'] for r in io.natural('heldout_bodies')]
    t=time.time()
    with Pool(8) as p: res=p.map(run_feats,runs[:])
    np.savez('logs/nat_feats.npz',**{r:F for r,F,_ in res},names=np.array(describe.feature_names(io.CH7)+['sign_conf','axis_conf']))
    print(time.time()-t, res[0][1].shape)

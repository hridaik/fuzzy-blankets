"""PART C: held-out evaluation, run ONCE after freeze(). Per dish: controller, CRN twin, matched sham, random-location (dose matched),
fixed (dev-learned single pulse), whole-body (same actuator & amplitude), whole-body dose-matched."""
import sys,json,os,hashlib,glob,time,numpy as np; sys.path.insert(0,'code')
from controller import *
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG=json.load(open(os.path.join(ROOT,'CONTROLLER_CONFIG.json')))
QUOTA=CFG['eval']['per_direction']; MAXDISHES=CFG['eval']['max_dishes']
if os.environ.get('T5_POOL','heldout')!='heldout': QUOTA=1; MAXDISHES=2
POOL=os.environ.get('T5_POOL','heldout'); DRY=POOL!='heldout'
OUT=os.path.join(ROOT,'logs','heldout_summary.jsonl' if not DRY else 'dry_summary.jsonl'); LOGDIR='episodes_heldout' if not DRY else 'episodes_dry'
def code_hash():
    h=hashlib.sha256()
    for f in sorted(glob.glob('code/t5mon/*.py'))+['code/rig.py','code/controller.py','code/run_heldout.py','MONITOR_CONFIG.json','CONTROLLER_CONFIG.json']: h.update(open(os.path.join(ROOT,f),'rb').read())
    return h.hexdigest()
def main():
    d=connect(); H=code_hash()
    if not DRY:
        assert H==open(os.path.join(ROOT,'FROZEN_HASH.txt')).read().split()[0], 'code changed since freeze'
        if not d.status().get('frozen'): print('freeze:',d.freeze(H))
    C=Controller(CFG); cnt={'S+':0,'S-':0}; n=0
    done=set()
    if os.path.exists(OUT):
        for l in open(OUT): done.add(json.loads(l)['seed']); 
        for l in open(OUT):
            r=json.loads(l)
            if r.get('arm')=='ctrl' and r['reason']!='quota_skip': cnt[r['start']]+=1
    def full(st): return cnt.get(st,0)>=QUOTA
    while n<MAXDISHES and not all(cnt[k]>=QUOTA for k in cnt):
        S=C.run(d,None,pool=POOL,tag='H_ctrl',logdir=LOGDIR,skip_if=full); seed=S['seed']; S['arm']='ctrl'
        rec=[S]
        if S['reason'] in('quota_skip','baseline_not_clean'): 
            with open(OUT,'a') as f: f.write(json.dumps(S,default=str)+'\n')
            n+=1; continue
        cnt[S['start']]+=1; n+=1
        acts=json.load(open(os.path.join(ROOT,LOGDIR,f"ep_{S['episode']:05d}.json")))['actions']
        T0=S['t_end']; st=S['start']; lab=S['label']; hold=CFG['hold']
        plan=[dict(t=a['t'],label=a['label'],p=a['body_frame'][0],q=a['body_frame'][1],radius=a['radius'],amp=a['amp'],dur=a['dur'],ramp=a['ramp'],dose_target=a['dose'],mode='body') for a in acts]
        rng=np.random.default_rng(int(seed))
        arms={}
        arms['twin']=lambda: replay(d,seed,CFG,[],T0,st,pool=POOL,tag='H_twin',logdir=LOGDIR)
        arms['sham']=lambda: replay(d,seed,CFG,plan,T0,st,pool=POOL,sham_of=S['episode'],tag='H_sham',logdir=LOGDIR)
        arms['random']=lambda: replay(d,seed,CFG,[dict(p,mode='random_dose') for p in plan],T0,st,pool=POOL,tag='H_random',logdir=LOGDIR,rng=rng)
        fx=CFG['fixed']; fplan=[dict(t=CFG['baseline_tu'],mode='body',label=lab,p=fx['p'],q=fx['q'],radius=fx['radius'],amp=fx['amp'],dur=fx['dur'],ramp=fx['ramp'])]
        arms['fixed']=lambda: replay(d,seed,CFG,fplan,max(T0,CFG['baseline_tu']+fx['dur']+hold),st,pool=POOL,tag='H_fixed',logdir=LOGDIR)
        arms['whole']=lambda: replay(d,seed,CFG,[dict(p,mode='whole') for p in plan],T0,st,pool=POOL,tag='H_whole',logdir=LOGDIR)
        arms['whole_dm']=lambda: replay(d,seed,CFG,[dict(p,mode='whole',amp=p['dose_target']/(p['dur']*24)) for p in plan],T0,st,pool=POOL,tag='H_whole_dm',logdir=LOGDIR)
        for k,fn in arms.items():
            R=fn(); R['arm']=k; R.pop('actions',None); rec.append(R)
        with open(OUT,'a') as f:
            for r in rec: f.write(json.dumps(r,default=lambda o:o.item() if hasattr(o,'item') else str(o))+'\n')
        print(n,seed,st,'ctrl success',S['success'],S['reason'],'dose',round(S['dose']),{r['arm']:(r['success'],round(r['dose'])) for r in rec[1:]},flush=True)
    print('done',cnt,flush=True)
if __name__=='__main__': main()

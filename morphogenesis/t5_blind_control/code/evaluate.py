"""Held-out evaluation (post-run, reporting only). Dish-clustered bootstrap CIs, paired effects, selectivity permutation test, variance decomposition."""
import json,os,collections,numpy as np
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); rng=np.random.default_rng(20261010)
R=[json.loads(l) for l in open(os.path.join(ROOT,'logs','heldout_summary.jsonl'))]
ARMS=['ctrl','twin','sham','random','fixed','whole','whole_dm']
dishes=collections.defaultdict(dict)
for r in R:
    if r['reason' if 'reason' in r and r.get('arm')=='ctrl' else 'arm'] in('quota_skip','baseline_not_clean') and r.get('arm')=='ctrl': continue
    dishes[r['seed']][r['arm']]=r
dishes={s:a for s,a in dishes.items() if all(k in a for k in ARMS)}
def devend(r): # progress toward target at end: target S- => want u negative
    s=-1.0 if r['target']=='S-' else 1.0
    if 'u_end' not in r: r['u_end']=json.load(open(os.path.join(ROOT,'episodes_heldout',f"ep_{r['episode']:05d}.json")))['frames'][-1]['u'][0]
    return s*r['u_end']
def log(r):
    L=json.load(open(os.path.join(ROOT,'episodes_heldout',f"ep_{r['episode']:05d}.json"))); return L
def t_target(r):
    L=log(r); F=L['frames']; acts=L['actions']; t0=acts[0]['t'] if acts else None
    if t0 is None: return None
    tg=r['target']; idx=None
    for i in range(len(F)-1,-1,-1):
        if F[i]['state']==tg and F[i]['state_sure']: idx=i
        else: break
    return None if idx is None else max(F[idx]['t']-t0,0.0)
seeds=sorted(dishes); N=len(seeds)
def boot(vals,B=5000):  # vals: per-dish array; percentile CI of mean
    v=np.asarray(vals,float); v=v[~np.isnan(v)]
    if len(v)==0: return (np.nan,np.nan,np.nan)
    m=[v[rng.integers(len(v),size=len(v))].mean() for _ in range(B)]; return (float(v.mean()),float(np.quantile(m,.025)),float(np.quantile(m,.975)))
out={'n_dishes':N,'by_direction':{d:sum(dishes[s]['ctrl']['start']==d for s in seeds) for d in('S+','S-')}}
tab={}
for arm in ARMS:
    A=[dishes[s][arm] for s in seeds]; succ=[float(a['success']) for a in A]
    ds=[a['dose'] for a in A if a['success']]
    tt=[t_target(a) for a in A if a['success']]
    row=dict(success=boot(succ),V_body=boot([float(a['V_body']) for a in A]),V_body_cons=boot([float(a['V_body_conservative']) for a in A]),
             persist=boot([float(a['end_state']==a['target'] and a['end_sure']) for a in A]),dose_all=boot([a['dose'] for a in A]),
             dose_to_success=boot(ds) if ds else None,time_to_target=boot([x for x in tt if x is not None]) if tt else None,
             events=sum(bool(a['events']) for a in A),dev_end=boot([devend(a) for a in A]))
    if arm=='ctrl': row['probes']=boot([a['n_pulses'] for a in A]); row['reasons']=dict(collections.Counter(a['reason'] for a in A))
    tab[arm]=row
out['table']=tab
# per-direction success
out['success_by_direction']={arm:{d:boot([float(dishes[s][arm]['success']) for s in seeds if dishes[s]['ctrl']['start']==d]) for d in('S+','S-')} for arm in ARMS}
# paired effects (dish-level) vs twin and sham: success and end-progress
pe={}
for arm in ['ctrl','random','fixed','whole','whole_dm']:
    for ref in ('twin','sham'):
        pe[f'{arm}-{ref}']=dict(success=boot([float(dishes[s][arm]['success'])-float(dishes[s][ref]['success']) for s in seeds]),dev_end=boot([devend(dishes[s][arm])-devend(dishes[s][ref]) for s in seeds]))
out['paired']=pe
# sham-vs-twin check (procedure without dose should do nothing)
out['sham_minus_twin_dev_end']=boot([devend(dishes[s]['sham'])-devend(dishes[s]['twin']) for s in seeds])
# selectivity: controller vs random at matched dose; sign-flip permutation null over dishes
def perm(stat_a,stat_b,B=20000):
    d=np.array(stat_a)-np.array(stat_b); obs=d.mean(); null=[(d*rng.choice([-1,1],size=len(d))).mean() for _ in range(B)]
    return dict(obs=float(obs),p_two_sided=float((np.abs(null)>=abs(obs)-1e-12).mean()),ci=boot(d))
out['selectivity']=dict(
  success_ctrl_minus_random=perm([float(dishes[s]['ctrl']['success']) for s in seeds],[float(dishes[s]['random']['success']) for s in seeds]),
  dev_end_ctrl_minus_random=perm([devend(dishes[s]['ctrl']) for s in seeds],[devend(dishes[s]['random']) for s in seeds]),
  dose_ratio_random_over_ctrl=boot([dishes[s]['random']['dose']/max(dishes[s]['ctrl']['dose'],1e-9) for s in seeds]),
  success_ctrl_minus_fixed=perm([float(dishes[s]['ctrl']['success']) for s in seeds],[float(dishes[s]['fixed']['success']) for s in seeds]),
  success_ctrl_minus_whole=perm([float(dishes[s]['ctrl']['success']) for s in seeds],[float(dishes[s]['whole']['success']) for s in seeds]),
  dose_ctrl_minus_fixed=perm([dishes[s]['ctrl']['dose'] for s in seeds],[dishes[s]['fixed']['dose'] for s in seeds]),
  dose_whole_over_ctrl=boot([dishes[s]['whole']['dose']/max(dishes[s]['ctrl']['dose'],1e-9) for s in seeds]))
# random-arm realised dose match & cells
out['random_cells']=boot([np.mean(dishes[s]['random']['cells']) for s in seeds]); out['ctrl_cells']=boot([np.mean(dishes[s]['ctrl'].get('cells',[np.nan])) for s in seeds]) if 'cells' in dishes[seeds[0]]['ctrl'] else None
# dev-pool variance decomposition of log dose* (B2): share by factor (type-I sequential SS, order: dish, direction, duration, location)
B=[json.loads(l) for l in open(os.path.join(ROOT,'logs','b2_results.jsonl'))]; B=[b for b in B if b['dose_star'] and b['loc']!='whole']
y=np.log([b['dose_star'] for b in B]); tot=((y-y.mean())**2).sum(); res=y.copy(); shares={}
for name in ('dur','loc','label','seed'):
    g=collections.defaultdict(list)
    for yy,b in zip(res,B): g[b[name]].append(yy)
    mu={k:np.mean(v) for k,v in g.items()}; fitted=np.array([mu[b[name]] for b in B]); shares[name]=float(((fitted-res.mean())**2).sum()/tot); res=res-(fitted-res.mean())
shares['residual']=float((res**2).sum()/tot) if False else float(1-sum(shares.values())); out['dose_variance_share_dev_B2']=shares
json.dump(out,open(os.path.join(ROOT,'logs','heldout_eval.json'),'w'),indent=1,default=float)
print(json.dumps(out,indent=1,default=float)[:6000])

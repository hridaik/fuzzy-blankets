"""Exemplar pages. RULE (declared before looking at held-out results): within each start state (S+, S-) rank controller episodes by the
pre-declared metric M = dose if success else +inf (ties by time of last action end); pick the median-rank, the best (lowest M), the worst
(highest M, i.e. a failure if any), and two random picks (numpy default_rng(20261010)). One compare page (controller/twin/sham/random/fixed/whole/whole_dm)
per start state for the median-rank dish."""
import json,os,sys,numpy as np; sys.path.insert(0,'code')
from build_viewer import build
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R=[json.loads(l) for l in open(os.path.join(ROOT,'logs','heldout_summary.jsonl'))]
by={}
for r in R: by.setdefault(r['seed'],{})[r['arm']]=r
rng=np.random.default_rng(20261010); out=[]; os.makedirs('viewer/heldout',exist_ok=True)
ep=lambda r:f"episodes_heldout/ep_{r['episode']:05d}.json"
for st in('S+','S-'):
    D=[(s,a) for s,a in by.items() if 'ctrl' in a and a['ctrl']['start']==st and all(k in a for k in('twin','sham','random','fixed','whole','whole_dm'))]
    M=lambda a:(a['ctrl']['dose'] if a['ctrl']['success'] else 1e9, a['ctrl'].get('t_last_end') or 0)
    D.sort(key=lambda sa:M(sa[1])); n=len(D)
    picks={'median':D[n//2],'best':D[0],'worst':D[-1]}
    for k,i in enumerate(rng.choice(n,2,replace=False)): picks[f'random{k+1}']=D[int(i)]
    for name,(s,a) in picks.items():
        c=a['ctrl']; fn=f"viewer/heldout/ep_{st.replace('+','plus').replace('-','minus')}_{name}_seed{s}.html"
        build(fn,f"Controller episode — start {st}, {name}, seed {s}",f"success={c['success']} ({c['reason']}) dose={c['dose']:.0f} pulses={c['n_pulses']} V_body_cons={c['V_body_conservative']}",[ep(c)+':controller:'+c['reason']]); out.append(fn)
    s,a=picks['median']; fn=f"viewer/heldout/compare_{st.replace('+','plus').replace('-','minus')}_median_seed{s}.html"
    build(fn,f"Compare — start {st}, median-rank dish, seed {s}","same dish (CRN); controller / twin (no action) / sham (dose 0) / random location (dose matched) / fixed pulse / whole body (same amp) / whole body (dose matched)",
          [ep(a[k])+f':{k}:dose {a[k]["dose"]:.0f}, success {a[k]["success"]}' for k in('ctrl','twin','sham','random','fixed','whole','whole_dm')]); out.append(fn)
json.dump(out,open('viewer/pages.json','w'),indent=1); print(out)

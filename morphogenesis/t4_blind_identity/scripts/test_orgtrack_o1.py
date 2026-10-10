import sys; sys.path.insert(0,'.')
import numpy as np, collections
from t4 import io
from t4.orgtrack import OrganismTracker
cat=io.catalog()
for cond in ['N0','P01','P02','P03','P04','P05','P09','T3a','Xmig']:
    rr=[r for r in cat if r['condition']==cond and r['split']=='development']
    for r in rr[:3 if cond!='N0' else 1]:
        ot=OrganismTracker(io.CHANNELS['O1'],1.6,3,0.15,2.1)
        ev=collections.Counter(); first={}
        nor=[]
        for k,f in enumerate(io.point_frames(r['run'],'O1')):
            orgs,e=ot.step(f['t'],f['xy'],f['lev'],f['ids']); nor.append(len(orgs))
            for x in e:
                ev[x['type']]+=1; first.setdefault(x['type'],f['t'])
        print(cond,r['arm'],r['run'],'onset',r['onset'],'norg',''.join(map(str,nor[::max(1,len(nor)//20)])),dict(ev),'first',first)

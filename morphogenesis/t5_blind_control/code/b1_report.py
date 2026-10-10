import json,collections,numpy as np,sys
R=[json.loads(l) for l in open('logs/b1_results.jsonl')]
R=[r for r in R if r.get('stage') in('2a','2b')]
print(len(R))
T=collections.defaultdict(list)
for r in R:
    if r['stage']=='2a': T[(r['label'],r['dur'],round(r['amp']*r['dur']))].append(r['flipped'])
for lab in('L3','L4'):
    print(lab,'2a flip fraction; rows=dur, cols=product(amp*dur) 5 10 20 40 80 160')
    for dur in (2,5,10,30):
        print(' dur',dur,[f"{np.mean(T[(lab,float(dur),p)]):.1f}" for p in(5,10,20,40,80,160)])
T=collections.defaultdict(list); U=collections.defaultdict(list); C=collections.defaultdict(list)
for r in R:
    if r['stage']=='2b': k=(r['label'],(r['p'],r['q']),round(r['amp']*r['dur'])); T[k].append(r['flipped']); U[k].append(r['umax_dev']); C[k].append(r['cells'])
    if r['stage']=='2a' and r['dur']==10: k=(r['label'],(0.0,0.0),round(r['amp']*r['dur'])); T[k].append(r['flipped']); U[k].append(r['umax_dev']); C[k].append(r['cells'])
for lab in('L3','L4'):
    print(lab,'2b dur=10: location (p,q) vs product 10 20 40 80: flip frac|mean umax_dev|cells')
    for loc in [(0.0,0.0),(1.5,0),(-1.5,0),(0,1.5),(0,-1.5),(3,0),(-3,0)]:
        print(' ',loc,[f"{np.mean(T[(lab,loc,p)]):.1f}|{np.mean(U[(lab,loc,p)]):.2f}|{np.mean(C[(lab,loc,p)]):.0f}" for p in(10,20,40,80)])
print('events:',collections.Counter(tuple(r['events']) for r in R)); print('max pat_dz',max(r['pat_dz_max'] for r in R),'max mst',max(r['mst_max'] for r in R),'geo_warn',sum(r['geo_warn'] for r in R),'Vc false',sum(not r['Vc'] for r in R))

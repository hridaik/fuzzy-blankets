import json,collections,numpy as np
R=[json.loads(l) for l in open('logs/b2_results.jsonl')]
print(len(R),'configs;', sum(len(r['trials']) for r in R),'episodes; damage trials',sum(r['n_damage'] for r in R))
print('dose* (amp*dur*cells at minimal flipping amp found; bisection resolution ~1.4x) rows: loc,dur ; cols: L3 seed5002, L3 5005, L4 5001, L4 5004')
for loc in('C','side','head','tail','whole'):
    for dur in(5.0,10.0,20.0,40.0):
        row=[]
        for lab,seed in(('L3',5002),('L3',5005),('L4',5001),('L4',5004)):
            x=[r for r in R if r['label']==lab and r['seed']==seed and r['loc']==loc and r['dur']==dur]
            row.append('' if not x else ('none' if x[0]['dose_star'] is None else f"{x[0]['dose_star']:.0f}/{x[0]['prod_star']:.1f}x{x[0]['cells']}"))
        if any(row): print(f'{loc:5s} dur{dur:4.0f}',row)
d=collections.defaultdict(list)
for r in R:
    if r['dose_star']: d[(r['label'],r['loc'],r['dur'])].append(r['dose_star'])
print('\ngeom-mean dose* by (label,loc,dur) over seeds')
for k in sorted(d): print(k,round(float(np.exp(np.mean(np.log(d[k])))),0),len(d[k]))

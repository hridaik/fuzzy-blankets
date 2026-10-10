import sys,json,os,numpy as np; sys.path.insert(0,'code')
from controller import *
d=connect(); cfgp=sys.argv[1]; cfg=json.load(open(cfgp)); C=Controller(cfg)
OUT='logs/b3_dev.jsonl'
seeds=[int(x) for x in sys.argv[3:]]; mode=sys.argv[2]
for s in seeds:
    if mode=='ctrl':
        S=C.run(d,s,tag='b3_dev_ctrl'); S['arm']='ctrl:'+cfg['version']
    else:  # fixed amp list given as mode 'fixed:1.5,2.0'
        for amp in [float(x) for x in mode.split(':')[1].split(',')]:
            st=json.load(open('logs/seed_states.json'))[str(s)]
            lab=cfg['actuator'][st]; plan=[dict(t=cfg['baseline_tu'],mode='body',label=lab,p=0.0,q=0.0,radius=cfg['radius'],amp=amp,dur=cfg['dur'],ramp=cfg['ramp'])]
            S=replay(d,s,cfg,plan,cfg['baseline_tu']+cfg['dur']+cfg['hold'],st,tag='b3_dev_fixed'); S['arm']=f'fixed:{amp}'; S.pop('actions',None)
            with open(OUT,'a') as f: f.write(json.dumps(S,default=lambda o:o.item() if hasattr(o,'item') else str(o))+'\n')
            print(s,S['arm'],S['start'],S['success'],round(S['dose']),flush=True)
        continue
    S.pop('actions',None)
    with open(OUT,'a') as f: f.write(json.dumps(S,default=lambda o:o.item() if hasattr(o,'item') else str(o))+'\n')
    print(s,S['arm'],S['start'],S['success'],S['reason'],S['n_pulses'],round(S['dose']),flush=True)

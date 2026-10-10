"""Episode / compare pages. usage: build_viewer.py OUT.html TITLE META EPFILE:LABEL[:SUB] ... (each EPFILE an episode log json)"""
import sys,json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(path,label,sub=''):
    L=json.load(open(path)); fr=L['frames']
    keep=['t','xy','lev','state','state_sure','p_plus','u','V_body','V_body_conservative','V_body_now','material_ok','geometry_ok','pattern_ok','events','centroid','e1','pat_dz','mst_max','s1_rel','s2_rel']
    frames=[{k:f[k] for k in keep} for f in fr]
    acts=[dict(t=a['t'],label=a['label'],mask=a['mask'],amp=a['amp'],dur=a['dur'],ramp=a['ramp'],dose=a['dose'],sham=(a['dose']==0 and L.get('sham'))) for a in L['actions']]
    return dict(label=label,sub=sub+f" · episode {L['episode']} seed {L['seed']}",frames=frames,actions=acts,decisions=L['decisions'],bodyid=f"seed {L['seed']}")
def build(out,title,meta,specs):
    cfg=json.load(open(os.path.join(ROOT,'MONITOR_CONFIG.json')))
    eps=[load(*s.split(':')[0:1],*(s.split(':')[1:])) for s in specs]
    n=min(len(e['frames']) for e in eps)
    for e in eps: e['frames']=e['frames'][:n]
    data=dict(title=title,meta=meta,eps=eps,bounds=cfg['bounds'])
    html=open(os.path.join(ROOT,'viewer','template.html')).read().replace('__DATA__',json.dumps(data,separators=(',',':')))
    open(out,'w').write(html)
if __name__=='__main__': build(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4:])

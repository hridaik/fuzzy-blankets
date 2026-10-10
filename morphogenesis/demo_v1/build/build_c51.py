"""Chapter 5.1 flock clip: Stage 6.9 translation pilot, specified model (R=0.9, v=0.28, seed 37), frames from stage6_flock/interactive_demo/data/stage6_9_bundle.json."""
import sys; sys.path.insert(0, '.')
from common import *
d = json.load(open(f'{MORPH}/../stage6_flock/interactive_demo/data/stage6_9_bundle.json')); s = d['spec']; F = s['frames']
X = np.array([[f['x'], f['y']] for f in F]).transpose(0, 2, 1); mem = [f['members'] for f in F]
write_js('c51flock', dict(T=len(F), L=s['L'], N=s['N'], X=enc16(X - s['L'] / 2, 1000), members=mem, seed=s['seed'], R=s['R'], v=s['v'], gate_passes=s['gate_passes'], note='Stage 6.9 translation pilot, specified model; tracked collective = members (material tracker); positions on a 24x24 torus (centred)'))
print(len(F), X.shape, [len(m) for m in mem][:5])

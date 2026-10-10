"""Sealed live environment server (engine side). Run as a separate process: python live_server.py --ready ready.json [--sealed DIR] [--port 0].
Clients talk JSON lines over a local TCP socket with a one-time token. The server never returns any internal quantity; the hidden state of every episode goes to the sealed directory only."""
import sys, os, json, socket, secrets, time, base64, argparse, hashlib, traceback
HERE = os.path.dirname(os.path.abspath(__file__)); V3 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(V3, 'code')); sys.dont_write_bytecode = True
import numpy as np
import world4, build_blind4 as B4, build_blind3 as B3
from world4 import Experiment4, CH4
from world3 import Mask
LEVELS = ('O1', 'O2', 'O3a', 'O3b', 'O3c'); LIGHTS = {v: k for k, v in B3.LIGHT_LABELS.items()}                  # 'L3' -> 'MA'
CH = {'MA': ('mem', 0), 'MB': ('mem', 1), 'SEC': ('sec', 0), 'RG': ('rg', 0), 'MIG': ('mig', 0)}
POOLS = dict(development=range(5000, 5400), heldout=range(6000, 6200))
DEFAULT_BUDGET = dict(ep_time=600.0, ep_dose=20000.0, ep_actions=20, total_episodes=200, total_time=60000.0, total_dose=400000.0)
PROTOCOL = 1
class Err(Exception): pass
def enc_img(a, dtype):
    a = np.ascontiguousarray(a.astype(dtype)); return dict(shape=list(a.shape), dtype=str(a.dtype), b64=base64.b64encode(a.tobytes()).decode())
class Episode:
    def __init__(self, eid, pool, seed, sham_of, server):
        self.id, self.pool, self.seed, self.sham = eid, pool, seed, sham_of is not None; self.sham_of = sham_of
        st = 'a' if np.random.default_rng(seed + 17).random() < 0.5 else 'b'; self.state0 = st
        priv = {k: v for k, v in CH.items()}; self.ex = Experiment4(st, seed=seed, noise=0.02, sig_h=0.4, private=priv, form_seed=seed); self.ex.run(100.0, observe=False); self.ex.t0 = self.ex.w.time; self.ex.obs = []
        self.actions = []; self.step_idx = 0; self.time_used = 0.0; self.dose = 0.0; self.ended = False; self.log = []; self.record()
    def t(self): return round(self.ex.w.time - self.ex.t0, 6)
    def record(self):
        w = self.ex.w; self.log.append(dict(t=self.t(), X=w.X.copy(), C=w.C.copy(), MU=w.MU.copy(), L=w.L.copy(), D=w.D.copy(), E=w.E.copy(), alive=w.alive.copy(), cell_id=w.cell_id.copy()))
class Server:
    def __init__(self, sealed, budget):
        self.sealed = sealed; os.makedirs(sealed, exist_ok=True); os.chmod(sealed, 0o700); self.budget = dict(DEFAULT_BUDGET, **budget); self.eps = {}; self.next_id = 1; self.frozen = None; self.used = dict(episodes=0, time=0.0, dose=0.0); self.used_seeds = {p: set() for p in POOLS}; self.load()
    def load(self):
        # session state survives a server restart (counters, used seeds, freeze); running episodes do not
        fp = os.path.join(self.sealed, 'freeze.json')
        if os.path.exists(fp): self.frozen = json.load(open(fp))['hash']
        sp = os.path.join(self.sealed, 'session.json')
        if os.path.exists(sp):
            d = json.load(open(sp)); self.used = d['used']; self.next_id = d['next_id']; self.used_seeds = {p: set(v) for p, v in d['used_seeds'].items()}
    def save(self):
        tmp = os.path.join(self.sealed, 'session.json.tmp'); json.dump(dict(used=self.used, next_id=self.next_id, used_seeds={p: sorted(v) for p, v in self.used_seeds.items()}), open(tmp, 'w')); os.replace(tmp, os.path.join(self.sealed, 'session.json'))
    def ping(self): return dict(ok=True, protocol=PROTOCOL)
    def bstat(self, ep=None):
        d = dict(total_episodes_used=self.used['episodes'], total_episodes_max=self.budget['total_episodes'], total_time_used=round(self.used['time'], 3), total_time_max=self.budget['total_time'], total_dose_used=round(self.used['dose'], 3), total_dose_max=self.budget['total_dose'])
        if ep is not None: d.update(episode_time_used=round(ep.time_used, 3), episode_time_max=self.budget['ep_time'], episode_dose_used=round(ep.dose, 3), episode_dose_max=self.budget['ep_dose'], episode_actions_used=len(ep.actions), episode_actions_max=self.budget['ep_actions'])
        return d
    def get(self, eid):
        ep = self.eps.get(eid)
        if ep is None or ep.ended: raise Err('unknown or finished episode')
        return ep
    # ---------------------------------------------------------------- API
    def reset(self, seed_pool='development', seed=None, sham_of=None):
        if self.used['episodes'] >= self.budget['total_episodes']: raise Err('episode budget exhausted')
        if sham_of is not None:
            o = self.eps.get(sham_of); 
            if o is None: raise Err('unknown episode for sham request')
            seed_pool, seed = o.pool, o.seed
        if seed_pool not in POOLS: raise Err('unknown seed pool')
        if seed_pool == 'heldout' and self.frozen is None: raise Err('the held-out pool is locked until freeze(hash) has been called')
        if seed is None:
            free = [s for s in POOLS[seed_pool] if s not in self.used_seeds[seed_pool]]; seed = free[0]
        elif seed not in POOLS[seed_pool]: raise Err('seed not in pool')
        if sham_of is None: self.used_seeds[seed_pool].add(seed)
        eid = self.next_id; self.next_id += 1; ep = Episode(eid, seed_pool, int(seed), sham_of, self); self.eps[eid] = ep; self.used['episodes'] += 1; self.save()
        return dict(episode=eid, seed_pool=seed_pool, seed=int(seed), sham=ep.sham, time=ep.t(), budget=self.bstat(ep))
    def observe(self, episode, level):
        ep = self.get(episode)
        if level not in LEVELS: raise Err('unknown level')
        w = ep.ex.w; f = dict(t=ep.t(), X=w.X, C=w.C, D=w.D, E=w.E, alive=w.alive, cell_id=w.cell_id); rng = np.random.default_rng([ep.seed, int(round(ep.t() * 2)), LEVELS.index(level)]); a = f['alive']; t = f['t']
        if level in ('O1', 'O2'):
            X = f['X'][a] + B3.POS_NOISE * rng.standard_normal((a.sum(), 2)); Lv = B3.lnoise(rng, B3.levels(f)[a])[:, B3.COL_PERM]
            if level == 'O1': return dict(level=level, t=t, id=f['cell_id'][a].tolist(), xy=np.round(X, 5).tolist(), level_values=np.round(Lv, 5).tolist(), budget=self.bstat(ep))
            p = rng.permutation(len(X)); return dict(level=level, t=t, xy=np.round(X[p], 5).tolist(), level_values=np.round(Lv[p][:, B3.O2_COLS], 5).tolist(), budget=self.bstat(ep))
        if level in ('O3a', 'O3b'):
            cols = B3.O3A if level == 'O3a' else B3.O3B; g = np.linspace(-12.0, 12.0, B3.IMG_PX); GX, GY = np.meshgrid(g, g); P = np.stack([GX.ravel(), GY.ravel()], 1); px = 24.0 / B3.IMG_PX
            d = np.exp(-np.linalg.norm(P[:, None, :] - f['X'][a][None], axis=-1)); LvT = B3.levels(f)[a][:, B3.COL_PERM]; im = np.stack([(d @ LvT[:, c]).reshape(B3.IMG_PX, B3.IMG_PX) for c in cols])
            from scipy.ndimage import gaussian_filter
            im = np.stack([gaussian_filter(m, B3.PSF_SIGMA / px) for m in im]); pk = np.maximum(im.max(axis=(1, 2), keepdims=True), 1e-6); im = np.clip(im + rng.standard_normal(im.shape) * pk / B3.SNR, 0, None)
            return dict(level=level, t=t, fov=12.0, image=enc_img(im, np.float16), budget=self.bstat(ep))
        q = B4.c_channels(f, B4.FOV_C, B4.PX_C, rng); return dict(level=level, t=t, fov=B4.FOV_C, scale=B4.C_SCALE.tolist(), image=enc_img(q, np.uint8), budget=self.bstat(ep))
    def act(self, episode, channel_label, arena_mask, amplitude, duration, ramp):
        ep = self.get(episode); b = self.budget
        if len(ep.actions) >= b['ep_actions']: raise Err('action budget of the episode exhausted')
        if not (0 <= amplitude <= 500): raise Err('amplitude out of range'); 
        if duration <= 0 or ramp < 0 or 2 * ramp > duration + 1e-9: raise Err('invalid duration / ramp')
        w = ep.ex.w; kind = arena_mask.get('type') if isinstance(arena_mask, dict) else None
        if kind == 'disc': shapes = [('disc', float(arena_mask['xy'][0]), float(arena_mask['xy'][1]), float(arena_mask['radius']), 1.0)]
        elif kind == 'halfplane': shapes = [('halfplane', float(arena_mask['n'][0]), float(arena_mask['n'][1]), float(arena_mask['d']), 1.0)]
        elif kind == 'all': shapes = [('halfplane', 0.0, 0.0, -1.0, 1.0)]
        else: raise Err('unsupported mask')
        mask = Mask(shapes); inside = int(((mask(w.X) * w.alive) > 0.5).sum()); dose = float(amplitude) * float(duration) * inside
        if channel_label in LIGHTS: act = dict(type='light', channel=LIGHTS[channel_label], mask=mask, amp=float(amplitude), t_on=ep.t(), t_off=ep.t() + duration, ramp=float(ramp))
        else: raise Err('unknown channel label (lights L1-L5)')
        if ep.dose + (0.0 if ep.sham else dose) > b['ep_dose'] or self.used['dose'] + (0.0 if ep.sham else dose) > b['total_dose']: raise Err('dose budget exhausted')
        ep.actions.append(act); ep.dose += 0.0 if ep.sham else dose; self.used['dose'] += 0.0 if ep.sham else dose; self.save()
        return dict(accepted=True, dose=round(0.0 if ep.sham else dose, 4), cells_in_mask=inside, time=ep.t(), budget=self.bstat(ep))
    def step(self, episode, dt):
        ep = self.get(episode); b = self.budget; n = round(dt / CH4)
        if dt <= 0 or abs(n * CH4 - dt) > 1e-9: raise Err('dt must be a positive multiple of 0.5')
        if ep.time_used + dt > b['ep_time'] + 1e-9 or self.used['time'] + dt > b['total_time'] + 1e-9: raise Err('time budget exhausted')
        obs = []; ep.ex.run_sched(dt, ep.actions, sham=ep.sham, obs_times=[]); ep.time_used += dt; self.used['time'] += dt; self.save(); ep.step_idx += 1; ep.record()
        return dict(time=ep.t(), budget=self.bstat(ep))
    def end_episode(self, episode):
        ep = self.get(episode); ep.ended = True; d = os.path.join(self.sealed, f'episode_{ep.id:05d}'); os.makedirs(d, exist_ok=True)
        np.savez_compressed(os.path.join(d, 'hidden.npz'), t=np.array([r['t'] for r in ep.log]), **{k: np.stack([r[k] for r in ep.log]) for k in ('X', 'C', 'MU', 'L', 'D', 'E', 'alive', 'cell_id')})
        json.dump(dict(pool=ep.pool, seed=ep.seed, sham=ep.sham, sham_of=ep.sham_of, state0=ep.state0, hidden_events=ep.ex.hidden()['events'], actions=[{k: v for k, v in a.items() if k != 'mask'} for a in ep.actions], private=ep.ex.hidden()['private'], freeze_hash=self.frozen, pose=ep.ex.hidden_pose), open(os.path.join(d, 'episode.json'), 'w'), default=str)
        return dict(ended=True, budget=self.bstat(ep))
    def freeze(self, hash):
        if self.frozen is not None: raise Err('already frozen')
        if not isinstance(hash, str) or len(hash) < 8: raise Err('hash must be a string of at least 8 characters')
        self.frozen = hash; open(os.path.join(self.sealed, 'freeze.json'), 'w').write(json.dumps(dict(hash=hash, time=time.time()))); return dict(frozen=True, heldout_unlocked=True)
    def status(self): return dict(budget=self.bstat(), frozen=self.frozen is not None, levels=list(LEVELS), light_labels=sorted(LIGHTS), pools=dict(development=[POOLS['development'].start, POOLS['development'].stop - 1]))
def handle(srv, req):
    m = req.get('method'); a = req.get('args', {})
    fn = {'reset': srv.reset, 'observe': srv.observe, 'act': srv.act, 'step': srv.step, 'end_episode': srv.end_episode, 'freeze': srv.freeze, 'status': lambda: srv.status(), 'ping': srv.ping}.get(m)
    if fn is None: raise Err('unknown method')
    return fn(**a)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--ready', required=True); ap.add_argument('--sealed', default=os.path.join(V3, 'live_sealed')); ap.add_argument('--port', type=int, default=0); ap.add_argument('--budget', default='{}'); args = ap.parse_args()
    srv = Server(args.sealed, json.loads(args.budget)); cp = os.path.join(srv.sealed, 'conn.json')
    if os.path.exists(cp): cn = json.load(open(cp)); token, port = cn['token'], cn['port']          # restart: same connection data
    else: token, port = secrets.token_hex(16), args.port
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(('127.0.0.1', port)); s.listen(1); port = s.getsockname()[1]
    json.dump(dict(port=port, token=token), open(cp, 'w')); os.chmod(cp, 0o600)
    json.dump(dict(host='127.0.0.1', port=port, token=token, protocol=PROTOCOL), open(args.ready, 'w')); os.chmod(args.ready, 0o600)
    while True:
        c, _ = s.accept(); f = c.makefile('rwb')
        try:
            for line in f:
                try:
                    req = json.loads(line)
                    if req.get('token') != token: resp = dict(ok=False, error='bad token')
                    elif req.get('method') == 'shutdown': f.write((json.dumps(dict(ok=True)) + '\n').encode()); f.flush(); c.close(); s.close(); return
                    else: resp = dict(ok=True, result=handle(srv, req))
                except Err as e: resp = dict(ok=False, error=str(e))
                except Exception as e: resp = dict(ok=False, error='server error'); open(os.path.join(srv.sealed, 'server_errors.log'), 'a').write(traceback.format_exc() + '\n')
                f.write((json.dumps(resp) + '\n').encode()); f.flush()
        finally:
            try: c.close()
            except Exception: pass
if __name__ == '__main__': main()

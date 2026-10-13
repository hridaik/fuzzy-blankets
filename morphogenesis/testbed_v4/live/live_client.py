"""Client library for the live dish environment. Standard library + numpy only; it cannot import anything from the simulator."""
import json, socket, base64
import numpy as np
class DishError(Exception): pass
def _dec(im): return np.frombuffer(base64.b64decode(im['b64']), dtype=np.dtype(im['dtype'])).reshape(im['shape'])
class Dish:
    def __init__(self, ready_file):
        r = json.load(open(ready_file)); self.token = r['token']; self.sock = socket.create_connection(('127.0.0.1', r['port'])); self.f = self.sock.makefile('rwb')
    def _call(self, method, **args):
        self.f.write((json.dumps(dict(token=self.token, method=method, args=args)) + '\n').encode()); self.f.flush(); resp = json.loads(self.f.readline())
        if not resp['ok']: raise DishError(resp['error'])
        return resp['result']
    def ping(self): return self._call('ping')
    def status(self): return self._call('status')
    def reset(self, seed_pool='development', seed=None, sham_of=None): return self._call('reset', seed_pool=seed_pool, seed=seed, sham_of=sham_of)
    def observe(self, episode, level):
        r = self._call('observe', episode=episode, level=level)
        if 'image' in r: r['image'] = _dec(r['image'])
        else:
            r['xy'] = np.array(r['xy']); r['level_values'] = np.array(r['level_values'])
            if 'id' in r: r['id'] = np.array(r['id'])
        return r
    def act(self, episode, channel_label, arena_mask, amplitude, duration, ramp): return self._call('act', episode=episode, channel_label=channel_label, arena_mask=arena_mask, amplitude=amplitude, duration=duration, ramp=ramp)
    def step(self, episode, dt): return self._call('step', episode=episode, dt=dt)
    def end_episode(self, episode): return self._call('end_episode', episode=episode)
    def freeze(self, hash): return self._call('freeze', hash=hash)
    def shutdown(self):
        try: self.f.write((json.dumps(dict(token=self.token, method='shutdown')) + '\n').encode()); self.f.flush(); self.f.readline()
        except Exception: pass

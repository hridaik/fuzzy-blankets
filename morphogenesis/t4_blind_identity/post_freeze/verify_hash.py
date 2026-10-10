import json, hashlib
cfg = json.load(open('FROZEN_CONFIG.json')); h = hashlib.sha256()
for f in cfg['files_hashed']:
    h.update(f.encode()); h.update(open(f, 'rb').read())
print('recomputed', h.hexdigest()); print('frozen    ', cfg['code_sha256']); print('MATCH' if h.hexdigest() == cfg['code_sha256'] else 'MISMATCH')

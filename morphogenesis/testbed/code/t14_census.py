"""T1.4(b): engine census from the ORACLE's own initial beliefs (50 primary randn/8, 50 secondary std exp(2)); class vs oracle class per draw."""
import sys, time; sys.path.insert(0,'.')
from common import *
KMU, KA, DT = 1.4, 1.2, 0.02
def main():
    t = vanilla8(); eng = make_engine(t, Params(k_mu=KMU, k_a=KA)); key = jax.random.PRNGKey(0)
    ref = json.load(open(M2A + '/sealed/reference_phenotype_v2.json')); rp, rs = np.array(ref['pos']), np.array(ref['sec'])
    rows = json.load(open(M2A + '/data/v2/r1_results.json'))['rows']; ocls = {r['id']: r['class'] for r in rows}
    # oracle class-1 reference: the oracle's own class-1 end state (secondary_0005)
    o5 = oracle_run('secondary_0005'); p1, s1 = o5['pos'][:, :, -1], o5['sec'][:, :, -1]
    out = []
    t0 = time.time()
    for kind, N in (('primary', 50), ('secondary', 50)):
        for k in range(N):
            nm = f'{kind}_{k:04d}'
            if nm not in ocls: continue
            o = oracle_run(nm); st = eng.init_from_mu(o['v0'].T)
            fin = eng.run_final(st, 0.0, DT, int(500 / DT), key, None, 0)
            X, C, MU, _ = [np.array(a) for a in fin]
            sp = max(float(jnp.abs(a).max()) for a in eng.drift(fin, 1e9, jnp.zeros((8, 4))))
            d0 = d_pair(X.T, C.T, rp, rs); d1 = d_pair(X.T, C.T, p1, s1)
            cls = 0 if d0 < 0.17 else (1 if d1 < 0.17 else 2)
            mb = float(np.array(jax.nn.softmax(MU, axis=1)).max(1).min())
            out.append(dict(id=nm, oracle_class=int(ocls[nm]), engine_class=cls, d0=d0, d1=d1, resid=sp, min_maxbelief=mb))
        print(kind, time.time() - t0, flush=True)
    json.dump(out, open(os.path.join(TB, 'data', 't14_census.json'), 'w'), indent=1)
    for kind in ('primary', 'secondary'):
        r = [x for x in out if x['id'].startswith(kind)]
        print(kind, len(r), 'engine class counts', np.bincount([x['engine_class'] for x in r], minlength=3), 'oracle', np.bincount([x['oracle_class'] for x in r], minlength=3),
              'agree', sum(x['engine_class'] == x['oracle_class'] for x in r), 'max resid', max(x['resid'] for x in r), 'max d0 among class0', max([x['d0'] for x in r if x['engine_class'] == 0]))
main()

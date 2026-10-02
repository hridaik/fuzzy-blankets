import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from d4_dirs import *
if __name__ == "__main__":
    rng = np.random.default_rng(1)
    specs = [dirs_disp1()[0], dirs_disp1()[3 * 16 + 4], dirs_body()[3], dirs_pulse_single()[0], dirs_region()[0], dirs_global()[0]]
    print([s["id"] for s in specs])
    run_tasks([(job, (s,)) for s in specs], workers=6, label="D4-pilot")
    for s in specs:
        r = json.load(open(os.path.join(DATA, "v2", "d4", f"dir_{s['id']}.json"))); print(s["id"], {k: r[k] for k in ("swap", "switch", "outcomes_top", "nonmonotone")}, r["evals"])

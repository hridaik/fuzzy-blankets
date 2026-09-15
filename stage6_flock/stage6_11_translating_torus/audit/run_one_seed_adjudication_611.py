"""Runs branch_adjudication_611.run_seed for ONE seed (argv[1]) and saves its
JSON -- lets all 5 seeds run as independent parallel processes."""
import json
import sys
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(AUDIT_DIR.parent / "code"))
import common_611  # noqa: E402,F401
from common_611 import dump_json  # noqa: E402
import branch_adjudication_611 as BA  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

seed = int(sys.argv[1])
trigger_states = json.load(open(AUDIT_DIR / "trigger_states_611.json"))
mf = ROC.make_flock()
out = BA.run_seed(seed, trigger_states[str(seed)], mf)
dump_json(out, AUDIT_DIR / f"branch_adjudication_611__seed{seed}.json")
print(f"seed {seed} done")

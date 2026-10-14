"""E-low v3 (docs/prereg_lowdata_v3.md section 3): per test field, P(no miss) and overlap of the plan pi(lam) on a
geometric lambda grid of 24 points between 0.6 lam* and min(8 lam*, cap), cap = 0.4 w (planner feasibility,
h >= 0.2 w/2), 200 runs per point with common random numbers (seed as in E-low phase B). Cached per field.

    python3 scripts/curves_v3.py --dir results/lowdata_v3 --jobs 4
"""
import argparse
import glob
import os
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import core  # noqa: E402
import exp_lowdata as X  # noqa: E402
import exp_system as E  # noqa: E402


def cap(reg):
    return 0.4 * reg["w"]


def curve(args):
    d, key, fi = args
    out_f = os.path.join(d, f"curve_{key}_{fi}.pkl")
    if os.path.exists(out_f):
        return out_f
    rname, reg = X.regime(key)
    w = reg["w"]
    F = core.load_fields(reg["kind"], w=w, seed=0)[fi]
    r = pickle.load(open(os.path.join(d, f"A_{key}_{fi}.pkl"), "rb"))
    S_l = E.sim_core(F, lambda: "lqr_i", reg)
    seed_t = E._seed(rname, "lowdata-test", F.fid)
    hi = min(8 * r["oracle_lam"], cap(reg))
    grid = np.geomspace(0.6 * r["oracle_lam"], hi, 24)
    lams, P, OV = [], [], []
    for lam in grid:
        try:
            ys = core.plan(F, w, float(lam), E.UNIT)
        except ValueError:
            continue
        ev = E.evaluate(F, w, ys, S_l, X.N_TEST, seed_t, reg)
        lams.append(float(lam)), P.append(ev["p_nomiss"]), OV.append(ev["overlap"])
    rec = dict(key=key, fi=fi, fid=F.fid, lam=np.array(lams), P=np.maximum.accumulate(np.array(P)), ov=np.array(OV),
               oracle_lam=r["oracle_lam"], oracle_overlap=r["oracle_overlap"], cap=cap(reg))
    pickle.dump(rec, open(out_f, "wb"))
    print(f"[curve] {key} field {F.fid}: {len(lams)} points, P {rec['P'][0]:.2f}..{rec['P'][-1]:.2f}", flush=True)
    return out_f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(HERE, "..", "results", "lowdata_v3"))
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    todo = []
    for f in sorted(glob.glob(os.path.join(a.dir, "A_*.pkl"))):
        key, fi = os.path.basename(f)[2:-4].split("_")
        todo.append((a.dir, key, int(fi)))
    with ProcessPoolExecutor(a.jobs) as ex:
        list(ex.map(curve, todo))


if __name__ == "__main__":
    main()

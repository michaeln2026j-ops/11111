"""Extend the lambda curves of the v2/v3 fields below their lowest point (0.6 lam*) down to 0.25 lam*
(6 geometric points), with the same seeds as the original curves, so that deployments with small erosion
are read from simulation instead of the lowest grid point. Updates curve_*.pkl in place (keeps the old
points; marks the file with 'extended': True).

    python3 scripts/extend_curves.py --jobs 4
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


def extend(f):
    c = pickle.load(open(f, "rb"))
    if c.get("extended"):
        return f
    key, fi = c["key"], c["fi"]
    rname, reg = X.regime(key)
    w = reg["w"]
    F = core.load_fields(reg["kind"], w=w, seed=0)[fi]
    S_l = E.sim_core(F, lambda: "lqr_i", reg)
    seed_t = E._seed(rname, "lowdata-test", F.fid)
    lam, P, ov = list(c["lam"]), list(c["P"]), list(c["ov"])
    for g in np.geomspace(0.25, 0.6, 7)[:-1] * c["oracle_lam"]:
        ys = core.plan(F, w, float(g), E.UNIT)
        ev = E.evaluate(F, w, ys, S_l, X.N_TEST, seed_t, reg)
        lam.append(float(g)), P.append(ev["p_nomiss"]), ov.append(ev["overlap"])
    o = np.argsort(lam)
    c["lam"], c["ov"] = np.array(lam)[o], np.array(ov)[o]
    c["P"] = np.maximum.accumulate(np.array(P)[o])
    c["extended"] = True
    pickle.dump(c, open(f, "wb"))
    print(f"[extend] {key} field {F.fid}: P at 0.25 lam* {c['P'][0]:.2f}", flush=True)
    return f


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(HERE, "..", "results", "lowdata_v2", "curve_*.pkl"))
                   + glob.glob(os.path.join(HERE, "..", "results", "lowdata_v3", "curve_*.pkl")))
    with ProcessPoolExecutor(a.jobs) as ex:
        list(ex.map(extend, files))

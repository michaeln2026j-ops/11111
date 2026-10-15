"""Validation of the field-edge terms in evt_theory.predict_cdf: predicted 0.9-quantile of the exact score at
the reference plan, with and without the edge terms, against the empirical 0.9-quantile of 200 independent
simulated runs (hist bank of validity_resample.py), on the E-low v3 fields.

    python3 scripts/check_boundary.py R3 --jobs 4
"""
import argparse
import os
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import core  # noqa: E402
import evt_theory as T  # noqa: E402
import exp_lowdata as X  # noqa: E402
import exp_system as E  # noqa: E402

D = os.path.join(HERE, "..", "results", "lowdata_v3")


def one(args):
    key, fi = args
    rname, reg = X.regime(key)
    w = reg["w"]
    F = core.load_fields(reg["kind"], w=w, seed=0)[fi]
    r = pickle.load(open(os.path.join(D, f"A_{key}_{fi}.pkl"), "rb"))
    S = pickle.load(open(os.path.join(D, f"hist_{key}_{fi}.pkl"), "rb"))
    tg = r["lam0"] * np.linspace(0.3, 3.0, 60)
    Fn = T.predict_cdf(F, w, reg, r["lam0"], tg, n_cond=200, rng=np.random.default_rng(E._seed(rname, "lowdata", F.fid)))
    q_new = X.inv_cdf(tg, Fn, 0.9)
    q_old = X.inv_cdf(r["tgrid"], r["Fhat"], 0.9)
    return key, F.fid, r["K0"], q_old, q_new, float(np.quantile(S, 0.9))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="+")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--limit", type=int, default=15)
    a = ap.parse_args()
    todo = [(k, fi) for k in a.keys for fi in range(5, 5 + a.limit)]
    with ProcessPoolExecutor(a.jobs) as ex:
        res = list(ex.map(one, todo))
    lines = []
    for key in a.keys:
        rr = [x for x in res if x[0] == key]
        eo = np.log([x[3] / x[5] for x in rr]); en = np.log([x[4] / x[5] for x in rr])
        for x in rr:
            lines.append(f"{key} field {x[1]:4d} passes {x[2]:3d}: q_old {x[3]:.3f}  q_new {x[4]:.3f}  sim {x[5]:.3f}")
        lines.append(f"{key}: log(q/sim) without edges mean {eo.mean():+.3f} sd {eo.std():.3f};  with edges mean {en.mean():+.3f} sd {en.std():.3f}")
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(D, f"check_boundary_{'_'.join(a.keys)}.txt"), "w").write(txt + "\n")

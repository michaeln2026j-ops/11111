"""RV6 (docs/prereg_revision.md): R3 theory with the field-edge terms on the 30 E-low v2 fields (50-79), in the
format of check_boundary.py, with the CPU time of each prediction.

    python3 scripts/rev_edges.py --jobs 1     # -> results/revision/rv6_edges_R3.txt
"""
import argparse
import os
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import core  # noqa: E402
import evt_theory as T  # noqa: E402
import exp_lowdata as X  # noqa: E402
import exp_system as E  # noqa: E402

D = os.path.join(HERE, "..", "results", "lowdata_v2")


def one(fi):
    key = "R3"
    rname, reg = X.regime(key)
    w = reg["w"]
    F = core.load_fields(reg["kind"], w=w, seed=0)[fi]
    r = pickle.load(open(os.path.join(D, f"A_{key}_{fi}.pkl"), "rb"))
    S = pickle.load(open(os.path.join(D, f"hist_{key}_{fi}.pkl"), "rb"))
    tg = r["lam0"] * np.linspace(0.3, 3.0, 60)
    t0 = time.process_time()
    Fn = T.predict_cdf(F, w, reg, r["lam0"], tg, n_cond=200, rng=np.random.default_rng(E._seed(rname, "lowdata", F.fid)))
    cpu = time.process_time() - t0
    return key, F.fid, r["K0"], X.inv_cdf(r["tgrid"], r["Fhat"], 0.9), X.inv_cdf(tg, Fn, 0.9), float(np.quantile(S, 0.9)), cpu


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    a = ap.parse_args()
    with ProcessPoolExecutor(a.jobs) as ex:
        res = list(ex.map(one, range(50, 80)))
    lines = [f"{x[0]} field {x[1]:4d} passes {x[2]:3d}: q_old {x[3]:.3f}  q_new {x[4]:.3f}  sim {x[5]:.3f}  cpu {x[6]:.0f}s"
             for x in res]
    eo = np.log([x[3] / x[5] for x in res]); en = np.log([x[4] / x[5] for x in res])
    lines.append(f"R3: log(q/sim) without edges mean {eo.mean():+.3f} sd {eo.std():.3f};  with edges mean {en.mean():+.3f} "
                 f"sd {en.std():.3f}; cpu median {np.median([x[6] for x in res]):.0f}s")
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(HERE, "..", "results", "revision", "rv6_edges_R3.txt"), "w").write(txt + "\n")

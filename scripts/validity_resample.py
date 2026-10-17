"""Direct check of the coverage guarantee over BOTH sources of randomness (docs/prereg_validity.md):
which fields calibrate / which is new (random splits), and how each calibration field's single historical
run turned out (redrawn from a bank of 200 independent historical runs per field).

    python3 scripts/validity_resample.py --jobs 2      # builds the run banks (cached), then 4000 replicates
"""
import argparse
import math
import os
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import ceplus as CP  # noqa: E402
import core  # noqa: E402
import exp_lowdata as X  # noqa: E402
import exp_system as E  # noqa: E402
from analyze_lowdata_v3 import KEYS, RES, load  # noqa: E402

EPS, DELTA, N_CAL, REPS, N_HIST = 0.1, 0.1, 25, 4000, 200


def bank(args):
    d, key, fi = args
    out_f = os.path.join(d, f"hist_{key}_{fi}.pkl")
    if os.path.exists(out_f):
        return pickle.load(open(out_f, "rb"))
    rname, reg = X.regime(key)
    w = reg["w"]
    F = core.load_fields(reg["kind"], w=w, seed=0)[fi]
    r = pickle.load(open(os.path.join(d, f"A_{key}_{fi}.pkl"), "rb"))
    ys0 = core.plan(F, w, r["lam0"], E.UNIT)
    rng = np.random.default_rng(E._seed(rname, "lowdata-hist", F.fid))
    cond = E.make_cond(rng, N_HIST, reg)
    Xs, Ds = E.sim_core(F, lambda: "lqr_i", reg)(ys0, cond, rng)
    S = np.asarray(core.exact_scores(F, ys0, Xs, Ds, w, r["lam0"]), float)
    pickle.dump(S, open(out_f, "wb"))
    print(f"[bank] {key} field {F.fid}: S median {np.median(S):.3f}, q0.9 {np.quantile(S, 0.9):.3f}", flush=True)
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()
    recs = []
    for d in (os.path.join(RES, "lowdata_v2"), os.path.join(RES, "lowdata_v3")):
        for r in load(d):
            r["dir"] = d
            r["cur"] = pickle.load(open(os.path.join(d, f"curve_{r['key']}_{r['fi']}.pkl"), "rb"))
            recs.append(r)
    with ProcessPoolExecutor(a.jobs) as ex:
        banks = list(ex.map(bank, [(r["dir"], r["key"], r["fi"]) for r in recs]))
    for r, b in zip(recs, banks):
        r["bank"] = b
        lg = math.sqrt(2 * math.log(max(r["N_len"], 2.0)))
        r["q"] = {"raw": 1.0, "scale law": lg, "spec x scale law": r["reg"]["p2p"] * lg,
                  "theory": X.inv_cdf(r["tgrid"], r["Fhat"], 1 - EPS) if r["ok"] else np.nan}
    rng = np.random.default_rng(0)
    out = []
    for sc in KEYS + ("mixed",):
        pool = recs if sc == "mixed" else [r for r in recs if r["key"] == sc]
        n = len(pool)
        names = ["raw", "scale law", "theory"] + (["spec x scale law"] if sc == "mixed" else [])
        out.append(f"\n== {sc}: {n} fields, {REPS} replicates (random split {N_CAL}/{n - N_CAL} + redrawn historical run)")
        for cls, dl in (("marginal", None), ("PAC", DELTA)):
            for nm in names:
                cov, ex = np.empty(REPS), np.empty(REPS)
                for b in range(REPS):
                    perm = rng.permutation(n)
                    cal, tgt = perm[:N_CAL], perm[N_CAL:]
                    V = []
                    for i in cal:
                        q = pool[i]["q"][nm]
                        s = pool[i]["bank"][rng.integers(len(pool[i]["bank"]))]
                        V.append(np.inf if not np.isfinite(q) else s / q)
                    t = CP.quantile(np.array(V), EPS, dl)
                    ps, es = [], []
                    for g in tgt:
                        r = pool[g]
                        q = r["q"][nm]
                        lam = min(q * t, r["cap"]) if np.isfinite(q * t) else r["cap"]
                        ps.append(np.interp(lam, r["cur"]["lam"], r["cur"]["P"]))
                        es.append(100 * (np.interp(lam, r["cur"]["lam"], r["cur"]["ov"]) - r["oracle_overlap"]))
                    cov[b], ex[b] = np.mean(ps), np.mean(es)
                ok = cov.mean() >= 1 - EPS - 0.005 if cls == "marginal" else np.mean(cov >= 1 - EPS) >= 1 - DELTA - 0.02
                out.append(f"  [{cls:8s}] {nm:18s} mean coverage {cov.mean():.4f} (se {cov.std() / math.sqrt(REPS):.4f})  "
                           f"P(cov>=0.9) {np.mean(cov >= 0.9):.3f}  {'PASS' if ok else 'FAIL'}  mean excess {ex.mean():+.2f} pp")
                print(out[-1], flush=True)
    txt = "\n".join(out)
    with open(os.path.join(RES, "lowdata_v3", "validity_resample.txt"), "w") as f:
        f.write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()

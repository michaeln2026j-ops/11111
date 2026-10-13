"""E1 validity of the coverage certificate.

(a) Target sweep: eps in {0.05, 0.1, 0.2, 0.3}; for each field and each eps,
    T independent calibration draws -> plan -> n_test executions. Reports the
    realised P(no miss) against 1 - eps (reliability), for CE-U, CE-A and the
    parametric Gaussian-on-score baseline.
(b) Calibration-size sweep: n_cal in {20, 50, 100, 200} at eps = 0.1.
Outputs: results/validity_<kind>.csv, results/ncal_<kind>.csv
"""
import argparse
import os

import numpy as np
import pandas as pd

import core
import exp_lib as L

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def one(F, sig, eps, n_cal, n_test, rng, lam0):
    infield = lambda n: [(F, np.arange(n))]
    q, hist, scores = L.calibrate_conformal(infield, sig, eps, 3.0, rng, lam0=lam0, n_cal=n_cal)
    out = {}
    for name, lv in [("CE", q), ("Gaussian on score", L.gaussian_score_lambda(scores, eps))]:
        try:
            ys = core.plan(F, 3.0, lv, sig)
            out[name] = L.evaluate_plan(F, ys, n_test, rng)
        except ValueError:
            out[name] = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="paddy")
    ap.add_argument("--fields", type=int, default=15)
    ap.add_argument("--trials", type=int, default=4)
    ap.add_argument("--n-test", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    fields = core.load_fields(args.kind, seed=0)
    train, evalf = fields[:20], fields[20:20 + args.fields]
    evalf = evalf[args.shard::args.nshards]
    SHARD = "" if args.nshards == 1 else f"_shard{args.shard}of{args.nshards}"
    sigA, *_ = L.SigmaModel.fit(train, rng)
    sigU = L.ConstSigma(1.0)
    rows, rows_n = [], []
    for fi, F in enumerate(evalf):
        for variant, sig, lam0 in [("U", sigU, 0.03), ("A", sigA, 1.0)]:
            for eps in (0.05, 0.1, 0.2, 0.3):
                for t in range(args.trials):
                    res = one(F, sig, eps, 100, args.n_test, rng, lam0)
                    for name, r in res.items():
                        if r is None:
                            continue
                        rows.append(dict(field=F.fid, variant=variant, method=name, eps=eps, trial=t,
                                         **r))
            if variant == "A":
                for n_cal in (20, 50, 100, 200):
                    for t in range(args.trials):
                        res = one(F, sig, 0.1, n_cal, args.n_test, rng, lam0)
                        r = res["CE"]
                        if r is not None:
                            rows_n.append(dict(field=F.fid, n_cal=n_cal, trial=t, **r))
        print(f"[{fi+1}/{len(evalf)}] field {F.fid}", flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(RES, f"validity_{args.kind}{SHARD}.csv"), index=False)
        pd.DataFrame(rows_n).to_csv(os.path.join(RES, f"ncal_{args.kind}{SHARD}.csv"), index=False)


if __name__ == "__main__":
    main()

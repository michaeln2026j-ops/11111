"""Diagnostic: is the implemented calibration a valid split-conformal certificate?

For each field and repetition: calibrate CE-U (exp_lib.calibrate_conformal), then draw FRESH test runs
at the frozen reference plan and record the score-level coverage P(S_test <= q) (the quantity that
Theorem 1 bounds: 1 - eps <= P <= 1 - eps + 1/(n+1)) and the no-miss coverage of the deployed plan
pi(q). Compares the v5 two-stage protocol (fresh certificate batch) with the one-stage protocol that
stops on the batch that triggered the stop (selection bias).
Outputs: results/diag_validity.csv
"""
import argparse
import os

import numpy as np
import pandas as pd

import core
import exp_lib as L

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="paddy")
    ap.add_argument("--fields", type=int, default=6)
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--n-cal", type=int, default=100)
    ap.add_argument("--n-test", type=int, default=400)
    ap.add_argument("--eps", type=float, default=0.1)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    args = ap.parse_args()
    w = 3.0
    const = L.ConstSigma(1.0)
    fields = core.load_fields(args.kind, w=w, seed=0)[20:20 + args.fields][args.shard::args.nshards]
    SHARD = "" if args.nshards == 1 else f"_shard{args.shard}of{args.nshards}"
    rows = []
    for F in fields:
        for rep in range(args.reps):
            for protocol, final in (("two-stage (v5)", True), ("one-stage (stop batch)", False)):
                rng = np.random.default_rng(10007 * F.fid + rep)  # same calibration stream for both protocols
                q, hist, _ = L.calibrate_conformal(lambda n: [(F, np.arange(n))], const, args.eps, w, rng,
                                                   lam0=0.03, n_cal=args.n_cal, final=final)
                lam_ref = hist[-1][0]
                trng = np.random.default_rng(99991 * F.fid + rep)  # common test runs
                ys = core.plan(F, w, lam_ref, const)
                X, D, _ = L.run(F, ys, args.n_test, trng, w=w)
                S = core.exact_scores(F, ys, X, D, w, lam_ref)
                ys_q = core.plan(F, w, q, const)
                X, D, _ = L.run(F, ys_q, args.n_test, trng, w=w)
                miss = core.evaluate(F, ys_q, X, D, w)
                rows.append(dict(field=F.fid, rep=rep, protocol=protocol, q=q, lam_ref=lam_ref,
                                 dominated=bool(q <= lam_ref + 1e-9), score_cov=float(np.mean(S <= q)),
                                 p_nomiss_lamref=float(np.mean(S <= lam_ref)),  # exact at pi(lam_ref)
                                 p_nomiss=float(np.mean(miss == 0)), n_cal=args.n_cal))
        print("field", F.fid, "done", flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(RES, f"diag_validity{SHARD}.csv"), index=False)


if __name__ == "__main__":
    main()

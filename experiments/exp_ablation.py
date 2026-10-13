"""E9 ablations of the three design choices (in-field calibration, eps = 0.1).

  full          : pass-to-pass score + fixed-point (decision-dependent) calibration
  naive-calib   : same score, but calibrated once on the NOMINAL plan (lam_ref = 0)
                  and applied to the eroded plan (ignores decision dependence, Thm 2)
  abs-score     : fixed-point calibration but with the absolute-error score
                  max_k,x |e_k(x)| (ignores that only relative pass-to-pass error
                  creates gaps, Lemma 1); erosion lam = q
  pointwise     : pass-to-pass difference but pointwise quantile (no sup)
Outputs: results/ablation.csv
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
    ap.add_argument("--fields", type=int, default=30)
    ap.add_argument("--n-cal", type=int, default=100)
    ap.add_argument("--n-test", type=int, default=300)
    ap.add_argument("--eps", type=float, default=0.1)
    ap.add_argument("--w", type=float, default=3.0)
    ap.add_argument("--rtk-scale", type=float, default=1.0)
    ap.add_argument("--kinds", default="paddy,wheat")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    rng = np.random.default_rng(9)
    const = L.ConstSigma(1.0)
    rows = []
    w, ck = args.w, dict(rtk_scale=args.rtk_scale)
    for kind in args.kinds.split(","):
        fields = core.load_fields(kind, w=w, seed=0)[20:20 + args.fields]
        for fi, F in enumerate(fields):
            infield = lambda n, F=F: [(F, np.arange(n))]
            q_full, hist, _ = L.calibrate_conformal(infield, const, args.eps, w, rng, lam0=0.03, n_cal=args.n_cal, **ck)
            # naive: calibrate on nominal plan only
            ys0 = core.plan(F, w, 0.0, const)
            X, D, _ = L.run(F, ys0, args.n_cal, rng, w=w, **ck)
            S0, *_ = core.pair_scores(F, ys0, X, D, np.ones(len(ys0)))
            q_naive = core.conformal_quantile(S0, args.eps)
            # absolute-error score on the final reference plan
            ysr = core.plan(F, w, hist[-1][0], const)
            X, D, _ = L.run(F, ysr, args.n_cal, rng, w=w, **ck)
            _, off = L.offsets(F, ysr, X, D)
            absmax = np.nanmax(np.abs(off), axis=(0, 2))
            q_abs = core.conformal_quantile(absmax, args.eps)
            diffs = L.pair_diffs(F, ysr, X, D)
            q_pw = L.pointwise_conformal_lambda(diffs, args.eps)
            for name, lv in [("full (ours)", q_full), ("naive calibration (no fixed point)", q_naive),
                             ("absolute-error score", q_abs), ("pointwise quantile (no sup)", q_pw)]:
                try:
                    ys = core.plan(F, w, lv, const)
                    r = L.evaluate_plan(F, ys, args.n_test, rng, w=w, **ck)
                except ValueError:
                    r = dict(p_nomiss=np.nan, e_miss=np.nan, passes=np.nan, overlap=np.nan)
                rows.append(dict(kind=kind, field=F.fid, variant=name, lam=lv, w=w, rtk_scale=args.rtk_scale, **r))
            print(f"{kind} [{fi+1}/{len(fields)}]", flush=True)
            pd.DataFrame(rows).to_csv(os.path.join(RES, f"ablation{args.tag}.csv"), index=False)


if __name__ == "__main__":
    main()

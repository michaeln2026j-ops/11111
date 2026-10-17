"""E3b cross-field certificates vs learning-based and robust baselines.

Each calibration field contributes ONE past operation. The calibration pool is
split into a fitting half (for learned models) and a conformal half.
Methods (all use the same run-level score at the same reference plan):
  QR (GBM)        : gradient-boosted quantile regression of the score on field
                    features (mean slope, log area, #passes); uncalibrated
  CQR             : conformalised quantile regression (Romano et al., 2019)
  Gaussian, Scenario, CVaR, DRO-CVaR, Worst-case : pooled scores
  CE-U (ours)     : split conformal on the pooled run-level score
Outputs: results/cross2.csv
"""
import argparse
import math
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

import core
import exp_lib as L

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def feats(F, ys):
    return [F.z_mean_slope, math.log(F.M.area), len(ys)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eps", type=float, default=0.1)
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--n-test-runs", type=int, default=40)
    ap.add_argument("--kind", default="paddy")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    args = ap.parse_args()
    rng = np.random.default_rng(21)
    const = L.ConstSigma(1.0)
    pool = core.load_fields(args.kind, seed=0)[20:]
    rows = []
    SHARD = "" if args.nshards == 1 else f"_shard{args.shard}of{args.nshards}"
    for rep in range(args.repeats)[args.shard::args.nshards]:
        rp = np.random.default_rng(500 + rep)
        idx = rp.permutation(len(pool))
        half = len(idx) // 2
        cal = [pool[i] for i in idx[:half]]
        test = [pool[i] for i in idx[half:]][:30]
        def pool_scores(lam_ref):
            S, Xf = [], []
            for F in cal:
                ys = core.plan(F, 3.0, lam_ref, const)
                X, D, _ = L.run(F, ys, 1, rng)
                S.append(float(core.exact_scores(F, ys, X, D, 3.0, lam_ref)[0]))  # exact: no miss <=> S <= lam_ref
                Xf.append(feats(F, ys))
            return np.array(S), np.array(Xf)

        # per-repeat fixed point for the reference plan (Theorem 2), then a FRESH certificate batch
        lam_ref = 0.10
        for _ in range(5):
            S, Xf = pool_scores(lam_ref)
            q0 = core.conformal_quantile(S, args.eps)
            if q0 <= lam_ref + 1e-9 and lam_ref <= L.MARGIN * q0 * 1.02 + 1e-9:
                break
            lam_ref = q0 * L.MARGIN
        S, Xf = pool_scores(lam_ref)
        fit, con = np.arange(0, len(S), 2), np.arange(1, len(S), 2)
        gbm = GradientBoostingRegressor(loss="quantile", alpha=1 - args.eps, n_estimators=200, max_depth=2,
                                        learning_rate=0.05, subsample=0.8, random_state=rep)
        gbm.fit(Xf[fit], S[fit])
        resid = S[con] - gbm.predict(Xf[con])
        q_res = core.conformal_quantile(resid, args.eps)
        pooled = {
            "Gaussian on score": L.gaussian_score_lambda(S, args.eps),
            "Scenario (Campi-Garatti)": L.scenario_lambda(S, args.eps),
            "CVaR (empirical)": L.cvar_lambda(S, args.eps),
            "Wasserstein DRO-CVaR": L.dro_cvar_lambda(S, args.eps),
            "Worst-case (max score)": float(S.max()),
            "CE-U (ours, uniform)": float(core.conformal_quantile(S, args.eps)),
        }
        qce = pooled["CE-U (ours, uniform)"]
        pooled["CE-U (ours, pi(lam_ref))"] = lam_ref if qce <= lam_ref + 1e-9 else qce  # assumption-free
        for F in test:
            ys_ref = core.plan(F, 3.0, lam_ref, const)
            xq = np.array([feats(F, ys_ref)])
            lam = dict(pooled)
            lam["QR (GBM, uncalibrated)"] = float(gbm.predict(xq)[0])
            lam["CQR (Romano 2019)"] = float(gbm.predict(xq)[0] + q_res)
            for m, lv in lam.items():
                try:
                    ys = core.plan(F, 3.0, lv, const)
                    r = L.evaluate_plan(F, ys, args.n_test_runs, np.random.default_rng([rep, F.fid, 1]))  # CRN
                except ValueError:
                    r = dict(p_nomiss=np.nan, e_miss=np.nan, passes=np.nan, overlap=np.nan)
                rows.append(dict(rep=rep, kind=args.kind, field=F.fid, method=m, lam=lv, n_cal=len(cal),
                                 lam_ref=lam_ref, dominated=bool(lv <= lam_ref + 1e-9), area_ha=F.M.area / 1e4, **r))
        print(f"repeat {rep+1}/{args.repeats}", flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(RES, f"cross2_{args.kind}{SHARD}.csv"), index=False)


if __name__ == "__main__":
    main()

"""E2 main comparison (in-field calibration) on real paddy (hilly) and wheat
(plain) fields. For each evaluation field, n_cal past operations on the same
field are used for calibration; every method's plan is then executed n_test
times under fresh conditions.

Usage: python3 experiments/exp_main.py --kind paddy --fields 30
Outputs: results/main_<kind>.csv
"""
import argparse
import os
import time

import numpy as np
import pandas as pd

import core
import exp_lib as L

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="paddy")
    ap.add_argument("--fields", type=int, default=30)
    ap.add_argument("--n-cal", type=int, default=100)
    ap.add_argument("--n-test", type=int, default=300)
    ap.add_argument("--eps", type=float, default=0.1)
    ap.add_argument("--alpha", type=float, default=0.003)
    ap.add_argument("--n-cal-risk", type=int, default=500)
    ap.add_argument("--ctrl", default="lqr_i")
    ap.add_argument("--w", type=float, default=3.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    w = args.w
    fields = core.load_fields(args.kind, w=w, seed=args.seed)
    train, evalf = fields[:20], fields[20:20 + args.fields]
    sig, feats, dev = L.SigmaModel.fit(train, rng, w=w, ctrl=args.ctrl)
    print(f"{args.kind}: {len(fields)} fields, sigma-hat a={sig.a*100:.2f} cm b={sig.b:.3f} m/(tan slope)")
    const = L.ConstSigma(1.0)
    rows = []
    for fi, F in enumerate(evalf):
        t0 = time.time()
        infield = lambda n, F=F: [(F, np.arange(n))]
        # ---- conformal erosion, uniform and adaptive (fixed-point calibration)
        qU, histU, scoresU = L.calibrate_conformal(infield, const, args.eps, w, rng, lam0=0.03,
                                                   n_cal=args.n_cal, ctrl=args.ctrl)
        qA, histA, scoresA = L.calibrate_conformal(infield, sig, args.eps, w, rng, lam0=1.0,
                                                   n_cal=args.n_cal, ctrl=args.ctrl)
        # ---- baselines sharing the uniform calibration runs
        ys_ref = core.plan(F, w, histU[-1][0], const)
        X, D, _ = L.run(F, ys_ref, args.n_cal, rng, ctrl=args.ctrl, w=w)
        diffs = L.pair_diffs(F, ys_ref, X, D)
        lam = {
            "Nominal (no margin)": (0.0, const),
            "Fixed overlap 5 cm": (0.025, const),
            "Fixed overlap 10 cm": (0.05, const),
            "Gaussian pointwise": (L.gaussian_pointwise_lambda(diffs, args.eps), const),
            "Gaussian on score": (L.gaussian_score_lambda(scoresU, args.eps), const),
            "Empirical pointwise quantile": (L.empirical_pointwise_lambda(diffs, args.eps), const),
            "Cantelli bound on score": (L.cantelli_score_lambda(scoresU, args.eps), const),
            "Worst-case (max score)": (float(np.max(scoresU)), const),
            "CE-U (ours, uniform)": (qU, const),
            "CE-A (ours, terrain-adaptive)": (qA, sig),
        }
        # ---- risk control (Theorem 4), adaptive
        recs = L.surrogate_risk(infield, sig, w, rng, histA[-1][0], args.n_cal_risk, ctrl=args.ctrl)
        lamR = L.risk_lambda(recs, w, args.alpha, np.linspace(0, 6, 121))
        lam["CE-R (ours, risk alpha)"] = (lamR, sig)
        for name, (lv, sf) in lam.items():
            try:
                ys = core.plan(F, w, lv, sf)
                r = L.evaluate_plan(F, ys, args.n_test, rng, w=w, ctrl=args.ctrl)
            except ValueError:  # erosion exceeds the implement: method infeasible here
                r = dict(p_nomiss=np.nan, e_miss=np.nan, p95_miss=np.nan, passes=np.nan,
                         overlap=np.nan, infeasible=True)
            r.update(method=name, field=F.fid, kind=args.kind, slope=F.z_mean_slope,
                     area_ha=F.M.area / 1e4, lam=lv, fp_iters=len(histU) if "CE-U" in name else
                     (len(histA) if "CE-A" in name else 0))
            rows.append(r)
        print(f"[{fi+1}/{len(evalf)}] field {F.fid} slope {F.z_mean_slope:.2f} deg, "
              f"qU={qU*100:.1f} cm, qA={qA:.2f}, lamR={lamR:.2f}, {time.time()-t0:.1f}s", flush=True)
        os.makedirs(RES, exist_ok=True)
        pd.DataFrame(rows).to_csv(os.path.join(RES, f"main_{args.kind}{args.tag}.csv"), index=False)


if __name__ == "__main__":
    main()

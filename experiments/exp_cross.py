"""E3 cross-field certificates and distribution shift.

Calibration uses ONE past operation on each of many other fields (exchangeable
at the field level); the certificate is then applied to unseen fields.
Settings:
  in-region : calibrate on paddy fields, test on held-out paddy fields
  shift     : calibrate on wheat (North China Plain, flat), test on paddy
              (hilly south), comparing
                CE-U  (uniform, unweighted)
                CE-A  (terrain-normalised score)
                CE-AW (terrain-normalised + covariate-shift weights on the
                       field slope feature, Tibshirani et al. 2019)
Weights use a Gaussian-KDE density ratio of the mean field slope (known from
the DEM before operating) between test and calibration populations.
Outputs: results/cross.csv
"""
import argparse
import math
import os

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

import core
import exp_lib as L

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


FEATURE = lambda F: F.z_mean_slope  # covariate used by the weighted variant


def field_scores(fields, sig, lam, rng, runs_per_field=1):
    S, feat = [], []
    for F in fields:
        try:
            ys = core.plan(F, 3.0, lam, sig)
        except ValueError:
            continue
        X, D, _ = L.run(F, ys, runs_per_field, rng)
        s, *_ = core.pair_scores(F, ys, X, D, sig.vec(F, ys))
        S.append(s)
        feat.append(np.full(runs_per_field, FEATURE(F)))
    return np.concatenate(S), np.concatenate(feat)


def certify(cal_fields, sig, eps, rng, lam0, iters=3):
    """Fixed-point calibration; returns q and the final reference scores/features."""
    lam = lam0
    for _ in range(iters):
        S, f = field_scores(cal_fields, sig, lam, rng)
        q = core.conformal_quantile(S, eps)
        if q <= lam + 1e-9:
            break
        lam = q * 1.05
    return q, S, f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eps", type=float, default=0.1)
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--n-test-runs", type=int, default=50)
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--reverse", action="store_true",
                    help="harmful shift: calibrate on small hilly paddy fields, test on large wheat fields; "
                         "weights on log main-area (known before operating)")
    args = ap.parse_args()
    global FEATURE
    if args.reverse:
        FEATURE = lambda F: math.log(F.M.area)
    rng = np.random.default_rng(args.seed)
    paddy = core.load_fields("paddy", seed=0)
    wheat = core.load_fields("wheat", seed=0)
    sigA, *_ = L.SigmaModel.fit(paddy[:10] + wheat[:10], rng)
    sigU = L.ConstSigma(1.0)
    pool_p, pool_w = paddy[20:], wheat[20:]
    rows = []
    SHARD = "" if args.nshards == 1 else f"_shard{args.shard}of{args.nshards}"
    for rep in range(args.repeats)[args.shard::args.nshards]:
        rp = np.random.default_rng(1000 + rep)
        idx = rp.permutation(len(pool_p))
        cal_p = [pool_p[i] for i in idx[: len(idx) // 2]]
        test_p = [pool_p[i] for i in idx[len(idx) // 2:]][:30]
        cal_w = [pool_w[i] for i in rp.permutation(len(pool_w))[: len(cal_p)]]
        if args.reverse:  # calibrate on paddy, test on unseen wheat fields
            test_w = [pool_w[i] for i in rp.permutation(len(pool_w))[:30]]
            cal_w, test_p = cal_p, test_w
        sl_cal = np.array([FEATURE(F) for F in cal_w])
        sl_tst = np.array([FEATURE(F) for F in test_p])
        kc, kt = gaussian_kde(sl_cal), gaussian_kde(sl_tst)
        wfun = lambda f: np.clip(kt(f) / np.maximum(kc(f), 1e-12), 0, 50)
        tag = "shift paddy->wheat" if args.reverse else "shift wheat->paddy"
        settings = {
            (tag, "CE-U"): (cal_w, sigU, 0.03, None),
            (tag, "CE-A"): (cal_w, sigA, 1.0, None),
            (tag, "CE-AW (weighted)"): (cal_w, sigA, 1.0, wfun),
        }
        if not args.reverse:
            settings[("in-region", "CE-U")] = (cal_p, sigU, 0.03, None)
            settings[("in-region", "CE-A")] = (cal_p, sigA, 1.0, None)
        cache = {}
        for (setting, method), (cal, sig, lam0, wt) in settings.items():
            key = (id(cal), id(sig))
            if key not in cache:
                cache[key] = certify(cal, sig, args.eps, rng, lam0)
            q0, S, f = cache[key]
            for F in test_p:
                q = q0
                if wt is not None:  # test-point-specific weighted quantile
                    wv = wt(f)
                    q = core.conformal_quantile(S, args.eps, weights=wv,
                                                w_test=float(wt(np.array([FEATURE(F)]))[0]))
                try:
                    ys = core.plan(F, 3.0, q, sig)
                    r = L.evaluate_plan(F, ys, args.n_test_runs, rng)
                except ValueError:
                    continue
                rows.append(dict(rep=rep, setting=setting, method=method, q=q, field=F.fid,
                                 n_cal=len(cal), slope=F.z_mean_slope, **r))
        print(f"repeat {rep+1}/{args.repeats} done", flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(RES, f"cross_reverse{SHARD}.csv" if args.reverse else f"cross{SHARD}.csv"),
                                  index=False)


if __name__ == "__main__":
    main()

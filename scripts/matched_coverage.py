"""Matched-coverage comparison of the E-low v2 pivots (secondary analysis, post hoc).

Methods that deploy different erosions also reach different realised coverage, so their overlap is not
directly comparable. Here every pivot family (raw, scale law, theory ratio, theory PIT, learned features,
oracle-ideal) is rescaled by one common factor c chosen so that the pooled realised P(no miss) over the
test fields equals 0.9 exactly; the excess overlap at that matched coverage then compares the pivots by how
well they ORDER and SCALE the fields, free of the realised-coverage noise of one calibration draw.

Step 1 (simulation, cached): for every v2 test field, P(no miss) of the plan pi(lam) on a lambda grid around
the oracle, 200 runs each with common random numbers (the same conditions and seeds as phase B).
Step 2: monotone interpolation of P_g(lam) and of the overlap; bisection on c.
Step 3: validity and efficiency over 400 independent calibration draws per (eps, n_cal, pivot): the coverage
of one draw is the mean P(no miss) over all non-calibration fields (a new field from the population), so the
spread over draws is exactly the Beta(k, n+1-k) conditional-coverage spread; PAC requires >= 1-eps in at
least 90% of draws. The CQR-style baseline (Romano et al. 2019) uses a field-feature model of the score
trained on one run per field of the disjoint v1 pool.

    python3 scripts/matched_coverage.py --jobs 4
"""
import argparse
import glob
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
import exp_lib as L  # noqa: E402
import exp_lowdata as X  # noqa: E402
import exp_system as E  # noqa: E402

RES = os.path.join(HERE, "..", "results", "lowdata_v2")
GRID = np.geomspace(0.7, 2.6, 20)  # multiples of the field oracle lambda (covers the PAC range in R3)


def curve(args):
    key, fi = args
    cache = os.path.join(RES, f"curve_{key}_{fi}.pkl")
    if os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    rname, reg = X.regime(key)
    w = reg["w"]
    F = core.load_fields(reg["kind"], w=w, seed=0)[fi]
    r = pickle.load(open(os.path.join(RES, f"A_{key}_{fi}.pkl"), "rb"))
    S_l = E.sim_core(F, lambda: "lqr_i", reg)
    seed_t = E._seed(rname, "lowdata-test", F.fid)
    lams, P, OV = [], [], []
    for m in GRID:
        lam = float(m * r["oracle_lam"])
        try:
            ys = core.plan(F, w, lam, E.UNIT)
        except ValueError:
            continue
        ev = E.evaluate(F, w, ys, S_l, X.N_TEST, seed_t, reg)
        lams.append(lam), P.append(ev["p_nomiss"]), OV.append(ev["overlap"])
    out = dict(key=key, fi=fi, lam=np.array(lams), P=np.maximum.accumulate(np.array(P)), ov=np.array(OV),
               oracle_overlap=r["oracle_overlap"])
    pickle.dump(out, open(cache, "wb"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    from feature_pivot import features, load  # noqa: E402
    lines = []
    for key in ("R1", "R2", "R3"):
        rname, reg = X.regime(key)
        fields = core.load_fields(reg["kind"], w=reg["w"], seed=0)
        te = load(key, RES)
        with ProcessPoolExecutor(a.jobs) as ex:
            cur = list(ex.map(curve, [(key, r["fi"]) for r in te]))
        # pivots (as in feature_pivot.py)
        tr = load(key, os.path.join(HERE, "..", "results", "lowdata"))
        Xtr = np.array([features(fields[r["fi"]], r) for r in tr])
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-12
        A = np.c_[np.ones(len(tr)), (Xtr - mu) / sd]
        beta = np.linalg.solve(A.T @ A + np.diag([0] + [1] * (A.shape[1] - 1)), A.T @ np.log([r["oracle_lam"] for r in tr]))
        Xte = np.array([features(fields[r["fi"]], r) for r in te])
        # CQR-style frontier baseline (Romano et al. 2019): feature model of the score trained on what the
        # low-data setting provides (one run per field of the disjoint v1 pool), conformalised across fields
        beta1 = np.linalg.solve(A.T @ A + np.diag([0] + [1] * (A.shape[1] - 1)),
                                A.T @ np.log([max(r["S_hist"], 1e-3) for r in tr]))
        piv = {"raw (no pivot)": np.ones(len(te)),
               "CQR, field features (one-run trained)": np.exp(np.c_[np.ones(len(te)), (Xte - mu) / sd] @ beta1),
               "scale law": np.array([math.sqrt(2 * math.log(max(r["N_len"], 2))) for r in te]),
               "learned features (oracle-trained)": np.exp(np.c_[np.ones(len(te)), (Xte - mu) / sd] @ beta),
               "theory ratio (CE-EVT-R)": np.array([X.inv_cdf(r["tgrid"], r["Fhat"], 0.9) for r in te]),
               "oracle (ideal)": np.array([r["oracle_lam"] for r in te])}
        S = np.array([r["S_hist"] for r in te])
        n = len(te)
        lines.append(f"\n{key}: {n} fields; pooled coverage matched to 0.900 by a common factor c")
        for nm, q in piv.items():
            for tag, dl in (("marginal", None), ("PAC", 0.1)):
                lam0 = np.array([q[g] * CP.quantile(np.delete(S / q, g), 0.1, dl) for g in range(n)])

                def pooled(c):
                    return np.mean([np.interp(c * lam0[g], cur[g]["lam"], cur[g]["P"]) for g in range(n)])
                lo, hi = 0.3, 3.0
                for _ in range(60):
                    mid = 0.5 * (lo + hi)
                    lo, hi = (mid, hi) if pooled(mid) < 0.9 else (lo, mid)
                c = hi
                ex = np.mean([100 * (np.interp(c * lam0[g], cur[g]["lam"], cur[g]["ov"]) - cur[g]["oracle_overlap"])
                              for g in range(n)])
                lines.append(f"   [{tag:8s}] {nm:34s} c {c:.3f}  excess at matched coverage {ex:+.2f} pp")
        # validity and efficiency over many independent calibration draws, for several eps and n_cal
        rng = np.random.default_rng(0)
        lines.append(f"   repeated calibration draws (400 per cell): mean coverage | P(coverage >= 1-eps) | mean excess pp")
        for eps in (0.05, 0.1, 0.2):
            for n_cal in (10, 20, 25):
                for nm in ("raw (no pivot)", "CQR, field features (one-run trained)", "scale law", "theory ratio (CE-EVT-R)"):
                    q = piv[nm]
                    for tag, dl in (("marg", None), ("PAC", 0.1)):
                        cov, ok, exs = [], [], []
                        for _ in range(400):
                            # one calibration draw; the guarantee is about a NEW field: average over all others
                            cal = rng.choice(n, size=n_cal, replace=False)
                            tgt = np.setdiff1d(np.arange(n), cal)
                            t = CP.quantile(S[cal] / q[cal], eps, dl)
                            if not np.isfinite(t):
                                cov.append(np.nan)
                                continue
                            pc = np.mean([np.interp(q[g] * t, cur[g]["lam"], cur[g]["P"]) for g in tgt])
                            cov.append(pc), ok.append(pc >= 1 - eps)
                            exs.append(np.mean([100 * (np.interp(q[g] * t, cur[g]["lam"], cur[g]["ov"])
                                                       - cur[g]["oracle_overlap"]) for g in tgt]))
                        if np.all(np.isnan(cov)):
                            lines.append(f"   eps {eps:.2f} n_cal {n_cal:2d} [{tag:4s}] {nm:38s} n/a (too few fields)")
                            continue
                        lines.append(f"   eps {eps:.2f} n_cal {n_cal:2d} [{tag:4s}] {nm:38s} {np.nanmean(cov):.3f} | "
                                     f"{np.mean(ok):.2f} | {np.mean(exs):+.2f}")
    txt = "\n".join(lines)
    print(txt)
    # the registered v2 reading (results/lowdata_v2/matched_coverage.txt) was made before scripts/extend_curves.py
    # added points below 0.7 lam* to the cached curves; re-running now reads the extended curves, so write elsewhere
    out_f = a.out or os.path.join(RES, "matched_coverage.txt")
    with open(out_f, "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()

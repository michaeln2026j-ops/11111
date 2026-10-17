"""Numerical check of Theorem 5 / Proposition 5.4 (docs/theory_transfer.md), a few minutes on a laptop.

For one field per regime, the deployed erosion lam1 is fixed and the reference erosion lam0 >= lam1 is
varied. With n runs per plan it reports:
  F0      = P(U_{pi0} <= lam1)            (reference coverage at the deployed threshold)
  F1      = P(no miss at pi(lam1))        (actual deployed coverage)
  theta   = (1 - F0) / E[N_t]             (finite-level extremal index, Lemma 5.3)
  H       = tail hazard of the pair scores just below t (Lemma 5.2)
  h       = max over index-matched pairs of the shift of their upper quantiles between the two plans
  bound   = (1 - F0) * (1 + (exp(hH) - 1) / theta)    (Theorem 5; must be >= 1 - F1)
  overcov = (a / |J0|) * (1 - F0) / theta             (Proposition 5.4; bounds F1 - F0 when h = 0)

    python3 scripts/check_transfer.py               # R1, R2, R3, 2000 runs per plan
    python3 scripts/check_transfer.py --regimes R1 --n 4000
"""
import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "experiments"))
import core  # noqa: E402
import exp_system as E  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--regimes", default="R1,R2,R3")
ap.add_argument("--n", type=int, default=2000)
ap.add_argument("--field", type=int, default=50, help="index of the (fresh) field")
args = ap.parse_args()


def pair_matrix(F, ys, X, D, w, lam):
    """Exact pair decomposition (core.exact_pair_scores): (R, K + 1), max over columns = exact score."""
    return core.exact_pair_scores(F, ys, X, D, w, lam)


def run(F, w, reg, lam, n, seed):
    ys = core.plan(F, w, lam, E.UNIT)
    rng = np.random.default_rng(seed)
    cond = E.make_cond(rng, n, reg)
    X, D = core.simulate(F, ys, cond, rng)
    S = core.exact_scores(F, ys, X, D, w, lam)       # U_pi (needed erosion), exact
    miss = core.evaluate(F, ys, X, D, w)
    T = pair_matrix(F, ys, X, D, w, lam)
    return ys, S, miss, T


for key in args.regimes.split(","):
    rname = [k for k in E.REGIMES if k.startswith(key)][0]
    reg = E.REGIMES[rname]
    w = reg["w"]
    F = core.load_fields(reg["kind"], w=w, seed=0)[args.field]
    t0 = time.time()
    # deployed erosion: the 0.9 quantile of the needed erosion at a plan near it (one fixed-point step)
    lam_guess = {"R1": 0.11, "R2": 0.15, "R3": 0.40}[key]
    _, S_g, _, _ = run(F, w, reg, lam_guess, 600, 7)
    lam1 = float(np.quantile(S_g, 0.9))
    ys1, _, miss1, T1 = run(F, w, reg, lam1, args.n, 11)
    F1 = float(np.mean(miss1 == 0))
    print(f"\n=== {rname}, field {F.fid} (K1 = {len(ys1)} passes), deployed lam1 = {lam1:.3f} m, "
          f"actual deployed coverage F1 = {F1:.4f}  (n = {args.n})")
    print("   lam0    K0   a   F0      1-F1    theta   H[1/m]  h[m]    Thm5 bound(>=1-F1)  F1-F0   Prop5.4 bound")
    for infl in (1.0, 1.1, 1.25, 1.5):
        lam0 = lam1 * infl
        ys0, S0, _, T0 = run(F, w, reg, lam0, args.n, 13)
        t = lam1
        U0 = T0.max(axis=1)  # U_pi = max over pairs (the theorem's statistic; >= the exact score)
        F0 = float(np.mean(U0 <= t + 1e-12))
        N = (T0 > t + 1e-12).sum(axis=1)
        EN = N.mean()
        theta = (1 - F0) / EN if EN > 0 else 1.0
        # hazard of pooled pair scores on [t - 2 cm, t]
        pooled = T0.ravel()
        dt = 0.02 if w < 5 else 0.05
        s_hi, s_lo = np.mean(pooled > t), np.mean(pooled > t - dt)
        H = np.log(s_lo / s_hi) / dt if s_hi > 0 else np.nan
        # h: largest shift of the pooled interior pair-score tail quantiles between the two plans (empirical
        # proxy for the plan-induced perturbation L*delta; pooled over pairs to suppress sampling noise)
        q = (0.95, 0.99, 0.995)
        i0 = T0[:, 1:-1].ravel()
        i1 = T1[:, 1:-1].ravel()
        i0, i1 = i0[np.isfinite(i0)], i1[np.isfinite(i1)]
        h = float(np.max(np.abs(np.quantile(i0, q) - np.quantile(i1, q))))
        bound = (1 - F0) * (1 + (np.exp(h * H) - 1) / theta)
        a = len(ys0) - len(ys1)
        p54 = a / (len(ys0) + 1) * (1 - F0) / theta
        ok = "OK " if bound >= (1 - F1) - 2 * np.sqrt(F1 * (1 - F1) / args.n) else "VIOL"
        print(f"   {lam0:.3f}  {len(ys0):3d}  {a:2d}  {F0:.4f}  {1 - F1:.4f}  {theta:.3f}  {H:6.1f}  {h:.4f}  "
              f"{bound:.4f} {ok}          {F1 - F0:+.4f}  {p54:.4f}", flush=True)
    print(f"   ({time.time() - t0:.0f}s)")

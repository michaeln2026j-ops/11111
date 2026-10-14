"""CE+ : budget-matched, self-normalised conformal erosion (v7).

Three changes relative to the two-stage CE of v6 (exp_system.certify):

1. Budget. CE+ uses exactly n_cal calibration runs on the field, the same budget as the conformal,
   model-based and learning baselines (v6 CE spent 2-5 pilot batches of n_cal runs before its
   certificate batch). The reference plan is fixed in advance from the TRAINING fields only:
   lam0 = REF_INFLATE x the largest training-field (1 - eps) score quantile, so that pi(lam0) has at
   least as many passes as the deployed plans (Theorem 2's dominating reference).

2. Deployment at the conformal quantile (Theorem 2), without the 1.10 pilot margin.

3. Self-normalisation by an observable of the run. Before the infield passes the machine drives a
   headland (probe) line; the autosteer reports its measured cross-track error (XTE). Its RMS z is a
   noisy reading of how rough / slippery the operation is. The score is normalised,
       T = S / sigma(z),   sigma(z) = max(a + b z, SIG_FLOOR),
   with (a, b) fitted on the TRAINING fields only (never on calibration or test runs), and the plan of
   a new operation uses lam = t * sigma(z_new), where t is the conformal quantile of the calibration T.
   (S_i, z_i) are exchangeable across runs, so P(S_new <= t sigma(z_new)) >= 1 - eps holds exactly for
   any fixed sigma(.) (split conformal with a normalised score); a smooth day gets less erosion, a rough
   day more. Under GNSS-dominated error (DGPS) the fit gives b ~ 0 and CE+ reduces to CE-q.

v8 additions (docs/theory_v8.md):
4. Training-only choice of the normalisation (Proposition B): adaptive sigma(z) is used only if, in
   leave-one-field-out cross-validation on the TRAINING fields, it lowers the mean erosion needed for
   1 - eps coverage by at least GATE; otherwise sigma is constant.

The PAC variant uses the order statistic that holds P(no miss | calibration) >= 1 - eps with
probability >= 1 - delta over the calibration draw (training-conditional conformal, Vovk 2012).
"""
import copy
import math

import numpy as np
from scipy.stats import binom

import core

REF_INFLATE = 1.25
SIG_FLOOR = 0.3  # sigma(z) floor relative to the training mean of sigma (avoids a vanishing erosion)
LAM_GRID = 0.002  # deployed erosions are rounded UP to 2 mm so test runs can be grouped by plan
GATE = 0.03  # adaptive normalisation must save >= 3% erosion in training-field cross-validation


def order_index(n, eps, delta=None):
    """1-based order statistic of the conformal quantile: marginal (delta None) or PAC."""
    if delta is None:
        return int(math.ceil((n + 1) * (1 - eps)))
    for k in range(1, n + 1):
        if binom.cdf(k - 1, n, 1 - eps) >= 1 - delta:
            return k
    return n + 1


def quantile(scores, eps, delta=None):
    s = np.sort(np.asarray(scores, float))
    k = order_index(len(s), eps, delta)
    return float(s[k - 1]) if k <= len(s) else np.inf


def subset_cond(cond, idx):
    """Condition restricted to runs idx (all per-run arrays sliced, scalars kept)."""
    c = copy.copy(cond)
    n = len(cond.k_s)
    for k, v in vars(cond).items():
        if isinstance(v, np.ndarray) and v.shape[:1] == (n,):
            setattr(c, k, v[idx])
    return c


def probe_xte(F, w, cond, ctrl_factory, seed):
    """Measured XTE RMS of a headland probe line (the field's first nominal line), driven before the
    infield passes under the same per-run condition with independent noise. Returns (R,)."""
    ys = core.plan(F, w, 0.0, lambda f, y: 1.0)[:1]
    st = {}
    core.simulate(F, ys, cond, np.random.default_rng(seed), ctrl=ctrl_factory(), meas_stats=st)
    return st["xte_rms"][:, 0]


class Scale:
    """sigma(z) = max(a + b z, SIG_FLOOR * mean training sigma); constant when adaptive=False."""

    def __init__(self, a=1.0, b=0.0, floor=0.0):
        self.a, self.b, self.floor = a, b, floor

    def __call__(self, z):
        return np.maximum(self.a + self.b * np.asarray(z, float), self.floor)


def fit_training(train_fields, w, reg, make_cond, sim_factory, ctrl_factory, eps, lam_train, n=40, seed=0,
                 adaptive=True, gate=False):
    """Fit sigma(z) and the reference erosion lam0 on the TRAINING fields only.

    sim_factory(F) -> simulate(ys, cond, rng) for the stack's controller on field F (BCD lines; the
    controller, not the line placement, sets the run-to-run roughness response).
    Scores of each training field are divided by that field's median so that sigma captures the
    within-field (run-to-run) dependence on z, not field-size effects.
    Returns (Scale, lam0)."""
    rng = np.random.default_rng(seed)
    zs, ys_, qs = [], [], []
    for i, F in enumerate(train_fields):
        try:
            ys = core.plan(F, w, lam_train, lambda f, y: 1.0)
        except ValueError:
            continue
        cond = make_cond(rng, n, reg)
        z = probe_xte(F, w, cond, ctrl_factory, seed + 101 * i + 1)
        X, D = sim_factory(F)(ys, cond, rng)
        S = core.exact_scores(F, ys, X, D, w, lam_train)
        if not np.isfinite(S).all():
            continue
        qs.append(np.quantile(S, 1 - eps))
        zs.append(z)
        ys_.append(S / np.median(S))
    lam0 = REF_INFLATE * max(qs)
    if not adaptive or not zs:
        return Scale(), lam0
    sc = _fit_scale(zs, ys_)
    if gate:  # Proposition B: leave-one-training-field-out check, training data only
        if len(zs) < 3 or loo_saving(zs, ys_, eps) < GATE:
            sc = Scale()
    return sc, lam0


def _fit_scale(zs, ss):
    z, s = np.concatenate(zs), np.concatenate(ss)
    A = np.c_[np.ones_like(z), z]
    (a, b), *_ = np.linalg.lstsq(A, s, rcond=None)
    b = max(b, 0.0)  # rougher runs never get less erosion
    a = float(np.mean(s - b * z))
    mean_sig = float(np.mean(a + b * z))
    return Scale(a, b, SIG_FLOOR * mean_sig)


def loo_saving(zs, ss, eps):
    """Mean relative erosion saving of the adaptive normalisation over the constant one when each
    training field is held out in turn (scores already divided by the field median)."""
    sav = []
    for i in range(len(zs)):
        sc = _fit_scale([z for j, z in enumerate(zs) if j != i], [x for j, x in enumerate(ss) if j != i])
        sig = sc(zs[i])
        t = np.quantile(ss[i] / sig, 1 - eps)
        sav.append(1.0 - np.mean(t * sig) / np.quantile(ss[i], 1 - eps))
    return float(np.mean(sav))


def calibrate(F, w, reg, make_cond, planner, simulate, ctrl_factory, scale, lam0, eps, n_cal, rng, seed,
              delta=None):
    """One batch of n_cal runs at the fixed reference plan pi(lam0) on the field.
    Returns dict(t, S, z, lam0, dominated) where t is the conformal quantile of S / sigma(z)."""
    ys = planner(lam0)
    if ys is None:
        raise ValueError("infeasible reference plan")
    cond = make_cond(rng, n_cal, reg)
    z = probe_xte(F, w, cond, ctrl_factory, seed + 7)
    X, D = simulate(ys, cond, rng)
    S = core.exact_scores(F, ys, X, D, w, lam0)
    T = S / scale(z)
    t = quantile(T, eps, delta)
    return dict(t=t, S=S, z=z, lam0=lam0, q_const=quantile(S, eps, delta),
                dominated=bool(t * float(np.max(scale(z))) <= lam0 + 1e-9))


def deploy_eval(F, w, reg, make_cond, planner, simulate, ctrl_factory, scale, t, n, seed, overlap_fn,
                path_fn=None):
    """Evaluate the run-adaptive deployment on n fresh test runs (same conditions as the other systems:
    Condition drawn from default_rng(seed) exactly like exp_system.evaluate). Each run gets its own
    erosion lam = t sigma(z) (rounded up to LAM_GRID); runs are grouped by erosion and every group is
    executed with its own plan. Returns the metrics of exp_system.evaluate plus mean erosion."""
    rng = np.random.default_rng(seed)
    cond = make_cond(rng, n, reg)
    z = probe_xte(F, w, cond, ctrl_factory, seed + 11)
    lam = np.ceil(t * scale(z) / LAM_GRID - 1e-9) * LAM_GRID
    miss = np.full(n, np.nan)
    ov = np.zeros(n)
    passes = np.zeros(n)
    plen = np.zeros(n)
    for gi, lv in enumerate(np.unique(lam)):
        idx = np.nonzero(lam == lv)[0]
        ys = planner(float(lv))
        if ys is None:
            raise ValueError("infeasible erosion")
        c = subset_cond(cond, idx)
        X, D = simulate(ys, c, np.random.default_rng(seed + 1 + 7919 * (gi + 1)))
        miss[idx] = core.evaluate(F, ys, X, D, w)
        ov[idx] = overlap_fn(F, ys, w)
        passes[idx] = len(ys)
        if path_fn is not None:
            try:
                plen[idx] = path_fn(F, ys)
            except Exception:
                plen[idx] = np.nan
    return dict(p_nomiss=float(np.mean(miss == 0)), e_miss=float(miss.mean()),
                p95_miss=float(np.percentile(miss, 95)), passes=float(passes.mean()),
                overlap=float(ov.mean()), path_m=float(np.nanmean(plen)) if path_fn else np.nan,
                lam_mean=float(lam.mean()), lam_sd=float(lam.std()))

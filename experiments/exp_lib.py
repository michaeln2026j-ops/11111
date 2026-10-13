"""Shared experiment machinery: sigma-hat model, calibration with fixed-point
reference plans, methods (ours + baselines), and metrics."""
import math

import numpy as np
from scipy.stats import norm

import core

W_DEFAULT = 3.0


# ------------------------------------------------------------------ sigma-hat model
class SigmaModel:
    """sigma_hat(pass) = sqrt(a^2 + (b * |lateral slope|)^2), fitted on training
    fields only (never on calibration or test data)."""

    def __init__(self, a=0.02, b=0.0):
        self.a, self.b = a, b
        self._cache = {}

    def __call__(self, field, y):
        key = (field.fid, round(float(y), 2))
        if key not in self._cache:
            f = core.pass_feature(field, y)
            self._cache[key] = math.sqrt(self.a ** 2 + (self.b * f) ** 2)
        return self._cache[key]

    def vec(self, field, ys):
        return np.array([self(field, y) for y in ys])

    @classmethod
    def fit(cls, fields, rng, w=W_DEFAULT, runs=20, ctrl="lqr_i", **cond_kw):
        feats, dev = [], []
        for F in fields:
            ys = core.plan(F, w, 0.0, lambda f, y: 1.0)
            cond = core.Condition(rng, runs, **cond_kw)
            X, D = core.simulate(F, ys, cond, rng, ctrl=ctrl)
            _, pair, _, _ = core.pair_scores(F, ys, X, D, np.full(len(ys), 0.5))
            fk = np.array([core.pass_feature(F, y) for y in ys])
            for k in range(len(ys) - 1):
                if np.isfinite(pair[:, k]).all():
                    feats.append(0.5 * (fk[k] + fk[k + 1]))
                    dev.append(np.percentile(pair[:, k], 90))  # = max diff / (2*0.5)
        feats, dev = np.array(feats), np.array(dev)
        # least squares on dev^2 = a'^2 + b'^2 f^2 (dev in metres, pair-normalised)
        A = np.c_[np.ones_like(feats), feats ** 2]
        coef, *_ = np.linalg.lstsq(A, dev ** 2, rcond=None)
        a = math.sqrt(max(coef[0], 1e-6)) / 2
        b = math.sqrt(max(coef[1], 0.0)) / 2
        return cls(a, b), feats, dev


class ConstSigma(SigmaModel):
    def __init__(self, value=1.0):
        super().__init__(value, 0.0)

    def __call__(self, field, y):
        return self.a


# ------------------------------------------------------------------------ execution
def run(field, ys, n, rng, ctrl="lqr_i", w=W_DEFAULT, **cond_kw):
    cond = core.Condition(rng, n, **cond_kw)
    X, D = core.simulate(field, ys, cond, rng, ctrl=ctrl)
    return X, D, cond


def overlap_ratio(field, ys, w):
    tot = 0.0
    for y in ys:
        c = field.chord(field.M, y)
        if c:
            tot += w * (c[1] - c[0])
    return tot / field.M.area - 1.0


# ----------------------------------------------------------------------- calibration
def calibrate_conformal(field_runs, sig, eps, w, rng, lam0=1.0, iters=3, n_cal=100, ctrl="lqr_i",
                        weights_fn=None, **cond_kw):
    """Fixed-point (decision-dependent) conformal calibration, Theorems 1-3.

    field_runs: callable(i) -> Field used for calibration run i (in-field: the
    same field; cross-field: a distinct calibration field per run).
    Calibration runs are executed with the reference plan pi(lam_ref); we iterate
    lam_ref <- q until the certified plan needs no more passes than the
    reference plan (score domination, Theorem 2).
    Returns q, lam_ref history.
    """
    lam_ref, hist = lam0, []
    q = np.inf
    for _ in range(iters):
        scores, wts = [], []
        for F, idx in field_runs(n_cal):
            ys = core.plan(F, w, lam_ref, sig)
            X, D, cond = run(F, ys, len(idx), rng, ctrl=ctrl, w=w, **cond_kw)
            S, *_ = core.pair_scores(F, ys, X, D, sig.vec(F, ys))
            scores.append(S)
            if weights_fn is not None:
                wts.append(weights_fn(cond))
        scores = np.concatenate(scores)
        if weights_fn is None:
            q = core.conformal_quantile(scores, eps)
        else:
            wts = np.concatenate(wts)
            q = core.conformal_quantile(scores, eps, weights=wts, w_test=wts.max())
        hist.append((lam_ref, q))
        if q <= lam_ref + 1e-9:
            break
        lam_ref = q * 1.05
    return q, hist, scores


def surrogate_risk(field_runs, sig, w, rng, lam_ref, n_cal, ctrl="lqr_i", **cond_kw):
    """Collect pair maxima on reference runs to evaluate the monotone surrogate
    loss (Theorem 4) for any lambda without re-simulation."""
    recs = []
    for F, idx in field_runs(n_cal):
        ys = core.plan(F, w, lam_ref, sig)
        X, D, cond = run(F, ys, len(idx), rng, ctrl=ctrl, w=w, **cond_kw)
        sv = sig.vec(F, ys)
        recs.append((F, ys, X, D, sv))
    return recs


def offsets(F, ys, X, D, step=1.0):
    """Lateral offsets of every pass on a common along-track grid (nan = absent)."""
    minx, _, maxx, _ = F.M.bounds
    xg = np.arange(math.ceil(minx), math.floor(maxx) + 1, step)
    off = np.stack([core.pass_offsets(X[k], D[k], xg) for k in range(len(ys))])
    return xg, off


def pair_diffs(F, ys, X, D):
    _, off = offsets(F, ys, X, D, step=1.0)
    d = (off[1:] - off[:-1]).ravel()
    return d[np.isfinite(d)]


def risk_lambda(recs, w, alpha, lam_grid):
    """Conformal risk control on the surrogate gap-sum loss (bound B=1)."""
    losses = []  # (n_runs, len(lam_grid))
    for F, ys, X, D, sv in recs:
        _, off = offsets(F, ys, X, D, step=1.0)
        R = D[0].shape[0]
        diffs = off[1:] - off[:-1]  # (K-1, R, nx)
        ssum = (sv[1:] + sv[:-1])[:, None, None]
        L = np.zeros((R, len(lam_grid)))
        for i, lam in enumerate(lam_grid):
            g = np.clip(diffs - lam * ssum, 0, None)
            g = np.nan_to_num(g)
            b = np.nan_to_num(np.clip(off[0] - lam * sv[0], 0, None)) + \
                np.nan_to_num(np.clip(-off[-1] - lam * sv[-1], 0, None))
            L[:, i] = (g.sum(axis=(0, 2)) + b.sum(axis=1)) / F.M.area
        losses.append(L)
    Lall = np.concatenate(losses)
    n = len(Lall)
    Rn = Lall.mean(0)
    ok = (n * Rn + 1.0) / (n + 1) <= alpha
    if not ok.any():
        return np.inf
    return lam_grid[np.argmax(ok)]


# --------------------------------------------------------------------- evaluation
def evaluate_plan(F, ys, n_test, rng, w=W_DEFAULT, ctrl="lqr_i", **cond_kw):
    X, D, _ = run(F, ys, n_test, rng, ctrl=ctrl, w=w, **cond_kw)
    miss = core.evaluate(F, ys, X, D, w)
    return dict(p_nomiss=float(np.mean(miss == 0)), e_miss=float(miss.mean()),
                p95_miss=float(np.percentile(miss, 95)), passes=len(ys),
                overlap=overlap_ratio(F, ys, w))


def gaussian_pointwise_lambda(pair_diffs_m, eps):
    """Engineering baseline: per-point Gaussian gap probability <= eps."""
    sd = np.nanstd(pair_diffs_m)
    return norm.ppf(1 - eps) * sd / 2


def gaussian_score_lambda(scores, eps):
    """Parametric chance constraint on the same run-level score (Normal fit)."""
    return float(np.mean(scores) + norm.ppf(1 - eps) * np.std(scores, ddof=1))


def empirical_pointwise_lambda(pair_diffs_m, eps):
    """Data-driven engineering baseline: empirical (1-eps) quantile of the
    pointwise pass-to-pass difference (no sup over the field, no calibration)."""
    return float(np.quantile(pair_diffs_m, 1 - eps)) / 2


def cantelli_score_lambda(scores, eps):
    """Distribution-free but non-conformal: one-sided Chebyshev (Cantelli)
    bound on the run-level score, P(S >= mu + k sd) <= 1/(1+k^2)."""
    k = math.sqrt((1 - eps) / eps)
    return float(np.mean(scores) + k * np.std(scores, ddof=1))


# ------------------------------------------------------------- stronger baselines
def scenario_lambda(scores, eps, beta=0.01):
    """Scenario approach with sample discarding (Campi & Garatti, 2011) for a
    single decision variable (d = 1): discard the k largest scores, where k is
    the largest integer with  sum_{i<=k} C(n,i) eps^i (1-eps)^(n-i) <= beta."""
    from scipy.stats import binom

    s = np.sort(np.asarray(scores))[::-1]
    n = len(s)
    k = -1
    while k + 1 < n and binom.cdf(k + 1, n, eps) <= beta:
        k += 1
    return float(s[k + 1]) if k + 1 < n else float(s[-1])


def cvar_lambda(scores, eps):
    """Empirical CVaR_eps of the run score (Rockafellar & Uryasev)."""
    s = np.sort(np.asarray(scores))
    tail = s[int(math.floor((1 - eps) * len(s))):]
    return float(tail.mean())


def dro_cvar_lambda(scores, eps, beta=0.01):
    """Worst-case CVaR over a type-1 Wasserstein ball around the empirical
    distribution (Esfahani & Kuhn, 2018): CVaR_eps + rho/eps, with the
    radius from the standard concentration rate rho = sd * sqrt(log(1/beta)/n)."""
    s = np.asarray(scores)
    rho = np.std(s, ddof=1) * math.sqrt(math.log(1 / beta) / len(s))
    return cvar_lambda(s, eps) + rho / eps


def pointwise_conformal_lambda(pair_diffs_m, eps):
    """Split conformal on the POINTWISE pass-to-pass difference (no sup):
    valid per point, not per operation (ablation of the run-level score)."""
    return float(core.conformal_quantile(pair_diffs_m, eps)) / 2


def slope_rule_lambda(field, comp=0.85, base=0.025, h=2.6):
    """Physics-based industry rule: base pass-to-pass accuracy plus the residual
    antenna roll offset on the field's mean side slope, h*tan(slope)*(1-c)."""
    return base + h * math.tan(math.radians(field.z_mean_slope)) * (1 - comp)


def pair_union_lambda(pair_scores_runs, eps, n_terms):
    """Theorem 3 (pair level): per-pair conformal quantile at level eps/n_terms,
    union bound over the n_terms constraints of the operation."""
    return float(core.conformal_quantile(pair_scores_runs, eps / max(n_terms, 1)))

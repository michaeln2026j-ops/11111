"""Published uncertainty-quantification (UQ) planning baselines.

Every function here turns calibration runs of the closed-loop execution on the
SAME field (in-field setting) into a constraint tightening for the coverage
planner core.plan, so that the result can be compared directly with the
conformal-erosion methods in exp_lib (CE-U / CE-A).

  (a) lindemann_cp_lambda   conformal prediction regions per constraint, union
                            bound over the T constraints of one operation
  (b) cpp_lambda            conformal predictive programming, chance constraint
                            replaced by a conformal quantile at a FIXED decision
  (c) gp_margin / gp_plan   Gaussian-process cautious tightening (individual
                            Gaussian chance constraints on the GP predictive law)

Units.  (a), (b) return an erosion lam in METRES for the uniform sigma
UNIT = exp_lib.ConstSigma(1.0): ys = core.plan(F, w, lam, UNIT) gives the
half-width h_k = w/2 - lam, i.e. pass spacing w - 2*lam.  (c) returns
(z, sig_fn) with z dimensionless (a standard-normal quantile) and sig_fn(F, y)
in metres: ys = core.plan(F, w, z, sig_fn) gives h_k = w/2 - z*sig_fn(F, y_k).
lam = inf means "not computable with this many calibration runs"; core.plan
then raises ValueError("infeasible erosion"), which the experiment scripts
already treat as an infeasible method.

Constraints of one operation (shared by all three baselines).  With e_k(x) the
field-frame lateral offset of pass k at along-track sample x (1 m grid of
core.evaluate / core.pair_scores, main-area mask of core.pair_scores) the plan
leaves no gap iff, for all x,
    pair k:      e_{k+1}(x) - e_k(x) <= (w - (y_{k+1} - y_k))     (= 2 lam)
    boundary 1:  e_1(x)              <= w/2 - (y_1 - y_lo)         (=   lam)
    boundary N: -e_N(x)              <= w/2 - (y_hi - y_N)         (=   lam)
For uniform erosion these are  r(x) <= lam  with the per-constraint scores
r = (e_{k+1}-e_k)/2, e_1, -e_N; the max of r over all constraints of a run is
exactly the run score S of core.pair_scores(F, ys, X, D, ones) (checked in
selftest).

=============================================================================
(a) Lindemann, Cleaveland, Shim, Pappas (2023)
=============================================================================
Reference (verified: venue, volume, issue and DOI from the NSF-PAR record; page
range as cited by later papers; arXiv id):
  L. Lindemann, M. Cleaveland, G. Shim and G. J. Pappas, "Safe Planning in
  Dynamic Environments Using Conformal Prediction," IEEE Robotics and
  Automation Letters, vol. 8, no. 8, pp. 5116-5123, Aug. 2023,
  doi:10.1109/LRA.2023.3292071.  arXiv:2210.10254.
Algorithm: an MPC uses trajectory predictions Y_hat_tau of the uncertain
environment; for every prediction step tau a split-conformal region
||Y_tau - Y_hat_tau|| <= C_tau is calibrated SEPARATELY at level 1 - delta/T,
so that by the union bound all T regions hold jointly with probability
>= 1 - delta; the constraints are tightened as c(x_tau, Y_hat_tau) - L*C_tau >= 0
(L = Lipschitz constant of c).  The predictions are assumed independent of the
planner's decision (exogenous agents).
Adaptation (minimal, explicit):
  * Uncertain quantity Y = execution offsets e_k(x); prediction Y_hat = nominal
    execution (e = 0), which is what the planner assumes.
  * One "time step" = one gap constraint of the operation.  granularity='point'
    (default): every (pair k, sample x) and the two boundary terms at every x,
    i.e. one constraint per 1 m of travel (0.5 s at v = 2 m/s), which is the
    literal per-time-step view because the gap constraint at (k, x) is decided
    when pass k+1 drives over x.  T = number of such constraints of the
    reference plan.  granularity='pair': one constraint per pass pair (sup over
    x) plus the two boundary terms, T = K + 1 (one coarse time step per pass).
  * Score: score='signed' (default) uses the constraint-direction projection
    r = (e_{k+1}-e_k)/2, e_1, -e_N, i.e. the region is one-sided and L = 1
    (tightest valid choice; CP accepts any score).  score='abs' uses |r|, the
    two-sided norm-ball region of the paper.
  * pool=False is the paper's procedure: C_tau from the n_cal scores of
    constraint tau alone, level eps/T, lam = max_tau C_tau (uniform erosion
    must satisfy every tightened constraint).  It needs n_cal >= T/eps - 1
    calibration runs, otherwise lam = inf (reported in info['n_required']).
    pool=True (default, as specified for this study) pools the per-constraint
    scores of all constraints and runs and takes ONE conformal quantile at level
    eps/T.  The union bound only needs the SUM of the per-constraint violation
    probabilities, sum_tau P(r_tau > lam) = T * P(r_J > lam) with J a uniformly
    drawn constraint, and the pooled quantile targets exactly
    P(r_J > lam) <= eps/T (the pooled scores are draws of r_J), so the
    union-bound argument is kept in expectation; what is lost is the exact
    finite-sample conformal guarantee, because the T pooled scores of one run
    are dependent, not exchangeable draws.  It is the only variant that is
    finite with ~1e2 calibration runs.
    granularity='pair', pool=True equals exp_lib.pair_union_lambda.
    Which granularity to report: 'point' is the literal per-time-step union
    (and the default requested for this study); 'pair' (one coarse step per
    pass) is the LESS conservative choice a practitioner could equally defend.
    To pre-empt a "weakened baseline" objection, report both, or 'pair' as
    the headline Lindemann number.
  * Decision dependence: none, as in the paper.  Calibration runs use the
    reference plan pi(lam_ref) (default lam_ref = 0, the nominal plan) and T is
    counted on it (t_count='ref').  t_count='final' re-counts T on the plan
    pi(lam) actually executed (no re-simulation) until T stops growing.

=============================================================================
(b) Zhao, Yu, Deshmukh, Lindemann (2024): conformal predictive programming
=============================================================================
Reference (verified: title, authors and arXiv id; no journal version found;
later arXiv versions add M. Sesia as co-author; algorithm checked against the
authors' code, github.com/SAIDS-Lab/Conformal-Predictive-Programming-for-CCO,
commit 9927b0f, resources/chance_constraint_encoders.py):
  Y. Zhao, X. Yu, J. V. Deshmukh and L. Lindemann, "Conformal Predictive
  Programming for Chance Constrained Optimization," arXiv:2402.07407, 2024.
Algorithm: min J(x) s.t. P(f(x, Y) <= 0) >= 1 - delta is replaced, with
calibration samples Y^(1..K) whose law does not depend on x, by the quantile
lemma  Quantile_{1-delta}(f(x, Y^(1)), ..., f(x, Y^(K)), inf) <= 0, encoded as
CPP-MIP  #{i : f(x, Y^(i)) <= 0} >= ceil((K+1)(1-delta))  (or CPP-KKT).
Joint constraints f_1..f_J: "Max" encodes max_j f_j, "Union" encodes every
f_j separately at delta/J.
Adaptation: decision x = lam (scalar), cost J = number of passes (monotone in
lam), f(lam, Y) = S(Y) - lam with S the run score (max over all gap
constraints = CPP "Max" joint encoding, joint='max'), evaluated on runs of ONE
fixed decision, the nominal plan lam_ref = 0, because CPP assumes the
uncertainty is exogenous to the decision.  For scalar lam the MIP has the
closed-form solution lam* = ceil((K+1)(1-delta))-th smallest S (implemented
as the count literally, and checked against core.conformal_quantile).
joint='union' is the CPP "Union" encoding over the K+1 per-pair constraints.
What is NOT handled (by design, it is the point of this baseline): the score
distribution under the certified plan pi(lam*) differs from the one at lam_ref
(passes move to different terrain, there are more passes, hence more pairs).
This is exactly the decision dependence exp_lib.calibrate_conformal (CE-U)
handles by its fixed-point reference plan.

=============================================================================
(c) Hewing, Kabzan, Zeilinger (2020): cautious MPC with GP regression
=============================================================================
Reference (verified: title, authors, journal, volume, issue, year, arXiv id;
the page range could not be confirmed and is omitted):
  L. Hewing, J. Kabzan and M. N. Zeilinger, "Cautious Model Predictive Control
  Using Gaussian Process Regression," IEEE Transactions on Control Systems
  Technology, vol. 28, no. 6, 2020.  arXiv:1705.10702.
Algorithm: the unknown part of the dynamics is a GP learnt from data; the
predicted state is approximated as Gaussian with the GP mean and variance
(posterior variance + noise), and each half-space state chance constraint
P(h^T x <= b) >= p is replaced by the tightened mean constraint
h^T mu <= b - Phi^{-1}(p) sqrt(h^T Sigma h): individual (per constraint, per
prediction step) chance constraints, no joint guarantee.
Adaptation:
  * The GP replaces the unknown execution model.  sklearn
    GaussianProcessRegressor, kernel C * RBF(ARD, 3 length scales) +
    WhiteKernel, normalize_y, hyper-parameters by marginal likelihood, trained
    on n_gp points subsampled uniformly from the calibration runs (the paper
    likewise uses a sparse/limited data set).  Inputs (moisture is unobserved
    by the planner, so it is NOT an input): lateral side slope g_y (tan,
    signed, field frame, at the pass line), pass direction (+1/-1), along-track
    position x [m]; inputs are standardised.
  * pair GP (pair_model='diff', default): target = pass-to-pass difference
    e_{k+1}(x) - e_k(x) with inputs (mean slope of the two lines, direction of
    pass k, x); its predictive law is that of h^T e with h = (-1, 1), i.e.
    sqrt(h^T Sigma h) including the cross-pass covariance (the per-run mounting
    bias alternates sign between passes, so adjacent offsets are correlated).
    pair_model='indep': per-pass GP of e_k(x) and the diagonal-covariance form
    sqrt(sig_k^2 + sig_{k+1}^2), mean mu_{k+1} - mu_k.
  * pass GP: target e_k(x); used for the two boundary constraints (and for
    'indep').
  * Tightening, per constraint, with z = Phi^{-1}(1 - eps) (union=True: the
    Bonferroni level Phi^{-1}(1 - eps/T), T = pointwise constraint count):
        pair:      t_pair = max_x [mu_D(x) + z sd_D(x)]+         (metres)
        boundary:  t_lo   = max_x [ mu_1(x) + z sd_1(x)]+,
                   t_hi   = max_x [-mu_N(x) + z sd_N(x)]+
    (max over x because one lateral spacing must satisfy every pointwise
    constraint of the pair; [.]+ : a cautious planner never widens a pass
    beyond the implement width).  use_mean=False drops the mean terms.
  * Exact planner gp_plan(F, model): greedy placement with
    y_1 = y_lo + w/2 - t_lo, y_{k+1} = y_k + w - t_pair(k, k+1) (fixed point,
    because the GP inputs of pass k+1 depend on y_{k+1}), stop when
    y_k + w/2 - t_hi >= y_hi.
  * sig_fn for core.plan with lam = z (requested interface): the pair
    tightening is split equally over the two passes, sig(y) = t_pair(y)/(2z)
    with t_pair evaluated for a pass at y and its neighbour at the same
    terrain (max over both directions; 'indep' uses the opposite direction for
    the neighbour), so z*(sig_k + sig_{k+1}) = t_pair for equal neighbours, i.e.
    "z * sqrt(sig_k^2 + sig_{k+1}^2)/2 per pass" for the 'indep' model.  For a
    pass whose strip touches the boundary (|y - y_lo| or |y_hi - y| <= w/2) sig
    is raised to t_lo/z or t_hi/z so that the single-pass boundary constraint
    is tightened by its own z*sd, as in the exact planner.  The mean terms are
    divided by z, so sig_fn is built for lam = z (model.z).
  * Faithfulness check (selftest): on fresh runs of the exact GP plan the
    empirical POINTWISE violation rate of the pair constraints is at or below
    eps, i.e. the baseline meets its own design target; its near-zero
    P(no miss) is the consequence of individual (per point) chance
    constraints, not of a mis-fitted GP.  Report union=True (Bonferroni) next
    to it, since that is the operation-level reading of the same method.

Calibration conditions.  Every function accepts core.Condition keywords or
cond_fn(rng, n) -> core.Condition (see collect).  Calibration conditions must
be drawn from the same law as the test conditions of the regime being
evaluated (e.g. exp_system.py's wet regime draws moisture ~ U(0.6, 0.9) in
make_cond, which plain Condition keywords cannot express: pass
cond_fn=lambda r, n: make_cond(r, n, reg)).
"""
import math
import time
import warnings

import numpy as np
from scipy.stats import norm

import core
import exp_lib

W_DEFAULT = exp_lib.W_DEFAULT
UNIT = exp_lib.ConstSigma(1.0)  # uniform sigma: h_k = w/2 - lam

__all__ = ["UNIT", "CalData", "collect", "pass_grids", "active_constraints", "pointwise_violation", "point_scores",
           "pair_sup_scores", "n_constraints", "lindemann_cp_lambda", "cpp_mip_scalar", "cpp_lambda",
           "GPMargin", "fit_gp_margin", "gp_margin", "gp_plan", "selftest"]


# ------------------------------------------------------------------ calibration data
class CalData:
    """Calibration runs of one field executed with the reference plan
    ys = core.plan(field, w, lam_ref, UNIT).  Pass the same CalData to several
    baselines (cal=...) to share the runs."""

    def __init__(self, field, ys, X, D, cond, lam_ref, w, ctrl):
        self.field, self.ys, self.X, self.D, self.cond = field, np.asarray(ys), X, D, cond
        self.lam_ref, self.w, self.ctrl = lam_ref, w, ctrl

    @property
    def n(self):
        return self.D[0].shape[0]


def collect(field, rng, n_cal=100, w=W_DEFAULT, ctrl="lqr_i", lam_ref=0.0, cond_fn=None, **cond_kw):
    """Run n_cal calibration operations of the reference plan pi(lam_ref).

    Operating conditions: core.Condition(rng, n_cal, **cond_kw), or, when
    cond_fn is given, cond_fn(rng, n_cal) -> core.Condition.  Use cond_fn
    whenever the test regime draws conditions with a custom generator (e.g. the
    wet regime of exp_system.py, moisture ~ U(0.6, 0.9) per run, which plain
    Condition keywords cannot express): calibration and test conditions must
    come from the same law, otherwise the baseline is calibrated on the wrong
    distribution."""
    lam_ref = 0.0 if lam_ref is None else float(lam_ref)
    ys = core.plan(field, w, lam_ref, UNIT)
    if cond_fn is not None:
        if cond_kw:
            raise ValueError("pass either cond_fn or core.Condition keywords, not both")
        cond = cond_fn(rng, n_cal)
        X, D = core.simulate(field, ys, cond, rng, ctrl=ctrl)
    else:
        X, D, cond = exp_lib.run(field, ys, n_cal, rng, ctrl=ctrl, w=w, **cond_kw)
    return CalData(field, ys, X, D, cond, lam_ref, w, ctrl)


def _get_cal(field, rng, n_cal, w, ctrl, lam_ref, cal, cond_kw):
    if cal is None:
        return collect(field, rng, n_cal, w=w, ctrl=ctrl, lam_ref=lam_ref, **cond_kw)
    same = cal.field is field or (cal.field.fid == field.fid and
                                  cal.field.meta.get("heading_deg") == field.meta.get("heading_deg"))
    if not same:
        raise ValueError("calibration data belong to a different field / heading (in-field setting)")
    if cal.w != w:
        raise ValueError(f"calibration data were collected with w={cal.w}, not w={w}")
    # arguments that only affect data collection must not silently disagree with the shared data
    if lam_ref is not None and float(lam_ref) != cal.lam_ref:
        raise ValueError(f"calibration data were collected at lam_ref={cal.lam_ref}, not {lam_ref}")
    if isinstance(ctrl, str) and isinstance(cal.ctrl, str) and ctrl != cal.ctrl:
        raise ValueError(f"calibration data were collected with ctrl={cal.ctrl!r}, not {ctrl!r}")
    if cond_kw:
        raise ValueError(f"condition arguments {sorted(cond_kw)} are ignored when cal= is given")
    return cal


# --------------------------------------------------------------- constraint geometry
def pass_grids(field, ys, dx=1.0):
    """Along-track sample positions of every pass, identical to the X returned by
    core.simulate (pass k driven +x for even k, -x for odd k); used to count the
    constraints of a plan without simulating it (equality checked in selftest)."""
    X = []
    for k, y in enumerate(ys):
        c = field.chord(field.P, y)
        x0, x1 = (c if c else (0.0, 0.0))
        L = max(x1 - x0, 1.0)
        sk = np.arange(int(L / dx)) * dx
        X.append(x0 + sk if k % 2 == 0 else x1 - sk)
    return X


def active_constraints(field, ys, X, w=W_DEFAULT):
    """Active pointwise gap constraints of plan ys, with the grid and main-area
    mask of core.pair_scores.  Returns xg (nx,), m (K, nx) pass k present and
    relevant at x (boundary terms use m[0], m[-1]), pm (K-1, nx) pair k active."""
    minx, _, maxx, _ = field.M.bounds
    xg = np.arange(math.ceil(minx), math.floor(maxx) + 1, 1.0)
    ys = np.asarray(ys)
    K = len(ys)
    present = np.stack([np.isfinite(core.pass_offsets(X[k], np.zeros((1, len(X[k]))), xg)[0])
                        for k in range(K)])
    mask = np.zeros((K, len(xg)), bool)
    for j, x in enumerate(xg):
        c = core._chord_x(field.M, x)
        if c is None:
            continue
        lo, hi = c
        mask[:, j] = (ys > lo - w) & (ys < hi + w)
    m = mask & present
    return xg, m, m[:-1] & m[1:]


def n_constraints(field, ys, w=W_DEFAULT, granularity="point"):
    """Number T of gap constraints of plan ys (no simulation needed)."""
    _, m, pm = active_constraints(field, ys, pass_grids(field, ys), w)
    if granularity == "point":
        return int(pm.sum() + m[0].sum() + m[-1].sum())
    return int(pm.any(axis=1).sum() + m[0].any() + m[-1].any())


def pointwise_violation(field, ys, X, D, w=W_DEFAULT):
    """Empirical fraction of the pointwise gap constraints of an ARBITRARY plan
    ys violated by executed runs (X, D), pooled over runs and constraints:
    pair k at x violated iff e_{k+1}(x) - e_k(x) > w - (y_{k+1} - y_k),
    boundaries iff e_1(x) > w/2 - (y_1 - y_lo) or -e_N(x) > w/2 - (y_hi - y_N).
    This is the quantity an individual (per-point) chance constraint at level
    eps promises to keep <= eps; P(no miss) is the operation-level one."""
    ys = np.asarray(ys)
    _, off = exp_lib.offsets(field, ys, X, D)
    _, m, pm = active_constraints(field, ys, X, w)
    y_lo, y_hi = field.lateral_range()
    kk, jj = np.nonzero(pm)
    v = (off[kk + 1, :, jj] - off[kk, :, jj]) > (w - (ys[kk + 1] - ys[kk]))[:, None]
    b1 = off[0][:, m[0]] > w / 2 - (ys[0] - y_lo)
    bN = -off[-1][:, m[-1]] > w / 2 - (y_hi - ys[-1])
    n = v.size + b1.size + bN.size
    return float((v.sum() + b1.sum() + bN.sum()) / max(n, 1))


def point_scores(field, cal, score="signed"):
    """Per-constraint, per-run scores on the reference plan.

    Returns dict(scores=(T, R) array, kind=(T,) pair index k or -1 (boundary 1)
    or -2 (boundary N), x=(T,) along-track position).  Rows are the pointwise
    constraints r = (e_{k+1}-e_k)/2, e_1, -e_N; score='abs' takes |r|."""
    xg, off = exp_lib.offsets(field, cal.ys, cal.X, cal.D)  # (K, R, nx)
    _, m, pm = active_constraints(field, cal.ys, cal.X, cal.w)
    kk, jj = np.nonzero(pm)
    pair = (off[kk + 1, :, jj] - off[kk, :, jj]) / 2.0  # (P, R)
    b1 = off[0][:, m[0]].T
    bN = -off[-1][:, m[-1]].T
    S = np.concatenate([pair, b1, bN])
    if score == "abs":
        S = np.abs(S)
    elif score != "signed":
        raise ValueError("score must be 'signed' or 'abs'")
    kind = np.r_[kk, np.full(len(b1), -1), np.full(len(bN), -2)]
    x = np.r_[xg[jj], xg[m[0]], xg[m[-1]]]
    return dict(scores=S, kind=kind, x=x)


def pair_sup_scores(field, cal, score="signed"):
    """Per-pair sup-over-x scores (one row per active pair, then boundary 1 and
    boundary N), shape (T, R); signed rows are core.pair_scores with sigma = 1."""
    if score == "signed":
        _, pair, b1, bN = core.pair_scores(field, cal.ys, cal.X, cal.D, np.ones(len(cal.ys)), w=cal.w)
        rows = [pair[:, k] for k in range(pair.shape[1]) if np.isfinite(pair[:, k]).all()]
        rows += [r for r in (b1, bN) if np.isfinite(r).all()]
        return np.array(rows)
    ps = point_scores(field, cal, score=score)
    return np.array([ps["scores"][ps["kind"] == k].max(axis=0) for k in np.unique(ps["kind"])])


# --------------------------------------------------------------- conformal helpers
def _order_k(n, level, delta=None):
    """ceil((n+1)(1-level)) (marginal, core's rule) or, with delta, the smallest k with
    BinomCDF(k-1; n, 1-level) >= 1-delta (training-conditional / PAC, Vovk 2012; v8 fairness control)."""
    if delta is None:
        return int(math.ceil((n + 1) * (1 - level)))
    from scipy.stats import binom
    for k in range(1, n + 1):
        if binom.cdf(k - 1, n, 1 - level) >= 1 - delta:
            return k
    return n + 1


def _cq_pooled(s, level, delta=None):
    """Split-conformal quantile ceil((n+1)(1-level))-th smallest (core's rule); PAC order with delta."""
    s = np.asarray(s, float).ravel()
    n = s.size
    k = _order_k(n, level, delta)
    if k > n or n == 0:
        return np.inf
    return float(np.partition(s, k - 1)[k - 1])


def _cq_rows(P, level, delta=None):
    """Separate split-conformal quantile of every row of P (T, R)."""
    R = P.shape[1]
    k = _order_k(R, level, delta)
    if k > R:
        return np.full(P.shape[0], np.inf)
    return np.partition(P, k - 1, axis=1)[:, k - 1]


def _lindemann_q(P, level, pool, delta=None):
    return _cq_pooled(P, level, delta) if pool else float(np.max(_cq_rows(P, level, delta)))


# ------------------------------------------------------------------ (a) Lindemann
def lindemann_cp_lambda(field, rng, eps, n_cal=100, w=W_DEFAULT, ctrl="lqr_i", granularity="point",
                        pool=True, score="signed", lam_ref=None, t_count="ref", cal=None, info=False,
                        pac_delta=None, **cond_kw):
    """Conformal constraint tightening with a union bound over the T gap
    constraints of one operation (Lindemann et al., RA-L 2023).

    Returns lam [m] for ys = core.plan(field, w, lam, UNIT); with info=True
    returns (lam, dict).  granularity: 'point' (one constraint per (pair, x) and
    boundary x) or 'pair' (sup over x per pair).  pool: True = one pooled
    quantile at eps/T, False = the paper's separate per-constraint quantiles
    (needs n_cal >= T/eps - 1).  t_count: 'ref' (T of the reference plan) or
    'final' (T of the executed plan pi(lam)).  cal: shared CalData (then n_cal,
    lam_ref and condition arguments are taken from it).  lam_ref: reference
    plan of the calibration runs (None -> 0, the nominal plan).  **cond_kw:
    core.Condition keywords, or cond_fn=callable(rng, n) -> core.Condition
    (see collect). pac_delta: PAC version (v8 fairness control): the union bound splits (eps, delta)
    over the T constraints, each quantile taken with the PAC order at (eps/T, delta/T)."""
    t0 = time.time()
    dT = None
    cal = _get_cal(field, rng, n_cal, w, ctrl, lam_ref, cal, cond_kw)
    if granularity == "point":
        P = point_scores(field, cal, score)["scores"]
    elif granularity == "pair":
        P = pair_sup_scores(field, cal, score)
    else:
        raise ValueError("granularity must be 'point' or 'pair'")
    T = P.shape[0]
    T_used = T
    dT = None if pac_delta is None else pac_delta / T_used
    lam = _lindemann_q(P, eps / T_used, pool, dT)
    if t_count == "final":
        for _ in range(20):
            try:
                ys = core.plan(field, w, lam, UNIT)
            except ValueError:
                break
            T_new = n_constraints(field, ys, w, granularity)
            if T_new <= T_used:
                break
            T_used = T_new
            dT = None if pac_delta is None else pac_delta / T_used
            lam = _lindemann_q(P, eps / T_used, pool, dT)
    elif t_count != "ref":
        raise ValueError("t_count must be 'ref' or 'final'")
    if not info:
        return lam
    return lam, dict(T_ref=T, T=T_used, level=eps / T_used, n_runs=cal.n, n_scores=P.size,
                     n_required=int(math.ceil(T_used / eps - 1)) if not pool else int(math.ceil(1 / eps - 1 / T_used)),
                     K_ref=len(cal.ys), lam_ref=cal.lam_ref, granularity=granularity, pool=pool,
                     score=score, runtime_s=time.time() - t0)


# ------------------------------------------------------------------------ (b) CPP
def cpp_mip_scalar(f0, delta, pac_delta=None):
    """CPP-MIP for a scalar decision lam with f(lam, Y_i) = f0_i - lam:
    min lam s.t. #{i : f0_i - lam <= 0} >= ceil((K+1)(1-delta)).  Returns inf
    when K < ceil((K+1)(1-delta)) (the authors' code raises 'Training dataset
    not large enough')."""
    f0 = np.sort(np.asarray(f0, float).ravel())
    K = len(f0)
    need = _order_k(K, delta, pac_delta)
    if need > K:
        return np.inf
    return float(f0[need - 1])  # the smallest lam that satisfies `need` sample constraints


def cpp_lambda(field, rng, eps, n_cal=100, w=W_DEFAULT, ctrl="lqr_i", joint="max", lam_ref=None, cal=None,
               info=False, pac_delta=None, **cond_kw):
    """Conformal predictive programming (Zhao et al., 2024) at a fixed decision.

    Calibration runs use the nominal plan pi(lam_ref = 0); joint='max' applies
    the quantile lemma to the run score S (max over all constraints), joint=
    'union' to every per-pair constraint at eps/J.  Returns lam [m] for
    ys = core.plan(field, w, lam, UNIT) (and a dict with info=True).
    cal / lam_ref / **cond_kw (incl. cond_fn) as in lindemann_cp_lambda."""
    t0 = time.time()
    cal = _get_cal(field, rng, n_cal, w, ctrl, lam_ref, cal, cond_kw)
    if joint == "max":
        S, *_ = core.pair_scores(field, cal.ys, cal.X, cal.D, np.ones(len(cal.ys)), w=w)
        lam, J = cpp_mip_scalar(S, eps, pac_delta), 1
    elif joint == "union":
        P = pair_sup_scores(field, cal)
        J = P.shape[0]
        lam = max(cpp_mip_scalar(p, eps / J, None if pac_delta is None else pac_delta / J) for p in P)
    else:
        raise ValueError("joint must be 'max' or 'union'")
    if not info:
        return lam
    return lam, dict(joint=joint, J=J, n_runs=cal.n, K_ref=len(cal.ys), lam_ref=cal.lam_ref,
                     n_required=int(math.ceil(J / eps - 1)), runtime_s=time.time() - t0)


# ------------------------------------------------------------------ (c) GP cautious
def _fit_gp(Fx, y, seed):
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel

    mu, sd = Fx.mean(0), Fx.std(0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    kern = (ConstantKernel(1.0, (1e-4, 1e2)) * RBF(np.ones(Fx.shape[1]), (1e-2, 1e3))
            + WhiteKernel(0.5, (1e-5, 1e1)))
    gp = GaussianProcessRegressor(kern, normalize_y=True, n_restarts_optimizer=0, random_state=seed)
    try:  # n_gp ~ 1e3: one BLAS thread is as fast as four and leaves the shared CPUs free
        from threadpoolctl import threadpool_limits
        limit = threadpool_limits(1)
    except Exception:
        limit = None
    try:
        with warnings.catch_warnings():  # length scales at their bound = irrelevant input (e.g. x), benign
            warnings.simplefilter("ignore", ConvergenceWarning)
            gp.fit((Fx - mu) / sd, y)
    finally:
        if limit is not None:
            limit.restore_original_limits()
    return gp, mu, sd


class GPMargin:
    """Fitted cautious-GP tightening.  Callable as sig_fn(field, y) [m] for
    core.plan(field, w, model.z, model); model.plan(field) is the exact
    per-constraint planner gp_plan."""

    def __init__(self, gp_pair, gp_pass, z, w=W_DEFAULT, pair_model="diff", use_mean=True):
        self.gp_pair, self.gp_pass = gp_pair, gp_pass  # (gp, feat_mean, feat_sd)
        self.z, self.w, self.pair_model, self.use_mean = float(z), w, pair_model, use_mean
        self._cache = {}

    # -- GP predictions
    @staticmethod
    def _predict(model, slope, d, xs):
        gp, mu, sd = model
        Fx = np.c_[slope, np.full(len(xs), float(d)), xs]
        m, s = gp.predict((Fx - mu) / sd, return_std=True)
        return m, s

    @staticmethod
    def _xs(field, y):
        c = field.chord(field.M, y) or field.chord(field.P, y)
        if c is None:
            return None
        xs = np.arange(math.ceil(c[0]), math.floor(c[1]) + 1, 1.0)
        return xs if len(xs) else np.array([0.5 * (c[0] + c[1])])

    def _pos(self, v):
        return np.clip(v, 0.0, None)

    def pair_tightening(self, field, yk, yk1, d):
        """t_pair [m] for the pair (pass k at yk driven in direction d, pass k+1
        at yk1 driven in -d): max_x [mu_D + z sd_D]+."""
        xs = self._xs(field, 0.5 * (yk + yk1))
        if xs is None:
            return 0.0
        gk, gk1 = field.gy(xs, np.full_like(xs, yk)), field.gy(xs, np.full_like(xs, yk1))
        if self.pair_model == "diff":
            m, s = self._predict(self.gp_pair, 0.5 * (gk + gk1), d, xs)
        else:  # independent passes: h^T Sigma h with diagonal Sigma
            m0, s0 = self._predict(self.gp_pass, gk, d, xs)
            m1, s1 = self._predict(self.gp_pass, gk1, -d, xs)
            m, s = m1 - m0, np.sqrt(s0 ** 2 + s1 ** 2)
        return float(np.max(self._pos(self.use_mean * m + self.z * s)))

    def boundary_tightening(self, field, y, d, side):
        """t_lo = max_x [mu_1 + z sd_1]+ (side='lo') or t_hi = max_x [-mu_N + z sd_N]+."""
        xs = self._xs(field, y)
        if xs is None:
            return 0.0
        m, s = self._predict(self.gp_pass, field.gy(xs, np.full_like(xs, y)), d, xs)
        sgn = 1.0 if side == "lo" else -1.0
        return float(np.max(self._pos(sgn * self.use_mean * m + self.z * s)))

    # -- sig_fn interface for core.plan (lam = z)
    def __call__(self, field, y):
        if not self.z > 0:  # sig = t / (2z) is only defined for eps < 0.5; model.plan() has no such limit
            raise ValueError(f"sig_fn interface needs z > 0 (eps < 0.5), got z={self.z}; use model.plan(field)")
        key = (field.fid, field.meta.get("heading_deg"), round(float(y), 2))
        if key not in self._cache:
            t = max(self.pair_tightening(field, y, y, d) for d in (1.0, -1.0))
            sig = t / (2 * self.z)
            y_lo, y_hi = field.lateral_range()
            if y - y_lo <= self.w / 2 + 1e-6:  # first pass (driven +x)
                sig = max(sig, self.boundary_tightening(field, y, 1.0, "lo") / self.z)
            if y_hi - y <= self.w / 2 + 1e-6:  # last pass (direction depends on K parity)
                sig = max(sig, max(self.boundary_tightening(field, y, d, "hi") for d in (1.0, -1.0)) / self.z)
            self._cache[key] = sig
        return self._cache[key]

    def vec(self, field, ys):
        return np.array([self(field, y) for y in ys])

    def plan(self, field, max_passes=400):
        return gp_plan(field, self, self.w, max_passes=max_passes)

    def variant(self, eps=None, union=False, pair_model=None, use_mean=None):
        """Same fitted GPs, different level / pair model / mean use (no refit).
        eps given: z = Phi^{-1}(1-eps) or, with union, Phi^{-1}(1-eps/T)."""
        z = self.z if eps is None else norm.ppf(1 - (eps / self.fit_info["T"] if union else eps))
        pm = self.pair_model if pair_model is None else pair_model
        if pm == "diff" and self.gp_pair is None:
            raise ValueError("pair GP not fitted (model was fitted with pair_model='indep')")
        v = GPMargin(self.gp_pair, self.gp_pass, z, w=self.w, pair_model=pm,
                     use_mean=self.use_mean if use_mean is None else use_mean)
        v.fit_info = dict(self.fit_info)
        return v


def _gp_training(field, cal, n_gp, rng):
    xg, off = exp_lib.offsets(field, cal.ys, cal.X, cal.D)  # (K, R, nx)
    _, m, pm = active_constraints(field, cal.ys, cal.X, cal.w)
    ys = cal.ys
    K, R = len(ys), cal.n
    sgn = np.where(np.arange(K) % 2 == 0, 1.0, -1.0)
    G = field.gy(xg[None, :], ys[:, None])  # (K, nx) side slope on the pass lines
    kk, jj = np.nonzero(pm)
    Fp = np.c_[0.5 * (G[kk, jj] + G[kk + 1, jj]), sgn[kk], xg[jj]]
    Yp = off[kk + 1, :, jj] - off[kk, :, jj]  # (P, R)
    k2, j2 = np.nonzero(m)
    Fs = np.c_[G[k2, j2], sgn[k2], xg[j2]]
    Ys = off[k2, :, j2]

    def sub(Fx, Y):
        idx = rng.choice(Y.size, size=min(n_gp, Y.size), replace=False)
        i, r = np.unravel_index(idx, Y.shape)
        return Fx[i], Y[i, r]

    return sub(Fp, Yp), sub(Fs, Ys)


def fit_gp_margin(field, cal, eps, n_gp=1000, pair_model="diff", use_mean=True, union=False, rng=None):
    """Fit the pair-difference and per-pass GPs on calibration data and build
    the GPMargin with z = Phi^{-1}(1-eps) (union=True: Phi^{-1}(1-eps/T))."""
    rng = np.random.default_rng(0) if rng is None else rng
    (Fp, yp), (Fs, ys_) = _gp_training(field, cal, n_gp, rng)
    seed = int(rng.integers(2 ** 31 - 1))
    gp_pair = _fit_gp(Fp, yp, seed) if pair_model == "diff" else None
    gp_pass = _fit_gp(Fs, ys_, seed)
    T = n_constraints(field, cal.ys, cal.w, "point")
    z = norm.ppf(1 - (eps / T if union else eps))
    model = GPMargin(gp_pair, gp_pass, z, w=cal.w, pair_model=pair_model, use_mean=use_mean)
    pred_sd = lambda g, Fx: float(np.median(g[0].predict((Fx - g[1]) / g[2], return_std=True)[1]))
    model.fit_info = dict(T=T, n_gp=len(yp), pair_kernel=str(gp_pair[0].kernel_) if gp_pair else None,
                          pass_kernel=str(gp_pass[0].kernel_), emp_sd_pair=float(np.std(yp)),
                          emp_sd_pass=float(np.std(ys_)),
                          gp_sd_pair=pred_sd(gp_pair, Fp) if gp_pair else None, gp_sd_pass=pred_sd(gp_pass, Fs))
    return model


def gp_margin(field, rng, eps, n_cal=100, w=W_DEFAULT, ctrl="lqr_i", n_gp=1000, pair_model="diff",
              use_mean=True, union=False, lam_ref=None, cal=None, info=False, **cond_kw):
    """Cautious-MPC style GP tightening (Hewing et al., TCST 2020).

    Returns (z, sig_fn): ys = core.plan(field, w, z, sig_fn) gives
    h_k = w/2 - z*sig_fn(field, y_k) with sig_fn in metres (sig_fn is a
    GPMargin; sig_fn.plan(field) is the exact per-constraint planner).  With
    info=True returns (z, sig_fn, dict).  union=False: individual chance
    constraints at eps each (the published cautious-MPC formulation); union=True:
    Bonferroni level eps/T (operation-level reading of the same method).
    cal / lam_ref / **cond_kw (incl. cond_fn) as in lindemann_cp_lambda."""
    t0 = time.time()
    cal = _get_cal(field, rng, n_cal, w, ctrl, lam_ref, cal, cond_kw)
    model = fit_gp_margin(field, cal, eps, n_gp=n_gp, pair_model=pair_model, use_mean=use_mean,
                          union=union, rng=rng)
    if not info:
        return model.z, model
    return model.z, model, dict(model.fit_info, z=model.z, n_runs=cal.n, K_ref=len(cal.ys),
                                lam_ref=cal.lam_ref, runtime_s=time.time() - t0)


def gp_plan(field, model, w=W_DEFAULT, max_passes=400, iters=6):
    """Exact cautious planner: every gap constraint tightened by its own GP
    predictive quantile (see module docstring)."""
    y_lo, y_hi = field.lateral_range()
    y = y_lo + w / 2
    for _ in range(iters):
        y = y_lo + w / 2 - model.boundary_tightening(field, y, 1.0, "lo")
    ys = [y]
    while True:
        k = len(ys) - 1
        d = 1.0 if k % 2 == 0 else -1.0
        if ys[-1] + w / 2 - model.boundary_tightening(field, ys[-1], d, "hi") >= y_hi - 1e-9:
            break
        yk = ys[-1]
        y = yk + w
        for _ in range(iters):
            y = yk + w - model.pair_tightening(field, yk, y, d)
        if y - yk < 0.2 * w:
            raise ValueError("infeasible erosion")
        ys.append(y)
        if len(ys) > max_passes:
            raise ValueError("too many passes")
    return np.array(ys)


# ------------------------------------------------------------------------ selftest
def selftest(n_cal=50, n_test=50, eps=0.1, w=W_DEFAULT, ctrl="lqr_i", seed=0, n_gp=800):
    """Two real paddy fields (the steepest and the median-slope one): every
    baseline calibrated on n_cal in-field runs of the nominal plan, CE-U
    (exp_lib.calibrate_conformal, fixed point, n_cal runs per iteration) for
    reference; each plan executed n_test times under common test conditions."""
    t_all = time.time()
    Fs = sorted(core.load_fields("paddy", w=w), key=lambda F: F.z_mean_slope)
    fields = [Fs[-1], Fs[len(Fs) // 2]]
    print(f"uncertainty baselines selftest: eps={eps}, w={w} m, ctrl={ctrl}, n_cal={n_cal} (nominal plan), "
          f"n_test={n_test}, {len(Fs)} paddy fields -> steepest + median slope")
    for F in fields:
        rng = np.random.default_rng(seed)
        t = time.time()
        cal = collect(F, rng, n_cal, w=w, ctrl=ctrl, lam_ref=0.0)
        t_cal = time.time() - t
        K0 = len(cal.ys)
        print(f"\nfield {F.fid}: main area {F.M.area:.0f} m2, mean slope {F.z_mean_slope:.2f} deg, nominal K={K0}, "
              f"calibration sim {t_cal:.2f} s")
        # ---- consistency checks
        Xg = pass_grids(F, cal.ys)
        assert all(len(a) == len(b) and np.allclose(a, b) for a, b in zip(Xg, cal.X)), "pass_grids != simulate X"
        ps = point_scores(F, cal)
        S, *_ = core.pair_scores(F, cal.ys, cal.X, cal.D, np.ones(K0), w=w)
        assert np.allclose(ps["scores"].max(axis=0), S), "pointwise max != core.pair_scores run score"
        assert ps["scores"].shape[0] == n_constraints(F, cal.ys, w, "point")
        P_pair = pair_sup_scores(F, cal)
        lam_pu = exp_lib.pair_union_lambda(P_pair.ravel(), eps, P_pair.shape[0])
        assert lam_pu == lindemann_cp_lambda(F, rng, eps, w=w, granularity="pair", cal=cal)
        assert cpp_mip_scalar(S, eps) == core.conformal_quantile(S, eps)
        c1 = collect(F, np.random.default_rng(7), 5, w=w, ctrl=ctrl)
        c2 = collect(F, np.random.default_rng(7), 5, w=w, ctrl=ctrl, cond_fn=lambda r, n: core.Condition(r, n))
        assert all(np.array_equal(a, b) for a, b in zip(c1.D, c2.D)), "cond_fn path != Condition-keyword path"
        for bad in (dict(lam_ref=0.05), dict(ctrl="stanley"), dict(rtk_scale=3.0)):
            try:
                cpp_lambda(F, rng, eps, w=w, cal=cal, **bad)
                raise AssertionError(f"shared cal accepted mismatching {bad}")
            except ValueError:
                pass

        meths = []  # (name, plan builder, lam shown, runtime of the UQ step)

        def add(name, lam, sig, rt, note=""):
            meths.append((name, (lambda lam=lam, sig=sig: core.plan(F, w, lam, sig)), lam, rt, note))

        add("Nominal (lam=0)", 0.0, UNIT, 0.0)
        for gran, pool, tc in [("point", True, "ref"), ("point", True, "final"), ("point", False, "ref"),
                               ("pair", True, "ref"), ("pair", False, "ref")]:
            lam, inf_ = lindemann_cp_lambda(F, rng, eps, w=w, granularity=gran, pool=pool, t_count=tc,
                                            cal=cal, info=True)
            note = f"T={inf_['T']}" + (f" needs n_cal>={inf_['n_required']}" if not np.isfinite(lam) else "")
            add(f"(a) Lindemann {gran}/{'pool' if pool else 'sep'}/{tc}", lam, UNIT, inf_["runtime_s"], note)
        for joint in ("max", "union"):
            lam, inf_ = cpp_lambda(F, rng, eps, w=w, joint=joint, cal=cal, info=True)
            note = f"J={inf_['J']}" + (f" needs n_cal>={inf_['n_required']}" if not np.isfinite(lam) else "")
            add(f"(b) CPP {joint} @ lam=0", lam, UNIT, inf_["runtime_s"], note)
        z, gpm, inf_ = gp_margin(F, rng, eps, w=w, n_gp=n_gp, pair_model="diff", cal=cal, info=True)
        print(f"  GP fit {inf_['runtime_s']:.1f} s on {inf_['n_gp']} pts: pair-diff sd emp/GP-median "
              f"{100 * inf_['emp_sd_pair']:.2f}/{100 * inf_['gp_sd_pair']:.2f} cm, pass sd emp/GP-median "
              f"{100 * inf_['emp_sd_pass']:.2f}/{100 * inf_['gp_sd_pass']:.2f} cm\n    pair kernel "
              f"{inf_['pair_kernel']}\n    pass kernel {inf_['pass_kernel']}")
        for tag, model in [("diff", gpm), ("indep", gpm.variant(pair_model="indep")),
                           ("diff+bonf", gpm.variant(eps=eps, union=True))]:
            add(f"(c) GP {tag} sig_fn", model.z, model, inf_["runtime_s"] if tag == "diff" else 0.0,
                f"z={model.z:.2f}" + (f" (eps/T, T={inf_['T']})" if "bonf" in tag else ""))
            meths.append((f"(c) GP {tag} exact", (lambda model=model: gp_plan(F, model, w)), model.z, 0.0,
                          "exact per-constraint planner"))
        t = time.time()
        qU, hist, _ = exp_lib.calibrate_conformal(lambda n: [(F, np.arange(n))], UNIT, eps, w, rng, lam0=0.03,
                                                  n_cal=n_cal, ctrl=ctrl)
        add("CE-U (exp_lib, fixed point)", qU, UNIT, time.time() - t, f"{len(hist)} iters x {n_cal} runs")

        print(f"  {'method':34s} {'lam/z':>8s} {'K':>3s} {'P(no miss)':>10s} {'E[miss]':>8s} {'overlap':>8s} "
              f"{'pt_viol':>8s} {'uq_s':>5s} {'eval_s':>6s}  note")
        for name, builder, lam, rt, note in meths:
            t = time.time()
            shown = (f"{100 * lam:6.2f}cm" if "(c)" not in name else f"{lam:8.2f}") if np.isfinite(lam) else "     inf"
            try:
                ys = builder()
            except ValueError as e:
                print(f"  {name:34s} {shown:>8s} {'-':>3s} {'infeasible':>10s} {'':8s} {'':8s} {'':8s} {rt:5.2f} "
                      f"{'':6s}  {note} ({e})")
                continue
            # same draws as exp_lib.evaluate_plan(F, ys, n_test, default_rng(seed + 1000)): common test conditions
            Xt, Dt, _ = exp_lib.run(F, ys, n_test, np.random.default_rng(seed + 1000), ctrl=ctrl, w=w)
            miss = core.evaluate(F, ys, Xt, Dt, w)
            pv = pointwise_violation(F, ys, Xt, Dt, w)
            print(f"  {name:34s} {shown:>8s} {len(ys):3d} {np.mean(miss == 0):10.2f} {miss.mean():8.5f} "
                  f"{exp_lib.overlap_ratio(F, ys, w):8.4f} {pv:8.5f} {rt:5.2f} {time.time() - t:6.2f}  {note}")
    print(f"\npt_viol = fraction of pointwise gap constraints violated on the test runs (what an individual chance "
          f"constraint at eps={eps} bounds); P(no miss) = operation-level coverage (target >= {1 - eps:.2f}).")
    print(f"checks passed (pass grids == simulate X; pointwise max == core.pair_scores S; pair/pool == "
          f"exp_lib.pair_union_lambda; CPP-MIP == core.conformal_quantile; cond_fn == Condition path; "
          f"mismatching shared cal rejected); total {time.time() - t_all:.1f} s")

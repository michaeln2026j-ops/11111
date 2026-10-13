"""Model-based uncertainty-aware coverage baselines (Gaussian belief / model MC).

These are the MODEL-BASED counterparts of the conformal certificate (CE-U,
exp_lib.calibrate_conformal): instead of a distribution-free quantile of the
observed run score, a parametric linear-Gaussian model of the execution error
is fitted to the calibration runs and the erosion lam is chosen so that the
MODEL-predicted probability of a coverage gap is <= eps.  They are expected to
be mis-calibrated when the real (heavy-tailed, earth-fixed, time-correlated)
RTK error and the per-run mounting bias violate the stationary-Gaussian /
short-memory assumptions; selftest() prints the model's own prediction next to
the true simulator outcome.

  belief_pointwise_lambda  (a-i)  per-point Gaussian chance constraint,
                                  lam = max_c (mu_c + z_{1-eps} sd_c)
  belief_rice_lambda       (a-ii) run-level Gaussian extreme-value correction:
                                  correction='rice' (default): discrete Rice /
                                  upcrossing bound on P(sup of an AR(1) segment
                                  > lam); correction='bonferroni': Bonferroni
                                  over the effective number of independent
                                  along-track samples n(1-rho)/(1+rho)
  model_mc_lambda          (b)    model-based Monte Carlo chance constraint: m
                                  synthetic operations drawn from the FITTED
                                  model (not from the simulator), smallest lam
                                  whose Clopper-Pearson lower bound on
                                  P(no miss) is >= 1-eps

Units and interface (identical to baselines/uncertainty.py): every function
returns an erosion lam in METRES for the uniform sigma UNIT =
exp_lib.ConstSigma(1.0), ys = core.plan(F, w, lam, UNIT) (pass spacing
w - 2*lam); with info=True a (lam, dict) tuple.  lam = inf means "no finite
lam satisfies the model constraint" (core.plan then raises
ValueError("infeasible erosion")).

=============================================================================
References (verified by web search on 2026-10-13; what could NOT be verified
is stated explicitly)
=============================================================================
Uncertainty-aware coverage / belief-space coverage (the modelling idea):
  [P14] L. Paull, M. Seto and H. Li, "Area coverage planning that accounts for
        pose uncertainty with an AUV seabed surveying application," Proc. IEEE
        Int. Conf. Robotics and Automation (ICRA), 2014, pp. 6592-6599,
        doi:10.1109/ICRA.2014.6907832.  (IEEE Xplore document 6907832.)
        Pose estimates (EKF) are mapped through the coverage-sensor model to a
        PROBABILITY OF COVERAGE over a discretised workspace (per cell), which
        then drives entropy-reduction path planning.
  [P18] L. Paull, M. Seto, J. J. Leonard and H. Li, "Probabilistic cooperative
        mobile robot area coverage and its application to autonomous seabed
        mapping," Int. J. Robotics Research, vol. 37, no. 1, pp. 21-45, 2018.
        (Volume/issue/pages confirmed by several citing papers; the DOI
        10.1177/0278364917741969 appears in one listing (ACM DL) only and is
        therefore not asserted here.)  NOTE: the task brief attributed this
        title to "ICRA 2014"; the ICRA 2014 paper is [P14], the title belongs
        to the IJRR 2018 journal paper.
  [S19] R. Schirmer, P. Biber and C. Stachniss, "Coverage Path Planning in
        Belief Space," Proc. IEEE ICRA, 2019, pp. 7604-7610.  (Authors, title,
        venue, year confirmed on the University of Bonn publication page,
        pages from DBLP; DOI not found and omitted.)  Plans a coverage path
        of PARALLEL LANES that accounts for the robot's localisation/execution
        uncertainty (belief), estimated from a map of localisability.
  As far as could be verified (abstracts, project pages, figure captions;
  full texts were not retrievable here), neither paper certifies a run-level
  (joint over the whole operation) no-gap probability: [P14] works with a
  per-cell probability of coverage, [S19] with per-location belief -- the
  per-point tightening of variant (a-i).  The Gaussian AR(1) error model
  below is our data-driven stand-in for their filter-propagated belief.
Gaussian chance constraints for linear-Gaussian models / sample approximation:
  [B11] L. Blackmore, M. Ono and B. C. Williams, "Chance-Constrained Optimal
        Path Planning With Obstacles," IEEE Trans. Robotics, vol. 27, no. 6,
        pp. 1080-1094, Dec. 2011, doi:10.1109/TRO.2011.2161160.  Bounds on
        the violation probability of linear-Gaussian systems turn the chance
        constraint into deterministic tightened constraints.
  [B10] L. Blackmore, M. Ono, A. Bektassov and B. C. Williams, "A Probabilistic
        Particle-Control Approximation of Chance-Constrained Stochastic
        Predictive Control," IEEE Trans. Robotics, vol. 26, no. 3, pp. 502-517,
        June 2010, doi:10.1109/TRO.2010.2044948.  The state distribution is
        represented by particles drawn from the (assumed known) stochastic
        MODEL; the chance constraint is approximated by the fraction of
        particles that satisfy it -> (b).
Extreme-value correction:
  [R44] S. O. Rice, "Mathematical analysis of random noise," Bell System
        Technical Journal, vol. 23, no. 3, pp. 282-332, 1944, and vol. 24,
        no. 1, pp. 46-156, 1945 (doi:10.1002/j.1538-7305.1944.tb00874.x,
        doi:10.1002/j.1538-7305.1945.tb00453.x).  Expected number of
        upcrossings of a level by a Gaussian process.
  [L83] M. R. Leadbetter, G. Lindgren and H. Rootzen, Extremes and Related
        Properties of Random Sequences and Processes, Springer Series in
        Statistics, 1983, doi:10.1007/978-1-4612-5449-2 (extremes and
        upcrossings of dependent sequences and of continuous-time processes).
  [O56] D. B. Owen, "Tables for computing bivariate normal probabilities,"
        Ann. Math. Statist., vol. 27, no. 4, pp. 1075-1090, 1956 (Owen's T).
  [ZvS95] F. W. Zwiers and H. von Storch, "Taking serial correlation into
        account in tests of the mean," J. Climate, vol. 8, pp. 336-351, 1995
        (verified through secondary sources, e.g. NCL's equiv_sample_size,
        which cites it for the AR(1) equivalent sample size n(1-r1)/(1+r1)).
  [CP34] C. J. Clopper and E. S. Pearson, "The use of confidence or fiducial
        limits illustrated in the case of the binomial," Biometrika, vol. 26,
        pp. 404-413, 1934, doi:10.2307/2331986.

=============================================================================
Model (fitted by moments on in-field calibration runs)
=============================================================================
Constraints (as in baselines/uncertainty.py; e_k(x) = field-frame lateral
offset of pass k on the 1 m grid and main-area mask of core.pair_scores):
    pair k:      r_k(x) = (e_{k+1}(x) - e_k(x)) / 2 <= lam
    boundary 1:  e_1(x) <= lam,      boundary N:  -e_N(x) <= lam
and the operation has no gap iff all hold at every active x (the max of all
constraint values is the run score S of core.pair_scores(..., sig = 1),
checked in selftest).
Linear-Gaussian model: three constraint classes c in {pair, b1, bN} (all
pass-to-pass pairs pooled; boundary e_1; boundary -e_N); every contiguous
active segment of every constraint is an independent stationary Gaussian
AR(1) sequence along track (1 m step),
    r(x) = mu_c + sd_c * u(x),  u(x+1) = rho_c u(x) + sqrt(1 - rho_c^2) n(x),
independent across pairs, boundaries and runs.  Moment (Yule-Walker) fit
over all calibration points of the class: mu_c = mean, sd_c^2 = variance
about mu_c, rho_c = lag-1 autocovariance / sd_c^2 (lag pairs within a
contiguous segment only).  This is the "pass-to-pass difference process" of
the brief; the boundary classes are the same model for the single-pass
offsets e_1 and -e_N (boundary='pooled' fits one class for both).
Diagnostics returned: excess kurtosis, empirical lag-h autocorrelation vs
rho^h, empirical vs Gaussian tail exceedances.

(a-i) pointwise:  P(r(x) > lam) <= eps at every point under the model, i.e.
      lam = max_c (mu_c + Phi^{-1}(1 - eps) sd_c).  Geometry-free.
(a-ii) run level: P(any gap in the operation) <= eps under the model.  For a
      segment of n samples with standardised level h = (lam - mu)/sd, the
      event {max > h} is contained in {u_1 > h} U {upcrossing at some t}, so
      (discrete Rice / upcrossing bound [R44, L83], exact inequality):
          P(max_{t<=n} u_t > h) <= Q(h) + (n - 1) P(u_t <= h < u_{t+1}),
          P(u_t <= h < u_{t+1}) = Phi(h) - Phi_2(h, h; rho) = 2 T(h, a),
          a = sqrt((1 - rho)/(1 + rho))                      (Owen's T [O56])
      and the run-level probability is 1 - prod_j (1 - p_j) over all segments
      j of the plan (independence is part of the model).  The discrete form is
      used because the continuous-time limit of an AR(1) (Ornstein-Uhlenbeck)
      is not mean-square differentiable, so the continuous Rice formula gives
      an infinite upcrossing rate; the gap is checked on the 1 m grid of
      core.evaluate, so the discrete maximum is exactly the target.
      correction='bonferroni': p_j = n_eff,j Q(h), n_eff = clip(n (1-rho)/
      (1+rho), 1, n) (AR(1) equivalent sample size [ZvS95]), combined by the
      Bonferroni sum sum_j p_j <= eps (i.e. z = Phi^{-1}(1 - eps/N_eff) when
      all segments share one class).  CAUTION: n_eff is the equivalent sample
      size for the MEAN of an AR(1); for its MAXIMUM it undercounts (stationary
      Gaussian sequences with r_n log n -> 0, e.g. AR(1), have the i.i.d.
      asymptotic maximum: Berman's condition, [L83] ch. 4), so this heuristic is
      anti-conservative even w.r.t. its own model (selftest: model-predicted
      P(no miss) ~0.35-0.45 at eps = 0.1).  'rice' is a true model bound.
(b) model-based MC chance constraint [B10] + [CP34]: m (default 2000)
      synthetic operations are simulated FROM THE FITTED MODEL with the
      segment geometry of the plan; S_syn = max over all segments and samples
      of the synthetic constraint values; lam = smallest S_syn-order
      statistic s_(c) such that the one-sided Clopper-Pearson lower
      confidence bound (confidence conf, default 0.95) on P(S <= lam) with c
      successes out of m is >= 1 - eps (valid for the data-dependent order
      statistic: F(s_(c)) ~ Beta(c, m - c + 1)).  m is raised to
      max(m, ceil(10/eps)) (doubled further if still needed) so that small eps
      remain certifiable instead of returning inf.  The certificate is valid
      FOR THE MODEL only ("model-based MC certification"), not for the real
      process.

Adaptation decisions
  * Calibration data: n_cal in-field runs of the nominal plan pi(lam_ref=0)
    (baselines.uncertainty.collect; pass cal= to share runs between the three
    functions).  Same calibration protocol as the other UQ baselines.
  * Decision dependence of the geometry (not of the error law): the model is
    stationary, so the plan only enters through the number/length of the
    constraint segments of the plan actually executed.  (a-ii) and (b) use a
    fixed-point iteration lam_0 = 0, lam_{i+1} = lam_req(geometry of
    core.plan(lam_i)), stopped when lam_req(plan(lam_i)) <= lam_i; the
    returned lam is thus certified (under the model) for its own plan.  No
    re-simulation is needed (a model-based method would not re-calibrate).
  * One stationary model per class pooled over all pairs/positions (no slope
    regressor): the belief papers propagate one localisation covariance;
    position-dependent tightening is the GP baseline in uncertainty.py.
    The two boundaries are separate classes (default boundary='split'): their
    means differ by the DEM-driven residual roll offset h_ant (1 - c) g_y at
    the two field edges (up to ~4.5 cm between e_1 and -e_N on side-slope
    paddies), so pooling them violates the model's own stationarity and
    misallocates the risk between the edges.  The pair class needs no split:
    the slope offset is common to adjacent passes in the field frame and
    cancels in e_{k+1} - e_k (pooled pair means ~0, spread < 1 cm).
  * rho is the lag-1 Yule-Walker estimate (the moment estimator of an AR(1)).
    The executed offsets are smooth at 1 m (controller dynamics) and
    decorrelate faster than rho^h at lags ~5 m (acf 0.4 vs 0.8), so this fit
    over-states the correlation length and somewhat under-counts extremes;
    matching rho to the lag-5 acf instead raises the Rice lam by ~0.4-0.6 cm
    on the selftest fields (checked in review).  Kept as specified.
  * Pass-to-pass cross-correlation (shared pass between adjacent pairs, the
    alternating per-run mounting bias) is NOT modelled: segments are
    independent, as in pointwise belief planning.  The AR(1) is fitted at lag
    1 only, so the long-memory part of the RTK error and the per-run constant
    bias are under-represented at long lags (diagnostic printed).
  * Uses only the recorded field-frame offsets of calibration runs (what an
    RTK-logged calibration provides); never cond.k_s / OU state / comp /
    mount / the RTK series.
"""
import math
import time

import numpy as np
from scipy.special import owens_t
from scipy.stats import beta as beta_dist
from scipy.stats import kurtosis, norm

import core
import exp_lib
from baselines import uncertainty as U

W_DEFAULT = exp_lib.W_DEFAULT
UNIT = exp_lib.ConstSigma(1.0)  # uniform sigma: h_k = w/2 - lam

__all__ = ["UNIT", "GEOM_KEYS", "GaussAR1", "BeliefModel", "fit_belief_model", "constraint_segments",
           "belief_pointwise_lambda", "belief_rice_lambda", "model_mc_lambda", "cp_lower", "selftest"]


# ------------------------------------------------------------------ AR(1) class model
class GaussAR1:
    """Stationary Gaussian AR(1) sequence on the 1 m along-track grid."""

    def __init__(self, mu, sd, rho):
        self.mu, self.sd = float(mu), float(max(sd, 1e-9))
        self.rho = float(np.clip(rho, -0.999, 0.999))

    def __repr__(self):
        return f"GaussAR1(mu={100 * self.mu:.3f} cm, sd={100 * self.sd:.3f} cm, rho={self.rho:.4f})"

    def h(self, lam):
        return (lam - self.mu) / self.sd

    def p_point(self, lam):
        return float(norm.sf(self.h(lam)))

    def upcross(self, lam):
        """P(u_t <= h < u_{t+1}) = 2 T(h, sqrt((1-rho)/(1+rho)))  (Owen's T)."""
        a = math.sqrt((1.0 - self.rho) / (1.0 + self.rho))
        return float(2.0 * owens_t(self.h(lam), a))

    def p_sup(self, lam, n, correction="rice"):
        """Bound on P(max over a segment of n samples > lam) (vector n)."""
        n = np.asarray(n, float)
        if correction == "rice":
            p = norm.sf(self.h(lam)) + (n - 1.0) * self.upcross(lam)
        elif correction == "bonferroni":
            p = self.n_eff(n) * norm.sf(self.h(lam))
        else:
            raise ValueError("correction must be 'rice' or 'bonferroni'")
        return np.minimum(p, 1.0)

    def n_eff(self, n):
        return np.clip(np.asarray(n, float) * (1.0 - self.rho) / (1.0 + self.rho), 1.0, np.asarray(n, float))


def _segments(mask_row):
    """Contiguous runs of True in a boolean row -> list of index arrays."""
    j = np.flatnonzero(mask_row)
    if len(j) == 0:
        return []
    br = np.flatnonzero(np.diff(j) > 1)
    st, en = np.r_[0, br + 1], np.r_[br + 1, len(j)]
    return [j[s:e] for s, e in zip(st, en)]


GEOM_KEYS = ("pair", "b1", "bN")  # constraint groups: pass-to-pass pairs, boundary e_1, boundary -e_N


def constraint_segments(field, ys, w=W_DEFAULT):
    """Lengths (samples) of the contiguous constraint segments of plan ys, per
    constraint group: dict(pair=[...], b1=[...], bN=[...]) -- computed from the
    plan geometry alone (pass grids identical to core.simulate, mask of
    core.pair_scores)."""
    _, m, pm = U.active_constraints(field, ys, U.pass_grids(field, ys), w)
    pair = [len(s) for k in range(pm.shape[0]) for s in _segments(pm[k])]
    b1 = [len(s) for s in _segments(m[0])]
    bN = [len(s) for s in _segments(m[-1])]
    return dict(pair=np.array(pair, int), b1=np.array(b1, int), bN=np.array(bN, int))


# ------------------------------------------------------------------- fitted model
class BeliefModel:
    """Stationary Gaussian AR(1) model per constraint group: 'pair' (all
    pass-to-pass half-differences, pooled), 'b1' (e_1) and 'bN' (-e_N).
    bN=None pools both boundaries into one class (boundary='pooled')."""

    def __init__(self, pair, b1, bN=None, diag=None):
        self.pooled = bN is None
        self.cls = dict(pair=pair, b1=b1, bN=b1 if bN is None else bN)
        self.diag = diag or {}

    def classes(self):
        """Distinct fitted classes (name -> GaussAR1)."""
        return dict(pair=self.cls["pair"], bnd=self.cls["b1"]) if self.pooled else dict(self.cls)

    def __repr__(self):
        return "BeliefModel(" + ", ".join(f"{k}={v}" for k, v in self.classes().items()) + ")"

    def pointwise_lambda(self, eps):
        z = norm.ppf(1.0 - eps)
        return max(c.mu + z * c.sd for c in self.cls.values())

    def p_gap(self, lam, geom, correction="rice"):
        """Model bound on P(any gap) of an operation with segment geometry geom."""
        ps = [self.cls[c].p_sup(lam, geom[c], correction) for c in GEOM_KEYS if len(geom.get(c, ()))]
        p = np.concatenate(ps) if ps else np.zeros(0)
        if correction == "rice":
            return float(1.0 - np.prod(1.0 - p))
        return float(min(1.0, p.sum()))

    def required_lambda(self, geom, eps, correction="rice", tol=1e-7):
        """Smallest lam with p_gap(lam, geom) <= eps (bisection; monotone for
        lam >= max mu_c over the groups present, and p_gap >= 1/2 > eps below
        that for eps < 1/2; for eps >= 1/2 the returned lam is conservative)."""
        used = [self.cls[c] for c in GEOM_KEYS if len(geom.get(c, ()))] or list(self.cls.values())
        lo = max(c.mu for c in used)
        hi = lo + 40.0 * max(c.sd for c in used)
        if self.p_gap(hi, geom, correction) > eps:
            return np.inf
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if self.p_gap(mid, geom, correction) <= eps:
                hi = mid
            else:
                lo = mid
            if hi - lo < tol:
                break
        return float(hi)

    def synthetic_scores(self, geom, m, seed):
        """Run scores of m synthetic operations drawn from the fitted model
        (max over all segments and samples of the constraint values)."""
        rng = np.random.default_rng(seed)
        mu, sd, rho, n = [], [], [], []
        for c in GEOM_KEYS:
            for L in geom.get(c, ()):
                g = self.cls[c]
                mu.append(g.mu), sd.append(g.sd), rho.append(g.rho), n.append(L)
        mu, sd, rho, n = (np.array(a, float) for a in (mu, sd, rho, n))
        if len(n) == 0:
            return np.full(m, -np.inf)
        s = np.sqrt(1.0 - rho ** 2)
        u = rng.standard_normal((m, len(n)))
        best = mu + sd * u
        for t in range(1, int(n.max())):
            u = rho * u + s * rng.standard_normal(u.shape)
            act = t < n
            best[:, act] = np.maximum(best[:, act], (mu + sd * u)[:, act])
        return best.max(axis=1)


def _class_moments(series):
    """series: list of (R, n_seg) arrays.  Yule-Walker / moment fit."""
    v = np.concatenate([s.ravel() for s in series])
    if not np.isfinite(v).all():
        raise ValueError("non-finite calibration offsets on active constraints")
    mu = v.mean()
    var = np.mean((v - mu) ** 2)
    num = sum(((s[:, 1:] - mu) * (s[:, :-1] - mu)).sum() for s in series if s.shape[1] > 1)
    cnt = sum(s[:, 1:].size for s in series if s.shape[1] > 1)
    rho = num / max(cnt, 1) / var if var > 0 else 0.0

    def acf(h):
        nm = sum(((s[:, h:] - mu) * (s[:, :-h] - mu)).sum() for s in series if s.shape[1] > h)
        ct = sum(s[:, h:].size for s in series if s.shape[1] > h)
        return nm / ct / var if ct else np.nan

    g = GaussAR1(mu, math.sqrt(var), rho)
    zs = (v - mu) / g.sd
    diag = dict(n_points=int(v.size), n_series=int(sum(s.shape[0] for s in series)),
                excess_kurtosis=float(kurtosis(v)),
                acf={h: (float(acf(h)), float(g.rho ** h)) for h in (1, 5, 20, 50)},
                tail={z: (float(np.mean(zs > z)), float(norm.sf(z))) for z in (2.0, 3.0, 4.0)})
    return g, diag


def fit_belief_model(field, cal, boundary="split"):
    """Fit the Gaussian AR(1) class model on calibration runs `cal`
    (baselines.uncertainty.CalData).  boundary='split' (default): separate
    classes for e_1 and -e_N (their means differ by the DEM-driven roll offset
    h (1 - c) g at the two field edges); 'pooled': one boundary class."""
    if boundary not in ("split", "pooled"):
        raise ValueError("boundary must be 'split' or 'pooled'")
    xg, off = exp_lib.offsets(field, cal.ys, cal.X, cal.D)  # (K, R, nx)
    _, m, pm = U.active_constraints(field, cal.ys, cal.X, cal.w)
    pair = []
    for k in range(pm.shape[0]):
        for j in _segments(pm[k]):
            pair.append((off[k + 1][:, j] - off[k][:, j]) / 2.0)
    b1 = [off[0][:, j] for j in _segments(m[0])]
    bN = [-off[-1][:, j] for j in _segments(m[-1])]
    gp, dp = _class_moments(pair)
    diag = dict(pair=dp, n_runs=cal.n, K_ref=len(cal.ys), lam_ref=cal.lam_ref, fid=field.fid,
                heading_deg=field.meta.get("heading_deg"), w=cal.w, boundary=boundary)
    if boundary == "pooled":
        gb, diag["bnd"] = _class_moments(b1 + bN)
        return BeliefModel(gp, gb, None, diag)
    g1, diag["b1"] = _class_moments(b1)
    gN, diag["bN"] = _class_moments(bN)
    return BeliefModel(gp, g1, gN, diag)


# ------------------------------------------------------------------ helpers
def cp_lower(c, m, conf=0.95):
    """One-sided Clopper-Pearson lower confidence bound for a binomial
    proportion with c successes out of m (confidence conf)."""
    c = np.asarray(c)
    return np.where(c > 0, beta_dist.ppf(1.0 - conf, np.maximum(c, 1), m - c + 1), 0.0)


def _cp_min_count(m, eps, conf):
    """Smallest c in 1..m with cp_lower(c, m) >= 1 - eps (None if none);
    cp_lower is increasing in c, so binary search."""
    if cp_lower(m, m, conf) < 1.0 - eps:
        return None
    lo, hi = 0, m  # cp_lower(lo) < 1-eps <= cp_lower(hi)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if cp_lower(mid, m, conf) >= 1.0 - eps:
            hi = mid
        else:
            lo = mid
    return int(hi)


def _get_model(field, rng, n_cal, w, ctrl, lam_ref, cal, model, cond_kw, boundary="split"):
    if model is not None:
        d = model.diag
        if "fid" in d and (d["fid"] != field.fid or d.get("heading_deg") != field.meta.get("heading_deg")):
            raise ValueError("model was fitted on a different field / heading (in-field setting)")
        if "w" in d and d["w"] != w:
            raise ValueError(f"model was fitted on calibration runs with w={d['w']}, not w={w}")
        if cond_kw:
            raise ValueError(f"condition arguments {sorted(cond_kw)} are ignored when model= is given")
        return model, None
    cal = U._get_cal(field, rng, n_cal, w, ctrl, lam_ref, cal, cond_kw)
    return fit_belief_model(field, cal, boundary=boundary), cal


def _fixed_point(field, w, req_fn, iters=30):
    """lam_0 = 0, lam_{i+1} = req(geometry(plan(lam_i))) until req <= lam_i."""
    lam, hist = 0.0, []
    for _ in range(iters):
        try:
            ys = core.plan(field, w, lam, UNIT)
        except ValueError:
            hist.append((lam, None, np.inf))
            return np.inf, hist
        req = req_fn(constraint_segments(field, ys, w))
        hist.append((lam, len(ys), req))
        if req <= lam + 1e-9:
            return lam, hist
        if not np.isfinite(req):
            return np.inf, hist
        lam = req
    import warnings
    warnings.warn("belief fixed point did not converge; returning the largest requirement seen")
    return max(h[2] for h in hist), hist


# ------------------------------------------------------------------ (a-i) pointwise
def belief_pointwise_lambda(field, rng, eps, n_cal=100, w=W_DEFAULT, ctrl="lqr_i", lam_ref=0.0, cal=None,
                            model=None, info=False, boundary="split", **cond_kw):
    """Gaussian belief, pointwise: lam = max_c (mu_c + Phi^{-1}(1-eps) sd_c),
    i.e. every along-track point has model gap probability <= eps (no
    run-level correction, as in per-cell / per-lane belief coverage).
    Returns lam [m] for core.plan(field, w, lam, UNIT) (and dict if info)."""
    t0 = time.time()
    model, _ = _get_model(field, rng, n_cal, w, ctrl, lam_ref, cal, model, cond_kw, boundary)
    lam = float(model.pointwise_lambda(eps))
    if not info:
        return lam
    return lam, dict(model=model, z=float(norm.ppf(1 - eps)), runtime_s=time.time() - t0)


# ------------------------------------------------------------- (a-ii) run level
def belief_rice_lambda(field, rng, eps, n_cal=100, w=W_DEFAULT, ctrl="lqr_i", correction="rice", lam_ref=0.0,
                       cal=None, model=None, info=False, boundary="split", **cond_kw):
    """Gaussian belief with a run-level extreme-value correction: smallest lam
    whose MODEL bound on P(any gap over the operation) is <= eps, for the
    segment geometry of the plan core.plan(field, w, lam, UNIT) itself
    (fixed point).  correction: 'rice' (discrete Rice/upcrossing bound per
    AR(1) segment, independent segments) or 'bonferroni' (Bonferroni over
    the AR(1) effective number of independent samples)."""
    t0 = time.time()
    model, _ = _get_model(field, rng, n_cal, w, ctrl, lam_ref, cal, model, cond_kw, boundary)
    lam, hist = _fixed_point(field, w, lambda g: model.required_lambda(g, eps, correction))
    if not info:
        return lam
    return lam, dict(model=model, correction=correction, hist=hist, K=hist[-1][1],
                     p_gap_model=(model.p_gap(lam, constraint_segments(field, core.plan(field, w, lam, UNIT), w),
                                              correction) if np.isfinite(lam) else np.nan),
                     runtime_s=time.time() - t0)


# ------------------------------------------------------- (b) model-based MC
def model_mc_lambda(field, rng, eps, n_cal=100, w=W_DEFAULT, ctrl="lqr_i", m=2000, conf=0.95, lam_ref=0.0,
                    cal=None, model=None, info=False, boundary="split", **cond_kw):
    """Model-based MC chance constraint: m synthetic operations drawn from the
    FITTED Gaussian AR(1) model (segment geometry of the executed plan, fixed
    point over lam), lam = smallest synthetic run-score order statistic whose
    one-sided Clopper-Pearson lower bound (confidence conf) on P(no miss) is
    >= 1-eps.  Valid for the model only.  Common random numbers (one seed
    drawn from rng) across fixed-point iterations.  m is raised to
    max(m, ceil(10/eps)) (then doubled while needed) so that the CP bound can
    reach 1-eps with some failures left (m_used is reported in the dict)."""
    t0 = time.time()
    model, _ = _get_model(field, rng, n_cal, w, ctrl, lam_ref, cal, model, cond_kw, boundary)
    m = max(int(m), int(math.ceil(10.0 / eps)))
    c_min = _cp_min_count(m, eps, conf)
    while c_min is None and m < 2 ** 22:
        m *= 2
        c_min = _cp_min_count(m, eps, conf)
    seed = int(rng.integers(2 ** 62))
    if c_min is None:
        lam, hist = np.inf, []
    else:
        def req(g):
            S = np.sort(model.synthetic_scores(g, m, seed))
            return float(S[c_min - 1])

        lam, hist = _fixed_point(field, w, req)
    if not info:
        return lam
    return lam, dict(model=model, m=m, m_used=m, conf=conf, c_min=c_min, cp_lower=float(cp_lower(c_min, m, conf))
                     if c_min else np.nan, hist=hist, K=hist[-1][1] if hist else None, seed=seed,
                     runtime_s=time.time() - t0)


# ------------------------------------------------------------------ selftest
def selftest(n_cal=50, n_test=50, eps=0.1, w=W_DEFAULT, ctrl="lqr_i", seed=0, m=2000):
    """Two real paddy fields (steepest and median mean slope, as in
    baselines.uncertainty.selftest): the three model-based baselines and the
    Bonferroni variant, all fitted on the same n_cal in-field runs of the
    nominal plan; CE-U (exp_lib.calibrate_conformal, fixed point, n_cal runs
    per iteration) for reference; every plan executed n_test times under
    common test conditions.  P_model = MODEL-predicted P(no miss) of the plan
    (model MC, m operations) vs the simulator's P(no miss)."""
    t_all = time.time()
    # ---- unit checks of the extreme-value machinery (no simulation)
    from scipy.stats import multivariate_normal
    for h, rho in [(1.0, 0.5), (2.0, 0.9), (-0.5, 0.3), (0.0, 0.7)]:
        g = GaussAR1(0.0, 1.0, rho)
        ref = norm.cdf(h) - multivariate_normal(mean=[0, 0], cov=[[1, rho], [rho, 1]]).cdf([h, h])
        assert abs(g.upcross(h) - ref) < 2e-5, (h, rho, g.upcross(h), ref)
    g = GaussAR1(0.01, 0.02, 0.9)
    mdl = BeliefModel(g, g, g)
    geom = dict(pair=np.array([60, 80, 100]), b1=np.array([60]), bN=np.array([], int))
    Ssyn = mdl.synthetic_scores(geom, 20000, 1)
    for lam in (0.04, 0.06):
        p_mc, p_rice = np.mean(Ssyn > lam), mdl.p_gap(lam, geom, "rice")
        se = math.sqrt(p_mc * (1 - p_mc) / len(Ssyn))
        assert p_rice >= p_mc - 3 * se, (lam, p_rice, p_mc)
    one = mdl.synthetic_scores(dict(pair=np.array([1])), 20000, 2)
    assert abs(one.mean() - 0.01) < 5e-4 and abs(one.std() - 0.02) < 5e-4
    assert abs(mdl.p_gap(0.06, dict(pair=np.array([1]))) - norm.sf(2.5)) < 1e-12
    for mm, ee in ((2000, 0.1), (500, 0.05), (3000, 0.001)):  # binary-search CP count == brute force
        cs = np.arange(1, mm + 1)
        ok = cp_lower(cs, mm) >= 1 - ee
        assert _cp_min_count(mm, ee, 0.95) == (int(cs[np.argmax(ok)]) if ok.any() else None)
    print(f"belief baselines selftest: eps={eps}, w={w} m, ctrl={ctrl}, n_cal={n_cal} (nominal plan), "
          f"n_test={n_test}, model MC m={m}")
    print("  unit checks: Owen-T upcrossing == Phi - Phi2 (scipy); Rice bound >= model MC exceedance "
          f"(lam 4/6 cm: {mdl.p_gap(0.04, geom):.3f}>={np.mean(Ssyn > 0.04):.3f}, "
          f"{mdl.p_gap(0.06, geom):.4f}>={np.mean(Ssyn > 0.06):.4f}); AR(1) sampler moments OK; CP count OK")
    Fs = sorted(core.load_fields("paddy", w=w), key=lambda F: F.z_mean_slope)
    fields = [Fs[-1], Fs[len(Fs) // 2]]
    for F in fields:
        rng = np.random.default_rng(seed)
        t = time.time()
        cal = U.collect(F, rng, n_cal, w=w, ctrl=ctrl, lam_ref=0.0)
        t_cal = time.time() - t
        t = time.time()
        model = fit_belief_model(F, cal)
        t_fit = time.time() - t
        model_pool = fit_belief_model(F, cal, boundary="pooled")
        K0 = len(cal.ys)
        S0, *_ = core.pair_scores(F, cal.ys, cal.X, cal.D, np.ones(K0), w=w)
        ps = U.point_scores(F, cal)
        assert np.allclose(ps["scores"].max(axis=0), S0)
        geo0 = constraint_segments(F, cal.ys, w)
        assert sum(geo0[c].sum() for c in GEOM_KEYS) == ps["scores"].shape[0], "segment count != constraint count"
        print(f"\nfield {F.fid}: main area {F.M.area:.0f} m2, mean slope {F.z_mean_slope:.2f} deg, nominal K={K0}, "
              f"calibration sim {t_cal:.2f} s, model fit {t_fit:.3f} s")
        for c, gc in list(model.classes().items()) + [("bnd*", model_pool.cls["b1"])]:
            d = model.diag[c] if c in model.diag else model_pool.diag["bnd"]
            acf = ", ".join(f"{h}:{a:.2f}/{b:.2f}" for h, (a, b) in d["acf"].items())
            tail = ", ".join(f"z>{z:g}:{a:.4f}/{b:.4f}" for z, (a, b) in d["tail"].items())
            print(f"  {c:4s} {gc}  n={d['n_points']} pts/{d['n_series']} series, excess kurtosis "
                  f"{d['excess_kurtosis']:.2f}\n       acf emp/AR(1) lag {acf}\n       tail emp/Gauss {tail}")
        print("  (bnd* = e_1 and -e_N pooled into one class, boundary='pooled'; only used for the * row)")
        meths = []
        lam_pw, i_pw = belief_pointwise_lambda(F, rng, eps, model=model, info=True)
        assert abs(lam_pw - max(c.mu + norm.ppf(1 - eps) * c.sd for c in model.cls.values())) < 1e-12
        meths.append(("(a-i) belief pointwise z_{1-eps}", lam_pw, i_pw["runtime_s"], f"z={i_pw['z']:.2f}", model))
        for corr in ("rice", "bonferroni"):
            lam_r, i_r = belief_rice_lambda(F, rng, eps, model=model, correction=corr, info=True)
            meths.append((f"(a-ii) belief run-level {corr}", lam_r, i_r["runtime_s"],
                          f"fixed pt {len(i_r['hist'])} it, model P(gap)<={i_r['p_gap_model']:.3f}", model))
        lam_r, i_r = belief_rice_lambda(F, rng, eps, model=model_pool, info=True)
        meths.append(("(a-ii) rice, pooled boundary *", lam_r, i_r["runtime_s"],
                      f"fixed pt {len(i_r['hist'])} it, model* P(gap)<={i_r['p_gap_model']:.3f}", model_pool))
        lam_mc, i_mc = model_mc_lambda(F, rng, eps, m=m, model=model, info=True)
        meths.append(("(b) model-based MC chance constr.", lam_mc, i_mc["runtime_s"],
                      f"c>={i_mc['c_min']}/{i_mc['m_used']}, CP-LB {i_mc['cp_lower']:.4f}, {len(i_mc['hist'])} it",
                      model))
        t = time.time()
        qU, hist, _ = exp_lib.calibrate_conformal(lambda n: [(F, np.arange(n))], UNIT, eps, w, rng, lam0=0.03,
                                                  n_cal=n_cal, ctrl=ctrl)
        meths.append(("CE-U (exp_lib, fixed point)", qU, time.time() - t, f"{len(hist)} iters x {n_cal} runs", model))
        print(f"  {'method':36s} {'lam':>8s} {'K':>3s} {'P_model':>7s} {'P(no miss)':>10s} {'E[miss]':>8s} "
              f"{'overlap':>8s} {'uq_s':>6s}  note")
        for name, lam, rt, note, mdl_i in [("Nominal (lam=0)", 0.0, 0.0, "", model)] + meths:
            shown = f"{100 * lam:6.2f}cm" if np.isfinite(lam) else "     inf"
            try:
                ys = core.plan(F, w, lam, UNIT)
            except ValueError as e:
                print(f"  {name:36s} {shown:>8s} {'-':>3s} {'':7s} {'infeasible':>10s}  {note} ({e})")
                continue
            Sm = mdl_i.synthetic_scores(constraint_segments(F, ys, w), m, seed + 99)
            p_model = float(np.mean(Sm <= lam))
            r = exp_lib.evaluate_plan(F, ys, n_test, np.random.default_rng(seed + 1000), w=w, ctrl=ctrl)
            print(f"  {name:36s} {shown:>8s} {r['passes']:3d} {p_model:7.3f} {r['p_nomiss']:10.2f} "
                  f"{r['e_miss']:8.5f} {r['overlap']:8.4f} {rt:6.2f}  {note}")
    print(f"\nchecks passed (Owen-T upcrossing; Rice >= model MC; sampler moments; CP count; pointwise max == "
          f"core.pair_scores S; segment count == constraint count); total {time.time() - t_all:.1f} s")


if __name__ == "__main__":
    selftest()

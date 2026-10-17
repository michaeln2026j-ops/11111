"""Sequential pass-to-pass guidance ("follow the previous executed pass") baseline.

What the baseline is
--------------------
The commercial "adaptive curve" / contour guidance modes do not drive a
pre-planned set of parallel lines. They log the path the machine actually
drove on pass k and build the guidance line of pass k+1 from that log,
offset by one swath spacing. The method only needs the logged GNSS track, so
it is the standard online, sensor-driven alternative to a fixed offline
plan. Here the next reference line is

    r_{k+1}(x) = C[ S_smooth_m[ yhat_k ] ](x) + side * spacing,
    spacing    = w - m                         (m = target overlap),

where yhat_k(x) is the MEASURED field-frame lateral position logged on pass
k (antenna-derived, so it includes the earth-fixed RTK error, the per-run
mounting bias and the residual roll offset), S is a centred moving average
over smooth_m metres along x, and C is a curvature limiter. Pass 1 follows
the nominal line ys[0], exactly as in core.simulate.

References (checked by web search on 2026-10-13; see the note on access)
-------------------------------------------------------------------------
[1] John Deere, AutoTrac guidance on-screen help (Gen 4 display), "Adaptive
    Curve Track":
    displaysimulator.deere.com/onscreen_help/4640/current/en/autotrac_guidance/
    guidance_select_guidance_method_adaptive_curve_track.htm
    The page says the operator records a driven curved path. After the
    first pass, each additional pass is generated from the previous pass,
    "to ensure that steering errors are not propagated through the entire
    field". Generated passes are not identical copies of the original, and
    their curvature changes to keep pass-to-pass accuracy. A "Smooth Tight
    Turns" setting smooths a propagated path that is too tight. Straight
    extensions are added at the ends. Shift Track is not recommended because
    it does not account for GPS drift. The operator manual has the same
    method under "Adaptive Curve Mode" (manuals.deere.com, OMPFP16160).
    This is the rule implemented here.
[2] US 7,451,030 B2, "System and method for interactive selection and
    determination of agricultural vehicle guide paths offset from each other
    with varying curvature along their length". Claim 1 (USPTO full text):
    subsequent paths are computed by perpendicular offsets from the first
    path at multiple locations. Same Novariant, Inc. family as US
    2006/0178820 A1 ("... guiding an agricultural vehicle through a
    recorded template of guide paths", assignee Novariant: second path
    from "piecewise perpendicular offsets from the first path") and US
    7,256,388 B2 (original assignee Novariant Inc.). The family text
    describes projecting a perpendicular offset at each point of the
    previous path, then pruning "loops and reversals caused by high
    curvature and/or noise", then low-pass filtering. This is the
    smoothing/limiting step S, C used here. The assignee, inventors and
    dates of 7,451,030 itself were NOT confirmed (only of its siblings).
[3] US 8,583,326 B2 (published as US 2011/0196565 A1), "GNSS contour
    guidance path selection", D. M. Collins and M. D. Brown, AgJunction LLC
    (originally Hemisphere GPS). Contour guidance with a "contour lock"
    mode: after the vehicle has followed a new (as-driven) path for a set
    time, the system locks onto it as the guide path and ignores the other
    guidance paths, and it unlocks when the vehicle strays beyond a set
    deviation (claims / abstract, re-checked in review via search excerpts).
    Cite it for as-driven contour guidance in commercial GNSS systems, NOT
    as the source of the offset rule. The offset rule is [1] (and [2] for
    the offset/prune/filter construction).
[4] L. Paull, S. Saeedi, M. Seto, H. Li, "Sensor-driven online coverage
    planning for autonomous underwater vehicles", IEEE/RSJ IROS 2012,
    doi:10.1109/IROS.2012.6385838. Journal version: IEEE/ASME Trans.
    Mechatronics 18(6):1827-1838, 2013. CAVEAT: this is an AUV
    side-scan-sonar planner. It replans online from the sensor coverage
    actually achieved, using information gain / branch entropy on a
    hexagonal cell decomposition with multi-objective optimisation. It
    does NOT use the "previous executed pass + spacing" rule. Cite it only
    as the academic precedent for replacing a pre-planned lawnmower with
    online re-planning from achieved, measured coverage, not as the source
    of the rule above. (OpenAlex confirms the IROS record and first author
    Paull; the four-author list was confirmed for the journal version.
    IROS page numbers were not verified.)
[5] US 11,212,954 B2, "Apparatus and methods for field operations based on
    historical field operation data", Deere & Company, C. A. Maeder,
    Q. R. Liu, T. D. Pickett, J. J. Adams, issued 2022-01-04 (appl.
    16/406,830; pub. US 2020/0352082 A1; continuation US 11,825,761).
    A guidance line generator builds the line for a SECOND field operation
    from a map of crop-row locations logged during a first operation and
    from the implement of the second vehicle. This is the patent closest to
    John Deere AutoPath (launched 2020-11; an implement-mounted receiver
    records each row as planted, and later operations follow those rows
    instead of a static AB line). Same "follow the as-executed path"
    principle, but across operations, not pass to pass. Cite only for that
    context. The sources do not tie AutoPath to this patent explicitly.
Not cited: the requested "AutoPath US11914379". Searches for patent number
11914379 (twice, 2026-10-13) found no record, so it was not verified and
must not be cited as-is; [5] is the verified substitute.
Access note: the proxy on this machine blocks IEEE, Google Patents, USPTO,
OpenAlex, MIT and Deere pages (direct fetch fails). Everything above comes
from search-index excerpts of those pages. Check the exact wording, patent
bibliographic data and IROS pages against the originals before submission.

Adaptation decisions (A1-A9)
----------------------------
A1  Physics: the integration loop of core.simulate is copied verbatim:
    kinematic bicycle, steering lag/rate limit, DEM side-slip + OU
    roughness, antenna roll offset -h sin(roll)(1-comp), earth-fixed GNSS
    N/E error projected on the field lateral axis and sampled at
    T0[k] + t through the same lookup as the core (core.gnss_ne: the NOAA
    CORS bank of grade cond.gnss, default "rtk_fix", or the legacy i2Nav
    record; _gnss_ne falls back to core.rtk_ne on an older core), mounting
    bias cond.mount. The true state (d, psi, s) stays
    relative to the NOMINAL straight line ys[k]. That keeps the physics
    identical and makes D the true field-frame offset from ys[k].
    Only the controller's reference changes.
A2  Logged path: the guidance logs the measured field-frame position
    (x + eps_x, ys[k] + sgn*meas), with eps_x the same GNSS error sample
    projected on the field x axis. It never uses the true state.
    Controllers and the reference builder only see meas, psi_meas, delta,
    the measured x, known vehicle parameters and their own state (no k_s,
    OU, comp, mount or GNSS error series).
A3  Smoothing S: the logged samples (every 0.1 m) are binned on a 0.5 m grid,
    then a centred moving average over smooth_m metres is applied. The
    window shrinks at the pass ends. The whole of pass k is available when
    pass k+1 is planned, because the headland turn comes in between.
    smooth_m = 0 means binning only. smooth_m = 10 m is the default given
    for this baseline. It is NOT the best setting for coverage. A sweep on
    field 73 (40 paired runs, m = 5 cm, seed 0, gnss="rtk_fix" CORS bank,
    main-area metrics; re-run in review) gave, for
    smooth_m = 0/5/10/20/40 m:
      gap sd     4.36/4.36/4.67/5.16/5.36 cm      (fixed plan 5.36)
      m95        18.2/17.5/20.5/25.0/26.0 cm      (fixed plan 25.8)
      E[miss]    .00099/.00098/.00121/.00160/.00177 (fixed .00172)
      drift sd   10.7/10.3/9.3/5.2/3.3 cm         (fixed plan 2.05)
    So 0-5 m gives the strongest pass-to-pass result, and longer windows
    trade it for less drift. Field 73 is a selftest (test) field. For a
    fair comparison, choose smooth_m on non-test fields, or report the
    sweep. selftest prints a short sensitivity block.
A4  Extension: outside the x-range logged on pass k (non-rectangular
    fields), the reference continues at the constant end offset. This is a
    straight extension parallel to the operating (AB) direction, as in the
    straight end extensions of [1]. Extrapolating the noisy end slope would
    add drift.
A5  Curvature limit C ("Smooth Tight Turns" [1], loop trimming/low-pass
    [2]): where |kappa(x)| = |r''|/(1+r'^2)^1.5 > kappa_max, apply a
    local 1-2-1 smoothing, repeated (up to 500 sweeps) until the limit
    holds. Default kappa_max = 0.02 1/m (50 m radius) for in-field passes.
    The headland turn radius is not used for this. The limiter is a safety
    net: with smooth_m >= 5 m it changes < 2% of the samples (0.2-0.3% at 10 m), mostly at
    the pass ends where the moving-average window shrinks (selftest
    reports the fraction). With smooth_m = 0 it is the only smoothing left
    (it then touches ~36% of the samples).
A6  Tracking a curved reference with the same controllers. Errors are
    taken w.r.t. the reference: e = meas - e_r(x_meas), with e_r the
    reference offset in the vehicle frame, and
    epsi = psi_meas - atan(r'(x_meas)). Curvature feed-forward is
    delta_ff = atan(l_wb * kappa_v) with kappa_v = sgn r''/(1+r'^2)^1.5.
    lqr_i:  u = delta_ff - K[e, epsi, delta - delta_ff, int e], with the
            same conditional-integration anti-windup and clamp as core.
    lqr:    u = delta_ff - K[e, epsi].
    stanley:u = -epsi - atan(1.2 e / v) + delta_ff.
    pure_pursuit: goal point on the reference Ld = 4 m ahead,
            alpha = atan2(e_r(x + sgn Ld) - meas, Ld) - psi_meas.
    Controller objects get command(e, epsi, delta - delta_ff, dt), and
    delta_ff is added to the result. reset(R, 1, VEH, cond) is called at
    the start of every pass. Arrays are (R, 1). The objects in
    baselines/controllers.py work unchanged. In mode="nominal",
    controllers.ESOSMC is bit-identical to core.simulate. OffsetFreeMPC
    differs by <= 1 cm in D: its matrix products and QP over the flattened
    batch depend on the batch shape, (R, K) vs (R, 1). It is
    deterministic for a fixed shape and statistically equivalent.
A7  Line acquisition: the post-turn residual N(0, 3 cm), N(0, 0.5 deg) of
    core.simulate is applied relative to the pass's REFERENCE line (offset
    and tangent at the start point), not the nominal line.
    acquisition="core" (default) keeps core's convention: the residual is
    in TRUE coordinates, so the controller starts each pass with a measured
    error of eps(start) and corrects it. This holds for fixed and
    sequential passes alike, so comparisons with core.simulate are like for
    like. acquisition="measured" models a GNSS-guided turn instead: the
    MEASURED offset from the target is N(0, 3 cm). This simulator-side
    placement uses the true eps(start); the controller never sees it. It
    applies to every pass, so a fixed plan under the same convention is
    mode="nominal", acquisition="measured" (plan_sequential_eval does this
    automatically).
    Review note: "core" is the convention of the paper's simulator, but it
    is mildly CONSERVATIVE AGAINST this baseline. Under "core" every pass
    starts with a measured error equal to the GNSS bias (mount, roll offset,
    RTK). The decaying start transient is logged and copied into the next
    passes, so it piles up at the pass ends. On a flat, noise-free copy of
    field 73 with only a 2 cm mounting bias, the last of 34 passes deviates
    by up to 12 cm at its ends under "core" and by 0 under "measured" (the
    interior is unaffected). On the real fields the roll-offset version of
    this effect is the WHOLE systematic drift slope: field 73, paired runs,
    sl_mu +1.20 mm/pass under "core" vs -0.04 under "measured", last-pass
    drift sd 11.2 vs 8.4 cm. E[miss] and m95 change by less than their
    Monte-Carlo error (0.00158 vs 0.00157; 24.2 vs 24.2 cm; selftest
    decomposition). So quote drift numbers from acquisition="measured". "measured" is the
    physically consistent choice for a GNSS-guided headland turn. Report it
    as a sensitivity row, or as the main row if the comparison does not
    have to match core.simulate.
A8  Pass count: K = len(ys_nominal), i.e. the same number of passes as the
    fixed plan with overlap m. No extra pass is added. Drift accumulated at
    the far boundary therefore shows up as missed area, as it would for an
    operator who drives the planned number of passes. On the selftest fields
    the last planned pass overhangs the main area by 0.2-1.6 m, so this
    costs nothing there: P(no miss) equals P(interior gap-free) in every
    selftest row (checked in review).
A9  Random numbers: rng_mode="core" draws exactly the random stream of
    core.simulate, in the same order: (R, K) blocks per step, for all
    nsteps. So
      * mode="nominal" (straight lines ys) reproduces core.simulate bit for
        bit (selftest asserts this), and
      * fixed vs. sequential comparisons with the same seed are paired
        (common random numbers).
    It needs 16*K*nsteps*R bytes. rng_mode="pass" draws per pass instead
    (same distribution, little memory). rng_mode="auto" uses "core" below
    256 MB.

What it can and cannot remove (discussion)
------------------------------------------
Write the measured position of pass k as yhat_k = y_k + eps_k. Here y_k is
the true position and eps_k = n_k + sgn_k b + rho_k is the measurement
error: n_k the earth-fixed RTK error at the time pass k is at x, b the
mounting bias, rho_k the residual roll offset. Pass k+1 tracks its
reference with a measured-frame residual e_{k+1}. The true pass-to-pass
excess spacing, which causes a gap when it exceeds m, is then
    fixed plan:  g_k = (e_{k+1} - e_k) + (eps_k - eps_{k+1})
    sequential:  g_k = (e_{k+1} - (I - S)e_k) + (eps_k - eps_{k+1})
                       - (I - S)(r_k)            [~0 for a smooth r_k]
* The sequential rule removes the low-frequency part S e_k of the previous
  pass's tracking residual. That part comes from slope-induced slip which
  the integrator has not yet rejected, and from acquisition transients.
  The part below the smoothing scale stays: smoothing trades that against
  injecting measurement noise into the reference. In selftest (m = 5 cm,
  CORS rtk_fix errors) the sd of D_{k+1} - D_k drops from 5.8-5.9 to
  5.1-5.2 cm with the full error model, and from 4.8 to 3.9 cm with the
  GNSS and mount errors off.
* It cannot remove the RTK difference n_k - n_{k+1}. The two passes cross
  the same x at different times. The gap is about t_turn near one
  headland and 2L/v + t_turn near the other, so the earth-fixed error
  has decorrelated. The log contains n_k, and following it copies n_k
  into the next pass's TRUE position.
  It also cannot remove the alternating mounting term +-2b, which flips
  sign with the driving direction. Neither can the fixed plan, so both
  keep the same pass-to-pass RTK and mount terms.
* Drift accumulation: summing g_k telescopes the eps terms, leaving
      y_K - ys_K  ~  -eps_K + sum_{j<=K} S e_j     (sequential)
      y_K - ys_K  =   e_K - eps_K                  (fixed plan).
  So the sequential plan's absolute error is a SUM of the smoothed
  residuals of all previous passes, while the fixed plan's stays bounded.
  The zero-mean part of the sum is a random walk (sd ~ sqrt(K)). The
  residual also has a part with the same sign in the FIELD frame on every
  pass, whatever the driving direction, and that part grows linearly in K.
  selftest reports the mean and sd over runs of the offset-vs-pass slope
  ("sl_mu", "sl_sd", mm/pass). On paddy field 73 (1.33 deg mean slope,
  33-36 passes) sl_mu is +1.2 to +1.7 mm/pass under acquisition="core".
  Review finding: that systematic part is the start-of-pass roll-offset
  transient that the "core" convention creates (A7 note). Under
  "measured", sl_mu = -0.04 (field 73) and +0.02 (field 65) mm/pass, inside
  its Monte-Carlo standard error (~0.5 mm/pass at 50 runs). So a downhill
  slide at the pass start is not detectable as systematic drift with
  lqr_i. The random part (sl_sd ~3-4 mm/pass) dominates. The last pass's
  mean offset has an sd of 7.4-11.1 cm (8.4-10.2 cm under "measured"),
  against 1.9-4.8 cm for the fixed plan, whose absolute error now also
  carries the slowly varying CORS bias. With the GNSS and mount errors
  switched off it is still 8.8-10.1 cm (fixed plan 0.8-2.9 cm). So the
  drift comes from the tracking residuals, not the GNSS error. (Numbers:
  selftest, 50 paired runs, gnss="rtk_fix".) Drift matters at the
  far boundary (A8) and for later operations that reuse fixed AB lines
  ([1]: shifting adaptive curves "does not account for GPS drift").

API
---
plan_fixed(field, w, m)                    -> ys   fixed spacing w-m (core.plan, as terrain3d.plan_flat2d)
build_reference(xs_log, ys_log, xr, smooth_m, kappa_max)
                                           -> (r, r1, r2, frac_limited)  smoothed, limited
                                              reference on grid xr for every run
simulate_sequential(field, ys_nominal, cond, rng, ctrl="lqr_i", spacing=None, smooth_m=10.0,
                    kappa_max=0.02, mode="sequential", rng_mode="auto", acquisition="core",
                    return_info=False)
                                           -> X, D  (core.simulate format; D = TRUE field-frame
                                              offsets from the nominal ys) [, info: references,
                                              logged as-driven paths, tracking RMS/max, limiter]
plan_sequential_eval(field, w, m, n, rng, ctrl="lqr_i", smooth_m=10.0, kappa_max=0.02,
                     compare_fixed=True, rng_mode="auto", acquisition="core", **cond_kw)
                                           -> metrics dict ("seq"; "fixed" with identical noise)
run_metrics(field, ys, X, D, w, m)         -> P(no miss), E[miss], P(interior gap-free), gap/drift
                                              statistics on the main area (core.pair_scores mask)
selftest()                                 2 real paddy fields, m in {0, 5, 10} (+25) cm, 50 paired
                                           runs each; exactness and reference-builder checks;
                                           error decomposition (acquisition, RTK/mount off)
"""
import math
import time

import numpy as np

import core
import exp_lib

W_DEFAULT = 3.0
REF_STEP = 0.5          # reference grid spacing [m]
KAPPA_MAX = 0.02        # in-field reference curvature limit [1/m] (50 m radius)
PP_LOOKAHEAD = 4.0      # same as core's built-in pure pursuit
AUTO_MEM_BYTES = 256e6  # rng_mode="auto": pre-draw core's stream below this size


# ------------------------------------------------------------------ planning helper
def plan_fixed(field, w=W_DEFAULT, m=0.0):
    """Fixed offline plan with constant spacing w - m (core.plan, half-width
    w/2 - m/2). The first line is at y_lo + (w - m)/2. The sequential
    baseline uses it as its nominal plan, so both have the same K and ys[0]."""
    return core.plan(field, w, 1.0, lambda f, y: m / 2.0)


# ------------------------------------------------------------- reference builder
def _movsum(a, n):
    """Centred moving sum over n (odd) samples along axis 1, zero padded."""
    if n <= 1:
        return a.copy()
    h = n // 2
    c = np.cumsum(np.pad(a, ((0, 0), (h + 1, h))), axis=1)
    return c[:, n:] - c[:, :-n]


def build_reference(xs_log, ys_log, xr, smooth_m=10.0, kappa_max=KAPPA_MAX, max_sweeps=500):
    """Smoothed, curvature-limited lateral reference from logged positions.

    xs_log, ys_log : (T, R) logged MEASURED field-frame positions of one pass
    xr             : regular grid of x (spacing REF_STEP) on which r is built
    Returns r, r1 = dr/dx, r2 = d2r/dx2 (each (R, len(xr))) and the fraction
    of grid samples the curvature limiter modified.
    """
    T, R = xs_log.shape
    nb = len(xr)
    b = xr[1] - xr[0]
    j = np.rint((xs_log - xr[0]) / b).astype(int)
    ok = (j >= 0) & (j < nb) & np.isfinite(ys_log)
    flat = (np.arange(R)[None, :] * nb + j)[ok]
    s = np.bincount(flat, weights=ys_log[ok], minlength=R * nb).reshape(R, nb)
    c = np.bincount(flat, minlength=R * nb).reshape(R, nb).astype(float)
    n = max(1, int(round(smooth_m / b)))
    n += 1 - n % 2  # odd window
    S, C = _movsum(s, n), _movsum(c, n)
    valid = C > 0
    r = np.where(valid, S / np.where(valid, C, 1.0), np.nan)
    for i in np.nonzero(~valid.all(axis=1))[0]:  # fill gaps; constant extension beyond the ends (A4)
        v = valid[i]
        r[i] = np.interp(xr, xr[v], r[i, v]) if v.any() else 0.0
    # curvature limiter (A5): local 1-2-1 smoothing where |kappa| > kappa_max
    touched = np.zeros_like(r, bool)
    if kappa_max is not None and np.isfinite(kappa_max):
        for _ in range(max_sweeps):
            r1 = np.gradient(r, b, axis=1)
            r2 = np.zeros_like(r)
            r2[:, 1:-1] = (r[:, 2:] - 2 * r[:, 1:-1] + r[:, :-2]) / b ** 2
            bad = np.abs(r2) / (1 + r1 ** 2) ** 1.5 > kappa_max
            if not bad.any():
                break
            touched |= bad
            sm = r.copy()
            sm[:, 1:-1] = 0.25 * r[:, :-2] + 0.5 * r[:, 1:-1] + 0.25 * r[:, 2:]
            r = np.where(bad, sm, r)
    r1 = np.gradient(r, b, axis=1)
    r2 = np.gradient(r1, b, axis=1)
    return r, r1, r2, float(touched.mean())


def _lookup(A, x, x0, b):
    """Row-wise linear interpolation of A (R, n) at x (R, 1) on a regular grid."""
    n = A.shape[1]
    f = (x[:, 0] - x0) / b
    i0 = np.clip(np.floor(f).astype(int), 0, n - 2)
    t = np.clip(f - i0, 0.0, 1.0)
    ar = np.arange(A.shape[0])
    return (A[ar, i0] * (1 - t) + A[ar, i0 + 1] * t)[:, None]


# ---------------------------------------------------------------------- simulator
def _gnss_ne(cond, tsec):
    """Earth-fixed (north, east) GNSS error of every run at mission time tsec [s], as (R, 1)
    arrays, with exactly the lookup core.simulate uses: core.gnss_ne (NOAA CORS bank of the
    receiver grade cond.gnss, or the legacy i2Nav record) when the core provides it, otherwise
    the legacy core.rtk_ne() record wrapped at cond.rtk_offset (review fix: the module had the
    legacy lookup hard-coded, so it silently stopped replicating core.simulate when the core
    switched to the CORS bank)."""
    tsec = np.full((1, 1), tsec)
    if hasattr(core, "gnss_ne"):
        return core.gnss_ne(cond, tsec)
    en, ee = core.rtk_ne()
    ti = (cond.rtk_offset[:, None] + tsec.astype(int)) % len(en)
    return en[ti], ee[ti]


def simulate_sequential(field, ys_nominal, cond, rng, ctrl="lqr_i", spacing=None, smooth_m=10.0,
                        kappa_max=KAPPA_MAX, mode="sequential", rng_mode="auto", acquisition="core",
                        dx=1.0, return_info=False):
    """Execute K = len(ys_nominal) passes one after another. Pass k+1 tracks the
    measured, smoothed path of pass k offset by `spacing`.

    field       core.Field;  ys_nominal: nominal line positions (ascending),
                e.g. plan_fixed(F, w, m). Only ys[0] is a guidance target in
                mode="sequential"; the others are the frame D is reported in.
    cond        core.Condition (R runs);  rng: numpy Generator
    ctrl        "lqr_i" | "lqr" | "stanley" | "pure_pursuit" | controller object (A6)
    spacing     pass-to-pass offset of the reference [m], a magnitude >= 0;
                default |ys[1]-ys[0]| (= w - m for plan_fixed). The side
                (+y or -y) follows the order of ys_nominal (ascending or
                descending both work).
    smooth_m    moving-average length along x [m] (A3);  kappa_max: A5
    mode        "sequential" (this baseline) | "nominal" (track the straight
                lines ys: the core.simulate reference, used for validation)
    rng_mode    "core" | "pass" | "auto" (A9)
    Returns X, D exactly as core.simulate: X[k] along-track grid (1 m), D[k]
    (R, n_k) TRUE field-frame lateral offsets from ys_nominal[k]. So
    core.evaluate(field, ys_nominal, X, D, w) scores coverage directly. With
    return_info=True, info also holds the per-pass references, tracking RMS
    and limiter statistics.
    """
    t_start = time.time()
    ys = np.asarray(ys_nominal, float)
    R, K = len(cond.k_s), len(ys)
    if mode not in ("sequential", "nominal"):
        raise ValueError("mode must be 'sequential' or 'nominal'")
    if acquisition not in ("core", "measured"):
        raise ValueError("acquisition must be 'core' or 'measured'")
    # spacing is a MAGNITUDE; the direction of travel across the field comes from `side`
    # (review fix: with descending ys the signed default ys[1]-ys[0] < 0 was multiplied by
    # side = -1, so every reference stepped the wrong way and D grew by 2*spacing per pass)
    if spacing is None:
        spacing = abs(float(ys[1] - ys[0])) if K > 1 else 0.0
    spacing = float(spacing)
    if spacing < 0:
        raise ValueError("spacing is a magnitude (>= 0); the side follows the order of ys_nominal")
    side = 1.0 if K < 2 or ys[-1] >= ys[0] else -1.0
    v, l, tau, dt, h = core.VEH["v"], core.VEH["l_wb"], core.VEH["tau"], core.VEH["dt"], core.VEH["h_ant"]
    dmax, rmax = core.VEH["delta_max"], core.VEH["rate_max"]
    chords = [field.chord(field.P, y) for y in ys]
    x0 = np.array([c[0] if c else 0.0 for c in chords])
    x1 = np.array([c[1] if c else 0.0 for c in chords])
    L = np.maximum(x1 - x0, 1.0)
    sgn = np.where(np.arange(K) % 2 == 0, 1.0, -1.0)
    nsteps = int(L.max() / (v * dt)) + 2
    t_turn = math.pi * 4.5 / v + 6.0
    T0 = np.r_[0.0, np.cumsum(L / v + t_turn)[:-1]]
    th = math.radians(-field.rot)
    proj_e, proj_n = -math.sin(th), math.cos(th)    # field +y in (E, N)
    projx_e, projx_n = math.cos(th), math.sin(th)   # field +x in (E, N)  (logged x, A2)
    mount = cond.mount[:, None]
    k_s, rough, comp = cond.k_s[:, None], cond.rough[:, None], cond.comp[:, None]
    th_ou = 1.0 / 2.0
    rec_every = max(1, int(round(dx / (v * dt))))
    nrec = nsteps // rec_every + 1
    s_grid = np.arange(nrec) * rec_every * v * dt
    K_lqr, K_lqri = core._lqr_gains(v, l, dt)
    psi_sd = math.radians(0.15)

    # ---- random numbers (A9)
    if rng_mode == "auto":
        rng_mode = "core" if 16.0 * K * nsteps * R <= AUTO_MEM_BYTES else "pass"
    if rng_mode == "core":
        d_init = rng.normal(0, 0.03, (R, K))
        psi_init = rng.normal(0, math.radians(0.5), (R, K))
        Z_ou = np.empty((K, nsteps, R))
        Z_psi = np.empty((K, nsteps, R))
        for t in range(nsteps):
            Z_ou[:, t, :] = rng.standard_normal((R, K)).T
            Z_psi[:, t, :] = rng.normal(0, psi_sd, (R, K)).T
    elif rng_mode != "pass":
        raise ValueError("rng_mode must be 'core', 'pass' or 'auto'")

    # reference grid shared by all passes
    minx, _, maxx, _ = field.P.bounds
    xr = np.arange(math.floor(minx) - 10.0, math.ceil(maxx) + 10.0 + REF_STEP / 2, REF_STEP)
    ref = None  # (r, r1, r2) for the current pass, None = straight nominal line
    X, D = [], []
    info = dict(refs=[None], logs=[], track_rms=np.zeros((R, K)), track_max=np.zeros((R, K)),
                limited=[], rng_mode=rng_mode, xr=xr, spacing=spacing, side=side)
    for k in range(K):
        sk_ = sgn[k]
        n_k = int(L[k] / dx)
        sk = np.arange(n_k) * dx
        idx = np.clip(np.searchsorted(s_grid, sk), 0, nrec - 1)
        t_need = int(idx.max()) * rec_every + 1 if n_k else 1
        t_k = min(nsteps, max(int(L[k] / (v * dt)) + 2, t_need))
        rec = np.zeros((nrec, R))
        xs_log = np.empty((t_k, R))
        ys_log = np.empty((t_k, R))
        se2 = np.zeros(R)
        emax = np.zeros(R)
        ne = np.zeros(R)
        # line acquisition residual w.r.t. the pass's reference (A7)
        if rng_mode == "core":
            d = d_init[:, k:k + 1].copy()
            psi = psi_init[:, k:k + 1].copy()
        else:
            d = rng.normal(0, 0.03, (R, 1))
            psi = rng.normal(0, math.radians(0.5), (R, 1))
        xs0 = np.full((R, 1), x0[k] if sk_ > 0 else x1[k])
        if ref is not None:
            d = d + sk_ * (_lookup(ref[0], xs0, xr[0], REF_STEP) - ys[k])
            psi = psi + np.arctan(_lookup(ref[1], xs0, xr[0], REF_STEP))
        if acquisition == "measured":  # GNSS-frame acquisition: MEASURED offset ~ N(0, 3 cm) from the target
            g_v0 = sk_ * field.gy(xs0, ys[k] + sk_ * d)
            gn0, ge0 = _gnss_ne(cond, T0[k] + 0 * dt)
            eps0 = (h * np.sin(np.arctan(g_v0)) * (1 - comp) * (-1.0)
                    + sk_ * cond.rtk_scale * (proj_e * ge0 + proj_n * gn0).astype(float) + mount)
            d = d - eps0
        delta = np.zeros((R, 1))
        integ = np.zeros((R, 1))
        ou = np.zeros((R, 1))
        s_trav = np.zeros((R, 1))
        if not isinstance(ctrl, str):
            ctrl.reset(R, 1, core.VEH, cond)
        for t in range(t_k):
            # ---------------- physics: verbatim core.simulate (A1) ----------------
            xf = x0[k] + s_trav if sk_ > 0 else x1[k] - s_trav
            yf = ys[k] + sk_ * d
            g = field.gy(xf, yf)
            g_v = sk_ * g
            z_ou = Z_ou[k, t][:, None] if rng_mode == "core" else rng.standard_normal((R, 1))
            ou += -th_ou * ou * dt + rough * math.sqrt(2 * th_ou * dt) * z_ou
            beta = -k_s * g_v * 0.35 + ou
            roll = np.arctan(g_v)
            gn, ge = _gnss_ne(cond, T0[k] + t * dt)  # (R, 1) at the earth time of this pass (core.gnss_ne)
            eps_y = proj_e * ge + proj_n * gn
            meas = d + h * np.sin(roll) * (1 - comp) * (-1.0) + sk_ * cond.rtk_scale * eps_y.astype(float) + mount
            z_psi = Z_psi[k, t][:, None] if rng_mode == "core" else rng.normal(0, psi_sd, (R, 1))
            psim = psi + z_psi
            # ---------------- guidance: errors w.r.t. the reference (A2, A6) ------
            x_meas = xf + cond.rtk_scale * (projx_e * ge + projx_n * gn).astype(float)
            xs_log[t] = x_meas[:, 0]
            ys_log[t] = (ys[k] + sk_ * meas)[:, 0]
            if ref is None:
                e_r, psi_r, dff = 0.0, 0.0, 0.0
            else:
                rr = _lookup(ref[0], x_meas, xr[0], REF_STEP)
                r1 = _lookup(ref[1], x_meas, xr[0], REF_STEP)
                r2 = _lookup(ref[2], x_meas, xr[0], REF_STEP)
                e_r = sk_ * (rr - ys[k])
                psi_r = np.arctan(r1)
                dff = np.arctan(l * sk_ * r2 / (1 + r1 ** 2) ** 1.5)
            e = meas - e_r
            epsi = psim - psi_r
            if not isinstance(ctrl, str):
                dcmd = ctrl.command(e, epsi, delta - dff, dt) + dff
            elif ctrl == "pure_pursuit":
                Ld = PP_LOOKAHEAD
                tgt = 0.0 if ref is None else \
                    sk_ * (_lookup(ref[0], x_meas + sk_ * Ld, xr[0], REF_STEP) - ys[k])
                alpha = np.arctan2(tgt - meas, Ld) - psim
                dcmd = np.arctan(2 * l * np.sin(alpha) / Ld)
            elif ctrl == "stanley":
                dcmd = -epsi - np.arctan(1.2 * e / v) + dff
            elif ctrl == "lqr":
                dcmd = dff - (K_lqr[0] * e + K_lqr[1] * epsi)
            elif ctrl == "lqr_i":
                ddv = delta - dff
                u_try = dff - (K_lqri[0] * e + K_lqri[1] * epsi + K_lqri[2] * ddv + K_lqri[3] * (integ + e * dt))
                sat = np.abs(u_try) >= dmax
                integ = np.where(sat, integ, np.clip(integ + e * dt, -0.3, 0.3))
                dcmd = dff - (K_lqri[0] * e + K_lqri[1] * epsi + K_lqri[2] * ddv + K_lqri[3] * integ)
            else:
                raise ValueError(f"unknown controller {ctrl!r}")
            # ---------------- actuator + kinematics: verbatim core.simulate --------
            dcmd = np.clip(dcmd, -dmax, dmax)
            ddel = np.clip((dcmd - delta) / tau * dt, -rmax * dt, rmax * dt)
            delta += ddel
            d += v * np.sin(psi + beta) * dt
            psi += v * np.tan(delta) / l * dt
            s_trav += v * np.cos(psi) * dt
            if t % rec_every == 0:
                rec[t // rec_every] = (sk_ * d)[:, 0]
            # tracking error (measured, w.r.t. the reference) inside the chord, after 10 m
            inside = (s_trav[:, 0] >= 10.0) & (s_trav[:, 0] <= L[k])
            ea = np.abs(e[:, 0])
            se2 += np.where(inside, ea ** 2, 0.0)
            emax = np.maximum(emax, np.where(inside, ea, 0.0))
            ne += inside
        if return_info:
            info["logs"].append((xs_log, ys_log))
        info["track_rms"][:, k] = np.sqrt(se2 / np.maximum(ne, 1))
        info["track_max"][:, k] = emax
        X.append(x0[k] + sk if sk_ > 0 else x1[k] - sk)
        D.append(rec[idx, :].T.copy())
        # ---- reference for pass k+1 (A3-A5)
        if mode == "sequential" and k + 1 < K:
            r, r1, r2, frac = build_reference(xs_log, ys_log, xr, smooth_m, kappa_max)
            ref = (r + side * spacing, r1, r2)
            info["limited"].append(frac)
            if return_info:
                info["refs"].append(ref[0])
        elif return_info and k + 1 < K:
            info["refs"].append(None)
    info["runtime_s"] = time.time() - t_start
    return (X, D, info) if return_info else (X, D)


# ------------------------------------------------------------------------ metrics
def run_metrics(field, ys, X, D, w=W_DEFAULT, m=0.0):
    """Coverage and pass-to-pass statistics of one batch of runs.

    p_nomiss, e_miss, p95_miss : core.evaluate on the nominal ys
    All pass-to-pass statistics below are restricted to the MAIN AREA with
    the mask of core.pair_scores (at grid x, pass k counts when ys[k] lies
    within w of the main-area chord), so they describe the same region
    core.evaluate scores (pass ends in the headland strips are excluded):
    gap_sd     sd of the pass-to-pass difference D_{k+1} - D_k (main-area x,
               pairs, runs) [m]
    m95        95th pct over runs of max_{k,x}(D_{k+1} - D_k) = the raw pair
               maximum of core.pair_scores: the interior overlap needed for
               95% gap-free operations [m]
    p_int_nogap  fraction of runs with max_{k,x}(D_{k+1} - D_k) <= m
               (interior gap-free; the rest of P(no miss) is the boundary)
    drift_sd   sd over runs of the main-area mean true offset of the LAST
               pass [m] (absolute drift at the far boundary)
    slope_mean_mm, slope_sd_mm  mean / sd over runs of the least-squares
               slope of the per-pass mean true offset vs pass index
               [mm/pass]: systematic and random drift accumulation
    (Review fix: these statistics were computed over the whole along-track
    extent of every pass, including the pass ends outside the main area,
    which inflated m95 by up to 1.2 cm and made it inconsistent with
    P(no miss).)
    """
    miss = core.evaluate(field, ys, X, D, w)
    ys = np.asarray(ys, float)
    xg, off = exp_lib.offsets(field, ys, X, D)
    mask = np.zeros((len(ys), len(xg)), bool)       # same mask as core.pair_scores
    for j, x in enumerate(xg):
        c = core._chord_x(field.M, x)
        if c is not None:
            mask[:, j] = (ys > c[0] - w) & (ys < c[1] + w)
    offm = np.where(mask[:, None, :], off, np.nan)
    diff = offm[1:] - offm[:-1]                     # (K-1, R, nx), nan outside the main area
    with np.errstate(all="ignore"):
        pmax = np.nanmax(np.where(np.isnan(diff), -np.inf, diff), axis=(0, 2))  # (R,)
        mean_k = np.where(mask.any(1)[:, None], np.nanmean(offm, axis=2), np.nanmean(off, axis=2))  # (K, R)
    kk = np.arange(len(ys)) - (len(ys) - 1) / 2.0
    slope = (kk[:, None] * mean_k).sum(0) / (kk ** 2).sum()
    return dict(p_nomiss=float(np.mean(miss == 0)), e_miss=float(miss.mean()),
                p95_miss=float(np.percentile(miss, 95)), passes=len(ys),
                overlap=exp_lib.overlap_ratio(field, ys, w), m=m,
                gap_sd=float(np.nanstd(diff)), m95=float(np.percentile(pmax, 95)),
                p_int_nogap=float(np.mean(pmax <= m + 1e-12)),
                drift_sd=float(np.std(mean_k[-1])), slope_mean_mm=float(1e3 * np.mean(slope)),
                slope_sd_mm=float(1e3 * np.std(slope)))


def plan_sequential_eval(field, w=W_DEFAULT, m=0.05, n=50, rng=None, ctrl="lqr_i", smooth_m=10.0,
                         kappa_max=KAPPA_MAX, compare_fixed=True, rng_mode="auto", acquisition="core",
                         fixed_track=False, **cond_kw):
    """Monte-Carlo evaluation of sequential guidance with target overlap m.

    The nominal plan is plan_fixed(field, w, m) (spacing w - m, same K).
    With compare_fixed=True the fixed plan runs with the SAME Condition and
    the SAME random stream (common random numbers; exact when the resolved
    rng_mode is "core"), so the two results are paired. It runs through
    core.simulate for acquisition="core", and through simulate_sequential
    (mode="nominal", acquisition="measured") otherwise (A7).
    fixed_track=True also gives the fixed plan's tracking RMS: it re-runs
    the fixed plan in nominal mode, and checks that this run matches
    core.simulate when paired.
    Returns {"seq": metrics, "fixed": metrics or None, "paired": bool}. Each
    metrics dict is run_metrics(...) plus track_rms (mean RMS measured
    lateral error w.r.t. the reference, passes 2..K [m]), limited (fraction
    of reference samples the curvature limiter touched) and runtime_s.
    """
    rng = np.random.default_rng() if rng is None else rng
    ys = plan_fixed(field, w, m)
    cond = core.Condition(rng, n, **cond_kw)
    seed = int(rng.integers(2 ** 62))
    kw = dict(ctrl=ctrl, rng_mode=rng_mode, acquisition=acquisition, return_info=True)
    t = time.time()
    X, D, info = simulate_sequential(field, ys, cond, np.random.default_rng(seed), spacing=w - m,
                                     smooth_m=smooth_m, kappa_max=kappa_max, **kw)
    seq = run_metrics(field, ys, X, D, w, m)
    seq.update(track_rms=float(info["track_rms"][:, 1:].mean()) if len(ys) > 1 else float("nan"),
               limited=float(np.mean(info["limited"])) if info["limited"] else 0.0,
               runtime_s=time.time() - t)
    out = dict(seq=seq, fixed=None, paired=info["rng_mode"] == "core")
    if compare_fixed:
        t = time.time()
        inf_f = None
        if acquisition == "core":
            Xf, Df = core.simulate(field, ys, cond, np.random.default_rng(seed), ctrl=ctrl)
        else:
            Xf, Df, inf_f = simulate_sequential(field, ys, cond, np.random.default_rng(seed), mode="nominal", **kw)
        fx = run_metrics(field, ys, Xf, Df, w, m)
        fx.update(runtime_s=time.time() - t)
        if fixed_track and inf_f is None:
            _, Dn, inf_f = simulate_sequential(field, ys, cond, np.random.default_rng(seed), mode="nominal", **kw)
            if out["paired"]:
                assert all(np.array_equal(a, b) for a, b in zip(Df, Dn)), "nominal mode != core.simulate"
        if inf_f is not None:
            fx.update(track_rms=float(inf_f["track_rms"][:, 1:].mean()) if len(ys) > 1 else float("nan"))
        out["fixed"] = fx
    return out


# ------------------------------------------------------------------------ selftest
def _check_exact(F, n=8, seed=3, w=W_DEFAULT):
    """mode='nominal' + rng_mode='core' must reproduce core.simulate bit for bit."""
    ys = plan_fixed(F, w, 0.05)
    worst = 0.0
    cases = [(c, {}) for c in ("lqr_i", "pure_pursuit", "stanley", "lqr")]
    if hasattr(core, "gnss_ne"):  # also the legacy single-record GNSS path of the core
        cases.append(("lqr_i", dict(gnss="i2nav")))
    for ctrl, kw in cases:
        cond = core.Condition(np.random.default_rng(seed), n, **kw)
        Xa, Da = core.simulate(F, ys, cond, np.random.default_rng(seed + 1), ctrl=ctrl)
        Xb, Db = simulate_sequential(F, ys, cond, np.random.default_rng(seed + 1), ctrl=ctrl,
                                     mode="nominal", rng_mode="core")
        assert all(np.array_equal(a, b) for a, b in zip(Xa, Xb))
        worst = max(worst, max(float(np.max(np.abs(a - b))) for a, b in zip(Da, Db)))
    assert worst < 1e-12, f"nominal mode differs from core.simulate by {worst}"
    return worst


class _ZeroRNG:
    """numpy-Generator stand-in whose draws are all zero (noise-free checks)."""

    def normal(self, loc=0.0, scale=1.0, size=None):
        return np.zeros(size)

    def standard_normal(self, size=None):
        return np.zeros(size)


def _check_signs(F, w=W_DEFAULT, m=0.05, b=0.02):
    """Sign conventions of the reference, offset side and mounting term (added in review).

    On a flat copy of F with every random draw zero and no RTK / roughness:
      (i)  the sequential rule must reproduce the nominal lines exactly, for
           ascending AND descending ys (side = -1);
      (ii) with a pure mounting bias b and GNSS-frame acquisition (no start
           transient) the sequential passes must sit at -sgn_k b exactly, as the
           fixed plan does: the +-2b term is the same for both plans.
    Returns the largest deviation [m]."""
    import copy

    Ff = copy.copy(F)
    Ff.gy_map = np.zeros_like(F.gy_map)
    ys = plan_fixed(F, w, m)
    sg = np.where(np.arange(len(ys)) % 2 == 0, 1.0, -1.0)

    def cond(mount):
        c = core.Condition(np.random.default_rng(0), 2, rtk_scale=0.0, mount_sd=0.0)
        c.rough = np.zeros(2)
        c.mount = np.full(2, mount)
        return c

    worst = 0.0
    for y in (ys, ys[::-1].copy()):
        _, Dz = simulate_sequential(Ff, y, cond(0.0), _ZeroRNG(), rng_mode="pass")
        worst = max(worst, max(float(np.abs(d).max()) for d in Dz))
    _, Db = simulate_sequential(Ff, ys, cond(b), _ZeroRNG(), rng_mode="pass", acquisition="measured")
    worst = max(worst, max(float(np.abs(Db[k] + sg[k] * b).max()) for k in range(len(ys))))
    assert worst < 1e-9, f"sequential sign-convention check failed (max deviation {worst} m)"
    return worst


def _check_reference():
    """Reference builder: smoothing, constant extension and curvature limit."""
    xr = np.arange(0.0, 100.0 + 1e-9, REF_STEP)
    xs = np.linspace(10, 90, 801)[:, None].repeat(2, 1)
    ys = np.c_[0.05 * np.sin(2 * np.pi * xs[:, 0] / 2.0), 0.002 * xs[:, 1]]  # 2 m ripple; ramp
    r, r1, r2, frac = build_reference(xs, ys, xr, smooth_m=10.0, kappa_max=KAPPA_MAX)
    mid = (xr > 20) & (xr < 80)
    assert np.abs(r[0, mid]).max() < 0.01                 # 2 m ripple averaged out
    assert np.abs(r[1, mid] - 0.002 * xr[mid]).max() < 1e-3  # ramp preserved
    assert np.ptp(r[:, xr < 4.0], axis=1).max() < 1e-12      # constant extension beyond the log
    r, r1, r2, frac = build_reference(xs, ys, xr, smooth_m=0.0, kappa_max=KAPPA_MAX)
    r1d = np.gradient(r, REF_STEP, axis=1)[:, 1:-1]
    kap = np.abs(np.diff(r, 2, axis=1)) / REF_STEP ** 2 / (1 + r1d ** 2) ** 1.5
    assert frac > 0 and kap.max() <= KAPPA_MAX * (1 + 1e-9), kap.max()  # limiter active and satisfied
    return float(kap.max())


def selftest(n_runs=50, n_fields=2, w=W_DEFAULT, overlaps=(0.0, 0.05, 0.10), extra_overlaps=(0.25,),
             smooth_m=10.0, seed=0):
    """Fixed plan (core.simulate) vs sequential guidance on the first n_fields
    paddy fields of core.load_fields("paddy", seed=0) (the same two as the
    F2C selftest). Runs are paired: same Condition, same random stream."""
    t_all = time.time()
    fields = core.load_fields("paddy", w=w, seed=0)[:n_fields]
    t0 = time.time()
    worst = _check_exact(fields[0])
    sgn_dev = _check_signs(fields[0], w=w)
    kap = _check_reference()
    print(f"sequential baseline selftest: w={w} m, {n_runs} runs/config, ctrl=lqr_i, smooth_m={smooth_m} m, "
          f"kappa_max={KAPPA_MAX} 1/m, acquisition='core'; fixed = core.simulate on plan_fixed(F, w, m) "
          f"with the SAME Condition and random stream (paired)")
    print(f"checks ({time.time() - t0:.1f} s): mode='nominal' reproduces core.simulate for lqr_i, pure_pursuit, "
          f"stanley, lqr, + lqr_i on the legacy i2nav GNSS record (max |dD| = {worst:.1e} m); noise-free flat-field sign checks (ascending and "
          f"descending ys, mount-only bias) max dev {sgn_dev:.1e} m; reference builder: ripple removed, ramp kept, constant "
          f"end extension, curvature limiter active and satisfied (max kappa {kap:.4f} 1/m)")
    hdr = (f"  {'m_cm':>4s} {'method':>6s} {'K':>3s} {'ovl':>6s} {'P(nm)':>5s} {'P(ig)':>5s} {'E[miss]':>8s} {'p95miss':>8s} "
           f"{'gap_sd':>6s} {'m95':>6s} {'drift':>6s} {'sl_mu':>6s} {'sl_sd':>5s} {'trk':>5s} {'lim':>5s} {'t_s':>5s}")

    def row(lbl, name, r):
        print(f"  {lbl:>4s} {name:>6s} {r['passes']:3d} {r['overlap']:6.3f} {r['p_nomiss']:5.2f} {r['p_int_nogap']:5.2f} {r['e_miss']:8.5f} "
              f"{r['p95_miss']:8.5f} {100 * r['gap_sd']:6.2f} {100 * r['m95']:6.2f} {100 * r['drift_sd']:6.2f} "
              f"{r['slope_mean_mm']:6.2f} {r['slope_sd_mm']:5.2f} {100 * r.get('track_rms', np.nan):5.2f} "
              f"{r.get('limited', np.nan):5.3f} {r['runtime_s']:5.1f}")

    for F in fields:
        print(f"\nfield {F.fid}: main area {F.M.area:.0f} m2, mean slope {F.z_mean_slope:.2f} deg")
        print(hdr)
        for m in tuple(overlaps) + tuple(extra_overlaps):
            res = plan_sequential_eval(F, w, m, n_runs, np.random.default_rng(seed + int(round(1e3 * m))),
                                       smooth_m=smooth_m, fixed_track=True)
            assert res["paired"]
            lbl = f"{100 * m:.0f}" + ("*" if m in extra_overlaps else "")
            row(lbl, "fixed", res["fixed"])
            row(lbl, "seq", res["seq"])
    print("\ndecomposition, m = 5 cm (fixed vs seq; gap_sd / m95 / drift in cm, sl_mu in mm/pass):")
    variants = (("full model, acq=core", "core", {}),
                ("full model, acq=measured", "measured", {}),
                ("no RTK, no mount, acq=core", "core", dict(rtk_scale=0.0, mount_sd=0.0)))
    for F in fields:
        for label, acq, kw in variants:
            res = plan_sequential_eval(F, w, 0.05, n_runs, np.random.default_rng(seed + 7), smooth_m=smooth_m,
                                       acquisition=acq, **kw)
            f, s = res["fixed"], res["seq"]
            print(f"  field {F.fid:3d} {label:27s} gap_sd {100 * f['gap_sd']:.2f} -> {100 * s['gap_sd']:.2f} | "
                  f"m95 {100 * f['m95']:5.2f} -> {100 * s['m95']:5.2f} | drift {100 * f['drift_sd']:.2f} -> "
                  f"{100 * s['drift_sd']:5.2f} | sl_mu {f['slope_mean_mm']:5.2f} -> {s['slope_mean_mm']:5.2f} | "
                  f"E[miss] {f['e_miss']:.5f} -> {s['e_miss']:.5f}")
    print(f"\nsmoothing sensitivity, field {fields[-1].fid}, m = 5 cm, acq=core (smooth_m = 10 m is the given default; "
          f"see A3):")
    for sm in (0.0, 5.0, 20.0):
        res = plan_sequential_eval(fields[-1], w, 0.05, n_runs, np.random.default_rng(seed + 7), smooth_m=sm)
        f, s = res["fixed"], res["seq"]
        print(f"  smooth_m {sm:4.0f} m: gap_sd {100 * f['gap_sd']:.2f} -> {100 * s['gap_sd']:.2f} | m95 {100 * f['m95']:5.2f} -> "
              f"{100 * s['m95']:5.2f} | drift {100 * f['drift_sd']:.2f} -> {100 * s['drift_sd']:5.2f} | E[miss] "
              f"{f['e_miss']:.5f} -> {s['e_miss']:.5f} | lim {s['limited']:.3f}")
    print("\nm_cm = target overlap (* = extra, beyond the required {0, 5, 10} cm); K = passes; ovl = planned overlap "
          "ratio; P(nm) = P(no miss) of the main area; P(ig) = P(interior gap-free, max_{k,x}(D_{k+1}-D_k) <= m); gap_sd = sd of "
          "D_{k+1}-D_k [cm]; gap_sd, m95, drift and sl_* use the main-area mask of core.pair_scores; m95 = 95th pct over runs of "
          "max_{k,x}(D_{k+1}-D_k), the overlap needed for 95% interior gap-free runs [cm]; drift = sd over runs of the "
          "last pass's mean true offset [cm]; sl_mu / sl_sd = mean / sd over runs of the offset-vs-pass slope "
          "[mm/pass]; trk = RMS measured lateral error w.r.t. the guidance reference, passes 2..K [cm]; lim = "
          "fraction of reference samples the curvature limiter touched; t_s = simulation + scoring seconds "
          "(fixed: core.simulate only; its trk comes from a bit-identical nominal-mode re-run).")
    print(f"total selftest runtime {time.time() - t_all:.1f} s")


if __name__ == "__main__":
    selftest()

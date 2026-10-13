"""Commercial-practice baseline: terrain-compensated (TC) autosteer plus the
overlap settings a manufacturer / farmer would use.

What this module models
-----------------------
A commercial RTK autosteer system on hilly ground does two things that the
paper's certified planner does differently:
  (1) the steering controller removes the antenna-roll offset with an IMU roll
      estimate ("terrain compensation") and compensates the expected downhill
      drift, and
  (2) the swath overlap is a single global number, either the manufacturer-
      derived nominal value or a value the farmer "tuned once" on his own fields.

API
---
    ctrl = VendorTC(field, ys, tc=True, ff=True, k_ff=K_FF_NOMINAL,
                    roll_noise_deg=0.15, roll_bias_deg=0.1, seed=None)
        pluggable controller for core.simulate (reset / command). Must be run
        with vendor_condition() (comp == 0, see V2), e.g.
    cond = vendor_condition(rng, n, **cond_kw)      # core.Condition with comp == 0
    X, D, cond, ctrl, sec = execute(F, ys, n, rng, ctrl="vendor", imu_seed=None, **cond_kw)
        ctrl: "vendor" (TC + feed-forward), "vendor_noff" (TC only), a
        core built-in name ("lqr_i", ... -> default Condition, comp = 0.85),
        or a factory f(F, ys, imu_seed) -> controller object.
    ys = plan_overlap(F, overlap, w=3.0)            # boustrophedon with spacing w - overlap
    o  = nominal_overlap()                          # 2 x 2.5 cm = 0.05 m
    o  = farmer_tuned_overlap(train_fields, rng, target=0.9, ...)   # see (2) below
    r  = evaluate_overlap(F, overlap, n_runs, rng, ctrl="vendor")   # P(no miss), overlap ratio, ...
    m  = tracking_metrics(F, ys, X, D)              # ISO 12188-2-style XTE + pass-to-pass stats
    k  = calibrate_ff(train_fields, rng)            # data-driven feed-forward gain (optional)
    selftest()

(1) VendorTC -- terrain-compensated LQR-I autosteer
---------------------------------------------------
Measurement model of core.simulate (vehicle frame, left positive):
    meas = d - h sin(roll) (1 - comp) + sgn eps_y(T_k + t) + b_mount,
    roll = atan(sgn * dz/dy)   (roll > 0  <=>  left side up)
so with roll > 0 the antenna, h = 2.6 m above the ground point, is displaced
to the right (downhill, negative) by h sin(roll).  The ground-point correction
is therefore  +h sin(roll):
    meas_c = meas + h sin(roll_imu)
           = d - h [sin(roll) - sin(roll_imu)] + sgn eps_y + b_mount   (comp = 0).
IMU roll estimate (per step, vectorised over runs x passes):
    roll_imu = atan(sgn * field.gy(x_hat, y_hat)) + b_r + n_t,
    b_r ~ N(0, 0.1 deg) per run (drawn at reset, same IMU for all passes of a run),
    n_t ~ N(0, 0.15 deg) white at the 20 Hz control rate,
both drawn from the controller's OWN generator (seed), so the simulator's
random stream -- and hence common random numbers with the built-in
controllers -- is untouched.  The DEM roll is the "true roll" proxy the IMU
senses: it is the same expression core.simulate uses for the plant's roll.
Slope feed-forward: the expected side-slip on the side slope g_v is
    beta_hat = -k_ff tan(roll_imu),   k_ff = 0.35 E[k_s] = K_FF_NOMINAL = 0.1753,
(plant: beta = -0.35 k_s g_v + OU); the controller steers the COURSE angle
psi + beta_hat instead of the heading, i.e. it tracks the crab-angle reference
psi_ff = k_ff tan(roll_imu), so on a constant slope the integrator only has
to remove the residual (k_s - E[k_s]) part of the drift.
Inner loop: the built-in lag-aware LQR-I law of core.simulate re-implemented
on (meas_c, psi_meas - psi_ff) with the gains of core._lqr_gains (state
[d, psi, delta, int d], discrete Riccati on the lag-augmented model) and the
same anti-windup (conditional integration, integrator clamped to +/-0.3 m s).
With tc=False, ff=False it reproduces the string controller "lqr_i"
bit-for-bit (checked in selftest [1a]).

(2) Overlap settings
--------------------
  nominal_overlap()  = 2 x vendor-claimed pass-to-pass accuracy = 2 x 2.5 cm
                       = 5 cm (study design rule: a common conservative rule
                       of thumb, NOT a manufacturer recommendation).
  farmer_tuned_overlap(train_fields, rng, target=0.9)
                     = the smallest single global overlap on a 1 cm grid whose
                       P(no miss) averaged over the TRAINING fields is >= target
                       ("tuned once" on the farmer's own fields, then used
                       everywhere).  Search: upward scan at a coarse step
                       (default 4 cm) to the first success, then a 1 cm upward
                       scan inside the last failing bracket (exactly the
                       smallest grid point if P(no miss) is monotone below the
                       bracket; coarse=0.01 gives the plain 1 cm scan).  Every
                       candidate on a training field uses the same simulator
                       and IMU seeds (common random numbers), so the per-run
                       conditions (slip gain, roughness, RTK start time,
                       mounting error, IMU bias) are identical across candidates.
  Overlap o maps to core.plan with constant sigma = 1 m and lam = o / 2: pass
  spacing w - o, and the outermost swath edges extend o / 2 beyond the
  main-area boundary (half the overlap on each side, the convention of the
  boundary terms of core.pair_scores).

Verified references (web search, 2026-10-13)
--------------------------------------------
Terrain compensation (manufacturer patents / documentation):
  [D1] A. K. W. Rekow, D. Mercer, F. W. Nelson, T. Pickett (Deere & Company),
       "Direct modification of DGPS information with inertial measurement
       data", US 6,789,014 B1 (US appl. 10/435,067; Canadian counterpart
       CA 2,466,563, filed 2004-05-07, issued 2012-07-10, owner Deere & Co.,
       inventors confirmed on the CIPO record).  An inertial compensation
       assembly between the GPS receiver and the navigation controller
       measures roll and yaw and corrects the GPS position and course for the
       antenna lever arm on non-level terrain (and the track spacing for slope).
  [D2] Related: "Inertial augmentation for GPS navigation on ground vehicles",
       US 6,694,260 B1 (CA 2,466,691, filed 2004-05-07): roll / yaw compensation
       of GPS position, course and track spacing without a full IMU suite
       (assignee not confirmed from the search results -- verify before citing).
  [D3] S. Han, J. F. Reid, T. D. Pickett (Deere & Company), "Vehicular guidance
       system having compensation for variations in ground elevation",
       US 7,593,798 B2 (appl. 10/696,788, filed 2003-10-30; divisional
       US 7,844,380 B2; publ. US 2005/0096802 A1): roll and pitch for the
       vehicle position estimated from STORED ELEVATION DATA and used for
       guidance -- the DEM-based roll that VendorTC uses as the IMU's
       true-roll proxy.
  [D4] John Deere StarFire receiver onscreen help ("Fore-aft and height",
       "TCM calibration", displaysimulator.deere.com): the terrain compensation
       module corrects for roll / pitch on side slopes; the antenna height is
       entered from ground to the dome; on a 10 deg slope a 30.5 cm height
       error gives a ~5 cm ground offset (= 0.305 sin 10 deg, i.e. the
       correction is h sin(roll)); roll zero is calibrated at +/-2 deg.
  [T1] Trimble Autopilot datasheet / product page: "T3 sensors ... calculate
       the roll angle of your vehicle to shift it on line"; "one-inch
       repeatability" with a Trimble RTK service.
  [O1] R. Ospina, N. Noguchi, "Improved inclination correction method applied
       to the guidance system of agricultural vehicles", Int. J. Agric. Biol.
       Eng. 13(6):183-194, 2020, doi:10.25165/j.ijabe.20201306.6012 (IMU
       correction of the RTK antenna lateral error caused by tractor tilt;
       notes Trimble T3 and Deere iTC as commercial inclination-correction
       products).
Accuracy definitions:
  [I1] ISO 12188-2:2012, "Tractors and machinery for agriculture and forestry
       -- Test procedures for positioning and guidance systems in agriculture
       -- Part 2: Testing of satellite-based auto-guidance systems during
       straight and level travel" (confirmed 2023): performance criterion =
       lateral deviation (cross-track error, XTE) of a representative vehicle
       point from the desired trajectory, steady state, straight and LEVEL
       paths.  tracking_metrics() reports XTE statistics on the main area.
  [I2] J. D. Rounsaville, J. S. Dvorak, T. S. Stombaugh, "Methods for
       calculating relative cross-track error for ASABE/ISO standard 12188-2
       from discrete measurements", Trans. ASABE 59(6):1609-1616, 2016
       (the standard leaves the XTE computation unspecified; path
       interpolation recommended -- here: linear interpolation on a 1 m grid,
       core.pass_offsets).
  [V1] Deere StarFire 6000 / 7500 specifications: Radio RTK and Mobile RTK
       "+/- 2.5 cm (1.0 in.)" pass-to-pass; footnote: "Horizontal pass-to-pass
       accuracy specifications are 1D and are based upon a 15-minute time
       period, 95 percent confidence interval, clear view of the sky, no
       signal interference ..." -> VENDOR_P2P = 0.025 m, and the empirical
       analogue p2p95 = 95 % quantile of |e_{k+1}(x) - e_k(x)| between
       adjacent passes (adjacent passes are ~1-2 min apart, well inside the
       15 min window).  The claim is for level ground / ideal sky and does not
       include slope effects -- which is the point of the comparison.
  (The ISO full text was not accessible; the pass-to-pass definition used is
  the manufacturer's [V1], not a quotation of ISO 12188-2.)

Adaptation decisions (explicit)
-------------------------------
  V1 Position for the DEM lookup.  core.simulate does not pass the vehicle
     position to controllers, so VendorTC reconstructs it as a real system
     would from its own data: the AB-line start point of each pass (the field
     chord, as core.simulate starts each pass), dead-reckoned along-track
     distance s += v cos(psi_meas) dt, and the lateral position
     y_k + sgn * (previous corrected offset).  The error is cm-level, far
     below the 1 m DEM grid (selftest [1b] measures the effect).
  V2 Condition(comp = 0) EXACTLY.  The vendor system does not know the
     simulator's lumped compensation fraction; it receives the RAW antenna
     position and applies the FULL correction h sin(roll_imu) itself.
     Keeping comp = 0.85 would double-compensate (85 % over-correction,
     vehicle dragged downhill).  core.Condition(comp=0) alone would still add
     the per-run jitter clip(N(0, 0.05), 0, 1) (a spurious +2 % mean hidden
     compensation in half the runs), so vendor_condition() zeroes cond.comp
     after drawing; the random-number consumption is identical to
     core.Condition, preserving common random numbers.  The IMU noise / bias
     model replaces that jitter as the compensation-error model.
  V3 IMU noise is white at the control rate (pessimistic vs a gyro-fused
     roll; same order as the 0.10 deg roll/pitch spec of GNSS+MEMS receivers,
     e.g. the Javad TRE-DUO-IMU datasheet).  Values are the study's design
     values (0.15 deg noise, 0.1 deg per-run bias).
  V4 Feed-forward gain k_ff = 0.35 E[k_s] (E[k_s] = 0.15 + 0.85 E[m]
     E[LogN(0, 0.25)] = 0.5008 for m ~ Beta(2, 3)): the population-mean slip
     coefficient, i.e. what a manufacturer would calibrate on an average soil.
     No per-run information (cond.k_s, moisture, OU state, comp, mount, RTK
     series) is ever read; reset() ignores cond.  calibrate_ff() estimates
     the same gain from training runs (regression of the measured heading on
     the IMU side slope) and selftest [2] compares the two.
  V5 Pitch / yaw compensation are not modelled (the simulator has no
     roll-induced heading error and no pitch lever arm across track).
  V6 The mounting calibration error b_mount (vehicle frame) is NOT removed --
     a real system cannot observe it either.
"""
import math
import time
import warnings

import numpy as np

import core
import exp_lib

W_DEFAULT = 3.0
VENDOR_P2P = 0.025  # [m] vendor-claimed RTK pass-to-pass accuracy ([V1]: 1D, 15 min, 95 %)
ROLL_NOISE_DEG = 0.15
ROLL_BIAS_DEG = 0.10
# population-mean side-slip gain: beta = -0.35 k_s g_v, E[k_s] = 0.15 + 0.85 * E[Beta(2,3)] * E[LogN(0,0.25)]
E_KS = 0.15 + 0.85 * 0.4 * math.exp(0.25 ** 2 / 2)
K_FF_NOMINAL = 0.35 * E_KS


# --------------------------------------------------------------------------- controller
class VendorTC:
    """Terrain-compensated LQR-I autosteer (commercial practice), batched over
    (R runs, K passes).  Requires vendor_condition() (comp == 0), see module
    docstring V2.

    Parameters
    ----------
    field, ys : the field and the planned pass positions (the AB lines the
        system is following; used only for the pass start points and the DEM).
    tc : apply the antenna-roll correction meas + h sin(roll_imu).
    ff : apply the slope feed-forward (crab-angle reference k_ff tan(roll_imu)).
    k_ff : feed-forward gain [rad per unit side slope tan].
    roll_noise_deg, roll_bias_deg : IMU roll white noise / per-run bias std.
    seed : int / Generator / None for the controller's own IMU generator
        (created once; successive reset() calls continue its stream).
    record : accumulate the regression sums used by calibrate_ff().
    """

    raw_antenna = True  # execute() pairs it with vendor_condition()
    name = "vendor_tc"

    def __init__(self, field, ys, tc=True, ff=True, k_ff=K_FF_NOMINAL, roll_noise_deg=ROLL_NOISE_DEG,
                 roll_bias_deg=ROLL_BIAS_DEG, seed=None, record=False, t_settle=10.0):
        self.field, self.ys = field, np.asarray(ys, float)
        self.tc, self.ff, self.k_ff = tc, ff, k_ff
        self.sd_n, self.sd_b = math.radians(roll_noise_deg), math.radians(roll_bias_deg)
        self.rng = seed if isinstance(seed, np.random.Generator) else np.random.default_rng(seed)
        self.record, self.t_settle = record, t_settle
        K = len(self.ys)
        chords = [field.chord(field.P, y) for y in self.ys]  # same pass start points as core.simulate
        self.x0 = np.array([c[0] if c else 0.0 for c in chords])
        self.x1 = np.array([c[1] if c else 0.0 for c in chords])
        self.L = np.maximum(self.x1 - self.x0, 1.0)
        self.sgn = np.where(np.arange(K) % 2 == 0, 1.0, -1.0)
        self.sxy = self.sxx = 0.0
        self.n_rec = 0

    def reset(self, R, K, veh, cond=None):  # cond is deliberately never read (unknown to a real system)
        if K != len(self.ys):
            raise ValueError(f"VendorTC built for {len(self.ys)} passes, simulate has {K}")
        self.v, self.h, self.dmax = veh["v"], veh["h_ant"], veh["delta_max"]
        self.K1, self.K4 = core._lqr_gains(veh["v"], veh["l_wb"], veh["dt"])
        self.integ = np.zeros((R, K))
        self.s = np.zeros((R, K))  # dead-reckoned along-track distance
        self.d_hat = None  # previous corrected offset (lateral position for the DEM lookup)
        self.bias = self.rng.normal(0.0, self.sd_b, (R, 1))  # per-run IMU roll bias (same IMU on all passes)
        self.t = 0
        self.corr_abs = 0.0  # running sum of |h sin(roll_imu)| (diagnostic)
        self.corr_n = 0

    def roll_imu(self, meas):
        """IMU roll estimate (R, K) [rad] at the reconstructed vehicle position."""
        d_lat = meas if self.d_hat is None else self.d_hat
        x = np.where(self.sgn > 0, self.x0 + self.s, self.x1 - self.s)
        y = self.ys[None, :] + self.sgn * d_lat
        roll = np.arctan(self.sgn * self.field.gy(x, y))  # vehicle-frame roll (left side up > 0)
        return roll + self.bias + self.rng.normal(0.0, self.sd_n, meas.shape)

    def command(self, meas, psi_meas, delta, dt):
        e, p = meas, psi_meas
        if self.tc or self.ff or self.record:
            roll = self.roll_imu(meas)
            if self.tc:
                corr = self.h * np.sin(roll)  # antenna -> ground point (sign: see module docstring)
                e = meas + corr
                self.corr_abs += float(np.abs(corr).sum())
                self.corr_n += corr.size
            if self.ff:
                p = psi_meas - self.k_ff * np.tan(roll)  # course-angle error psi + beta_hat
            if self.record and self.t * dt >= self.t_settle:
                on = (self.s <= self.L[None, :])  # inside the field chord
                g = np.tan(roll)[on]
                self.sxy += float(np.sum(psi_meas[on] * g))
                self.sxx += float(np.sum(g * g))
                self.n_rec += int(on.sum())
            self.d_hat = e
        K4 = self.K4
        u_try = -(K4[0] * e + K4[1] * p + K4[2] * delta + K4[3] * (self.integ + e * dt))
        sat = np.abs(u_try) >= self.dmax
        self.integ = np.where(sat, self.integ, np.clip(self.integ + e * dt, -0.3, 0.3))
        u = -(K4[0] * e + K4[1] * p + K4[2] * delta + K4[3] * self.integ)
        self.s = self.s + self.v * np.cos(psi_meas) * dt
        self.t += 1
        return u

    def mean_correction(self):
        """Mean |h sin(roll_imu)| applied [m] over the last simulate call."""
        return self.corr_abs / max(self.corr_n, 1)


# ----------------------------------------------------------------------- execution
def vendor_condition(rng, n, **kw):
    """core.Condition with the simulator's lumped roll compensation switched off
    exactly (comp == 0, raw antenna position; see V2).  Same random-number
    consumption as core.Condition (common random numbers preserved)."""
    kw.pop("comp", None)
    cond = core.Condition(rng, n, comp=0.0, **kw)
    cond.comp[:] = 0.0
    return cond


def _make_ctrl(F, ys, ctrl, imu_seed):
    if callable(ctrl) and not isinstance(ctrl, str):
        return ctrl(F, ys, imu_seed)
    if ctrl in ("vendor", "vendor_tc"):
        return VendorTC(F, ys, seed=imu_seed)
    if ctrl == "vendor_noff":
        return VendorTC(F, ys, ff=False, seed=imu_seed)
    if ctrl in ("pure_pursuit", "stanley", "lqr", "lqr_i"):
        return ctrl
    raise KeyError(ctrl)


def execute(F, ys, n, rng, ctrl="vendor", imu_seed=None, **cond_kw):
    """Run n operations of plan ys.  Vendor controllers get vendor_condition()
    (comp == 0), built-ins the default core.Condition (comp = 0.85 unless
    given).  Returns X, D, cond, controller, simulate wall time [s]."""
    c = _make_ctrl(F, ys, ctrl, imu_seed)
    if getattr(c, "raw_antenna", False):
        cond = vendor_condition(rng, n, **cond_kw)
    else:
        cond = core.Condition(rng, n, **cond_kw)
    t0 = time.perf_counter()
    X, D = core.simulate(F, ys, cond, rng, ctrl=c)
    return X, D, cond, c, time.perf_counter() - t0


# --------------------------------------------------------------------- overlap rules
def nominal_overlap(p2p=VENDOR_P2P):
    """Manufacturer-derived nominal overlap: 2 x claimed pass-to-pass accuracy (0.05 m)."""
    return 2.0 * p2p


def plan_overlap(F, overlap, w=W_DEFAULT):
    """Boustrophedon plan with one global overlap: spacing w - overlap, swath
    edges overlap / 2 beyond the main-area boundary (core.plan, sigma = 1, lam = overlap / 2)."""
    return core.plan(F, w, overlap / 2.0, lambda f, y: 1.0)


def evaluate_overlap(F, overlap, n_runs, rng, ctrl="vendor", w=W_DEFAULT, imu_seed=None, **cond_kw):
    """P(no miss), E[miss], 95 % miss, passes and overlap ratio of the global-overlap plan."""
    ys = plan_overlap(F, overlap, w)
    X, D, _, _, sec = execute(F, ys, n_runs, rng, ctrl=ctrl, imu_seed=imu_seed, **cond_kw)
    miss = core.evaluate(F, ys, X, D, w)
    return dict(overlap=overlap, p_nomiss=float(np.mean(miss == 0)), e_miss=float(miss.mean()),
                p95_miss=float(np.percentile(miss, 95)), passes=len(ys),
                overlap_ratio=exp_lib.overlap_ratio(F, ys, w), sim_s=sec)


def farmer_tuned_overlap(train_fields, rng, target=0.9, w=W_DEFAULT, n_runs=30, ctrl="vendor", grid=0.01,
                         coarse=0.04, o_max=1.0, return_trace=False, **cond_kw):
    """Smallest single global overlap on a `grid` (1 cm) lattice with mean over
    the TRAINING fields of P(no miss) >= target ("tuned once" practice).

    Coarse upward scan (step `coarse`) to the first success, then a fine
    upward scan inside the last failing bracket.  Common random numbers per
    training field across candidates.  Returns the overlap [m] (np.inf with a
    warning if o_max is not enough), plus the trace {overlap: mean P} if
    return_trace."""
    seeds = rng.integers(0, 2 ** 31 - 1, size=(len(train_fields), 2))
    cache = {}

    def score(i):
        if i not in cache:
            ps = [evaluate_overlap(F, i * grid, n_runs, np.random.default_rng(int(s[0])), ctrl=ctrl, w=w,
                                   imu_seed=int(s[1]), **cond_kw)["p_nomiss"]
                  for F, s in zip(train_fields, seeds)]
            cache[i] = float(np.mean(ps))
        return cache[i]

    step = max(1, int(round(coarse / grid)))
    n_max = int(round(o_max / grid))
    i = 0
    while i <= n_max and score(i) < target:
        i += step
    if i > n_max:
        warnings.warn(f"farmer_tuned_overlap: target {target} not reached up to {o_max} m")
        best = np.inf
    else:
        best_i = i
        for j in range(max(i - step + 1, 0), i):
            if score(j) >= target:
                best_i = j
                break
        best = round(best_i * grid, 10)
    trace = {round(k * grid, 10): v for k, v in sorted(cache.items())}
    return (best, trace) if return_trace else best


def calibrate_ff(train_fields, rng, n_runs=20, w=W_DEFAULT, overlap=None, **cond_kw):
    """Data-driven feed-forward gain: least-squares slope (through the origin)
    of the measured heading on the IMU side slope tan(roll_imu), over the
    settled in-field samples of training runs of VendorTC without feed-forward
    (steady state on a slope: psi = -beta = 0.35 k_s g_v)."""
    sxy = sxx = 0.0
    o = nominal_overlap() if overlap is None else overlap
    for F in train_fields:
        ys = plan_overlap(F, o, w)
        seed = int(rng.integers(0, 2 ** 31 - 1))
        fac = lambda F_, ys_, s_: VendorTC(F_, ys_, ff=False, seed=s_, record=True)  # noqa: E731
        _, _, _, c, _ = execute(F, ys, n_runs, rng, ctrl=fac, imu_seed=seed, **cond_kw)
        sxy, sxx = sxy + c.sxy, sxx + c.sxx
    return sxy / sxx


# ------------------------------------------------------------------------ metrics
def tracking_metrics(F, ys, X, D):
    """ISO 12188-2-style cross-track error statistics on the main area [I1, I2]:
    rms / p95 of |XTE| (true field-frame lateral offset, path-interpolated on a
    1 m grid), mean |per-pass bias|, and the vendor-style pass-to-pass figure
    p2p95 = 95 % quantile of |e_{k+1}(x) - e_k(x)| over adjacent passes [V1]."""
    xg, off = exp_lib.offsets(F, ys, X, D, step=1.0)  # (K, R, nx)
    mask = np.zeros((len(ys), len(xg)), bool)
    for j, x in enumerate(xg):
        c = core._chord_x(F.M, x)
        if c is not None:
            mask[:, j] = (ys > c[0]) & (ys < c[1])
    full = np.broadcast_to(mask[:, None, :], off.shape)
    e = np.abs(off[full])
    e = e[np.isfinite(e)]
    m2 = mask[1:] & mask[:-1]
    dd = np.abs(off[1:] - off[:-1])[np.broadcast_to(m2[:, None, :], (len(ys) - 1,) + off.shape[1:])]
    dd = dd[np.isfinite(dd)]
    bias = [np.abs(np.nanmean(off[k][:, mask[k]], axis=1)) for k in range(len(ys)) if mask[k].sum() >= 10]
    bias = np.concatenate(bias) if bias else np.array([np.nan])
    return dict(rms=float(np.sqrt(np.mean(e ** 2))), p95=float(np.percentile(e, 95)),
                p2p95=float(np.percentile(dd, 95)) if dd.size else float("nan"), bias=float(np.mean(bias)))


# --------------------------------------------------------------------- verification
class _SlopeField:
    """Duck-typed constant side slope tan(theta) = g, one 400 m pass (rot = 0)."""

    def __init__(self, g, length=400.0):
        from shapely.geometry import box

        self.P = box(0.0, -20.0, length, 20.0)
        self.rot = 0.0
        self._g = g

    def gy(self, x, y):
        return np.full(np.shape(x), self._g, float)

    chord = core.Field.chord


class _SpyField:
    """Wraps a Field and records the DEM cells of the plant's (core.simulate)
    and the controller's gy() calls, which alternate within each step."""

    def __init__(self, F):
        self._F, self._calls = F, []

    def __getattr__(self, a):
        return getattr(self._F, a)

    def gy(self, x, y):
        F = self._F
        i = np.clip(np.rint(y - F.gy0).astype(int), 0, F.gy_map.shape[0] - 1)
        j = np.clip(np.rint(x - F.gx0).astype(int), 0, F.gy_map.shape[1] - 1)
        self._calls.append((i, j))
        return F.gy_map[i, j]

    def mismatch(self):
        plant, ctrl = self._calls[0::2], self._calls[1::2]
        n = bad = 0
        dr = []
        for (ip, jp), (ic, jc) in zip(plant, ctrl):
            m = (ip != ic) | (jp != jc)
            n += m.size
            bad += int(m.sum())
            if m.any():
                gm = self._F.gy_map
                dr.append(np.abs(np.arctan(gm[ip[m], jp[m]]) - np.arctan(gm[ic[m], jc[m]])))
        dr = np.degrees(np.concatenate(dr)).mean() if dr else 0.0
        return bad / max(n, 1), float(dr)


def _slope_test(ctrl_fac, comp, slope_deg=5.0, k_s=0.6, R=10, seed=0, imu=True):
    """Constant 5 deg side slope, RTK / mounting error / roughness off: the
    remaining offset is the controller's own (slip + roll-compensation) error."""
    F = _SlopeField(math.tan(math.radians(slope_deg)))
    ys = np.array([0.0])
    rng = np.random.default_rng(seed)
    cond = core.Condition(rng, R)
    cond.k_s[:], cond.rough[:], cond.comp[:], cond.mount[:] = k_s, 0.0, comp, 0.0
    cond.rtk_scale = 0.0
    X, D = core.simulate(F, ys, cond, rng, ctrl=ctrl_fac(F, ys))
    return X[0] - X[0][0], D[0]


def selftest(n_runs=50, seed=0, w=W_DEFAULT, test_fids=(34, 174), train_fids=(98, 177), n_train=30, target=0.9):
    t_all = time.time()
    veh = core.VEH
    h = veh["h_ant"]
    print(f"vendor selftest  (h_ant={h} m, IMU roll noise {ROLL_NOISE_DEG} deg, per-run bias {ROLL_BIAS_DEG} deg, "
          f"k_ff = 0.35 E[k_s] = {K_FF_NOMINAL:.4f}, vendor p2p claim {100 * VENDOR_P2P:.1f} cm -> nominal overlap "
          f"{100 * nominal_overlap():.1f} cm)")
    Fs = {F.fid: F for F in core.load_fields("paddy", w=w)}
    tests, trains = [Fs[i] for i in test_fids], [Fs[i] for i in train_fids]

    # ------------------------------------------------------------- 1. consistency
    print("\n[1] consistency checks (field %d, 10 runs, common random numbers)" % test_fids[0])
    F = tests[0]
    ys = plan_overlap(F, nominal_overlap(), w)
    rng = np.random.default_rng(seed)
    X0, D0 = core.simulate(F, ys, core.Condition(rng, 10), rng, ctrl="lqr_i")
    rng = np.random.default_rng(seed)
    X1, D1 = core.simulate(F, ys, core.Condition(rng, 10), rng, ctrl=VendorTC(F, ys, tc=False, ff=False, seed=1))
    dmax = max(float(np.abs(a - b).max()) for a, b in zip(D0, D1))
    print(f"  [1a] VendorTC(tc=off, ff=off), comp=0.85  vs built-in lqr_i: max |dD| = {dmax:.1e} m (bit-for-bit)")
    assert dmax == 0.0
    rng = np.random.default_rng(seed)
    c_ideal = core.Condition(rng, 10)
    c_ideal.comp[:] = 1.0  # perfect (oracle) roll compensation inside the simulator
    X2, D2 = core.simulate(F, ys, c_ideal, rng, ctrl="lqr_i")
    rng = np.random.default_rng(seed)
    spy = _SpyField(F)
    X3, D3 = core.simulate(spy, ys, vendor_condition(rng, 10), rng,
                           ctrl=VendorTC(spy, ys, ff=False, roll_noise_deg=0.0, roll_bias_deg=0.0, seed=1))
    dd = np.concatenate([np.abs(a - b).ravel() for a, b in zip(D2, D3)])
    mis, droll = spy.mismatch()
    print(f"  [1b] VendorTC(tc, noise-free IMU), comp=0  vs lqr_i with oracle comp=1: |dD| mean {1e3 * dd.mean():.3f} mm,"
          f" max {1e3 * dd.max():.1f} mm")
    print(f"       residual = reconstructed-position DEM-cell lookups (V1): {100 * mis:.2f} % of the controller's "
          f"lookups hit another 1 m cell than the plant's, mean |d roll| there {droll:.2f} deg")
    assert mis < 0.02 and dd.mean() < 1e-3
    print("  [1c] constant 5 deg side slope, k_s=0.6, no RTK / mount / roughness, 400 m pass, 10 runs:")
    print(f"       {'controller':34s} {'ss offset mm':>12s} {'ss sd mm':>8s} {'peak|e| 0-40 m mm':>18s}")
    roll_off = 1e3 * h * math.sin(math.radians(5)) * 0.15
    for lab, fac, comp in [("lqr_i, comp=0.85", lambda F_, ys_: "lqr_i", 0.85),
                           ("VendorTC tc only, comp=0", lambda F_, ys_: VendorTC(F_, ys_, ff=False, seed=3), 0.0),
                           ("VendorTC tc+ff, comp=0", lambda F_, ys_: VendorTC(F_, ys_, seed=3), 0.0),
                           ("VendorTC tc+ff, comp=0.85 (WRONG)", lambda F_, ys_: VendorTC(F_, ys_, seed=3), 0.85)]:
        s, D = _slope_test(fac, comp)
        tail = D[:, s >= 200]
        print(f"       {lab:34s} {1e3 * tail.mean():+12.2f} {1e3 * tail.std():8.2f} "
              f"{1e3 * np.abs(D[:, s <= 40]).max():18.1f}")
    print(f"       (expected: lqr_i uphill offset +{roll_off:.1f} mm = h sin5 (1-0.85); VendorTC ~ IMU-bias level "
          f"{1e3 * h * math.sin(math.radians(ROLL_BIAS_DEG)):.1f} mm sd; full TC on top of comp=0.85 over-corrects "
          f"by {1e3 * h * math.sin(math.radians(5)) * 0.85:.0f} mm downhill)")

    # ------------------------------------------------------------- 2. feed-forward gain
    t0 = time.time()
    k_hat = calibrate_ff(trains, np.random.default_rng(seed + 1), n_runs=20, w=w)
    print(f"\n[2] feed-forward gain: nominal 0.35 E[k_s] = {K_FF_NOMINAL:.4f};  calibrate_ff on training fields "
          f"{train_fids} (20 runs each) = {k_hat:.4f}  ({time.time() - t0:.1f} s)")

    # ------------------------------------------------------------- 3. tracking on test fields
    print(f"\n[3] tracking on the test paddy fields {test_fids}, nominal overlap plan "
          f"({100 * nominal_overlap():.0f} cm), {n_runs} runs, common random numbers (seed {seed}).")
    print("    XTE = true field-frame lateral offset on the main area (ISO 12188-2 criterion); p2p95 = 95 % |XTE_k+1 -"
          " XTE_k| over adjacent passes (vendor-style pass-to-pass, claim 25 mm); |corr| = mean |h sin(roll_imu)|")
    specs = [("lqr_i (built-in, comp=0.85)", "lqr_i"), ("VendorTC tc only (comp=0)", "vendor_noff"),
             ("VendorTC tc+ff (comp=0)", "vendor")]
    res3 = {}
    for F in tests:
        ys = plan_overlap(F, nominal_overlap(), w)
        print(f"\n  field {F.fid}: {len(ys)} passes, main area {F.M.area:.0f} m2, mean slope {F.z_mean_slope:.2f} deg")
        print(f"  {'controller':30s} {'RMS XTE mm':>10s} {'p95 mm':>7s} {'p2p95 mm':>8s} {'|bias| mm':>9s} "
              f"{'P(no miss)':>10s} {'E[miss]':>8s} {'|corr| mm':>9s} {'sim s':>6s}")
        for lab, ctrl in specs:
            rng = np.random.default_rng(seed)
            X, D, _, c, sec = execute(F, ys, n_runs, rng, ctrl=ctrl, imu_seed=seed + 7)
            m = tracking_metrics(F, ys, X, D)
            miss = core.evaluate(F, ys, X, D, w)
            corr = f"{1e3 * c.mean_correction():9.1f}" if isinstance(c, VendorTC) else f"{'-':>9s}"
            res3[(F.fid, ctrl)] = m
            print(f"  {lab:30s} {1e3 * m['rms']:10.1f} {1e3 * m['p95']:7.1f} {1e3 * m['p2p95']:8.1f} "
                  f"{1e3 * m['bias']:9.1f} {np.mean(miss == 0):10.2f} {miss.mean():8.5f} {corr} {sec:6.2f}")
        assert res3[(F.fid, "vendor")]["rms"] < res3[(F.fid, "lqr_i")]["rms"], "TC did not reduce XTE on a hilly field"

    # ------------------------------------------------------------- 4. overlap settings
    t0 = time.time()
    o_f, trace = farmer_tuned_overlap(trains, np.random.default_rng(seed + 2), target=target, w=w, n_runs=n_train,
                                      return_trace=True)
    nsim = len(trace) * len(trains)
    print(f"\n[4] overlap settings with VendorTC (comp=0).  farmer_tuned_overlap on training fields {train_fids}, "
          f"{n_train} runs/field/candidate, target {target}:")
    print("    search trace (overlap cm: mean P(no miss)): " +
          ", ".join(f"{100 * o:.0f}: {p:.2f}" for o, p in trace.items()))
    print(f"    -> farmer-tuned overlap = {100 * o_f:.0f} cm  ({nsim} simulations, {time.time() - t0:.1f} s)")
    assert trace[o_f] >= target and all(p < target for o, p in trace.items() if o < o_f - 1e-9)
    print(f"\n  test fields {test_fids}, {n_runs} fresh runs (seed {seed + 100}), VendorTC tc+ff:")
    print(f"  {'field':>5s} {'setting':14s} {'overlap cm':>10s} {'passes':>6s} {'overlap %':>9s} {'P(no miss)':>10s} "
          f"{'E[miss]':>8s} {'p95 miss':>8s}")
    for F in tests:
        for lab, o in (("nominal", nominal_overlap()), ("farmer-tuned", o_f)):
            r = evaluate_overlap(F, o, n_runs, np.random.default_rng(seed + 100), w=w, imu_seed=seed + 101)
            print(f"  {F.fid:5d} {lab:14s} {100 * o:10.0f} {r['passes']:6d} {100 * r['overlap_ratio']:9.2f} "
                  f"{r['p_nomiss']:10.2f} {r['e_miss']:8.5f} {r['p95_miss']:8.5f}")
    print(f"\nselftest passed in {time.time() - t_all:.1f} s")


if __name__ == "__main__":
    selftest()

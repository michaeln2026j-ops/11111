"""Sideslip-observer adaptive path tracking in presence of sliding
(Lenain, Thuilot, Cariou & Martinet, 2006-2007), as a pluggable controller for core.simulate.

References (citations checked 2026-10-13, see "Verification" below)
-------------------------------------------------------------------
[1] R. Lenain, B. Thuilot, C. Cariou, P. Martinet, "High accuracy path tracking
    for vehicles in presence of sliding: Application to farm vehicle automatic
    guidance for agricultural tasks", Autonomous Robots 21(1):79-97, 2006.
    doi:10.1007/s10514-006-7806-4  (HAL: hal-02588284)
[2] R. Lenain, B. Thuilot, C. Cariou, P. Martinet, "Adaptive and predictive path
    tracking control for off-road mobile robots", European Journal of Control
    13(4):419-439, 2007. doi:10.3166/ejc.13.419-439  (HAL: hal-02589667)
[3] R. Lenain, B. Thuilot, C. Cariou, P. Martinet, "Sideslip angles observer for
    vehicle guidance in sliding conditions: application to agricultural path
    tracking tasks", Proc. IEEE ICRA 2006, Orlando FL, May 2006
    (HAL: hal-00094497).

Verification. Web search confirmed the following:
  [1] authors, title, journal, 21(1):79-97, 2006, and the DOI (Springer
      article URL); HAL record hal-02588284.
  [2] authors, title, journal, 13(4):419-439, 2007, and the DOI (Crossref,
      HAL and ETH research-collection records).
  [3] authors, title and venue (HAL record and the authors' PDF on
      pagesperso.ls2n.fr). Page numbers were NOT confirmed.
The full texts could not be fetched from this machine because the publisher,
HAL and author sites do not resolve. The method summary below therefore
comes from the abstracts:
  [1]: sliding effects; RTK-GPS; previous laws inaccurate only at curvature
       transitions; MPC added.
  [2]: nonlinear law plus MPC for off-road robots with poor adherence.
  [3]: observer-like estimator of the sideslip angles from a single RTK-GPS.
The straight-line law quoted below is the group's published structure as
recalled, NOT re-checked against the full text. The controller implemented
here does not depend on that quotation: it is re-derived for the simulator's
model (A1). Check the equation-level details against the PDFs before
submission.

What the published method does
------------------------------
* Extended kinematic model [1,3]. A bicycle model in curvilinear coordinates
  (s, y, theta~) relative to the reference path, with two sliding parameters
  beta_R and beta_F. Each is the angle between the wheel plane and the actual
  velocity vector at the rear or front tyre centre. They cannot be measured, so
  the sliding-compensated law depends on estimating them.
* Control law [1,2]. Exact linearisation of the extended model by conversion
  to chained form. The lateral error y obeys y'' + K_p y' + K_d y = 0, where
  ' = d/ds is with respect to curvilinear abscissa. The convergence is
  therefore independent of speed, and the gains are set by a settling
  distance. For a straight reference (c(s) = 0) the published front-steering
  law reduces to
      delta_F = atan( tan(beta_R) + L/cos(beta_R) * cos^3(th2) * (-K_p tan th2 - K_d y) ) - beta_F,
      th2 = theta~ + beta_R.
* Sideslip estimation [3]. An observer-like estimator built on the extended
  kinematic model. It uses only RTK-GPS lateral and heading information,
  together with the measured steering.
* Predictive layer [1,2]. Model predictive control of the curvature
  (feed-forward) part of the law, using a first-order actuator model. It
  anticipates actuator delay at curvature transitions.

Adaptation to this codebase (explicit decisions)
------------------------------------------------
A1  Model. core.simulate drives straight passes (c = 0) with
        d' = v sin(psi + beta),   psi' = v tan(delta)/l,   delta' = (u - delta)/tau  (rate-limited),
    so beta plays the role of beta_R in the lateral equation. The simulator
    has no front-axle slip (beta_F = 0), and its yaw equation does not contain
    beta_R. Exact linearisation of THIS model with
    a2 = d, a3 = tan(psi + beta) and da3/ds = -K_d a2 - K_p a3 gives
        delta* = atan( l cos^3(th2) (-K_d d - K_p tan th2) ),   th2 = psi + beta,
    which is the paper's law with the tan(beta_R), 1/cos(beta_R) and beta_F
    terms removed. Those terms compensate yaw-rate couplings that this
    simulator does not have. Keeping them here would leave a steady-state
    offset d = sin(beta)/(l K_d), about 2.6 cm at beta = 0.026 rad. The
    sliding compensation is the use of th2: the controller aligns the velocity
    vector, not the chassis, with the line.
    With a correct beta estimate this removes the classical slope offset
    without integral action.
A2  Observer. The internal construction of the observer in [3] could not be
    checked (see Verification). Following the task specification, it is
    implemented as a steady-state Kalman/Luenberger observer. Its state is
    x = [d, psi, beta], beta is a random walk, and the measurements are
    y = [meas, psi_meas]. It runs on the model of A1, linearised and
    discretised at dt with the simulator's update order:
        A = [[1, v dt, v dt], [0, 1, 0], [0, 0, 1]],  C = [[1,0,0],[0,1,0]],
    input tan(delta) through B = [0, v dt/l, 0]^T. The gains come from the
    DARE through scipy.linalg.solve_discrete_are (filter form). Propagation
    uses the nonlinear model with the measured steering angle. As in [3], the
    only exteroceptive input is the RTK-GNSS solution (lateral offset and
    heading), together with the measured steering angle.
    Noise intensities: Q = diag(q_d, q_psi, q_beta)^2, R = diag(r_d, r_psi)^2.
    Tuning protocol: grid search on two hilly paddy fields NOT used by the
    selftest (ids 98 and 177, nominal plan, 20 runs, seed 7). The grid
    covered q_beta in [2e-4, 0.1] rad/step, r_d in [0.01, 0.2] m, omega_n in
    {1.0, 1.23, 1.4, 1.6} rad/s, xi in {0.7, 0.85, 1}, H in {0, tau, 0.4 s},
    gate in {None, 5 cm} and reject in {None, 6, 8, 10, 12 cm}. Results on
    the tuning fields:
      design                        RMS  p99  pair-sd  steer-rate RMS  jump peak
      default (effort-matched)      4.49 12.4  5.04 cm   2.8 deg/s     23.9 cm
      robust  (default + reject 8)  4.49 12.1  5.02      2.5            4.2
      fast    (tracking-optimal)    3.83 10.3  3.67      7.8            9.8
      LQR-I   (built-in)            4.59 12.3  5.70      2.9           18.7
      Stanley (built-in)            4.14 11.4  5.83      1.4           19.9
    default  r_d = 0.04 m, q_beta = 5e-3 rad/step, q_d = 2e-3 m,
             q_psi = 1e-4 rad, r_psi = 0.15 deg. This is the lowest RMS
             whose steering-rate RMS does not exceed that of the built-in
             LQR-I, an equal-control-effort comparison. It also matches the
             physical error levels:
               - r_d: real RTK lateral sd is about 1.1 cm at 1 Hz, held for
                 20 steps, so the white-equivalent sd at 20 Hz is about
                 1.1 cm * sqrt(20) = 5 cm.
               - q_beta: a 2 s-correlated sideslip of sd 0.015 rad has a
                 per-step increment sd of 3.4e-3 rad.
             So beta is a genuinely slowly varying random walk. Observer
             poles |0.92|, |0.92| (d/beta, about 0.6 s) and |0.963|
             (psi, 1.3 s).
    fast     [LenainSSO.fast()]: r_d = 0.01 m, q_beta = 0.05, the minimum-RMS
             point with no effort constraint. Observer poles |0.595|
             (0.1 s). Within each 1 s hold of the real RTK error,
             differences of the measurement are exact, so a nearly
             differentiating beta channel follows the 2 s-correlated slip.
             The price is 2.7x the LQR-I steering-rate RMS, 1-Hz steering
             spikes (rate limit active on about 2 % of steps), and partial
             exploitation of the 1-Hz zero-order hold of the RTK series. It
             is reported as an upper bound for the method, not as the
             default.
    The innovation clip (`gate`) made every setting worse, because it
    prolongs the jump transient, so it is off.
A3  Predictive steering-lag compensation. On straight passes the curvature
    feed-forward that [1,2] handle with MPC is identically zero. The
    actuator-lag compensation is therefore applied to the feedback part: the
    law A1 is evaluated at the first-order prediction of the observer state
    one actuator time constant ahead (H = tau = 0.25 s),
        d_p = d^ + H v sin(th2^),   th2_p = th2^ + H v tan(delta)/l.
    For the linearised loop with lag 1/(tau s + 1) this gives the exact
    characteristic polynomial
        (tau s + 1)(s^2 + v K_p s + v^2 K_d),
    so the design poles of [1] are kept and the actuator pole is only
    appended (asserted in selftest). Without prediction, at xi = 1, the
    poles move to -0.84 and -1.58 +/- 2.16j (damping 0.59), which is faster
    and less damped. predict=False is reported as an ablation: it trades
    damping for bandwidth, with slightly lower RMS but a larger jump
    response. This is the same prediction-over-the-actuator-model idea as
    [1,2], applied to the deviation term.
A4  Gains. omega_n = 1.23 rad/s matches the dominant closed-loop pair of the
    built-in lag-augmented LQR-I (|-0.86 +/- 0.88j| = 1.23 rad/s), so the two
    have the same bandwidth. xi = 1.0 was the best damping on the tuning grid
    (xi = 0.85: +0.4 mm RMS; xi = 0.7: about +1 mm). At equal steering
    effort, omega_n = 1.0 with a faster observer was no better.
        K_d = (omega_n / v)^2 = 0.378 1/m^2,   K_p = 2 xi omega_n / v = 1.23 1/m,
    a critically damped convergence over a settling distance (5 %) of about
    4.74 v / omega_n = 7.7 m.
A5  Robustness to RTK jumps and the steering rate limit. The loop has no
    integrator, so nothing winds up when the steering is rate- or
    angle-limited. The observer always propagates with the measured steering
    angle, so its model stays consistent under saturation. The selftest
    places the real 21 cm / 2 s jump of the i2Nav series (index 1168) on a
    flat stub strip. Without any outlier logic (the published method) the
    response is bounded and decays: peak 24 cm, against 18.7 cm for LQR-I.
    The beta channel reads the jump as transient slip, and this produces the
    small overshoot. The asserted bound is a peak below 1.25 x the jump
    amplitude with no sustained rate saturation.
    Optional `reject` (metres; [1-3] have none) adds an innovation-outlier
    test: a position update whose innovation exceeds `reject` is skipped,
    and the observer coasts on the model with the heading measurement.
    After more than `reject_max_s` = 3 s of continuous rejection d^ is
    re-acquired from the receiver. With reject = 8 cm (the robust preset)
    the jump peak falls to 4 cm, and RMS and pair-sd are unchanged on the
    tuning fields. A threshold near the projected jump amplitude is fragile:
    a partly accepted outlier makes the true epochs look like outliers until
    re-acquisition. Experiments must state which variant they use: the
    faithful default or the robust preset.
A6  Information. The controller sees only meas, psi_meas, delta, the known
    vehicle parameters (v, l_wb, tau, delta_max, rate_max) and its own state.
    It never reads cond.k_s, OU state, comp, mount or the RTK series.
    Constant antenna biases (residual roll offset, mounting error) are
    unobservable from these signals, exactly as for the other controllers.

API
---
LenainSSO(omega_n=1.23, xi=1.0, horizon=None (= tau), r_d=0.04, r_psi=deg2rad(0.15),
          q_d=2e-3, q_psi=1e-4, q_beta=5e-3, gate=None, reject=None, reject_max_s=3.0,
          compensate=True, predict=True)
LenainSSO.fast(**kw)     tracking-optimal observer (A2), r_d=0.01, q_beta=0.05
LenainSSO.robust(**kw)   default + innovation-outlier rejection at 8 cm (A5)
    reset(R, K, veh, cond) / command(meas, psi_meas, delta, dt) -> delta_cmd (R, K)
    .beta_hat, .d_hat, .psi_hat : observer state (R, K) after the last call
    .L : observer gain (3 x 2);  .Kd, .Kp : chained-form gains;  .stats : diagnostics
    compensate=False gives the classical no-sliding chained-form law on the
    raw measurements (no observer, beta^ = 0; on a constant slip it keeps the
    offset (K_p/K_d + H v) tan(beta)). predict=False removes the lag
    compensation. Both are for ablation.
    .summary() -> steering activity (rate_rms_dps, rate_limited, angle_limited, max|delta|, max|beta^|)
BuiltinProbe("lqr_i" | "stanley")   exact pluggable replica of the built-ins with the same
                                    steering-activity diagnostics (equality asserted in selftest)
tracking_metrics(F, ys, X, D) -> dict(rms, p99, pair_sd)
evaluate_controller(F, ctrl_factory, n, seed, w, overlaps) -> dict (adds steering activity)
selftest(n_runs=50, w=3.0, seed=0)
"""
import math
import os
import sys
import time

import numpy as np
from scipy.linalg import solve_discrete_are

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core  # noqa: E402
import exp_lib  # noqa: E402

W_DEFAULT = 3.0


class LenainSSO:
    """Chained-form path tracking with sideslip observer and lag-predictive compensation."""

    name = "lenain_sso"

    def __init__(self, omega_n=1.23, xi=1.0, horizon=None, r_d=0.04, r_psi=math.radians(0.15),
                 q_d=2e-3, q_psi=1e-4, q_beta=5e-3, gate=None, reject=None, reject_max_s=3.0,
                 compensate=True, predict=True, veh=None):
        self.omega_n, self.xi = float(omega_n), float(xi)
        self.horizon = horizon
        self.r_d, self.r_psi = float(r_d), float(r_psi)
        self.q = (float(q_d), float(q_psi), float(q_beta))
        self.gate = gate
        self.reject, self.reject_max_s = reject, float(reject_max_s)
        self.compensate, self.predict = bool(compensate), bool(predict)
        self._design(veh or core.VEH)

    @classmethod
    def fast(cls, **kw):
        """Tracking-optimal observer without steering-effort constraint (A2)."""
        return cls(**{**dict(r_d=0.01, q_beta=0.05), **kw})

    @classmethod
    def robust(cls, **kw):
        """Default design plus innovation-outlier rejection of RTK jumps (A5)."""
        return cls(**{**dict(reject=0.08), **kw})

    # ------------------------------------------------------------------ design
    def _design(self, veh):
        self.v, self.l, self.dt = veh["v"], veh["l_wb"], veh["dt"]
        self.tau, self.dmax, self.rmax = veh["tau"], veh["delta_max"], veh["rate_max"]
        self.H = self.tau if self.horizon is None else float(self.horizon)
        # chained-form gains in the distance domain: y'' + Kp y' + Kd y = 0 (d/ds)
        self.Kd = (self.omega_n / self.v) ** 2
        self.Kp = 2.0 * self.xi * self.omega_n / self.v
        v, l, dt = self.v, self.l, self.dt
        A = np.array([[1.0, v * dt, v * dt], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        C = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        Q = np.diag(np.square(self.q))
        Rm = np.diag([self.r_d ** 2, self.r_psi ** 2])
        P = solve_discrete_are(A.T, C.T, Q, Rm)  # a-priori steady-state covariance
        L = P @ C.T @ np.linalg.inv(C @ P @ C.T + Rm)  # filter-form gain
        self.L, self.P = L, P
        self.A, self.C = A, C
        # observer error dynamics (posterior): (I - L C) A must be Schur
        self.obs_eig = np.linalg.eigvals((np.eye(3) - L @ C) @ A)
        assert np.all(np.abs(self.obs_eig) < 1.0), "observer not stable"

    # -------------------------------------------------------------- controller
    def reset(self, R, K, veh, cond):
        if veh is not None and (veh["v"], veh["l_wb"], veh["dt"], veh["tau"]) != (self.v, self.l, self.dt, self.tau):
            self._design(veh)
        self.d_hat = self.psi_hat = self.beta_hat = None
        self.stats = _new_stats()
        self.stats.update(gated=0.0, max_abs_beta=0.0, rejected=0.0)
        self._nrej = None

    def _observe(self, meas, psi_meas, delta):
        if not self.compensate:  # ablation: classical no-sliding chained-form law on raw measurements
            self.d_hat, self.psi_hat = np.asarray(meas, float), np.asarray(psi_meas, float)
            self.beta_hat = np.zeros_like(self.d_hat)
            return
        if self.d_hat is None:  # first epoch of the passes: initialise on the measurements
            self.d_hat = np.array(meas, dtype=float)
            self.psi_hat = np.array(psi_meas, dtype=float)
            self.beta_hat = np.zeros_like(self.d_hat)
            return
        v, l, dt = self.v, self.l, self.dt
        # time update (simulator order: d uses previous psi, psi uses the current steering)
        d_pr = self.d_hat + v * np.sin(self.psi_hat + self.beta_hat) * dt
        p_pr = self.psi_hat + v * np.tan(delta) / l * dt
        b_pr = self.beta_hat
        e_d, e_p = meas - d_pr, psi_meas - p_pr
        if self.gate is not None:
            g = np.abs(e_d) > self.gate
            self.stats["gated"] += float(g.mean())
            e_d = np.clip(e_d, -self.gate, self.gate)
        if self.reject is not None:  # innovation outlier rejection with forced re-acquisition
            if self._nrej is None:
                self._nrej = np.zeros(e_d.shape, int)
            out = np.abs(e_d) > self.reject
            self._nrej = np.where(out, self._nrej + 1, 0)
            reacq = self._nrej * dt > self.reject_max_s
            skip = out & ~reacq
            self.stats["rejected"] += float(skip.mean())
            e_d = np.where(skip, 0.0, e_d)
            d_pr = np.where(reacq, meas, d_pr)  # persistent disagreement: trust the receiver again
            e_d = np.where(reacq, 0.0, e_d)
            self._nrej = np.where(reacq, 0, self._nrej)
        L = self.L
        self.d_hat = d_pr + L[0, 0] * e_d + L[0, 1] * e_p
        self.psi_hat = p_pr + L[1, 0] * e_d + L[1, 1] * e_p
        self.beta_hat = b_pr + L[2, 0] * e_d + L[2, 1] * e_p

    def law(self, d, th2):
        """Exact-linearisation steering for d' = v sin th2, th2' = v tan(delta)/l (c = 0)."""
        return np.arctan(self.l * np.cos(th2) ** 3 * (-self.Kd * d - self.Kp * np.tan(th2)))

    def command(self, meas, psi_meas, delta, dt):
        self._observe(meas, psi_meas, delta)
        th2 = self.psi_hat + (self.beta_hat if self.compensate else 0.0)
        d = self.d_hat
        if self.predict:  # first-order prediction over the actuator time constant (A3)
            d = d + self.H * self.v * np.sin(th2)
            th2 = th2 + self.H * self.v * np.tan(delta) / self.l
        u = np.clip(self.law(d, th2), -self.dmax, self.dmax)
        _update_stats(self.stats, u, delta, self.tau, self.rmax, self.dmax, self.dt)
        self.stats["max_abs_beta"] = max(self.stats["max_abs_beta"], float(np.abs(self.beta_hat).max()))
        return u

    def summary(self):
        out = _summary(self.stats)
        out.update(max_abs_beta_hat_deg=math.degrees(self.stats["max_abs_beta"]),
                   gated=self.stats["gated"] / max(self.stats["steps"], 1))
        return out

    def linear_poles(self):
        """Continuous closed-loop poles of the linearised tracking loop with actuator lag
        (perfect state knowledge); with predict=True they are the design pair plus -1/tau."""
        v, l, tau, H = self.v, self.l, self.tau, (self.H if self.predict else 0.0)
        # x = [d, th2, delta], u = -l Kd (d + H v th2) - l Kp (th2 + H v delta / l)
        Acl = np.array([[0.0, v, 0.0], [0.0, 0.0, v / l],
                        [-l * self.Kd / tau, -l * (self.Kd * H * v + self.Kp) / tau, (-1.0 - self.Kp * H * v) / tau]])
        return np.linalg.eigvals(Acl)


# ------------------------------------------------- steering-activity diagnostics
def _new_stats():
    return dict(steps=0, rate_limited=0.0, angle_limited=0.0, max_abs_delta=0.0, rate_ss=0.0, rate_n=0,
                prev=None)


def _update_stats(s, u, delta, tau, rmax, dmax, dt):
    s["steps"] += 1
    s["rate_limited"] += float((np.abs(u - delta) / tau > rmax).mean())
    s["angle_limited"] += float((np.abs(u) >= dmax).mean())
    s["max_abs_delta"] = max(s["max_abs_delta"], float(np.abs(delta).max()))
    if s["prev"] is not None:  # actual steering rate from consecutive steering angles
        s["rate_ss"] += float(np.sum(((delta - s["prev"]) / dt) ** 2))
        s["rate_n"] += delta.size
    s["prev"] = np.array(delta, dtype=float)


def _summary(s):
    n = max(s["steps"], 1)
    return dict(rate_limited=s["rate_limited"] / n, angle_limited=s["angle_limited"] / n,
                max_abs_delta_deg=math.degrees(s["max_abs_delta"]),
                rate_rms_dps=math.degrees(math.sqrt(s["rate_ss"] / max(s["rate_n"], 1))))


class BuiltinProbe:
    """Pluggable replica of core.simulate's built-in 'stanley' / 'lqr_i' branches, used only to
    record the same steering-activity diagnostics for the reference controllers; selftest asserts
    it reproduces the built-in trajectories exactly."""

    def __init__(self, name):
        assert name in ("stanley", "lqr_i")
        self.name = name

    def reset(self, R, K, veh, cond):
        self.veh, self.integ = veh, np.zeros((R, K))
        self.K4 = core._lqr_gains(veh["v"], veh["l_wb"], veh["dt"])[1]
        self.stats = _new_stats()

    def command(self, meas, psim, delta, dt):
        veh = self.veh
        if self.name == "stanley":
            u = -psim - np.arctan(1.2 * meas / veh["v"])
        else:
            K4 = self.K4
            u_try = -(K4[0] * meas + K4[1] * psim + K4[2] * delta + K4[3] * (self.integ + meas * dt))
            sat = np.abs(u_try) >= veh["delta_max"]
            self.integ = np.where(sat, self.integ, np.clip(self.integ + meas * dt, -0.3, 0.3))
            u = -(K4[0] * meas + K4[1] * psim + K4[2] * delta + K4[3] * self.integ)
        _update_stats(self.stats, np.clip(u, -veh["delta_max"], veh["delta_max"]), delta, veh["tau"],
                      veh["rate_max"], veh["delta_max"], dt)
        return u

    def summary(self):
        return _summary(self.stats)


# ---------------------------------------------------------------------- metrics
def tracking_metrics(F, ys, X, D):
    """RMS / p99 of the true field-frame lateral error over the main-area x-range, and the
    sd of the pass-to-pass offset difference (exp_lib.pair_diffs)."""
    _, off = exp_lib.offsets(F, ys, X, D)
    e = np.abs(off[np.isfinite(off)])
    pdiff = exp_lib.pair_diffs(F, ys, X, D)
    return dict(rms=float(np.sqrt(np.mean(e ** 2))), p99=float(np.percentile(e, 99)),
                pair_sd=float(np.std(pdiff)))


def evaluate_controller(F, ctrl_factory, n=50, seed=0, w=W_DEFAULT, overlaps=(0.05, 0.10)):
    """Common-random-number evaluation: the same seed -> identical conditions and noise for
    every controller. Tracking metrics on the nominal plan (spacing w); P(no miss) on plans
    with overlap o (spacing w - o, core.plan with lam = o/2, sigma = 1)."""
    out = {}
    ys = core.plan(F, w, 0.0, lambda f, y: 1.0)
    t = time.time()
    c = ctrl_factory()
    X, D, _ = exp_lib.run(F, ys, n, np.random.default_rng(seed), ctrl=c, w=w)
    out["sim_s"] = time.time() - t
    out.update(tracking_metrics(F, ys, X, D))
    if hasattr(c, "summary"):
        out.update(c.summary())
    out["passes"] = len(ys)
    for o in overlaps:
        yo = core.plan(F, w, o / 2.0, lambda f, y: 1.0)
        r = exp_lib.evaluate_plan(F, yo, n, np.random.default_rng(seed + 1), w=w, ctrl=ctrl_factory())
        out[f"p_nomiss_{o}"] = r["p_nomiss"]
        out[f"e_miss_{o}"] = r["e_miss"]
        out[f"overlap_{o}"] = r["overlap"]
    return out


# --------------------------------------------------------------- unit checks
class _StubField:
    """Flat straight test strip (rot = 0, field +y = north) with constant lateral slope."""

    def __init__(self, length=200.0, slope=0.0):
        self.rot, self.P, self._g, self._L = 0.0, None, slope, length

    def chord(self, poly, y):
        return (0.0, self._L)

    def gy(self, x, y):
        return np.full(np.shape(x), self._g)


class _StubCond:
    def __init__(self, n, k_s=0.0, rough=0.0, comp=1.0, mount=0.0, rtk_offset=0, rtk_scale=0.0):
        self.k_s, self.rough = np.full(n, k_s), np.full(n, rough)
        self.comp, self.mount = np.full(n, comp), np.full(n, mount)
        self.rtk_offset = np.full(n, rtk_offset, dtype=int)
        self.rtk_scale = rtk_scale


def _step_and_jump_checks(ctrls):
    """(a) constant sideslip on a 5% side slope with k_s = 1.5 (beta = -0.026 rad), no RTK
    noise: steady-state offset of the true position over the last 50 m; (b) real RTK
    series with its 21 cm / 2 s jump placed 30 s into the pass, flat ground: peak |d| in
    the 15 s after the jump vs the p99 |d| elsewhere."""
    res = {}
    for name, mk in ctrls.items():
        F = _StubField(slope=0.05)
        cond = _StubCond(1, k_s=1.5)
        c = mk()
        X, D = core.simulate(F, np.array([0.0]), cond, np.random.default_rng(3), ctrl=c)
        ss = float(np.mean(D[0][0, -50:]))
        bhat = float(np.mean(c.beta_hat)) if isinstance(c, LenainSSO) else float("nan")
        F0 = _StubField(slope=0.0)
        en, _ = core.rtk_ne()
        j = int(np.argmax(np.abs(np.diff(en))))  # 1168: the 21 cm jump
        cond = _StubCond(1, rtk_offset=j + 1 - 30, rtk_scale=1.0)
        c2 = mk()
        X, D = core.simulate(F0, np.array([0.0]), cond, np.random.default_rng(4), ctrl=c2)
        dd = np.abs(D[0][0])
        s = X[0] / core.VEH["v"]  # time along pass (x0 = 0)
        win = (s >= 30) & (s < 45)
        sm = c2.summary() if hasattr(c2, "summary") else {}
        res[name] = dict(ss_offset=ss, beta_hat=bhat, jump_peak=float(dd[win].max()),
                         p99_else=float(np.percentile(dd[~win & (s > 5)], 99)),
                         rate_limited=sm.get("rate_limited", float("nan")))
    return res


# --------------------------------------------------------------------- selftest
def selftest(n_runs=50, w=W_DEFAULT, seed=0):
    t_all = time.time()
    c0 = LenainSSO()
    print(f"LenainSSO: Kd={c0.Kd:.4f} 1/m^2, Kp={c0.Kp:.4f} 1/m (omega_n={c0.omega_n} rad/s, xi={c0.xi}), "
          f"H={c0.H} s; observer gain L=\n{np.array2string(c0.L, precision=4)}")
    print("  observer |eig| (dt-discrete):", np.round(np.abs(c0.obs_eig), 4),
          " linear closed-loop poles with lag+prediction:", np.round(c0.linear_poles(), 3))
    cnp = LenainSSO(predict=False)
    print("  same without prediction:", np.round(cnp.linear_poles(), 3))
    pp = np.sort_complex(c0.linear_poles())
    want = np.sort_complex(np.r_[np.roots([1, c0.v * c0.Kp, c0.v ** 2 * c0.Kd]), -1 / c0.tau])
    assert np.allclose(pp, want, atol=1e-6), "prediction must place poles at design pair + actuator pole"

    # the pluggable replicas of the built-ins must reproduce them exactly (steering diagnostics)
    Fs = core.load_fields("paddy", w=w)
    Ft = Fs[0]
    yt = core.plan(Ft, w, 0.0, lambda f, y: 1.0)
    for nm in ("lqr_i", "stanley"):
        _, Da, _ = exp_lib.run(Ft, yt, 3, np.random.default_rng(1), ctrl=nm, w=w)
        _, Db, _ = exp_lib.run(Ft, yt, 3, np.random.default_rng(1), ctrl=BuiltinProbe(nm), w=w)
        assert all(np.array_equal(a, b) for a, b in zip(Da, Db)), f"BuiltinProbe({nm}) differs from built-in"

    ctrls = {"lenain_sso": LenainSSO, "lenain_robust": LenainSSO.robust, "lenain_fast": LenainSSO.fast,
             "lenain_nocomp": lambda: LenainSSO(compensate=False), "lenain_nopred": lambda: LenainSSO(predict=False),
             "lqr_i": lambda: BuiltinProbe("lqr_i"), "stanley": lambda: BuiltinProbe("stanley")}
    print("\nunit checks (stub flat strip, 1 run): (a) constant sideslip beta=-0.026 rad -> steady-state "
          "offset; (b) real 21 cm/2 s RTK jump at t=30 s")
    uc = _step_and_jump_checks(ctrls)
    for name, r in uc.items():
        print(f"  {name:13s} ss_offset={100 * r['ss_offset']:+6.2f} cm  beta_hat={r['beta_hat']:+.4f}  "
              f"jump peak|d|={100 * r['jump_peak']:5.2f} cm (p99 elsewhere {100 * r['p99_else']:4.2f} cm)  "
              f"rate-limited={r['rate_limited']:.4f}")
    en, ee = core.rtk_ne()
    amp = float(np.abs(np.diff(en)).max())
    for nm in ("lenain_sso", "lenain_robust", "lenain_fast"):
        assert abs(uc[nm]["ss_offset"]) < 0.005, "sliding compensation must remove the slope offset"
        assert abs(uc[nm]["beta_hat"] + 1.5 * 0.05 * 0.35) < 2e-3, "beta_hat must converge"
        assert uc[nm]["jump_peak"] < 1.25 * amp, "bounded response to the RTK jump"
        assert uc[nm]["rate_limited"] < 0.05, "no sustained steering-rate saturation"
    assert uc["lenain_sso"]["rate_limited"] < 0.01 and uc["lenain_robust"]["jump_peak"] < 0.08

    rank = sorted(((np.mean([core.pass_feature(F, y) for y in core.plan(F, w, 0.0, lambda f, y: 1.0)]), F)
                   for F in Fs), key=lambda r: -r[0])
    print(f"\nclosed loop on the 2 paddy fields with the largest mean side slope (of {len(Fs)}; parameters were "
          f"tuned on fields 98/177); {n_runs} runs, common random numbers per controller, w={w} m")
    hdr = (f"  {'ctrl':13s} {'K':>3s} {'RMS cm':>7s} {'p99 cm':>7s} {'pair sd':>7s} | "
           f"{'P(nm) 5cm':>9s} {'E[m] 5cm':>9s} {'P(nm) 10cm':>10s} {'E[m] 10cm':>9s} | "
           f"{'steer deg/s':>11s} {'rate-lim':>8s} | {'sim s':>5s}")
    for s_mean, F in rank[:2]:
        print(f"\nfield {F.fid}: main area {F.M.area:.0f} m2, mean slope {F.z_mean_slope:.2f} deg, "
              f"mean side slope {math.degrees(math.atan(s_mean)):.2f} deg")
        print(hdr)
        for name, mk in ctrls.items():
            r = evaluate_controller(F, mk, n=n_runs, seed=seed, w=w)
            print(f"  {name:13s} {r['passes']:3d} {100 * r['rms']:7.2f} {100 * r['p99']:7.2f} "
                  f"{100 * r['pair_sd']:7.2f} | {r['p_nomiss_0.05']:9.2f} {r['e_miss_0.05']:9.5f} "
                  f"{r['p_nomiss_0.1']:10.2f} {r['e_miss_0.1']:9.5f} | {r['rate_rms_dps']:11.2f} "
                  f"{r['rate_limited']:8.4f} | {r['sim_s']:5.2f}")
        print(f"  overlap ratio of the plans: 5 cm -> {r['overlap_0.05']:.4f}, 10 cm -> {r['overlap_0.1']:.4f}")
    print(f"\nchecks passed; total {time.time() - t_all:.1f} s")


if __name__ == "__main__":
    selftest()

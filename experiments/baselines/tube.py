"""Tube-based robust MPC margin: the cross-section of the robust tube of the
ancillary (LQR) controller, projected on the lateral offset, used as the
coverage erosion margin.

References (checked by web search on 2026-10-13)
------------------------------------------------
[MSR05] D. Q. Mayne, M. M. Seron, S. V. Rakovic, "Robust model predictive
        control of constrained linear systems with bounded disturbances",
        Automatica 41(2):219-224, 2005. (Authors, title, volume, issue and
        pages confirmed from the University of Newcastle repository record
        and an arXiv reference list. The DOI 10.1016/j.automatica.2004.08.019
        is from memory and was NOT confirmed by the search; check it before
        submission.) Tube MPC: nominal model z+ = A z + B v, actual
        x+ = A x + B u + w, w in W. Ancillary law u = v + K (x - z), so the
        error e = x - z obeys e+ = A_K e + w, A_K = A + B K. With Z a
        disturbance-invariant (RPI) set for it (A_K Z + W in Z) and
        x0 in z0 + Z, x_t is in z_t + Z for all t: the robust "tube".
[RKKM05] S. V. Rakovic, E. C. Kerrigan, K. I. Kouramas, D. Q. Mayne,
        "Invariant approximations of the minimal robust positively invariant
        set", IEEE Trans. Automatic Control 50(3):406-410, 2005,
        doi:10.1109/TAC.2005.843854. (Authors, title, volume, issue, pages
        and date confirmed from the Imperial College repository record. The
        DOI is from the dblp/BibSonomy record.) mRPI set
        F_inf = sum_{i>=0} A_K^i W. Outer approximation: F_s = sum_{i=0}^{s-1}
        A_K^i W (eq. 2). If A_K^s W is in alpha W with alpha in [0, 1), then
        F(alpha, s) = (1 - alpha)^-1 F_s is RPI and contains F_inf. For
        W = {w : f_i'w <= g_i}, the smallest such alpha is
        alpha^o(s) = max_i h_W((A_K^s)' f_i) / g_i (eq. 11, h_W the support
        function). The index range of F_s and the alpha^o(s) formula were
        confirmed from the Polyhedra.jl documentation example
        ("Minimal Robust Positively Invariant Set"), which implements eqs. (2)
        and (11) of [RKKM05] and cites it. The paper text itself could not
        be opened from this machine. Error bound used for choosing s: because
        F_s is convex and in F_inf, F(alpha, s) = F_s + alpha/(1-alpha) F_s is
        in F_inf + alpha/(1-alpha) F_s.

Algorithm as implemented
------------------------
1. Training data (never the test fields). Each training field runs the
   nominal plan (lam = 0) for n runs under core.Condition. This is exactly
   exp_lib.run (core.Condition then core.simulate, same rng stream). Two
   things differ, and neither changes the trajectories: the controller is
   wrapped by a logger, and offsets are recorded at every simulator step
   (core.simulate's dx = v dt). selftest() [0a] checks bit-for-bit
   identity with exp_lib.run(ctrl='lqr_i').
   Logged state of the closed loop, per (run, pass, step t):
       x_t = [d_t, psi_t, delta_t, I_t]   ('lqr_i';  'lqr': [d, psi, delta])
   d_t is the true lateral offset (vehicle frame, ground truth: D). The
   calibration baselines use the same ground truth. delta_t is the
   steering-angle sensor value. I_t is the controller's integrator.
   psi_t is reconstructed offline. In core.simulate the heading is driven
   only by the steering, psi_t = psi_0 + c_t with
   c_t = sum_{s<=t} (v/l) dt tan(delta_s), and psi_meas = psi + white noise.
   So psi_0 is estimated per pass as mean_t(psi_meas_t - c_t). This uses
   only psi_meas, delta and the known v, l. selftest() [0c] checks that the
   remaining residual has the 0.15 deg white-noise sd of the heading sensor.
2. Closed-loop linearised lateral-error model, x_{t+1} = A_K x_t + w_t.
   model='sim' (default): exact linearisation of the implemented loop at one
   simulator step (dt = 0.05 s). The replicated lqr_i law is probed,
   including its conditional-integration ordering. The plant step is linear
   Euler with the steering lag and is semi-implicit: psi is updated with
   the new delta, as in core.simulate. model='design': the LQR design model
   A4 - B4 K4 of core._lqr_gains.
   The nominal trajectory is the straight pass, z = 0, nominal input v = 0.
   So the MSR05 residual "x+ - A_K x - B v" is the one-step prediction
   residual w_t = x_{t+1} - A_K x_t. It lumps together side slip and
   roughness, the measurement errors fed back through K (earth-fixed RTK
   error, mounting bias, residual roll offset, heading noise), steering
   rate limits, anti-windup and the sin/tan nonlinearity.
   ts='step' (default) works at the controller rate. ts='log' works at the
   1 m logging grid: x subsampled by 10, A_K^10.
3. Disturbance set W from the residuals of all training samples:
       'Wmax' : box, w_bar_j = max |w_j|
       'W99'  : box, w_bar_j = 99th percentile of |w_j| (q)
       'Wg'   : slope-binned box W(g). Equal-count bins of the local
                |lateral slope| g at the vehicle position (DEM, field.gy).
                Per bin, the 99th percentile of |w_j|.
       'Whull': extra diagnostic, not one of the three requested variants:
                W = convex hull of all residuals (data-driven polytope; Qhull).
                It isolates how much of the conservatism comes from the box
                shape.
   The initial-state set X0 is the state after the first step of each pass
   (line-acquisition residual). It is a box of max (Wmax) or q-th
   percentile (W99, Wg) of |x_0|, or the convex hull (Whull).
4. Tube cross-section Z = F(alpha, s) [RKKM05], projected on d:
       r_tube = max_{+-} h_{F_s}(+-e_d) / (1 - alpha^o(s)),
       h_{F_s}(c) = sum_{i<s} h_W((A_K^i)' c)
   (support functions, so no polytope is ever formed. For a box,
   h_W(c) = sum_j |c_j| w_bar_j). s is the smallest integer with
   alpha^o(s) < 1 and alpha/(1-alpha) h_{F_s}(e_d) <= eps_tube (default
   1 mm). This is the [RKKM05] epsilon criterion applied to the lateral
   coordinate only, the one the margin needs. The exact projection of F_inf
   (series summed to convergence) is reported as a check:
   r_inf <= r_tube <= r_inf + eps_tube.
   Initial state, MSR05 logic: if X0 is inside Z, z0 = 0 is admissible and
   lam = r_tube. selftest() reports which branch every variant takes.
   Containment is checked by LP on the vertices of X0: the zonotope for box
   W, the hull-sum polytope for Whull. The check is sufficient: membership
   in F_s'/(1-alpha) for s' = 30, 100, 300 (<= s) is tried in turn, and
   F_s' is in F_s. Otherwise the nominal starts at
   z0 = x0, and lam = r_tube + sup_{t >= t_entry} h_X0((A_K^t)' e_d).
   t_entry = sqrt(H^2 - (w/2)^2) / (v dt) is the shortest travel from the
   start of a pass to any main-area point it covers (H = 2w headland,
   convex field).
5. Margin: lam = r_tube (plus the X0 term of step 4 when X0 is not inside
   Z). Each pass stays in its own tube, so the pass-to-pass difference stays
   within 2 lam and each side of the swath is eroded by lam:
   core.plan(F, w, lam, unit sigma).
   For 'Wg' the disturbance bound varies along the pass with the local
   slope. The RPI set is then replaced by the exact time-varying reachable
   tube of the pass (z0 = x0):
       r_k = sup_{m in main area} h_X0((A_K^m)' e_d)
             + sum_{i<m} h_{W(g_{m-1-i})}((A_K^i)' e_d),
   evaluated on the planned line from the DEM, both driving directions
   (max). The plan then uses core.plan(F, w, 1.0, SlopeTube) with per-pass
   sigma = r_k in metres. With all bins equal this reproduces <= the
   constant-W lam (checked in selftest() [0e]).

API
---
    data = collect(train_fields, rng, ctrl='lqr_i', n=30)       # TrainData
    lam, diag = tube_lambda(train_fields, rng, variant='W99', ctrl='lqr_i',
                            n=30, model='sim', ts='step', q=99.0, n_bins=6,
                            eps_tube=1e-3, data=None)
        lam  : margin in metres ('Wg': 1.0, with per-pass metres in
               diag['sig_fn']).
        diag : r_tube, r_inf, alpha, s, r_x0, x0_in_Z, wbar (or bins),
               rho(A_K), n_res, runtime_s, sig_fn, ...
    ys = plan(F, lam, diag, w=3.0)                 # core.plan with the margin
    res = evaluate_tube(F, ys, n_test, rng, lam, diag)
        P(no miss), E[miss], overlap, RMS / p99 tracking error, tube
        containment (fraction of runs with |d| <= r in the main area) and
        W-violation rates (test residuals outside W).
    closed_loop_matrix(ctrl, model), mrpi_box(Phi, wbar), SlopeTube.

Expected behaviour (stated a priori; selftest() reports what happens)
--------------------------------------------------------------------
'Wmax' is very conservative. The worst residual of each coordinate is
assumed to occur with the worst sign at every step. Correlations between
the coordinates (slip, measurement bias, saturation) are discarded by the
box. The plan may become infeasible (core.plan's minimum half-width).
'W99' is a box of 99th-percentile residuals. Over a run of about 10^4
steps x K passes, essentially every run leaves this box many times. So the
RPI guarantee does not hold at run level: the run-level sup is not
controlled, and W99 can under-cover. Here, though, its coverage comes from
the worst-case-sequence conservatism of the mRPI rather than from any
calibrated probability.
'Wg' moves margin from flat to sloped passes. It inherits the per-sample
(not per-run) 99% level of W99, and extrapolates the top slope bin beyond
the training range.

Observed in selftest() (train field 177, n = 30; test fields 34 and 174,
n = 50; seed 0)
The residual coordinates are strongly correlated: corr(psi, delta) = 1.00,
because psi is updated with the new delta, and corr(delta, I) = -0.92.
A box discards both.
'W99' : r_tube = 59.3 cm. X0 is not inside Z, so the X0 term (+3.3 cm) is
        added: lam = 62.6 cm. P(no miss) = 1.00 on both test fields at 72%
        overlap. The largest run-level sup|d| is only 25.5 / 20.2 cm, so the
        tube is about 2.5x too wide. Yet 96% / 82% of test runs have
        residuals outside W99, so the tube assumption fails in most runs and
        coverage comes only from the worst-case sum. The predicted W99
        under-coverage was NOT observed in this setting.
'Wmax': lam = 130.9 cm. Infeasible: the half-width w/2 - lam is below
        core.plan's minimum of 0.3 m.
'Wg'  : per-bin r_tube 36.5-77.7 cm (low to high |g|). Per pass 52-78 cm
        (field 34) and 37-77 cm (field 174). P(no miss) = 1.00, overlap
        1.02 / 0.68.
'Whull': lam = 65.8 cm, half of Wmax at the same (max) level. The box shape
        alone costs about a factor 2.
Sensitivity of W99: design model 61.4 cm, 1 m logging-rate model 56.7 cm.
Identification takes < 1 s per variant after the 0.5 s training simulation.

Controller-information rule: the controller replica sees only meas,
psi_meas and delta. The identification uses ground-truth offsets of TRAINING
runs only. cond.k_s, OU state, cond.comp, cond.mount and the RTK series are
never read.
"""
import math
import time

import numpy as np
from scipy.optimize import linprog
from scipy.signal import fftconvolve
from scipy.spatial import ConvexHull
from shapely.geometry import box as _box

import core
import exp_lib

W_DEFAULT = exp_lib.W_DEFAULT
VARIANTS = ("W99", "Wmax", "Wg", "Whull")
_UNIT = exp_lib.ConstSigma(1.0)


# --------------------------------------------------------------------- controller replica + logger
class _Logger:
    """Replica of core.simulate's built-in 'lqr' / 'lqr_i' laws (same gains,
    same conditional-integration anti-windup, bit-for-bit) that also logs, at
    every simulator step, the signals needed to rebuild the closed-loop
    state: steering angle, integrator, and the steering-driven heading
    increment c_t (for the offline heading reconstruction). `cond` is never
    read."""

    def __init__(self, kind="lqr_i", log=True):
        if kind not in ("lqr", "lqr_i"):
            raise ValueError("tube margin is defined for the LQR ancillary laws 'lqr_i' / 'lqr'")
        self.kind, self.log = kind, log

    def reset(self, R, K, veh, cond=None):
        self.K1, self.K4 = core._lqr_gains(veh["v"], veh["l_wb"], veh["dt"])
        self.dmax, self.v, self.l = veh["delta_max"], veh["v"], veh["l_wb"]
        self.integ = np.zeros((R, K))
        self.t = 0
        self.c = np.zeros((R, K))
        self.sr, self.sr2 = np.zeros((R, K)), np.zeros((R, K))
        self.L_delta, self.L_integ, self.L_c = [], [], []

    def command(self, meas, psi_meas, delta, dt):
        if self.t:
            self.c = self.c + self.v / self.l * dt * np.tan(delta)  # psi_t - psi_0 (heading driven by steering)
        r = psi_meas - self.c
        self.sr += r
        self.sr2 += r * r
        if self.log:
            self.L_delta.append(delta.copy())
            self.L_integ.append(self.integ.copy())
            self.L_c.append(self.c.copy())
        self.t += 1
        if self.kind == "lqr":
            return -(self.K1[0] * meas + self.K1[1] * psi_meas)
        K4 = self.K4
        u_try = -(K4[0] * meas + K4[1] * psi_meas + K4[2] * delta + K4[3] * (self.integ + meas * dt))
        sat = np.abs(u_try) >= self.dmax
        self.integ = np.where(sat, self.integ, np.clip(self.integ + meas * dt, -0.3, 0.3))
        return -(K4[0] * meas + K4[1] * psi_meas + K4[2] * delta + K4[3] * self.integ)

    # ----------------------------------------------------------------- state reconstruction
    def psi0(self):
        return self.sr / self.t

    def heading_noise_sd(self):
        p0 = self.psi0()
        return np.sqrt(np.maximum(self.sr2 / self.t - p0 ** 2, 0.0))

    def states(self, ys, D):
        """Yield per pass k: S (R, m, nx), S[:, i] = closed-loop state after
        step i (x_{i+1}); D[k][:, i] is the offset after step i (dx = v dt)."""
        C, De, Ig = np.stack(self.L_c), np.stack(self.L_delta), np.stack(self.L_integ)  # (T, R, K)
        p0 = self.psi0()
        for k in range(len(ys)):
            sg = 1.0 if k % 2 == 0 else -1.0
            m = min(D[k].shape[1], self.t - 1)
            idx = np.arange(1, m + 1)
            cols = [sg * D[k][:, :m], p0[:, k, None] + C[idx, :, k].T, De[idx, :, k].T]
            if self.kind == "lqr_i":
                cols.append(Ig[idx, :, k].T)
            yield np.stack(cols, -1)


def _nx(ctrl):
    return 4 if ctrl == "lqr_i" else 3


# --------------------------------------------------------------------- closed-loop model
def closed_loop_matrix(ctrl="lqr_i", model="sim"):
    """Per-step (dt) closed-loop matrix A_K of the lateral-error state.

    'sim'   : exact linearisation of core.simulate's step with the implemented
              law (probed on the replica): u from (d, psi, delta, I); delta+ =
              delta + (u - delta) dt / tau; d+ = d + v psi dt; psi+ = psi + v/l dt delta+.
    'design': the LQR design model (lqr_i: A4 - B4 K4 of core._lqr_gains;
              lqr: explicit Euler of the lag plant with u = -K1 [d, psi]).
    """
    veh = core.VEH
    v, l, tau, dt = veh["v"], veh["l_wb"], veh["tau"], veh["dt"]
    K1, K4 = core._lqr_gains(v, l, dt)
    nx = _nx(ctrl)
    if model == "design":
        if ctrl == "lqr_i":
            A4 = np.array([[1, v * dt, 0, 0], [0, 1, v / l * dt, 0], [0, 0, 1 - dt / tau, 0], [dt, 0, 0, 1]])
            B4 = np.array([[0], [0], [dt / tau], [0]])
            return A4 - B4 @ K4[None, :]
        return np.array([[1, v * dt, 0], [0, 1, v / l * dt],
                         [-dt / tau * K1[0], -dt / tau * K1[1], 1 - dt / tau]])
    if model != "sim":
        raise ValueError(model)
    eps = 1e-3  # the replica is exactly linear while unsaturated
    lg = _Logger(ctrl, log=False)
    lg.reset(nx, 1, veh)
    E = eps * np.eye(nx)
    d, psi, delta = E[:, 0:1].copy(), E[:, 1:2].copy(), E[:, 2:3].copy()
    if ctrl == "lqr_i":
        lg.integ = E[:, 3:4].copy()
    u = lg.command(d, psi, delta, dt)
    delta2 = delta + (u - delta) / tau * dt
    d2 = d + v * psi * dt
    psi2 = psi + v * delta2 / l * dt
    cols = [d2, psi2, delta2] + ([lg.integ] if ctrl == "lqr_i" else [])
    return (np.concatenate(cols, axis=1) / eps).T


def _phi(ctrl, model, ts):
    M = closed_loop_matrix(ctrl, model)
    sub = _sub(ts)
    return np.linalg.matrix_power(M, sub), sub


def _sub(ts):
    if ts == "step":
        return 1
    if ts == "log":
        return max(1, int(round(1.0 / (core.VEH["v"] * core.VEH["dt"]))))
    raise ValueError(ts)


# --------------------------------------------------------------------- training data
class TrainData:
    """Logged closed-loop states of the training runs (per field, per pass)."""

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.S, self.G = [], []  # lists over (field, pass): (R, m, nx), (R, m) local |lateral slope|
        self.fids, self.noise_sd, self.runtime_s = [], [], 0.0


def _simulate_logged(F, ys, cond, rng, ctrl):
    lg = _Logger(ctrl)
    dxs = core.VEH["v"] * core.VEH["dt"]
    X, D = core.simulate(F, ys, cond, rng, ctrl=lg, dx=dxs)
    return lg, X, D


def collect(train_fields, rng, ctrl="lqr_i", n=30, w=W_DEFAULT, lam_ref=0.0, **cond_kw):
    """Run the nominal plan (lam_ref) on each training field n times and log
    the closed-loop states (same draws as exp_lib.run; see module doc)."""
    t0 = time.perf_counter()
    data = TrainData(ctrl)
    for F in train_fields:
        ys = core.plan(F, w, lam_ref, _UNIT)
        cond = core.Condition(rng, n, **cond_kw)
        lg, X, D = _simulate_logged(F, ys, cond, rng, ctrl)
        S = lg.states(ys, D)
        for k, Sk in enumerate(S):
            m = Sk.shape[1]
            if m < 3:
                continue
            g = np.abs(F.gy(np.broadcast_to(X[k][:m], (Sk.shape[0], m)), ys[k] + D[k][:, :m]))
            data.S.append(Sk)
            data.G.append(g)
        data.fids.append(F.fid)
        data.noise_sd.append(lg.heading_noise_sd().ravel())
    data.noise_sd = np.concatenate(data.noise_sd)
    data.runtime_s = time.perf_counter() - t0
    return data


def residuals(data, Phi, sub=1):
    """One-step prediction residuals w = x+ - A_K x (N, nx), the local slope at
    x (N,), and the initial states (n0, nx)."""
    W, G, X0 = [], [], []
    for S, g in zip(data.S, data.G):
        Ss, gs = S[:, ::sub], g[:, ::sub]
        if Ss.shape[1] < 2:
            continue
        W.append((Ss[:, 1:] - Ss[:, :-1] @ Phi.T).reshape(-1, S.shape[2]))
        G.append(gs[:, :-1].ravel())
        X0.append(Ss[:, 0])
    return np.concatenate(W), np.concatenate(G), np.concatenate(X0)


# --------------------------------------------------------------------- mRPI (support functions)
def _h_box(C, wbar):
    return np.abs(C) @ wbar


def _mrpi(Phi, h_fn, facets, eps_tube=1e-3, s_max=20000, tol_inf=1e-12):
    """RKKM05 outer approximation projected on d (coordinate 0).

    h_fn(C) : support function of W for directions C (m, nx) -> (m,)
    facets  : (Fm (nf, nx), g (nf,)) with W = {w : Fm w <= g}, g > 0.
    Returns dict(r, r_pos, r_neg, alpha, s, r_inf).
    """
    nx = Phi.shape[0]
    Fm, g = facets
    if np.any(g <= 0):
        raise ValueError("0 must be in the interior of W")
    e = np.zeros((2, nx))
    e[0, 0], e[1, 0] = 1.0, -1.0
    Cd = e.copy()  # (Phi^i)' (+-e_d)
    Cf = Fm.copy()  # (Phi^i)' f_j
    hs = np.zeros(2)
    s, alpha = 0, np.inf
    for s in range(1, s_max + 1):
        hs += h_fn(Cd)
        Cd = Cd @ Phi  # rows c' Phi = (Phi' c)'
        Cf = Cf @ Phi
        alpha = float(np.max(h_fn(Cf) / g))
        if alpha < 1 and alpha / (1 - alpha) * hs.max() <= eps_tube:
            break
    else:
        raise RuntimeError("mRPI: no admissible (alpha, s) found; A_K not Schur?")
    r_pos, r_neg = hs / (1 - alpha)
    # exact projection of F_inf (series to convergence), as a check
    hinf, C = hs.copy(), Cd.copy()
    for _ in range(200000):
        t = h_fn(C)
        hinf += t
        C = C @ Phi
        if t.max() < tol_inf:
            break
    return dict(r=float(max(r_pos, r_neg)), r_pos=float(r_pos), r_neg=float(r_neg), alpha=alpha, s=s,
                r_inf=float(hinf.max()), hs=hs)


def mrpi_box(Phi, wbar, eps_tube=1e-3):
    """mRPI outer approximation for the box W = {|w_j| <= wbar_j}."""
    nx = len(wbar)
    return _mrpi(Phi, lambda C: _h_box(C, wbar), (np.eye(nx), np.asarray(wbar, float)), eps_tube)


def _support_profile(Phi, h_fn, n_max, tol=1e-12):
    """h(t) = h_X((Phi^t)' e_d) and h_X((Phi^t)'(-e_d)) for t = 0..n_max-1 (2, n)."""
    nx = Phi.shape[0]
    C = np.zeros((2, nx))
    C[0, 0], C[1, 0] = 1.0, -1.0
    out = []
    for _ in range(n_max):
        hv = h_fn(C)
        out.append(hv)
        if hv.max() < tol:
            break
        C = C @ Phi
    return np.array(out).T


def _contains(Phi, alpha, s, pts, gens, simplex, s_try=(30, 100, 300)):
    """LP membership of pts in (1-alpha)^-1 sum_{i<s'} Phi^i W for s' in s_try
    (s' <= s; F_s' is in F_s, so success for any s' is sufficient for
    pts in F(alpha, s)). W = zonotope G [-1, 1]^m (simplex=False, gens = G)
    or conv of the columns of gens (simplex=True)."""
    from scipy import sparse

    nx, ng = gens.shape
    todo = list(pts)
    for sp in sorted({min(t, s) for t in s_try}):
        blocks, P = [], np.eye(nx)
        for _ in range(sp):
            blocks.append((P @ gens) / (1 - alpha))
            P = Phi @ P
        A = sparse.csr_matrix(np.concatenate(blocks, axis=1))
        if simplex:
            A = sparse.vstack([A, sparse.kron(sparse.eye(sp), np.ones((1, ng)))]).tocsr()
        left = []
        for x in todo:
            b = np.r_[x, np.ones(sp)] if simplex else x
            r = linprog(np.zeros(A.shape[1]), A_eq=A, b_eq=b, bounds=(0, None) if simplex else (-1, 1),
                        method="highs")
            if r.status != 0:
                left.append(x)
        todo = left
        if not todo:
            return True
    return False


def _x0_term(Phi, alpha, s, gens, simplex, pts, t_entry, s_cap=None, tol=1e-10):
    """MSR05 initial-state step with the nominal initial state z0 as a decision variable.

    For every x0 in pts (the vertices of X0) solve the LP
        f(x0) = min_{z0 : x0 - z0 in Z'} max_{t >= t_entry} |e_d' A_K^t z0|,
    with Z' = (1-alpha)^-1 F_s' (s' = min(s, s_cap)), which is inside Z = F(alpha, s).
    The nominal z_t = A_K^t z0 is then driven by the ancillary law (v = K z), and x_t - z_t is in Z
    for all t, so |d_t| <= r_tube + f(x0) after main-area entry. f is convex in x0, being an
    infimal convolution of convex functions, so its max over X0 is attained at a vertex.
    z0 = x0 is feasible, so f(x0) <= the naive term sup_t |e_d' A_K^t x0|. The returned value
    is recomputed for the optimal z0 over the full horizon, not only the LP's truncated one.
    Returns (max_x0 f, z0 at the argmax)."""
    from scipy import sparse

    nx, ng = gens.shape
    rows, c = [], np.linalg.matrix_power(Phi, t_entry)[0].copy()  # e_d' A_K^t, t >= t_entry
    for _ in range(200000):
        rows.append(c)
        if np.abs(c).sum() < tol:
            break
        c = c @ Phi
    Cd = np.array(rows)
    sp = s if s_cap is None else min(s, s_cap)
    blocks, P = [], np.eye(nx)
    for _ in range(sp):
        blocks.append((P @ gens) / (1 - alpha))
        P = Phi @ P
    G = np.concatenate(blocks, axis=1)
    nl = G.shape[1]
    nT = len(Cd)
    A_ub = sparse.vstack([sparse.hstack([sparse.csr_matrix(Cd), sparse.csr_matrix((nT, nl)), -np.ones((nT, 1))]),
                          sparse.hstack([sparse.csr_matrix(-Cd), sparse.csr_matrix((nT, nl)), -np.ones((nT, 1))])])
    A_eq = sparse.hstack([sparse.eye(nx), sparse.csr_matrix(G), sparse.csr_matrix((nx, 1))])
    if simplex:
        A_eq = sparse.vstack([A_eq, sparse.hstack([sparse.csr_matrix((sp, nx)), sparse.kron(sparse.eye(sp), np.ones((1, ng))),
                                                   sparse.csr_matrix((sp, 1))])])
    A_ub, A_eq = A_ub.tocsr(), A_eq.tocsr()
    cobj = np.zeros(nx + nl + 1)
    cobj[-1] = 1.0
    bounds = [(None, None)] * nx + [(0, None) if simplex else (-1, 1)] * nl + [(0, None)]
    best, zbest = 0.0, np.zeros(nx)
    for x0 in pts:
        b_eq = np.r_[x0, np.ones(sp)] if simplex else np.asarray(x0, float)
        r = linprog(cobj, A_ub=A_ub, b_ub=np.zeros(2 * nT), A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
        z0 = r.x[:nx] if r.status == 0 else np.asarray(x0, float)  # z0 = x0 is always feasible
        # exact value for this z0 over the full horizon (t >= t_entry, series until negligible)
        f = float(np.abs(Cd @ z0).max())
        if f > best:
            best, zbest = f, z0
    return best, zbest


def _zonotope_contains(Phi, wbar, alpha, s, pts):
    """pts in F(alpha, s) for the box W = diag(wbar) [-1, 1]^nx (sufficient LP check)."""
    return _contains(Phi, alpha, s, pts, np.diag(wbar), simplex=False)


def _hullsum_contains(Phi, V, alpha, s, pts):
    """pts in F(alpha, s) for W = conv(V) (sufficient LP check)."""
    return _contains(Phi, alpha, s, pts, V.T, simplex=True)


def _box_vertices(b):
    nx = len(b)
    sg = np.array(np.meshgrid(*[[-1.0, 1.0]] * nx, indexing="ij")).reshape(nx, -1).T
    return sg * b[None, :]


def _hull(P):
    """Convex hull of point cloud P (n, nx): vertices and facets {F w <= g}."""
    sc = np.abs(P).max(0)
    sc = np.where(sc > 0, sc, 1.0)
    H = ConvexHull(P / sc)
    V = P[H.vertices]
    Fm = H.equations[:, :-1] / sc[None, :]
    g = -H.equations[:, -1]
    return V, Fm, g


# --------------------------------------------------------------------- slope-binned tube
def _window(field, y, w):
    """Along-track range [x_lo, x_hi] of the main area within the swath of a
    pass at y (where its coverage is required); None if it covers no main area."""
    strip = field.M.intersection(_box(field.P.bounds[0] - 1, y - w / 2, field.P.bounds[2] + 1, y + w / 2))
    if strip.is_empty:
        return None
    b = strip.bounds
    return b[0], b[2]


class SlopeTube:
    """Per-pass tube radius [m] for W(g) (time-varying box along the pass),
    exact reachable tube from X0 (see module doc, step 5). Use as
    core.plan(F, w, 1.0, SlopeTube(...))."""

    def __init__(self, Phi, edges, wbar_b, x0bar, sub=1, w=W_DEFAULT, tol=1e-9):
        self.Phi, self.edges, self.wbar_b = Phi, np.asarray(edges), np.asarray(wbar_b)
        self.x0bar, self.w = np.asarray(x0bar), w
        self.dxs = core.VEH["v"] * core.VEH["dt"] * sub
        nx = Phi.shape[0]
        c, C = [], np.eye(nx)[0]
        wtop = self.wbar_b.max(0)
        for i in range(200000):
            a = np.abs(C)
            c.append(a)
            if a @ (wtop + self.x0bar) < tol:
                break
            C = Phi.T @ C
        self.c = np.array(c)  # (Nc, nx): |(Phi^i)' e_d|
        self.hx0 = self.c @ self.x0bar
        # remaining series beyond the truncation (geometric decay at the spectral radius; < 1e-6 m)
        rho = float(np.abs(np.linalg.eigvals(Phi)).max())
        self.tail = float(self.c[-1] @ (wtop + self.x0bar)) / max(1 - rho, 1e-6)
        self._cache = {}

    def profile(self, field, y, forward=True):
        """(x positions, tube radius) along the pass at lateral position y."""
        ch = field.chord(field.P, y)
        if ch is None:
            return np.zeros(0), np.zeros(0)
        x0, x1 = ch
        L = max(x1 - x0, 1.0)
        n = max(int(L / self.dxs), 1)
        s = np.arange(n) * self.dxs
        xs = x0 + s if forward else x1 - s
        g = np.abs(field.gy(xs, np.full_like(xs, y)))
        b = np.clip(np.searchsorted(self.edges[1:-1], g, side="right"), 0, len(self.wbar_b) - 1)
        wb = self.wbar_b[b]  # (n, nx) disturbance bound of the step leaving sample m
        conv = np.zeros(n)
        for j in range(wb.shape[1]):
            cj = fftconvolve(self.c[:, j], wb[:, j])[: n - 1]  # index m-1 -> sum_{i<m} c_i wb_{m-1-i}
            conv[1:] += cj
        hx0 = np.zeros(n)
        k = min(n, len(self.hx0))
        hx0[:k] = self.hx0[:k]
        return xs, hx0 + conv + self.tail

    def window(self, field, y):
        return _window(field, y, self.w)

    def __call__(self, field, y):
        key = (field.fid, round(float(y), 3))
        if key not in self._cache:
            win = self.window(field, y)
            r = 0.0
            for fwd in (True, False):
                xs, rr = self.profile(field, y, fwd)
                if win is not None:
                    m = (xs >= win[0]) & (xs <= win[1])
                    if m.any():
                        r = max(r, float(rr[m].max()))
            self._cache[key] = r
        return self._cache[key]

    def vec(self, field, ys):
        return np.array([self(field, y) for y in ys])


# --------------------------------------------------------------------- main API
def _entry_steps(w, sub):
    H = 2 * w
    dxs = core.VEH["v"] * core.VEH["dt"] * sub
    return int(math.floor(math.sqrt(H ** 2 - (w / 2) ** 2) / dxs))


def tube_from_data(data, variant="W99", model="sim", ts="step", q=99.0, n_bins=6, eps_tube=1e-3,
                   w=W_DEFAULT, check_x0=True):
    """Tube margin from logged training data. Returns (lam, diag)."""
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}")
    t0 = time.perf_counter()
    Phi, sub = _phi(data.ctrl, model, ts)
    Wr, Gr, X0 = residuals(data, Phi, sub)
    diag = dict(variant=variant, model=model, ts=ts, ctrl=data.ctrl, n_res=len(Wr), n_x0=len(X0),
                rho=float(np.abs(np.linalg.eigvals(Phi)).max()), Phi=Phi, sub=sub, train_fids=list(data.fids))
    t_entry = _entry_steps(w, sub)
    diag["t_entry"] = t_entry
    absW, absX0 = np.abs(Wr), np.abs(X0)
    if variant in ("Wmax", "W99", "Wg"):
        if variant == "Wmax":
            wbar, x0bar = absW.max(0), absX0.max(0)
        else:
            wbar, x0bar = np.percentile(absW, q, axis=0), np.percentile(absX0, q, axis=0)
        wbar = np.maximum(wbar, 1e-12)  # 0 in int(W)
        diag.update(wbar=wbar, x0bar=x0bar)
        mr = mrpi_box(Phi, wbar, eps_tube)
        diag.update(r_tube=mr["r"], r_inf=mr["r_inf"], alpha=mr["alpha"], s=mr["s"])
        hX0 = _support_profile(Phi, lambda C: _h_box(C, x0bar), 200000)
        diag["r_x0_naive"] = float(hX0[:, t_entry:].max()) if hX0.shape[1] > t_entry else 0.0
        if variant != "Wg":
            Vx0 = _box_vertices(x0bar)
            inside = (_zonotope_contains(Phi, wbar, mr["alpha"], mr["s"], Vx0) if check_x0 else False)
            diag["x0_in_Z"] = inside
            if inside:
                diag["r_x0"] = 0.0
            else:  # MSR05: optimise the nominal initial state z0 (x0 in z0 + Z)
                diag["r_x0"], diag["z0_worst"] = _x0_term(Phi, mr["alpha"], mr["s"], np.diag(wbar), False, Vx0,
                                                          t_entry)
            lam = mr["r"] + diag["r_x0"]
            diag["sig_fn"] = _UNIT
        else:
            edges = np.quantile(Gr, np.linspace(0, 1, n_bins + 1))
            edges[0], edges[-1] = 0.0, np.inf
            b = np.clip(np.searchsorted(edges[1:-1], Gr, side="right"), 0, n_bins - 1)
            wbar_b = np.array([np.maximum(np.percentile(absW[b == i], q, axis=0), 1e-12) for i in range(n_bins)])
            r_b = []
            for i in range(n_bins):
                r_b.append(mrpi_box(Phi, wbar_b[i], eps_tube)["r"])
            st = SlopeTube(Phi, edges, wbar_b, x0bar, sub=sub, w=w)
            diag.update(edges=edges, wbar_b=wbar_b, r_bins=np.array(r_b), n_per_bin=np.bincount(b, minlength=n_bins),
                        sig_fn=st, g_train_max=float(Gr.max()))
            lam = 1.0
    else:  # Whull
        V, Fm, g = _hull(Wr)
        V0 = X0[ConvexHull(X0 / np.where(absX0.max(0) > 0, absX0.max(0), 1)).vertices]
        hW = lambda C: (C @ V.T).max(axis=1)  # noqa: E731
        mr = _mrpi(Phi, hW, (Fm, g), eps_tube)
        hX0 = _support_profile(Phi, lambda C: (C @ V0.T).max(axis=1), 200000)
        r_x0_naive = float(hX0[:, t_entry:].max()) if hX0.shape[1] > t_entry else 0.0
        inside = _hullsum_contains(Phi, V, mr["alpha"], mr["s"], V0) if check_x0 else False
        # MSR05 optimal z0 when X0 is not in Z (hull sum truncated at s' = 300 <= s: F_s' in F_s, so valid)
        r_x0 = 0.0 if inside else _x0_term(Phi, mr["alpha"], mr["s"], V.T, True, V0, t_entry, s_cap=300)[0]
        diag.update(r_tube=mr["r"], r_inf=mr["r_inf"], alpha=mr["alpha"], s=mr["s"], r_x0=r_x0, x0_in_Z=inside,
                    r_x0_naive=r_x0_naive, n_vert=len(V), n_facets=len(g), n_vert_x0=len(V0), V=V, Fm=Fm, g=g,
                    wbar=absW.max(0), x0bar=absX0.max(0))
        lam = mr["r"] + r_x0
        diag["sig_fn"] = _UNIT
    diag["lam"] = float(lam)
    diag["runtime_s"] = time.perf_counter() - t0
    return float(lam), diag


def tube_lambda(train_fields, rng, variant="W99", ctrl="lqr_i", n=30, w=W_DEFAULT, model="sim", ts="step",
                q=99.0, n_bins=6, eps_tube=1e-3, data=None, **cond_kw):
    """Tube-MPC coverage margin identified on TRAINING fields.

    Returns (lam, diag): lam in metres for 'W99' / 'Wmax' / 'Whull' (plan with
    core.plan(F, w, lam, diag['sig_fn']), sig_fn = 1); for 'Wg' lam = 1.0 and
    diag['sig_fn'](F, y) is the per-pass tube radius in metres. Pass `data`
    (from collect) to reuse one set of training runs across variants.
    """
    if data is None:
        data = collect(train_fields, rng, ctrl=ctrl, n=n, w=w, **cond_kw)
    lam, diag = tube_from_data(data, variant=variant, model=model, ts=ts, q=q, n_bins=n_bins,
                               eps_tube=eps_tube, w=w)
    diag["collect_s"] = data.runtime_s
    return lam, diag


def plan(F, lam, diag, w=W_DEFAULT):
    return core.plan(F, w, lam, diag["sig_fn"])


# --------------------------------------------------------------------- evaluation
def _metre_grid(F, ys, Xf, Df):
    """Exact equivalent of core.simulate(dx=1) output from a dx = v dt run."""
    rec = max(1, int(round(1.0 / (core.VEH["v"] * core.VEH["dt"]))))
    X1, D1 = [], []
    for k, y in enumerate(ys):
        c = F.chord(F.P, y)
        x0, x1 = (c[0], c[1]) if c else (0.0, 0.0)
        L = max(x1 - x0, 1.0)
        nk = int(L / 1.0)
        sk = np.arange(nk) * 1.0
        X1.append(x0 + sk if k % 2 == 0 else x1 - sk)
        D1.append(Df[k][:, ::rec][:, :nk])
        assert D1[-1].shape[1] == nk
    return X1, D1


def evaluate_tube(F, ys, n_test, rng, lam, diag, w=W_DEFAULT, ctrl=None, **cond_kw):
    """Execute plan ys n_test times (same draws as exp_lib.evaluate_plan with
    the same rng) and report coverage, tracking and tube diagnostics."""
    ctrl = ctrl or diag["ctrl"]
    t0 = time.perf_counter()
    cond = core.Condition(rng, n_test, **cond_kw)
    lg, Xf, Df = _simulate_logged(F, ys, cond, rng, ctrl)
    t_sim = time.perf_counter() - t0
    X1, D1 = _metre_grid(F, ys, Xf, Df)
    miss = core.evaluate(F, ys, X1, D1, w)
    res = dict(p_nomiss=float(np.mean(miss == 0)), e_miss=float(miss.mean()), passes=len(ys),
               overlap=exp_lib.overlap_ratio(F, ys, w), sim_s=t_sim)
    # tracking error and tube containment in the main-area window of each pass (1 m grid)
    sig = diag["sig_fn"]
    r_k = lam * np.array([sig(F, y) for y in ys])
    e_all, inside, sup = [], np.ones(n_test, bool), np.zeros(n_test)
    for k, y in enumerate(ys):
        win = _window(F, y, w)
        if win is None:
            continue
        m = (X1[k] >= win[0]) & (X1[k] <= win[1])
        if not m.any():
            continue
        a = np.abs(D1[k][:, m])
        e_all.append(a.ravel())
        inside &= a.max(axis=1) <= r_k[k]
        sup = np.maximum(sup, a.max(axis=1))
    e_all = np.concatenate(e_all)
    res.update(rms=float(np.sqrt(np.mean(e_all ** 2))), p99=float(np.percentile(e_all, 99)),
               p_in_tube=float(inside.mean()), sup_max=float(sup.max()), sup_med=float(np.median(sup)))
    # disturbance-set violations on the test residuals
    Phi, sub = diag["Phi"], diag["sub"]
    n_out, n_tot, run_viol = 0, 0, np.zeros(n_test, bool)
    for k, Sk in enumerate(lg.states(ys, Df)):
        m = Sk.shape[1]
        Ss = Sk[:, ::sub]
        if Ss.shape[1] < 2:
            continue
        Wt = Ss[:, 1:] - Ss[:, :-1] @ Phi.T  # (R, ms-1, nx)
        if diag["variant"] == "Whull":
            out = ((Wt @ diag["Fm"].T) > diag["g"] * (1 + 1e-9)).any(-1)
        elif diag["variant"] == "Wg":
            xs = Xf[k][:m][::sub][:-1]
            g = np.abs(F.gy(np.broadcast_to(xs, (n_test, len(xs))), ys[k] + Df[k][:, :m][:, ::sub][:, :-1]))
            b = np.clip(np.searchsorted(diag["edges"][1:-1], g, side="right"), 0, len(diag["wbar_b"]) - 1)
            out = (np.abs(Wt) > diag["wbar_b"][b]).any(-1)
        else:
            out = (np.abs(Wt) > diag["wbar"]).any(-1)
        n_out += int(out.sum())
        n_tot += out.size
        run_viol |= out.any(axis=1)
    res.update(frac_w_out=n_out / max(n_tot, 1), p_run_w_viol=float(run_viol.mean()), r_k=r_k)
    return res


# --------------------------------------------------------------------- selftest helpers
class _FlatField:
    """Duck-typed straight 200 m pass on a constant side slope (for alignment checks)."""

    def __init__(self, g=0.0, length=200.0):
        self.P = _box(0.0, -20.0, length, 20.0)
        self.rot, self._g, self.fid = 0.0, g, -1

    def gy(self, x, y):
        return np.full(np.shape(x), self._g, float)

    chord = core.Field.chord


def selftest(n_train=30, n_test=50, seed=0, w=W_DEFAULT, ctrl="lqr_i", train_fids=(177,), test_fids=(34, 174)):
    t_all = time.perf_counter()
    veh = core.VEH
    allF = {F.fid: F for F in core.load_fields("paddy", w=w)}
    trainF = [allF[i] for i in train_fids]
    testF = [allF[i] for i in test_fids]
    print(f"tube selftest: ctrl={ctrl}, w={w} m, dt={veh['dt']} s; train fields {list(train_fids)} "
          f"(slope {[round(F.z_mean_slope, 2) for F in trainF]} deg, n={n_train} runs each), "
          f"test fields {list(test_fids)} (slope {[round(F.z_mean_slope, 2) for F in testF]} deg, n={n_test})")

    # ---------------------------------------------------------------- [0] checks
    print("\n[0] checks")
    F = testF[0]
    ys = core.plan(F, w, 0.0, _UNIT)
    Xa, Da, _ = exp_lib.run(F, ys, 4, np.random.default_rng(5), ctrl=ctrl, w=w)
    rng = np.random.default_rng(5)
    cond = core.Condition(rng, 4)
    lg, Xf, Df = _simulate_logged(F, ys, cond, rng, ctrl)
    X1, D1 = _metre_grid(F, ys, Xf, Df)
    same = all(np.array_equal(a, b) for a, b in zip(Xa, X1)) and all(np.array_equal(a, b) for a, b in zip(Da, D1))
    print(f"  [0a] logger replica + dx=v*dt recording == exp_lib.run(ctrl='{ctrl}') bit-for-bit: {same}")
    assert same
    # [0b] alignment: no slip / no measurement bias -> d-row residual = kinematic nonlinearity only
    FF = _FlatField(0.0)
    rng = np.random.default_rng(1)
    cond = core.Condition(rng, 20)
    cond.k_s[:] = 0.0
    cond.rough[:] = 0.0
    cond.comp[:] = 1.0
    cond.mount[:] = 0.0
    cond.rtk_scale = 0.0
    lg, Xf, Df = _simulate_logged(FF, np.array([0.0]), cond, rng, ctrl)
    S = next(lg.states(np.array([0.0]), Df))
    v, dt = veh["v"], veh["dt"]
    wd = S[:, 1:, 0] - S[:, :-1, 0] - v * dt * S[:, :-1, 1]
    wd_shift = S[:, 2:, 0] - S[:, 1:-1, 0] - v * dt * S[:, :-2, 1]
    # a psi_0 estimation error dpsi0 adds the constant v dt dpsi0 per run: remove it, then only the
    # sin-nonlinearity (~1e-8 m) may remain if the logged states are aligned with D
    c0 = wd.mean(axis=1, keepdims=True)
    e_al = np.abs(wd - c0).max()
    e_sh = np.abs(wd_shift - wd_shift.mean(axis=1, keepdims=True)).max()
    print(f"  [0b] zero-slip straight pass: max |d+ - d - v dt psi - const_run| = {e_al:.1e} m (one-step "
          f"misalignment would give {e_sh:.1e} m); const_run = v dt dpsi0_hat: sd {np.std(c0):.1e} m "
          f"(expected v dt 0.15deg/sqrt(T) = {v * dt * math.radians(0.15) / math.sqrt(lg.t):.1e} m)")
    assert e_al < 1e-6 < 1e-4 < e_sh
    # ---------------------------------------------------------------- training data
    t = time.perf_counter()
    data = collect(trainF, np.random.default_rng(seed), ctrl=ctrl, n=n_train, w=w)
    print(f"  [0c] heading reconstruction psi = psi0_hat + sum (v/l) dt tan(delta): residual sd of psi_meas "
          f"{np.degrees(data.noise_sd.mean()):.4f} deg (sensor noise 0.15 deg; min/max "
          f"{np.degrees(data.noise_sd.min()):.3f}/{np.degrees(data.noise_sd.max()):.3f})")
    assert abs(np.degrees(data.noise_sd.mean()) - 0.15) < 0.01
    M = closed_loop_matrix(ctrl, "sim")
    Md = closed_loop_matrix(ctrl, "design")
    lam99, d99 = tube_from_data(data, "W99", w=w)
    mr = mrpi_box(d99["Phi"], d99["wbar"], 1e-3)
    ok = mr["r_inf"] <= mr["r"] + 1e-12 <= mr["r_inf"] + 1e-3 + 1e-12
    # alpha check: Phi^s W inside alpha W, by the zonotope support in each facet direction
    Ps = np.linalg.matrix_power(d99["Phi"], mr["s"])
    a_chk = (np.abs(Ps) @ d99["wbar"] / d99["wbar"]).max()
    print(f"  [0d] RKKM05 W99: alpha={mr['alpha']:.2e} (direct {a_chk:.2e}), s={mr['s']}, r_inf={100 * mr['r_inf']:.3f} "
          f"<= r_tube={100 * mr['r']:.3f} <= r_inf + 0.1 cm: {ok}")
    assert ok and abs(a_chk - mr["alpha"]) < 1e-9
    if not d99["x0_in_Z"]:
        # [0f] MSR05 initial state: the optimal nominal z0 must leave x0 - z0 in Z (independent LP) for the worst vertex
        Vx = _box_vertices(d99["x0bar"])
        worst = max(Vx, key=lambda x: _x0_term(d99["Phi"], mr["alpha"], mr["s"], np.diag(d99["wbar"]), False, [x],
                                               d99["t_entry"])[0])
        f_w, z_w = _x0_term(d99["Phi"], mr["alpha"], mr["s"], np.diag(d99["wbar"]), False, [worst], d99["t_entry"])
        memb = _zonotope_contains(d99["Phi"], d99["wbar"], mr["alpha"], mr["s"], [worst - z_w])
        print(f"  [0f] X0 not in Z: optimal nominal z0 (MSR05) gives r_X0 = {100 * d99['r_x0']:.2e} cm vs "
              f"{100 * d99['r_x0_naive']:.2f} cm for z0 = x0; worst vertex x0 - z0 in Z: {memb}")
        assert memb and d99["r_x0"] <= d99["r_x0_naive"] + 1e-12
    st_c = SlopeTube(d99["Phi"], np.array([0.0, np.inf]), d99["wbar"][None], d99["x0bar"], w=w)
    rmax = max(st_c(Ft, y) for Ft in testF for y in core.plan(Ft, w, 0.0, _UNIT))
    print(f"  [0e] reachable tube with constant W99 on the test lines: max r = {100 * rmax:.3f} cm <= lam_W99 = "
          f"{100 * lam99:.3f} cm: {rmax <= lam99 + 1e-9}")
    assert rmax <= lam99 + 1e-9
    print(f"  closed loop per step: rho(A_K) sim {np.abs(np.linalg.eigvals(M)).max():.5f}, design "
          f"{np.abs(np.linalg.eigvals(Md)).max():.5f}; max |A_K,sim - A_K,design| = {np.abs(M - Md).max():.4f}")

    # ---------------------------------------------------------------- [1] identification
    print(f"\n[1] identification on {data.fids}: {d99['n_res']} one-step residuals, {d99['n_x0']} initial "
          f"states, collect {data.runtime_s:.2f} s")
    names = ["d [m]", "psi [rad]", "delta [rad]", "I [m s]"][: _nx(ctrl)]
    Wr, Gr, X0 = residuals(data, d99["Phi"], 1)
    print("  residual |w|: " + ", ".join(
        f"{nm}: p99 {np.percentile(np.abs(Wr[:, j]), 99):.2e} / max {np.abs(Wr[:, j]).max():.2e}"
        for j, nm in enumerate(names)))
    print("  corr(w): " + np.array2string(np.corrcoef(Wr.T), precision=2, suppress_small=True).replace("\n", ""))
    res = {}
    for var, kw in [("W99", {}), ("Wmax", {}), ("Wg", {}), ("Whull", {}),
                    ("W99", dict(model="design")), ("W99", dict(ts="log"))]:
        lam, dg = tube_from_data(data, var, w=w, **kw)
        tag = var + ("" if not kw else "/" + ",".join(f"{a}={b}" for a, b in kw.items()))
        res[tag] = (lam, dg)
        if var == "Wg":
            print(f"  {tag:18s} bins |g| edges {np.round(dg['edges'][1:-1], 4)} (train max {dg['g_train_max']:.3f}); "
                  f"per-bin r_tube [cm] {np.round(100 * dg['r_bins'], 1)}  ({dg['runtime_s']:.2f} s)")
        else:
            print(f"  {tag:18s} r_tube {100 * dg['r_tube']:6.2f} cm (r_inf {100 * dg['r_inf']:6.2f}, alpha "
                  f"{dg['alpha']:.1e}, s={dg['s']:4d}), X0 in Z: {str(dg['x0_in_Z']):5s} r_X0 {100 * dg['r_x0']:.2f} cm "
                  f"(z0 = x0: {100 * dg['r_x0_naive']:.2f}) -> lam {100 * lam:6.2f} cm  ({dg['runtime_s']:.2f} s"
                  + (f", hull {dg['n_vert']} vert / {dg['n_facets']} facets" if var == "Whull" else "") + ")")

    # ---------------------------------------------------------------- [2] test fields
    print(f"\n[2] test fields: plan with the margin, {n_test} runs each (common conditions per field)")
    hdr = (f"  {'method':18s} {'lam [cm]':>14s} {'K':>3s} {'P(no miss)':>10s} {'E[miss]':>8s} {'overlap':>7s} "
           f"{'rms cm':>6s} {'p99 cm':>6s} {'sup|d| cm':>11s} {'P(in tube)':>10s} {'w out':>7s} {'P(run w out)':>12s} {'plan s':>6s}")
    for F in testF:
        print(f"\n  field {F.fid}: main area {F.M.area:.0f} m2, mean slope {F.z_mean_slope:.2f} deg")
        print(hdr)
        rows = [("nominal lam=0", 0.0, dict(sig_fn=_UNIT, variant="W99", Phi=d99["Phi"], sub=1,
                                             wbar=d99["wbar"], ctrl=ctrl))]
        rows += [(tag, lam, dg) for tag, (lam, dg) in res.items() if "/" not in tag]
        for tag, lam, dg in rows:
            t = time.perf_counter()
            try:
                ys = core.plan(F, w, lam, dg["sig_fn"])
            except ValueError as e:
                print(f"  {tag:18s} {100 * lam:14.2f} {'-':>3s} infeasible ({e})")
                continue
            t_plan = time.perf_counter() - t
            r = evaluate_tube(F, ys, n_test, np.random.default_rng(seed + 1000), lam, dg, w=w)
            lam_s = (f"{100 * lam:14.2f}" if tag != "Wg" else
                     f"{100 * r['r_k'].min():6.2f}-{100 * r['r_k'].max():6.2f}")
            print(f"  {tag:18s} {lam_s:>14s} {r['passes']:3d} {r['p_nomiss']:10.2f} {r['e_miss']:8.5f} "
                  f"{r['overlap']:7.3f} {100 * r['rms']:6.2f} {100 * r['p99']:6.2f} "
                  f"{100 * r['sup_med']:5.1f}/{100 * r['sup_max']:5.1f} {r['p_in_tube']:10.2f} "
                  f"{r['frac_w_out']:7.4f} {r['p_run_w_viol']:12.2f} {t_plan:6.2f}")
    print(f"\n(sup|d| = median/max over runs of the run-level sup of |lateral error| in the main area, i.e. the "
          f"margin a per-run guarantee needs; P(in tube) = runs with |d| <= r_k everywhere; 'w out' = fraction of "
          f"test one-step residuals outside the variant's W; 'P(run w out)' = runs with at least one; the nominal "
          f"row uses W99.)  total {time.perf_counter() - t_all:.1f} s")

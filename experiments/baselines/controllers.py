"""State-of-practice path-tracking controllers for agricultural vehicles, as
pluggable controller objects for core.simulate.

API (every controller)
----------------------
    ctrl = make(name, **kw)          # fresh instance; name in NAMES or a core built-in
    ctrl.reset(R, K, veh, cond)      # called by core.simulate at t = 0
    u = ctrl.command(meas, psi_meas, delta, dt)   # (R, K) steering command [rad]

All state is held as arrays over the flattened (R*K) batch and every operation
is vectorised; nothing loops over vehicles. `cond` is accepted for API
compatibility but never read: the slip gain, roughness, roll compensation and
mounting error are unknown to a real autosteer, so the controllers see only
VEH (v, l_wb, tau, delta_max, rate_max, dt) and the measurements.
Controller model (both designs, from core.VEH):
    d' = v sin(psi) + f_d,   psi' = v tan(delta)/l,   delta' = (u - delta)/tau
where f_d is the unknown lumped lateral drift (in the plant: v sin(psi+beta) -
v sin(psi) with beta the slope / roughness side-slip; plus RTK error motion).

(a) ESOSMC  -- sliding-mode control + linear extended state observer
---------------------------------------------------------------------
Published lineage (all verified 2026-10-13 by web search, see notes):
  [S1] J. Taghia, X. Wang, S. Lam, J. Katupitiya, "A sliding mode controller
       with a nonlinear disturbance observer for a farm vehicle operating in the
       presence of wheel slip", Autonomous Robots 41(1):71-88, 2017,
       doi:10.1007/s10514-015-9530-4.  (SMC on the kinematic lateral-offset
       model of a farm vehicle, disturbance observer for slip-induced matched
       and unmatched uncertainty; confirmed on Springer and dblp.)
  [S2] X. Ji, X. Wei, A. Wang, "A Novel Control Method for Unmanned
       Agricultural Tractors: Composite Back-stepping Sliding Mode Path
       Tracking", Information Technology and Control 52(2):515-528, 2023,
       doi:10.5755/j01.itc.52.2.31649.  (ESOs estimate lumped disturbance,
       sliding-mode path tracking; confirmed on the journal page.)
  [S3] A. Wang, X. Ji, Q. Song, X. Wei, W. Chen, K. Wang, "Path Tracking
       Controller and System Design for Agricultural Tractors Based on Improved
       Stanley and Sliding Mode Algorithms Considering Sideslip Compensation",
       Agronomy 15(10):2329, 2025 (ESO side-slip observation + sliding-mode
       heading control; title/authors/volume confirmed from the MDPI listing,
       DOI 10.3390/agronomy15102329 follows MDPI's scheme but the publisher page
       could not be opened from this machine -- verify before submission).
  [G]  Z. Gao, "Scaling and bandwidth-parameterization based controller
       tuning", Proc. American Control Conf. 2003, pp. 4989-4996,
       doi:10.1109/ACC.2003.1242516  (linear ESO, all observer poles at -omega_o).
Algorithm as implemented:
  ESO on the lateral channel, states (d_hat, f_hat), driven by the measured
  offset y and measured heading psi_m (discrete predictor-corrector form):
      predict  d_hat <- d_hat + dt (v sin psi_m[t-1] + f_hat)
      correct  e = y - d_hat;  d_hat += l1 e;  f_hat += l2 e
      l1 = 1 - p^2,  l2 = (1 - p)^2 / dt,  p = exp(-omega_o dt)
  (this places both discrete observer poles at exp(-omega_o dt), the exact
  discrete counterpart of Gao's bandwidth parametrisation beta1 = 2 omega_o,
  beta2 = omega_o^2).
  Sliding surface  s = psi_m + lam d_hat + f_hat / v,
  so that on s = 0:  d' = -v lam d + (f - f_hat)   (offset-free for f_hat -> f).
  Reaching law (exponential + constant rate, boundary-layer saturation):
      s' = -k_sw sat(s / phi) - eta s
  Equivalent control from s' = (v/l) tan(delta) + lam (v sin psi + f_hat):
      tan(delta_cmd) = -(l/v) [ lam (v sin psi_m + f_hat) + k_sw sat(s/phi) + eta s ]
  delta_cmd clipped to +/- delta_max (the plant also rate-limits it).
Adaptation decisions (explicit):
  A1 The kinematic offset model of [S1] is reduced to the straight-line case
     (zero path curvature); wheel-slip angles enter only through the lumped
     drift f_d, which the ESO of [S2]/[S3] estimates (no slip-angle model).
  A2 f_hat' is NOT used in the equivalent control (it is the derivative of a
     noisy estimate); it is covered by the switching gain k_sw, a standard choice.
  A3 The steering lag tau = 0.25 s and rate limit are not in the SMC design
     (as in [S1]-[S3]); robustness to them is obtained by keeping the
     in-layer bandwidth k_sw/phi + eta = 2 1/s << 1/tau and checked by the
     linearised closed-loop spectral radius in selftest() (lag + Euler plant).
  A4 Gains: lam = 0.5 1/m, eta = 1 1/s, k_sw = 0.05 rad/s, phi = 0.05 rad,
     omega_o = 3 rad/s, chosen on two non-test paddy fields (fid 98, 177) by
     a small grid (see tune()) so that the small-signal bandwidth matches the
     built-in LQR; the selftest fields are different.

(b) OffsetFreeMPC  -- linear offset-free MPC, condensed QP, accelerated dual FISTA
---------------------------------------------------------------------------------
  [P]  G. Pannocchia, J. B. Rawlings, "Disturbance models for offset-free
       model-predictive control", AIChE Journal 49(2):426-437, 2003
       (title/journal/volume/pages confirmed via the Univ. of Pisa repository
       and a USPTO citation; DOI not confirmed here). Main result: augment the
       model with n_d = n_y integrating disturbances, estimate them, and
       compute steady-state targets -> zero offset in the controlled variables.
  [M]  U. Maeder, F. Borrelli, M. Morari, "Linear offset-free model predictive
       control", Automatica 45(10):2214-2222, 2009,
       doi:10.1016/j.automatica.2009.06.005 (confirmed from a citing reference
       list).
  [PB] P. Patrinos, A. Bemporad, "An accelerated dual gradient-projection
       algorithm for embedded linear model predictive control", IEEE Trans.
       Automatic Control 59(1):18-33, 2014, doi:10.1109/TAC.2013.2275667
       (volume/pages/DOI from citing reference lists; verify on IEEE Xplore).
  Context (agricultural MPC path tracking): J. Backman, T. Oksanen, A. Visala,
       "Navigation system for agricultural machines: Nonlinear Model Predictive
       path tracking", Computers and Electronics in Agriculture 82:32-43, 2012,
       doi:10.1016/j.compag.2011.12.009 (from a citing reference list).
Algorithm as implemented:
  Model x = [d, psi, delta], u = delta_cmd, disturbance p = [f_d, f_psi]
  (lateral drift into d', yaw-rate bias into psi'), continuous
      d' = v psi + f_d,  psi' = (v/l) delta + f_psi,  delta' = (u - delta)/tau
  discretised exactly (ZOH) at Ts = 0.1 s:  x+ = A x + B u + Bd p,  p+ = p.
  Measured outputs y = [d_meas, psi_meas] (n_y = 2 = n_d, the [P] condition;
  delta comes from the steering-angle sensor and is used directly). Augmented
  system detectable (rank [[A - I, Bd], [C, 0]] = n_x + n_d is checked).
  Observer: steady-state Kalman filter on [d, psi, f_d, f_psi] (random-walk
  disturbances), run at the simulator rate dt = 0.05 s with delta and the held
  u as known inputs.
  Target: solve [[A - I, B], [Hc, 0]] [x_s; u_s] = [-Bd p_hat; r], Hc = [1 0 0],
  r = 0 (controlled variable = lateral offset).
  FHOCP on deviations (x - x_s, u - u_s), horizon N = 20 (2 s):
      min  sum_k x'Qx + u'Ru + x_N' P x_N,   P = DARE(A, B, Q, R)
      s.t. |u_k| <= delta_max                    (steering box)
           |u_k - delta_k| <= tau * rate_max     (steering-rate box: the peak
             rate (u - delta)/tau of the first-order actuator over the hold
             interval stays within rate_max, i.e. the plant rate limiter is
             inactive on the predicted trajectory)
  condensed to  min 0.5 z'(2H)z + 2 g'z  s.t. lo <= G z <= hi, G = [I; I - S_delta].
  Solver ([PB]): FISTA on the dual,  y+ = prox_{t sigma_[lo,hi]}(w + t G z(w)),
  z(w) = z_unc - H^-1 G' w, fixed n_iter iterations, step t = 1/||G H^-1 G'||
  after Jacobi row scaling (optional gradient restart, off by default),
  warm start from the previous multipliers
  shifted by one stage. Because the unconstrained optimum z_unc = -H^-1 g is
  the exact QP solution whenever it is feasible (convex QP), vehicles whose
  z_unc satisfies all constraints skip the iterations (exact, not a
  heuristic); only the rest run FISTA. The applied u_0 is finally projected on
  its own (exact, box) stage-0 constraint set. The MPC is re-solved every
  2 simulator steps (ZOH), the observer runs every step.
  Adaptation decisions: tan/sin linearised (straight lines, small angles);
  reference r = 0 (straight passes); weights Q = diag(4, 1, 0.1), R = 4 as in
  the built-in lqr_i (without the integral state), so the unconstrained MPC
  equals the infinite-horizon LQR on the lag-augmented model (terminal cost =
  DARE), which selftest() verifies.
"""
import math
import time

import numpy as np
from scipy.linalg import expm, solve_discrete_are

import core

NAMES = ("esosmc", "offset_free_mpc")


# ---------------------------------------------------------------------------- utils
def _zoh(Ac, Bc, T):
    """Exact zero-order-hold discretisation."""
    n, m = Ac.shape[0], Bc.shape[1]
    M = np.zeros((n + m, n + m))
    M[:n, :n], M[:n, n:] = Ac, Bc
    E = expm(M * T)
    return E[:n, :n], E[:n, n:]


def _sat(x):
    return np.clip(x, -1.0, 1.0)


# --------------------------------------------------------------------------- ESOSMC
class ESOSMC:
    """Sliding-mode lateral controller with a linear extended state observer
    estimating the lumped lateral drift f_d (side slip / slope drift).

    Parameters
    ----------
    lam : sliding-surface weight on the lateral offset [1/m] (s = psi + lam d + f/v)
    eta : proportional reaching rate [1/s]
    k_sw : switching (constant-rate) reaching gain [rad/s]
    phi : boundary-layer width of sat(s/phi) [rad]
    omega_o : ESO bandwidth [rad/s] (both observer poles at exp(-omega_o dt))
    """

    name = "esosmc"
    _lin_state = ("z1", "z2", "psi_prev")  # internal state (for the linearisation probe)

    def __init__(self, lam=0.3, eta=0.5, k_sw=0.025, phi=0.05, omega_o=3.0):
        self.lam, self.eta, self.k_sw, self.phi, self.omega_o = lam, eta, k_sw, phi, omega_o

    def reset(self, R, K, veh, cond=None):
        self.v, self.l, self.dmax = veh["v"], veh["l_wb"], veh["delta_max"]
        self.dt = veh["dt"]
        self._gains(self.dt)
        self.shape = (R, K)
        self.z1 = None  # d_hat (initialised from the first measurement)
        self.z2 = np.zeros(R * K)  # f_hat [m/s]
        self.psi_prev = np.zeros(R * K)
        self.t = 0

    def _gains(self, dt):
        p = math.exp(-self.omega_o * dt)
        self.l1, self.l2 = 1.0 - p * p, (1.0 - p) ** 2 / dt
        self._dt_g = dt

    def command(self, meas, psi_meas, delta, dt):
        if dt != self._dt_g:
            self._gains(dt)
        y, pm = meas.ravel(), psi_meas.ravel()
        v, l = self.v, self.l
        if self.z1 is None:
            self.z1 = y.copy()
        else:  # ESO predict (with last step's heading) + correct with current y
            self.z1 = self.z1 + dt * (v * np.sin(self.psi_prev) + self.z2)
            e = y - self.z1
            self.z1 = self.z1 + self.l1 * e
            self.z2 = self.z2 + self.l2 * e
        s = pm + self.lam * self.z1 + self.z2 / v
        tan_d = -(l / v) * (self.lam * (v * np.sin(pm) + self.z2)
                            + self.k_sw * _sat(s / self.phi) + self.eta * s)
        u = np.clip(np.arctan(tan_d), -self.dmax, self.dmax)
        self.psi_prev = pm
        self.t += 1
        return u.reshape(self.shape)


# --------------------------------------------------------------------- OffsetFreeMPC
class OffsetFreeMPC:
    """Linear offset-free MPC (Pannocchia & Rawlings 2003 disturbance model,
    steady-state Kalman filter, target calculation) with a condensed QP solved
    by a fixed number of accelerated dual gradient-projection (FISTA)
    iterations (Patrinos & Bemporad 2014), batched over all vehicles.

    Parameters
    ----------
    N, Ts : horizon length and MPC sampling time [s] (re-solved every Ts / dt steps)
    Q, R : stage weights on [d, psi, delta] and on u (deviation variables)
    n_iter : dual FISTA iterations per solve (fixed)
    sd_meas : Kalman measurement std of (d_meas [m], psi_meas [rad])
    sd_proc : Kalman process std per sqrt(s) of (d, psi, f_d, f_psi)
    yaw_disturbance : include f_psi (n_d = n_y = 2); False -> f_d only
    exact_check : skip the iterations for vehicles whose unconstrained optimum
        is feasible (exact); False runs FISTA on every vehicle (for testing)
    restart : gradient-based adaptive restart of the momentum (off by default:
        on this rank-deficient dual it slowed convergence in the selftest)
    """

    name = "offset_free_mpc"
    _lin_state = ("xi", "u_prev", "delta_prev")

    def __init__(self, N=20, Ts=0.1, Q=(2.0, 1.0, 0.1), R=8.0, n_iter=50,
                 sd_meas=(0.01, math.radians(0.15)), sd_proc=(0.003, 0.001, 0.04, 0.002),
                 yaw_disturbance=True, exact_check=True, restart=False):
        self.N, self.Ts, self.Qw, self.Rw, self.n_iter = N, Ts, np.diag(Q), float(R), n_iter
        self.sd_meas, self.sd_proc = sd_meas, sd_proc
        self.yaw_dist, self.exact_check, self.restart = yaw_disturbance, exact_check, restart
        self.audit = 0  # >0: check up to this many constrained solves per update against OSQP (tests)
        self._key = None

    # ------------------------------------------------------------------ design
    def _build(self, veh):
        key = (veh["v"], veh["l_wb"], veh["tau"], veh["dt"], veh["delta_max"], veh["rate_max"])
        if key == self._key:
            return
        self._key = key
        v, l, tau, dt = veh["v"], veh["l_wb"], veh["tau"], veh["dt"]
        self.v, self.l, self.tau, self.dt = v, l, tau, dt
        self.dmax, self.c_rate = veh["delta_max"], tau * veh["rate_max"]
        self.hold = max(1, int(round(self.Ts / dt)))
        Ts, N = self.hold * dt, self.N
        self.Ts_eff = Ts
        Ac = np.array([[0, v, 0], [0, 0, v / l], [0, 0, -1 / tau]], float)
        Bc = np.array([[0], [0], [1 / tau]], float)
        Bdc = np.array([[1, 0], [0, 1], [0, 0]], float)[:, : 2 if self.yaw_dist else 1]
        nd = Bdc.shape[1]
        self.nd = nd
        # MPC model at Ts (exact ZOH for u and the constant disturbance)
        Ad, BB = _zoh(Ac, np.c_[Bc, Bdc], Ts)
        Bd_u, Bd_p = BB[:, :1], BB[:, 1:]
        self.A, self.B, self.Bp = Ad, Bd_u, Bd_p
        # detectability of the augmented model (Pannocchia & Rawlings 2003, Lemma 1)
        C = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], float)  # d, psi measured; delta from sensor
        Mdet = np.block([[Ad - np.eye(3), Bd_p], [C, np.zeros((3, nd))]])
        assert np.linalg.matrix_rank(Mdet) == 3 + nd, "augmented model not detectable"
        # steady-state target map  [x_s; u_s] = Tss @ p
        Hc = np.array([[1.0, 0, 0]])
        Mss = np.block([[Ad - np.eye(3), Bd_u], [Hc, np.zeros((1, 1))]])
        self.Tss = np.linalg.solve(Mss, np.r_[-Bd_p, np.zeros((1, nd))])  # (4, nd)
        # terminal cost and LQR gain
        Q, Rr = self.Qw, np.array([[self.Rw]])
        P = solve_discrete_are(Ad, Bd_u, Q, Rr)
        self.P = P
        self.K_lqr = np.linalg.solve(Rr + Bd_u.T @ P @ Bd_u, Bd_u.T @ P @ Ad).ravel()
        # condensed prediction X = Phi x0 + Gam U  (x_1..x_N)
        Phi = np.zeros((3 * N, 3))
        Gam = np.zeros((3 * N, N))
        Ak = np.eye(3)
        for k in range(N):
            Ak = Ad @ Ak
            Phi[3 * k:3 * k + 3] = Ak
            for j in range(k + 1):
                Gam[3 * k:3 * k + 3, j] = (np.linalg.matrix_power(Ad, k - j) @ Bd_u).ravel()
        Qbar = np.kron(np.eye(N), Q)
        Qbar[-3:, -3:] = P
        H = Gam.T @ Qbar @ Gam + self.Rw * np.eye(N)
        F = Gam.T @ Qbar @ Phi  # (N, 3)
        self.H, self.F = H, F
        Hinv = np.linalg.inv(H)
        Hinv = 0.5 * (Hinv + Hinv.T)
        self.Hinv = Hinv
        self.Kunc = Hinv @ F  # z_unc = -x0 @ Kunc.T
        # rate rows: r_k = u_k - delta_k = (I - S) U - T x0
        S = np.zeros((N, N))
        T = np.zeros((N, 3))
        T[0, 2] = 1.0
        for k in range(1, N):
            S[k] = Gam[3 * (k - 1) + 2]
            T[k] = Phi[3 * (k - 1) + 2]
        G = np.r_[np.eye(N), np.eye(N) - S]  # (2N, N)
        W0 = G @ Hinv @ G.T
        Dsc = 1.0 / np.sqrt(np.diag(W0))  # Jacobi row scaling
        self.G_raw, self.T_rate = G, T
        self.Dsc = Dsc
        Gs = Dsc[:, None] * G
        self.Gs = Gs
        self.W = Gs @ Hinv @ Gs.T
        self.W = 0.5 * (self.W + self.W.T)
        self.step_t = 1.0 / np.linalg.eigvalsh(self.W).max()
        self.GK = Gs @ self.Kunc  # Gz_unc = -x0 @ GK.T
        self.Mz = Hinv @ Gs.T  # z = z_unc - y @ Mz.T
        self.m = 2 * N
        # observer at the simulator rate dt: xi = [d, psi, f_d, (f_psi)], known inputs delta, u
        n5 = 3 + nd
        A5c = np.zeros((n5, n5))
        A5c[:3, :3], A5c[:3, 3:] = Ac, Bdc
        B5c = np.r_[Bc, np.zeros((nd, 1))]
        A5, B5 = _zoh(A5c, B5c, dt)
        keep = [0, 1] + list(range(3, n5))
        self.Axi = A5[np.ix_(keep, keep)]
        self.axd = A5[keep, 2]  # effect of the current delta
        self.bxu = B5[keep, 0]  # effect of the held command
        Cxi = np.zeros((2, len(keep)))
        Cxi[0, 0] = Cxi[1, 1] = 1.0
        sdp = np.array(self.sd_proc[:2] + self.sd_proc[2:2 + nd])
        Qn = np.diag(sdp ** 2 * dt)
        Rn = np.diag(np.array(self.sd_meas) ** 2)
        Pk = solve_discrete_are(self.Axi.T, Cxi.T, Qn, Rn)
        self.Kf = Pk @ Cxi.T @ np.linalg.inv(Cxi @ Pk @ Cxi.T + Rn)  # filter (current) gain
        self.Cxi = Cxi
        self.obs_poles = np.linalg.eigvals((np.eye(len(keep)) - self.Kf @ Cxi) @ self.Axi)

    def reset(self, R, K, veh, cond=None):
        self._build(veh)
        n = R * K
        self.shape = (R, K)
        self.xi = None
        self.u_prev = np.zeros(n)
        self.delta_prev = np.zeros(n)
        self.u_hold = np.zeros(n)
        self.y_dual = np.zeros((n, self.m))
        self.t = 0
        self.n_solves = 0
        self.n_iter_vehicles = 0  # vehicle-solves that needed FISTA (active constraints)
        self.solve_time = 0.0
        self.audit_err = []

    # ------------------------------------------------------------------- QP
    def bounds(self, x0, us):
        """Scaled lo/hi of G z for deviation state x0 (n,3) and target input us (n,)."""
        N, D = self.N, self.Dsc
        lo = np.empty((len(x0), self.m))
        hi = np.empty_like(lo)
        lo[:, :N] = (-self.dmax - us)[:, None]
        hi[:, :N] = (self.dmax - us)[:, None]
        td = x0 @ self.T_rate.T
        lo[:, N:] = -self.c_rate + td
        hi[:, N:] = self.c_rate + td
        return lo * D, hi * D

    def solve(self, x0, us, y_warm=None, exact_check=None, n_iter=None):
        """Solve the condensed QP for a batch. Returns (z (n,N), y_dual (n,2N), active mask)."""
        exact_check = self.exact_check if exact_check is None else exact_check
        n_iter = self.n_iter if n_iter is None else n_iter
        z = -x0 @ self.Kunc.T
        Gz_unc = -x0 @ self.GK.T
        lo, hi = self.bounds(x0, us)
        y = np.zeros((len(x0), self.m)) if y_warm is None else y_warm.copy()
        if exact_check:
            act = np.any((Gz_unc < lo - 1e-12) | (Gz_unc > hi + 1e-12), axis=1)
            y[~act] = 0.0
        else:
            act = np.ones(len(x0), bool)
        if act.any():
            idx = np.nonzero(act)[0]
            ya = self._fista(Gz_unc[idx], lo[idx], hi[idx], y[idx], n_iter)
            y[idx] = ya
            z[idx] = z[idx] - ya @ self.Mz.T
        return z, y, act

    def _fista(self, Gz_unc, lo, hi, y0, n_iter):
        t, W = self.step_t, self.W
        y = y0
        w = y0.copy()
        th = np.ones((len(y0), 1))
        for _ in range(n_iter):
            vv = w + t * (Gz_unc - w @ W)
            y_new = vv - t * np.clip(vv / t, lo, hi)
            th_new = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * th * th))
            w = y_new + ((th - 1.0) / th_new) * (y_new - y)
            if self.restart:  # gradient restart (O'Donoghue & Candes 2015)
                rs = np.sum((w - y_new) * (y_new - y), axis=1, keepdims=True) > 0
                if rs.any():
                    rs1 = rs[:, 0]
                    w[rs1] = y_new[rs1]
                    th_new[rs1] = 1.0
            y, th = y_new, th_new
        return y

    # -------------------------------------------------------------- control
    def command(self, meas, psi_meas, delta, dt):
        if abs(dt - self.dt) > 1e-12:
            raise ValueError("OffsetFreeMPC was built for dt=%g, got %g" % (self.dt, dt))
        ym = np.stack([meas.ravel(), psi_meas.ravel()], 1)
        dl = delta.ravel()
        if self.xi is None:
            self.xi = np.zeros((len(dl), 2 + self.nd))
            self.xi[:, :2] = ym
        else:
            xp = self.xi @ self.Axi.T + self.delta_prev[:, None] * self.axd + self.u_prev[:, None] * self.bxu
            self.xi = xp + (ym - xp[:, :2]) @ self.Kf.T
        if self.t % self.hold == 0:
            t0 = time.perf_counter()
            p = self.xi[:, 2:]
            ss = p @ self.Tss.T  # (n, 4) = [d_s, psi_s, delta_s, u_s]
            x0 = np.c_[self.xi[:, 0] - ss[:, 0], self.xi[:, 1] - ss[:, 1], dl - ss[:, 2]]
            us = ss[:, 3]
            yw = self.y_dual
            N = self.N
            yw = np.c_[yw[:, 1:N], np.zeros((len(dl), 1)), yw[:, N + 1:], np.zeros((len(dl), 1))]
            z, self.y_dual, act = self.solve(x0, us, yw)
            if self.audit and act.any():  # verification only: compare with a high-accuracy QP solve
                for i in np.nonzero(act)[0][: self.audit]:
                    self.audit_err.append(abs(z[i, 0] - _qp_reference(self, x0[i], us[i])[0]))
            u = us + z[:, 0]
            lo0 = np.maximum(-self.dmax, dl - self.c_rate)
            hi0 = np.minimum(self.dmax, dl + self.c_rate)
            self.u_hold = np.clip(u, lo0, hi0)
            self.n_solves += len(dl)
            self.n_iter_vehicles += int(act.sum())
            self.solve_time += time.perf_counter() - t0
        u = self.u_hold
        self.u_prev, self.delta_prev = u, dl
        self.t += 1
        return u.reshape(self.shape)


# ------------------------------------------------------- built-in replicas (testing)
class BuiltinReplica:
    """Object version of core.simulate's built-in 'lqr' / 'lqr_i' laws (same
    gains from core._lqr_gains, same anti-windup), so that the built-ins can be
    wrapped by the steering recorder. selftest() checks it reproduces the
    string controller bit-for-bit."""

    def __init__(self, kind="lqr_i"):
        assert kind in ("lqr", "lqr_i")
        self.kind = kind

    def reset(self, R, K, veh, cond=None):
        self.K1, self.K4 = core._lqr_gains(veh["v"], veh["l_wb"], veh["dt"])
        self.dmax = veh["delta_max"]
        self.integ = np.zeros((R, K))

    def command(self, meas, psi_meas, delta, dt):
        if self.kind == "lqr":
            return -(self.K1[0] * meas + self.K1[1] * psi_meas)
        K4 = self.K4
        u_try = -(K4[0] * meas + K4[1] * psi_meas + K4[2] * delta + K4[3] * (self.integ + meas * dt))
        sat = np.abs(u_try) >= self.dmax
        self.integ = np.where(sat, self.integ, np.clip(self.integ + meas * dt, -0.3, 0.3))
        return -(K4[0] * meas + K4[1] * psi_meas + K4[2] * delta + K4[3] * self.integ)


# ------------------------------------------------------------------------- factory
PRESETS = {
    # "iso": tuned on non-test paddy fields (fid 98, 177; see tune()) for the lowest RMS lateral
    # error at a steering-rate RMS no larger than the built-in lqr_i's (2.9 deg/s there): the
    # equal-actuator-effort comparison. "aggressive": about 2x that steering effort (5.6-5.8 deg/s).
    "esosmc": {"iso": dict(lam=0.3, eta=0.5, k_sw=0.025, phi=0.05, omega_o=3.0),
               "aggressive": dict(lam=0.5, eta=1.0, k_sw=0.025, phi=0.05, omega_o=5.0)},
    "offset_free_mpc": {"iso": dict(Q=(2.0, 1.0, 0.1), R=8.0, sd_proc=(0.003, 0.001, 0.04, 0.002)),
                        "aggressive": dict(Q=(4.0, 1.0, 0.1), R=4.0, sd_proc=(0.003, 0.001, 0.16, 0.002))},
}


def make(name, preset="iso", **kw):
    """Fresh controller instance.

    name   : 'esosmc' | 'offset_free_mpc' (alias 'mpc'); the core built-ins
             'pure_pursuit', 'stanley', 'lqr', 'lqr_i' are returned as the
             string core.simulate understands.
    preset : 'iso' (default, equal steering effort to lqr_i) or 'aggressive'.
    kw     : overrides of the preset's constructor arguments.
    """
    key = name.lower()
    if key in ("mpc", "offsetfreempc"):
        key = "offset_free_mpc"
    if key in PRESETS:
        args = dict(PRESETS[key][preset])
        args.update(kw)
        return ESOSMC(**args) if key == "esosmc" else OffsetFreeMPC(**args)
    if key in ("pure_pursuit", "stanley", "lqr", "lqr_i"):
        if kw:
            raise ValueError("built-in controllers take no parameters")
        return key
    raise KeyError(name)


# ------------------------------------------------------------------ verification
class _SlopeField:
    """Duck-typed synthetic field for core.simulate: a 400 m straight pass on a
    constant side slope tan(theta) = g (no DEM), rot = 0."""

    def __init__(self, g, length=400.0):
        from shapely.geometry import box

        self.P = box(0.0, -20.0, length, 20.0)
        self.rot = 0.0
        self._g = g

    def gy(self, x, y):
        return np.full(np.shape(x), self._g, float)

    chord = core.Field.chord


def slope_step_test(ctrl, slope_deg=5.0, k_s=0.6, R=10, mount=0.0, seed=0):
    """Closed-loop run of core.simulate on a constant side slope with the
    measurement bias sources switched off (full roll compensation, no RTK
    error, no mounting error, no roughness), so the remaining lateral offset is
    the controller's own steady-state offset under side slip
    beta = -0.35 k_s tan(theta).  With `mount` != 0 the measurement is shifted
    by a constant: the controller then executes a step of size -mount (large
    transient / constraint test). Returns (s [m], D (R, n) field-frame offsets)."""
    F = _SlopeField(math.tan(math.radians(slope_deg)))
    rng = np.random.default_rng(seed)
    cond = core.Condition(rng, R)
    cond.k_s[:] = k_s
    cond.rough[:] = 0.0
    cond.comp[:] = 1.0
    cond.rtk_scale = 0.0
    cond.mount[:] = mount
    X, D = core.simulate(F, np.array([0.0]), cond, rng, ctrl=ctrl)
    return X[0] - X[0][0], D[0]


def linear_spectral_radius(ctrl, eps=1e-5):
    """Spectral radius (per simulator step) of the closed loop of `ctrl` with
    the simulator's linearised plant (Euler, dt; first-order steering lag; no
    noise, no slip), obtained by probing the actual implementation with small
    perturbations of plant + controller state (linear regime: inside the
    boundary layer / constraints inactive)."""
    veh = core.VEH
    v, l, tau, dt = veh["v"], veh["l_wb"], veh["tau"], veh["dt"]
    nsteps = getattr(ctrl, "hold", 1)
    ctrl.reset(1, 1, veh, None)
    # one call to initialise the internal state containers
    ctrl.command(np.zeros((1, 1)), np.zeros((1, 1)), np.zeros((1, 1)), dt)
    widths = []
    for a in ctrl._lin_state:
        val = getattr(ctrl, a)
        widths.append(1 if np.ndim(val) == 1 else val.shape[1])
    n = 3 + sum(widths)
    ctrl.reset(n, 1, veh, None)
    ctrl.command(np.zeros((n, 1)), np.zeros((n, 1)), np.zeros((n, 1)), dt)
    if hasattr(ctrl, "hold"):
        nsteps = ctrl.hold
        while ctrl.t % ctrl.hold:  # align to an MPC update instant
            ctrl.command(np.zeros((n, 1)), np.zeros((n, 1)), np.zeros((n, 1)), dt)
    E = eps * np.eye(n)
    d, psi, delta = E[:, 0].copy(), E[:, 1].copy(), E[:, 2].copy()
    o = 3
    for a, wdt in zip(ctrl._lin_state, widths):
        val = E[:, o:o + wdt]
        setattr(ctrl, a, val[:, 0].copy() if wdt == 1 else val.copy())
        o += wdt
    for _ in range(nsteps):
        u = ctrl.command(d[:, None], psi[:, None], delta[:, None], dt)[:, 0]
        delta = delta + (u - delta) / tau * dt
        d = d + v * psi * dt
        psi = psi + v * delta / l * dt
    cols = [d, psi, delta]
    for a in ctrl._lin_state:
        val = getattr(ctrl, a)
        cols += [val] if np.ndim(val) == 1 else list(val.T)
    M = np.array(cols) / eps  # (n, n): column j = image of basis vector j
    rho = np.abs(np.linalg.eigvals(M)).max()
    return rho ** (1.0 / nsteps)


class _Recorder:
    """Wraps a controller object and records steering-rate statistics."""

    def __init__(self, inner):
        self.inner = inner

    def reset(self, R, K, veh, cond):
        self.inner.reset(R, K, veh, cond)
        self.rate_max, self.dt = veh["rate_max"], veh["dt"]
        self.prev = None
        self.sq, self.n, self.at_lim, self.flips, self.max_abs = 0.0, 0, 0, 0, 0.0
        self.prev_rate = None

    def command(self, meas, psi_meas, delta, dt):
        if self.prev is not None:
            rate = (delta - self.prev) / dt
            self.sq += float(np.sum(rate ** 2))
            self.n += rate.size
            self.at_lim += int(np.sum(np.abs(rate) >= 0.999 * self.rate_max))
            if self.prev_rate is not None:
                self.flips += int(np.sum(np.sign(rate) * np.sign(self.prev_rate) < 0))
            self.prev_rate = rate
        self.prev = delta.copy()
        self.max_abs = max(self.max_abs, float(np.abs(delta).max()))
        return self.inner.command(meas, psi_meas, delta, dt)

    def stats(self):
        n = max(self.n, 1)
        return dict(rate_rms_deg=math.degrees(math.sqrt(self.sq / n)), frac_rate_lim=self.at_lim / n,
                    flip_rate_hz=self.flips / n / self.dt, max_delta_deg=math.degrees(self.max_abs))


def tracking_metrics(F, ys, X, D, w=3.0):
    """RMS / p99 of |lateral error| on the main-area grid, mean |per-pass bias|."""
    minx, _, maxx, _ = F.M.bounds
    xg = np.arange(math.ceil(minx), math.floor(maxx) + 1, 1.0)
    off = np.stack([core.pass_offsets(X[k], D[k], xg) for k in range(len(ys))])  # (K, R, nx)
    mask = np.zeros((len(ys), len(xg)), bool)
    for j, x in enumerate(xg):
        c = core._chord_x(F.M, x)
        if c is not None:
            mask[:, j] = (ys > c[0]) & (ys < c[1])
    e = np.abs(off[np.broadcast_to(mask[:, None, :], off.shape)])
    e = e[np.isfinite(e)]
    bias = []
    for k in range(len(ys)):
        if mask[k].sum() >= 10:
            bias.append(np.abs(np.nanmean(off[k][:, mask[k]], axis=1)))
    bias = np.concatenate(bias) if bias else np.array([np.nan])
    return dict(rms=float(np.sqrt(np.mean(e ** 2))), p99=float(np.percentile(e, 99)),
                bias=float(np.mean(bias)))


def _run(F, ys, ctrl, n_runs, seed, w=3.0):
    rng = np.random.default_rng(seed)
    cond = core.Condition(rng, n_runs)
    t0 = time.perf_counter()
    X, D = core.simulate(F, ys, cond, rng, ctrl=ctrl)
    rt = time.perf_counter() - t0
    miss = core.evaluate(F, ys, X, D, w)
    m = tracking_metrics(F, ys, X, D, w)
    m.update(p_nomiss=float(np.mean(miss == 0)), e_miss=float(miss.mean()), runtime=rt)
    return m


def tune(kind="esosmc", fids=(98, 177), n_runs=20, seed=7):
    """Gain grid used to set PRESETS, on NON-test paddy fields (fid 98, 177).
    Prints mean RMS |lateral error| and steering-rate RMS per setting, plus the
    built-in lqr_i reference; returns [(rms, rate_rms, kwargs)] sorted by rms.
    'iso' = lowest rms with rate_rms <= lqr_i's; 'aggressive' = about 2x the rate."""
    Fs = {F.fid: F for F in core.load_fields("paddy")}

    def ev(factory):
        r, rr = [], []
        for fid in fids:
            F = Fs[fid]
            ys = core.plan(F, 3.0, 0.0, lambda f, y: 0.0)
            rec = _Recorder(factory())
            r.append(_run(F, ys, rec, n_runs, seed)["rms"])
            rr.append(rec.stats()["rate_rms_deg"])
        return float(np.mean(r)), float(np.mean(rr))

    ref = ev(lambda: BuiltinReplica("lqr_i"))
    print(f"lqr_i reference: rms={1e3 * ref[0]:.1f} mm  steering rate RMS={ref[1]:.2f} deg/s")
    if kind == "esosmc":  # c = k_sw/phi + eta is the in-layer reaching bandwidth
        grid = [dict(lam=lam, eta=c - 0.5, k_sw=0.025, phi=0.05, omega_o=wo) for lam in (0.3, 0.5, 0.8)
                for c in (1.0, 1.5, 2.0) for wo in (1.0, 2.0, 3.0, 5.0)]
        cls = ESOSMC
    else:
        grid = [dict(Q=(qd, 1.0, 0.1), R=R, sd_proc=(0.003, 0.001, sf, 0.002)) for qd in (2.0, 4.0, 8.0, 16.0)
                for R in (4.0, 8.0) for sf in (0.04, 0.08, 0.16, 0.32)]
        cls = OffsetFreeMPC
    res = []
    for kw in grid:
        rms, rate = ev(lambda: cls(**kw))
        res.append((rms, rate, kw))
        print(f"{kw}  rms={1e3 * rms:.1f} mm  rate={rate:.2f} deg/s", flush=True)
    res.sort(key=lambda t: t[0])
    iso = [r for r in res if r[1] <= ref[1]]
    if iso:
        print("best at <= lqr_i steering effort:", iso[0])
    return res


def _qp_reference(mpc, x0, us):
    """High-accuracy OSQP solution of one condensed QP (verification only)."""
    import osqp
    from scipy import sparse

    lo, hi = mpc.bounds(x0[None], np.array([us]))
    g = mpc.F @ x0
    prob = osqp.OSQP()
    prob.setup(P=sparse.csc_matrix(2 * mpc.H), q=2 * g, A=sparse.csc_matrix(mpc.Gs), l=lo[0], u=hi[0],
               eps_abs=1e-10, eps_rel=1e-10, max_iter=200000, polish=False, verbose=False)
    r = prob.solve()
    return r.x


def selftest(n_runs=50, seed=0, w=3.0):
    t_all = time.time()
    veh = core.VEH
    print("controllers selftest  (v=%.1f m/s, l=%.1f m, tau=%.2f s, dt=%.2f s)" % (
        veh["v"], veh["l_wb"], veh["tau"], veh["dt"]))

    # ---------------------------------------------------------------- 1. QP checks
    mpc = OffsetFreeMPC()
    mpc.reset(1, 1, veh, None)
    print(f"\n[1] OffsetFreeMPC QP: N={mpc.N}, Ts={mpc.Ts_eff:.2f}s, {mpc.m} constraint rows, "
          f"observer poles |p| = {np.round(np.sort(np.abs(mpc.obs_poles)), 4)}")
    err_k = np.abs(mpc.Kunc[0] - mpc.K_lqr).max()
    print(f"  unconstrained MPC first row vs DARE-LQR gain: max |dK| = {err_k:.2e}")
    assert err_k < 1e-8
    rng = np.random.default_rng(seed)
    nb = 2000
    x0 = np.c_[rng.normal(0, 0.03, nb), rng.normal(0, 0.01, nb), rng.normal(0, 0.01, nb)]
    us = rng.normal(0, 0.005, nb)
    z_f, _, _ = mpc.solve(x0, us, exact_check=False, n_iter=mpc.n_iter)
    z_u = -np.linalg.solve(mpc.H, mpc.F @ x0.T).T
    e_unc = np.abs(z_f - z_u).max()
    print(f"  inactive constraints, {nb} random states, FISTA ({mpc.n_iter} it, cold, no shortcut) "
          f"vs H^-1 g: max |dz| = {e_unc:.2e} rad")
    assert e_unc < 1e-8
    # active constraints: large offsets; compare with OSQP (cold start = worst case for fixed iterations)
    nc = 60
    x0c = np.c_[rng.uniform(-2.0, 2.0, nc), rng.normal(0, 0.05, nc), rng.normal(0, 0.05, nc)]
    usc = rng.normal(0, 0.01, nc)
    lo, hi = mpc.bounds(x0c, usc)
    zr = np.array([_qp_reference(mpc, x0c[i], usc[i]) for i in range(nc)])
    sc = mpc.Dsc
    for n_it in (mpc.n_iter, 100, 300):
        z_f, _, act = mpc.solve(x0c, usc, n_iter=n_it)
        d0 = np.abs(z_f[:, 0] - zr[:, 0])
        gz = z_f @ mpc.Gs.T
        vi = np.clip(np.maximum(lo - gz, gz - hi) / sc, 0, None).max()
        print(f"  active constraints ({act.mean():.0%} of {nc} states with |d0|<=2 m), {n_it:3d} FISTA it, COLD start: "
              f"|du0 - du0_osqp| median {math.degrees(np.median(d0)):.4f} / max {math.degrees(d0.max()):.4f} deg, "
              f"max violation {math.degrees(vi):.4f} deg")

    # ------------------------------------------------- 2. linearised loop stability
    print("\n[2] linearised closed loop (simulator Euler plant + steering lag), spectral radius per step:")
    rho_e = linear_spectral_radius(ESOSMC())
    rho_m = linear_spectral_radius(OffsetFreeMPC())
    print(f"  ESOSMC (inside boundary layer)          rho = {rho_e:.5f}  (time const {-veh['dt'] / math.log(rho_e):.2f} s)")
    print(f"  OffsetFreeMPC (constraints inactive)    rho = {rho_m:.5f}  (time const {-veh['dt'] / math.log(rho_m):.2f} s)")
    assert rho_e < 1 and rho_m < 1

    # ------------------------------------------- 3. constant side slope / large step
    specs = [("lqr", lambda: "lqr", lambda: BuiltinReplica("lqr")),
             ("lqr_i", lambda: "lqr_i", lambda: BuiltinReplica("lqr_i")),
             ("esosmc", lambda: make("esosmc"), None),
             ("offset_free_mpc", lambda: make("offset_free_mpc"), None),
             ("esosmc/aggr", lambda: make("esosmc", "aggressive"), None),
             ("mpc/aggr", lambda: make("offset_free_mpc", "aggressive"), None)]
    beta = 0.35 * 0.6 * math.tan(math.radians(5))
    print(f"\n[3] core.simulate on a synthetic constant 5 deg side slope, k_s=0.6 (side slip {beta:.4f} rad), "
          f"measurement biases off (full roll compensation, no RTK/mount error), 400 m pass, 10 runs:")
    print(f"  {'ctrl':16s} {'ss offset mm':>12s} {'ss sd mm':>8s} | 1.5 m step: {'overshoot m':>11s} {'t(<5cm) s':>9s} "
          f"{'max|d| m':>8s} {'rate-lim %':>10s} {'FISTA %':>7s}")
    ss = {}
    for name, fac, rep in specs:
        s, D = slope_step_test(fac())
        tail = D[:, s >= 200]
        ss[name] = abs(tail.mean())
        c2 = rep() if rep else fac()
        if isinstance(c2, OffsetFreeMPC):
            c2.audit = 10
        rec = _Recorder(c2)
        s2, D2 = slope_step_test(rec, mount=1.5, slope_deg=0.0)
        e2 = D2 + 1.5  # the controller drives d + 1.5 to zero: d -> -1.5 m (starts at e2 = +1.5)
        over = max(0.0, float(-e2.min()))
        late = np.nonzero(np.any(np.abs(e2) > 0.05, axis=0))[0]
        settle = s2[late.max()] / veh["v"] if len(late) else 0.0
        st = rec.stats()
        fr = c2.n_iter_vehicles / max(c2.n_solves, 1) if isinstance(c2, OffsetFreeMPC) else float("nan")
        stable = bool(np.all(np.isfinite(D2)) and np.abs(e2[:, s2 >= 200]).max() < 0.1)
        if rep is None:
            assert stable, f"{name} unstable on the 1.5 m step"
        note = "" if stable else "  <- NOT settled after 200 m (rate-saturation limit cycle)"
        if isinstance(c2, OffsetFreeMPC) and c2.audit_err:
            ae = np.degrees(np.array(c2.audit_err))
            note += f"  warm-started FISTA vs OSQP on {len(ae)} constrained solves: |du0| median {np.median(ae):.2e}" \
                    f" / max {ae.max():.2e} deg"
        print(f"  {name:16s} {1e3 * ss[name]:12.2f} {1e3 * tail.std():8.2f} | {'':11s} {over:11.3f} {settle:9.1f} "
              f"{np.abs(D2).max():8.3f} {100 * st['frac_rate_lim']:10.2f} {100 * fr:7.2f}{note}")
    for name in ("esosmc", "offset_free_mpc", "esosmc/aggr", "mpc/aggr"):
        assert ss[name] <= ss["lqr"], f"{name}: steady-state slope offset worse than lqr"

    # ------------------------------------------------------------- 4. real fields
    Fs = core.load_fields("paddy", w=w)
    rank = []
    for F in Fs:
        ys = core.plan(F, w, 0.0, lambda f, y: 0.0)
        rank.append((np.mean([core.pass_feature(F, y) for y in ys]), F))
    rank.sort(key=lambda r: -r[0])
    print(f"\n[4] real hilly paddy fields (the 2 with the largest mean side slope of {len(Fs)}), nominal plan "
          f"(lam=0), {n_runs} runs, common random numbers (seed {seed}).")
    print("    e = true field-frame lateral offset on the main-area grid; |bias| = mean |per-pass mean offset|;"
          " rate = steering-rate RMS")
    for s_mean, F in rank[:2]:
        ys = core.plan(F, w, 0.0, lambda f, y: 0.0)
        print(f"\n  field {F.fid}: {len(ys)} passes, main area {F.M.area:.0f} m2, mean slope {F.z_mean_slope:.2f} deg, "
              f"mean side slope {math.degrees(math.atan(s_mean)):.2f} deg  (batch {n_runs * len(ys)} vehicles)")
        print(f"  {'ctrl':16s} {'RMS|e| mm':>9s} {'p99|e| mm':>9s} {'|bias| mm':>9s} {'P(no miss)':>10s} "
              f"{'E[miss]':>8s} {'rate deg/s':>10s} {'rate-lim %':>10s} {'sim s':>6s}  notes")
        for name, fac, rep in specs:
            c = rep() if rep else fac()
            rec = _Recorder(c)
            r = _run(F, ys, rec, n_runs, seed, w)
            st = rec.stats()
            rt = _run(F, ys, fac(), n_runs, seed, w)["runtime"]  # unwrapped timing (string for built-ins)
            note = ""
            if isinstance(c, OffsetFreeMPC):
                note = f"FISTA on {100 * c.n_iter_vehicles / max(c.n_solves, 1):.3f}% of solves, " \
                       f"QP time {c.solve_time:.2f} s"
            assert r["p99"] < 0.5 and np.isfinite(r["rms"]), f"{name}: lateral error blow-up"
            print(f"  {name:16s} {1e3 * r['rms']:9.1f} {1e3 * r['p99']:9.1f} {1e3 * r['bias']:9.1f} "
                  f"{r['p_nomiss']:10.2f} {r['e_miss']:8.5f} {st['rate_rms_deg']:10.2f} "
                  f"{100 * st['frac_rate_lim']:10.2f} {rt:6.2f}  {note}")

    # ------------------------------------------------------- 5. batch throughput
    print("\n[5] command() throughput for a batch of 10,000 vehicles (100 x 100), 200 steps of a random walk:")
    Rb, Kb = 100, 100
    for name in ("esosmc", "offset_free_mpc"):
        c = make(name)
        c.reset(Rb, Kb, veh, None)
        rng = np.random.default_rng(1)
        meas = rng.normal(0, 0.03, (Rb, Kb))
        psi = rng.normal(0, 0.005, (Rb, Kb))
        dl = np.zeros((Rb, Kb))
        t0 = time.perf_counter()
        for _ in range(200):
            u = c.command(meas, psi, dl, veh["dt"])
            dl = dl + np.clip((u - dl) / veh["tau"] * veh["dt"], -veh["rate_max"] * veh["dt"], veh["rate_max"] * veh["dt"])
            meas = meas + rng.normal(0, 0.002, (Rb, Kb))
            psi = psi + rng.normal(0, 0.0005, (Rb, Kb))
        ms = 1e3 * (time.perf_counter() - t0) / 200
        print(f"  {name:16s} {ms:6.2f} ms per simulator step")
    c = OffsetFreeMPC(exact_check=False)
    c.reset(Rb, Kb, veh, None)
    t0 = time.perf_counter()
    for _ in range(20):
        c.command(meas, psi, dl, veh["dt"])
    ms = 1e3 * (time.perf_counter() - t0) / 20
    print(f"  {'mpc, FISTA on all':16s} {ms:6.2f} ms per simulator step (worst case: every vehicle constrained, "
          f"{c.n_iter} iterations every {c.hold} steps)")
    print(f"\nselftest passed in {time.time() - t_all:.1f} s")

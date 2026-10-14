"""End-to-end check of the five-layer theory (docs/theory_evt.md). Each layer uses ONLY the quantities
computed by the previous layer (no re-estimation from simulated runs); simulation is used only to
check each layer's prediction.

  L1 Lyapunov      controller/actuator/noise parameters + condition C -> per-metre covariance tracks
                   (variance, slope variance, cross-covariance, incl. the line-acquisition transient) and
                   the mean path m_k(x|C) = noise-free closed-loop response
  L2 Kac-Rice      L1 -> upper bound mu_bar_j(t|C) for every interior pair
  L3 Chen-Stein    L2 -> P(U <= t | C) ~ exp(-sum_j mu_bar_j)
  L4 mixed Poisson L3 integrated over the condition distribution -> F_pi(t), 0.9-quantile (the erosion
                   CE would calibrate), extremal index theta, and the deployed coverage after a plan change
  L5 Gumbel        (separate flag) L4 on fields of different size -> sqrt(2 log N) scale law

    python3 scripts/check_evt.py --regime R1
"""
import argparse
import math
import os
import sys
import time

import numpy as np
from scipy.stats import norm

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "experiments"))
import core  # noqa: E402
import exp_system as E  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--regime", default="R1")
ap.add_argument("--field", type=int, default=50)
ap.add_argument("--n-frozen", type=int, default=2000)
ap.add_argument("--n-cond", type=int, default=300)
ap.add_argument("--n-sim", type=int, default=1500)
ap.add_argument("--layers", default="1234")
ap.add_argument("--cond-index", default="0", help="frozen condition: run index, or 'maxrough' / 'minrough'")
ap.add_argument("--const-l1", action="store_true", help="time-invariant Lyapunov L1 (default: time-varying quasi-linearisation)")
args = ap.parse_args()

rname = [k for k in E.REGIMES if k.startswith(args.regime)][0]
reg = E.REGIMES[rname]
w = reg["w"]
V = core.VEH
v, l, tau, dt = V["v"], V["l_wb"], V["tau"], V["dt"]
REC = max(1, int(round(1.0 / (v * dt))))  # simulator steps per 1 m record
TH_OU, SIG_PSI = 0.5, math.radians(0.15)
INIT_D, INIT_PSI = 0.03, math.radians(0.5)


class ZeroRNG:
    """Noise-free closed loop: every Gaussian draw of core.simulate is replaced by its mean."""

    def normal(self, loc=0.0, scale=1.0, size=None):
        return np.zeros(size) + loc

    def standard_normal(self, size=None):
        return np.zeros(size)


# =============================================================== L1: Lyapunov covariance tracks
_, KQ = core._lqr_gains(v, l, dt)


def step(xs, w_ou, w_psi, rough=1.0):
    d, psi, delta, integ, ou = xs
    ou = ou - TH_OU * ou * dt + rough * math.sqrt(2 * TH_OU * dt) * w_ou
    psim = psi + SIG_PSI * w_psi
    integ = integ + d * dt
    u = -(KQ[0] * d + KQ[1] * psim + KQ[2] * delta + KQ[3] * integ)
    delta = delta + (u - delta) / tau * dt
    d = d + v * (psi + ou) * dt
    psi = psi + v * delta / l * dt
    return np.array([d, psi, delta, integ, ou])


A = np.column_stack([step(e, 0, 0) for e in np.eye(5)])
B_ou = step(np.zeros(5), 1, 0)[:, None]
B_psi = step(np.zeros(5), 0, 1)[:, None]


def covariance_tracks(n_m):
    """Per-metre tracks for the three noise sources separately (linearity: total = init + rough^2 ou + psi).
    Returns dict of arrays (3, n_m) for var d, var slope (psi + ou), cov(d, slope)."""
    out = {k: np.zeros((3, n_m)) for k in ("vd", "vs", "cds", "c1", "c2")}
    AR = np.linalg.matrix_power(A, REC)
    for src in range(3):
        P = np.diag([INIT_D ** 2, INIT_PSI ** 2, 0, 0, 0]) if src == 0 else np.zeros((5, 5))
        Q = (B_ou @ B_ou.T) if src == 1 else (B_psi @ B_psi.T) if src == 2 else np.zeros((5, 5))
        for m in range(n_m):
            for _ in range(REC):
                P = A @ P @ A.T + Q
            out["vd"][src, m] = P[0, 0]
            out["vs"][src, m] = P[1, 1] + 2 * P[1, 4] + P[4, 4]
            out["cds"][src, m] = P[0, 1] + P[0, 4]
            out["c1"][src, m] = (AR @ P)[0, 0]  # Cov(d at m + 1 metre, d at m)
            out["c2"][src, m] = (AR @ AR @ P)[0, 0]  # Cov(d at m + 2 metres, d at m)
    return out


def tracks_for(rough, base):
    c = np.array([1.0, rough ** 2, 1.0])
    return {k: (c[:, None] * v_).sum(axis=0) for k, v_ in base.items()}


# =============================================================== L1': time-varying quasi-linearisation
H_ANT = V["h_ant"]
R_MAX, D_MAX = V["rate_max"], V["delta_max"]


def _ncdf_gain(lim, mu, sd):
    """Random-input describing function of a symmetric limiter |x| <= lim for x ~ N(mu, sd^2)."""
    sd = np.maximum(sd, 1e-9)
    return norm.cdf((lim - mu) / sd) - norm.cdf((-lim - mu) / sd)


def tv_tracks(trace, cond, n_m, idx=None):
    """Covariance tracks of every (condition, pass) along its noise-free (mean) trajectory.
    trace: core.simulate(..., trace=...) of the noise-free run, arrays (nrec, nc, K); cond: its Condition.
    Per 1 m segment the loop is linearised at the mean state (Jacobians of sin, tan and of the terrain
    gradient in the lateral position) and the steering limiter / rate limiter are replaced by their
    random-input describing functions, whose input s.d. is taken from the current covariance (Booton
    self-consistency). Returns dict vd, c1, c2 of shape (nc, K, n_m)."""
    nrec, nc, K = trace["rate"].shape
    n_m = min(n_m, nrec - 2)
    N = nc * K
    rs = lambda a: np.asarray(a, float).reshape(N)  # noqa: E731
    col = lambda a: np.repeat(np.asarray(a, float), K)  # noqa: E731  per-condition -> per (cond, pass)
    k_s, comp, rough = col(cond.k_s), col(cond.comp), col(cond.rough)
    P = np.zeros((N, 5, 5))
    P[:, 0, 0], P[:, 1, 1] = INIT_D ** 2, INIT_PSI ** 2
    out = {k: np.zeros((N, n_m)) for k in ("vd", "c1", "c2")}
    prevM = None
    eye5, eye2 = np.broadcast_to(np.eye(5), (N, 5, 5)), np.broadcast_to(np.eye(2), (N, 2, 2))
    for m in range(n_m + 1):
        mu_r, mu_u = rs(trace["rate"][m]), rs(trace["ucmd"][m])
        ang, dl = rs(trace["psi"][m]) + rs(trace["beta"][m]), rs(trace["delta"][m])
        dg, gv = rs(trace["dg"][m]), rs(trace["g_v"][m])
        c_beta = -0.35 * k_s * dg                                   # d beta / d d   (terrain feedback)
        kap = -H_ANT * (1 - comp) * (1 + gv ** 2) ** -1.5 * dg      # d meas / d d   (roll-antenna term)
        cos_a, sec2 = np.cos(ang), 1.0 / np.cos(dl) ** 2
        # describing-function gains from the current covariance (u and rate are linear in the state)
        au = -np.stack([KQ[0] * (1 + kap) + KQ[3] * (1 + kap) * dt, np.full(N, KQ[1]), np.full(N, KQ[2]),
                        np.full(N, KQ[3]), np.zeros(N)], axis=1)
        var_u = np.einsum("ni,nij,nj->n", au, P, au) + (KQ[1] * SIG_PSI) ** 2
        Nu = _ncdf_gain(D_MAX, mu_u, np.sqrt(var_u))
        ar = (Nu[:, None] * au - np.eye(5)[2][None, :]) / tau
        var_r = np.einsum("ni,nij,nj->n", ar, P, ar) + (Nu * KQ[1] * SIG_PSI / tau) ** 2
        Nr = _ncdf_gain(R_MAX, mu_r, np.sqrt(var_r))

        def lin_step(x, wv):  # x (N,5,c), wv (N,2,c): one simulator step of the quasi-linear deviation system
            d, psi, de, I, ou = (x[:, i] for i in range(5))
            ou = ou - TH_OU * ou * dt + rough[:, None] * math.sqrt(2 * TH_OU * dt) * wv[:, 0]
            beta = ou + c_beta[:, None] * d
            meas = (1 + kap[:, None]) * d
            I = I + meas * dt
            u = -(KQ[0] * meas + KQ[1] * (psi + SIG_PSI * wv[:, 1]) + KQ[2] * de + KQ[3] * I)
            de = de + Nr[:, None] * (Nu[:, None] * u - de) / tau * dt
            d = d + v * cos_a[:, None] * (psi + beta) * dt
            psi = psi + v * sec2[:, None] / l * de * dt
            return np.stack([d, psi, de, I, ou], axis=1)

        A = lin_step(eye5, np.zeros((N, 2, 5)))
        B = lin_step(np.zeros((N, 5, 2)), eye2)
        Phi = eye5.copy()
        P0 = P.copy()
        for _ in range(REC):
            P = A @ P @ np.transpose(A, (0, 2, 1)) + B @ np.transpose(B, (0, 2, 1))
            Phi = A @ Phi
        if m < n_m:
            out["vd"][:, m] = P0[:, 0, 0]
            M1 = Phi @ P0
            out["c1"][:, m] = M1[:, 0, 0]
            if prevM is not None:
                out["c2"][:, m - 1] = (Phi @ prevM)[:, 0, 0]
            prevM = M1
    out["c2"][:, n_m - 1] = out["c1"][:, n_m - 1]
    return {k: v_.reshape(nc, K, n_m) for k, v_ in out.items()}


# =============================================================== geometry helpers
def setup(F, lam):
    ys = core.plan(F, w, lam, E.UNIT)
    minx, _, maxx, _ = F.M.bounds
    xg = np.arange(math.ceil(minx), math.floor(maxx) + 1, 1.0)
    ch = [core._chord_x(F.M, x) for x in xg]
    chords = [F.chord(F.P, y) for y in ys]
    x0 = np.array([c[0] for c in chords])
    x1 = np.array([c[1] for c in chords])
    sgn = np.where(np.arange(len(ys)) % 2 == 0, 1.0, -1.0)
    # observation operator: core.pass_offsets interpolates the 1 m records linearly onto the integer
    # x-grid; the interpolation fraction is constant along a pass: frac(-x0) forward, frac(x1) backward
    fr = np.where(sgn > 0, np.mod(-x0, 1.0), np.mod(x1, 1.0))
    return ys, xg, ch, x0, x1, sgn, fr


def offsets(F, ys, X, D, xg):
    return np.stack([core.pass_offsets(X[k], D[k], xg) for k in range(len(ys))])  # (K, R, nx)


def pair_masks(ys, xg, ch, off_mean):
    """Valid sections of interior pair j (passes j-1, j): both passes present, nominal mid inside the chord."""
    K = len(ys)
    masks = []
    for j in range(1, K):
        mid = 0.5 * (ys[j - 1] + ys[j])
        ok = np.array([c is not None and c[0] <= mid <= c[1] for c in ch])
        ok &= np.isfinite(off_mean[j - 1]) & np.isfinite(off_mean[j])
        masks.append(ok)
    return masks


def dist_along(xg, k, x0, x1, sgn):
    """Distance travelled on pass k when it reaches field x (metres)."""
    return np.where(sgn[k] > 0, xg - x0[k], x1[k] - xg)


# =============================================================== L2: Kac-Rice bound
def rice_pair(t, mj, sig, sigp, r):
    """Kac-Rice upper bound on P(sup_x Z > t) for a Gaussian process on a 1 m grid (Riemann sum)."""
    if len(mj) == 0:
        return 0.0
    u = (t - mj) / sig
    mp = np.gradient(mj) if len(mj) > 1 else np.zeros_like(mj)
    mt = mp + r / sig ** 2 * (t - mj)
    st = np.sqrt(np.maximum(sigp ** 2 - r ** 2 / sig ** 2, 1e-12))
    a = mt / st
    psi_ = norm.pdf(a) + a * norm.cdf(a)
    return float(norm.sf(u[0]) + np.sum(st / sig * norm.pdf(u) * psi_))


_Y = np.r_[0.0, np.geomspace(1e-5, 9.0, 120)]  # integration nodes below the level (standardised units)


def rice_pair_discrete(t, mj, sig, c1z):
    """Discrete Kac-Rice bound for the sup over the 1 m grid (exactly how a miss is decided):
    P(max_i Z_i > t) <= P(Z_0 > t) + sum_i P(Z_i <= t < Z_{i+1}); each term is a bivariate-normal integral
    over Z_i <= t of P(Z_{i+1} > t | Z_i) (c1z: Cov(Z_i, Z_{i+1}) from L1). A gap in the grid restarts."""
    if len(mj) == 0:
        return 0.0
    u0 = (t - mj) / sig
    tot = float(norm.sf(u0[0]))
    if len(mj) > 1:
        rho = np.clip(c1z / (sig[:-1] * sig[1:]), -0.999999, 0.999999)
        cm = lambda u: mj[1:] + rho * sig[1:] * u  # noqa: E731  conditional mean of Z_{i+1} given Z_i = m + sig u
        cs = sig[1:] * np.sqrt(1 - rho ** 2)
        U = u0[:-1, None] - _Y[None, :]
        f = norm.pdf(U) * norm.sf((t - cm(U.T).T) / cs[:, None])
        tot += float(np.sum(np.trapezoid(f, _Y, axis=1)) + np.sum(norm.pdf(U[:, -1]) * 0))  # tail beyond 9 sd ~ 0
    return tot


def pair_params(j, mean_off, tr, xg, x0, x1, sgn, mask, fr=None):
    """Gap process Z_j = (e_j - e_{j-1}) / 2 on the valid sections: mean, sd, slope sd, cross-cov (from L1)."""
    a, b = j - 1, j
    idx = np.nonzero(mask)[0]
    nmax = tr["vd"].shape[-1] - 1
    sa = np.clip(dist_along(xg, a, x0, x1, sgn)[idx].astype(int), 0, nmax)
    sb = np.clip(dist_along(xg, b, x0, x1, sgn)[idx].astype(int), 0, nmax)
    mj = 0.5 * (mean_off[b][idx] - mean_off[a][idx])

    def obs(sidx, f, k=None):  # variance and lag-1 covariance of the interpolated (observed) offset of one pass
        if tr["vd"].ndim == 2:  # time-varying (per-pass) tracks
            v0, c1, c2 = tr["vd"][k][sidx], tr["c1"][k][sidx], tr["c2"][k][sidx]
        else:
            v0, c1, c2 = tr["vd"][sidx], tr["c1"][sidx], tr["c2"][sidx]
        var = (1 - f) ** 2 * v0 + f ** 2 * v0 + 2 * f * (1 - f) * c1
        lag1 = ((1 - f) ** 2 + f ** 2) * c1 + f * (1 - f) * (c2 + v0)
        return var, lag1
    fa = 0.0 if fr is None else fr[a]
    fb = 0.0 if fr is None else fr[b]
    va, la = obs(sa, fa, a)
    vb, lb = obs(sb, fb, b)
    sig = 0.5 * np.sqrt(va + vb)
    if tr["vd"].ndim == 2:  # continuous-Rice quantities are not tracked in the time-varying model
        sigp, r = np.full_like(sig, np.nan), np.zeros_like(sig)
    else:
        sigp = 0.5 * np.sqrt(tr["vs"][sa] + tr["vs"][sb])
        r = 0.25 * (sgn[b] * tr["cds"][sb] - sgn[a] * tr["cds"][sa])
    # Cov(Z_i, Z_{i+1}) for consecutive grid points: each pass moves +1 m (forward) or -1 m (backward) in travel
    c1z = 0.25 * (la + lb)[:-1]
    return mj, sig, sigp, r, c1z


def predict_M(t, mean_off, tr, geo, masks):
    ys, xg, ch, x0, x1, sgn, fr = geo
    out = []
    for j in range(1, len(ys)):
        mj, sig, sigp, r, c1z = pair_params(j, mean_off, tr, xg, x0, x1, sgn, masks[j - 1], fr)
        out.append(rice_pair_discrete(t, mj, sig, c1z) if DISCRETE else rice_pair(t, mj, sig, sigp, r))
    return np.array(out)


DISCRETE = True
TIME_VARYING = not args.const_l1


def interior_U(F, ys, X, D, lam):
    T = core.exact_pair_scores(F, ys, X, D, w, lam)
    return T[:, 1:-1], T


# =============================================================== run
Fd = core.load_fields(reg["kind"], w=w, seed=0)
F = Fd[args.field]
lam = {"R1": 0.11, "R2": 0.15, "R3": 0.40}[args.regime]
geo = setup(F, lam)
ys, xg, ch, x0, x1, sgn, fr = geo
K = len(ys)
n_m = int(np.max(x1 - x0)) + 2
t0 = time.time()
base = covariance_tracks(n_m)
print(f"{rname}  field {F.fid}  K = {K} passes  lam = {lam} m   closed-loop spectral radius "
      f"{max(abs(np.linalg.eigvals(A))):.4f}   (L1 tracks {time.time() - t0:.1f}s)")


def frozen(n, i0=0, seed=5):
    c = E.make_cond(np.random.default_rng(seed), max(n, i0 + 1), reg)
    for k_, v_ in list(vars(c).items()):
        if isinstance(v_, np.ndarray) and v_.shape[:1] == (len(c.k_s),):
            setattr(c, k_, np.repeat(v_[i0:i0 + 1], n, axis=0))
    return c


if any(c in args.layers for c in "123"):
    if args.cond_index in ("maxrough", "minrough"):
        c_ = E.make_cond(np.random.default_rng(5), 200, reg)
        i0 = int(np.argmax(c_.rough) if args.cond_index == "maxrough" else np.argmin(c_.rough))
    else:
        i0 = int(args.cond_index)
    cond = frozen(args.n_frozen, i0)
    rough = float(cond.rough[0])
    tr = tracks_for(rough, base)
    import ceplus
    Xz, Dz = core.simulate(F, ys, ceplus.subset_cond(cond, np.array([0])), ZeroRNG())  # same C as the runs
    mean_off = offsets(F, ys, Xz, Dz, xg)[:, 0, :]  # L1 mean path (noise-free response)
    X, D = core.simulate(F, ys, cond, np.random.default_rng(11))
    off = offsets(F, ys, X, D, xg)
    print(f"\nfrozen condition: k_s {cond.k_s[0]:.2f}  rough {rough:.4f} rad  comp {cond.comp[0]:.2f}  "
          f"mount {cond.mount[0]*100:+.1f} cm   ({args.n_frozen} runs)")
    # ---- L1 check
    print("\n[L1] Lyapunov tracks vs sample (field-frame offsets, all passes pooled by distance travelled)")
    print("     dist[m]   sd_pred[cm]  sd_sample[cm]   slope-sd_pred  slope-sd_sample")
    for dm in (2, 5, 10, 20, 40, 80):
        pv, sv, pslope, sslope = [], [], [], []
        for k in range(K):
            s_k = dist_along(xg, k, x0, x1, sgn)
            i = np.nonzero((np.abs(s_k - dm) < 0.5) & np.isfinite(off[k]).all(axis=0))[0]
            if len(i) and i[0] + 1 < off.shape[2] and np.isfinite(off[k][:, i[0] + 1]).all():
                sv.append(off[k][:, i[0]].std())
                j2 = i[0] + (1 if sgn[k] > 0 else -1)
                sslope.append(np.std(off[k][:, j2] - off[k][:, i[0]]))
        if sv and dm < len(tr["vd"]):
            print(f"     {dm:5d}     {np.sqrt(tr['vd'][dm])*100:6.2f}       {np.mean(sv)*100:6.2f}         "
                  f"{np.sqrt(tr['vs'][dm]):.4f}         {np.mean(sslope):.4f}")
    mres = np.nanmean(off, axis=1) - mean_off
    print(f"     mean path: RMS(sample mean - noise-free response) = {np.sqrt(np.nanmean(mres**2))*100:.2f} cm "
          f"(steady-state gap sd {0.5*np.sqrt(2*tr['vd'][-1])*100:.2f} cm)")
    # ---- L2 / L3 checks
    Ti, Tall = interior_U(F, ys, X, D, lam)
    Ui = Ti.max(axis=1)
    masks = pair_masks(ys, xg, ch, mean_off)
    print(f"\n[L2] Kac-Rice (from L1 only) vs empirical pair exceedances;  [L3] exp(-M) vs P(U_int <= t | C)")
    print("     t[cm]   sum mu_emp  sum mu_Rice   P_emp   exp(-M_Rice)  prod(1-mu_Rice)  prod(1-mu_emp)  "
          "CS bound 5mu_max  boundary-argmax share")
    bshare = np.mean(Tall.argmax(axis=1) % K == 0)
    for q in (0.5, 0.8, 0.9, 0.95, 0.99):
        t = float(np.quantile(Ui, q))
        mu_e = (Ti > t).mean(axis=0)
        mu_r = predict_M(t, mean_off, tr, geo, masks)
        print(f"     {t*100:5.2f}   {mu_e.sum():.4f}      {mu_r.sum():.4f}      {np.mean(Ui <= t):.4f}  "
              f"{math.exp(-mu_r.sum()):.4f}        {np.prod(1 - np.clip(mu_r, 0, 1)):.4f}           "
              f"{np.prod(1 - mu_e):.4f}          {5*mu_e.max():.4f}            {bshare:.3f}")

# ------------------------------------------------ L4 machinery (also used by L5)
rngc = np.random.default_rng(21)

def predict_F(Fx, lam_x, tgrid, ncond):
    g = setup(Fx, lam_x)
    cond_c = E.make_cond(rngc, ncond, reg)
    trc = {}
    Xz, Dz = core.simulate(Fx, g[0], cond_c, ZeroRNG(), trace=trc)
    TV = tv_tracks(trc, cond_c, int(np.max(g[4] - g[3])) + 2) if TIME_VARYING else None
    mo = offsets(Fx, g[0], Xz, Dz, g[1])  # (K, ncond, nx) mean paths per condition
    mk = pair_masks(g[0], g[1], g[2], np.nanmean(mo, axis=1))
    Ms = np.zeros((ncond, len(tgrid)))
    Pr = np.zeros((ncond, len(tgrid)))
    for i in range(ncond):
        tr_i = {k: v_[i] for k, v_ in TV.items()} if TIME_VARYING else tracks_for(float(cond_c.rough[i]), base)
        for a, t in enumerate(tgrid):
            mu = predict_M(t, mo[:, i, :], tr_i, g, mk)
            Ms[i, a] = mu.sum()
            Pr[i, a] = np.prod(1 - np.clip(mu, 0, 1))  # layer 3 in product form (normal-comparison lemma)
    return Pr.mean(axis=0), Ms, g


def simulate_U(Fx, lam_x, n, seed):
    g = setup(Fx, lam_x)
    rng = np.random.default_rng(seed)
    c = E.make_cond(rng, n, reg)
    X, D = core.simulate(Fx, g[0], c, rng)
    Ti, Tall = interior_U(Fx, g[0], X, D, lam_x)
    miss = core.evaluate(Fx, g[0], X, D, w)
    return Ti, Tall, miss



if "4" in args.layers:
    print(f"\n[L4] mixed Poisson over {args.n_cond} sampled conditions (prediction uses L1-L3 only) "
          f"vs {args.n_sim} simulated runs with random conditions")
    tg = time.time()
    Ti, Tall, miss = simulate_U(F, lam, args.n_sim, 31)
    Ui = Ti.max(axis=1)
    tgrid = np.quantile(Ui, [0.5, 0.7, 0.8, 0.85, 0.9, 0.93, 0.95, 0.97])
    Fp, Ms, _ = predict_F(F, lam, tgrid, args.n_cond)
    print("     t[cm]   F_pred   F_sim    theta_pred  theta_sim")
    for a, t in enumerate(tgrid):
        W = (Ti > t).sum(axis=1).mean()
        th_p = np.mean(1 - np.exp(-Ms[:, a])) / np.mean(Ms[:, a])
        print(f"     {t*100:5.2f}   {Fp[a]:.4f}   {np.mean(Ui <= t):.4f}   {th_p:.3f}       "
              f"{(1 - np.mean(Ui <= t)) / W if W > 0 else float('nan'):.3f}")
    # 0.9-quantile of the needed erosion: prediction (interpolated) vs simulation
    q_pred = float(np.interp(0.9, Fp, tgrid))
    se = np.exp(-Ms).std(axis=0) / math.sqrt(args.n_cond)  # (s.e. of the exp(-M) form; product form similar)  # Monte Carlo error of the condition integral
    print("     Monte Carlo s.e. of F_pred (condition integral): " + ", ".join(f"{x:.3f}" for x in se))
    print(f"     0.9-quantile of the interior needed erosion: predicted {q_pred*100:.2f} cm, simulated "
          f"{np.quantile(Ui, 0.9)*100:.2f} cm   (L4 {time.time() - tg:.0f}s)")
    # decision dependence: reference plan at 1.25 lam, deployed plan at lam
    lam0 = 1.25 * lam
    Ti0, _, _ = simulate_U(F, lam0, args.n_sim, 41)
    U0 = Ti0.max(axis=1)
    F0p, _, g0 = predict_F(F, lam0, np.array([lam]), args.n_cond)
    F1p, _, _ = predict_F(F, lam, np.array([lam]), args.n_cond)
    print(f"     plan change lam0 = {lam0:.3f} (K0 = {len(g0[0])}) -> lam1 = {lam:.3f} (K1 = {K}), threshold t = lam1:")
    print(f"       reference coverage F_pi0(t): predicted {F0p[0]:.4f}  simulated {np.mean(U0 <= lam):.4f}")
    print(f"       deployed  coverage F_pi1(t): predicted {F1p[0]:.4f}  simulated {np.mean(Ui <= lam):.4f}"
          f"   (exact no-miss rate incl. boundaries: {np.mean(miss == 0):.4f})")

if "5" in args.layers:
    print(f"\n[L5] scale law across fields: predicted (L1-L4) and simulated 0.9-quantile vs sqrt(2 log N)")
    tr_med = tracks_for(float(np.median(E.make_cond(np.random.default_rng(3), 2000, reg).rough)), base)
    s_ss = 0.5 * math.sqrt(2 * tr_med["vd"][-1])
    sp_ss = 0.5 * math.sqrt(2 * tr_med["vs"][-1])
    rows = []
    for fi in range(args.field, args.field + 8):
        Fx = Fd[fi]
        try:
            Ti5, _, _ = simulate_U(Fx, lam, args.n_sim, 51)
        except ValueError:
            continue
        U5 = Ti5.max(axis=1)
        tg5 = np.quantile(U5, [0.8, 0.85, 0.9, 0.93, 0.96])
        Fp5, _, g5 = predict_F(Fx, lam, tg5, args.n_cond)
        mk5 = pair_masks(g5[0], g5[1], g5[2], np.zeros((len(g5[0]), len(g5[1]))))
        Lsum = float(sum(m.sum() for m in mk5))
        N = Lsum * sp_ss / (2 * math.pi * s_ss)
        qp = float(np.interp(0.9, Fp5, tg5))
        qs = float(np.quantile(U5, 0.9))
        rows.append((Fx.fid, len(g5[0]), Lsum, N, math.sqrt(2 * math.log(N)), qp, qs))
        print(f"     field {Fx.fid:4d}  K {len(g5[0]):3d}  sum L {Lsum:7.0f} m  N {N:7.1f}  sqrt(2logN) {math.sqrt(2*math.log(N)):.3f}"
              f"   q0.9 predicted {qp*100:6.2f} cm   simulated {qs*100:6.2f} cm", flush=True)
    r = np.array([x[4:] for x in rows])
    for nm, col in (("predicted", 1), ("simulated", 2)):
        c = np.polyfit(r[:, 0], r[:, col], 1)
        res = r[:, col] - np.polyval(c, r[:, 0])
        R2 = 1 - res.var() / r[:, col].var()
        print(f"     {nm}: q0.9 = {c[1]*100:.2f} cm + {c[0]*100:.2f} cm * sqrt(2 log N)   R^2 = {R2:.3f}   "
              f"(Gumbel scale s = {s_ss*100:.2f} cm at the median condition)")

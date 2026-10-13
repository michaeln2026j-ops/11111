"""Core library: fields, terrain, batched execution simulator, coverage planning
and evaluation, conformal-erosion calibration and baselines.

Frames. Each field is rotated so that the real operating direction (mode of
recorded harvester headings) is the +x (along-track) axis; y is lateral.
Passes are straight lines y = y_k driven alternately in +x / -x.

Execution model (per pass, vehicle frame, batched over runs x passes):
  d'   = v sin(psi + beta) + drift                 lateral offset of the vehicle
  psi' = v tan(delta) / l_wb + w_r                 heading error
  delta' = (delta_cmd - delta) / tau, |delta|<=delta_max, rate-limited
  beta = k_s * sideslope + OU roughness            terrain-induced side slip
Measured offset (what the autosteer controls) is the antenna position:
  d_meas = d - h_ant * roll * (1 - c_comp) + sgn * eps_y(T_k + t) + b_mount
where eps_y is the EARTH-FIXED real GNSS positioning error (N/E series projected
on the field lateral axis) sampled at the true time of each pass (passes driven
sequentially with headland turns), sgn = +1/-1 for up/down-field passes, and
b_mount a per-run lateral mounting calibration error in the vehicle frame.
GNSS errors (Condition.gnss): each run draws a random real station-pair-day and
start time from the NOAA CORS bank of the chosen receiver grade (rtk_fix,
rtk_float, dgps, spp; see data_cors.py and gnss_bank), or the legacy single
vehicle RTK record (gnss="i2nav").
so on side slopes an uncompensated antenna drags the vehicle uphill, with the
sign flipping between up- and down-field passes (the classic slope offset).
"""
import json
import math
import os

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Polygon

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")


# ----------------------------------------------------------------------------- fields
class Field:
    """Real field: convex polygon (rotated to operating frame) + DEM slope map."""

    def __init__(self, fid, meta, headland=None, w=3.0):
        self.fid, self.kind, self.meta = fid, meta["kind"], meta
        poly = Polygon(meta["polygon_enu"])
        # heading is clockwise from north; rotate so heading -> +x
        ang = 90.0 - meta["heading_deg"]
        self.rot = -ang
        self.P = affinity.rotate(poly, self.rot, origin=(0, 0))
        H = headland if headland is not None else 2 * w
        self.H = H
        self.M = self.P.buffer(-H)  # main area, perimeter headland passes excluded
        self._load_dem()

    def _load_dem(self):
        f = os.path.join(DATA, "dem", f"{self.fid}.npz")
        d = np.load(f)
        z, xs, ys = d["z"].astype(float), d["xs"], d["ys"]
        if np.isnan(z).any():
            z = np.where(np.isnan(z), np.nanmean(z), z)
        if ys[0] > ys[-1]:
            ys, z = ys[::-1], z[::-1]
        # gradient in ENU (east=x, north=y)
        gy_n, gx_e = np.gradient(z, ys, xs)
        # resample onto a 1 m grid in the operating frame
        minx, miny, maxx, maxy = self.P.bounds
        self.gx0, self.gy0 = minx - 10, miny - 10
        nx, ny = int(maxx - minx + 21), int(maxy - miny + 21)
        X, Y = np.meshgrid(self.gx0 + np.arange(nx), self.gy0 + np.arange(ny))
        th = math.radians(-self.rot)  # operating frame -> ENU
        E = X * math.cos(th) - Y * math.sin(th)
        N = X * math.sin(th) + Y * math.cos(th)
        ge = _bilinear(gx_e, xs, ys, E, N)
        gn = _bilinear(gy_n, xs, ys, E, N)
        # gradient components in operating frame (x along, y lateral)
        c, s = math.cos(th), math.sin(th)
        self.gx_map = ge * c + gn * s
        self.gy_map = -ge * s + gn * c
        self.z_mean_slope = float(np.degrees(np.arctan(np.hypot(self.gx_map, self.gy_map))).mean())

    def gy(self, x, y):
        i = np.clip(np.rint(y - self.gy0).astype(int), 0, self.gy_map.shape[0] - 1)
        j = np.clip(np.rint(x - self.gx0).astype(int), 0, self.gy_map.shape[1] - 1)
        return self.gy_map[i, j]

    def lateral_range(self):
        minx, miny, maxx, maxy = self.M.bounds
        return miny, maxy

    def chord(self, poly, y):
        minx, _, maxx, _ = poly.bounds
        seg = LineString([(minx - 1, y), (maxx + 1, y)]).intersection(poly)
        if seg.is_empty:
            return None
        xs = [c[0] for c in (seg.coords if seg.geom_type == "LineString" else
                             [p for g in seg.geoms for p in g.coords])]
        return min(xs), max(xs)


def _bilinear(A, xs, ys, X, Y):
    fx = np.clip((X - xs[0]) / (xs[1] - xs[0]), 0, len(xs) - 1.001)
    fy = np.clip((Y - ys[0]) / (ys[1] - ys[0]), 0, len(ys) - 1.001)
    i, j = fy.astype(int), fx.astype(int)
    ty, tx = fy - i, fx - j
    return (A[i, j] * (1 - ty) * (1 - tx) + A[i + 1, j] * ty * (1 - tx)
            + A[i, j + 1] * (1 - ty) * tx + A[i + 1, j + 1] * ty * tx)


def load_fields(kind=None, w=3.0, min_area=4000.0, max_fields=None, seed=0):
    meta = json.load(open(os.path.join(DATA, "fields.json")))
    ids = [int(f[:-4]) for f in os.listdir(os.path.join(DATA, "dem")) if f.endswith(".npz")]
    out = []
    for i in sorted(ids):
        m = meta[i]
        if kind and m["kind"] != kind:
            continue
        if m["area_m2"] < min_area:
            continue
        try:
            F = Field(i, m, w=w)
        except Exception:
            continue
        if F.M.is_empty or F.M.area < 0.4 * m["area_m2"] or F.M.geom_type != "Polygon":
            continue
        out.append(F)
    rng = np.random.default_rng(seed)
    rng.shuffle(out)
    return out[:max_fields] if max_fields else out


# ------------------------------------------------------------------------- RTK noise
_RTK = None
_RTK_NE = None


def rtk_lateral():
    global _RTK
    if _RTK is None:
        d = np.load(os.path.join(DATA, "rtk_error.npz"))
        _RTK = d["lat_err"] - d["lat_err"].mean()
    return _RTK


def rtk_ne():
    """Earth-fixed (north, east) RTK error series in metres, 1 Hz, zero-mean."""
    global _RTK_NE
    if _RTK_NE is None:
        d = np.load(os.path.join(DATA, "rtk_error.npz"))
        _RTK_NE = (d["en"] - d["en"].mean(), d["ee"] - d["ee"].mean())
    return _RTK_NE


GNSS_GRADES = ("rtk_fix", "rtk_float", "dgps", "spp")
_GNSS = {}
SEG_GAP_S = 300.0  # data outages longer than this split a CORS series into separate segments
MIN_SEG_S = 7200.0  # segments shorter than 2 h are not used
CONVERGE_S = 1800.0  # first 30 min after the daily cold start (ambiguity convergence) are dropped


def _hf_residual():
    """High-frequency (< 30 s) part of the 1 Hz vehicle RTK record (i2Nav), (2, n): north, east.
    Winsorised at the 99.5th percentile so that its single 19 cm jump is not replicated."""
    from scipy.ndimage import uniform_filter1d
    en, ee = rtk_ne()
    out = []
    for x in (en, ee):
        hf = x - uniform_filter1d(x, 31, mode="nearest")
        c = np.percentile(np.abs(hf), 99.5)
        out.append(np.clip(hf, -c, c))
    return np.array(out)


def gnss_bank(grade):
    """1 Hz earth-fixed (north, east) error bank of one receiver grade from the NOAA CORS series.

    Every station-pair-day (30 s epochs, data_cors.py), without its first CONVERGE_S after the cold
    start (an operator waits for a fix), is split at outages > SEG_GAP_S; contiguous
    segments of at least MIN_SEG_S are linearly interpolated to 1 Hz and the vehicle-borne
    high-frequency residual of the 1 Hz i2Nav record is added (random circular shift, time reversal
    and sign per 1615 s tile, deterministic seed), since 30 s data carry no sub-30 s content.
    The real per-day biases are kept: a bias common to all passes of an operation cancels in the
    pass-to-pass error (Lemma 1), slowly varying ones do not.
    Returns dict(en, ee float32 concatenated, start, length int arrays per segment, labels)."""
    if grade in _GNSS:
        return _GNSS[grade]
    z = np.load(os.path.join(DATA, "cors_errors.npz"), allow_pickle=True)
    hf = _hf_residual()
    nh = hf.shape[1]
    rg = np.random.default_rng(12345)
    EN, EE, start, length, labels = [], [], [], [], []
    pos = 0
    for s in z[grade]:
        keep = np.asarray(s["t"], float) >= s["t"][0] + CONVERGE_S
        t = np.asarray(s["t"], float)[keep]
        s = {k: (np.asarray(v)[keep] if k in ("en", "ee") else v) for k, v in s.items()}
        cut = np.r_[0, np.nonzero(np.diff(t) > SEG_GAP_S)[0] + 1, len(t)]
        for a, b in zip(cut[:-1], cut[1:]):
            ts = t[a:b]
            if ts[-1] - ts[0] < MIN_SEG_S:
                continue
            tt = np.arange(ts[0], ts[-1] + 1.0)
            n = len(tt)
            tiles = []
            while sum(len(x[0]) for x in tiles) < n:
                h = np.roll(hf, rg.integers(nh), axis=1)
                if rg.random() < 0.5:
                    h = h[:, ::-1]
                tiles.append(h * rg.choice([-1.0, 1.0]))
            h = np.concatenate(tiles, axis=1)[:, :n]
            EN.append((np.interp(tt, ts, s["en"][a:b]) + h[0]).astype(np.float32))
            EE.append((np.interp(tt, ts, s["ee"][a:b]) + h[1]).astype(np.float32))
            start.append(pos)
            length.append(n)
            labels.append(f"{s['pair']} {s['date']}")
            pos += n
    _GNSS[grade] = dict(en=np.concatenate(EN), ee=np.concatenate(EE), start=np.array(start),
                        length=np.array(length), labels=labels)
    return _GNSS[grade]


def gnss_ne(cond, tsec):
    """Earth-fixed (north, east) GNSS error of every run of `cond` at mission times `tsec` [s].

    `tsec` must broadcast against (R, 1) (scalar, (1, K) or (R, K)); returns two arrays of the
    broadcast shape. CORS grades: each run reads its own segment from its own start time and is
    mirrored at the segment end (no artificial jump); legacy "i2nav": the single 1615 s record,
    wrapped as in v1-v4."""
    tsec = np.asarray(tsec)
    if cond.gnss == "i2nav":
        en, ee = rtk_ne()
        ti = (cond.rtk_offset[:, None] + tsec.astype(int)) % len(en)
        return en[ti], ee[ti]
    B = gnss_bank(cond.gnss)
    Lg = cond.gnss_len[:, None]
    p = (cond.gnss_u[:, None] + tsec.astype(np.int64)) % (2 * Lg)
    ti = cond.gnss_start[:, None] + np.where(p < Lg, p, 2 * Lg - 1 - p)
    return B["en"][ti], B["ee"][ti]


# --------------------------------------------------------------------- vehicle model
VEH = dict(v=2.0, l_wb=2.6, tau=0.25, delta_max=math.radians(35), rate_max=math.radians(30),
           h_ant=2.6, dt=0.05)


class Condition:
    """Per-run operating condition (sampled i.i.d. per run)."""

    def __init__(self, rng, n, moisture=None, comp=0.85, rtk_scale=1.0, mount_sd=0.015, gnss="rtk_fix",
                 moisture_range=None):
        # soil moisture index in [0, 1]; drives slip gain and roughness
        if moisture is not None:
            self.m = np.broadcast_to(moisture, (n,)).astype(float)
        elif moisture_range is not None:  # e.g. (0.6, 0.9): wet season
            self.m = rng.uniform(moisture_range[0], moisture_range[1], n)
        else:
            self.m = rng.beta(2, 3, n)
        self.k_s = 0.15 + 0.85 * self.m * rng.lognormal(0, 0.25, n)  # slip gain [-]
        self.rough = 0.004 + 0.012 * rng.lognormal(0, 0.3, n) * (0.5 + self.m)  # OU std of slip [rad]
        self.comp = np.clip(comp + rng.normal(0, 0.05, n), 0, 1)  # roll compensation fraction
        self.rtk_scale = rtk_scale
        self.rtk_offset = rng.integers(0, len(rtk_lateral()), n)
        # lateral antenna/implement mounting calibration error (vehicle frame, constant per run):
        # flips sign in the field frame between up- and down-field passes ("skip every other pass")
        self.mount = rng.normal(0.0, mount_sd, n)
        # real GNSS error: random CORS station-pair-day segment (length-weighted) and start second
        self.gnss = gnss
        if gnss != "i2nav":
            B = gnss_bank(gnss)
            seg = rng.choice(len(B["length"]), n, p=B["length"] / B["length"].sum())
            self.gnss_seg = seg
            self.gnss_start = B["start"][seg]
            self.gnss_len = B["length"][seg]
            self.gnss_u = rng.integers(0, 2 * self.gnss_len)


def simulate(field, ys, cond, rng, ctrl="lqr_i", dx=1.0):
    """Execute passes at lateral positions `ys` for every run in `cond`.

    `ctrl` is either a built-in name ("pure_pursuit", "stanley", "lqr", "lqr_i")
    or an object with reset(R, K, veh, cond) and command(meas, psi_meas, delta, dt)
    -> steering command (R, K), where meas is the measured lateral offset (vehicle
    frame, left positive) and psi_meas the measured heading error.

    Returns X (along-track grid, list per pass) and D: list of arrays (R, nx_k)
    with field-frame lateral offsets of the vehicle reference point.
    """
    R, K = len(cond.k_s), len(ys)
    v, l, tau, dt, h = VEH["v"], VEH["l_wb"], VEH["tau"], VEH["dt"], VEH["h_ant"]
    chords = [field.chord(field.P, y) for y in ys]
    x0 = np.array([c[0] if c else 0.0 for c in chords])
    x1 = np.array([c[1] if c else 0.0 for c in chords])
    L = np.maximum(x1 - x0, 1.0)
    sgn = np.where(np.arange(K) % 2 == 0, 1.0, -1.0)  # +x / -x
    nsteps = int(L.max() / (v * dt)) + 2
    # passes are driven sequentially: pass k starts after all previous passes + headland turns
    t_turn = math.pi * 4.5 / v + 6.0  # semicircular turn at r = 4.5 m plus line acquisition
    T0 = np.r_[0.0, np.cumsum(L / v + t_turn)[:-1]]  # (K,)
    th = math.radians(-field.rot)  # operating frame -> ENU
    proj_e, proj_n = -math.sin(th), math.cos(th)  # field +y axis expressed in (E, N)
    mount = cond.mount[:, None]
    # state (R, K)
    d = rng.normal(0, 0.03, (R, K))  # line acquisition residual after headland turn
    psi = rng.normal(0, math.radians(0.5), (R, K))
    delta = np.zeros((R, K))
    integ = np.zeros((R, K))
    ou = np.zeros((R, K))
    s_trav = np.zeros((R, K))
    k_s = cond.k_s[:, None]
    rough = cond.rough[:, None]
    comp = cond.comp[:, None]
    th_ou = 1.0 / 2.0  # 2 s correlation
    rec_every = max(1, int(round(dx / (v * dt))))
    nrec = nsteps // rec_every + 1
    rec = np.zeros((nrec, R, K))
    # LQR gains for [d, psi, int d] on linearised kinematics (discrete Riccati)
    K_lqr, K_lqri = _lqr_gains(v, l, dt)
    for t in range(nsteps):
        xf = np.where(sgn > 0, x0 + s_trav, x1 - s_trav)  # field-frame x
        yf = ys[None, :] + sgn * d  # vehicle-left = +y on +x passes
        g = field.gy(xf, yf)  # lateral elevation gradient (field frame)
        g_v = sgn * g  # in vehicle frame (left axis)
        ou += -th_ou * ou * dt + rough * math.sqrt(2 * th_ou * dt) * rng.standard_normal((R, K))
        beta = -k_s * g_v * 0.35 + ou  # slides downhill
        roll = np.arctan(g_v)
        gn, ge = gnss_ne(cond, T0[None, :] + t * dt)  # (R, K) at the earth time of each pass
        eps_y = proj_e * ge + proj_n * gn  # earth-fixed error projected on field lateral axis
        meas = d + h * np.sin(roll) * (1 - comp) * (-1.0) + sgn * cond.rtk_scale * eps_y + mount
        psim = psi + rng.normal(0, math.radians(0.15), (R, K))
        if not isinstance(ctrl, str):  # pluggable controller object (see baselines/controllers.py)
            if t == 0:
                ctrl.reset(R, K, VEH, cond)
            dcmd = ctrl.command(meas, psim, delta, dt)
        elif ctrl == "pure_pursuit":
            Ld = 4.0
            alpha = np.arctan2(-meas, Ld) - psim
            dcmd = np.arctan(2 * l * np.sin(alpha) / Ld)
        elif ctrl == "stanley":
            dcmd = -psim - np.arctan(1.2 * meas / v)
        elif ctrl == "lqr":
            dcmd = -(K_lqr[0] * meas + K_lqr[1] * psim)
        else:  # lqr with integral action + anti-windup (conditional integration, clamped state)
            u_try = -(K_lqri[0] * meas + K_lqri[1] * psim + K_lqri[2] * delta + K_lqri[3] * (integ + meas * dt))
            sat = np.abs(u_try) >= VEH["delta_max"]
            integ = np.where(sat, integ, np.clip(integ + meas * dt, -0.3, 0.3))
            dcmd = -(K_lqri[0] * meas + K_lqri[1] * psim + K_lqri[2] * delta + K_lqri[3] * integ)
        dcmd = np.clip(dcmd, -VEH["delta_max"], VEH["delta_max"])
        ddel = np.clip((dcmd - delta) / tau * dt, -VEH["rate_max"] * dt, VEH["rate_max"] * dt)
        delta += ddel
        d += v * np.sin(psi + beta) * dt
        psi += v * np.tan(delta) / l * dt
        s_trav += v * np.cos(psi) * dt
        if t % rec_every == 0:
            rec[t // rec_every] = sgn * d  # field-frame lateral offset
    # map records to along-track grid per pass
    X, D = [], []
    s_grid = np.arange(nrec) * rec_every * v * dt
    for k in range(K):
        n_k = int(L[k] / dx)
        sk = np.arange(n_k) * dx
        idx = np.clip(np.searchsorted(s_grid, sk), 0, nrec - 1)
        xk = x0[k] + sk if sgn[k] > 0 else x1[k] - sk
        X.append(xk)
        D.append(rec[idx, :, k].T)  # (R, n_k)
    return X, D


def pass_offsets(xk, dk, xg):
    """Vectorised linear interpolation of one pass's offsets (R, n_k) recorded on
    the regular along-track grid xk onto grid xg; nan where the pass is absent."""
    R = dk.shape[0]
    out = np.full((R, len(xg)), np.nan)
    if len(xk) < 2:
        return out
    step = xk[1] - xk[0]
    f = (xg - xk[0]) / step  # fractional index (works for both directions)
    ok = (f >= 0) & (f <= len(xk) - 1)
    fi = f[ok]
    i0 = np.clip(np.floor(fi).astype(int), 0, len(xk) - 2)
    t = fi - i0
    out[:, ok] = dk[:, i0] * (1 - t) + dk[:, i0 + 1] * t
    return out


def _lqr_gains(v, l, dt):
    A = np.array([[1, v * dt], [0, 1]])
    B = np.array([[0], [v / l * dt]])
    Q, Rr = np.diag([4.0, 1.0]), np.array([[2.0]])
    P = Q.copy()
    for _ in range(2000):
        P = Q + A.T @ P @ A - A.T @ P @ B @ np.linalg.solve(Rr + B.T @ P @ B, B.T @ P @ A)
    K1 = np.linalg.solve(Rr + B.T @ P @ B, B.T @ P @ A).ravel()
    # integral LQR designed on the lag-augmented model x = [d, psi, delta, int d], u = delta_cmd,
    # delta' = (u - delta)/tau  (the actuator lag is part of the design, so the loop is robust
    # to large GNSS jumps under steering-rate limits)
    tau = VEH["tau"]
    A4 = np.array([[1, v * dt, 0, 0], [0, 1, v / l * dt, 0], [0, 0, 1 - dt / tau, 0], [dt, 0, 0, 1]])
    B4 = np.array([[0], [0], [dt / tau], [0]])
    Q4 = np.diag([4.0, 1.0, 0.1, 0.4])
    R4 = np.array([[4.0]])
    P4 = Q4.copy()
    for _ in range(6000):
        P4 = Q4 + A4.T @ P4 @ A4 - A4.T @ P4 @ B4 @ np.linalg.solve(R4 + B4.T @ P4 @ B4, B4.T @ P4 @ A4)
    K4 = np.linalg.solve(R4 + B4.T @ P4 @ B4, B4.T @ P4 @ A4).ravel()
    return K1, K4


# ------------------------------------------------------------------ planning & scoring
def plan(field, w, lam, sig_fn, max_passes=400):
    """Greedy boustrophedon placement over the main area's lateral range with
    per-pass effective half-width h_k = w/2 - lam * sigma_hat(pass)."""
    y_lo, y_hi = field.lateral_range()
    ys, reach = [], y_lo
    while reach < y_hi - 1e-9:
        # solve y - h(y) = reach  by fixed-point (h varies slowly)
        y = reach + w / 2
        for _ in range(4):
            hy = w / 2 - lam * sig_fn(field, y)
            if hy < 0.2 * w / 2:
                raise ValueError("infeasible erosion")
            y = reach + hy
        ys.append(y)
        reach = y + (w / 2 - lam * sig_fn(field, y))
        if len(ys) > max_passes:
            raise ValueError("too many passes")
    return np.array(ys)


def pass_feature(field, y):
    """Mean |lateral slope| along the pass line (tan units)."""
    c = field.chord(field.M, y) or field.chord(field.P, y)
    if c is None:
        return 0.0
    xs = np.linspace(c[0], c[1], 30)
    return float(np.mean(np.abs(field.gy(xs, np.full_like(xs, y)))))


def evaluate(field, ys, X, D, w):
    """Exact lateral coverage of the main area along x-samples.

    Returns per-run missed-area fraction (R,) and per-run normalized scores
    are computed separately in `pair_terms`.
    """
    R = D[0].shape[0]
    K = len(ys)
    minx, _, maxx, _ = field.M.bounds
    xg = np.arange(math.ceil(minx), math.floor(maxx) + 1, 1.0)
    miss = np.zeros(R)
    total = 0.0
    # offsets at grid x for each pass (nan if pass absent)
    off = np.stack([pass_offsets(X[k], D[k], xg) for k in range(K)])
    for j, x in enumerate(xg):
        c = _chord_x(field.M, x)
        if c is None:
            continue
        lo, hi = c
        total += hi - lo
        rel = np.nonzero((ys > lo - w) & (ys < hi + w))[0]
        if len(rel) == 0:
            miss += hi - lo
            continue
        o = off[rel, :, j]  # (k, R)
        o = np.where(np.isnan(o), 1e3, o)  # absent pass covers nothing
        left = ys[rel, None] + o - w / 2
        right = ys[rel, None] + o + w / 2
        order = np.argsort(left, axis=0)
        left = np.take_along_axis(left, order, 0)
        right = np.take_along_axis(right, order, 0)
        left = np.clip(left, lo, hi)
        right = np.clip(right, lo, hi)
        reach = np.maximum.accumulate(right, axis=0)
        gaps = np.clip(left[1:] - reach[:-1], 0, None).sum(0)
        gaps += np.clip(left[0] - lo, 0, None) + np.clip(hi - reach[-1], 0, None)
        miss += gaps
    return miss / max(total, 1e-9)


def _chord_x(poly, x):
    _, miny, _, maxy = poly.bounds
    seg = LineString([(x, miny - 1), (x, maxy + 1)]).intersection(poly)
    if seg.is_empty:
        return None
    ys = [c[1] for c in (seg.coords if seg.geom_type == "LineString" else
                         [p for g in seg.geoms for p in g.coords])]
    return min(ys), max(ys)


def pair_scores(field, ys, X, D, sig, w=3.0):
    """Normalized pass-to-pass score per run (Lemma 1 / Theorem 1).

    S = max over x, adjacent pairs (k,k+1) of (e_{k+1} - e_k)/(sig_k + sig_{k+1}),
    plus boundary terms e_1/sig_1 and -e_N/sig_N, restricted to the main area.
    Also returns the raw per-pair maxima (R, K-1) for pair-level methods.
    """
    R, K = D[0].shape[0], len(ys)
    minx, _, maxx, _ = field.M.bounds
    xg = np.arange(math.ceil(minx), math.floor(maxx) + 1, 1.0)  # same grid as evaluate()
    off = np.stack([pass_offsets(X[k], D[k], xg) for k in range(K)])
    # mask to main-area chord
    mask = np.zeros((K, len(xg)), bool)
    for j, x in enumerate(xg):
        c = _chord_x(field.M, x)
        if c is None:
            continue
        lo, hi = c
        mask[:, j] = (ys > lo - w) & (ys < hi + w)
    pair = np.full((R, max(K - 1, 1)), -np.inf)
    for k in range(K - 1):
        m = mask[k] & mask[k + 1]
        if not m.any():
            continue
        diff = (off[k + 1][:, m] - off[k][:, m]) / (sig[k] + sig[k + 1])
        pair[:, k] = np.nanmax(diff, axis=1)
    b1 = np.nanmax(off[0][:, mask[0]], axis=1) / sig[0] if mask[0].any() else np.full(R, -np.inf)
    bN = np.nanmax(-off[-1][:, mask[-1]], axis=1) / sig[-1] if mask[-1].any() else np.full(R, -np.inf)
    S = np.maximum(pair.max(axis=1), np.maximum(b1, bN))
    return S, pair, b1, bN


def exact_scores(field, ys, X, D, w, lam_ref=0.0):
    """EXACT run-level score for a uniform-erosion plan executed at erosion lam_ref.

    At every x-section of core.evaluate's 1 m grid the passes relevant there (same rule as evaluate)
    cover the main-area chord [lo, hi] with footprints of half-width w/2 iff the covering radius
        r*(x) = max( d(lo, C), d(hi, C), max_{i: (c_i + c_{i+1})/2 in [lo, hi]} (c_{i+1} - c_i) / 2 )
    of the executed centres C (sorted) does not exceed w/2 (equal-length intervals). So the run has
    zero missed area iff  S = lam_ref + max_x (r*(x) - w/2) <= lam_ref, exactly as evaluate() scores it;
    S - lam_ref is the uniform footprint growth needed to close the worst gap (equivalently the extra
    erosion of a shift-equivariant uniform planner). Returns S (R,)."""
    R, K = D[0].shape[0], len(ys)
    minx, _, maxx, _ = field.M.bounds
    xg = np.arange(math.ceil(minx), math.floor(maxx) + 1, 1.0)
    off = np.stack([pass_offsets(X[k], D[k], xg) for k in range(K)])
    worst = np.full(R, -np.inf)
    for j, x in enumerate(xg):
        c = _chord_x(field.M, x)
        if c is None:
            continue
        lo, hi = c
        rel = np.nonzero((ys > lo - w) & (ys < hi + w))[0]
        if len(rel) == 0:
            return np.full(R, np.inf)
        C = ys[rel, None] + off[rel, :, j]  # (m, R)
        C = np.sort(np.where(np.isnan(C), 1e6, C), axis=0)  # absent pass: far away, covers nothing
        r = np.maximum(np.min(np.abs(C - lo), axis=0), np.min(np.abs(C - hi), axis=0))
        if len(rel) > 1:
            mid = 0.5 * (C[1:] + C[:-1])
            half = 0.5 * (C[1:] - C[:-1])
            half = np.where((mid >= lo) & (mid <= hi), half, -np.inf)
            r = np.maximum(r, half.max(axis=0))
        worst = np.maximum(worst, r - w / 2)
    return lam_ref + worst


def conformal_quantile(scores, eps, weights=None, w_test=None):
    s = np.sort(np.asarray(scores))
    n = len(s)
    if weights is None:
        k = int(math.ceil((n + 1) * (1 - eps)))
        return s[k - 1] if k <= n else np.inf
    order = np.argsort(scores)
    sw = np.asarray(weights)[order]
    p = np.cumsum(sw) / (sw.sum() + w_test)
    k = np.searchsorted(p, 1 - eps)
    return np.sort(scores)[k] if k < n else np.inf

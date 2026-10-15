"""Headland laps along the lateral sides of the main area (revision experiment RV5, docs/prereg_revision.md).

The registered evaluation treats the main-area boundary as a hard edge reached only by the outermost infield pass.
Here one headland lap runs along each lateral side, planned so that its inner footprint edge reaches lam into the
main area (nominal overlap 2 lam with the outermost pass, like an interior pair). Each lap is simulated as a straight
pass in the headland band, driven after all infield passes (so it reads the GNSS error at a later time), and its
offset is projected onto the local boundary through the boundary angle: at section x the lower lap covers the chord
up to  lo(x) + (lam + e_lo(x)) / cos(alpha_lo(x))  and the upper lap down to  hi(x) - (lam - e_hi(x)) / cos(alpha_hi(x)).

In the exact score the laps enter as pseudo-centres whose footprint edge is that reach, so zero missed area <=> S <= lam
remains exact (Lemma 1); growing the half-width moves a lap's reach by the same amount, which is conservative on
slanted sides (the true growth is larger by 1/cos(alpha)).
"""
import math

import numpy as np

import core

COS_MIN = 0.2


def lap_lines(F, w, lam):
    y_lo, y_hi = F.lateral_range()
    return y_lo - (w / 2 - lam), y_hi + (w / 2 - lam)


def simulate(F, ys, w, lam, cond, rng, sim):
    """Simulate infield passes `ys` followed by the two laps. Returns (X, D) of the infield passes and the lap
    offsets (e_lo, e_hi), each a (R, nx) array on the 1 m section grid (nan where the lap has no data)."""
    ylo, yhi = lap_lines(F, w, lam)
    X, D = sim(np.r_[ys, ylo, yhi], cond, rng)
    xg = grid(F)
    e_lo = core.pass_offsets(X[-2], D[-2], xg)
    e_hi = core.pass_offsets(X[-1], D[-1], xg)
    return X[:-2], D[:-2], (e_lo, e_hi)


def grid(F):
    minx, _, maxx, _ = F.M.bounds
    return np.arange(math.ceil(minx), math.floor(maxx) + 1, 1.0)


def _boundary(F):
    xg = grid(F)
    lo = np.full(len(xg), np.nan)
    hi = np.full(len(xg), np.nan)
    for j, x in enumerate(xg):
        c = core._chord_x(F.M, x)
        if c is not None and c[1] > c[0]:
            lo[j], hi[j] = c
    def cosang(b):
        g = np.gradient(np.where(np.isnan(b), np.nanmean(b), b), xg)
        return np.maximum(np.cos(np.arctan(g)), COS_MIN)
    return xg, lo, hi, cosang(lo), cosang(hi)


def reaches(F, lam, laps):
    xg, lo, hi, clo, chi = _boundary(F)
    e_lo, e_hi = laps
    r_lo = lo[None, :] + (lam + np.where(np.isnan(e_lo), -1e3, e_lo)) / clo[None, :]
    r_hi = hi[None, :] - (lam - np.where(np.isnan(e_hi), 1e3, e_hi)) / chi[None, :]
    return xg, lo, hi, r_lo, r_hi


def exact_scores(F, ys, X, D, w, lam, laps, split=False):
    """core.exact_scores with the two laps as pseudo-centres. With split=True also returns the worst
    boundary-related term (any gap touching lo/hi or a lap) and the worst infield pass-to-pass term."""
    R, K = D[0].shape[0], len(ys)
    xg, lo_a, hi_a, r_lo, r_hi = reaches(F, lam, laps)
    off = np.stack([core.pass_offsets(X[k], D[k], xg) for k in range(K)])
    h = w / 2
    worst = np.full(R, -np.inf)
    wb = np.full(R, -np.inf)
    wi = np.full(R, -np.inf)
    for j in range(len(xg)):
        lo, hi = lo_a[j], hi_a[j]
        if not np.isfinite(lo):
            continue
        rel = np.nonzero((ys > lo - w) & (ys < hi + w))[0]
        o = off[rel, :, j] if len(rel) else np.zeros((0, R))
        Cm = ys[rel, None] + np.where(np.isnan(o), 1e3, o)
        Cl = (r_lo[:, j] - h)[None, :]
        Ch = (r_hi[:, j] + h)[None, :]
        lab = np.r_[1, np.zeros(len(rel)), 1][:, None] * np.ones((1, R))  # 1 = lap pseudo-centre
        Cu = np.concatenate([Cl, Cm, Ch], 0)
        order = np.argsort(Cu, axis=0)
        C = np.take_along_axis(Cu, order, 0)
        isl = np.take_along_axis(lab, order, 0)
        edge = np.maximum(np.min(np.maximum((C - h) - lo, lo - (C + h)), axis=0),
                          np.min(np.maximum((C - h) - hi, hi - (C + h)), axis=0))
        mid = 0.5 * (C[1:] + C[:-1])
        gap = np.where((mid >= lo) & (mid <= hi), 0.5 * ((C[1:] - h) - (C[:-1] + h)), -np.inf)
        lapgap = np.where((isl[1:] + isl[:-1]) > 0, gap, -np.inf).max(axis=0)
        ingap = np.where((isl[1:] + isl[:-1]) == 0, gap, -np.inf).max(axis=0)
        worst = np.maximum(worst, np.maximum(edge, np.maximum(lapgap, ingap)))
        wb = np.maximum(wb, np.maximum(edge, lapgap))
        wi = np.maximum(wi, ingap)
    S = lam + worst
    return (S, lam + wb, lam + wi) if split else S


def evaluate(F, ys, X, D, w, lam, laps):
    """Missed-area fraction of the main area with the lap footprints included (as core.evaluate)."""
    R, K = D[0].shape[0], len(ys)
    xg, lo_a, hi_a, r_lo, r_hi = reaches(F, lam, laps)
    off = np.stack([core.pass_offsets(X[k], D[k], xg) for k in range(K)])
    miss = np.zeros(R)
    total = 0.0
    for j in range(len(xg)):
        lo, hi = lo_a[j], hi_a[j]
        if not np.isfinite(lo):
            continue
        total += hi - lo
        rel = np.nonzero((ys > lo - w) & (ys < hi + w))[0]
        o = off[rel, :, j] if len(rel) else np.zeros((0, R))
        left = np.concatenate([(r_lo[:, j] - w)[None], ys[rel, None] + np.where(np.isnan(o), 1e3, o) - w / 2,
                               r_hi[:, j][None]], 0)
        right = np.concatenate([r_lo[:, j][None], ys[rel, None] + np.where(np.isnan(o), 1e3, o) + w / 2,
                                (r_hi[:, j] + w)[None]], 0)
        order = np.argsort(left, axis=0)
        left = np.clip(np.take_along_axis(left, order, 0), lo, hi)
        right = np.clip(np.take_along_axis(right, order, 0), lo, hi)
        reach = np.maximum.accumulate(right, axis=0)
        gaps = np.clip(left[1:] - reach[:-1], 0, None).sum(0)
        gaps += np.clip(left[0] - lo, 0, None) + np.clip(hi - reach[-1], 0, None)
        miss += gaps
    return miss / max(total, 1e-9)

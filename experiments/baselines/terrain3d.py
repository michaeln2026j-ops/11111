"""Terrain-aware 3D side-to-side swath spacing (Hameed, la Cour-Harbo & Osen, 2016).

Reference
---------
I. A. Hameed, A. la Cour-Harbo, O. L. Osen, "Side-to-side 3D coverage path
planning approach for agricultural robots to minimize skip/overlap areas
between swaths", Robotics and Autonomous Systems, vol. 76, pp. 36-45, 2016.
doi:10.1016/j.robot.2015.11.009  (ScienceDirect PII S0921889015002973).

Citation check (2026-10-13): authors, title, journal and year were confirmed
on the Aalborg University research portal (vbn.aau.dk), the NTNU staff pages
of Hameed and Osen, and the ScienceDirect listing. Volume 76, pages 36-45 and
the DOI were confirmed from citing documents (US patent application
2023/0090080 and later reference lists). The publisher full text could not be
fetched from this machine (ScienceDirect, ResearchGate and doi.org are
blocked), so the method below follows the abstract and secondary
descriptions: the ResearchGate summary of the paper, and M. Plessen, "From 2D
to 3D terrain-following area coverage path planning", arXiv:2601.00614, which
describes the cylinder construction.
Verify the volume, pages and DOI against the publisher page before submission.

What the published method does
------------------------------
The abstract says that 3D coverage planners which project a 2D plan onto the
terrain leave skips on slopes. Adjacent lines that are w apart horizontally
are further apart on the topographic surface, and machine roll on a slope
reduces the implement's effective width. The paper (i) estimates the total
skip and overlap area numerically and uses that estimate to choose the
driving angle, and (ii) proposes "side-to-side" 3D coverage. In (ii), at each
sampling point of the current swath, a cylinder of radius equal to the
working width w, with its axis along the driving direction, is intersected
with the 3D terrain surface. The intersection is the point of the adjacent
swath, so adjacent swaths lie exactly w apart on the surface and touch with
zero skip and zero overlap, assuming perfect execution. On a side slope theta
the horizontal spacing is therefore w*cos(theta) instead of w.

Adaptation to this codebase (minimal and explicit)
--------------------------------------------------
A1  Straight passes. core.simulate and core.evaluate need straight passes
    y = y_k along +x, while the original side-to-side lines are curved (one
    cylinder intersection per sampling point). Two variants are provided:
      mode="mean"      (default, line-averaged): greedy boustrophedon with
                       horizontal half-width
                           h_k = (w/2) cos(theta_k) - overlap/2,
                           theta_k = atan(mean |side slope| along y_k in M),
                       where M is the main area and the side slope is
                       field.gy, the lateral elevation gradient (tan) that
                       the simulator also uses. Placement reuses
                       core.plan (lam = 1, sig = (w/2)(1-cos theta)+overlap/2),
                       so the first and last pass at the boundaries are
                       handled exactly as in the flat 2D baseline
                       core.plan(F, w, 0, .).
      mode="pointwise" (faithful cylinder rule): at every sampling point x_j
                       of line y_k (the 1 m along-track columns of
                       core.evaluate whose M chord meets the strip to the
                       next line) we solve the cylinder/surface intersection
                           dy^2 + (Z(x_j, y_k + dy) - Z(x_j, y_k))^2 = w^2
                       for the horizontal offset dy_j of the adjacent swath.
                       The straight line uses dy = min_j dy_j - overlap
                       (agg="min"), the straight line that keeps the
                       surface spacing <= w at every sampled point. This
                       keeps the paper's zero-skip guarantee under perfect
                       execution. agg="mean" averages instead. The boundary
                       passes use radius w/2 against the M lateral limits.
                       On a curved DEM cross-section the radius-w chord and
                       two radius-w/2 half-footprints differ by ~1e-5 m, so
                       "min" takes the smaller of the two. The plan is then
                       exactly gap-free under evaluate_surface.
A2  Terrain surface. Z is rebuilt by integrating the field-frame lateral
    gradient gy_map along y (trapezoid rule, 1 m grid). Only height
    differences within a cross-section are needed, so the integration
    constant per column does not matter. This is the same terrain the
    simulator uses for roll and side-slip.
A3  Cross-section. The cylinder axis is the horizontal driving direction (+x),
    so each intersection is solved in the vertical y-z plane at x_j. A
    longitudinal slope alpha would scale dZ by cos(alpha), which is a
    fourth-order effect, so it is ignored.
A4  Driving angle. Every method in this codebase uses the same recorded
    harvester direction, so the main comparison fixes the heading.
    optimal_heading() implements the paper's driving-angle search
    (skip + overlap area of a perfectly executed plan on the 3D surface) as
    an optional extra.
A5  Execution. The published planner assumes perfect path following. Here
    its lines run through the same closed-loop simulator (core.simulate:
    RTK noise, antenna roll offset, side-slip, steering lag) as every other
    method, so the comparison isolates the planning rule.
    perfect_execution() supplies the zero-error case the paper assumes.

Coverage evaluation: horizontal projection
------------------------------------------
core.evaluate measures coverage on the HORIZONTAL projection of the main
area. It treats the implement as covering a horizontal interval of width w
centred on the executed lateral position (w is the effective horizontal
swath). All planners, including this one, output horizontal line positions
y_k, which is what GNSS autosteer tracks. So the plans are directly
comparable, and only the horizontal spacing matters. We handle the two
footprint conventions as follows:
  * Codebase convention (core.evaluate, used in the paper's tables). The
    horizontal footprint is w. The 3D rule then shrinks the spacing, which
    acts as an extra slope-dependent margin of (w/2)(1 - cos theta) per
    side. That is O(theta^2), a few mm on these fields, whereas the
    slope-induced execution bias (antenna roll offset h tan(theta)(1-c),
    side-slip) is O(theta).
  * Hameed's convention (evaluate_surface, robustness check). w is measured
    on the surface, so the horizontal footprint of a pass centred at y_c is
    [y_c - a_L, y_c + a_R], where a_L and a_R solve the same cylinder
    intersection with radius w/2 at every x. Under this metric a flat 2D
    plan has geometric skips even when executed perfectly (the paper's
    motivation), and the side-to-side plan removes them.
    Missed area is still reported as a fraction of the horizontal main-area
    area. Surface and horizontal areas differ by a factor of 1/cos theta,
    i.e. <1% here.

API
---
side_slope(field, y)                         mean |tan side slope| on line y in M
plan_terrain3d(field, w, overlap=0.0, mode="mean"|"pointwise", agg="min") -> ys
plan_flat2d(field, w, overlap=0.0)           2D reference: core.plan, half-width w/2-overlap/2
surface_reach(field, x, y, r, sgn)           horizontal offset at surface distance r
perfect_execution(field, ys) -> X, D         zero-error execution (one run)
evaluate_surface(field, ys, X, D, w)         per-run missed fraction, 3D footprint
coverage_terms(field, ys, X, D, w, surface)  per-run (missed, overlap) fractions
evaluate_plan3d(F, ys, n, rng, w, ctrl)      metrics under both conventions
optimal_heading(field, w, headings, planner) the paper's driving-angle search
selftest()                                   2 steepest paddy fields, 50 runs each
"""
import math
import time
import weakref

import numpy as np

import core
import exp_lib

W_DEFAULT = 3.0

# ------------------------------------------------------------------ terrain surface
_ZCACHE = weakref.WeakKeyDictionary()


def _zlat(field):
    """Lateral height profile Z[i, j] on the field's 1 m grid (rows: y = gy0 + i,
    cols: x = gx0 + j), from trapezoidal integration of gy_map along y."""
    Z = _ZCACHE.get(field)
    if Z is None:
        g = field.gy_map
        Z = np.zeros_like(g)
        Z[1:] = np.cumsum(0.5 * (g[1:] + g[:-1]), axis=0)
        _ZCACHE[field] = Z
    return Z


def _Z(field, x, y):
    """Bilinear lateral height at (x, y); x, y broadcastable arrays [m]."""
    Z = _zlat(field)
    ny, nx = Z.shape
    fy = np.clip(np.asarray(y, float) - field.gy0, 0, ny - 1.001)
    fx = np.clip(np.asarray(x, float) - field.gx0, 0, nx - 1.001)
    i, j = fy.astype(int), fx.astype(int)
    ty, tx = fy - i, fx - j
    return (Z[i, j] * (1 - ty) * (1 - tx) + Z[i + 1, j] * ty * (1 - tx)
            + Z[i, j + 1] * (1 - ty) * tx + Z[i + 1, j + 1] * ty * tx)


def surface_reach(field, x, y, r, sgn=1.0, iters=8):
    """Horizontal lateral offset dy >= 0 such that the point (x, y + sgn*dy) on
    the terrain is at Euclidean distance r from (x, y) in the vertical
    cross-section, i.e. dy^2 + (Z(x, y+sgn*dy) - Z(x, y))^2 = r^2: the
    intersection of a cylinder of radius r (axis = driving direction) with the
    terrain surface (Hameed et al., 2016). x, y broadcastable; returns dy."""
    x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
    z0 = _Z(field, x, y)
    dy = np.full(x.shape, float(r))
    for _ in range(iters):  # dy = r / sqrt(1 + s^2), s = chord slope; contraction for |s| < 1
        s = (_Z(field, x, y + sgn * dy) - z0) / dy
        dy = r / np.sqrt(1.0 + s * s)
    return dy


# ------------------------------------------------------------------------- planning
def _chord_xs(field, y, step=1.0, min_n=30):
    c = field.chord(field.M, y) or field.chord(field.P, y)
    if c is None:
        return None
    n = max(min_n, int((c[1] - c[0]) / step) + 1)
    return np.linspace(c[0], c[1], n)


def side_slope(field, y, step=1.0):
    """Mean |lateral slope| (tan) along the straight line y inside the main
    area (falls back to the full polygon outside M), sampled every `step` m."""
    xs = _chord_xs(field, y, step)
    if xs is None:
        return 0.0
    return float(np.mean(np.abs(field.gy(xs, np.full_like(xs, y)))))


def plan_flat2d(field, w=W_DEFAULT, overlap=0.0):
    """Flat 2D reference: constant horizontal spacing w - overlap."""
    return core.plan(field, w, 1.0, lambda f, y: overlap / 2.0)


def plan_terrain3d(field, w=W_DEFAULT, overlap=0.0, mode="mean", agg="min", step=1.0,
                   max_passes=400):
    """Terrain-aware 3D side-to-side swath placement (Hameed et al., 2016).

    field   : core.Field (operating frame, passes are lines y = y_k along +x)
    w       : implement working width measured ON THE TERRAIN SURFACE [m]
    overlap : desired horizontal overlap between adjacent swaths [m] (0 = touch)
    mode    : "mean"      h_k = (w/2) cos(atan(mean|gy| on y_k in M)) - overlap/2,
                          greedy boustrophedon (core.plan placement);
              "pointwise" per-sampling-point cylinder intersection (radius w)
                          on the integrated terrain, aggregated along the line
                          by `agg` ("min": zero surface skip at every sampled
                          point; "mean": line-averaged spacing).
    step    : along-track sampling step for the side slope in mode="mean" [m]
    Returns np.ndarray of lateral swath-centre positions ys (ascending).
    """
    if mode == "mean":
        def sig(f, y):
            c = 1.0 / math.sqrt(1.0 + side_slope(f, y, step) ** 2)  # cos(atan(s))
            return (w / 2.0) * (1.0 - c) + overlap / 2.0

        return core.plan(field, w, 1.0, sig, max_passes=max_passes)
    if mode != "pointwise":
        raise ValueError(mode)
    if agg not in ("min", "mean"):
        raise ValueError(agg)
    red = np.min if agg == "min" else np.mean
    y_lo, y_hi = field.lateral_range()
    cx, clo, chi = _columns(field)
    eps = 1e-9  # 1 nm numerical safety so touching swaths are not scored as a gap

    def xs_strip(a, b):  # evaluation columns whose M chord meets the strip (a, b)
        sel = (clo < b) & (chi > a)
        return cx[sel] if sel.any() else cx

    # first pass: its left surface half-width w/2 must reach y_lo in every column
    y = y_lo + w / 2
    for _ in range(4):
        a = red(surface_reach(field, xs_strip(y_lo, y + w / 2), y, w / 2, -1.0))
        y = y_lo + a - overlap / 2 - (eps if agg == "min" else 0.0)
    ys = [y]
    while True:
        b = red(surface_reach(field, xs_strip(y - w / 2, y + w / 2), y, w / 2, +1.0))
        if y + b - overlap / 2 >= y_hi - 1e-9:
            break
        xs = xs_strip(y, y + w)
        dy = red(surface_reach(field, xs, y, w, +1.0))  # cylinder of radius w
        if agg == "min":
            # The cylinder chord (radius w) and the two half-footprints (radius
            # w/2 each, the rigid-implement model used by evaluate_surface)
            # coincide on a planar cross-section. On the curved DEM section
            # they differ by ~1e-5 m, so keep the smaller to stay exactly
            # gap-free.
            aR = surface_reach(field, xs, y, w / 2, +1.0)
            d = dy
            for _ in range(3):
                aL = surface_reach(field, xs, y + d - overlap, w / 2, -1.0)
                d = min(dy, float(np.min(aR + aL)))
            dy = d - eps
        y = y + dy - overlap
        ys.append(y)
        if len(ys) > max_passes:
            raise ValueError("too many passes")
    return np.array(ys)


_COLCACHE = weakref.WeakKeyDictionary()


def _columns(field):
    """Integer along-track columns of core.evaluate's grid with their main-area
    chord [lo, hi] (the columns the coverage metric is evaluated on)."""
    c = _COLCACHE.get(field)
    if c is None:
        minx, _, maxx, _ = field.M.bounds
        xs, lo, hi = [], [], []
        for x in np.arange(math.ceil(minx), math.floor(maxx) + 1, 1.0):
            ch = core._chord_x(field.M, x)
            if ch is not None:
                xs.append(x), lo.append(ch[0]), hi.append(ch[1])
        c = (np.array(xs), np.array(lo), np.array(hi))
        _COLCACHE[field] = c
    return c


# ----------------------------------------------------------------------- execution
def perfect_execution(field, ys, dx=1.0):
    """X, D as returned by core.simulate for a single run that follows every
    line exactly (the paper's assumption)."""
    X, D = [], []
    for k, y in enumerate(ys):
        c = field.chord(field.P, y) or (0.0, 0.0)
        L = max(c[1] - c[0], 1.0)
        sk = np.arange(int(L / dx)) * dx
        X.append(c[0] + sk if k % 2 == 0 else c[1] - sk)
        D.append(np.zeros((1, len(sk))))
    return X, D


# ---------------------------------------------------------------------- evaluation
def coverage_terms(field, ys, X, D, w=W_DEFAULT, surface=True):
    """Per-run (missed, overlap) area fractions of the main area on the
    horizontal projection, grid as in core.evaluate. surface=False uses the
    codebase footprint [y_c - w/2, y_c + w/2] and reproduces core.evaluate;
    surface=True uses the projection of a width-w implement lying on the
    terrain, [y_c - a_L, y_c + a_R] with a_L, a_R = surface_reach(., w/2)."""
    ys = np.asarray(ys, float)
    R, K = D[0].shape[0], len(ys)
    minx, _, maxx, _ = field.M.bounds
    xg = np.arange(math.ceil(minx), math.floor(maxx) + 1, 1.0)
    off = np.stack([core.pass_offsets(X[k], D[k], xg) for k in range(K)])
    miss, over, total = np.zeros(R), np.zeros(R), 0.0
    for j, x in enumerate(xg):
        c = core._chord_x(field.M, x)
        if c is None:
            continue
        lo, hi = c
        total += hi - lo
        rel = np.nonzero((ys > lo - w) & (ys < hi + w))[0]
        if len(rel) == 0:
            miss += hi - lo
            continue
        o = off[rel, :, j]  # (k, R)
        absent = np.isnan(o)
        yc = ys[rel, None] + np.where(absent, 0.0, o)
        if surface:
            aL = surface_reach(field, x, yc, w / 2, -1.0)
            aR = surface_reach(field, x, yc, w / 2, +1.0)
        else:
            aL = aR = w / 2
        left = np.where(absent, hi + 1e3, yc - aL)  # absent pass covers nothing
        right = np.where(absent, hi + 1e3, yc + aR)
        order = np.argsort(left, axis=0)
        left = np.clip(np.take_along_axis(left, order, 0), lo, hi)
        right = np.clip(np.take_along_axis(right, order, 0), lo, hi)
        reach = np.maximum.accumulate(right, axis=0)
        gaps = np.clip(left[1:] - reach[:-1], 0, None).sum(0)
        gaps += np.clip(left[0] - lo, 0, None) + np.clip(hi - reach[-1], 0, None)
        miss += gaps
        over += (right - left).sum(0) - ((hi - lo) - gaps)
    t = max(total, 1e-9)
    return miss / t, over / t


def evaluate_surface(field, ys, X, D, w=W_DEFAULT):
    """Per-run missed-area fraction when w is the working width on the 3D
    surface (Hameed's convention); counterpart of core.evaluate."""
    return coverage_terms(field, ys, X, D, w, surface=True)[0]


def evaluate_plan3d(F, ys, n_test, rng, w=W_DEFAULT, ctrl="lqr_i", **cond_kw):
    """Closed-loop evaluation under both footprint conventions.
    *_h  : codebase convention (core.evaluate, horizontal footprint w)
    *_s  : surface convention (evaluate_surface)
    overlap_* are planned (perfect-execution) overlap ratios."""
    X, D, _ = exp_lib.run(F, ys, n_test, rng, ctrl=ctrl, w=w, **cond_kw)
    mh = core.evaluate(F, ys, X, D, w)
    ms = evaluate_surface(F, ys, X, D, w)
    Xp, Dp = perfect_execution(F, ys)
    m0h, o0h = coverage_terms(F, ys, Xp, Dp, w, surface=False)
    m0s, o0s = coverage_terms(F, ys, Xp, Dp, w, surface=True)
    return dict(passes=len(ys), p_nomiss_h=float(np.mean(mh == 0)), e_miss_h=float(mh.mean()),
                p_nomiss_s=float(np.mean(ms == 0)), e_miss_s=float(ms.mean()),
                overlap_h=float(o0h[0]), overlap_s=float(o0s[0]),
                overlap_ratio=exp_lib.overlap_ratio(F, ys, w),
                perfect_miss_h=float(m0h[0]), perfect_miss_s=float(m0s[0]))


def optimal_heading(field, w=W_DEFAULT, headings=None, planner="2d", overlap=0.0):
    """Driving-angle search from Hameed et al. (2016): for each candidate
    heading (deg clockwise from north) rebuild the field frame, plan, and
    score the plan by its total skip + overlap area on the 3D surface under
    perfect execution. Returns (best_heading, rows) where rows are
    (heading, passes, skip_m2, overlap_m2)."""
    if headings is None:
        headings = field.meta["heading_deg"] + np.arange(0, 180, 15)
    rows = []
    for h in headings:
        G = core.Field(field.fid, dict(field.meta, heading_deg=float(h) % 360), headland=field.H, w=w)
        ys = plan_flat2d(G, w, overlap) if planner == "2d" else plan_terrain3d(G, w, overlap, mode="pointwise")
        Xp, Dp = perfect_execution(G, ys)
        m, o = coverage_terms(G, ys, Xp, Dp, w, surface=True)
        rows.append((float(h) % 360, len(ys), float(m[0] * G.M.area), float(o[0] * G.M.area)))
    best = min(rows, key=lambda r: r[2] + r[3])[0]
    return best, rows


# ------------------------------------------------------------------------ selftest
def selftest(n_runs=50, w=W_DEFAULT, seed=0):
    t_all = time.time()
    Fs = core.load_fields("paddy", w=w)
    # rank by mean side slope over the flat plan's lines (what the 3D rule reacts to)
    rank = []
    for F in Fs:
        ys = plan_flat2d(F, w)
        rank.append((np.mean([side_slope(F, y) for y in ys]), F))
    rank.sort(key=lambda r: -r[0])
    print(f"terrain3d selftest: {len(Fs)} paddy fields, 2 with the largest mean side slope; "
          f"w={w} m, {n_runs} closed-loop runs (lqr_i) per plan")
    for s_mean, F in rank[:2]:
        sl = np.array([side_slope(F, y) for y in plan_flat2d(F, w)])
        th = math.degrees(math.atan(s_mean))
        print(f"\nfield {F.fid}: main area {F.M.area:.0f} m2, mean slope {F.z_mean_slope:.2f} deg, "
              f"mean side slope {th:.2f} deg (max line {math.degrees(math.atan(sl.max())):.2f} deg)")
        print(f"  3D margin per side (w/2)(1-cos th) = {1e3 * w / 2 * (1 - math.cos(math.radians(th))):.1f} mm;"
              f"  residual antenna roll offset h tan(th)(1-0.85) = "
              f"{1e3 * core.VEH['h_ant'] * math.tan(math.radians(th)) * 0.15:.1f} mm")
        plans = {}
        for name, fn in [("flat2D", lambda: plan_flat2d(F, w)),
                         ("3D-mean", lambda: plan_terrain3d(F, w, mode="mean")),
                         ("3D-pointwise", lambda: plan_terrain3d(F, w, mode="pointwise"))]:
            t = time.time()
            ys = fn()
            plans[name] = (ys, 1e3 * (time.time() - t))
        print(f"  {'plan':13s} {'K':>3s} {'plan_ms':>7s} | {'perfect miss h/s':>16s} | "
              f"{'P(no miss) h':>12s} {'P(no miss) s':>12s} {'E[miss] h':>9s} {'E[miss] s':>9s} | "
              f"{'overlap':>7s} {'overlap s':>9s} {'eval_s':>6s}")
        for name, (ys, ms) in plans.items():
            t = time.time()
            r = evaluate_plan3d(F, ys, n_runs, np.random.default_rng(seed), w=w)
            print(f"  {name:13s} {r['passes']:3d} {ms:7.1f} | {r['perfect_miss_h']:7.4f}/{r['perfect_miss_s']:.4f}"
                  f"   | {r['p_nomiss_h']:12.2f} {r['p_nomiss_s']:12.2f} {r['e_miss_h']:9.5f} {r['e_miss_s']:9.5f} |"
                  f" {r['overlap_ratio'] + 0.0:7.4f} {r['overlap_s'] + 0.0:9.4f} {time.time() - t:6.2f}")
        # consistency checks
        ys3 = plans["3D-pointwise"][0]
        Xp, Dp = perfect_execution(F, ys3)
        assert coverage_terms(F, ys3, Xp, Dp, w, surface=True)[0][0] == 0.0, "pointwise 3D must have zero surface skip"
        X, D, _ = exp_lib.run(F, ys3, 5, np.random.default_rng(1), w=w)
        assert np.allclose(coverage_terms(F, ys3, X, D, w, surface=False)[0], core.evaluate(F, ys3, X, D, w))
        t = time.time()
        best, rows = optimal_heading(F, w)
        rec = rows[0]
        b = [r for r in rows if r[0] == best][0]
        print(f"  driving-angle search (2D plan, 12 headings, {time.time() - t:.2f} s): recorded "
              f"{rec[0]:.0f} deg skip+overlap {rec[2] + rec[3]:.1f} m2 (K={rec[1]}); best {best:.0f} deg "
              f"{b[2] + b[3]:.1f} m2 (K={b[1]})")
    print(f"\nchecks passed (pointwise 3D zero surface skip; horizontal footprint == core.evaluate); "
          f"total {time.time() - t_all:.1f} s")

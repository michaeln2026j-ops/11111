"""Fields2Cover (F2C) coverage path planning baseline.

Reference (verified against the paper record and the repository's CITATION.cff)
-------------------------------------------------------------------------------
G. Mier, J. Valente and S. de Bruin, "Fields2Cover: An open-source coverage
path planning library for unmanned agricultural vehicles," IEEE Robotics and
Automation Letters, vol. 8, no. 4, pp. 2166-2172, 2023,
doi:10.1109/LRA.2023.3248439.  Code: https://github.com/Fields2Cover/Fields2Cover
(BSD-3).  This module was written from the source at commit 93c0989 (v2.1.1).

What is replicated (file names refer to the F2C repository)
------------------------------------------------------------
1. Headland generator  hg/ConstHL::generateHeadlands:  inner cell =
   field.buffer(-headland_width).  Swaths are generated on this cell only.
2. Swath generator  sg/SwathGeneratorBase::generateSwaths(angle, op_width,
   cell):  rotate the cell by -angle, put parallel lines at
   y = minY + (k + 1/2) * op_width while  height > y_prev + op_width/2
   (allow_overlap = false, the default), rotate back, clip every line to the
   cell (each clipped LineString part is one swath; non-line parts dropped as
   in MultiLineString::append).
   sg/BruteForce::computeBestAngle:  evaluate angles i * step_angle,
   i = 0 .. int(2*pi/step_angle) - 1 (default step_angle = 1 degree),
   return the FIRST arg-min of the objective (std::min_element), with the
   generateBestSwaths fallback (try angle + i*pi/8 when the best angle yields
   no swath).
3. Swath-generator objectives (all minimised, obj/sg_obj):
     NSwath          cost = number of swaths (clipped parts)            n_swath.cpp
     SwathLength     cost = sum of swath lengths                       swath_length.cpp
     NSwathModified  cost = sum_edges |e| |sin(angle - angle(e))| / (2 op_width)
                     (fast approximation of NSwath, after Jin & Tang 2010)
4. Route planners (rp/):  genSortedSwaths = sort swaths by creation id, apply
   the start-point variant (bit 0: reverse list, bit 1: reverse first swath),
   sortSwaths, then reverseDirOddSwaths (each swath driven opposite to the
   previous one in the route).
     BoustrophedonOrder::sortSwaths   identity  (0, 1, 2, ...)
     SnakeOrder::sortSwaths           the exact std::rotate / std::reverse
                                      sequence of snake_order.cpp, giving
                                      0, 2, 4, ..., 5, 3, 1  (skip one swath)
5. Path planner  pp/PathPlanning::planPath(robot, swaths, turn): swath i is
   followed by turn.createTurn(end_i, out_angle_i, start_{i+1}, in_angle_{i+1}).
   With pp/DubinsCurves this is the shortest forward-only Dubins path
   (steering_functions Dubins_State_Space, kappa_max = 1/r_min); the 6 Dubins
   words LSL, RSR, LSR, RSL, RLR, LRL are solved in closed form here and every
   candidate is checked by forward propagation to the goal pose.

Adaptations to this problem (minimal, explicit)
------------------------------------------------
* Field / headland:  F2C runs on meta['polygon_enu'] (ENU metres) with
  headland width = core.Field's default 2*w, so the F2C inner cell is exactly
  core.Field.M (the main area that core.evaluate scores).
* Angles:  F2C angles are counter-clockwise from east (ENU x); core.Field uses
  heading_deg clockwise from north.  heading = (90 - deg(angle)) mod 360, and
  core.Field's operating frame (heading -> +x) equals F2C's rotated frame for
  that angle, so swath k of F2C sits at y_lo + (k + 1/2) op_width in core's frame.
* Width / overlap:  F2C uses a fixed operating (coverage) width.  We set
  op_width = w - overlap (implement width minus the fixed overlap).
* Swath placement used for EXECUTION:  placement='full' (default) uses
  core.plan(F, w, overlap/2, ConstSigma(1)), i.e. the same fixed spacing and the
  same first line as F2C, but it keeps the last line when the remaining strip
  is narrower than op_width/2.  F2C's generator drops that line (it lies
  outside the cell after clipping), leaving a boundary strip of up to
  op_width/2 uncovered, which core.evaluate would count as a miss in every run
  regardless of execution error.  placement='f2c' reproduces F2C exactly.
* Driving direction / start variant:  `variant` is F2C's genSortedSwaths
  variant (default 0, as in F2C).  Swaths::sort orients every swath towards
  increasing WORLD X before the variant is applied, so with variant 0 the first
  swath runs along -x of the field frame whenever the field's +x axis points
  west (local_variant() does this mapping; local=True takes a field-frame
  variant instead).  core.simulate always drives its first pass along +x and
  alternates; a route starting along -x is simulated on the same field
  operated at heading + 180 deg (lines y' = -y, same physical passes, same DEM
  and earth-fixed RTK) and mapped back (X = -X', D = -D').
* Path length:  swath = line clipped to the cell (F2C).  The closing pass that
  placement='full' adds beyond F2C's last line (its line lies just outside the
  cell) is given the along-track extent of the cell inside its coverage band,
  i.e. what must be driven to cover the strip F2C leaves.
* Turns are not executed by core.simulate (it models the straight passes);
  the Dubins turns enter only path/turn length, as in F2C's path planner.
  simulate_route hands core.simulate the passes in ROUTE order, so pass
  timing (earth-fixed RTK error, sequential passes) and driving direction
  follow the F2C route (Snake: spatial neighbours can share a direction).
* F2C's planPath(robot, swaths, turn) does not check that turns stay inside
  the field; path_length(detail=True) reports how many leave field.P.
* Dubins closed form (Shkel & Lumelsky style 6-word solution, with a 1e-9
  feasibility tolerance so tangent-circle solutions are not lost to rounding)
  is checked in selftest against an independent circle/tangent construction of
  all 6 words on random and headland-turn pose pairs (agreement < 1e-6 m).
* selftest uses common random run conditions for all rows of a field.
"""
import math
import time

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import LineString, Polygon

import core
import exp_lib

TWO_PI = 2.0 * math.pi
OBJECTIVES = ("n_swath", "swath_length", "n_swath_modified")


def _mod2pi(a):
    return a % TWO_PI


def heading_from_angle(angle_rad):
    """F2C swath angle (rad, CCW from east) -> core heading_deg (CW from north)."""
    return (90.0 - math.degrees(angle_rad)) % 360.0


def angle_from_heading(heading_deg):
    """core heading_deg (CW from north) -> F2C swath angle (rad, CCW from east)."""
    return _mod2pi(math.radians(90.0 - heading_deg))


# ------------------------------------------------------------------ headland
def no_headland_cell(meta, w=3.0, headland=None):
    """F2C ConstHL::generateHeadlands on the ENU field polygon.  headland
    defaults to core.Field's 2*w, so the result is core.Field.M in ENU."""
    H = 2 * w if headland is None else headland
    return Polygon(meta["polygon_enu"]).buffer(-H)


# ----------------------------------------------------------- swath generator
def swaths_at_angle(cell, angle_rad, op_width, allow_overlap=False):
    """F2C SwathGeneratorBase::generateSwaths.  Returns the list of swaths
    (shapely LineStrings, in the cell's coordinates) at the given angle."""
    if cell.is_empty or op_width <= 0:
        return []
    rot = affinity.rotate(cell, -angle_rad, origin=(0.0, 0.0), use_radians=True)
    minx, miny, maxx, maxy = rot.bounds
    height = maxy - miny
    offs, cy = [], -0.5 * op_width
    while height > cy + (0.0 if allow_overlap else 0.5 * op_width):
        cy += op_width
        offs.append(cy)
    lines = np.array([LineString([(minx - 1.0, miny + o), (maxx + 1.0, miny + o)]) for o in offs])
    lines = shapely.intersection(lines, rot) if len(lines) else lines
    out = []
    for g in lines:  # MultiLineString::append keeps only line geometries
        if g.is_empty:
            continue
        parts = [g] if g.geom_type == "LineString" else (list(g.geoms) if g.geom_type == "MultiLineString" else [])
        for p in parts:
            if p.length > 0:
                out.append(affinity.rotate(p, angle_rad, origin=(0.0, 0.0), use_radians=True))
    return out


def objective_cost(cell, angle_rad, op_width, objective="n_swath"):
    """Cost (minimised) of one angle under an F2C swath-generator objective."""
    if objective == "n_swath_modified":  # NSwathModified, fast path (no swaths)
        if cell.is_empty or op_width <= 0:
            return 0.0
        n_turns = 0.0
        polys = list(cell.geoms) if hasattr(cell, "geoms") else [cell]
        for ring in [r for q in polys for r in (q.exterior, *q.interiors)]:
            c = np.asarray(ring.coords)
            d = c - np.roll(c, 1, axis=0)
            n_turns += np.sum(np.hypot(d[:, 0], d[:, 1]) * np.abs(np.sin(angle_rad - np.arctan2(d[:, 1], d[:, 0]))))
        return float(n_turns / (2.0 * op_width))
    sw = swaths_at_angle(cell, angle_rad, op_width)
    if objective == "n_swath":
        return float(len(sw))
    if objective == "swath_length":
        return float(sum(s.length for s in sw))
    raise ValueError(f"objective must be one of {OBJECTIVES}")


def brute_force_angle(cell, op_width, objective="n_swath", step_angle=math.radians(1.0)):
    """F2C BruteForce::computeBestAngle (+ generateBestSwaths fallback).
    Returns (best_angle_rad, angles, costs)."""
    n = int(TWO_PI / step_angle)
    angles = np.arange(n) * step_angle
    costs = np.array([objective_cost(cell, a, op_width, objective) for a in angles])
    best = float(angles[int(np.argmin(costs))])  # first minimum, as std::min_element
    if not swaths_at_angle(cell, best, op_width):
        for i in range(1, 8):
            if swaths_at_angle(cell, best + i * math.pi / 8, op_width):
                best = _mod2pi(best + i * math.pi / 8)
                break
    return best, angles, costs


def best_heading(meta, w=3.0, objective="n_swath", step_deg=1.0, overlap=0.0, headland=None,
                 return_info=False):
    """F2C-optimal operating heading of a field.

    meta      field record (core.Field meta; uses meta['polygon_enu'], ENU m)
    w         implement width [m]; op_width = w - overlap.  Pass the SAME
              overlap as the swaths that will be planned (F2C searches the
              angle with the coverage width it then uses); default 0.0
    objective 'n_swath' (NSwath) | 'swath_length' (SwathLength) | 'n_swath_modified'
    step_deg  BruteForce step angle (F2C default: 1 degree)
    Returns heading_deg (clockwise from north, as core.Field expects); with
    return_info=True also a dict (angle_rad, angles, costs, n_ties, cell).
    """
    cell = no_headland_cell(meta, w, headland)
    op = w - overlap
    a, angles, costs = brute_force_angle(cell, op, objective, math.radians(step_deg))
    h = heading_from_angle(a)
    if not return_info:
        return h
    return h, dict(angle_rad=a, angles=angles, costs=costs, cell=cell, op_width=op,
                   n_ties=int(np.sum(np.isclose(costs, costs.min()))))


def make_field(fid, meta, heading_deg, w=3.0, headland=None):
    """core.Field of the same real field operated along heading_deg."""
    return core.Field(fid, dict(meta, heading_deg=float(heading_deg)), headland=headland, w=w)


def plan_swaths(field, w=3.0, overlap=0.1, placement="full"):
    """Lateral swath centres ys (field frame) at fixed spacing w - overlap.
    'full': core.plan(F, w, overlap/2, ConstSigma(1)) (closes the boundary strip);
    'f2c' : exactly F2C generateSwaths on the inner cell (may leave a strip of
            up to (w-overlap)/2 at the far side uncovered)."""
    ys = core.plan(field, w, overlap / 2.0, exp_lib.ConstSigma(1.0))
    if placement == "full":
        return ys
    if placement == "f2c":
        sw = swaths_at_angle(field.M, 0.0, w - overlap)
        return np.array(sorted({round(s.coords[0][1], 9) for s in sw}))
    raise ValueError("placement must be 'full' or 'f2c'")


# -------------------------------------------------------------- route planner
def _snake_sort(idx):
    """Literal port of f2c::rp::SnakeOrder::sortSwaths (std::rotate/reverse)."""
    s = list(idx)
    n = len(s)
    if n <= 2:
        return s
    i = 1
    while i < (n - 1) // 2 + 1:
        s[i:] = s[i + 1:] + s[i:i + 1]  # std::rotate(begin+i, begin+i+1, end)
        i += 1
    s[i + 1:] = s[i + 1:][::-1]  # std::reverse(begin+i+1, end)
    if n % 2 == 1:
        s[i:] = s[i + 1:] + s[i:i + 1]
    return s


def route_order(ys, order="boustrophedon", variant=0):
    """F2C SingleCellSwathsOrderBase::genSortedSwaths on swaths sorted by
    lateral position.  ys: swath centres (or an int number of swaths).
    Returns the spatial indices in visiting order (np.int array)."""
    n = ys if isinstance(ys, (int, np.integer)) else len(ys)
    idx = list(range(n))
    if variant & 1:
        idx = idx[::-1]
    if order == "boustrophedon":
        pass
    elif order == "snake":
        idx = _snake_sort(idx)
    else:
        raise ValueError("order must be 'boustrophedon' or 'snake'")
    return np.asarray(idx, dtype=int)


def route_dirs(n, variant=0):
    """Driving direction (+1 = +x of the operating frame) of route position i
    for a LOCAL variant (bit 1: first route swath driven along -x); see
    local_variant() for F2C's own (world-frame) variants."""
    s0 = -1.0 if variant & 2 else 1.0
    return s0 * np.where(np.arange(n) % 2 == 0, 1.0, -1.0)


def local_variant(field, variant=0):
    """F2C start variant -> local variant of this module.

    F2C genSortedSwaths first calls Swaths::sort, which orients EVERY swath
    towards increasing world X (ties: increasing world Y), then bit 0 reverses
    the swath list and bit 1 reverses the first swath.  So with F2C's default
    variant 0 the first swath is driven along -x of the field frame whenever the
    field's +x axis points west.  Local bit 1 = first route swath along -x."""
    h = math.radians(field.meta["heading_deg"])
    east, north = math.sin(h), math.cos(h)  # world direction of the field's +x axis
    plus_x_increasing = east > 1e-9 or (abs(east) <= 1e-9 and north > 0)
    return int(variant) ^ (0 if plus_x_increasing else 2)


def _mirrored(field):
    """The same field operated along heading + 180 deg (frame rotated by pi:
    x' = -x, y' = -y), cached on the field object."""
    fm = getattr(field, "_f2c_mirror", None)
    if fm is None:
        meta = dict(field.meta, heading_deg=(field.meta["heading_deg"] + 180.0) % 360.0)
        fm = core.Field(field.fid, meta, headland=field.H)
        field._f2c_mirror = fm
    return fm


# ----------------------------------------------------------- Dubins (forward)
_EPS = 1e-9  # feasibility tolerance of the closed-form Dubins words (candidates are re-checked by propagation)


def _dubins_candidates(alpha, beta, d):
    sa, sb, ca, cb = math.sin(alpha), math.sin(beta), math.cos(alpha), math.cos(beta)
    cab = math.cos(alpha - beta)
    out = []
    p2 = 2 + d * d - 2 * cab + 2 * d * (sa - sb)  # LSL
    if p2 >= -_EPS:
        if p2 < 1e-14:  # straight part vanishes: single left arc (atan2(0, 0) undefined)
            out.append(("LSL", _mod2pi(beta - alpha), 0.0, 0.0))
        else:
            t1 = math.atan2(cb - ca, d + sa - sb)
            out.append(("LSL", _mod2pi(-alpha + t1), math.sqrt(p2), _mod2pi(beta - t1)))
    p2 = 2 + d * d - 2 * cab + 2 * d * (sb - sa)  # RSR
    if p2 >= -_EPS:
        if p2 < 1e-14:  # single right arc
            out.append(("RSR", _mod2pi(alpha - beta), 0.0, 0.0))
        else:
            t1 = math.atan2(ca - cb, d - sa + sb)
            out.append(("RSR", _mod2pi(alpha - t1), math.sqrt(p2), _mod2pi(-beta + t1)))
    p2 = -2 + d * d + 2 * cab + 2 * d * (sa + sb)  # LSR
    if p2 >= -_EPS:  # tolerance: tangent circles (p = 0) must not be lost to rounding
        p = math.sqrt(max(p2, 0.0))
        t2 = math.atan2(-ca - cb, d + sa + sb) - math.atan2(-2.0, p)
        out.append(("LSR", _mod2pi(-alpha + t2), p, _mod2pi(-beta + t2)))
    p2 = -2 + d * d + 2 * cab - 2 * d * (sa + sb)  # RSL
    if p2 >= -_EPS:
        p = math.sqrt(max(p2, 0.0))
        t2 = math.atan2(ca + cb, d - sa - sb) - math.atan2(2.0, p)
        out.append(("RSL", _mod2pi(alpha - t2), p, _mod2pi(beta - t2)))
    tmp = (6 - d * d + 2 * cab + 2 * d * (sa - sb)) / 8  # RLR
    if abs(tmp) <= 1 + _EPS:
        p = _mod2pi(TWO_PI - math.acos(min(1.0, max(-1.0, tmp))))
        t = _mod2pi(alpha - math.atan2(ca - cb, d - sa + sb) + p / 2)
        out.append(("RLR", t, p, _mod2pi(alpha - beta - t + p)))
    tmp = (6 - d * d + 2 * cab + 2 * d * (sb - sa)) / 8  # LRL
    if abs(tmp) <= 1 + _EPS:
        p = _mod2pi(TWO_PI - math.acos(min(1.0, max(-1.0, tmp))))
        t = _mod2pi(-alpha - math.atan2(ca - cb, d + sa - sb) + p / 2)
        out.append(("LRL", t, p, _mod2pi(beta - alpha - t + p)))
    return out


def _dubins_propagate(q0, word, params, r):
    x, y, th = q0
    for c, s in zip(word, params):
        if c == "S":
            x += r * s * math.cos(th)
            y += r * s * math.sin(th)
        elif c == "L":
            x += r * (math.sin(th + s) - math.sin(th))
            y += r * (-math.cos(th + s) + math.cos(th))
            th += s
        else:
            x += r * (-math.sin(th - s) + math.sin(th))
            y += r * (math.cos(th - s) - math.cos(th))
            th -= s
    return x, y, th


def dubins_shortest(q0, q1, r):
    """Shortest forward Dubins path between poses q = (x, y, theta) with
    minimum turning radius r.  Returns (length, word, (t, p, q)) with t, p, q
    the normalised segment lengths (length = r * (t + p + q))."""
    dx, dy = q1[0] - q0[0], q1[1] - q0[1]
    D = math.hypot(dx, dy)
    phi = math.atan2(dy, dx) if D > 1e-12 else 0.0
    alpha, beta = _mod2pi(q0[2] - phi), _mod2pi(q1[2] - phi)
    best = (math.inf, None, None)
    tol = 1e-6 * max(1.0, D, r)
    for word, t, p, q in _dubins_candidates(alpha, beta, D / r):
        L = r * (t + p + q)
        if L >= best[0]:
            continue
        xe, ye, te = _dubins_propagate(q0, word, (t, p, q), r)
        dth = abs((te - q1[2] + math.pi) % TWO_PI - math.pi)
        if math.hypot(xe - q1[0], ye - q1[1]) < 1e-4 * max(1.0, D) + tol and dth < 1e-6:
            best = (L, word, (t, p, q))
    return best


def dubins_points(q0, word, params, r, step=0.25):
    """Sample a Dubins path (as returned by dubins_shortest) every ~step m."""
    pts, q = [q0[:2]], tuple(q0)
    for c, s in zip(word, params):
        n = max(1, int(math.ceil(r * s / step)))
        for j in range(1, n + 1):
            pts.append(_dubins_propagate(q, c, (s * j / n,), r)[:2])
        q = _dubins_propagate(q, c, (s,), r)
    return np.asarray(pts)


# ---------------------------------------------------------------- path length
def _swath_ends(field, y, half):
    """Along-track extent (x0, x1) of the swath at lateral position y.

    F2C's swath is the line clipped to the inner cell M (field.M).  A closing
    pass of placement='full' whose line lies just outside M (F2C itself drops
    it) has no such clip, but it must still span the part of M inside its
    coverage band [y - half, y + half]; that x-extent is used (clipping the line
    onto M's tip instead would give a ~0 m swath and under-count the path)."""
    c = field.chord(field.M, float(y))
    if c is not None:
        return c
    minx, _, maxx, _ = field.M.bounds
    band = field.M.intersection(shapely.box(minx - 1.0, y - half, maxx + 1.0, y + half))
    if not band.is_empty:
        b = band.bounds
        return b[0], b[2]
    c = field.chord(field.P, float(y))
    if c is None:
        raise ValueError(f"swath at y={y:.3f} does not intersect the field")
    return c


def _check_ascending(ys):
    ys = np.asarray(ys, float)
    if len(ys) > 1 and not np.all(np.diff(ys) > 0):
        raise ValueError("ys must be strictly ascending (spatial order, as returned by plan_swaths)")
    return ys


def path_length(field, ys, order="boustrophedon", r_min=4.5, variant=0, detail=False, local=False):
    """F2C PathPlanning::planPath(robot, swaths, DubinsCurves) length.

    variant is F2C's genSortedSwaths start variant (0..3, default 0 as in F2C);
    local=True interprets it in the field frame instead (see local_variant).

    Swaths are the chords of the inner cell field.M at ys (F2C clips swaths to
    the no-headland cell); consecutive route swaths are joined by the shortest
    forward Dubins path of radius r_min between swath end and next swath start.
    Returns the total length [m], or with detail=True a dict with total, swath,
    turn (lengths, m), n_swaths, n_turns, mean_turn, the Dubins word counts,
    turns_outside_field (turns leaving field.P, which F2C does not check) and
    max_outside_m (largest excursion beyond the field boundary)."""
    ys = _check_ascending(ys)
    lv = int(variant) if local else local_variant(field, variant)
    perm, dirs = route_order(ys, order, lv), route_dirs(len(ys), lv)
    gaps = np.diff(ys)
    # half coverage band of each swath (half the distance to its nearest neighbour)
    half = (0.5 * np.minimum(np.r_[np.inf, gaps], np.r_[gaps, np.inf]) if len(ys) > 1
            else np.full(len(ys), 0.5 * (field.M.bounds[3] - field.M.bounds[1])))
    starts, ends, sw_len = [], [], 0.0
    for k, s in zip(perm, dirs):
        x0, x1 = _swath_ends(field, ys[k], half[k])
        sw_len += x1 - x0
        th = 0.0 if s > 0 else math.pi
        a, b = (x0, x1) if s > 0 else (x1, x0)
        starts.append((a, ys[k], th))
        ends.append((b, ys[k], th))
    turn, words, n_out, max_out = 0.0, {}, 0, 0.0
    for i in range(len(perm) - 1):
        L, word, prm = dubins_shortest(ends[i], starts[i + 1], r_min)
        turn += L
        words[word] = words.get(word, 0) + 1
        if detail:  # does the turn stay inside the field boundary (headland)?
            pts = dubins_points(ends[i], word, prm, r_min)
            out = ~shapely.contains_xy(field.P, pts[:, 0], pts[:, 1])
            if out.any():
                n_out += 1
                max_out = max(max_out, float(shapely.distance(
                    field.P, shapely.points(pts[out])).max()))
    if not detail:
        return sw_len + turn
    nt = max(len(perm) - 1, 0)
    return dict(total=sw_len + turn, swath=sw_len, turn=turn, n_swaths=len(perm), n_turns=nt,
                mean_turn=turn / nt if nt else 0.0, words=words,
                turns_outside_field=n_out, max_outside_m=max_out)


# ------------------------------------------------------- execution / evaluation
def simulate_route(field, ys, cond, rng, order="boustrophedon", ctrl="lqr_i", variant=0, local=False):
    """core.simulate with the passes driven in F2C route order and direction
    (route position i opposite to i-1, reverseDirOddSwaths), with pass timing
    (earth-fixed RTK error, sequential passes) following the route.
    variant: F2C start variant (local=True: field-frame variant, see local_variant).
    core.simulate always drives its first pass along +x; a route whose first
    swath runs along -x is simulated on the same field rotated by 180 deg
    (heading + 180, lines y' = -y) and mapped back (X = -X', D = -D').
    Returns X, D in SPATIAL order of ys (ascending, field frame of `field`), so
    core.evaluate / core.pair_scores / exp_lib helpers apply unchanged."""
    ys = _check_ascending(ys)
    lv = int(variant) if local else local_variant(field, variant)
    perm = route_order(ys, order, lv)
    if lv & 2:
        Xm, Dm = core.simulate(_mirrored(field), -ys[perm], cond, rng, ctrl=ctrl)
        X, D = [-x for x in Xm], [-d for d in Dm]
    else:
        X, D = core.simulate(field, ys[perm], cond, rng, ctrl=ctrl)
    inv = np.argsort(perm)
    return [X[i] for i in inv], [D[i] for i in inv]


def evaluate_route(field, ys, n, rng, w=3.0, order="boustrophedon", ctrl="lqr_i", r_min=4.5,
                   variant=0, local=False, **cond_kw):
    """Monte-Carlo execution of an F2C plan: P(no miss), E[miss], p95 miss,
    planned overlap ratio and the F2C path/turn length (variant as in
    simulate_route / path_length)."""
    cond = core.Condition(rng, n, **cond_kw)
    X, D = simulate_route(field, ys, cond, rng, order=order, ctrl=ctrl, variant=variant, local=local)
    miss = core.evaluate(field, np.asarray(ys, float), X, D, w)
    pl = path_length(field, ys, order, r_min, variant, detail=True, local=local)
    return dict(p_nomiss=float(np.mean(miss == 0)), e_miss=float(miss.mean()),
                p95_miss=float(np.percentile(miss, 95)), passes=len(ys),
                overlap=exp_lib.overlap_ratio(field, ys, w), path=pl["total"], turn=pl["turn"],
                turns_outside=pl["turns_outside_field"], max_outside_m=pl["max_outside_m"])


def f2c_plan(fid, meta, w=3.0, overlap=0.1, objective="n_swath", order="boustrophedon", r_min=4.5,
             step_deg=1.0, placement="full", heading_deg=None):
    """Complete F2C pipeline on one field: ConstHL -> BruteForce(objective) ->
    fixed-width swaths -> Boustrophedon/Snake route -> Dubins path.
    heading_deg=None searches the F2C-optimal heading; otherwise uses it.
    Returns dict(field, heading_deg, ys, route, path)."""
    h = best_heading(meta, w, objective, step_deg, overlap) if heading_deg is None else heading_deg
    F = make_field(fid, meta, h, w)
    ys = plan_swaths(F, w, overlap, placement)
    return dict(field=F, heading_deg=h, ys=ys, route=route_order(ys, order),
                path=path_length(F, ys, order, r_min, detail=True))


# -------------------------------------------------------------------- selftest
def _dubins_geometric(q0, q1, r):
    """Independent reference (selftest only): shortest forward Dubins length from
    explicit circle-centre / tangent geometry of the 6 words (both CCC branches)."""
    md = _mod2pi
    cL = lambda q: np.array([q[0] - r * math.sin(q[2]), q[1] + r * math.cos(q[2])])
    cR = lambda q: np.array([q[0] + r * math.sin(q[2]), q[1] - r * math.cos(q[2])])
    t0, t1, out = q0[2], q1[2], []
    for f, sg in ((cL, 1.0), (cR, -1.0)):  # LSL, RSR (outer tangent)
        v = f(q1) - f(q0)
        D = math.hypot(*v)
        ps = math.atan2(v[1], v[0]) if D > 1e-12 else t0
        out.append(r * (md(sg * (ps - t0)) + md(sg * (t1 - ps))) + D)
    for f0, f1, sg in ((cL, cR, 1.0), (cR, cL, -1.0)):  # LSR, RSL (inner tangent)
        v = f1(q1) - f0(q0)
        D = math.hypot(*v)
        if D >= 2 * r - 1e-12:
            l = math.sqrt(max(D * D - 4 * r * r, 0.0))
            ps = math.atan2(v[1], v[0]) + sg * math.atan2(2 * r, l)
            out.append(r * (md(sg * (ps - t0)) + md(sg * (ps - t1))) + l)
    for f, sg in ((cR, -1.0), (cL, 1.0)):  # RLR, LRL
        c1, c3 = f(q0), f(q1)
        v = c3 - c1
        D = math.hypot(*v)
        if 1e-12 < D <= 4 * r:
            h, n = math.sqrt(max(4 * r * r - D * D / 4, 0.0)), np.array([-v[1], v[0]]) / D
            for side in (1.0, -1.0):
                c2 = (c1 + c3) / 2 + side * h * n
                u1, u2 = (c2 - c1) / 2, (c2 - c3) / 2  # tangent points relative to c1, c3
                if sg > 0:  # LRL: on a left circle the heading at offset u is atan2(u_x, -u_y)
                    p1, p2 = math.atan2(u1[0], -u1[1]), math.atan2(u2[0], -u2[1])
                    out.append(r * (md(p1 - t0) + md(p1 - p2) + md(t1 - p2)))
                else:       # RLR: on a right circle it is atan2(-u_x, u_y)
                    p1, p2 = math.atan2(-u1[0], u1[1]), math.atan2(-u2[0], u2[1])
                    out.append(r * (md(t0 - p1) + md(p2 - p1) + md(p2 - t1)))
    return min(out)


def _check_dubins():
    r = 4.5
    # quarter / half circles and straight line have closed-form lengths; the
    # last case (tangent circles, LSR with an empty straight) was lost to
    # rounding before the feasibility tolerance _EPS was added
    cases = [((0, 0, 0), (10, 0, 0), 10.0), ((0, 0, 0), (0, 2 * r, math.pi), math.pi * r),
             ((0, 0, 0), (r, r, math.pi / 2), math.pi * r / 2),
             ((0, 0, 0), (0, 3 * r, math.pi), math.pi * r + r),
             ((0, 0, 0), (2 * r, 2 * r, 0.0), math.pi * r)]
    for q0, q1, L in cases:
        assert abs(dubins_shortest(q0, q1, r)[0] - L) < 1e-6, (q0, q1)
    rng = np.random.default_rng(1)
    for _ in range(200):  # every returned path must reach the goal pose
        q0 = tuple(rng.uniform(-20, 20, 2)) + (rng.uniform(0, TWO_PI),)
        q1 = tuple(rng.uniform(-20, 20, 2)) + (rng.uniform(0, TWO_PI),)
        L, word, prm = dubins_shortest(q0, q1, r)
        assert np.isfinite(L) and L >= math.hypot(q1[0] - q0[0], q1[1] - q0[1]) - 1e-9
        xe, ye, _ = _dubins_propagate(q0, word, prm, r)
        assert math.hypot(xe - q1[0], ye - q1[1]) < 1e-6
        assert abs(L - _dubins_geometric(q0, q1, r)) < 1e-6, (q0, q1)
    for dy in (0.5, 2.9, 5.8, 2 * r, 12.0, 4 * r):  # headland U-turns (both sides, shifted ends)
        for dx in (-8.0, -2.0, 0.0, 3.0, 8.0):
            for q1 in ((dx, dy, math.pi), (dx, -dy, math.pi), (dx, dy, 0.0)):
                L = dubins_shortest((0.0, 0.0, 0.0), q1, r)[0]
                assert abs(L - _dubins_geometric((0.0, 0.0, 0.0), q1, r)) < 1e-6, q1


def selftest(n_runs=50, n_fields=2, w=3.0, overlap=0.10, r_min=4.5, seed=0):
    """Recorded heading vs F2C-optimal heading on real paddy fields:
    #swaths, path/turn length (Boustrophedon & Snake, Dubins r_min), and
    simulated P(no miss) / overlap with 10 cm fixed overlap (lqr_i autosteer)."""
    t_all = time.time()
    _check_dubins()
    assert _snake_sort(range(6)) == [0, 2, 4, 5, 3, 1] and _snake_sort(range(7)) == [0, 2, 4, 6, 5, 3, 1]
    fields = core.load_fields("paddy", w=w, seed=0)[:n_fields]
    op = w - overlap
    print(f"F2C baseline selftest: w={w} m, overlap={overlap} m (op_width={op:.2f}), headland=2w, "
          f"r_min={r_min} m, runs={n_runs}, ctrl=lqr_i, placement='full' unless noted, "
          f"common random conditions across rows of a field")
    hdr = (f"  {'heading':>17s} {'deg':>5s} {'NSw':>4s} {'pass':>4s} {'strip':>5s} {'order':>6s} {'dir0':>4s} "
           f"{'path_m':>7s} {'turn_m':>7s} {'out':>6s} {'P(nm)':>5s} {'E[miss]':>8s} {'ovl':>5s} {'t_s':>4s}")

    def row(name, F, n_f2c, npass, strip, order, m, dt):
        d0 = "-x" if local_variant(F, 0) & 2 else "+x"
        print(f"  {name:>17s} {F.meta['heading_deg']:5.0f} {n_f2c:4d} {npass:4d} {strip:5.2f} {order[:6]:>6s} "
              f"{d0:>4s} {m['path']:7.0f} {m['turn']:7.0f} {m['turns_outside']:3d}/{m['max_outside_m']:<2.0f} "
              f"{m['p_nomiss']:5.2f} {m['e_miss']:8.5f} {m['overlap']:5.3f} {dt:4.1f}")

    # mirrored execution (route starting along -x) must reproduce the same physical offsets:
    # slope-only conditions (no RTK / mount error, no roll compensation) -> uphill drag ~ h_ant * gy
    Fc = max(fields, key=lambda f: f.z_mean_slope)
    ys_c = plan_swaths(Fc, w, overlap)
    mu = []
    for lv in (0, 2):
        rng = np.random.default_rng(seed)
        cond = core.Condition(rng, 10, comp=0.0, rtk_scale=0.0, mount_sd=0.0)
        X, D = simulate_route(Fc, ys_c, cond, rng, variant=lv, local=True)
        mu.append(np.array([d[:, 10:].mean() for d in D]))
    Fm = _mirrored(Fc)  # same physical pass lines: chord(P', -y) = -chord(P, y)
    assert all(np.allclose(Fm.chord(Fm.P, -y), [-c for c in Fc.chord(Fc.P, y)[::-1]], atol=1e-6) for y in ys_c)
    gy = np.array([np.mean(Fc.gy(np.linspace(*Fc.chord(Fc.P, y), 30), np.full(30, y))) for y in ys_c])
    c0, c2, c02 = np.corrcoef(mu[0], gy)[0, 1], np.corrcoef(mu[1], gy)[0, 1], np.corrcoef(mu[0], mu[1])[0, 1]
    assert c0 > 0.5 and c2 > 0.5 and c02 > 0.5, (c0, c2, c02)
    print(f"mirror check (field {Fc.fid}, slope-only): corr(offset, gy) start +x {c0:.2f} / start -x {c2:.2f}, "
          f"corr between the two {c02:.2f}")

    for F0 in fields:
        meta = F0.meta
        t0 = time.time()
        h_ns, info = best_heading(meta, w, "n_swath", 1.0, overlap, return_info=True)
        t_bf = time.time() - t0
        h_sl = best_heading(meta, w, "swath_length", 1.0, overlap)
        print(f"\nfield {F0.fid}: area {F0.P.area:.0f} m2, main area {F0.M.area:.0f} m2, mean slope "
              f"{F0.z_mean_slope:.2f} deg | BruteForce(NSwath) over 360 angles: {t_bf:.2f} s, "
              f"min NSwath = {info['costs'].min():.0f} at {info['n_ties']} tied angles")
        print(hdr)
        for name, h in (("recorded", meta["heading_deg"]), ("F2C NSwath", h_ns), ("F2C SwathLength", h_sl)):
            F = make_field(F0.fid, meta, h, w)
            n_f2c = len(swaths_at_angle(info["cell"], angle_from_heading(h), op))
            ys = plan_swaths(F, w, overlap, "full")
            ys_f2c = plan_swaths(F, w, overlap, "f2c")
            lo, hi = F.lateral_range()
            strip = max(0.0, hi - (ys_f2c[-1] + op / 2)) if len(ys_f2c) else hi - lo
            # F2C's lines coincide with core.plan's; NSwath counts clipped parts (> lines if non-convex)
            assert np.allclose(ys_f2c, ys[:len(ys_f2c)]) and n_f2c >= len(ys_f2c)
            for order in ("boustrophedon", "snake"):
                t1 = time.time()
                rng = np.random.default_rng([seed, F0.fid])  # same run conditions for every row
                m = evaluate_route(F, ys, n_runs, rng, w=w, order=order, r_min=r_min)
                row(name, F, n_f2c, len(ys), strip, order, m, time.time() - t1)
            if name == "F2C NSwath":  # exact F2C swath set (last line dropped by the generator)
                t1 = time.time()
                rng = np.random.default_rng([seed, F0.fid])
                m = evaluate_route(F, ys_f2c, n_runs, rng, w=w, order="boustrophedon", r_min=r_min)
                row("NSwath f2c-exact", F, n_f2c, len(ys_f2c), strip, "boustrophedon", m, time.time() - t1)
    print("\nNSw = F2C NSwath cost at that heading; pass = executed passes; strip = boundary strip F2C's own "
          "generator leaves uncovered [m]; dir0 = field-frame direction of the first swath under F2C's default "
          "variant 0 (towards increasing world X); out = turns leaving the field polygon / max excursion [m]; "
          "P(nm) = P(no miss) of the main area; ovl = planned overlap ratio; t_s = sim+eval seconds.")
    print(f"total selftest runtime {time.time() - t_all:.1f} s")

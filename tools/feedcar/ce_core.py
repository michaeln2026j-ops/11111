# -*- coding: utf-8 -*-
"""Core of the feed-car certification tools (no ROS, Python 2.7 and 3 compatible, pure Python).

Route:        the taught route (~/routes/<name>.yaml), polyline of (x, y) in the map frame.
project():    signed lateral error e (left of the travel direction positive) and arc length s of a point,
              searched in a window around the previous match (as route_follow's `win`), so the two
              sides of a closed loop that pass close to each other are never confused.
RunRecorder:  splits the pose stream into runs (one traversal of the route; a closed loop wraps from the
              end of the route back to its start) and hands every finished run to a writer.
"""
from __future__ import division, print_function

import math


def _pts_from_yaml_obj(obj):
    """Accept the common layouts: a list of {x, y, ...} / [x, y, ...], or a dict holding such a list
    under one of the usual keys. Raises ValueError with the keys found otherwise."""
    if isinstance(obj, dict):
        for k in ("points", "poses", "waypoints", "route", "path", "data"):
            if k in obj:
                return _pts_from_yaml_obj(obj[k])
        raise ValueError("route yaml: no point list found, top-level keys: %s" % sorted(obj.keys()))
    pts = []
    for p in obj:
        if isinstance(p, dict):
            if "x" in p and "y" in p:
                pts.append((float(p["x"]), float(p["y"])))
            elif "position" in p:
                pts.append((float(p["position"]["x"]), float(p["position"]["y"])))
            elif "pose" in p:
                q = p["pose"].get("position", p["pose"])
                pts.append((float(q["x"]), float(q["y"])))
            else:
                raise ValueError("route yaml: point without x/y, keys: %s" % sorted(p.keys()))
        else:
            pts.append((float(p[0]), float(p[1])))
    if len(pts) < 2:
        raise ValueError("route yaml: fewer than 2 points")
    return pts


def load_route(path, closed_tol=1.0):
    import yaml
    with open(path) as f:
        obj = yaml.safe_load(f)
    return Route(_pts_from_yaml_obj(obj), closed_tol=closed_tol)


class Route(object):
    def __init__(self, pts, closed_tol=1.0):
        # drop repeated points (zero-length segments)
        clean = [pts[0]]
        for p in pts[1:]:
            if math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1e-6:
                clean.append(p)
        self.closed = math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) < closed_tol
        if self.closed and math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) > 1e-6:
            clean.append(clean[0])  # close the loop with one segment
        self.p = clean
        self.n_seg = len(clean) - 1
        self.s0 = [0.0]
        for i in range(self.n_seg):
            self.s0.append(self.s0[-1] + self._seglen(i))
        self.length = self.s0[-1]

    def _seglen(self, i):
        a, b = self.p[i], self.p[i + 1]
        return math.hypot(b[0] - a[0], b[1] - a[1])

    def _proj_seg(self, i, x, y):
        (ax, ay), (bx, by) = self.p[i], self.p[i + 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = ((x - ax) * dx + (y - ay) * dy) / L2
        t = min(1.0, max(0.0, t))
        qx, qy = ax + t * dx, ay + t * dy
        d = math.hypot(x - qx, y - qy)
        cross = dx * (y - ay) - dy * (x - ax)
        return d, (1.0 if cross >= 0 else -1.0) * d, self.s0[i] + t * math.sqrt(L2)

    def project(self, x, y, hint=None, win=40):
        """Returns (segment index, s, signed lateral error e). hint=None: global search."""
        if hint is None:
            cand = range(self.n_seg)
        elif self.closed:
            cand = [(hint + k) % self.n_seg for k in range(-win, win + 1)]
        else:
            cand = range(max(0, hint - win), min(self.n_seg, hint + win + 1))
        best = None
        for i in cand:
            d, e, s = self._proj_seg(i, x, y)
            if best is None or d < best[0]:
                best = (d, i, s, e)
        return best[1], best[2], best[3]


class RunRecorder(object):
    """Feed samples (t, x, y, yaw, v, scan_d); a run is closed when the matched arc length wraps from the
    last 20 % of the route to its first 20 % (next lap of a loop, or the next single-pass run), or on
    finish(). writer(run_index, rows, complete) receives the rows (t, s, e, x, y, yaw, v, scan_d);
    complete = the run covered at least `min_cover` of the route length."""

    def __init__(self, route, writer, win=40, offset=(0.0, 0.0), min_cover=0.95, max_jump=2.0):
        self.r, self.writer, self.win = route, writer, win
        self.dx, self.dy = offset
        self.min_cover, self.max_jump = min_cover, max_jump
        self.hint, self.rows, self.k, self.s_prev = None, [], 0, None
        self.n_lost = 0

    def feed(self, t, x, y, yaw, v=float("nan"), scan_d=float("nan")):
        # measured point = dispenser outlet (offset in the vehicle frame), default the base_link origin
        px = x + self.dx * math.cos(yaw) - self.dy * math.sin(yaw)
        py = y + self.dx * math.sin(yaw) + self.dy * math.cos(yaw)
        i, s, e = self.r.project(px, py, self.hint, self.win)
        if self.hint is not None and abs(e) > self.max_jump:  # lost the local match (e.g. relocalisation)
            i, s, e = self.r.project(px, py, None)
            self.n_lost += 1
        self.hint = i
        L = self.r.length
        if self.s_prev is not None and self.s_prev > 0.8 * L and s < 0.2 * L:
            self._flush()
        self.rows.append((t, s, e, px, py, yaw, v, scan_d))
        self.s_prev = s

    def _flush(self):
        if self.rows:
            ss = [r[1] for r in self.rows]
            cover = (max(ss) - min(ss)) / self.r.length
            self.writer(self.k, self.rows, cover >= self.min_cover)
            self.k += 1
        self.rows = []

    def finish(self):
        self._flush()

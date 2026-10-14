# -*- coding: utf-8 -*-
"""Offline test of the feed-car tools on a synthetic closed route (no ROS needed).

    python3 tools/feedcar/test_feedcar.py
"""
from __future__ import division, print_function

import math
import os
import shutil
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ce_certify as C  # noqa: E402
from ce_core import Route, RunRecorder, _pts_from_yaml_obj  # noqa: E402


def stadium(L=30.0, R=6.0, ds=0.3):
    """Closed loop: two straights of length L joined by half circles of radius R, counter-clockwise."""
    pts = []
    for x in np.arange(0, L, ds):
        pts.append((x, 0.0))
    for a in np.arange(-math.pi / 2, math.pi / 2, ds / R):
        pts.append((L + R * math.cos(a), R + R * math.sin(a)))
    for x in np.arange(L, 0, -ds):
        pts.append((x, 2 * R))
    for a in np.arange(math.pi / 2, 3 * math.pi / 2, ds / R):
        pts.append((R * math.cos(a), R + R * math.sin(a)))
    pts.append(pts[0])
    return pts


def main():
    rng = np.random.default_rng(1)
    # yaml layouts and projection sign
    assert _pts_from_yaml_obj({"points": [{"x": 0, "y": 0}, {"x": 1, "y": 0}]}) == [(0.0, 0.0), (1.0, 0.0)]
    assert _pts_from_yaml_obj([[0, 0, 0.1], [2, 0, 0.1]])[1] == (2.0, 0.0)
    r = Route([(0, 0), (10, 0)])
    assert not r.closed and abs(r.project(5, 0.3)[2] - 0.3) < 1e-12 and abs(r.project(5, -0.2)[2] + 0.2) < 1e-12
    route = Route(stadium())
    assert route.closed, "stadium must be detected as a closed loop"
    print("route length %.1f m, %d segments" % (route.length, route.n_seg))
    # order statistic agrees with the experiment code (ceplus.quantile)
    sys.path.insert(0, os.path.join(HERE, "..", "..", "experiments"))
    try:
        import ceplus as CP
        for n in (9, 15, 22, 30, 57):
            x = rng.random(n)
            for dl in (None, 0.1):
                a, b = C.bound(x, 0.1, dl), CP.quantile(x, 0.1, dl)
                assert (not np.isfinite(a) and not np.isfinite(b)) or abs(a - b) < 1e-12, (n, dl, a, b)
        print("order statistics agree with experiments/ceplus.quantile")
    except ImportError:
        print("(experiments/ not importable, order-statistic cross-check skipped)")
    # simulate laps: lateral error = AR(1) along s with a per-lap scale (conditions vary between laps)
    out = tempfile.mkdtemp()
    written = []

    def writer(k, rows, complete):
        fn = os.path.join(out, "run_test_%03d%s.csv" % (k, "" if complete else "_partial"))
        with open(fn, "w") as f:
            f.write("t,s,e,x,y,yaw,v,scan_d\n")
            for row in rows:
                f.write(",".join("%.5f" % v for v in row) + "\n")
        written.append((k, complete, max(abs(row[2]) for row in rows)))

    rec = RunRecorder(route, writer)
    n_laps, ds = 41, 0.2
    true_max = []
    t = 0.0
    s_start = 0.37 * route.length  # the logger starts mid-route: first run is partial
    for lap in range(n_laps):
        sig = 0.03 * math.exp(0.3 * rng.standard_normal())
        e, emax = 0.0, 0.0
        s_vals = np.arange(s_start if lap == 0 else 0.0, route.length, ds)
        for s in s_vals:
            e = 0.97 * e + math.sqrt(1 - 0.97 ** 2) * sig * rng.standard_normal()
            # point on the route at arc length s, displaced by e to the left
            i = max(0, min(route.n_seg - 1, int(np.searchsorted(route.s0, s, side="right") - 1)))
            (ax, ay), (bx, by) = route.p[i], route.p[i + 1]
            L = math.hypot(bx - ax, by - ay)
            u = (s - route.s0[i]) / L
            nx, ny = -(by - ay) / L, (bx - ax) / L
            x, y = ax + u * (bx - ax) + e * nx, ay + u * (by - ay) + e * ny
            yaw = math.atan2(by - ay, bx - ax)
            rec.feed(t, x, y, yaw, 0.2, 1.0 - e)
            emax = max(emax, abs(e))
            t += 1.0
        if lap > 0:
            true_max.append(emax)
    rec.finish()
    comp = [w for w in written if w[1]]
    assert not written[0][1], "first (mid-route) run must be partial"
    assert len(comp) == n_laps - 1, (len(comp), n_laps - 1)
    rec_max = np.array([w[2] for w in comp])
    err = np.max(np.abs(rec_max - np.array(true_max)))
    print("runs: %d complete + %d partial; recorded vs true run max |e|: max abs diff %.2e m"
          % (len(comp), len(written) - len(comp), err))
    assert err < 2e-3, "recorded lateral error must match the simulated one"
    C.main([out, "--tol", "0.12"])
    # calibration of the guarantee: fresh synthetic runs vs the certified marginal bound, many repetitions
    hits = []
    for rep in range(400):
        def lapmax():
            sig = 0.03 * math.exp(0.3 * rng.standard_normal())
            x = sig * rng.standard_normal(600)
            # AR(1) with coefficient 0.97 via a cheap filter
            e = np.empty_like(x)
            acc = 0.0
            for j in range(len(x)):
                acc = 0.97 * acc + math.sqrt(1 - 0.97 ** 2) * x[j]
                e[j] = acc
            return np.max(np.abs(e))
        cal = [lapmax() for _ in range(30)]
        hits.append(lapmax() <= C.bound(cal, 0.1))
    print("coverage of a fresh run by the marginal bound (n = 30, 400 repetitions): %.3f (guarantee >= 0.9)"
          % np.mean(hits))
    assert np.mean(hits) > 0.86
    shutil.rmtree(out)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()

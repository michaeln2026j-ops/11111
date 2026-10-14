# -*- coding: utf-8 -*-
"""Certified lateral margin of a taught route from logged runs (conformal, distribution-free).

    python ce_certify.py ~/ce_logs/feed_full                      # all complete runs of the route
    python ce_certify.py ~/ce_logs/feed_full --eps 0.1 --delta 0.1 --s-range 10:60 --s-range 75:120

Run score S = max over the route (or over the given arc-length ranges, e.g. the trough sections) of
|e(s)|: the whole run stays inside a tube of half-width b  <=>  S <= b (exact). With n runs on the same
route treated as exchangeable (same vehicle, same route, operating conditions drawn from the same mix):
  marginal  P(S_new <= b_marg) >= 1 - eps                    (split conformal)
  PAC       P( P(S_new <= b_pac | runs) >= 1 - eps ) >= 1 - delta  (training-conditional)
The guarantee is about the next run as a whole, not about single points: a pointwise 3-sigma band is
reported next to it, with a leave-one-run-out check of how often each band is broken by a whole run.
Python 2.7 / 3, numpy only.
"""
from __future__ import division, print_function

import argparse
import glob
import math
import os
import sys

import numpy as np


def order_k(n, eps, delta=None):
    """Index (1-based) of the order statistic used as the bound; n + 1 means 'not enough runs'."""
    if delta is None:
        return int(math.ceil((n + 1) * (1 - eps)))
    # coverage of the k-th order statistic ~ Beta(k, n - k + 1);  P(cov >= 1 - eps) = P(Bin(n, 1 - eps) <= k - 1)
    p, cdf = 1 - eps, 0.0
    for k in range(1, n + 1):
        cdf += math.exp(math.lgamma(n + 1) - math.lgamma(k) - math.lgamma(n - k + 2)
                        + (k - 1) * math.log(p) + (n - k + 1) * math.log(1 - p))  # P(Bin = k - 1)
        if cdf >= 1 - delta:
            return k
    return n + 1


def bound(scores, eps, delta=None):
    s = np.sort(np.asarray(scores, float))
    k = order_k(len(s), eps, delta)
    return float(s[k - 1]) if k <= len(s) else float("inf")


def load_runs(path):
    files = sorted(f for f in glob.glob(os.path.join(os.path.expanduser(path), "run_*.csv")) if "_partial" not in f)
    runs = []
    for f in files:
        a = np.genfromtxt(f, delimiter=",", names=True)
        if a.size > 10:
            runs.append((os.path.basename(f), a))
    return runs


def in_ranges(s, ranges):
    if not ranges:
        return np.ones(len(s), bool)
    m = np.zeros(len(s), bool)
    for lo, hi in ranges:
        m |= (s >= lo) & (s <= hi)
    return m


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("logdir")
    ap.add_argument("--eps", type=float, default=0.1)
    ap.add_argument("--delta", type=float, default=0.1)
    ap.add_argument("--s-range", action="append", default=[], help="lo:hi arc-length range (m), repeatable")
    ap.add_argument("--tol", type=float, default=None, help="allowed half-width (m) to check against")
    a = ap.parse_args(argv)
    ranges = [tuple(float(v) for v in r.split(":")) for r in a.s_range]
    runs = load_runs(a.logdir)
    n = len(runs)
    if n == 0:
        sys.exit("no complete runs in %s" % a.logdir)
    S, Sl, Sr, pts = [], [], [], []
    for _, r in runs:
        m = in_ranges(r["s"], ranges)
        e = r["e"][m]
        S.append(np.max(np.abs(e)))
        Sl.append(np.max(e))
        Sr.append(np.max(-e))
        pts.append(e)
    S, Sl, Sr = np.array(S), np.array(Sl), np.array(Sr)
    allp = np.concatenate(pts)
    print("route log %s: %d complete runs%s" % (a.logdir, n, "" if not ranges else ", ranges %s" % ranges))
    print("pointwise |e|: mean %.1f cm, sd %.1f cm, 95%% %.1f cm" % (100 * np.mean(np.abs(allp)), 100 * np.std(allp),
                                                                  100 * np.percentile(np.abs(allp), 95)))
    print("run max |e| (S): median %.1f cm, max %.1f cm" % (100 * np.median(S), 100 * np.max(S)))
    kmin = [k for k in range(1, 200) if order_k(k, a.eps) <= k][0]
    kpac = [k for k in range(1, 400) if order_k(k, a.eps, a.delta) <= k][0]
    print("runs needed: marginal >= %d, PAC >= %d (eps %.2f, delta %.2f)" % (kmin, kpac, a.eps, a.delta))
    rows = []
    for nm, sc in (("two-sided |e|", S), ("left of travel (e > 0)", Sl), ("right of travel (e < 0)", Sr)):
        bm, bp = bound(sc, a.eps), bound(sc, a.eps, a.delta)
        rows.append((nm, bm, bp))
        print("  %-26s certified half-width: marginal %s   PAC %s" % (
            nm, "%.1f cm" % (100 * bm) if np.isfinite(bm) else "n/a (too few runs)",
            "%.1f cm" % (100 * bp) if np.isfinite(bp) else "n/a (too few runs)"))
    # leave-one-run-out: how often does a whole held-out run leave each band?
    if n >= kmin + 1:
        brk = {"conformal (marginal)": 0, "pointwise 3-sigma": 0, "pointwise 95% |e|": 0}
        for i in range(n):
            o = np.delete(np.arange(n), i)
            po = np.concatenate([pts[j] for j in o])
            brk["conformal (marginal)"] += S[i] > bound(S[o], a.eps)
            brk["pointwise 3-sigma"] += S[i] > abs(np.mean(po)) + 3 * np.std(po)
            brk["pointwise 95% |e|"] += S[i] > np.percentile(np.abs(po), 95)
        print("leave-one-run-out, fraction of whole runs leaving the band (target <= %.2f):" % a.eps)
        for k, v in brk.items():
            print("  %-22s %.2f (%d/%d)" % (k, v / n, v, n))
    if a.tol is not None:
        for nm, bm, bp in rows[:1]:
            ok = bp <= a.tol
            print("tolerance %.1f cm: %s" % (100 * a.tol, "CERTIFIED (PAC)" if ok else "not certified at PAC level"))
    # optional: localisation-independent check from the lidar side distance
    if all("scan_d" in r.dtype.names for _, r in runs):
        fin = [np.isfinite(r["scan_d"]).mean() for _, r in runs]
        if min(fin) > 0.8:
            edges = np.arange(0, max(r["s"].max() for _, r in runs) + 0.5, 0.5)
            prof = []
            for _, r in runs:
                idx = np.digitize(r["s"], edges)
                prof.append(np.array([np.nanmedian(r["scan_d"][idx == b]) if np.any(idx == b) else np.nan
                                      for b in range(1, len(edges))]))
            prof = np.array(prof)
            Sd = []
            for i in range(n):
                ref = np.nanmedian(np.delete(prof, i, axis=0), axis=0)  # leave-one-out reference profile
                Sd.append(np.nanmax(np.abs(prof[i] - ref)))
            print("lidar side distance (independent of localisation): run max |d - d_ref| median %.1f cm; "
                  "certified marginal %.1f cm, PAC %.1f cm" % (100 * np.median(Sd), 100 * bound(Sd, a.eps),
                                                                100 * bound(Sd, a.eps, a.delta)))


if __name__ == "__main__":
    main()

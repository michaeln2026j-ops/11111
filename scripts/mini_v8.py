"""Small v8 check (minutes on a laptop): CE+ v8 (training-only gating, Proposition B) vs the conformal
baselines on FRESH fields (never used by v1-v7: offset 50), all on the BCD + LQR-I stack, same calibration
budget (n_cal runs) for every method. Pre-registered primary method: CE+ v8 PAC (docs/theory_v8.md).

    python3 scripts/mini_v8.py                 # 1 field per regime
    python3 scripts/mini_v8.py --fields 3      # more fields
    python3 scripts/mini_v8.py --regimes R1    # one regime

Prints, per field: P(no miss) on n_test fresh runs, meets (one-sided binomial test vs 0.9), overlap and
excess overlap over the per-field oracle; and the training-only gating decision (Proposition B).
"""
import argparse
import os
import sys
import time

import numpy as np
from scipy.stats import binomtest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "experiments"))
import ceplus as CP  # noqa: E402
import core  # noqa: E402
import exp_lib as L  # noqa: E402
import exp_system as E  # noqa: E402
from baselines import uncertainty as UQ  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--fields", type=int, default=1)
ap.add_argument("--offset", type=int, default=50)
ap.add_argument("--regimes", default="R1,R2,R3")
ap.add_argument("--n-cal", type=int, default=100)
ap.add_argument("--n-test", type=int, default=200)
args = ap.parse_args()
eps = 0.1


def meets(p, n):
    return binomtest(int(round(p * n)), n, 0.9, alternative="less").pvalue >= 0.05


for key in args.regimes.split(","):
    rname = [k for k in E.REGIMES if k.startswith(key)][0]
    reg = E.REGIMES[rname]
    w = reg["w"]
    fields = core.load_fields(reg["kind"], w=w, seed=0)
    ctrl = lambda: "lqr_i"  # noqa: E731
    lam_train = 0.10 if reg["p2p"] < 0.05 else 0.40
    t0 = time.time()
    rng_seed = E._seed(rname, "ceplus", "LQR-I", False)
    sc, lam0 = CP.fit_training(fields[:5], w, reg, E.make_cond, lambda F: E.sim_core(F, ctrl, reg), ctrl, eps,
                               lam_train, seed=rng_seed, gate=True)
    print(f"\n=== {rname}: training fit {time.time() - t0:.0f}s, normalisation "
          f"{'ADAPTIVE (XTE)' if sc.b > 0 else 'CONSTANT'} (a={sc.a:.2f}, b={sc.b:.2f}), lam0={lam0:.3f}", flush=True)
    for F in fields[args.offset:args.offset + args.fields]:
        t1 = time.time()
        seed = 100003 * F.fid + 17 * len(rname)
        S_l = E.sim_core(F, ctrl, reg)
        lam_s, ov_s, p_s = E.oracle_lambda(F, w, S_l, reg, seed, eps)
        bcd = lambda lam, F=F: core.plan(F, w, lam, E.UNIT)  # noqa: E731
        res = {}
        lc = UQ.cpp_lambda(F, np.random.default_rng(seed), eps, n_cal=args.n_cal, w=w, ctrl="lqr_i", **E.cond_kw(reg))
        res["CPP (Zhao)"] = E.evaluate(F, w, bcd(lc), S_l, args.n_test, seed + 1, reg)
        lp = UQ.lindemann_cp_lambda(F, np.random.default_rng(seed + 2), eps, n_cal=args.n_cal, w=w, ctrl="lqr_i",
                                    granularity="pair", **E.cond_kw(reg))
        res["Lindemann pair-level"] = E.evaluate(F, w, bcd(lp), S_l, args.n_test, seed + 1, reg)
        for nm, dl in (("CE+ v8", None), ("CE+ v8 PAC", 0.1)):
            c = CP.calibrate(F, w, reg, E.make_cond, bcd, S_l, ctrl, sc, lam0, eps, args.n_cal,
                             np.random.default_rng(seed + 5), seed, delta=dl)
            res[nm] = CP.deploy_eval(F, w, reg, E.make_cond, bcd, S_l, ctrl, sc, c["t"], args.n_test, seed + 1,
                                     L.overlap_ratio)
        print(f"  field {F.fid} (oracle lam {lam_s:.3f}, oracle P {p_s:.3f}, {time.time() - t1:.0f}s)")
        for nm, r in res.items():
            print(f"    {nm:30s} P={r['p_nomiss']:.3f} meets={'yes' if meets(r['p_nomiss'], args.n_test) else 'NO '} "
                  f"passes={r['passes']:.1f} overlap={100 * r['overlap']:.2f}% excess={100 * (r['overlap'] - ov_s):+.2f} pp",
                  flush=True)

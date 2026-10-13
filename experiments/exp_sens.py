"""E4/E5 controllers, terrain compensation, implement width, GNSS grade, and
E5b online adaptation under seasonal drift (adaptive conformal inference).

Outputs: results/sens.csv, results/aci.csv
"""
import argparse
import os

import numpy as np
import pandas as pd

import core
import exp_lib as L

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def certify_eval(F, sig, rng, eps, n_cal, n_test, lam0, w=3.0, ctrl="lqr_i", **ck):
    infield = lambda n: [(F, np.arange(n))]
    q, hist, scores = L.calibrate_conformal(infield, sig, eps, w, rng, lam0=lam0, n_cal=n_cal,
                                            ctrl=ctrl, **ck)
    ys = core.plan(F, w, q, sig)
    r = L.evaluate_plan(F, ys, n_test, rng, w=w, ctrl=ctrl, **ck)
    ys0 = core.plan(F, w, 0.0, sig)
    r0 = L.evaluate_plan(F, ys0, n_test, rng, w=w, ctrl=ctrl, **ck)
    r.update(q=q, nominal_e_miss=r0["e_miss"], nominal_p_nomiss=r0["p_nomiss"],
             nominal_passes=r0["passes"])
    return r


def _shard(args):
    return "" if args.nshards == 1 else f"_shard{args.shard}of{args.nshards}"


def sweep(args, rng):
    fields = core.load_fields("paddy", seed=0)
    train, evalf = fields[:20], fields[20:20 + args.fields]
    evalf = evalf[args.shard::args.nshards]
    sigU = L.ConstSigma(1.0)
    rows = []
    configs = []
    for c in ("pure_pursuit", "stanley", "lqr", "lqr_i"):
        configs.append(("controller", c, dict(ctrl=c)))
    for comp in (0.0, 0.5, 0.85, 0.95):
        configs.append(("roll compensation", comp, dict(comp=comp)))
    for w in (1.5, 3.0, 6.0, 12.0):
        configs.append(("implement width (m)", w, dict(w=w)))
    for g in ("rtk_fix", "rtk_float", "dgps"):  # real NOAA CORS error series of each receiver grade
        configs.append(("GNSS receiver grade", g, dict(gnss=g)))
    for fi, F0 in enumerate(evalf):
        for group, val, kw in configs:
            kw = dict(kw)
            w = kw.pop("w", 3.0)
            ctrl = kw.pop("ctrl", "lqr_i")
            F = F0 if w == 3.0 else core.Field(F0.fid, F0.meta, w=w)
            if F.M.is_empty or F.M.geom_type != "Polygon":
                continue
            try:
                lam0 = 0.3 if val == "dgps" else 0.03
                r = certify_eval(F, sigU, rng, args.eps, args.n_cal, args.n_test, lam0, w=w, ctrl=ctrl, **kw)
            except ValueError:
                continue
            rows.append(dict(group=group, value=val, field=F0.fid, slope=F0.z_mean_slope, **r))
        print(f"sens [{fi+1}/{len(evalf)}]", flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(RES, f"sens{_shard(args)}.csv"), index=False)


def aci(args, rng):
    """Seasonal drift: soil moisture rises from 0.15 to 0.9 over T operations.
    Static: split CP on the first n0 (dry) operations. ACI: Gibbs & Candes (2021)
    update eps_t <- eps_t + gamma (eps - miss_t), quantile over a sliding window."""
    fields = core.load_fields("paddy", seed=0)[20:20 + args.aci_fields][args.shard::args.nshards]
    sig = L.ConstSigma(1.0)
    rows = []
    T, n0, gamma, win = args.aci_T, 60, 0.01, 150
    for F in fields:
        for method in ("static", "aci"):
            r = np.random.default_rng(hash((F.fid, method)) % 2**32)
            moist = np.r_[np.full(n0, 0.15), np.linspace(0.15, 0.9, T)]
            hist_scores = []
            lam = 0.03
            # warm-up on dry season
            for t in range(n0):
                ys = core.plan(F, 3.0, lam, sig)
                X, D, _ = L.run(F, ys, 1, r, moisture=moist[t])
                s, *_ = core.pair_scores(F, ys, X, D, sig.vec(F, ys))
                hist_scores.append(float(s[0]))
            q_static = core.conformal_quantile(hist_scores, args.eps)
            eps_t = args.eps
            for t in range(n0, n0 + T):
                if method == "static":
                    q = q_static
                else:
                    ref = hist_scores[-win:]
                    q = core.conformal_quantile(ref, float(np.clip(eps_t, 1e-3, 0.999))) if eps_t > 0 else max(ref) * 1.2
                    q = min(q, 1.0)
                try:
                    ys = core.plan(F, 3.0, q, sig)
                except ValueError:
                    ys = core.plan(F, 3.0, 1.0, sig)
                X, D, _ = L.run(F, ys, 1, r, moisture=moist[t])
                miss = float(core.evaluate(F, ys, X, D, 3.0)[0])
                s, *_ = core.pair_scores(F, ys, X, D, sig.vec(F, ys))
                hist_scores.append(float(s[0]))
                err = float(miss > 0)
                eps_t = eps_t + gamma * (args.eps - err)
                rows.append(dict(field=F.fid, method=method, t=t - n0, moisture=moist[t], q=q,
                                 miss=miss, err=err, passes=len(ys)))
        print("aci field done", F.fid, flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(RES, f"aci{_shard(args)}.csv"), index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="sweep")
    ap.add_argument("--fields", type=int, default=12)
    ap.add_argument("--aci-fields", type=int, default=8)
    ap.add_argument("--aci-T", type=int, default=400)
    ap.add_argument("--n-cal", type=int, default=100)
    ap.add_argument("--n-test", type=int, default=200)
    ap.add_argument("--eps", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    (sweep if args.part == "sweep" else aci)(args, rng)


if __name__ == "__main__":
    main()

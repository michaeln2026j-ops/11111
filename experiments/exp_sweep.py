"""E10: per-field response curves P_f(no miss | global margin m) for the fixed-
overlap family (what every commercial guidance system exposes: one overlap
setting), on the same fields as E2 main. Lets us plot, for ANY global setting,
the fraction of fields that meet the target vs. the overlap paid, against the
per-field calibrated certificate (CE-U) — the comparison that separates
"tuning a margin" from "certifying a margin".
Outputs: results/sweep_<kind>.csv
"""
import argparse
import os

import numpy as np
import pandas as pd

import core
import exp_lib as L

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="paddy")
    ap.add_argument("--fields", type=int, default=60)
    ap.add_argument("--n-test", type=int, default=200)
    ap.add_argument("--w", type=float, default=3.0)
    ap.add_argument("--rtk-scale", type=float, default=1.0)
    ap.add_argument("--tag", default="")
    ap.add_argument("--shard", type=int, default=0, help="this process's shard index")
    ap.add_argument("--nshards", type=int, default=1, help="total number of shards (fields split round-robin)")
    args = ap.parse_args()
    rng = np.random.default_rng(31)
    const = L.ConstSigma(1.0)
    fields = core.load_fields(args.kind, w=args.w, seed=0)[20:20 + args.fields]
    fields = fields[args.shard::args.nshards]
    SHARD = "" if args.nshards == 1 else f"_shard{args.shard}of{args.nshards}"
    grid_cm = [0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, 25, 30, 40, 50]
    rows = []
    for fi, F in enumerate(fields):
        for m in grid_cm:
            lam = m / 200.0  # overlap m (cm) between adjacent passes -> erosion m/2 per side
            try:
                ys = core.plan(F, args.w, lam, const)
                r = L.evaluate_plan(F, ys, args.n_test, rng, w=args.w, rtk_scale=args.rtk_scale)
            except ValueError:
                continue
            rows.append(dict(kind=args.kind, field=F.fid, overlap_setting_cm=m, slope=F.z_mean_slope, **r))
        print(f"{args.kind} [{fi+1}/{len(fields)}]", flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(RES, f"sweep_{args.kind}{args.tag}{SHARD}.csv"), index=False)


if __name__ == "__main__":
    main()

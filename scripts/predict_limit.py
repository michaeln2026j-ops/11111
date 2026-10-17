"""Proposition L (docs/theory_limit.md): predicted PAC margin inflation under the ideal (oracle) scale, from the
theory CDFs alone (one run per field, normalised by its own predicted 1-eps quantile, PAC order statistic,
leave-one-out, 2000 repetitions), against the value observed on the E-low v2 fields.

    python3 scripts/predict_limit.py
"""
import glob
import os
import pickle
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import ceplus as CP  # noqa: E402
import exp_lowdata as X  # noqa: E402

OBS = {"R1": 1.018, "R2": 1.207, "R3": 1.645}  # results/lowdata_v2/feature_pivot.txt, oracle (ideal) PAC lam/lam*


def main():
    rng = np.random.default_rng(0)
    for key in ("R1", "R2", "R3"):
        rs = [pickle.load(open(f, "rb")) for f in glob.glob(os.path.join(HERE, "..", "results", "lowdata_v2", f"A_{key}_*.pkl"))]
        rs = [r for r in rs if np.all(np.isfinite(r["Fhat"]))]
        n = len(rs)

        def draw(r):
            F = np.maximum.accumulate(r["Fhat"])
            u = rng.random()
            if u > F[-1]:
                return r["tgrid"][-1] * 1.25
            if u < F[0]:
                return r["tgrid"][0] * u / max(F[0], 1e-9)
            return float(np.interp(u, F, r["tgrid"]))
        q = np.array([X.inv_cdf(r["tgrid"], r["Fhat"], 0.9) for r in rs])
        tail = np.array([X.inv_cdf(r["tgrid"], r["Fhat"], 0.97) for r in rs]) / q
        rat = []
        for _ in range(2000):
            V = np.array([draw(r) for r in rs]) / q
            g = rng.integers(n)
            rat.append(CP.quantile(np.delete(V, g), 0.1, 0.1))
        print(f"{key}: theory tail ratio q.97/q.9 {tail.mean():.3f}; predicted ideal-PAC lam/lam* {np.mean(rat):.3f} "
              f"(sd {np.std(rat):.3f}); observed {OBS[key]:.3f}")


if __name__ == "__main__":
    main()

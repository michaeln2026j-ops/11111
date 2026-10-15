"""Worked example for Section 3 (R1 field 440): 29 logged runs -> margin. One fixed draw (seed 1, the first and only
draw taken), plus the average over 2000 redraws of 29 runs from the same 200-run bank."""
import math
import sys
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import rev_resample as RR

r = [x for x in RR.nominal_records() if x["key"] == "R1" and x["fid"] == 440][0]
c, bank = r["cur"], np.asarray(r["bank"])
n, eps = 29, 0.1
k = math.ceil((n + 1) * (1 - eps))
s = np.sort(np.random.default_rng(1).choice(bank, n, replace=False))
lam = s[k - 1]
print(f"field 440 (R1, w = 3 m), reference margin {100 * r['lam0']:.1f} cm, n = {n}, k* = {k}")
print(f"scores: min {100 * s[0]:.1f} cm, median {100 * np.median(s):.1f} cm, max {100 * s[-1]:.1f} cm; 27th smallest {100 * lam:.1f} cm")
print(f"deployed margin {100 * lam:.1f} cm -> line spacing {300 - 200 * lam:.1f} cm, overlap {100 * np.interp(lam, c['lam'], c['ov']):.2f}%, "
      f"P(no miss) on test runs {np.interp(lam, c['lam'], c['P']):.3f}")
print(f"field's own 0.9 margin (oracle) {100 * r['oracle_lam']:.1f} cm, overlap {100 * r['oracle_overlap']:.2f}%")
rng = np.random.default_rng(2)
P = [np.interp(np.sort(rng.choice(bank, n, replace=False))[k - 1], c["lam"], c["P"]) for _ in range(2000)]
print(f"over 2000 redraws of 29 runs: mean P(no miss) {np.mean(P):.3f}, 10th-90th percentile {np.quantile(P, 0.1):.3f}-{np.quantile(P, 0.9):.3f}")

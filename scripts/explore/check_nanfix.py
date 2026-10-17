"""Check of the exact interpolated-offset variance (evt_theory.pair_params): no NaN, and how much the
predicted CDF moves against the phase-A record computed with the stationary shortcut.

    python3 scripts/explore/check_nanfix.py R3 88
"""
import os
import pickle
import sys
import warnings

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "experiments"))
import core  # noqa: E402
import evt_theory as T  # noqa: E402
import exp_lowdata as X  # noqa: E402
import exp_system as E  # noqa: E402

key, fi = sys.argv[1], int(sys.argv[2])
r = pickle.load(open(os.path.join(X.OUT, f"A_{key}_{fi}.pkl"), "rb"))
rname, reg = X.regime(key)
w = reg["w"]
F = core.load_fields(reg["kind"], w=w, seed=0)[fi]
with warnings.catch_warnings(record=True) as wl:
    warnings.simplefilter("always")
    Fn = T.predict_cdf(F, w, reg, r["lam0"], r["tgrid"], n_cond=200,
                       rng=np.random.default_rng(E._seed(rname, "lowdata", F.fid)))
inv = lambda F_, v: float(np.interp(v, np.maximum.accumulate(F_), r["tgrid"]))  # noqa: E731
old_ok = not np.isnan(r["Fhat"]).any()
print(f"{key} field {F.fid} ({fi}): NaN {np.isnan(Fn).any()}  sqrt warnings {sum('sqrt' in str(x.message) for x in wl)}  "
      f"q0.9 old {inv(r['Fhat'], .9) if old_ok else float('nan'):.4f}  new {inv(Fn, .9):.4f}  oracle {r['oracle_lam']:.4f}  "
      f"max|dF| {np.abs(Fn - r['Fhat']).max() if old_ok else float('nan'):.4f}", flush=True)

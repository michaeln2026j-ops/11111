"""Wall time of the theory predictor alone (evt_theory.predict_cdf, n_cond = 200, single core) per field."""
import os, pickle, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import core, evt_theory as T, exp_lowdata as X, exp_system as E  # noqa: E401,E402
out = []
for key in ("R1", "R2", "R3"):
    rname, reg = X.regime(key); w = reg["w"]
    fields = core.load_fields(reg["kind"], w=w, seed=0)
    for fi in (5, 10, 15):
        r = pickle.load(open(os.path.join(HERE, "..", "results", "lowdata_v3", f"A_{key}_{fi}.pkl"), "rb"))
        F = fields[fi]; t0 = time.time()
        T.predict_cdf(F, w, reg, r["lam0"], r["tgrid"], n_cond=200, rng=np.random.default_rng(E._seed(rname, "lowdata", F.fid)))
        dt = time.time() - t0
        out.append(f"{key} field {F.fid} ({fi}): passes {r['K0']}, length {r['N_len']:.0f} m, theory {dt:.0f} s")
        print(out[-1], flush=True)
open(os.path.join(HERE, "..", "results", "lowdata_v3", "theory_runtime.txt"), "w").write("\n".join(out) + "\n")

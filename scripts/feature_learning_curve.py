"""Learning curve: how much field data does a data-driven predictor need to match the zero-data theory?
(secondary analysis, post hoc)

Predict log lam*_f on the E-low v2 fields (50-79) from field features, trained on m fields of the E-low v1
pool (80+, disjoint) with two kinds of training target:
  oracle  : lam*_f from hundreds of simulated runs per training field (not available in practice)
  one-run : the single historical run score S_f (what the low-data setting actually provides)
and a hybrid that keeps the theory quantile and learns only a feature correction of its log-residual.
Reported: sd of log(q / lam*) on the test fields (lower = better pivot), mean over 40 random training subsets.

    python3 scripts/feature_learning_curve.py
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import core  # noqa: E402
import exp_lowdata as X  # noqa: E402
from feature_pivot import RES, features, load  # noqa: E402


def ridge(Xa, y, alpha=1.0):
    mu, sd = Xa.mean(0), Xa.std(0) + 1e-12
    A = np.c_[np.ones(len(y)), (Xa - mu) / sd]
    b = np.linalg.solve(A.T @ A + alpha * np.diag([0] + [1] * (A.shape[1] - 1)), A.T @ y)
    return lambda Z: np.c_[np.ones(len(Z)), (Z - mu) / sd] @ b


def main():
    rng = np.random.default_rng(0)
    out = []
    for key in ("R1", "R2", "R3"):
        rname, reg = X.regime(key)
        fields = core.load_fields(reg["kind"], w=reg["w"], seed=0)
        tr, te = load(key, os.path.join(RES, "lowdata")), load(key, os.path.join(RES, "lowdata_v2"))
        Xtr = np.array([features(fields[r["fi"]], r) for r in tr])
        Xte = np.array([features(fields[r["fi"]], r) for r in te])
        orc_tr = np.log([r["oracle_lam"] for r in tr])
        one_tr = np.log([max(r["S_hist"], 1e-3) for r in tr])
        qth_tr = np.log([X.inv_cdf(r["tgrid"], r["Fhat"], 0.9) for r in tr])
        orc_te = np.log([r["oracle_lam"] for r in te])
        qth_te = np.log([X.inv_cdf(r["tgrid"], r["Fhat"], 0.9) for r in te])
        th = np.std(qth_te - orc_te)
        out.append(f"\n{key}: theory (zero data) log-error sd {th:.3f}   [test {len(te)} fields; pool {len(tr)}]")
        out.append(f"   {'m':>4s} {'features<-oracle':>17s} {'features<-one run':>18s} {'theory+features<-one run':>25s}")
        for m in (5, 10, 20, 30, len(tr)):
            res = {"o": [], "1": [], "h": []}
            for _ in range(40 if m < len(tr) else 1):
                idx = rng.choice(len(tr), size=m, replace=False)
                f_o = ridge(Xtr[idx], orc_tr[idx])
                f_1 = ridge(Xtr[idx], one_tr[idx])
                f_h = ridge(Xtr[idx], one_tr[idx] - qth_tr[idx], alpha=10.0)  # correction of the theory, shrunk
                res["o"].append(np.std(f_o(Xte) - orc_te))
                res["1"].append(np.std(f_1(Xte) - orc_te))
                res["h"].append(np.std(qth_te + f_h(Xte) - orc_te))
            out.append(f"   {m:4d} {np.mean(res['o']):17.3f} {np.mean(res['1']):18.3f} {np.mean(res['h']):25.3f}")
    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(RES, "lowdata_v2", "feature_learning_curve.txt"), "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()

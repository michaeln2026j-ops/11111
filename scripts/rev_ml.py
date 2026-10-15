"""RV7 (docs/prereg_revision.md, descriptive): tuned learned predictors of the per-field required margin, against
the theory and the Monte Carlo digital twin. Same data and metric as feature_learning_curve.py (sd of
log(prediction / lam*) on the 30 E-low v2 test fields; training on the disjoint E-low v1 pool).

    python3 scripts/rev_ml.py     # -> results/revision/rv7_ml.txt
"""
import os
import pickle
import sys
import warnings

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import core  # noqa: E402
import exp_lowdata as X  # noqa: E402
from feature_pivot import RES, features, load  # noqa: E402

warnings.filterwarnings("ignore")
ALPHAS = np.logspace(-3, 6, 28)


def ridgecv():
    return make_pipeline(StandardScaler(), RidgeCV(alphas=ALPHAS))


def gbm(m):
    g = GradientBoostingRegressor(max_depth=2, n_estimators=200, subsample=0.8, random_state=0)
    if m < 10:
        return make_pipeline(StandardScaler(), g)
    return make_pipeline(StandardScaler(), GridSearchCV(g, {"learning_rate": [0.01, 0.03, 0.1]}, cv=5))


def main():
    rng = np.random.default_rng(0)
    out = ["RV7 tuned learned predictors (descriptive, post hoc): sd of log(pred / lam*) on the E-low v2 test fields; "
           "mean over 20 random training subsets (1 for the full pool)."]
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
        tw = [os.path.join(RES, "revision", f"twin_{key}_{r['fi']}.pkl") for r in te]
        line = f"\n{key}: theory {np.std(qth_te - orc_te):.3f}"
        if all(os.path.exists(f) for f in tw):
            qtw = np.log([pickle.load(open(f, "rb"))["q"] for f in tw])
            line += f"; MC twin (1000 nominal runs) {np.std(qtw - orc_te):.3f}"
        out.append(line + f"   [test {len(te)}, pool {len(tr)}]")
        out.append(f"   {'m':>4s} {'ridgeCV<-1run':>13s} {'GBM<-1run':>10s} {'hybridCV<-1run':>14s} "
                   f"{'ridgeCV<-oracle':>15s} {'GBM<-oracle':>11s}")
        for m in (10, 20, 30, len(tr)):
            res = {k: [] for k in ("r1", "g1", "h1", "ro", "go")}
            for _ in range(20 if m < len(tr) else 1):
                idx = rng.choice(len(tr), size=m, replace=False)
                for k, mdl, y, base in (("r1", ridgecv(), one_tr, None), ("g1", gbm(m), one_tr, None),
                                        ("h1", ridgecv(), one_tr - qth_tr, qth_te), ("ro", ridgecv(), orc_tr, None),
                                        ("go", gbm(m), orc_tr, None)):
                    mdl.fit(Xtr[idx], y[idx])
                    p = mdl.predict(Xte) + (base if base is not None else 0)
                    res[k].append(np.std(p - orc_te))
            out.append(f"   {m:4d} {np.mean(res['r1']):13.3f} {np.mean(res['g1']):10.3f} {np.mean(res['h1']):14.3f} "
                       f"{np.mean(res['ro']):15.3f} {np.mean(res['go']):11.3f}")
    txt = "\n".join(out)
    os.makedirs(os.path.join(RES, "revision"), exist_ok=True)
    open(os.path.join(RES, "revision", "rv7_ml.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()

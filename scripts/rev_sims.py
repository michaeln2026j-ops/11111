"""Simulations of the revision experiments RV4 (model mismatch), RV5 (headland laps) and the MC twin of RV2/RV6
(docs/prereg_revision.md). One cached pickle per job in results/revision/; safe to interrupt and resume.

    python3 scripts/rev_sims.py --jobs 4 [--only mm|lap|twin]
"""
import argparse
import os
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import core  # noqa: E402
import exp_lib as L  # noqa: E402
import exp_lowdata as X  # noqa: E402
import exp_system as E  # noqa: E402
import laps as LP  # noqa: E402
import truth as TR  # noqa: E402

RES = os.path.join(HERE, "..", "results")
OUT = os.path.join(RES, "revision")
FIELDS = [("lowdata_v3", fi) for fi in range(5, 20)] + [("lowdata_v2", fi) for fi in range(50, 80)]
N_BANK, N_TEST, N_TWIN, N_GRID = 200, 200, 1000, 28
_F = {}


def field(key, fi):
    if key not in _F:
        _, reg = X.regime(key)
        _F[key] = core.load_fields(reg["kind"], w=reg["w"], seed=0)
    return _F[key][fi]


def ctx(d, key, fi):
    rname, reg = X.regime(key)
    F = field(key, fi)
    r = pickle.load(open(os.path.join(RES, d, f"A_{key}_{fi}.pkl"), "rb"))
    return rname, reg, F, r


def curve(F, w, reg, q, sim_eval, cap):
    lo = 0.25 * q
    grid = np.geomspace(lo, cap, N_GRID) if lo < cap else np.array([])
    lam, P, ov, em = [], [], [], []
    for g in grid:
        try:
            ys = core.plan(F, w, float(g), E.UNIT)
        except ValueError:
            continue
        miss = sim_eval(ys, float(g))
        lam.append(float(g)), P.append(float(np.mean(miss == 0))), em.append(float(miss.mean()))
        ov.append(L.overlap_ratio(F, ys, w))
    P = np.array(P)
    return dict(lam=np.array(lam), P=np.maximum.accumulate(P) if len(P) else P, P_raw=P, ov=np.array(ov),
                emiss=np.array(em))


def job_mm(args):
    d, key, fi, variant = args
    out_f = os.path.join(OUT, f"mm_{TR.SHORT[variant]}_{key}_{fi}.pkl")
    if os.path.exists(out_f):
        return out_f
    t0 = time.time()
    rname, reg, F, r = ctx(d, key, fi)
    w, lam0, cap = reg["w"], r["lam0"], 0.4 * reg["w"]
    sim = E.sim_core(F, lambda: "lqr_i", reg)
    sb = E._seed(rname, "rev-bank-" + variant, F.fid)
    rng = np.random.default_rng(sb)
    ys0 = core.plan(F, w, lam0, E.UNIT)
    Xs, Ds = sim(ys0, TR.make_cond(rng, N_BANK, reg, variant, sb), rng)
    bank = np.asarray(core.exact_scores(F, ys0, Xs, Ds, w, lam0), float)
    st = E._seed(rname, "rev-test-" + variant, F.fid)

    def ev(ys, lam):
        rg = np.random.default_rng(st)  # common random numbers across the grid
        Xt, Dt = sim(ys, TR.make_cond(rg, N_TEST, reg, variant, st), rg)
        return core.evaluate(F, ys, Xt, Dt, w)
    cur = curve(F, w, reg, float(np.quantile(bank, 0.9)), ev, cap)
    rec = dict(key=key, fi=fi, fid=F.fid, variant=variant, lam0=lam0, cap=cap, bank=bank, cur=cur)
    pickle.dump(rec, open(out_f, "wb"))
    print(f"[mm] {variant:24s} {key} {fi:3d}: q0.9 {np.quantile(bank, 0.9):.3f}  grid {len(cur['lam'])}  "
          f"({time.time() - t0:.0f}s)", flush=True)
    return out_f


def job_lap(args):
    d, key, fi = args
    out_f = os.path.join(OUT, f"lap_{key}_{fi}.pkl")
    if os.path.exists(out_f):
        return out_f
    t0 = time.time()
    rname, reg, F, r = ctx(d, key, fi)
    w, lam0, cap = reg["w"], r["lam0"], 0.4 * reg["w"]
    sim = E.sim_core(F, lambda: "lqr_i", reg)
    sb = E._seed(rname, "rev-lap-bank", F.fid)
    rng = np.random.default_rng(sb)
    ys0 = core.plan(F, w, lam0, E.UNIT)
    Xs, Ds, lp = LP.simulate(F, ys0, w, lam0, E.make_cond(rng, N_BANK, reg), rng, sim)
    S, Sb, Si = LP.exact_scores(F, ys0, Xs, Ds, w, lam0, lp, split=True)
    T = core.exact_pair_scores(F, ys0, Xs, Ds, w, lam0)  # same infield runs, hard edge
    S_hard = T.max(axis=1)
    hb, hi = np.maximum(T[:, 0], T[:, -1]), T[:, 1:-1].max(axis=1) if T.shape[1] > 2 else np.full(len(S), -np.inf)
    st = E._seed(rname, "rev-lap-test", F.fid)

    def ev(ys, lam):
        rg = np.random.default_rng(st)
        Xt, Dt, lpt = LP.simulate(F, ys, w, lam, E.make_cond(rg, N_TEST, reg), rg, sim)
        return LP.evaluate(F, ys, Xt, Dt, w, lam, lpt)
    cur = curve(F, w, reg, float(np.quantile(S, 0.9)), ev, cap)
    rec = dict(key=key, fi=fi, fid=F.fid, lam0=lam0, cap=cap, bank=np.asarray(S, float), bank_b=Sb, bank_i=Si,
               hard=S_hard, hard_b=hb, hard_i=hi, cur=cur)
    pickle.dump(rec, open(out_f, "wb"))
    print(f"[lap] {key} {fi:3d}: q0.9 laps {np.quantile(S, 0.9):.3f} hard {np.quantile(S_hard, 0.9):.3f}  "
          f"boundary-binding laps {np.mean(Sb >= Si):.2f} hard {np.mean(hb >= hi):.2f}  ({time.time() - t0:.0f}s)",
          flush=True)
    return out_f


def job_twin(args):
    d, key, fi = args
    out_f = os.path.join(OUT, f"twin_{key}_{fi}.pkl")
    if os.path.exists(out_f):
        return out_f
    t0 = time.time()
    rname, reg, F, r = ctx(d, key, fi)
    w, lam0 = reg["w"], r["lam0"]
    sim = E.sim_core(F, lambda: "lqr_i", reg)
    ys0 = core.plan(F, w, lam0, E.UNIT)
    S = []
    for b in range(N_TWIN // 200):
        rng = np.random.default_rng([E._seed(rname, "rev-twin", F.fid), b])
        Xs, Ds = sim(ys0, E.make_cond(rng, 200, reg), rng)
        S.append(core.exact_scores(F, ys0, Xs, Ds, w, lam0))
    S = np.concatenate(S)
    rec = dict(key=key, fi=fi, fid=F.fid, lam0=lam0, S=S, q=float(np.quantile(S, 0.9)), cpu_s=time.time() - t0)
    pickle.dump(rec, open(out_f, "wb"))
    print(f"[twin] {key} {fi:3d}: q0.9 {rec['q']:.3f} ({rec['cpu_s']:.0f}s)", flush=True)
    return out_f


def run(a):
    kind, rest = a[0], a[1:]
    return {"mm": job_mm, "lap": job_lap, "twin": job_twin}[kind](rest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", default=None)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--reverse", action="store_true")
    ap.add_argument("--variant", default=None, help="only mm jobs of this variant")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    todo = []
    for d, fi in FIELDS:
        for key in ("R1", "R2", "R3"):
            todo.append(("twin", d, key, fi))
    for d, fi in FIELDS:
        for key in ("R1", "R2", "R3"):
            todo.append(("lap", d, key, fi))
            for v in TR.VARIANTS:
                if v != "nominal":
                    todo.append(("mm", d, key, fi, v))
    for d, fi in FIELDS:  # nominal margin curves with missed-area means (cost analysis of RV1), added last
        for key in ("R1", "R2", "R3"):
            todo.append(("mm", d, key, fi, "nominal"))
    if a.only:
        todo = [t for t in todo if t[0] == a.only]
    if a.variant:
        todo = [t for t in todo if t[0] == "mm" and t[-1] == a.variant]
    if a.reverse:
        todo = todo[::-1]
    todo = todo[a.shard::a.nshards]
    with ProcessPoolExecutor(a.jobs) as ex:
        for f in ex.map(run, todo):
            pass


if __name__ == "__main__":
    main()

"""E2b SYSTEM-LEVEL comparison against published algorithms.

Every system = (coverage planner) x (path-tracking controller) x (margin /
certification layer). All systems are executed by the SAME corrected simulator on
the SAME real fields with common random numbers (one seed per field x regime),
and scored by the SAME evaluator (core.evaluate). Our conformal-erosion layer is
applied on top of every planner/controller (the "+CE" rows) to show it is a
planner- and controller-agnostic certification layer.

Regimes (representative operating conditions):
  R1 plain-RTK    : wheat fields (North China Plain), RTK, 3 m implement
  R2 hilly-GNSSx3 : paddy fields (hilly south), degraded RTK (error x3), 3 m
  R3 hilly-narrow : paddy fields, RTK, 1.5 m implement, wet soil (moisture 0.6-0.9)

Generic certification layer (any planner parameterised so that one unit of erosion
lam shrinks every adjacent spacing by 2 lam): with the reference plan ys_ref built
at lam_ref, a run has zero miss at lam iff
   lam >= S = lam_ref + max( max_k sup_x (e_{k+1}-e_k - (w - (y_{k+1}-y_k)))/2,
                             sup_x e_1 - (w/2 - (y_1 - y_lo)),
                             sup_x -e_N - (w/2 - (y_hi - y_N)) )
which reduces to Lemma 1 for the uniform planner; q = conformal quantile of S
(fixed-point in lam_ref, Theorems 1-2).

Usage: python3 exp_system.py [--shard i --nshards n] [--fields 30]
Outputs: results/system[_shard..].csv
"""
import argparse
import math
import os
import time
import traceback

import numpy as np
import pandas as pd

import core
import exp_lib as L

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
UNIT = L.ConstSigma(1.0)

from baselines import controllers as BC  # noqa: E402
from baselines import f2c_planner as F2C  # noqa: E402
from baselines import lenain as LEN  # noqa: E402
from baselines import sequential as SEQ  # noqa: E402
from baselines import terrain3d as T3D  # noqa: E402
from baselines import uncertainty as UQ  # noqa: E402

try:
    from baselines import tube as TUBE
except Exception:  # module from wave 2 may be missing
    TUBE = None
try:
    from baselines import vendor as VEND
except Exception:
    VEND = None
try:
    from baselines import belief as BEL
except Exception:
    BEL = None

REGIMES = {
    "R1 plain-RTK": dict(kind="wheat", w=3.0, cond=dict()),
    "R2 hilly-GNSSx3": dict(kind="paddy", w=3.0, cond=dict(rtk_scale=3.0)),
    "R3 hilly-narrow-wet": dict(kind="paddy", w=1.5, cond=dict(moisture=None, wet=True)),
}


def cond_kw(reg):
    c = dict(reg["cond"])
    c.pop("wet", None)
    c.pop("moisture", None)
    return c


def make_cond(rng, n, reg):
    c = cond_kw(reg)
    if reg["cond"].get("wet"):
        c["moisture"] = rng.uniform(0.6, 0.9, n)
    return core.Condition(rng, n, **c)


# ------------------------------------------------------------- generic machinery
def generic_scores(F, ys, lam_ref, X, D, w):
    """Run-level score S (see module docstring) for an arbitrary planner."""
    xg, off = L.offsets(F, ys, X, D, step=1.0)
    K = len(ys)
    y_lo, y_hi = F.lateral_range()
    mask = np.zeros((K, len(xg)), bool)
    for j, x in enumerate(xg):
        c = core._chord_x(F.M, x)
        if c is None:
            continue
        lo, hi = c
        mask[:, j] = (ys > lo - w) & (ys < hi + w)
    R = D[0].shape[0]
    S = np.full(R, -np.inf)
    for k in range(K - 1):
        m = mask[k] & mask[k + 1]
        if not m.any():
            continue
        slack = w - (ys[k + 1] - ys[k])
        val = np.nanmax(off[k + 1][:, m] - off[k][:, m], axis=1)
        S = np.maximum(S, (val - slack) / 2)
    if mask[0].any():
        S = np.maximum(S, np.nanmax(off[0][:, mask[0]], axis=1) - (w / 2 - (ys[0] - y_lo)))
    if mask[-1].any():
        S = np.maximum(S, np.nanmax(-off[-1][:, mask[-1]], axis=1) - (w / 2 - (y_hi - ys[-1])))
    return lam_ref + S


def certify(F, w, planner, simulate, eps, n_cal, rng, reg, lam0=0.03, iters=10):
    """Fixed-point conformal erosion for any (planner, simulator) pair."""
    lam_ref = lam0
    q = np.inf
    for _ in range(iters):
        ys = planner(lam_ref)
        cond = make_cond(rng, n_cal, reg)
        X, D = simulate(ys, cond, rng)
        S = generic_scores(F, ys, lam_ref, X, D, w)
        q = core.conformal_quantile(S, eps)
        if q <= lam_ref + 1e-9:
            return q, S
        lam_ref = q * 1.05
    return q, S


def evaluate(F, w, ys, simulate, n, seed, reg):
    rng = np.random.default_rng(seed)  # common random numbers across systems
    cond = make_cond(rng, n, reg)
    X, D = simulate(ys, cond, rng)
    miss = core.evaluate(F, ys, X, D, w)
    try:
        plen = F2C.path_length(F, ys, "boustrophedon", 4.5)
    except Exception:
        plen = np.nan
    return dict(p_nomiss=float(np.mean(miss == 0)), e_miss=float(miss.mean()),
                p95_miss=float(np.percentile(miss, 95)), passes=len(ys),
                overlap=L.overlap_ratio(F, ys, w), path_m=plen)


def sim_core(F, ctrl_factory, reg):
    def f(ys, cond, rng):
        c = ctrl_factory()
        return core.simulate(F, ys, cond, rng, ctrl=c)
    return f


def sim_seq(F, w, ctrl, reg):
    def f(ys, cond, rng):
        sp = (ys[1] - ys[0]) if len(ys) > 1 else w
        return SEQ.simulate_sequential(F, ys, cond, rng, ctrl=ctrl, spacing=sp)
    return f


def oracle_lambda(F, w, simulate, reg, seed, eps, n=1000):
    """Per-field oracle erosion for the default stack (BCD + LQR-I): (1-eps) quantile
    of fresh run scores at the converged reference plan (uses TEST-distribution data)."""
    rng = np.random.default_rng(seed + 7)
    q, _ = certify(F, w, lambda lam: core.plan(F, w, lam, UNIT), simulate, eps, 200, rng, reg)
    lam_ref = q
    ys = core.plan(F, w, lam_ref, UNIT)
    cond = make_cond(rng, n, reg)
    X, D = simulate(ys, cond, rng)
    S = generic_scores(F, ys, lam_ref, X, D, w)
    lam_star = float(np.quantile(S, 1 - eps))
    return lam_star, L.overlap_ratio(F, core.plan(F, w, lam_star, UNIT), w)


# ------------------------------------------------------------------ the systems
def systems_for(F, Ff2c, w, reg, rng, eps, n_cal, train_fields):
    """Yield (name, family, ys, simulate) for every system on this field."""
    lqri = lambda: "lqr_i"
    S_lqri = sim_core(F, lqri, reg)
    out = []
    bcd = lambda lam: core.plan(F, w, lam, UNIT)

    def add(name, family, ys, sim, field=F, extra=None):
        out.append(dict(name=name, family=family, ys=ys, sim=sim, field=field, extra=extra or {}))

    # --- industry practice -------------------------------------------------------
    add("BCD + LQR-I + 5 cm (2x vendor accuracy)", "industry", bcd(0.025), S_lqri)
    if VEND is not None:
        try:
            m_t = VEND.farmer_tuned_overlap(train_fields, rng, target=1 - eps)
            add(f"BCD + LQR-I + farmer-tuned global overlap", "industry", bcd(m_t / 2), S_lqri,
                extra=dict(param=m_t))
            vt = sim_core(F, lambda: VEND.VendorTC(), reg)
            add("BCD + vendor terrain comp. + 5 cm", "industry", bcd(0.025), vt)
            add("BCD + vendor terrain comp. + farmer-tuned", "industry", bcd(m_t / 2), vt)
        except Exception:
            traceback.print_exc()
    # --- published coverage planners --------------------------------------------
    S_f2c = sim_core(Ff2c, lqri, reg)
    f2c = lambda lam: core.plan(Ff2c, w, lam, UNIT)
    add("Fields2Cover (opt. heading) + 5 cm", "planner", f2c(0.025), S_f2c, field=Ff2c)
    t3d = lambda lam: T3D.plan_terrain3d(F, w, overlap=2 * lam)
    add("Hameed 3D terrain spacing (0 overlap)", "planner", t3d(0.0), S_lqri)
    add("Hameed 3D terrain spacing + 5 cm", "planner", t3d(0.025), S_lqri)
    S_seq = sim_seq(F, w, "lqr_i", reg)
    seq = lambda lam: SEQ.plan_fixed(F, w, 2 * lam)
    add("Follow-previous-pass guidance + 5 cm", "planner", seq(0.025), S_seq)
    # --- published path-tracking controllers -------------------------------------
    S_len = sim_core(F, lambda: LEN.LenainSSO(), reg)
    add("BCD + Lenain sideslip-observer ctrl + 5 cm", "controller", bcd(0.025), S_len)
    S_eso = sim_core(F, lambda: BC.make("esosmc"), reg)
    add("BCD + ESO sliding-mode ctrl + 5 cm", "controller", bcd(0.025), S_eso)
    S_mpc = sim_core(F, lambda: BC.make("offset_free_mpc"), reg)
    add("BCD + offset-free MPC + 5 cm", "controller", bcd(0.025), S_mpc)
    # --- model-based / robust / learning-based uncertainty layers ---------------
    if TUBE is not None:
        for var in ("W99", "Wmax"):
            try:
                lam_t = TUBE.tube_lambda(train_fields, rng, variant=var, ctrl="lqr_i")
                lam_t = lam_t[0] if isinstance(lam_t, tuple) else lam_t
                add(f"Tube-MPC radius margin ({var})", "robust", bcd(float(lam_t)), S_lqri,
                    extra=dict(param=float(lam_t)))
            except Exception:
                traceback.print_exc()
    if BEL is not None:
        for nm, fn in (("Gaussian belief, pointwise", "belief_pointwise_lambda"),
                       ("Gaussian belief, Rice extreme-value", "belief_rice_lambda"),
                       ("Model-based MC chance constraint", "model_mc_lambda")):
            try:
                lam_b = getattr(BEL, fn)(F, rng, eps, n_cal=n_cal, w=w, ctrl="lqr_i", **cond_kw(reg))
                lam_b = lam_b[0] if isinstance(lam_b, tuple) else lam_b
                add(nm, "model-based", bcd(float(lam_b)), S_lqri, extra=dict(param=float(lam_b)))
            except Exception:
                traceback.print_exc()
    try:
        z, gsig = UQ.gp_margin(F, rng, eps, n_cal=n_cal, w=w, ctrl="lqr_i", **cond_kw(reg))
        add("GP cautious margin (Hewing et al.)", "learning", core.plan(F, w, z, gsig), S_lqri)
    except Exception:
        traceback.print_exc()
    try:
        lam_l = UQ.lindemann_cp_lambda(F, rng, eps, n_cal=n_cal, w=w, ctrl="lqr_i", **cond_kw(reg))
        add("Conformal planning, union bound (Lindemann et al.)", "conformal", bcd(float(lam_l)), S_lqri,
            extra=dict(param=float(lam_l)))
    except Exception:
        traceback.print_exc()
    try:
        lam_c = UQ.cpp_lambda(F, rng, eps, n_cal=n_cal, w=w, ctrl="lqr_i", **cond_kw(reg))
        add("Conformal predictive programming (Zhao et al.)", "conformal", bcd(float(lam_c)), S_lqri,
            extra=dict(param=float(lam_c)))
    except Exception:
        traceback.print_exc()
    # --- scalar chance-constraint rules on our run score (appendix class) --------
    ys_ref = bcd(0.10)
    cond = make_cond(rng, n_cal, reg)
    X, D = S_lqri(ys_ref, cond, rng)
    Sref = generic_scores(F, ys_ref, 0.10, X, D, w)
    add("Scenario approach (PAC, beta=0.01)", "chance-rule", bcd(L.scenario_lambda(Sref, eps)), S_lqri)
    add("Gaussian chance constraint", "chance-rule", bcd(L.gaussian_score_lambda(Sref, eps)), S_lqri)
    add("Wasserstein DRO-CVaR", "chance-rule", bcd(L.dro_cvar_lambda(Sref, eps)), S_lqri)
    # --- ours: the certification layer on top of every stack ---------------------
    stacks = [("BCD + LQR-I", F, bcd, S_lqri),
              ("Fields2Cover + LQR-I", Ff2c, f2c, S_f2c),
              ("Hameed 3D + LQR-I", F, t3d, S_lqri),
              ("Follow-previous-pass + LQR-I", F, seq, S_seq),
              ("BCD + Lenain ctrl", F, bcd, S_len),
              ("BCD + offset-free MPC", F, bcd, S_mpc)]
    for nm, field, planner, sim in stacks:
        try:
            t0 = time.time()
            q, _ = certify(field, w, planner, sim, eps, n_cal, rng, reg)
            add(f"{nm} + CE (ours)", "ours", planner(q), sim, field=field,
                extra=dict(param=float(q), calib_s=time.time() - t0))
        except ValueError:
            add(f"{nm} + CE (ours)", "ours", None, sim, field=field, extra=dict(infeasible=True))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields", type=int, default=30)
    ap.add_argument("--n-cal", type=int, default=100)
    ap.add_argument("--n-test", type=int, default=200)
    ap.add_argument("--eps", type=float, default=0.1)
    ap.add_argument("--regimes", default="all")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    SHARD = "" if args.nshards == 1 else f"_shard{args.shard}of{args.nshards}"
    regs = REGIMES if args.regimes == "all" else {k: v for k, v in REGIMES.items() if k.startswith(args.regimes)}
    jobs = []
    for rname, reg in regs.items():
        fields = core.load_fields(reg["kind"], w=reg["w"], seed=0)
        train, evalf = fields[:5], fields[20:20 + args.fields]
        for F in evalf:
            jobs.append((rname, reg, train, F))
    jobs = jobs[args.shard::args.nshards]
    rows = []
    for ji, (rname, reg, train, F) in enumerate(jobs):
        t_job = time.time()
        w = reg["w"]
        seed = 100003 * F.fid + 17 * len(rname)
        rng = np.random.default_rng(seed)
        try:
            Ff2c = F2C.make_field(F.fid, F.meta, F2C.best_heading(F.meta, w=w), w=w)
        except Exception:
            Ff2c = F
        try:
            lam_star, ov_star = oracle_lambda(F, w, sim_core(F, lambda: "lqr_i", reg), reg, seed, args.eps)
        except ValueError:
            lam_star, ov_star = np.nan, np.nan
        for s in systems_for(F, Ff2c, w, reg, rng, args.eps, args.n_cal, train):
            base = dict(regime=rname, kind=reg["kind"], w=w, field=F.fid, slope=F.z_mean_slope,
                        area_ha=F.M.area / 1e4, system=s["name"], family=s["family"],
                        oracle_lam=lam_star, oracle_overlap=ov_star, **s["extra"])
            if s["ys"] is None:
                rows.append(dict(base, p_nomiss=np.nan, infeasible=True))
                continue
            try:
                r = evaluate(s["field"], w, s["ys"], s["sim"], args.n_test, seed + 1, reg)
            except ValueError:
                rows.append(dict(base, p_nomiss=np.nan, infeasible=True))
                continue
            r["regret_pp"] = (r["overlap"] - ov_star) * 100 if np.isfinite(ov_star) else np.nan
            rows.append(dict(base, **r))
        print(f"[{ji+1}/{len(jobs)}] {rname} field {F.fid}: {time.time()-t_job:.0f}s", flush=True)
        os.makedirs(RES, exist_ok=True)
        pd.DataFrame(rows).to_csv(os.path.join(RES, f"system{args.tag}{SHARD}.csv"), index=False)


if __name__ == "__main__":
    main()

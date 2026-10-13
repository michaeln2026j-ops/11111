"""E2b SYSTEM-LEVEL comparison against published algorithms.

Every system = (coverage planner) x (path-tracking controller) x (margin /
certification layer). All systems are executed by the SAME corrected simulator on
the SAME real fields with common random numbers (one seed per field x regime),
and scored by the SAME evaluator (core.evaluate). Our conformal-erosion layer is
applied on top of every planner/controller (the "+CE" rows) to show it is a
planner- and controller-agnostic certification layer.

Regimes (representative operating conditions; GNSS errors are REAL NOAA CORS series of the
receiver grade, a random station-pair-day and start time per run, see core.gnss_bank):
  R1 RTK flat 3 m        : wheat fields (North China Plain), RTK fix, 3 m implement
  R2 RTK hilly-wet 1.5 m : paddy fields (hilly south), RTK fix, 1.5 m implement, wet soil (0.6-0.9)
  R3 DGPS hilly 6 m      : paddy fields, code-differential (sub-metre) guidance, 6 m implement
"spec overlap" = 2 x the manufacturer pass-to-pass accuracy of the grade (RTK 2.5 cm, DGPS 20 cm).

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

# p2p: manufacturer pass-to-pass accuracy of the receiver grade; "spec overlap" = 2 x p2p
# (RTK 2.5 cm; SBAS/DGPS-class sub-metre guidance about 15-25 cm, e.g. StarFire SF1 / RangePoint RTX)
REGIMES = {
    "R1 RTK flat 3 m": dict(kind="wheat", w=3.0, p2p=0.025, cond=dict(gnss="rtk_fix")),
    "R2 RTK hilly-wet 1.5 m": dict(kind="paddy", w=1.5, p2p=0.025,
                                   cond=dict(gnss="rtk_fix", moisture_range=(0.6, 0.9))),
    "R3 DGPS hilly 6 m": dict(kind="paddy", w=6.0, p2p=0.20, cond=dict(gnss="dgps")),
}


def cond_kw(reg):
    return dict(reg["cond"])


def make_cond(rng, n, reg):
    return core.Condition(rng, n, **cond_kw(reg))


# ------------------------------------------------------------- generic machinery
def generic_scores(F, ys, lam_ref, X, D, w):
    """Run-level score of an arbitrary plan executed at erosion lam_ref: EXACT, i.e. zero missed area
    (core.evaluate) <=> S <= lam_ref (covering radius per x-section, core.exact_scores)."""
    return core.exact_scores(F, ys, X, D, w, lam_ref)


def certify(F, w, planner, simulate, eps, n_cal, rng, reg, lam0=0.03, iters=10):
    """Two-stage fixed-point conformal erosion for any (planner, simulator) pair.

    Stage 1 (pilot batches): lam_ref <- 1.05 q until q <= lam_ref (dominating reference plan).
    Stage 2 (certificate): a FRESH batch at the frozen plan pi(lam_ref); its quantile q* is never used
    to decide when to stop, so it is not selected (stopping on the batch that triggered the stop
    biases q downwards: score-level coverage 0.893 < 0.900 in the v5 audit).
    Deployment, assumption-free: pi(lam_ref) when q* <= lam_ref, because zero miss <=> S <= lam_ref
    exactly for the deployed plan itself, so P(no miss) >= P(S <= q*) >= 1 - eps without any
    assumption on how execution depends on the plan; otherwise (rare, flagged) pi(q*).
    Returns dict(q, lam_ref, lam_dep, dominated, S, pilot_iters)."""
    lam_ref = lam0
    it = 0
    for it in range(1, iters + 1):
        ys = planner(lam_ref)
        cond = make_cond(rng, n_cal, reg)
        X, D = simulate(ys, cond, rng)
        q = core.conformal_quantile(generic_scores(F, ys, lam_ref, X, D, w), eps)
        if q <= lam_ref + 1e-9:
            break
        lam_ref = q * 1.05
    ys = planner(lam_ref)
    cond = make_cond(rng, n_cal, reg)
    X, D = simulate(ys, cond, rng)
    S = generic_scores(F, ys, lam_ref, X, D, w)
    q = float(core.conformal_quantile(S, eps))
    dom = bool(q <= lam_ref + 1e-9)
    return dict(q=q, lam_ref=float(lam_ref), lam_dep=float(lam_ref if dom else q), dominated=dom, S=S,
                pilot_iters=it)


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


def sim_vendor(F, reg):
    """Commercial terrain-compensated autosteer: raw antenna position (comp = 0) + IMU roll correction."""
    def f(ys, cond, rng):
        c = VEND.VendorTC(F, ys, seed=int(F.fid) * 7 + 1)
        comp0 = cond.comp.copy()
        cond.comp[:] = 0.0
        try:
            return core.simulate(F, ys, cond, rng, ctrl=c)
        finally:
            cond.comp[:] = comp0
    return f


_TUNED = {}  # (regime, what) -> parameter tuned once on the training fields


def tuned(key, fn):
    if key not in _TUNED:
        try:
            _TUNED[key] = fn()
        except Exception:
            traceback.print_exc()
            _TUNED[key] = None
    return _TUNED[key]


def sim_seq(F, w, ctrl, reg):
    def f(ys, cond, rng):
        sp = (ys[1] - ys[0]) if len(ys) > 1 else w
        return SEQ.simulate_sequential(F, ys, cond, rng, ctrl=ctrl, spacing=sp)
    return f


def oracle_lambda(F, w, simulate, reg, seed, eps, n=1000):
    """Per-field oracle erosion for the default stack (BCD + LQR-I): (1-eps) quantile
    of fresh run scores at the converged reference plan (uses TEST-distribution data)."""
    rng = np.random.default_rng(seed + 7)
    lam_ref = certify(F, w, lambda lam: core.plan(F, w, lam, UNIT), simulate, eps, 200, rng, reg,
                      lam0=reg["p2p"])["lam_dep"]
    ys = core.plan(F, w, lam_ref, UNIT)
    cond = make_cond(rng, n, reg)
    X, D = simulate(ys, cond, rng)
    S = generic_scores(F, ys, lam_ref, X, D, w)  # exact: the erosion at which each run starts missing
    lam_star = float(np.quantile(S, 1 - eps))
    ys_star = core.plan(F, w, lam_star, UNIT)
    chk = evaluate(F, w, ys_star, simulate, 200, seed + 3, reg)  # sanity: P(no miss) of the oracle plan
    return lam_star, L.overlap_ratio(F, ys_star, w), chk["p_nomiss"]


# ------------------------------------------------------------------ the systems
def systems_for(F, Ff2c, w, reg, rng, eps, n_cal, train_fields, rname=""):
    """Yield (name, family, ys, simulate) for every system on this field."""
    lqri = lambda: "lqr_i"
    S_lqri = sim_core(F, lqri, reg)
    out = []

    def safe(planner):  # infeasible margin (no plan fits the field) -> None, recorded as infeasible
        def g(lam):
            try:
                return planner(lam)
            except ValueError:
                return None
        return g

    bcd = lambda lam: core.plan(F, w, lam, UNIT)
    bcd_s = safe(bcd)
    p2p = reg["p2p"]
    ck = cond_kw(reg)

    def add(name, family, ys, sim, field=F, extra=None):
        out.append(dict(name=name, family=family, ys=ys, sim=sim, field=field, extra=extra or {}))

    # --- industry practice -------------------------------------------------------
    add("BCD + LQR-I + spec overlap (2x vendor p2p)", "industry", bcd_s(p2p), S_lqri, extra=dict(param=p2p))
    big = p2p > 0.05
    tune_kw = dict(target=1 - eps, w=w, grid=0.05 if big else 0.01, coarse=0.2 if big else 0.04,
                   o_max=4.0 if big else 1.0, **ck)
    m_l = tuned((rname, "farmer_lqri"), lambda: VEND.farmer_tuned_overlap(train_fields, rng, ctrl="lqr_i", **tune_kw))
    if m_l is not None and np.isfinite(m_l):
        add("BCD + LQR-I + farmer-tuned global overlap", "industry", bcd_s(m_l / 2), S_lqri,
            extra=dict(param=m_l / 2))
    if VEND is not None:
        S_vt = sim_vendor(F, reg)
        add("BCD + vendor terrain comp. + spec overlap", "industry", bcd_s(p2p), S_vt, extra=dict(param=p2p))
        m_v = tuned((rname, "farmer_vendor"), lambda: VEND.farmer_tuned_overlap(train_fields, rng, ctrl="vendor",
                                                                                **tune_kw))
        if m_v is not None and np.isfinite(m_v):
            add("BCD + vendor terrain comp. + farmer-tuned", "industry", bcd_s(m_v / 2), S_vt,
                extra=dict(param=m_v / 2))
    # --- published coverage planners --------------------------------------------
    S_f2c = sim_core(Ff2c, lqri, reg)
    f2c = lambda lam: core.plan(Ff2c, w, lam, UNIT)
    add("Fields2Cover (opt. heading) + spec overlap", "planner", safe(f2c)(p2p), S_f2c, field=Ff2c)
    t3d = lambda lam: T3D.plan_terrain3d(F, w, overlap=2 * lam)
    add("Hameed 3D terrain spacing (0 overlap)", "planner", safe(t3d)(0.0), S_lqri)
    add("Hameed 3D terrain spacing + spec overlap", "planner", safe(t3d)(p2p), S_lqri)
    S_seq = sim_seq(F, w, "lqr_i", reg)
    seq = lambda lam: SEQ.plan_fixed(F, w, 2 * lam)
    add("Follow-previous-pass guidance + spec overlap", "planner", safe(seq)(p2p), S_seq)
    # --- published path-tracking controllers -------------------------------------
    S_len = sim_core(F, lambda: LEN.LenainSSO(), reg)
    add("BCD + Lenain sideslip-observer ctrl + spec overlap", "controller", bcd_s(p2p), S_len)
    S_eso = sim_core(F, lambda: BC.make("esosmc"), reg)
    add("BCD + ESO sliding-mode ctrl + spec overlap", "controller", bcd_s(p2p), S_eso)
    S_mpc = sim_core(F, lambda: BC.make("offset_free_mpc"), reg)
    add("BCD + offset-free MPC + spec overlap", "controller", bcd_s(p2p), S_mpc)
    # --- model-based / robust / learning-based uncertainty layers ---------------
    if TUBE is not None:
        for var in ("W99", "Wmax"):
            try:
                lam_t = tuned((rname, "tube_" + var),
                              lambda: TUBE.tube_lambda(train_fields, rng, variant=var, ctrl="lqr_i", w=w, **ck))
                lam_t = lam_t[0] if isinstance(lam_t, tuple) else lam_t
                add(f"Tube-MPC radius margin ({var})", "robust", bcd_s(float(lam_t)), S_lqri,
                    extra=dict(param=float(lam_t)))
            except Exception:
                traceback.print_exc()
    if BEL is not None:
        for nm, fn in (("Gaussian belief, pointwise", "belief_pointwise_lambda"),
                       ("Gaussian belief, Rice extreme-value", "belief_rice_lambda"),
                       ("Model-based MC chance constraint", "model_mc_lambda")):
            try:
                lam_b = getattr(BEL, fn)(F, rng, eps, n_cal=n_cal, w=w, ctrl="lqr_i", **ck)
                lam_b = lam_b[0] if isinstance(lam_b, tuple) else lam_b
                add(nm, "model-based", bcd_s(float(lam_b)), S_lqri, extra=dict(param=float(lam_b)))
            except Exception:
                traceback.print_exc()
    for nm, kw in (("GP cautious margin (Hewing et al.)", dict()),
                   ("GP cautious margin, Bonferroni (Hewing et al.)", dict(union=True))):
        try:
            z, gsig = UQ.gp_margin(F, rng, eps, n_cal=n_cal, w=w, ctrl="lqr_i", **kw, **ck)
            add(nm, "learning", safe(lambda z_: core.plan(F, w, z_, gsig))(z), S_lqri, extra=dict(param=float(z)))
        except Exception:
            traceback.print_exc()
    for nm, gran in (("Conformal planning, union bound (Lindemann et al.)", "point"),
                     ("Conformal planning, pair-level union bound (Lindemann et al.)", "pair")):
        try:
            lam_l = UQ.lindemann_cp_lambda(F, rng, eps, n_cal=n_cal, w=w, ctrl="lqr_i", granularity=gran, **ck)
            add(nm, "conformal", bcd_s(float(lam_l)), S_lqri, extra=dict(param=float(lam_l)))
        except Exception:
            traceback.print_exc()
    try:
        lam_c = UQ.cpp_lambda(F, rng, eps, n_cal=n_cal, w=w, ctrl="lqr_i", **ck)
        add("Conformal predictive programming (Zhao et al.)", "conformal", bcd_s(float(lam_c)), S_lqri,
            extra=dict(param=float(lam_c)))
    except Exception:
        traceback.print_exc()
    # --- scalar chance-constraint rules on our run score (appendix class) --------
    # reference plan of the scalar rules: same conservative reference (4 x spec) for every rule
    lam_r = 4 * p2p
    ys_ref = bcd(lam_r)
    cond = make_cond(rng, n_cal, reg)
    X, D = S_lqri(ys_ref, cond, rng)
    Sref = generic_scores(F, ys_ref, lam_r, X, D, w)
    add("Scenario approach (PAC, beta=0.01)", "chance-rule", bcd_s(L.scenario_lambda(Sref, eps)), S_lqri)
    add("Gaussian chance constraint", "chance-rule", bcd_s(L.gaussian_score_lambda(Sref, eps)), S_lqri)
    add("Wasserstein DRO-CVaR", "chance-rule", bcd_s(L.dro_cvar_lambda(Sref, eps)), S_lqri)
    # --- ours: the certification layer on top of every stack ---------------------
    stacks = [("BCD + LQR-I", F, bcd, S_lqri),
              ("Fields2Cover + LQR-I", Ff2c, f2c, S_f2c),
              ("Hameed 3D + LQR-I", F, t3d, S_lqri),
              ("Follow-previous-pass + LQR-I", F, seq, S_seq),
              ("BCD + Lenain ctrl", F, bcd, S_len),
              ("BCD + offset-free MPC", F, bcd, S_mpc)]
    thm2 = {"BCD + LQR-I", "Fields2Cover + LQR-I", "BCD + Lenain ctrl", "BCD + offset-free MPC"}
    for nm, field, planner, sim in stacks:
        try:
            t0 = time.time()
            c = certify(field, w, planner, sim, eps, n_cal, rng, reg, lam0=p2p)
            ex = dict(q_cert=c["q"], lam_ref=c["lam_ref"], dominated=c["dominated"], pilot_iters=c["pilot_iters"],
                      calib_s=time.time() - t0)
            add(f"{nm} + CE (ours)", "ours", safe(planner)(c["lam_dep"]), sim, field=field,
                extra=dict(param=c["lam_dep"], **ex))
            if nm in thm2:  # straight-line tracking of a uniform BCD plan: Theorem 2 also certifies pi(q*)
                add(f"{nm} + CE-q (ours, Thm 2)", "ours", safe(planner)(c["q"]), sim, field=field,
                    extra=dict(param=c["q"], **ex))
        except ValueError:
            add(f"{nm} + CE (ours)", "ours", None, sim, field=field, extra=dict(infeasible=True))
            if nm in thm2:
                add(f"{nm} + CE-q (ours, Thm 2)", "ours", None, sim, field=field, extra=dict(infeasible=True))
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
            Ff2c = F2C.make_field(F.fid, F.meta, F2C.best_heading(F.meta, w=w, overlap=2 * reg["p2p"]), w=w)
        except Exception:
            Ff2c = F
        try:
            lam_star, ov_star, p_star = oracle_lambda(F, w, sim_core(F, lambda: "lqr_i", reg), reg, seed, args.eps)
        except ValueError:
            lam_star, ov_star, p_star = np.nan, np.nan, np.nan
        for s in systems_for(F, Ff2c, w, reg, rng, args.eps, args.n_cal, train, rname=rname):
            base = dict(regime=rname, kind=reg["kind"], w=w, field=F.fid, slope=F.z_mean_slope,
                        area_ha=F.M.area / 1e4, system=s["name"], family=s["family"],
                        oracle_lam=lam_star, oracle_overlap=ov_star, oracle_p=p_star, **s["extra"])
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

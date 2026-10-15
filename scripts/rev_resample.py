"""RV2 / RV3 / RV4 analyses (docs/prereg_revision.md): cross-field resampling with configuration-aware baselines and
per-configuration coverage, and target-field calibration with few runs, on the nominal model or a truth variant.

    python3 scripts/rev_resample.py rv2            # nominal model, banks and curves of E-low v2/v3
    python3 scripts/rev_resample.py rv3            # small-n CE-q on the same fields
    python3 scripts/rev_resample.py rv4            # every truth variant of results/revision/mm_*.pkl
"""
import glob
import math
import os
import pickle
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import ceplus as CP  # noqa: E402
import exp_lowdata as X  # noqa: E402
import truth as TR  # noqa: E402
from analyze_lowdata_v3 import CQR, KEYS, load  # noqa: E402

RES = os.path.join(HERE, "..", "results")
REV = os.path.join(RES, "revision")
EPS, DELTA, REPS = 0.1, 0.1, 4000
FARMER = {"R1": 0.12, "R2": 0.14, "R3": 0.35}  # v8 farmer-tuned and vendor margins (results/v8/system_v8.csv)
VENDOR = {"R1": 0.025, "R2": 0.025, "R3": 0.20}


def edge_q():
    """R3 theory 0.9-quantile with the field-edge terms, by (key, fid) (check_boundary / RV6 outputs)."""
    out = {}
    for f in glob.glob(os.path.join(RES, "lowdata_v3", "check_boundary_R3*.txt")) + \
            glob.glob(os.path.join(REV, "rv6_edges_R3*.txt")):
        for m in re.finditer(r"(R\d) field\s+(\d+)\s+passes\s+\d+: q_old [\d.]+\s+q_new ([\d.]+)", open(f).read()):
            out[(m.group(1), int(m.group(2)))] = float(m.group(3))
    return out


def nominal_records():
    recs = []
    for d in ("lowdata_v2", "lowdata_v3"):
        for r in load(os.path.join(RES, d)):
            r["cur"] = pickle.load(open(os.path.join(RES, d, f"curve_{r['key']}_{r['fi']}.pkl"), "rb"))
            r["bank"] = pickle.load(open(os.path.join(RES, d, f"hist_{r['key']}_{r['fi']}.pkl"), "rb"))
            recs.append(r)
    return recs


def add_pivots(recs):
    cqr = CQR([r for r in load(os.path.join(RES, "lowdata"))])  # E-low v1 fields only, one run each
    eq = edge_q()
    for r in recs:
        lg = math.sqrt(2 * math.log(max(r["N_len"], 2.0)))
        th = X.inv_cdf(r["tgrid"], r["Fhat"], 1 - EPS) if r["ok"] else np.nan
        tw = os.path.join(REV, f"twin_{r['key']}_{r['fi']}.pkl")
        r["q"] = {"raw": 1.0, "spec x scale law": r["reg"]["p2p"] * lg, "theory": th,
                  "theory+edges": eq.get((r["key"], r["fid"]), th) if r["key"] == "R3" else th,
                  "CQR": cqr(r), "MC twin": pickle.load(open(tw, "rb"))["q"] if os.path.exists(tw) else np.nan}
    return recs


def read(r, lam):
    c = r["cur"]
    return np.interp(lam, c["lam"], c["P"]), 100 * (np.interp(lam, c["lam"], c["ov"]) - r["oracle_overlap"])


def resample(pool, names, n_cal, rng, reps=REPS):
    """Returns {(name, cls): dict(cov, cov_cfg, refuse, ex_dep, ex_cap)}."""
    n = len(pool)
    cfg = np.array([r["key"] for r in pool])
    out = {}
    for cls, dl in (("marginal", None), ("PAC", DELTA)):
        for nm in names:
            cov, ref, exd, exc = np.empty(reps), np.empty(reps), np.empty(reps), np.empty(reps)
            covc = {k: [] for k in KEYS}
            for b in range(reps):
                perm = rng.permutation(n)
                cal, tgt = perm[:n_cal], perm[n_cal:]
                s = np.array([pool[i]["bank"][rng.integers(len(pool[i]["bank"]))] for i in cal])
                lam = np.empty(len(tgt))
                if nm == "Mondrian":
                    for k in KEYS:
                        t = CP.quantile(s[cfg[cal] == k], EPS, dl) if np.any(cfg[cal] == k) else np.inf
                        lam[cfg[tgt] == k] = t
                elif nm == "per-config scale":
                    med = {k: (np.median(s[cfg[cal] == k]) if np.any(cfg[cal] == k) else np.nan) for k in KEYS}
                    qc = np.array([med[k] for k in cfg[cal]])
                    t = CP.quantile(np.where(np.isfinite(qc), s / qc, np.inf), EPS, dl)
                    lam = np.array([med[k] for k in cfg[tgt]]) * t
                else:
                    qc = np.array([pool[i]["q"][nm] for i in cal])
                    t = CP.quantile(np.where(np.isfinite(qc), s / qc, np.inf), EPS, dl)
                    lam = np.array([pool[g]["q"][nm] for g in tgt]) * t
                ok = np.isfinite(lam)
                ps, es = np.empty(len(tgt)), np.empty(len(tgt))
                for j, g in enumerate(tgt):
                    r = pool[g]
                    ps[j], es[j] = read(r, min(lam[j], r["cap"]) if ok[j] else r["cap"])
                cov[b], ref[b] = ps.mean(), 1 - ok.mean()
                exc[b] = es.mean()
                exd[b] = es[ok].mean() if ok.any() else np.nan
                for k in KEYS:
                    m = cfg[tgt] == k
                    if m.any():
                        covc[k].append(ps[m].mean())
            out[(nm, cls)] = dict(cov=cov, cov_cfg={k: np.array(v) for k, v in covc.items()}, refuse=ref,
                                  ex_dep=exd, ex_cap=exc)
    return out


def report(res, title, out):
    out.append(f"\n== {title}")
    out.append(f"  {'pivot':18s} {'class':8s} {'coverage':>8s} {'valid':>5s} {'refuse':>6s} "
               + " ".join(f"{'cov ' + k:>8s}" for k in KEYS) + f" {'excess(dep)':>11s} {'excess(cap)':>11s}")
    for (nm, cls), v in res.items():
        if cls == "marginal":
            ok = v["cov"].mean() >= 1 - EPS - 0.005
            cc = " ".join(f"{v['cov_cfg'][k].mean():8.3f}" if len(v['cov_cfg'][k]) else f"{'-':>8s}" for k in KEYS)
            cv = f"{v['cov'].mean():8.4f}"
        else:
            ok = np.mean(v["cov"] >= 1 - EPS) >= 1 - DELTA - 0.02
            cc = " ".join(f"{np.mean(v['cov_cfg'][k] >= 0.9):8.3f}" if len(v['cov_cfg'][k]) else f"{'-':>8s}" for k in KEYS)
            cv = f"{np.mean(v['cov'] >= 0.9):8.3f}"
        out.append(f"  {nm:18s} {cls:8s} {cv} {'PASS' if ok else 'FAIL':>5s} {v['refuse'].mean():6.3f} {cc} "
                   f"{np.nanmean(v['ex_dep']):+11.2f} {v['ex_cap'].mean():+11.2f}")


def small_n(pool, out, reps=2000, title="RV3"):
    rng = np.random.default_rng(1)
    out.append(f"\n== {title}: target-field CE-q from n runs of the field's bank ({reps} replicates per field); "
               f"coverage = mean P(no miss) / fraction of cells >= 0.9; excess pp")
    for key in KEYS:
        rr = [r for r in pool if r["key"] == key]
        out.append(f"  {key} ({len(rr)} fields)")
        for n in (9, 15, 22, 40, 100):
            for cls, dl in (("marginal", None), ("PAC", DELTA)):
                if cls == "PAC" and n < 22:
                    continue
                k = CP.order_index(n, EPS, dl)
                P, Ex = [], []
                for r in rr:
                    b = np.asarray(r["bank"])
                    idx = rng.random((reps, len(b))).argsort(axis=1)[:, :n]
                    lam = np.sort(b[idx], axis=1)[:, k - 1] if k <= n else np.full(reps, np.inf)
                    lam = np.minimum(lam, r["cap"])
                    c = r["cur"]
                    P.append(np.interp(lam, c["lam"], c["P"]))
                    Ex.append(100 * (np.interp(lam, c["lam"], c["ov"]) - r["oracle_overlap"]))
                P, Ex = np.concatenate(P), np.concatenate(Ex)
                out.append(f"    n={n:3d} {cls:8s} coverage {P.mean():.4f} / {np.mean(P >= 0.9):.3f}  excess {Ex.mean():+6.2f}")
        for lab, tab in (("farmer-tuned", FARMER), ("vendor 2x p2p", VENDOR)):
            pe = [read(r, min(tab[key], r["cap"])) for r in rr]
            out.append(f"    {lab:12s} lam {tab[key]:.3f}: coverage {np.mean([p for p, _ in pe]):.4f} / "
                       f"{np.mean([p >= 0.9 for p, _ in pe]):.3f}  excess {np.mean([e for _, e in pe]):+6.2f}")


def rv2():
    recs = add_pivots(nominal_records())
    out = ["RV2 (pre-registered, docs/prereg_revision.md): mixed-fleet cross-field resampling, nominal model. "
           "Marginal: mean coverage (PASS if >= 0.895); PAC: fraction of replicates with coverage >= 0.9 (PASS if >= 0.88). "
           "Per-configuration columns: marginal mean coverage / PAC fraction >= 0.9. excess(dep): over deployed fields; "
           "excess(cap): refused fields deployed at the cap."]
    names = ["raw", "spec x scale law", "theory", "theory+edges", "Mondrian", "per-config scale", "CQR", "MC twin"]
    names = [n for n in names if n in ("Mondrian", "per-config scale") or all(np.isfinite(r["q"][n]) or n == "theory" for r in recs)]
    for n_cal in (25, 60):
        res = resample(recs, names, n_cal, np.random.default_rng(n_cal))
        report(res, f"mixed fleet, {len(recs)} fields, n_cal = {n_cal}, {REPS} replicates", out)
    txt = "\n".join(out)
    open(os.path.join(REV, "rv2_resampling.txt"), "w").write(txt + "\n")
    print(txt)


def rv3():
    recs = nominal_records()
    out = ["RV3 (pre-registered): target-field CE-q with few runs, nominal model."]
    small_n(recs, out)
    txt = "\n".join(out)
    open(os.path.join(REV, "rv3_small_n.txt"), "w").write(txt + "\n")
    print(txt)


def variant_records(variant, base):
    recs = []
    by = {(r["key"], r["fi"]): r for r in base}
    for f in sorted(glob.glob(os.path.join(REV, f"mm_{TR.SHORT[variant]}_*.pkl"))):
        m = pickle.load(open(f, "rb"))
        r0 = by[(m["key"], m["fi"])]
        c = m["cur"]
        if len(c["lam"]) == 0 or c["P"].max() < 0.9:
            lam_s, ov_s = np.nan, np.nan
        else:
            i = int(np.argmax(c["P"] >= 0.9))
            lam_s = c["lam"][i] if i == 0 else np.interp(0.9, c["P"][i - 1:i + 1], c["lam"][i - 1:i + 1])
            ov_s = np.interp(lam_s, c["lam"], c["ov"])
        r = dict(r0, bank=m["bank"], cur=c, oracle_lam=lam_s, oracle_overlap=ov_s, variant=variant)
        recs.append(r)
    return recs


def rv4():
    base = add_pivots(nominal_records())
    out = ["RV4 (pre-registered): model mismatch. Theory, MC twin and all fixed pivots use the NOMINAL model; banks "
           "(calibration runs) and curves (test runs) come from the truth variant. Fields whose truth curve never "
           "reaches P 0.9 below the cap have no oracle; their excess is not defined and they are counted separately."]
    for v in TR.VARIANTS:
        if v == "nominal":
            continue
        recs = variant_records(v, base)
        if not recs:
            continue
        out.append(f"\n######## {v}: {len(recs)} fields")
        for key in KEYS:
            rr = [r for r in recs if r["key"] == key]
            if not rr:
                continue
            qt = np.array([np.quantile(r["bank"], 0.9) for r in rr])
            for nm in ("theory", "theory+edges", "MC twin"):
                q = np.array([r["q"][nm] for r in rr])
                e = np.log(q / qt)
                out.append(f"  {key} accuracy {nm:13s}: log(q/q_truth) mean {np.nanmean(e):+.3f} sd {np.nanstd(e, ddof=1):.3f}")
            out.append(f"  {key} fields without a feasible truth oracle: {int(sum(not np.isfinite(r['oracle_lam']) for r in rr))}/{len(rr)}")
        feas = [r for r in recs if np.isfinite(r["oracle_lam"])]
        for r in feas:
            r["oracle_overlap"] = float(r["oracle_overlap"])
        names = ["raw", "spec x scale law", "theory+edges", "Mondrian", "MC twin"]
        for n_cal in (25, 60):
            if len(feas) <= n_cal + 10:
                continue
            res = resample(feas, names, n_cal, np.random.default_rng(n_cal), reps=2000)
            report(res, f"{v}: mixed fleet, {len(feas)} feasible fields, n_cal = {n_cal}, 2000 replicates", out)
        small_n(feas, out, reps=500, title=f"{v}: target-field CE-q")
    txt = "\n".join(out)
    open(os.path.join(REV, "rv4_mismatch.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    {"rv2": rv2, "rv3": rv3, "rv4": rv4}[sys.argv[1]]()

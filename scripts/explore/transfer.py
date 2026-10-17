"""Transfer gap: P(S at the lam0 plan <= lam) vs P(no miss of the plan built with erosion lam), same runs' seeds."""
import sys, pickle, numpy as np
sys.path.insert(0, '/home/user/11111/experiments')
import exp_lowdata as X, exp_system as E, core
key = sys.argv[1]; fis = [int(a) for a in sys.argv[2:]]
rname, reg = X.regime(key); w = reg['w']
fields = core.load_fields(reg['kind'], w=w, seed=0)
n = 300
for fi in fis:
    r = pickle.load(open(f'/home/user/11111/results/lowdata/A_{key}_{fi}.pkl', 'rb'))
    F = fields[fi]; S_l = E.sim_core(F, lambda: "lqr_i", reg)
    lam0 = r['lam0']; ys0 = core.plan(F, w, lam0, E.UNIT)
    rng = np.random.default_rng(7 + fi); cond = E.make_cond(rng, n, reg); Xs, Ds = S_l(ys0, cond, rng)
    S = core.exact_scores(F, ys0, Xs, Ds, w, lam0)
    out = []
    for lam in r['oracle_lam'] * np.array([0.9, 1.0, 1.1]):
        ys = core.plan(F, w, lam, E.UNIT)
        rng = np.random.default_rng(7 + fi); cond = E.make_cond(rng, n, reg); Xl, Dl = S_l(ys, cond, rng)
        miss = core.evaluate(F, ys, Xl, Dl, w)
        Sl = core.exact_scores(F, ys, Xl, Dl, w, lam)
        out.append(f"lam {lam:.3f} K {len(ys)}/{len(ys0)}: P(S0<=lam) {np.mean(S <= lam):.3f}  P(nomiss) {np.mean(miss == 0):.3f}  P(S_lam<=lam) {np.mean(Sl <= lam):.3f}")
    print(key, fi, " | ".join(out), flush=True)

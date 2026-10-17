"""How much within-field run-to-run spread does the start-of-run XTE probe z explain?"""
import sys, pickle, numpy as np
sys.path.insert(0, '/home/user/11111/experiments')
import ceplus as CP, exp_lowdata as X, exp_system as E, core
key = sys.argv[1]; fis = [int(a) for a in sys.argv[2:]]
rname, reg = X.regime(key); w = reg['w']
fields = core.load_fields(reg['kind'], w=w, seed=0)
n = 300
for fi in fis:
    r = pickle.load(open(f'/home/user/11111/results/lowdata/A_{key}_{fi}.pkl', 'rb'))
    F = fields[fi]; S_l = E.sim_core(F, lambda: "lqr_i", reg)
    ys0 = core.plan(F, w, r['lam0'], E.UNIT)
    rng = np.random.default_rng(11 + fi); cond = E.make_cond(rng, n, reg)
    z = CP.probe_xte(F, w, cond, lambda: "lqr_i", 5 + fi)
    Xs, Ds = S_l(ys0, cond, rng); S = core.exact_scores(F, ys0, Xs, Ds, w, r['lam0'])
    b = np.polyfit(z, S, 1); res = S - np.polyval(b, z)
    tail = lambda a: np.quantile(a, .97) / np.quantile(a, .9)
    print(f"{key} {fi}: corr(S,z) {np.corrcoef(S, z)[0,1]:.2f}  R2 {1 - res.var()/S.var():.2f}  "
          f"sd(S)/q0.9 {S.std()/np.quantile(S,.9):.3f}  sd(S/z)/q {np.std(S/z)/np.quantile(S/z,.9):.3f}  "
          f"q.97/q.9 raw {tail(S):.3f}  S/z {tail(S/z):.3f}", flush=True)

# Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations

*Draft v0.3 (body text). Every number below is copied from a file in this repository; each table carries an HTML comment naming its source. Items marked TODO are open; the bibliography has been verified against publisher, proceedings or repository records (remaining [CHECK] markers, if any, need bibliographic verification before submission).*

---

## Abstract

Coverage path planners for tillage, seeding, spraying and harvesting assume that the machine executes the planned passes exactly. In practice, cross-track error between adjacent passes leaves unworked strips, and industry practice compensates with a fixed overlap that is either too small to prevent misses or too large to be economical. We formulate coverage planning under execution uncertainty as a chance-constrained problem on a random set and propose conformal erosion (CE): the implement footprint is eroded by a margin $\lambda$ calibrated with conformal prediction, so that the probability of zero missed area is at least $1-\varepsilon$ in finite samples, without a model of the error distribution. We show that the run score used by CE is the smallest valid score, so that CE is never more conservative than any other valid score under the same order-statistic rule, and we bound the effect of decision dependence (the deployed plan differs from the calibrated one) by a multiplicative transfer factor. A five-layer extreme-value theory (Lyapunov covariance, discrete Kac–Rice, product form, mixed Poisson, Gumbel scale law) predicts the required margin from controller parameters and terrain alone; on held-out fields its 0.9-quantile predictions deviate from simulation by −0.6% to +1.4%. Using this prediction only as a pivot for cross-field conformal calibration (CE-EVT-R) retains a distribution-free guarantee for fields with no operation history; a pre-registered resampling check over both sources of randomness (which fields calibrate, and which historical run each contributes; 4000 replicates) confirmed the guarantee in all 26 tested cells. Three pre-registered low-data experiments are reported in sequence. The first failed. In the second, both registered claims were met (excess overlap 1.56 → 0.27 percentage points, RTK flat, PAC; 1.10 → −0.38 points, DGPS hilly, marginal), but a post hoc matched-coverage analysis shows that these gains were mostly differences in the realised coverage of one calibration draw: within one machine configuration, field-level pivots differ by tenths of a point at matched coverage, consistent with an information limit we derive. In the third, on a fleet mixing three machine configurations, the theory pivot reduced excess overlap from 24.80 to 1.87 points against raw pooling and from 3.16 to 1.87 points against a learned (CQR-type) scale (marginal rule); 5 of 8 registered comparisons were met, and a gated variant intended never to be worse than the best classical pivot met its claim in only 1 of 6 cells. The theory's advantage therefore lies across machine configurations and as a zero-data predictor, not within a single configuration.

**Keywords:** coverage path planning; conformal prediction; chance constraints; GNSS guidance; pass-to-pass accuracy; extreme-value theory; agricultural machinery

### Highlights

- The exact run score is the smallest valid score for zero-miss certificates.
- Theory-pivoted cross-field conformal certifies fields with no own operation data.
- Coverage guarantee verified directly over field splits and redrawn historical runs.
- Mixed machine fleet: theory pivot cut excess overlap versus raw and learned scales.
- Within one machine type all pivots sit near an information limit; failures reported.

---

## 1. Introduction

### 1.1 Problem

Field operations such as spraying, fertilising, seeding and tillage are planned as sets of parallel passes (swaths) whose spacing equals the implement width minus an overlap. The plan is optimal only if the machine follows it exactly. Real execution deviates from the planned line because of GNSS positioning error, wheel slip on slopes and wet soil, antenna roll on side slopes, mounting offsets and the finite bandwidth of the steering controller. A missed strip arises whenever two adjacent passes drift apart by more than the overlap, and the relevant quantity is therefore the relative error between adjacent passes, which the industry calls pass-to-pass accuracy. Overlap between adjacent passes, much of it set deliberately to absorb deviation from the planned line, applies inputs twice on the overlapped strip. With global agricultural pesticide use of about 3.73 million tonnes of active ingredients in 2023 (FAO, 2025) and a global cropland nitrogen use efficiency of only about 40–46% (Zhang et al., 2015, 2021), both under-application (missed strips) and over-application (overlap) carry agronomic and environmental cost. The trend towards autonomous tractors (Global Market Insights, 2026) removes the operator who used to correct visible gaps by eye.

Current practice sets a fixed overlap, typically from a vendor's pass-to-pass specification or from operator experience. In our simulations with real GNSS error series, the vendor rule (twice the nominal pass-to-pass accuracy) did not meet a 0.9 zero-miss target on any field in any regime, and under RTK it left a gap on essentially every run (Sections 6.3, 6.5), while an overlap tuned by hand on a few fields reached the target on 70–73% of new flat or DGPS fields and on 27% of wet hilly fields. A fixed margin has no stated reliability; it is neither certified nor adaptive to field size, terrain or receiver grade.

### 1.2 Gap in the literature

Coverage path planning (CPP) research (Galceran and Carreras, 2013) has produced efficient decompositions, swath-angle optimisation and smooth headland turns (Höffmann et al., 2024; Mier et al., 2023, 2025); terrain-aware planners adjust spacing to 3D geometry (Hameed et al., 2016). These planners assume perfect execution or add a heuristic margin. The control literature reduces tracking error with slip observers (Lenain et al., 2006), offset-free model predictive control (Pannocchia and Rawlings, 2003) and tube MPC (Mayne et al., 2005), but a smaller error does not by itself yield a stated probability of complete coverage.

Conformal prediction gives finite-sample, distribution-free guarantees and has recently been used for planning: conformal planning around predicted obstacle trajectories with union bounds over time steps (Lindemann et al., 2023), conformal predictive programming for chance-constrained optimisation (Zhao et al., 2024), and related trajectory methods (Sun et al., 2023; Wang and Ning, 2025). Three features of these methods are problematic for field coverage. (i) They calibrate on the nominal plan and then deploy a different, more conservative plan; when the score is a maximum over pass pairs, adding passes makes the score stochastically larger, so the guarantee calibrated on the nominal plan does not transfer. (ii) Union bounds over many constraints are conservative. (iii) They require many calibration runs on the target itself; at $\varepsilon=0.1$ a marginal conformal quantile needs at least 9 runs and a PAC (training-conditional) quantile with $\delta=0.1$ at least 22, while a field is typically worked a few times per year. Weighted conformal prediction (Tibshirani et al., 2019), conformal risk control (Angelopoulos et al., 2024) and non-exchangeable conformal prediction (Barber et al., 2023) address covariate shift, monotone losses and drift, but not the specific structure of a maximum over pass pairs whose number depends on the decision. Performative prediction (Perdomo et al., 2020) studies decision-dependent distributions without coverage guarantees.

### 1.3 Contributions

1. **Formulation.** We state certified coverage planning as a chance constraint on the missed area of a random set, reduce the zero-miss event exactly to a scalar run score, $\{M=0\}\iff\{S\le\lambda\}$, and give the conformal-erosion certificate for boustrophedon plans (Section 3).
2. **Optimality of the exact score.** Among all valid scores, the exact score is pointwise minimal; consequently, under any order-statistic rule (marginal conformal, PAC, scenario), CE deploys no more passes than any method using another valid score on the same data, and union-bound calibration is never tighter (Section 5.1).
3. **Decision dependence.** Calibrating on a reference plan with at least as many passes as the deployed plan gives the correct dominance direction; a multiplicative bound $\varepsilon[1+(e^{hH}-1)/\theta]$ quantifies the coverage loss when the plans also differ in terrain features, and a closed-form factor $\kappa$ follows from the extreme-value theory (Sections 5.2, 5.3).
4. **A five-layer extreme-value theory of execution error,** from the closed-loop Lyapunov covariance through a discrete Kac–Rice bound, a product-form combination of pass pairs and a mixed-Poisson average over operating conditions to a Gumbel scale law. Each layer is validated against simulation using only the previous layer's output; the predicted margin is within −0.6% to +1.4% of simulation (Section 5.3, 6.4).
5. **Certification without target-field data (CE-EVT-R).** The theory's predicted quantile is used as a ratio pivot for cross-field conformal calibration with one historical run per calibration field. Validity follows from field exchangeability and does not depend on the accuracy of the theory; the theory affects only efficiency. We show why the ratio pivot is stable where the probability-integral-transform (PIT) pivot is not (Section 4.3, 5.4), and we verify the guarantee directly over both sources of randomness, random field splits and redrawn historical runs, in a pre-registered check (Section 6.8).
6. **Where a field-level pivot can and cannot help.** An information limit (Proposition 8) shows that with one run per field the PAC margin inflation is set by within-field run-to-run randomness, which no field-level prediction removes. Empirically, within one machine configuration all field-level pivots differ by tenths of a percentage point once realised coverage is matched; the theory's decisive advantages are across machine configurations (a mixed fleet) and as a predictor that needs no run data at all, where learned feature predictors trained on one run per field do not reach it (Sections 5.5, 6.5–6.7).
7. **Transparent evaluation.** System-level comparison against about 25 published planners, controllers and uncertainty layers on public field boundaries, terrain and GNSS data; a sequence of three pre-registered low-data experiments, reported in full: the first failed, the second met both registered claims (with a post hoc matched-coverage caveat), and the third met 5 of 8 comparisons for the mixed fleet and failed its 'never worse' claim; per-cell reporting of where the method does not help (Section 6).

---

## 2. Related work (condensed)

*Coverage path planning.* Boustrophedon cellular decomposition (BCD) with swath-angle optimisation is the standard for agricultural fields (Höffmann et al., 2024). Fields2Cover provides an open implementation with brute-force heading search and Dubins turns (Mier et al., 2023); Mier et al. (2025) add continuous-curvature headland paths. Hameed et al. (2016) compute 3D-terrain-equivalent spacing. None of these attaches a probability to complete coverage.

*Robust and model-based margins.* Tube MPC bounds the tracking error by a robust invariant set (Mayne et al., 2005); belief-space planning and Gaussian chance constraints propagate a parametric error model, optionally with Rice's extreme-value correction (Rice, 1944); Gaussian-process cautious control tightens constraints by a learned variance (Hewing et al., 2020); distributionally robust CVaR constraints use a Wasserstein ambiguity set (Mohajerin Esfahani and Kuhn, 2018); the scenario approach gives PAC guarantees from sampled constraints (Campi and Garatti, 2008). Parametric models misrepresent the heavy, temporally clustered tail of RTK errors (wrong fixes, float drift; Section 6.1), and worst-case sets are very conservative.

*Conformal prediction.* Split conformal prediction and its training-conditional (PAC) variant (Vovk, 2012); weighted conformal under covariate shift (Tibshirani et al., 2019); conformalized quantile regression with covariate-dependent scales (Romano, Patterson and Candès, 2019), the template of our CQR-type data-driven baseline; conformal risk control and Learn-then-Test (Angelopoulos et al., 2024, 2025); non-exchangeable conformal (Barber et al., 2023); hierarchical conformal with one sample per group (Dunn, Wasserman and Ramdas, 2023); functional conformal bands with modulation functions (Lei, Rinaldo and Wasserman, 2015; Diquigiovanni, Fontana and Vantini, 2022), of which a sup-normalised run score is an instance. Conformal planning: Lindemann et al. (2023), Zhao et al. (2024), Sun et al. (2023).

*Extreme values of Gaussian processes.* Kac–Rice formula and Rice's method (Azaïs and Wschebor, 2009; Piterbarg, 1996); normal comparison lemmas and maxima of stationary sequences and processes (Leadbetter, Lindgren and Rootzén, 1983; Li and Shao, 2002); rate of convergence of normal extremes (Hall, 1979); statistical linearisation (Booton, 1954; Kazakov, 1956).

---

## 3. Problem formulation

### 3.1 Fields, plans and erosion

A field is a polygon $P\subset\mathbb R^2$; the evaluated **main area** $W\subset P$ is $P$ inset by twice the implement width $w$ (the remainder is headland). After boustrophedon decomposition and choice of the working direction, a plan is a set of straight pass centrelines $y_1<\dots<y_K$ in field coordinates $(x,y)$, $x$ along the working direction. For an **erosion** (margin) $\lambda\ge0$, the greedy planner $\pi(\lambda)$ places passes at spacing $d=w-2\lambda$, i.e. it plans as if the footprint had half-width $w/2-\lambda$; the number of passes $K(\lambda)$ is non-decreasing in $\lambda$. Under a strictly monotone effective half-width, the greedy rule uses the fewest passes among all placements that satisfy the gap condition (research proposal, Proposition 5; a standard exchange argument for interval covering).

### 3.2 Execution model

Pass $k$ is executed with lateral offset $e_k(x)$ from its centreline, so its footprint at section $x$ is $[y_k+e_k(x)-w/2,\ y_k+e_k(x)+w/2]$. The error process $e=(e_k)_k$ is random, unknown, correlated along and across passes (passes are driven in sequence and read the same GNSS error trajectory at different times), and its law depends on the plan through the terrain and time at which each pass is driven. Coverage is evaluated on a 1 m grid of sections across $W$, by exact interval union in the lateral direction.

### 3.3 Zero-miss event and objective

Let $M(\lambda,e)$ be the missed area of $W$ when $\pi(\lambda)$ is executed with error $e$. The certified coverage problem is
$$
\min_{\lambda}\ J(\pi(\lambda))\quad\text{s.t.}\quad \Pr_{e\sim\mathcal D(\pi(\lambda))}\big[M(\lambda,e)=0\big]\ \ge\ 1-\varepsilon ,
$$
where $J$ is the overlap ratio of the main area (total swath area within $W$ divided by the area of $W$, minus one). A secondary cost, the applied overlap including swath that reaches into the headland, is also defined (`exp_lib.overlap_applied`). Three features make the constraint hard: it acts on the measure of a random set; $\mathcal D$ is unknown and temporally correlated; and $\mathcal D$ depends on the decision $\lambda$.

### 3.4 Exact run score

**Lemma 1 (exact covering radius).** At section $x$, let $C(x)$ be the sorted executed centres of the passes relevant to the chord $[\ell(x),u(x)]$ of $W$. The chord is fully covered iff its covering radius
$$
r^\star(x)=\max\Big\{d(\ell,C),\ d(u,C),\ \max_{i:\ (c_i+c_{i+1})/2\in[\ell,u]}\tfrac12(c_{i+1}-c_i)\Big\}\ \le\ \tfrac w2 .
$$
For the plan $\pi(\lambda_{\rm ref})$ actually executed, define the **exact run score**
$$
S \;=\; \lambda_{\rm ref}+\max_x\big(r^\star(x)-w/2\big).
$$
Then $\{M=0\}\iff\{S\le\lambda_{\rm ref}\}$ (up to floating-point ties).

The score is the growth of the footprint half-width that would close the worst gap. Its interior terms are the classic pass-to-pass gaps $\tfrac12(e_{k+1}-e_k)$ adjusted for spacing; boundary terms handle the first and last pass. A common-mode error shared by all passes (a slowly varying GNSS bias, a uniform slope drift) cancels in the interior terms; misses are caused by relative error between adjacent passes. Reading $S$ as the erosion needed by *another* plan $\pi(\lambda)$, $\{M(\lambda,e)=0\}\iff\{S\le\lambda\}$, is a transfer statement that holds exactly only for a shift-equivariant planner and execution (Section 5.2).

---

## 4. Method

All variants share one structure: compute exact run scores of calibration runs on a **reference plan** $\pi(\lambda_0)$, take a conformal order statistic, and deploy an eroded plan. They differ in where calibration data come from and how scores are normalised.

**Order statistics.** For $n$ calibration scores and miss level $\varepsilon$, the marginal rule takes the $k$-th smallest score with $k=\lceil(n+1)(1-\varepsilon)\rceil$; the PAC rule takes the smallest $k$ with $\mathrm{BinomCDF}(k-1;n,1-\varepsilon)\ge1-\delta$; if $k>n$ the quantile is $+\infty$ (no deployment).

### 4.1 CE: conformal erosion with a dominating reference plan

Under exchangeability of calibration and test runs, the marginal rule gives $1-\varepsilon\le\Pr[S_{n+1}\le\hat\lambda]\le1-\varepsilon+1/(n+1)$ (the upper bound without ties), and the PAC rule gives $\Pr[S_{n+1}\le\hat\lambda\mid\text{calibration}]\ge1-\varepsilon$ with probability at least $1-\delta$.

Two deployments are evaluated. **CE** (assumption-free) runs a pilot fixed point $\lambda_{\rm ref}\leftarrow1.10\,q$ until $q\le\lambda_{\rm ref}$, then a fresh certificate batch at the frozen $\pi(\lambda_{\rm ref})$; it deploys $\pi(\lambda_{\rm ref})$ itself when the fresh quantile $q^\star\le\lambda_{\rm ref}$, which by Lemma 1 needs no transfer assumption. **CE-q** deploys $\pi(q^\star)$, which uses the transfer of Section 5.2.

```
Algorithm 1  CE-q (conformal erosion, target-field calibration)
Input : field P, width w, miss level eps, [delta], reference erosion lam0, n runs
1  ys0 <- greedy_plan(P, w, lam0)                       # reference plan pi(lam0)
2  for i = 1..n: execute ys0, record offsets; S_i <- exact_score(ys0, offsets, lam0)
3  lam_hat <- order statistic k(n, eps[, delta]) of {S_i}
4  if lam_hat = +inf or lam_hat > lam0: refuse (or enlarge lam0 and recalibrate on fresh runs)
5  return greedy_plan(P, w, lam_hat)                    # K(lam_hat) <= K(lam0)
```

### 4.2 CE+: budget-matched, self-normalised calibration

CE+ (v7/v8) uses exactly $n$ calibration runs on the field, the same budget as all conformal, model-based and learning baselines, and makes three changes.

1. **Reference plan from training fields only.** $\lambda_0=1.25\times$ the largest $(1-\varepsilon)$ score quantile over five training fields (`REF_INFLATE = 1.25`). Proposition 2 (Section 5.2) bounds the price of this inflation.
2. **XTE-normalised score.** Before the infield passes the machine drives one headland probe line; the autosteer's measured cross-track error (XTE) RMS $z$ is a noisy reading of the day's roughness and slip. The score is $T=S/\sigma(z)$ with $\sigma(z)=\max(a+bz,\ 0.3\,\bar\sigma)$, $(a,b)$ fitted on training fields only, after dividing each training field's scores by that field's median so that $\sigma$ captures run-to-run, not field-size, variation. A new operation deploys $\lambda=t\,\sigma(z_{\rm new})$ with $t$ the conformal quantile of the calibration $T_i$. Since $(S_i,z_i)$ are exchangeable across runs, the guarantee holds for any fixed $\sigma(\cdot)$. Under GNSS-dominated error the fit gives $b\approx0$ and CE+ reduces to CE-q.
3. **Training-only gating (Proposition B).** The adaptive $\sigma(z)$ is used only if, in leave-one-field-out cross-validation on the training fields, it lowers the mean erosion needed for $1-\varepsilon$ coverage by at least 3% (`GATE = 0.03`); otherwise $\sigma$ is constant.

Deployed erosions are rounded up to a 2 mm grid. **CE+ PAC** uses the PAC order statistic.

```
Algorithm 2  CE+ (training fields T, target field g)
Offline (training fields only):
1  for f in T: S_f <- exact scores of 40 runs at pi_f(lam_train); z_f <- probe-line XTE RMS
2  lam0 <- 1.25 * max_f quantile_{1-eps}(S_f)
3  fit sigma(z) = max(a + b z, 0.3 * mean sigma) on {(z_f, S_f / median S_f)}
4  if LOO saving on T < GATE: sigma <- constant                 # Proposition B
Calibration on g (n runs at pi_g(lam0)):
5  T_i <- S_i / sigma(z_i);  t <- order statistic k(n, eps[, delta]) of {T_i}
Each new operation on g:
6  drive probe line, read z_new;  lam <- ceil_2mm(t * sigma(z_new));  execute pi_g(lam)
```

### 4.3 CE-EVT-R: certification with zero target-field runs

CE and CE+ need $n\ge9$ (marginal) or $n\ge22$ (PAC) runs on the target field. A farm or cooperative more typically holds **many fields with one or two historical operations each**, and the new field has none. CE-EVT-R calibrates across fields and uses the theory of Section 5.3 only to put fields on a common scale.

For each field $f$ and its reference plan $\pi_f(\lambda_0)$, the five-layer theory produces a predicted CDF $\hat F_f$ of the run score, computed from controller parameters, the DEM and the distribution of operating conditions, **without any run data**. Let $\hat q_f=\hat F_f^{-1}(1-\varepsilon)$ be the predicted $(1-\varepsilon)$ quantile.

- **Ratio pivot.** For calibration field $f_i$ with one historical score $S_i$, set $V_i=S_i/\hat q_{f_i}$.
- **+∞ rule (fixed in advance).** If $\hat F_f$ is not finite (numerical failure of the predictor), set $V_f=+\infty$; if this happens on the target field, no plan is deployed and the field counts as a failure.
- **Cross-field conformal.** $v^\star$ is the marginal or PAC order statistic of $\{V_i\}_{i\le n}$.
- **Deployment.** On the new field $g$, $\lambda_g=\hat q_g\,v^\star$.

```
Algorithm 3  CE-EVT-R (one run on each of n calibration fields, none on target g)
1  for each field f in {f_1..f_n, g}:  F_hat_f <- EVT_predict_cdf(f, lam0)   # no run data
2      q_f <- F_hat_f^{-1}(1 - eps)   if F_hat_f finite, else mark f bad
3  for i = 1..n:  V_i <- S_i / q_{f_i}   (V_i <- +inf if f_i bad)
4  v* <- order statistic k(n, eps[, delta]) of {V_i}
5  if g bad or v* = +inf: refuse
6  return greedy_plan(g, w, q_g * v*)
```

**Validity does not depend on the theory.** $\hat q_f$ is a fixed function of field $f$'s geometry, terrain and the controller, independent of all run data. If fields are drawn independently from a common population and each contributes one run, $(V_1,\dots,V_n,V_{\rm new})$ are exchangeable, so $\Pr[S_{\rm new}\le\hat q_g v^\star]\ge1-\varepsilon$ (marginal) or the PAC analogue (Proposition 5). The $+\infty$ rule is also a fixed function of field data and preserves exchangeability. Theory error enters only through efficiency: the closer $V$ is to identically distributed across fields, the closer $\lambda_g$ is to field $g$'s own $(1-\varepsilon)$ quantile. Deploying $\pi_g(\lambda_g)$ rather than $\pi_g(\lambda_0)$ uses the transfer of Section 5.2–5.3 and requires $\lambda_g\le\lambda_0$.

**Why a ratio pivot.** A first version (E-low v1) used the PIT pivot $V_i=\hat F_{f_i}(S_i)$ with deployment $\lambda_g=\hat F_g^{-1}(v^\star)$. Its sensitivity to theory error is analysed in Section 5.4; in short, the PIT inverse amplifies errors by $1/\hat f_g(\lambda)$, which diverges in the tail where $v^\star$ lies, whereas the ratio pivot is linear in $\hat q_g$ and uses the theory exactly at the quantile where it is most accurate.

**Computational cost.** The predictor is run once per field and reference plan, before any operation, and needs no run data. On a single core with 200 sampled operating conditions (`n_cond = 200`), the predictor alone took 133–187 s per field in R1, 287–353 s in R2 and 16–51 s in R3 (three E-low v3 test fields per regime). The cost is largest for the long R2 fields (5225–5703 m of passes) and smallest for the short R3 fields (324–1016 m); it is incurred once, offline, when a field is added to the farm's records. <!-- source: results/lowdata_v3/theory_runtime.txt -->

---

## 5. Theory

Full statements and proofs are given in the internal notes `docs/theory_v8.md` (Section 5.1), `docs/theory_transfer.md` (Section 5.2) and `docs/theory_evt.md` (Section 5.3); Appendix A reproduces the proofs available there. Numbering below is that of this paper.

### 5.1 The exact score is the smallest valid score

**Definition 1 (needed erosion).** $\bar\lambda(e)=\inf\{\lambda:\ M(\lambda,e)=0\}$.

**Definition 2 (valid score).** A run-level score $S'$ is *valid* if $S'(e)\le\lambda\Rightarrow M(\lambda,e)=0$ for all $\lambda,e$, i.e. it never declares a miss-free run that misses. The pass-pair score of CPP-style methods and the maximum of Lindemann-type per-constraint scores are valid under the small-error condition A1 (adjacent passes do not swap order, $|e_k|<w/2$).

**Lemma 2 (lower bound).** Every valid score satisfies $S'(e)\ge\bar\lambda(e)$ for every run.

**Theorem 1 (exact score attains the bound).** Under shift-equivariant transfer, the exact score of Lemma 1 computed at the reference plan satisfies $S^\star(e)=\bar\lambda(e)$; hence $\{M=0\}\iff\{S^\star\le\lambda\}$ and $S^\star\le S'$ run by run for every valid $S'$.

*Numerical check* (6 fields × 200 runs, three regimes): $\{M>0\}=\{S^\star>\lambda\}$ on 100% of runs; $S^\star\le S_{\rm pair}$ on 100% of runs; the pair score never declared a missing run miss-free; the gap between the two at the 90% quantile was 0.4–1.3 cm under RTK and 5.5–9.2 cm under DGPS (`docs/theory_v8.md` §1).

**Corollary 1 (dominance under any order-statistic rule).** If a certification rule takes the $k$-th order statistic of the calibration scores — marginal conformal, PAC/training-conditional conformal, or the scenario approach — then $S^\star_{(k)}\le S'_{(k)}$ for **every** calibration sample, not only in expectation. Because $K(\lambda)$ is non-decreasing, CE deploys no more passes than the same rule applied to any valid score on the same data.

**Lemma 3 (union bounds are looser).** If $S'=\max_jS'_j$ and per-constraint quantiles $q_j$ are taken at level $\varepsilon/J$, then on the empirical distribution $\#\{i:\max_jS'_{ij}>\max_jq_j\}\le\sum_j\#\{i:S'_{ij}>q_j\}\le n\varepsilon$, so $\max_jq_j$ is at least the joint empirical $(1-\varepsilon)$ quantile.

**Consequence for fair comparison.** For a one-dimensional decision $\lambda$, the scenario approach at confidence $\delta$ applied to $S^\star$ is the PAC version of CE, and marginal conformal applied to $S^\star$ is CE-q. The contribution of CE is therefore not the quantile rule but (a) the score and (b) the reference plan. Comparisons must be made **within a guarantee class** (marginal vs marginal, PAC vs PAC); for this reason PAC versions of CPP and Lindemann were added for the v8 confirmatory study.

### 5.2 Decision dependence and transfer

**Proposition 1 (nominal-plan calibration does not transfer).** CPP and Lindemann et al. calibrate on the nominal plan $\pi(0)$ and deploy $\pi(\hat\lambda)$ with $K(\hat\lambda)\ge K(0)$. Because the run score is a maximum over pass pairs, more pairs make it stochastically larger, so coverage computed on $\pi(0)$ does not transfer to $\pi(\hat\lambda)$; these methods have no distribution-free guarantee on the deployed plan even when they reach the target empirically. CE calibrates on $\pi(\lambda_0)$ with $\lambda_0\ge\hat\lambda$, which gives the correct direction.

The remaining question is how much coverage changes when the paired pass pairs of $\pi_0=\pi(\lambda_0)$ and $\pi_1=\pi(\hat\lambda)$ cross different terrain at different times.

*Setting.* Pair $j=(k,k+1)$ has score $T_j=\sup_x\tfrac12(e_{k+1}(x)-e_k(x))$ over the main area, with boundary pseudo-pairs $e_1$ and $-e_K$; $U_\pi=\max_{j\in J(\pi)}T_j$ and $\pi(\lambda)$ is miss-free iff $U_{\pi(\lambda)}\le\lambda$. **Assumption G (generative structure):** $e_k=\Psi(C,\phi_k,\tau_k,\xi_k)$ with operating condition $C$ (soil moisture, slip and roughness gains, roll-compensation factor, mounting bias, GNSS error trajectory), per-pass terrain features $\phi_k$ and start time $\tau_k$, and independent per-pass noise $\xi_k$; $\Psi$ does not depend on the plan. Couple both plans by sharing $C$ and $\xi_k$. **Assumption L:** under this coupling $|T_j^{(0)}-T_j^{(1)}|\le h_j$, with $h_j$ proportional to the difference of paired features computable from the plan and DEM.

**Theorem 2 (multiplicative transfer; `theory_transfer.md` Theorem 5).** Under G and L, with $J(\pi_1)\subseteq J(\pi_0)$, $h=\max_jh_j$, $H$ an upper bound on the hazard rate of the pair scores on $[t-h,t]$, and $\theta_t=1/\mathbb E[N_t\mid N_t\ge1]$ the finite-threshold extremal index ($N_t$ the number of exceeding pairs),
$$
1-F_{\pi_1}(t)\ \le\ \big(1-F_{\pi_0}(t)\big)\Big[1+\frac{e^{hH}-1}{\theta_t}\Big].
$$
Consequently, if $\hat\lambda$ is the conformal quantile on $\pi_0$ and $\lambda_0\ge\hat\lambda$, the deployed miss probability is at most $\varepsilon[1+(e^{hH}-1)/\theta]$ (marginal), and the same holds conditionally on calibration with probability $\ge1-\delta$ (PAC).

The transfer error is **relative**, not additive: it scales with $\varepsilon$. On flat homogeneous fields $h=0$ and the factor is 1, which recovers the earlier translation-equivariance assumption as a special case with an explicit condition.

**Proposition 2 (price of an inflated reference plan).** With $h=0$ and identically distributed pairs, the over-coverage caused by the $a=|J(\pi_0)\setminus J(\pi_1)|$ extra reference pairs is at most $\varepsilon\,a/(K\theta)$, with $a\approx K\cdot2(\lambda_0-\hat\lambda)/(w-2\hat\lambda)$. For R1 ($\varepsilon=0.1$, $\lambda_0-\hat\lambda\approx5$ cm, $w=3$ m, $\theta\approx0.5$) this is $\lesssim0.7\%$, which justifies `REF_INFLATE = 1.25` as a trade-off between the premise $J(\pi_1)\subseteq J(\pi_0)$ and efficiency.

**Proposition 3 (training-only gating; Proposition B).** The CE+ normalisation $\hat\sigma$ is selected using training fields only, hence it is independent of calibration and test runs. Conditionally on $\hat\sigma$, $(S_i/\hat\sigma(z_i))$ remain exchangeable, so the marginal and PAC guarantees hold for whichever normalisation is selected. Corollary 1's pointwise dominance holds only for constant normalisation; the advantage of the adaptive variant is empirical and is enabled only when it helped on training fields.

### 5.3 A five-layer extreme-value theory of execution error

The five layers turn the closed-loop vehicle model into a prediction of the run-score distribution. Each layer consumes only the previous layer's output:

$$
\underbrace{(A_t,B_t,P_t)}_{\text{L1: covariance}}\ \to\ \underbrace{\mu_j(t\mid C)}_{\text{L2: pair exceedance}}\ \to\ \underbrace{P(U\le t\mid C)}_{\text{L3: product}}\ \to\ \underbrace{F_\pi(t)=\mathbb E_C[\cdot]}_{\text{L4: mixed Poisson}}\ \to\ \underbrace{t_\varepsilon\approx m+s\,a_N}_{\text{L5: Gumbel / pivot}} .
$$

**L1 — closed-loop covariance.** *Assumption A1 (linear regime):* no steering saturation or rate limit, small angles, terrain gradient locally constant. Then one pass obeys $\xi_{t+1}=A\xi_t+Bw_t+b_t(C)$ with state (lateral offset, heading, steering angle, integrator, Ornstein–Uhlenbeck slip), Gaussian innovations $w_t$ independent across passes and a deterministic input $b_t(C)$ (projected GNSS error, roll-induced antenna offset, mean slip, mounting bias).

**Proposition 4 (conditional Gaussianity and Lyapunov covariance).** Given $C$, pass offsets are independent Gaussian processes; the mean is the closed-loop response to $b_t(C)$; the stationary covariance solves $P=APA^\top+B\Sigma_wB^\top$ ($\rho(A)<1$); and the spectral moments along arc length are $\lambda_0=P_{dd}$, $\lambda_2=P_{\psi\psi}+2P_{\psi\beta}+P_{\beta\beta}$. The gap process $Z_j=\tfrac12(e_{k+1}-e_k)$ is then Gaussian with variance $\tfrac12\lambda_0$ and slope variance $\tfrac12\lambda_2$, **independent of the plan**; the plan affects only the mean $m_j$.

Three refinements were forced by failed validation checks. (a) *Observation operator:* misses are evaluated on offsets linearly interpolated to a 1 m grid with a pass-constant weight $f_k$, so $\mathrm{Var}\,\tilde e_k=(1-f)^2v_s+f^2v_{s+1}+2f(1-f)c_s$ (exact form; an earlier stationary approximation produced a negative variance on one field). Ignoring the operator overestimates variance by 2–3% and tail probability by 15–30%. (b) *Time-varying quasi-linearisation* along the noise-free closed-loop trajectory, with Jacobians of kinematics and terrain feedback and random-input describing functions for steering saturation and rate limits; covariance propagates by $P_{t+1}=A_tP_tA_t^\top+B_tB_t^\top$. (c) *Integrator clamp:* the anti-windup clamp $|I|\le0.3$ sits about 1.6 standard deviations from zero; it is replaced by a leaky integrator whose leak rate is fixed by matching the stationary variance to that of the truncated Gaussian (Kazakov-type energy criterion). This gives a best estimate; the unclamped linear model is a safe upper bound because clamping only reduces variance.

**L2 — single-pair exceedance (Kac–Rice).** **Theorem 3.** Given $C$, with $\sigma(x),\sigma'(x),r(x)$ the variance, slope variance and cross-covariance of $Z_j$ and $\Psi(a)=\varphi(a)+a\Phi(a)$,
$$
\mu_j(t\mid C)\le\bar\Phi\Big(\tfrac{t-m_j(0)}{\sigma(0)}\Big)+\int_0^{L_j}\frac{\tilde\sigma'(x)}{\sigma(x)}\varphi\Big(\tfrac{t-m_j(x)}{\sigma(x)}\Big)\Psi\Big(\tfrac{\tilde m'(x;t)}{\tilde\sigma'(x)}\Big)dx ,
$$
which reduces in the stationary case to $\bar\Phi(u)+\tfrac{L_j}{2\pi}\tfrac{s'}{s}e^{-u^2/2}$. Because misses are evaluated on the 1 m grid, the **discrete** version $\mu_j\le P(Z_{j,0}>t)+\sum_iP(Z_{j,i}\le t<Z_{j,i+1})$ (bivariate normal integrals with L1's lag-1 correlation) is used; it is a strict upper bound and tight in the tail. Where Rice is loose (any pair with bound $\ge0.01$, i.e. far from the tail), the exact Gaussian exceedance is computed by Monte Carlo from the full L1 covariance $\mathrm{Cov}(d_a,d_b)=(\Phi_{b-1}\cdots\Phi_aP_a)_{dd}$ ("hybrid exact L2").

**L3 — combining pairs.** Non-adjacent pairs are independent given $C$; adjacent pairs share one pass. Writing $Z_j=(e_{k+1}-e_k)/2$ and $Z_{j+1}=(e_{k+2}-e_{k+1})/2$ with single-pass variance $\sigma^2$ and autocorrelation $r$, the cross-correlation is $\rho_{xx'}=-\tfrac12 r(x,x')$: it equals $-\tfrac12$ at the same section and changes sign at longer lags because the under-damped closed loop has $r\approx-0.24$ at 10 m (so neither Slepian's inequality nor a small-correlation argument applies). We therefore use a bound that needs no condition on the sign or size of the covariance, only the independence of non-adjacent pairs. Let $A_j=\{T_j>t\}$, $\mu_j=P(A_j\mid C)$, $M=\sum_j\mu_j$ and $p_j=P(A_j\cap A_{j+1}\mid C)$.

**Theorem 4 (conditional product form, Bonferroni sandwich).** $1-M\le P(U_\pi\le t\mid C)\le 1-M+\sum_{|i-j|\ge2}\mu_i\mu_j+\sum_j p_j$, and $1-M\le\prod_j(1-\mu_j)\le1-M+\sum_{i<j}\mu_i\mu_j$; hence $\big|P(U_\pi\le t\mid C)-\prod_j(1-\mu_j(t\mid C))\big|\le \tfrac{M^2}{2}+\sum_j\min(\mu_j,\mu_{j+1})=:\eta(t\mid C)$. At the certified level ($P\approx0.9$, $M\approx0.105$) the first term is about 0.0055; the joint exceedance $p_j$ of adjacent pairs is suppressed by the negative same-section correlation and can be computed exactly with the L2 Gaussian Monte Carlo to tighten the bound. Validity of CE-EVT-R does not rely on this layer (Section 5.4); L3 accuracy affects only efficiency.

The product is used rather than $e^{-\sum_j\mu_j}$ because one pair can dominate under DGPS (a large GNSS jump gives $\mu_{\max}\approx0.5$); at a fixed DGPS condition and the 0.3 quantile the product gives 0.2988 against a true 0.3000, while $e^{-M}$ gives 0.4851 (`theory_evt.md` §3); the empirical error of the product form in that table is at most 0.0012, well inside $\eta$.

**L4 — mixed Poisson over operating conditions.** **Theorem 5.** $F_\pi(t)=\mathbb E_C\big[\prod_{j\in J(\pi)}(1-\mu_j(t\mid C))\big]+\rho_\pi(t)$, $|\rho_\pi|\le\mathbb E_C[\eta(t\mid C)]$. Consequences:

- *Source of clustering.* $\theta_t=\mathbb E_C[1-e^{-M}]/\mathbb E_C[M]+O(\cdot)<1$ by Jensen's inequality: exceedances cluster because operating conditions differ between runs, not because of local pair dependence.
- *Closed-form transfer.* If paired pairs have equal covariance given $C$ (Proposition 4) and mean shifts $m_j^{(1)}-m_j^{(0)}\le\Delta_j(C)$, then
$$
1-F_{\pi_1}(t)\le\kappa\big(1-F_{\pi_0}(t)\big)+(\kappa+1)\,5\,\mathbb E\mu_{\max},\qquad \kappa=\sup_C\exp\Big(\frac{\bar u\Delta(C)}{s}+\frac{\Delta(C)^2}{2s^2}\Big),
$$
with $\bar u$ the largest standardised threshold. Every term is computable: $s$ from L1, $\bar u\approx\sqrt{2\log N}$ from L5, and $\Delta$ from the DEM (dominated by the roll-induced antenna offset, $\Delta_j\le\tfrac12h_{\rm ant}(1-c_{\min})\sup_x|\Delta g^{(1)}_{y,j}-\Delta g^{(0)}_{y,j}|$) plus a GNSS timing term bounded by the modulus of continuity of the error series. Hence $P(\text{miss after deployment})\le\kappa\varepsilon+O(\varepsilon/K)$; on flat homogeneous fields $\Delta=0$, $\kappa=1$. This replaces the estimated hazard and extremal index of Theorem 2 by computable quantities.

**L5 — Gumbel scale law and cross-field pivot.** **Theorem 6.** For fixed $C$, stationary pairs with constant mean $m$ and effective length $N=\tfrac{s'}{2\pi s}\sum_jL_j$, as $N\to\infty$, $P\big(a_N(\tfrac{U-m}{s}-a_N)\le z\mid C\big)\to\exp(-e^{-z})$ with $a_N=\sqrt{2\log N}$ (Leadbetter, Lindgren and Rootzén, 1983). Hence the needed margin grows only like
$$
t_\varepsilon(C)=m+s\Big[a_N-\frac{\log(-\log(1-\varepsilon))}{a_N}\Big]+o(s/a_N).
$$
Two consequences: (i) a tenfold larger field raises the margin by about 15% at $N\sim10^3$; (ii) the margin is driven by the per-run noise scale $s(C)$, which is why normalising by the probe-line XTE (a noisy reading of $s(C)$) in CE+ is effective. Finally, a normalised score built from plan geometry and training data only is exchangeable across fields when each field contributes one run (validity, regardless of pivotality); and because normal extremes converge at rate $O(1/\log N)$ (Hall, 1979), per-field conditional coverage deviates from $1-\varepsilon$ by $O(1/\log N_{\min})$ plus the scale-estimation error (accuracy, from pivotality). This is the two-level model of Dunn, Wasserman and Ramdas (2022) with one sample per group.

### 5.4 Validity of CE-EVT-R and stability of the ratio pivot

**Proposition 5 (CE-EVT-R validity).** Suppose fields $f_1,\dots,f_n,g$ are i.i.d. from a population, each calibration field contributes one run at its reference plan, and $\hat q_f$ (with the $+\infty$ rule) is a measurable function of field $f$ only. Then $V_i=S_i/\hat q_{f_i}$ and $V_{\rm new}$ are exchangeable and $\Pr[S_{\rm new}\le\hat q_g v^\star]\ge1-\varepsilon$ for the marginal rule; for the PAC rule, with probability $\ge1-\delta$ over calibration, the conditional probability is $\ge1-\varepsilon$. The miss guarantee for $\pi_g(\hat q_gv^\star)$ follows by Theorem 5 when $\hat q_gv^\star\le\lambda_0$. *Proof:* $S_{\rm new}\le\hat q_gv^\star\iff V_{\rm new}\le v^\star$; apply the split-conformal quantile lemma to exchangeable $V$. $\square$

The proposition says nothing about efficiency. Efficiency depends on how well $\hat q_f$ tracks the true per-field quantile $\lambda^\star_f$.

**Proposition 6 (pivot sensitivity; heuristic, motivated post hoc).** Let the theory be exact up to a scale error, $\hat F_f(t)=F_f(t/(1+\delta_f))$.
- *Ratio pivot:* $\hat q_f=(1+\delta_f)q_f$, so $V_f=S_f/((1+\delta_f)q_f)$ and $\lambda_g=(1+\delta_g)q_gv^\star$. The deployed margin is affected linearly, $\partial\lambda_g/\partial\delta_g=q_gv^\star$, and the theory is evaluated only at the $(1-\varepsilon)$ quantile, which L1–L4 predict most accurately (Section 6.4).
- *PIT pivot:* $\lambda_g=\hat F_g^{-1}(v^\star)$ with $v^\star$ close to 1 (it is the $(1-\varepsilon)$ or PAC order statistic of PIT values), and $\partial\lambda_g/\partial v^\star=1/\hat f_g(\lambda_g)$. In the tail $\hat f_g\to0$, so small errors in $v^\star$ (from tail errors of $\hat F_{f_i}$ on calibration fields) become large errors in $\lambda_g$. With the PAC rule at $n\approx30$, $v^\star$ is near the largest PIT value, which is where this amplification is strongest. A non-finite $\hat F$ is in addition sorted to the top and drives $v^\star$ to the extreme tail (observed in E-low v1, R3).

Section 6.5 compares both pivots under the corrected theory: in R3 PAC the PIT pivot's excess overlap is 28.38 pp against 15.25 pp for the ratio pivot.

**Proposition 7 (validity criteria; `theory_v8.md` Proposition 4).** For per-field evaluation with $n_t=200$ test runs and a one-sided binomial test at 0.05, a field "fails" iff at most 172 runs are miss-free; a field with true coverage exactly 0.9 fails with probability $\alpha=0.043$. With $n=100$ calibration runs per field and $\varepsilon=0.1$, the per-field true coverage of an exactly calibrated marginal method is Beta(91, 10) (mean 0.901) with theoretical failure rate 14.5%; a PAC method ($\delta=0.1$) is Beta(95, 6) (mean 0.941) with failure rate 1.2% (general upper bound $\delta+\alpha=14.3\%$). Hence a marginal method meeting the target on about 85% of fields is behaving as designed, and a PAC method is invalid if $\ge9$ of 30 fields fail.

---


### 5.5 An information limit for cross-field PAC certification with one run per field

Every method compared in the zero-data setting is a *scale pivot*: a field-measurable scale $q_f>0$ (the theory quantile, the scale law, a feature model, or $q\equiv1$), pivots $V_i=S_i/q_{f_i}$, threshold $t=V_{(k)}$ and deployment $\lambda_g=q_g t$.

**Proposition 8 (margin inflation under the ideal scale).** Let $G_f$ be the distribution of the run score on field $f$, $\lambda^\star_f=G_f^{-1}(1-\varepsilon)$, and take the ideal (unavailable) scale $q_f=\lambda^\star_f$. With $H(v)=\mathbb E_f[G_f(v\lambda^\star_f)]$ one has $H(1)=1-\varepsilon$ and, for every target field,
$$\frac{\lambda_g}{\lambda^\star_g}=t=H^{-1}(B),\qquad B\sim\mathrm{Beta}(k,\,n+1-k).$$
For the PAC rule with $n=29$, $\varepsilon=\delta=0.1$, $k=n$ and $\mathbb E[B]=29/30$. If the normalised shapes coincide, $G_f(v\lambda^\star_f)=\Gamma(v)$, the inflation is the within-field tail ratio $\Gamma^{-1}(B)$, roughly $\Gamma^{-1}(0.967)/\Gamma^{-1}(0.9)$: a property of run-to-run randomness that no field-level prediction can remove. Because excess overlap is a nonlinear (pass-count) function of $\lambda$, a common margin ($q\equiv1$) can even be cheaper than the ideal scale when between-field spread is small and tails are heavy.

*Proof.* Under the ideal scale the $V_i$ are i.i.d. with distribution $H$; the probability integral transform of the $k$-th order statistic is $\mathrm{Beta}(k,n+1-k)$, and $\lambda_g/\lambda^\star_g=V_{(k)}$ does not depend on $g$. $\square$

**Prediction from the theory (post hoc).** Replacing $G_f$ by the theory CDFs $\hat F_f$ (L1–L4; the tail ratio is governed by the Gumbel scale-to-location ratio of L5) and simulating the PAC rule gives predicted ideal inflations $1.30\pm0.35$ (R1), $1.26\pm0.33$ (R2) and $1.85\pm0.74$ (R3), against $1.018$, $1.207$ and $1.645$ observed on the E-low v2 fields (`scripts/predict_limit.py`, `docs/theory_limit.md`). All three observations lie within one predicted standard deviation and the ordering (R3 far above R1 and R2) is predicted correctly; the large spread is itself predicted, since the PAC threshold at $n=29$ is a sample maximum. The two quantities that decide in advance whether CE-EVT-R can help are therefore computable from the theory: the between-field spread of $\lambda^\star_f$ relative to the theory error (room for the marginal rule) and the within-field tail ratio (floor for the PAC rule).

## 6. Experiments

### 6.1 Data and simulator

All data are public (`docs/experiments_report.md` §1).

- **Field boundaries and working directions:** 250 combine-harvester GNSS trajectories from the field–road trajectory dataset derived from the national agricultural machinery operation platform (Wu et al., 2023); DBSCAN extracts 964 fields, of which 137 paddy fields (hilly south of China) and 162 wheat fields (North China Plain) are used.
- **Terrain:** Copernicus GLO-30 DEM windows per field, providing cross- and along-slope.
- **GNSS error:** 12 NOAA CORS station pairs (baselines 5–30 km, mainly in US Midwest and Great Plains agricultural regions), 8 days each across four seasons of 2024–2025, processed with RTKLIB (Takasu and Yasuda, 2009) in its demo5 fork (Everett, n.d.) at four receiver grades. The first 30 min of each day is removed; truth is IGS20/ITRF2020 coordinates propagated to the epoch; 30 s epochs are interpolated to 1 Hz and high-frequency residuals from the i2Nav vehicle dataset (Tang et al., 2022) are added. Each simulated run draws a station-pair-day and start time.
- **Real robot logs:** CitrusFarm (UC Riverside; Teng et al., 2023) RTK trajectories, 123 rows, for offline replay (results not reported in this draft; see Section 6.10).

<!-- source: docs/experiments_report.md -->
| Grade | RMS | 95% | 99.9% | Max |
|---|---|---|---|---|
| RTK fixed | 2.7 cm | 4.2 cm | 24 cm | 1.39 m |
| RTK float | 2.9 cm | 4.7 cm | 24 cm | 1.39 m |
| DGPS | 30 cm | 53 cm | 1.8 m | 6.0 m |
| Single point | 1.5 m | 2.8 m | 5.0 m | 7.2 m |

*Table 1. Horizontal GNSS error of the CORS series.* The RTK-fixed tail comes from real wrong fixes (fix flag set but error 0.3–0.6 m) and float drift lasting minutes; a Gaussian with the same RMS underestimates the tail by orders of magnitude. Static geodetic antennas lack vehicle multipath and vibration, so the RTK errors are a lower bound on machine errors.

**Closed-loop simulator** (vectorised over runs, $\Delta t=0.05$ s, speed 2 m/s): kinematics $\dot d=v\sin(\psi+\beta)$, $\dot\psi=v\tan\delta/l$; first-order steering lag $\tau=0.25$ s with 35° saturation and 30°/s rate limit; terrain slip $\beta=-0.35\,k_s\,g_{\rm lat}$ plus OU roughness, with $k_s$ and roughness set by per-run soil moisture; antenna height 2.6 m with roll-compensation factor $c=0.85\pm0.05$; per-run mounting bias with $\sigma=1.5$ cm; GNSS error projected on the lateral axis, with passes executed in real time order including headland turns so that adjacent passes read the same error series one pass-duration apart. Controllers: pure pursuit, Stanley, LQR and LQR with integral action (LQR-I, default, designed on the delay-augmented model, with conditional-integration anti-windup); external controllers plug into the same interface.

### 6.2 Regimes, protocol and baselines

<!-- source: docs/experiments_report.md -->
| Regime | Fields | GNSS grade | Width $w$ | Soil | Vendor pass-to-pass |
|---|---|---|---|---|---|
| R1 RTK flat 3 m | wheat (plain) | RTK fixed | 3 m | normal | 2.5 cm |
| R2 RTK hilly-wet 1.5 m | paddy (hilly) | RTK fixed | 1.5 m | wet (moisture 0.6–0.9) | 2.5 cm |
| R3 DGPS hilly 6 m | paddy (hilly) | DGPS | 6 m | normal | 20 cm |

*Table 2. Operating regimes.*

**Field splits.** Fields are ordered by `core.load_fields(seed=0)`. Indices 0–4: training fields (CE+ fitting, farmer tuning, reference erosion). 5–19: earlier system experiments (v3–v6, which answer a different question with target-field data) and the E-low v3 test fields; no E-low design or analysis used them before E-low v3. 20–49: v7 system comparison. 50–79: v8 confirmatory system comparison, E-low v2 test fields and the E-low v3 calibration pool. 80 onward: E-low v1, all exploratory analyses that led to E-low v2, and the E-low v3 training pool (gate and CQR fitting only).

**System comparison protocol.** A system is a coverage planner × tracking controller × margin/certification layer. All systems run on the same simulator, fields and evaluator with common random numbers. Each system is calibrated on 100 runs per field and tested on 200 fresh runs; $\varepsilon=0.1$, $\delta=0.1$. Metrics: pooled P(no miss); **meet rate**, the fraction of fields whose per-field P(no miss) is not significantly below 0.9 (Proposition 7); main-area overlap; **regret**, overlap minus the per-field oracle overlap in percentage points (pp), where the oracle iterates $\lambda\leftarrow$ the 0.9 quantile of exact scores of test-distribution runs at $\pi(\lambda)$ itself, and is not attainable by any method; infeasible fields.

**Baselines** (about 25 published or industry systems, each implemented as a plug-in module reviewed against the original paper or source code): vendor-specification overlap (twice the nominal pass-to-pass accuracy) and farmer-tuned global overlap (tuned once on the training fields to P(no miss) ≥ 0.9), with and without vendor terrain compensation; Fields2Cover (Mier et al., 2023), Hameed 3D terrain spacing (Hameed et al., 2016) and follow-previous-pass guidance as planners; Lenain-type slip-observer control, ESO sliding-mode control and offset-free MPC (Pannocchia and Rawlings, 2003) as controllers; tube-MPC radius margin (Mayne et al., 2005); Gaussian chance constraints (pointwise, Rice extreme-value correction, model-based Monte Carlo); GP cautious margins (Hewing et al., 2020); conformal planning with union bounds (Lindemann et al., 2023); conformal predictive programming (CPP; Zhao et al., 2024); the scenario approach (PAC, $\beta=0.01$); Wasserstein DRO-CVaR. The CE layers are applied on six stacks: BCD + LQR-I, Fields2Cover, Hameed 3D, follow-previous-pass, Lenain controller and offset-free MPC.

### 6.3 Main comparison with target-field data

**Status.** The v7 results below were obtained on fields 20–49 and were used to diagnose and refine the method (v8 changes: training-only gating, PAC versions of CPP and Lindemann). They are therefore **exploratory**. The pre-registered confirmatory comparison (claims V and E of `docs/theory_v8.md` §6) runs on fresh fields 50–79.

> **v8 confirmatory results: TODO, to be filled from `results/system_v8*.csv`.** Pre-registered primary methods: CE+ v8 (marginal) and CE+ v8 PAC. Claim V: pooled P(no miss) of CE+ v8 not significantly below 0.9 and fewer than 9/30 failing fields for CE+ v8 PAC, in every regime. Claim E: one-sided paired Wilcoxon on main-area overlap, Holm-corrected at 0.05, CE+ v8 PAC < CPP-PAC and Lindemann pair-PAC; CE+ v8 < CPP and Lindemann pair-level. Secondary: `overlap_applied`, scenario/DRO/union-bound comparisons, descriptive validity of methods without guarantee, sensitivity to GATE, REF_INFLATE, SIG_FLOOR.

<!-- source: results/v7/summary.txt -->
| R1 RTK flat 3 m — BCD + LQR-I stack | P | meet | overlap % | regret pp |
|---|---|---|---|---|
| GP cautious margin, Bonferroni (Hewing et al.) | 0.873 | 0.633 | 8.642 | −0.235 |
| Farmer-tuned global overlap | 0.886 | 0.733 | 8.723 | −0.154 |
| Model-based MC chance constraint | 0.884 | 0.700 | 8.755 | −0.122 |
| Gaussian belief, Rice extreme-value | 0.886 | 0.667 | 8.863 | −0.015 |
| **CE+ (v7)** | 0.915 | 0.967 | 8.864 | −0.014 |
| **CE-q** | 0.906 | 0.933 | 9.073 | 0.196 |
| Gaussian chance constraint | 0.912 | 0.900 | 9.241 | 0.363 |
| **CE+ PAC (v7)** | 0.950 | 1.000 | 9.506 | 0.628 |
| CPP (Zhao et al.) | 0.937 | 0.967 | 9.828 | 0.950 |
| **CE** | 0.946 | 1.000 | 9.920 | 1.043 |
| Lindemann et al., pair-level union bound | 0.956 | 1.000 | 10.419 | 1.542 |
| Scenario approach (PAC, β = 0.01) | 0.964 | 1.000 | 10.769 | 1.892 |
| Wasserstein DRO-CVaR | 0.994 | 1.000 | 15.851 | 6.973 |
| Lindemann et al., union bound | 0.988 | 1.000 | 19.159 | 10.282 |
| Tube-MPC radius margin (W99) | 1.000 | 1.000 | 44.042 | 35.164 |

<!-- source: results/v7/summary.txt -->
| R2 RTK hilly-wet 1.5 m — BCD + LQR-I stack | P | meet | overlap % | regret pp |
|---|---|---|---|---|
| **CE+ (v7)** | 0.916 | 0.900 | 25.555 | 0.003 |
| **CE-q** | 0.907 | 0.867 | 25.918 | 0.365 |
| Gaussian chance constraint | 0.903 | 0.800 | 26.108 | 0.555 |
| CPP (Zhao et al.) | 0.915 | 0.933 | 26.515 | 0.962 |
| **CE+ PAC (v7)** | 0.947 | 1.000 | 27.491 | 1.938 |
| **CE** | 0.938 | 1.000 | 28.142 | 2.589 |
| Lindemann et al., pair-level union bound | 0.950 | 1.000 | 29.691 | 4.138 |
| Scenario approach (PAC, β = 0.01) | 0.957 | 1.000 | 30.160 | 4.607 |
| Lindemann et al., union bound (1 infeasible field) | 0.975 | 0.967 | 47.636 | 22.097 |
| Wasserstein DRO-CVaR | 0.993 | 1.000 | 48.472 | 22.920 |

<!-- source: results/v7/summary.txt -->
| R3 DGPS hilly 6 m — BCD + LQR-I stack | P | meet | overlap % | regret pp |
|---|---|---|---|---|
| Farmer-tuned global overlap | 0.868 | 0.700 | 13.821 | −1.219 |
| **CE-q** | 0.905 | 0.867 | 15.449 | 0.409 |
| **CE+ (v7)** | 0.910 | 0.833 | 15.997 | 0.957 |
| GP cautious margin, Bonferroni (Hewing et al.) | 0.935 | 0.967 | 17.037 | 1.997 |
| **CE** | 0.936 | 1.000 | 17.204 | 2.163 |
| Gaussian chance constraint | 0.926 | 1.000 | 17.417 | 2.376 |
| Model-based MC chance constraint | 0.939 | 1.000 | 17.841 | 2.800 |
| CPP (Zhao et al.) | 0.947 | 1.000 | 18.369 | 3.329 |
| **CE+ PAC (v7)** | 0.946 | 1.000 | 19.191 | 4.151 |
| Gaussian belief, Rice extreme-value | 0.956 | 1.000 | 20.044 | 5.004 |
| Scenario approach (PAC, β = 0.01) | 0.961 | 1.000 | 21.929 | 6.889 |
| Lindemann et al., pair-level union bound | 0.964 | 1.000 | 22.265 | 7.225 |
| Wasserstein DRO-CVaR | 0.988 | 1.000 | 42.882 | 27.842 |
| Lindemann et al., union bound | 0.992 | 1.000 | 68.289 | 53.248 |
| Tube-MPC radius margin (W99) | 0.999 | 1.000 | 179.142 | 164.102 |

*Table 3. v7 system comparison on the BCD + LQR-I stack (30 fields per regime, fields 20–49; exploratory). Rows with meet ≥ 0.5, sorted by overlap. Oracle meet rate: R1 0.97, R2 0.90, R3 0.97. Negative regret is possible because the oracle targets exactly 0.9 per field while a method may undershoot it.*

**Observations (exploratory).**

- *Fixed overlap fails.* On every stack, vendor-specification overlap reached a meet rate of 0.00 in all three regimes (e.g. BCD + LQR-I: regret −7.07 pp in R1, −22.04 pp in R2, −7.45 pp in R3), i.e. it is cheap because it misses on almost every run. The farmer-tuned overlap met the target on 0.733 (R1), 0.27 (R2) and 0.700 (R3) of fields.
- *Methods without guarantees under-cover.* GP cautious margins without Bonferroni and pointwise Gaussian belief had meet rate 0.00 in R1 and R2. Model-based MC and Rice-corrected Gaussian belief met the target on 0.43 and 0.30 of R2 fields.
- *Within the conformal class on the same stack,* every baseline with meet ≥ 0.9 was dominated (equal or higher meet rate and lower regret) by a CE variant, with two exceptions: CPP in R2 (meet 0.933, regret 0.96 pp; CE+ has regret 0.003 pp but meet 0.900) and GP cautious margin with Bonferroni in R3 (meet 0.97, regret 2.00 pp; CE has 2.16 pp at meet 1.00). Union-bound calibration (Lindemann et al.) was 10.3–53.2 pp worse than the oracle, consistent with Lemma 3.
- *CE+ is not uniformly best.* In R3, CE-q (regret 0.409, meet 0.867) had lower regret than CE+ (0.957, meet 0.833); the XTE normalisation adds little under GNSS-dominated error, as expected from the near-zero slope $b$. CE+'s meet rate in R3 (0.833) is at the level Proposition 7 predicts for an exactly calibrated marginal method (expected failure rate 14.5%).
- *CE is planner- and controller-agnostic.* Across stacks, the lowest-regret systems with meet ≥ 0.9 were all CE variants (Table 4); better controllers reduce the certified overlap further.

<!-- source: results/v7/summary.txt -->
| Regime | Lowest-regret system with meet ≥ 0.9 | P | meet | overlap % | regret pp |
|---|---|---|---|---|---|
| R1 | Follow-previous-pass + Lenain ctrl + CE+ PAC | 0.946 | 0.967 | 7.471 | −1.406 |
| R2 | BCD + Lenain ctrl + CE+ | 0.907 | 0.900 | 20.301 | −5.251 |
| R3 | BCD + offset-free MPC + CE-q | 0.908 | 0.933 | 15.070 | 0.030 |

*Table 4. Best certified systems across all stacks (v7, exploratory). Regret is relative to the BCD + LQR-I oracle, so stacks with better controllers can have negative regret.*

The matched-coverage comparison, which concerns the zero-data experiments, is reported with them (Section 6.5.3).

### 6.4 Validation of the extreme-value theory

The theory was checked layer by layer against simulation on fields not used elsewhere at that time (R1 wheat 440, R2 paddy 36 with 144 passes, R3 paddy 40; L5 on 8 R1 fields). Each layer used only the previous layer's output; the simulator was used only for checking. This validation was developmental: three theory corrections (observation operator, withdrawal of A2 in favour of a sign-free bound (finally the Bonferroni sandwich of Theorem 4), product form instead of $e^{-M}$) and the integrator-clamp model were introduced *because* earlier checks failed, so these numbers are not a confirmatory test.

<!-- source: docs/theory_evt.md (section 6) -->
| Layer | Quantity | R1 flat RTK | R2 hilly-wet RTK | R3 DGPS |
|---|---|---|---|---|
| 1 | RMS difference, noise-free closed-loop mean vs conditional sample mean | 0.07 cm | 0.20 cm | 0.09 cm |
| 1 | Pair standard deviation, sample / predicted | 1.00 | 0.999 (5–95%: 0.989–1.015) | agrees |
| 1 | Adjacent-section covariance, sample / predicted | — | 0.993 | — |
| 3 | Product form for $P(U\le t\mid C)$ at the 0.9 quantile (predicted / true) | 0.888 / 0.900 | 0.882 / 0.900 | 0.900 / 0.900 |
| 4 | Coverage after a plan change, predicted / simulated | 0.901 / 0.899 | 0.890 / 0.885 | 0.920 / 0.922 |
| 5 | Linearity of $q_{0.9}$ in $\sqrt{2\log N}$ over 8 fields | simulated $R^2=0.989$, predicted $R^2=0.964$; per-field error 0.1–0.7 cm | — | — |

*Table 5. Layer-by-layer validation (after the first round of corrections).*

<!-- source: docs/theory_evt.md (section 6.2) -->
| Regime | First version | Fix 1 (product form, time-varying L1) | Fix 2 (integrator, hybrid exact L2) | Safe upper bound |
|---|---|---|---|---|
| R1 flat RTK | 11.03 / 11.01 | 11.02 / 11.01 | **10.94 / 11.01** (−0.6%, within 1 s.e.) | 11.02 |
| R2 hilly-wet RTK | 15.75 / 15.26 | 15.76 / 15.26 | **15.39 / 15.26** (+0.9%) | 15.76 |
| R3 DGPS | 36.0 / 37.3 (−3.5%) | 37.97 / 37.09 | **37.61 / 37.09** (+1.4%) | 37.97 |

*Table 6. Required margin $q_{0.9}$ (cm), predicted / simulated, without any calibration run.* After fix 2, coverage after a plan change is predicted to within 0.007 (R3: 0.9220 vs 0.9220). The extremal index agrees in R2 (0.30 vs 0.31) but is underpredicted in R3 (0.54 vs 0.66), which does not affect $F_\pi$ (the Rice bound overstates $\mathbb E M$ in conditions far from the tail, where $e^{-M}\approx0$). In the three test conditions of the integrator model, the true variance lay between the best estimate and the safe upper bound, and the upper-bound margin prediction was not below simulation in any regime.

A diagnostic in the hardest condition (R2, slip gain 1.23) showed that the conditional marginals are Gaussian (skewness −0.002, excess kurtosis −0.012) and that a Gaussian model with *sample* moments reproduces the simulated exceedance (0.1105 vs 0.1033), while L1's moments before the integrator fix overstated it by 25%. The residual bias was therefore in L1's moments, which the integrator model removed. The tail remains very sensitive to moment errors: at $u\approx4$, a 1–2% error in standard deviation becomes a 20–30% error in exceedance probability.

### 6.5 Certification with zero target-field data

**Setting (both versions).** Stack BCD + LQR-I; $\varepsilon=0.1$, $\delta=0.1$. Leave-one-field-out: each test field is the new field; every other field contributes **one** historical run at its reference plan ($\lambda_0$ as in CE+, from training fields only). The deployed plan on the test field is evaluated with 200 fresh runs; the per-field oracle is as in Section 6.2. Primary efficiency metric: **excess overlap**, the deployed plan's main-area overlap minus the oracle overlap (pp), averaged over test fields. Comparators use exactly the same data: pooled conformal on raw scores (marginal, PAC), farmer-tuned global overlap, vendor-specification overlap; in v2 also the scale-law-normalised pooled conformal $S/\sqrt{2\log N_f}$ (marginal, PAC), which needs no L1–L4 theory.

#### 6.5.1 E-low v1 (pre-registered; claims not met)

`docs/prereg_lowdata.md` registered the PIT-pivot method CE-EVT on fresh fields (R1 wheat 80–139, R2 paddy 80–136, R3 paddy 80–110) with $n_{\rm cal}=\min(30,\text{pool}-1)$ and the claim that in every regime CE-EVT is valid and at least 10% better than the strongest valid comparator of its class.

<!-- source: results/lowdata/summary.txt -->
| Regime (test fields) | Method | Class | P(no miss) | Valid (v1 test) | Excess pp | Overlap % |
|---|---|---|---|---|---|---|
| R1 (60) | CE-EVT | marginal | 0.885 | NO (p=0.018) | +0.07 | 9.09 |
| R1 | CE-EVT PAC | PAC | 0.966 | yes (2 fails) | +5.35 | 14.37 |
| R1 | Pooled conformal, raw | marginal | 0.900 | yes (p=0.513) | +0.27 | 9.29 |
| R1 | Pooled conformal, raw PAC | PAC | 0.968 | yes (2 fails) | +3.22 | 12.24 |
| R1 | Pooled, scale-law normalised | marginal | 0.887 | NO (p=0.031) | +0.09 | 9.11 |
| R1 | Pooled, scale-law normalised PAC | PAC | 0.966 | yes (1 fail) | +2.49 | 11.51 |
| R1 | Theory only, no conformal | marginal | 0.894 | NO (p=0.028) | −0.04 | 8.98 |
| R1 | Farmer-tuned global overlap | marginal | 0.891 | yes (p=0.099) | −0.02 | 9.00 |
| R1 | Spec overlap (2× p2p) | marginal | 0.000 | NO | −7.29 | 1.73 |
| R2 (57) | CE-EVT | marginal | 0.868 | NO (p=0.000) | −0.90 | 24.13 |
| R2 | CE-EVT PAC | PAC | 0.954 | yes (1 fail) | +3.98 | 29.01 |
| R2 | Pooled conformal, raw | marginal | 0.869 | NO (p=0.000) | −0.81 | 24.22 |
| R2 | Pooled conformal, raw PAC | PAC | 0.947 | yes (1 fail) | +3.26 | 28.30 |
| R2 | Pooled, scale-law normalised | marginal | 0.879 | NO (p=0.002) | −0.52 | 24.52 |
| R2 | Pooled, scale-law normalised PAC | PAC | 0.954 | yes (0 fails) | +4.02 | 29.05 |
| R2 | Theory only, no conformal | marginal | 0.900 | yes (p=0.460) | +0.09 | 25.13 |
| R2 | Farmer-tuned global overlap | marginal | 0.844 | NO (p=0.000) | −2.04 | 22.99 |
| R2 | Spec overlap (2× p2p) | marginal | 0.000 | NO | −21.51 | 3.52 |
| R3 (31) | CE-EVT | marginal | 0.917 | yes (p=0.714) | +5.70 | 20.59 |
| R3 | CE-EVT PAC | PAC | 0.000 | NO (31 fails) | n/a | n/a |
| R3 | Pooled conformal, raw | marginal | 0.922 | yes (p=0.998) | +1.31 | 16.17 |
| R3 | Pooled conformal, raw PAC | PAC | 0.986 | yes (0 fails) | +20.84 | 35.70 |
| R3 | Pooled, scale-law normalised | marginal | 0.914 | yes (p=0.977) | +0.85 | 15.71 |
| R3 | Pooled, scale-law normalised PAC | PAC | 0.987 | yes (0 fails) | +23.44 | 38.30 |
| R3 | Theory only, no conformal | marginal | 0.854 | yes (p=0.059) | −0.51 | 14.38 |
| R3 | Farmer-tuned global overlap | marginal | 0.865 | NO (p=0.000) | −1.23 | 13.63 |
| R3 | Spec overlap (2× p2p) | marginal | 0.453 | NO | −7.36 | 7.50 |

*Table 7. E-low v1 (pre-registered). R3 had 33 infeasible deployments in total; CE-EVT PAC could not deploy on any R3 field.*

<!-- source: results/lowdata/summary.txt -->
| Regime | Class | Comparator (valid, strongest) | CE-EVT excess pp | Comparator excess pp | Relative | Holm p | Claim |
|---|---|---|---|---|---|---|---|
| R1 | PAC | Pooled conformal, raw PAC | +5.35 | +3.22 | −66.3% | 1.0000 | not met |
| R2 | PAC | Pooled conformal, raw PAC | +3.98 | +3.26 | −21.9% | 1.0000 | not met |
| R3 | marginal | Pooled conformal, raw | +5.70 | +1.31 | −334.2% | 1.0000 | not met |

*Table 8. E-low v1 registered comparisons. The claim was not met in any regime.*

**Why v1 failed (post hoc analysis on the same fields; exploratory).** Three causes were identified (`docs/prereg_lowdata_v2.md` §0):

1. *A theory bug.* The variance of the interpolated observation used a stationary approximation, which gave a negative variance on one R3 field and an all-NaN predicted CDF. The NaN was ranked highest and pushed R3's PIT quantile to the extreme tail (hence 31 PAC failures and the +5.70 pp marginal excess). The exact formula is now used.
2. *PIT pivot instability in the tail* (Proposition 6).
3. *A mis-specified marginal validity test.* The registered field-clustered test ignored that all test fields share (almost) the same calibration pool. Given the calibration set, coverage is Beta($k$, $n+1-k$) distributed, with standard deviation about 0.05 at $n=30$, so even the classical pooled-conformal method was judged "invalid" in R2 (0.869). This does not rescue v1: the efficiency claim failed in all three regimes regardless of validity.

The exploratory analysis also concluded that field-level normalisation can only remove **between-field** differences; at $n\approx30$ the PAC rule essentially takes the maximum, which is dominated by **within-field, run-to-run** randomness; and an oracle normalisation (dividing by each field's true required margin) could not beat the classical method in R2 PAC or R3 PAC. These conclusions were written into the v2 pre-registration as predictions.

#### 6.5.2 E-low v2 (pre-registered; both claims met, with a post hoc caveat)

`docs/prereg_lowdata_v2.md` was committed before any v2 result. Changes: ratio pivot (CE-EVT-R) with the $+\infty$ rule; corrected theory; fresh fields 50–79 in each regime (30 per regime), $n_{\rm cal}=29$ (all other fields); scale-law normalisation promoted to a comparator. Validity check: pooled P(no miss) not below the 5% quantile of Beta($k$, $n_{\rm cal}+1-k$), which accounts for the shared calibration set (0.798 for the marginal rule, $k=27$; 0.902 for the PAC rule). Efficiency: excess overlap; relative improvement $=(\text{comparator}-\text{ours})/\text{comparator}$; if the comparator's mean excess is ≤ 0.5 pp the cell has "no room" and a non-inferiority test (ours ≤ comparator + 0.25 pp) is used instead; paired one-sided Wilcoxon, Holm over regime × class × comparator, level 0.05. **Registered claims (only these two):** C1, R1 PAC better than pooled raw PAC by ≥ 10%; C2, R3 marginal better than pooled raw by ≥ 10%; both Holm-significant with CE-EVT-R valid.

<!-- source: results/lowdata_v2/summary.txt -->
| Method | Class | R1 P | R1 excess pp | R1 overlap % | R2 P | R2 excess pp | R2 overlap % | R3 P | R3 excess pp | R3 overlap % |
|---|---|---|---|---|---|---|---|---|---|---|
| **CE-EVT-R (ratio pivot)** | marginal | 0.844 | −0.97 | 7.90 | 0.967 | +5.26 | 30.47 | 0.885 | −0.38 | 15.09 |
| **CE-EVT-R PAC (ratio pivot)** | PAC | 0.914 | +0.27 | 9.14 | 0.979 | +7.44 | 32.65 | 0.978 | +15.25 | 30.72 |
| Pooled conformal, raw | marginal | 0.891 | +0.28 | 9.15 | 0.950 | +3.02 | 28.23 | 0.909 | +1.10 | 16.58 |
| Pooled conformal, raw PAC | PAC | 0.948 | +1.56 | 10.43 | 0.979 | +7.51 | 32.72 | 0.973 | +10.36 | 25.83 |
| Pooled, scale-law normalised | marginal | 0.871 | −0.49 | 8.38 | 0.964 | +4.28 | 29.49 | 0.898 | +0.36 | 15.83 |
| Pooled, scale-law normalised PAC | PAC | 0.925 | +0.61 | 9.48 | 0.979 | +7.29 | 32.50 | 0.969 | +9.14 | 24.61 |
| Farmer-tuned global overlap | marginal | 0.895 | +0.35 | 9.22 | 0.846 | −2.20 | 23.00 | 0.836 | −1.95 | 13.53 |
| Spec overlap (2× p2p) | marginal | 0.000 (invalid) | −7.12 | 1.75 | 0.000 (invalid) | −21.75 | 3.46 | 0.410 (invalid) | −7.89 | 7.59 |
| CE-EVT, PIT pivot (reported, not claimed) | marginal | 0.844 | −0.95 | 7.92 | 0.971 | +6.44 | 31.65 | 0.885 | −0.41 | 15.07 |
| CE-EVT PAC, PIT pivot (reported, not claimed) | PAC | 0.912 | +0.24 | 9.10 | 0.981 | +8.00 | 33.21 | 0.987 | +28.38 | 43.86 |
| Theory only, no conformal (no guarantee) | — | 0.904 | +0.05 | 8.92 | 0.906 | +0.17 | 25.38 | 0.881 | −0.59 | 14.89 |

*Table 9. E-low v2, all methods and cells (30 test fields per regime, fields 50–79, no infeasible deployments). All methods except vendor-spec overlap passed the Beta validity check (marginal threshold 0.798, PAC 0.902). "Theory only" deploys $\hat F_g^{-1}(1-\varepsilon)$ without conformal calibration and has no guarantee; the summary file applies the marginal Beta check to it, which is not meaningful for a method without an order-statistic rule.*

<!-- source: results/lowdata_v2/summary.txt -->
| Regime | Class | Comparator | Ours pp | Comparator pp | Relative | Abs. overlap rel. | Holm p | Outcome |
|---|---|---|---|---|---|---|---|---|
| R1 | marginal | Pooled conformal, raw | −0.97 | +0.28 | no room | +13.7% | 0.0000 | non-inferior |
| R1 | marginal | Scale-law normalised | −0.97 | −0.49 | no room | +5.7% | 0.0000 | non-inferior |
| R1 | marginal | Farmer-tuned | −0.97 | +0.35 | no room | +14.4% | 0.0000 | non-inferior |
| **R1** | **PAC** | **Pooled conformal, raw PAC (C1)** | **+0.27** | **+1.56** | **+82.6%** | +12.4% | **0.0002** | **better ≥ 10% — claim met** |
| R1 | PAC | Scale-law normalised PAC | +0.27 | +0.61 | +55.1% | +3.5% | 0.0785 | not significant |
| R2 | marginal | Pooled conformal, raw | +5.26 | +3.02 | −74.2% | −7.9% | 1.0000 | worse |
| R2 | marginal | Scale-law normalised | +5.26 | +4.28 | −22.9% | −3.3% | 1.0000 | worse |
| R2 | marginal | Farmer-tuned | +5.26 | −2.20 | no room | −32.5% | 1.0000 | non-inferiority not shown |
| R2 | PAC | Pooled conformal, raw PAC | +7.44 | +7.51 | +1.0% | +0.2% | 1.0000 | no improvement |
| R2 | PAC | Scale-law normalised PAC | +7.44 | +7.29 | −2.0% | −0.5% | 1.0000 | no improvement |
| **R3** | **marginal** | **Pooled conformal, raw (C2)** | **−0.38** | **+1.10** | **+134.7%** | +9.0% | **0.0012** | **better ≥ 10% — claim met** |
| R3 | marginal | Scale-law normalised | −0.38 | +0.36 | no room | +4.7% | 0.0016 | non-inferior |
| R3 | marginal | Farmer-tuned | −0.38 | −1.95 | no room | −11.5% | 1.0000 | non-inferiority not shown |
| R3 | PAC | Pooled conformal, raw PAC | +15.25 | +10.36 | −47.1% | −18.9% | 1.0000 | worse |
| R3 | PAC | Scale-law normalised PAC | +15.25 | +9.14 | −66.9% | −24.8% | 1.0000 | worse |

*Table 10. E-low v2 pre-registered comparisons (excess overlap, pp; Holm over all rows). "Abs. overlap rel." is the relative difference in absolute overlap, reported as registered. Relative improvement above 100% occurs when our excess is negative.*

**Registered predictions versus outcomes.** Table 11 compares each cell with the prediction written before the run.

<!-- source: docs/prereg_lowdata_v2.md (predictions); results/lowdata_v2/summary.txt (outcomes) -->
| Regime | Class | Predicted vs pooled raw | Observed | Predicted vs scale law | Observed |
|---|---|---|---|---|---|
| R1 | PAC | improve ≥ 10% (claim C1) | +82.6%, Holm p 0.0002 — **as predicted** | about equal (scale law slightly better) | +55.1%, not significant — direction **not as predicted** |
| R1 | marginal | no room → non-inferior | non-inferior — as predicted | non-inferior | non-inferior — as predicted |
| R2 | PAC | no improvement | +1.0%, n.s. — as predicted | no improvement | −2.0% — as predicted |
| R2 | marginal | no room → non-inferior | comparator +3.02 pp (room existed); ours worse (−74.2%) — **prediction wrong** | non-inferior | worse (−22.9%) — **prediction wrong** |
| R3 | marginal | improve ≥ 10% (claim C2) | +134.7%, Holm p 0.0012 — **as predicted** | improve | comparator +0.36 pp (no room); non-inferior — partly as predicted |
| R3 | PAC | no improvement | worse (−47.1%) — as predicted (no improvement) | no improvement | worse (−66.9%) — as predicted |

*Table 11. Pre-registered predictions and outcomes.*

**Realised marginal coverage below 0.9 is expected.** In R1, CE-EVT-R (marginal) reached pooled P(no miss) 0.844, and in R3 0.885. With $n_{\rm cal}=29$, the marginal rule takes $k=\lceil30\times0.9\rceil=27$, and given the calibration set the coverage of a new field is Beta(27, 3), with mean 0.9, standard deviation ≈0.054 and 5% quantile 0.798. All 30 test fields of a regime share 28 of their 29 calibration fields, so the pooled realised coverage is essentially **one draw** from this distribution, not an average over independent calibrations. 0.844 is about one standard deviation below the mean and above the registered 5% bound; pooled conformal on raw scores (0.891) and the scale-law variant (0.871) show the same draw-to-draw spread. The marginal guarantee is an average over calibration draws; a user who needs a per-calibration statement must use the PAC rule, at the price shown in the PAC rows. Section 6.8 checks the guarantee directly over both sources of randomness.

**Caveat on the size of the v2 gains (post hoc; Section 6.5.3).** The registered claims C1 and C2 stand as pre-registered results. Their large *relative* gains, however, were mostly differences in realised coverage at the single calibration draw, not differences in efficiency. In C1 (R1 PAC) the comparator, raw pooled PAC, realised 0.948 against 0.914 for CE-EVT-R PAC; in C2 (R3 marginal) raw pooling realised 0.909 against 0.885 (Table 9). Once each pivot is rescaled to the same realised coverage, the gap shrinks from +1.56 vs +0.27 pp to +0.41 vs +0.06 pp (C1) and from +1.10 vs −0.38 pp to +0.66 vs +0.46 pp (C2) (Table 11a). The v2 results should therefore not be read as evidence that the theory pivot is materially more efficient than raw pooling within one machine configuration.

#### 6.5.3 Matched-coverage re-analysis of E-low v2 (post hoc, secondary)

Pivots that deploy different margins also reach different realised coverage, so their excess overlap at one calibration draw is not directly comparable: a pivot that happens to under-cover looks cheap. `scripts/matched_coverage.py` (written after the v2 results; post hoc and secondary) rescales each pivot family on the E-low v2 test fields by one common factor $c$ so that pooled realised P(no miss) over the 30 test fields is exactly 0.9, and reports excess overlap at that matched coverage. $c>1$ means the pivot under-covered at the registered draw, $c<1$ that it over-covered.

<!-- source: results/lowdata_v2/matched_coverage.txt -->
| Regime | Class | Raw (no pivot) | Scale law | CQR, one-run trained | Features, oracle-trained | Theory (CE-EVT-R) | Oracle (ideal) |
|---|---|---|---|---|---|---|---|
| R1 | marginal | +0.40 (c 1.019) | +0.14 (1.050) | +0.00 (1.066) | +0.12 (1.063) | +0.10 (1.086) | +0.19 (1.072) |
| R1 | PAC | +0.41 (0.906) | +0.12 (0.965) | −0.00 (1.014) | +0.08 (0.994) | +0.06 (0.984) | +0.16 (0.993) |
| R2 | marginal | −0.05 (0.913) | −0.13 (0.879) | −0.01 (0.850) | −0.07 (0.868) | −0.08 (0.860) | −0.06 (0.882) |
| R2 | PAC | −0.07 (0.814) | −0.15 (0.816) | −0.10 (0.829) | −0.10 (0.810) | −0.05 (0.817) | −0.09 (0.826) |
| R3 | marginal | +0.66 (0.973) | +0.48 (1.007) | +2.73 (1.030) | +0.42 (1.039) | +0.46 (1.049) | +0.32 (1.073) |
| R3 | PAC | +0.82 (0.671) | +0.49 (0.694) | +3.10 (0.605) | +0.40 (0.706) | +0.60 (0.586) | +0.41 (0.622) |

*Table 11a. Excess overlap (pp) at matched pooled coverage 0.9 on the E-low v2 test fields, with the common factor $c$ in parentheses (post hoc). "CQR, one-run trained" is a ridge regression on field features trained with one run per training field; "features, oracle-trained" is the model of Table 13.*

Three observations. (i) **Within a regime the pivots are nearly indistinguishable at matched coverage.** Excluding the one-run-trained CQR, all pivots, including the unattainable oracle, lie within 0.30 pp of each other in R1 marginal, 0.35 pp in R1 PAC, 0.08–0.10 pp in R2 and 0.34–0.42 pp in R3; the theory pivot is never more than 0.20 pp from the best pivot of its cell. The differences of several percentage points in Table 9 (for example R2 marginal, +5.26 vs +3.02 pp) are therefore almost entirely differences in realised coverage at one calibration draw. (ii) **The registered gains shrink accordingly** (see the caveat in Section 6.5.2): the theory pivot remains below raw pooling in R1 (+0.10 vs +0.40 pp marginal, +0.06 vs +0.41 pp PAC) and in R3 (+0.46 vs +0.66, +0.60 vs +0.82 pp), but these are differences of tenths of a point. (iii) **A feature predictor trained on one run per field can fail badly** in the DGPS regime (+2.73 and +3.10 pp in R3), consistent with its large log error in Table 14.

The factors $c$ also show what happened at the registered draw: CE-EVT-R under-covered in R1 marginal ($c=1.086$), matching its realised 0.844, and every pivot over-covered in R2 ($c$ 0.81–0.91), matching the realised 0.95–0.98 of Table 9. This is the conditional, single-draw coverage explained in Section 6.5.2; Section 6.8 checks the guarantee itself.

#### 6.5.4 Information limit (secondary)

The values below are the observed side of Proposition 8 (Section 5.5), whose theory-only prediction is reported there.

Two cells did not improve as predicted (R2 PAC, R3 PAC) and one cell did worse than predicted (R2 marginal). An ideal pivot that divides each field's score by its true per-field required margin $\lambda^\star_f$ ("oracle normalisation", not available in practice) bounds what any field-level normalisation can achieve. The registered plan required reporting this bound; the numbers below come from the post hoc script `scripts/feature_pivot.py`, which reproduces the registered theory and raw rows exactly (e.g. R1 marginal −0.97 and R3 PAC +15.25 pp).

<!-- source: results/lowdata_v2/feature_pivot.txt -->
| Regime | Class | Raw (no pivot) | Scale law | Theory (CE-EVT-R) | Oracle (ideal) | Best possible relative gain over raw |
|---|---|---|---|---|---|---|
| R1 | marginal | +0.28 | −0.49 | −0.97 | −0.71 | no room |
| R1 | PAC | +1.56 | +0.61 | +0.27 | +0.24 | 84.6% |
| R2 | marginal | +3.02 | +4.28 | +5.26 | +4.22 | none (ideal worse than raw) |
| R2 | PAC | +7.51 | +7.29 | +7.44 | +6.81 | 9.3% |
| R3 | marginal | +1.10 | +0.36 | −0.38 | −0.91 | — (ideal below oracle) |
| R3 | PAC | +10.36 | +9.14 | +15.25 | +12.86 | none (ideal worse than raw) |

*Table 12. Mean excess overlap (pp) of field-level pivots on the E-low v2 fields; leave-one-field-out, $n_{\rm cal}=29$. The last column is $(\text{raw}-\text{ideal})/\text{raw}$, computed from the table.*

Interpretation:

- **R2 PAC is at the information limit.** Even ideal normalisation reduces excess overlap by only 9.3% relative to raw pooling, below the 10% threshold. The ratio $\lambda_g/\lambda^\star_g$ under the ideal pivot has standard deviation 0.000 across R2 test fields (`feature_pivot.txt`): the PAC rule picks the largest of 29 normalised scores ($k=29$, consistent with the Beta 5% bound 0.902 $=0.05^{1/29}$), and after perfect normalisation this maximum is a property of within-field run-to-run randomness common to all fields. No field-level information can reduce it.
- **R3 PAC.** Ideal normalisation is *worse* than raw (+12.86 vs +10.36 pp), and the theory pivot is worse still (+15.25). With DGPS, run-to-run variation (large GNSS jumps) dominates between-field variation; the maximum of 29 normalised scores is driven by the worst single run, and normalisation that equalises fields does not help.
- **R2 marginal.** Ideal normalisation is worse than raw (+4.22 vs +3.02). With one calibration draw, realised coverage differs between pivots (raw 0.950 vs CE-EVT-R 0.967 in Table 9), so excess overlap at a single draw mixes efficiency with calibration-draw luck. At matched coverage (Table 11a) raw, theory and oracle pivots in R2 marginal differ by at most 0.03 pp (−0.05, −0.08, −0.06 pp). R2 fields are homogeneous (paddy, similar size and slope class): the between-field spread of $\lambda_g/\lambda^\star_g$ under raw pooling is only 0.051 (sd), against 0.088 in R1 and 0.113 in R3, leaving little for a pivot to remove.
- **Where the pivot helped at the registered draw,** R1 PAC and R3 marginal, the theory pivot comes close to or beats the ideal (R1 PAC 0.27 vs 0.24 pp). At matched coverage these gains are tenths of a point (Section 6.5.3).

### 6.6 Is the theory needed? Learned feature predictors (post hoc) and a mixed-fleet probe (developmental)

Reviewers will ask whether a simple regression on field features could replace the five-layer theory as the pivot scale. The two feature analyses in this subsection were designed after the E-low v2 results and are **post hoc and secondary**; the mixed-fleet probe at the end is developmental (it designed E-low v3). A ridge regression of $\log\lambda^\star_f$ on six field features (log effective length, log area, log number of passes, mean slope, mean pass terrain feature, log lateral extent) is trained on the E-low v1 pool (fields 80+, disjoint from the test fields) and used as the pivot scale on the v2 fields.

<!-- source: results/lowdata_v2/feature_pivot.txt -->
| Regime | Train fields | Feature model train $R^2$ | corr(log q, log λ*): theory / features / scale law | log-error sd: theory / features | Excess pp marginal: features / theory | Excess pp PAC: features / theory |
|---|---|---|---|---|---|---|
| R1 | 60 | 0.92 | 0.95 / 0.98 / 0.97 | 0.029 / 0.020 | −0.66 / −0.97 | +0.16 / +0.27 |
| R2 | 57 | 0.85 | 0.80 / 0.89 / 0.88 | 0.029 / 0.021 | +4.89 / +5.26 | +7.68 / +7.44 |
| R3 | 30 | 0.58 | 0.87 / 0.70 / 0.70 | 0.056 / 0.080 | −0.23 / −0.38 | +8.73 / +15.25 |

*Table 13. Theory pivot vs a feature regression trained on oracle targets $\lambda^\star_f$ from hundreds of simulated runs per training field (post hoc).*

With oracle training targets — the best signal such a predictor could receive, but one that requires hundreds of runs on each training field — the feature model is slightly more accurate than the theory in R1 and R2 and gives lower excess overlap in R1 PAC and R3 PAC. The theory is more accurate in R3 (log-error sd 0.056 vs 0.080), where terrain and GNSS interactions are not captured by the features.

The practical question is what such a predictor achieves with the data the low-data setting actually provides: one run per field.

<!-- source: results/lowdata_v2/feature_learning_curve.txt -->
| Regime (theory, zero data) | m training fields | features ← oracle targets | features ← one run | theory + features ← one run |
|---|---|---|---|---|
| R1 (0.029) | 5 | 0.044 | 0.355 | 0.177 |
| | 10 | 0.030 | 0.173 | 0.107 |
| | 20 | 0.023 | 0.141 | 0.098 |
| | 30 | 0.022 | 0.130 | 0.105 |
| | 60 | 0.020 | 0.095 | 0.091 |
| R2 (0.029) | 5 | 0.034 | 0.202 | 0.086 |
| | 10 | 0.027 | 0.152 | 0.080 |
| | 20 | 0.023 | 0.097 | 0.057 |
| | 30 | 0.022 | 0.079 | 0.058 |
| | 57 | 0.021 | 0.049 | 0.045 |
| R3 (0.056) | 5 | 0.123 | 0.406 | 0.220 |
| | 10 | 0.094 | 0.324 | 0.216 |
| | 20 | 0.083 | 0.246 | 0.169 |
| | 30 | 0.080 | 0.206 | 0.146 |

*Table 14. Standard deviation of $\log(q/\lambda^\star)$ on the 30 v2 test fields (lower is better), mean over 40 random training subsets (one subset for the full pool). Post hoc.*

With one run per training field, a feature predictor does not reach the zero-data theory within the available pools: at the full pool its log error is 0.095 (R1), 0.049 (R2) and 0.206 (R3), against 0.029, 0.029 and 0.056 for the theory. Learning a feature correction of the theory from one run per field also degrades it (0.091, 0.045, 0.146). A feature predictor matches the theory only when it is trained on oracle targets from about 10 (R1, R2) fields, which requires hundreds of runs per field — the very data whose absence motivates the low-data setting. In R3 even oracle-trained features with 30 fields do not reach the theory. We conclude that, in this setting, the theory is the only one of the examined pivots that is accurate without per-field run data; we do not claim that it is the most accurate pivot when such data exist.

**Across machine configurations (design probe for E-low v3; developmental).** Within one regime all fields share the implement width, GNSS grade and controller, so the between-field spread that a pivot can remove is modest. A farm or contractor, however, typically operates several machine configurations. Before E-low v3, we pooled the v1 and v2 fields of all three regimes (RTK 3 m, RTK 1.5 m, DGPS 6 m) and measured how well each candidate scale predicts the per-field required margin $\lambda^\star_f$ (`docs/prereg_lowdata_v3.md` §0). This probe used only data already published in v1 and v2, none of the v3 test fields, and served to design the v3 claims; it is not a test.

<!-- source: docs/prereg_lowdata_v3.md (section 0) -->
| Predictor of $\lambda^\star_f$ in a mixed fleet | Run data needed | log-error sd |
|---|---|---|
| Theory (CE-EVT-R scale) | none | **0.047** |
| Normalised by implement width | none | 0.388 |
| Vendor pass-to-pass spec × scale law | none | 0.433 |
| Ridge regression on field features + machine configuration, trained with one run per field (147 fields) | one run per field | 0.136 |
| Same regression trained on oracle $\lambda^\star_f$ (not available in practice) | hundreds of runs per field | 0.054 |

*Table 14a. Mixed-fleet design probe (developmental, computed on v1/v2 data before E-low v3).*

Across configurations, the simple scales have log errors of 0.388–0.433, the one-run-trained regression 0.136 against 0.047 for the theory, and even oracle training (0.054) does not reach the theory. This motivated the registered claim C3 of E-low v3: that the theory's advantage, small within one configuration, becomes decisive across configurations.

### 6.7 E-low v3 (pre-registered; claims partially met)

`docs/prereg_lowdata_v3.md` was committed before any computation on its test fields. It addressed four open points of v2: whether the theory is needed at all, the low realised marginal coverage of one calibration draw, the absence of gains in some cells, and the missing matched-coverage comparison.

**Design.** Test fields: indices 5–19 in each regime (3 × 15 = 45 fields), never used in any E-low design or analysis. Calibration pool: the 30 v2 fields of the same regime, each with its one existing historical run (same-regime scenario), or all v2 fields of the three regimes (90 fields; mixed-fleet scenario, 45 test fields). Training pool (gate and CQR fitting only): the v1 fields (80 onward; 147 fields), disjoint from both. All methods are scale pivots $\lambda_g=q_g t$ with $t$ the conformal quantile of $S/q$ on $n_{\rm cal}=25$ calibration fields: raw pooling ($q\equiv1$), scale law ($\sqrt{2\log N_f}$), vendor spec × scale law ($\mathrm{p2p}_f\sqrt{2\log N_f}$; differs from the scale law only in the mixed fleet), a CQR-type ridge regression of $\log S$ on field features and machine configuration (log width, log p2p) trained with one run per training field (Romano et al., 2019), CE-EVT-R, and **CE-EVT-R-G**, a gated variant that, per scenario × regime × class, chooses between the theory and the best classical pivot on the training pool only: leave-one-out with 200 random calibration subsets, a common factor matching proxy coverage to $1-\varepsilon$, and the theory chosen only if its proxy excess overlap is at least 0.1 pp below the best classical pivot. Because the gate is a fixed function of the disjoint training pool, conformal validity is unaffected (as for Proposition 3). Deployments are capped at the planner limit $0.8\,w/2$. Each test field has a margin → P(no miss)/overlap curve (200 runs per point, common random numbers); each scenario × method × class is evaluated over 400 calibration subsets drawn from the pool. Validity: mean coverage ≥ 0.89 (marginal) or a fraction ≥ 0.85 of subsets with coverage ≥ 0.9 (PAC). Efficiency: per-field mean excess overlap, one-sided paired Wilcoxon over test fields, Holm over all C3 and C4 comparisons, level 0.05.

**Registered claims.** *C3 (mixed fleet):* CE-EVT-R at least 10% better than **every** comparator (raw, scale law, spec × scale law, CQR), in both classes, Holm-significant, and valid. *C4 ('never worse', same regime):* CE-EVT-R-G non-inferior (margin 0.25 pp, Holm-significant) to the best comparator (raw, scale law, CQR) and valid in all six regime × class cells. *C5 (secondary):* the gate's choice predicts in advance where CE-EVT-R gains ≥ 10% over raw pooling; hit rate over 6 + 2 cells.

<!-- source: results/lowdata_v3/summary.txt -->
| Method | Marginal: coverage mean | P(cov ≥ 0.9) | Excess pp | Matched-cov. excess pp | PAC: coverage mean | P(cov ≥ 0.9) | Excess pp | Matched-cov. excess pp |
|---|---|---|---|---|---|---|---|---|
| Raw pooling | 0.935 | 0.83 | +24.80 | +12.89 | 0.967 | 0.98 | +54.02 | +13.47 |
| Scale law | 0.935 | 0.84 | +33.97 | +17.22 | 0.967 | 0.97 | +66.95 | +17.07 |
| Spec × scale law | 0.930 | 0.69 | +13.18 | +10.68 | 0.973 | 0.95 | +20.05 | +9.97 |
| CQR (one-run trained) | 0.931 | 0.82 | +3.16 | +1.30 | 0.963 | 0.96 | +9.01 | +2.43 |
| **CE-EVT-R** | 0.918 | 0.55 | **+1.87** | **+0.73** | 0.958 | 0.86 | **+7.91** | +2.64 |
| CE-EVT-R-G (gate chose theory) | 0.916 | 0.54 | +1.73 | +0.98 | 0.960 | 0.88 | +8.50 | +3.52 |

*Table 15. E-low v3, mixed fleet (45 test fields from three machine configurations, 400 calibration subsets of $n_{\rm cal}=25$ from a pool of 90). All methods valid by the registered criteria. Deployments below the lowest point of a field's curve grid (counted in the summary file: raw 485 and 69, scale law 648 and 106, CQR 284 and 113, CE-EVT-R 1 and 0, marginal and PAC, out of 400 × 45) have their coverage and overlap read at that lowest point (0.6 $\lambda^\star$ in the pre-registration), which overstates both the coverage and the overlap of those deployments.*

<!-- source: results/lowdata_v3/summary.txt -->
| Claim | Scenario / cell | Comparison | Ours pp | Comparator pp | Relative | Holm p | Outcome |
|---|---|---|---|---|---|---|---|
| C3 | mixed, marginal | vs raw | +1.87 | +24.80 | +92.5% | 0.0000 | met |
| C3 | mixed, marginal | vs scale law | +1.87 | +33.97 | +94.5% | 0.0000 | met |
| C3 | mixed, marginal | vs CQR | +1.87 | +3.16 | +40.9% | 0.0029 | met |
| C3 | mixed, marginal | vs spec × scale law | +1.87 | +13.18 | +85.8% | 0.1805 | **not met** |
| C3 | mixed, PAC | vs raw | +7.91 | +54.02 | +85.4% | 0.0000 | met |
| C3 | mixed, PAC | vs scale law | +7.91 | +66.95 | +88.2% | 0.0000 | met |
| C3 | mixed, PAC | vs CQR | +7.91 | +9.01 | +12.3% | 0.0648 | **not met** |
| C3 | mixed, PAC | vs spec × scale law | +7.91 | +20.05 | +60.6% | 0.9555 | **not met** |
| C4 | R1, marginal | gated (raw) vs best (CQR) | +0.17 | −0.29 | — | 1.0000 | **not met** |
| C4 | R1, PAC | gated (scale law) vs best (scale law) | +0.39 | +0.37 | — | 0.0003 | met |
| C4 | R2, marginal | gated (scale law) vs best (raw) | +6.12 | +5.63 | — | 1.0000 | **not met** |
| C4 | R2, PAC | gated (theory) vs best (scale law) | +7.02 | +7.31 | — | 0.1912 | **not met** |
| C4 | R3, marginal | gated (theory) vs best (CQR) | +3.93 | +1.09 | — | 1.0000 | **not met** |
| C4 | R3, PAC | gated (raw) vs best (CQR) | +10.76 | +7.64 | — | 1.0000 | **not met** |

*Table 16. E-low v3 registered comparisons (mean excess overlap over 400 calibration subsets; Holm over all 14 rows). C3: 5 of 8 comparisons met, so the claim as registered (every comparator, both classes) is **not met**. C4: met in 1 of 6 cells, **not met**.*

<!-- source: results/lowdata_v3/summary.txt -->
| Regime | Class | Gate proxy excess pp (theory / raw / scale law) → choice | Raw | Scale law | CQR | CE-EVT-R | CE-EVT-R-G | C5 |
|---|---|---|---|---|---|---|---|---|
| R1 | marginal | +1.60 / +1.52 / +1.52 → raw | +0.18 / +0.24 (0.896) | −0.02 / +0.08 (0.893) | −0.29 / +0.26 (0.861, invalid) | −0.18 / +0.15 (0.877, invalid) | +0.17 / +0.24 (0.896) | miss |
| R1 | PAC | +2.44 / +2.99 / +2.20 → scale law | +0.81 / +0.23 (0.97) | +0.37 / +0.06 (0.96) | +0.68 / +0.27 (0.85) | +0.17 / +0.07 (0.98) | +0.39 / +0.05 (0.98) | miss |
| R2 | marginal | +3.89 / +3.98 / +3.52 → scale law | +5.63 / +0.34 (0.967) | +6.14 / +0.29 (0.970) | +10.02 / +0.87 (0.983) | +5.39 / +0.27 (0.967) | +6.12 / +0.24 (0.970) | hit |
| R2 | PAC | +3.49 / +3.96 / +4.03 → theory | +7.95 / +0.24 (1.00) | +7.31 / +0.13 (1.00) | +22.11 / +0.84 (1.00) | +7.09 / +0.20 (1.00) | +7.02 / +0.21 (1.00) | hit |
| R3 | marginal | +4.14 / +4.83 / +4.64 → theory | +2.46 / +0.62 (0.924) | +2.35 / +0.56 (0.922) | +1.09 / +1.34 (0.897) | +3.97 / +1.64 (0.931) | +3.93 / +1.57 (0.931) | miss |
| R3 | PAC | +17.37 / +6.19 / +8.90 → raw | +10.99 / +1.22 (1.00) | +9.03 / +1.22 (1.00) | +7.64 / +1.65 (0.96) | +13.04 / +1.16 (0.97) | +10.76 / +1.44 (1.00) | hit |

*Table 17. E-low v3, same-regime cells (15 test fields each). Each method cell: mean excess pp / excess pp at matched coverage (mean coverage for marginal, fraction of subsets with coverage ≥ 0.9 for PAC). C5 for the mixed fleet: the gate chose the theory in both classes and the theory gained ≥ 10% over raw (hits); C5 total 5 of 8.*

**C3 (mixed fleet): partially met.** Against raw pooling, the scale law and (marginal) CQR, the theory pivot reduced mean excess overlap by 40.9–94.5% with Holm p ≤ 0.0029, and it was valid. Three comparisons were not met. Against spec × scale law the mean gains were large (+1.87 vs +13.18 pp marginal, +7.91 vs +20.05 pp PAC) but not significant (Holm p 0.1805 and 0.9555): the signed-rank test is driven by the per-field sign and rank of differences, so a large mean gain that is concentrated on part of the 45 test fields need not make the comparison significant (an interpretation; the per-field differences are not tabulated in the summary file). Against CQR in the PAC class the gain was 12.3% with Holm p 0.0648. Because the claim required every comparator in both classes, **C3 as registered is not met.** At matched coverage the theory pivot is the cheapest in the marginal class (+0.73 pp against +1.30 for CQR and +10.68 to +17.22 for the classical scales) and close to CQR in PAC (+2.64 vs +2.43 pp). Note that the CQR comparator here already uses machine configuration as a feature; the classical scales that ignore the configuration (raw, scale law) are an order of magnitude worse, as the design probe predicted.

**C4 ('never worse' with a gate): failed.** CE-EVT-R-G was non-inferior to the best comparator only in R1 PAC. We see two reasons, both visible in Table 17. First, **within one regime the differences between pivots are below the resolution of 15 test fields with one historical run each**: at matched coverage the raw, scale-law and theory pivots differ by at most 0.17 pp in R1, 0.11 pp in R2 and 0.06 pp in R3 PAC, while the unmatched means move by several points with realised coverage (R2 marginal: CQR +10.02 pp at coverage 0.983, raw +5.63 pp at 0.967), so the comparator that happens to be best on the test fields is largely selected by noise, and the non-inferiority margin of 0.25 pp is of the same order as the differences being tested. In R1 marginal the 'best' comparator (CQR, −0.29 pp) was itself invalid (coverage 0.861). Second, **the training-only gate is unreliable**: the proxy difference between the theory and the best classical pivot was 0.08–0.50 pp in five of six cells, and in three of six same-regime cells it predicted the direction of the theory's gain wrongly (C5 misses: R1 marginal and PAC, where the theory gained 201.2% and 79.6% over raw on the test fields although the gate chose a classical pivot, and R3 marginal, where the gate chose the theory and the theory lost 61.4% to raw). A gate that ranks pivots whose true efficiency differs by tenths of a point cannot be expected to choose reliably from 30–60 training fields with one run each. The one exception at matched coverage is R3 marginal, where the theory pivot was more than 1 pp worse than the scale law (+1.64 vs +0.56 pp); over redrawn historical runs (Section 6.8) the difference is small (+5.06 vs +4.74 pp), which suggests a fixed-pool effect, but this is a post hoc reading.

**C5 (secondary): 5 of 8 hits** (both mixed-fleet cells, R2 marginal and PAC, R3 PAC).

**Realised marginal coverage of CE-EVT-R in R1 was 0.877**, below the registered 0.89 threshold, so CE-EVT-R was formally invalid in that cell (as was CQR, 0.861), although the coverage is averaged over 400 calibration subsets. These subsets are all drawn from the same 30 fields with the same single historical run per field, so the luck of those runs is not averaged out. Section 6.8 tests the guarantee with that second source of randomness included.

### 6.8 Direct check of the coverage guarantee over both sources of randomness (pre-registered)

The marginal guarantee of Proposition 5 averages over two sources of randomness: which fields calibrate and which is new, and the outcome of each calibration field's single historical run. All earlier checks (v2's single draw; v3's 400 subsets of one pool) held the second source fixed. Given a fixed set of historical runs, the coverage of a new field is a draw from Beta($k$, $n+1-k$) (Section 6.5.2), so the realised 0.844 (v2, R1 marginal) and 0.877 (v3, R1 marginal) measure the luck of one set of historical runs and say nothing on their own about whether the guarantee holds. Even averaging over 400 subsets of the v2 pool ($n_{\rm cal}=25$) leaves R1 marginal coverage at 0.880 for the theory pivot and 0.889 for the scale law (`results/lowdata_v2/matched_coverage.txt`).

`docs/prereg_validity.md` was committed before the computation. For each regime, the 45 fields of v2 and v3 (135 for the mixed fleet) each received a bank of 200 independent historical runs at the reference plan, with seeds distinct from all evaluation seeds. Each of 4000 replicates per scenario × method × class (i) drew 25 calibration fields at random, the remaining fields being new (20 per regime; 110 in the mixed fleet), (ii) drew one historical run per calibration field from its bank, and (iii) deployed $\lambda_g=\min(q_gt,\text{cap})$ on every new field, recording mean coverage and excess overlap. Criteria (the theorem applies to every scale pivot, so this tests the guarantee and its implementation, not the methods against each other): marginal, mean coverage over replicates ≥ $1-\varepsilon-0.005$; PAC, fraction of replicates with coverage ≥ $1-\varepsilon$ at least $1-\delta-0.02$.

<!-- source: results/lowdata_v3/validity_resample.txt -->
| Scenario | Class | Raw pooling | Scale law | Spec × scale law | Theory (CE-EVT-R) |
|---|---|---|---|---|---|
| R1 | marginal | 0.9193 / 0.700 / +1.16 | 0.9205 / 0.707 / +0.92 | — | 0.9194 / 0.689 / +0.92 |
| R1 | PAC | 0.9597 / 0.911 / +3.99 | 0.9604 / 0.911 / +3.75 | — | 0.9607 / 0.917 / +3.77 |
| R2 | marginal | 0.9283 / 0.754 / +2.95 | 0.9282 / 0.767 / +2.90 | — | 0.9286 / 0.759 / +3.06 |
| R2 | PAC | 0.9655 / 0.946 / +11.15 | 0.9652 / 0.949 / +10.63 | — | 0.9641 / 0.935 / +10.56 |
| R3 | marginal | 0.9225 / 0.733 / +5.21 | 0.9214 / 0.717 / +4.74 | — | 0.9211 / 0.717 / +5.06 |
| R3 | PAC | 0.9605 / 0.932 / +21.68 | 0.9595 / 0.926 / +21.04 | — | 0.9603 / 0.930 / +21.45 |
| Mixed fleet | marginal | 0.9295 / 0.745 / +29.84 | 0.9283 / 0.750 / +37.21 | 0.9250 / 0.736 / +12.82 | 0.9243 / 0.747 / **+2.96** |
| Mixed fleet | PAC | 0.9619 / 0.935 / +61.98 | 0.9631 / 0.942 / +73.86 | 0.9629 / 0.928 / +23.21 | 0.9625 / 0.931 / **+14.69** |

*Table 18. Direct check over 4000 replicates (random 25-field calibration split + redrawn historical run). Each cell: mean coverage / fraction of replicates with coverage ≥ 0.9 / mean excess overlap (pp, descriptive). Standard errors of mean coverage 0.0005–0.0008. Every cell passes its criterion.*

**The guarantee holds.** All 26 cells pass. Marginal mean coverage is 0.9193–0.9295, between $1-\varepsilon$ and the upper bound $1-\varepsilon+1/(n+1)$ of Section 4.1; the PAC fraction is 0.911–0.949 against a required 0.88. The sub-0.9 values of v2 and v3 were the luck of one fixed set of historical runs, as the conditional Beta($k$, $n+1-k$) coverage predicts; the fraction of replicates with marginal coverage ≥ 0.9 (0.689–0.767) shows how often a single draw falls below 0.9 even though the guarantee holds.

**Efficiency over replicates (descriptive, not tested).** In the mixed fleet, the theory pivot's mean excess overlap was +2.96 pp against +12.82 for spec × scale law and +29.84 for raw pooling (marginal), and +14.69 against +23.21 and +61.98 pp (PAC). Within a regime, the three pivots differ by tenths of a point relative to excess overlaps of 0.92–21.68 pp (largest gap: R3 PAC, +21.04 for the scale law vs +21.68 pp for raw pooling), which is within the noise of the experiments above. This replicates, over both sources of randomness, the pattern of Sections 6.5.3 and 6.7: the theory's advantage is across machine configurations, not within one.

### 6.9 Summary of evidence by status

<!-- source: results/v7/summary.txt; results/lowdata/summary.txt; results/lowdata_v2/summary.txt; results/lowdata_v2/matched_coverage.txt; results/lowdata_v2/feature_learning_curve.txt; docs/prereg_lowdata_v3.md; results/lowdata_v3/summary.txt; results/lowdata_v3/validity_resample.txt; docs/theory_evt.md -->
| Result (chronological within the low-data sequence) | Status | Outcome |
|---|---|---|
| v7 system comparison, fields 20–49 | exploratory (used for method refinement) | CE variants dominate certified baselines on the same stack, two exceptions |
| v8 confirmatory system comparison, fields 50–79 | pre-registered | TODO (results pending) |
| Five-layer theory, $q_{0.9}$ prediction | developmental validation | −0.6% / +0.9% / +1.4% |
| E-low v1, CE-EVT (PIT) | pre-registered | claim not met in R1, R2, R3 |
| E-low v2, CE-EVT-R (ratio), claims C1, C2 | pre-registered | both met (single calibration draw) |
| E-low v2, other cells | pre-registered predictions | 5 of 6 cells vs pooled raw as predicted; R2 marginal wrong |
| E-low v2, matched coverage | post hoc | within a regime, pivots within 0.08–0.42 pp (excluding one-run CQR); C1/C2 gains mostly realised-coverage differences |
| Information limit (oracle pivot), Proposition 8 | registered to report; computed post hoc; theory prediction post hoc | R2 PAC ≤ 9.3% possible gain; observed inflations within one predicted sd |
| Feature predictors, learning curve | post hoc | theory needed when only one run per field exists |
| Mixed-fleet design probe | developmental (design of v3) | theory log error 0.047 vs 0.136 (one-run regression), 0.433 (spec × scale law) |
| E-low v3, C3 mixed fleet | pre-registered | 5 of 8 comparisons met; claim as registered not met |
| E-low v3, C4 gated 'never worse' | pre-registered | met in 1 of 6 cells; not met |
| E-low v3, C5 gate predictions | pre-registered (secondary) | 5 of 8 hits |
| Direct coverage check, both sources of randomness | pre-registered | all 26 cells pass |
| Efficiency over 4000 replicates | pre-registered as descriptive | mixed fleet: theory +2.96 / +14.69 pp vs spec × scale law +12.82 / +23.21 (marginal / PAC); within regimes tenths of a point |

*Table 19. Status of each result.*

### 6.10 Field validation on a real vehicle: TODO

> **TODO.** All results above are from simulation driven by real field boundaries, terrain and GNSS error series. Planned: (a) offline replay on the CitrusFarm RTK robot logs (123 rows; `results/real.csv`, `results/real_aci.csv` exist but are not summarised here); (b) data collection on a commercial RTK autosteer tractor with a PPK rover as ground truth, one operation on each of 20–40 fields, using fields as the exchangeable unit as in CE-EVT-R (`docs/review/q1_critique.md`); the passive logger and offline certification tools exist in the repository (commit "Feed-car certification tools"). In particular, the relation between headland-probe XTE and pass-to-pass error must be checked on real data.

---

## 7. Discussion

### 7.1 The guarantee holds; efficiency is a separate question

Proposition 5 guarantees coverage for any field-measurable scale, whatever the theory's accuracy. The pre-registered resampling check (Section 6.8) confirms this directly, over random field splits and redrawn historical runs, in all 26 cells, including the mixed fleet. The sub-0.9 realised marginal coverages reported along the way (0.844 in v2 R1, 0.877 in v3 R1) were the luck of one fixed set of historical runs: given those runs, the coverage of a new field is a draw from Beta($k$, $n+1-k$), and in the resampling check only 0.689–0.767 of replicates reach 0.9 under the marginal rule even though the average coverage is 0.9193–0.9295. Practitioners should be told this plainly: the marginal rule is correct on average over calibration data; a per-calibration statement needs the PAC rule. The same phenomenon explains meet rates around 0.85–0.90 for marginal methods in Table 3 (Proposition 7).

Efficiency is where the theory matters, and Proposition 8 explains where it can.

### 7.2 Where the theory pivot helps: across machine configurations and with zero data

By Proposition 8, a field-level scale can only remove **between-field** variation of the required margin $\lambda^\star_f$; what remains under even the ideal scale is the within-field tail ratio, which is the same for every field-level predictor. A pivot therefore pays off when the between-field spread of $\lambda^\star_f$ is large compared with the predictor's own error. Within one machine configuration this spread is modest (between-field sd of $\lambda_g/\lambda^\star_g$ under raw pooling 0.051–0.113; Section 6.5.4). Across configurations it is large: implement width, GNSS grade and terrain change $\lambda^\star_f$ by factors that a width or vendor-specification scale captures only to a log error of 0.388–0.433, while the theory, using the closed-loop model, attains 0.047 without run data (Table 14a). Correspondingly, in the pre-registered mixed-fleet experiment the theory pivot cut mean excess overlap from 24.80 (raw) and 33.97 (scale law) to 1.87 pp in the marginal class, and over 4000 resampled replicates it was +2.96 pp against +12.82 for spec × scale law and +29.84 for raw pooling (PAC: +14.69 vs +23.21 and +61.98).

The second advantage is that the theory needs no run data. A learned predictor can match it only when trained on oracle targets from hundreds of runs per field; trained on the one run per field that the low-data setting provides, its log error at the full training pool was 0.095 (R1), 0.049 (R2) and 0.206 (R3) within regimes and 0.136 across configurations, against 0.029, 0.029, 0.056 and 0.047 for the theory (Tables 14, 14a). A learned, configuration-aware scale (CQR) was the strongest comparator in the mixed fleet and the theory's advantage over it was significant only in the marginal class (40.9%; PAC 12.3%, Holm p 0.0648).

We do not claim that the method is best in every cell. Against spec × scale law in the mixed fleet the mean gains were large but not significant, and the registered C3 claim, which required every comparator in both classes, was not met.

### 7.3 Where it cannot help: within one configuration

Within one regime all field-level pivots, including the ideal one, are at or near the information limit of Proposition 8. At matched coverage they differ by tenths of a percentage point (E-low v2: per-cell spreads of 0.08–0.42 pp, excluding the one-run-trained CQR, Table 11a; E-low v3: raw, scale-law and theory pivots within 0.17 pp except R3 marginal, Table 17; resampling: tenths of a point, Table 18). Four observations follow.

*The v2 gains were mostly coverage differences.* The registered claims C1 and C2 were met as pre-registered, but at matched coverage the theory's lead over raw pooling was +0.06 vs +0.41 pp (C1) and +0.46 vs +0.66 pp (C2). The large relative gains came from differences in realised coverage at the single calibration draw (raw pooling covered 0.948 vs 0.914 in C1 and 0.909 vs 0.885 in C2).

*No pivot choice can be made reliably from training data.* The gated variant CE-EVT-R-G was designed to fall back to a classical pivot where the theory would not help; it met its 'never worse' claim in 1 of 6 cells, and its gate mispredicted the direction of the theory's gain in three of six same-regime cells. With true efficiency differences of tenths of a point, both the gate's training proxy and the test comparison with 15 fields and one historical run each are dominated by noise, and the 'best' comparator on the test fields is partly selected by chance (in R1 marginal it was an invalid method).

*PAC margins are set by run-to-run randomness.* The PAC rule with $n\approx25$–$30$ takes essentially the maximum normalised score. The theory reproduces the resulting ideal inflations (predicted 1.30, 1.26, 1.85 vs observed 1.018, 1.207, 1.645; Section 5.5; a post hoc analysis), and R3 (DGPS) has the heaviest within-field tail. Only more runs per field or more calibration fields reduce the PAC margin; a better pivot cannot.

*Theory accuracy in the extreme tail.* The tail is very sensitive to moment errors (Section 6.4). The ratio pivot uses the theory only at the $(1-\varepsilon)$ quantile, where it is accurate; the PIT pivot of E-low v1 used it deeper in the tail and inherited the amplification of Proposition 6.

### 7.4 Limitations

1. **Simulation.** All quantitative results are from a closed-loop simulator; data are real (field boundaries, DEM, CORS GNSS) but execution is simulated. CORS antennas are static, so RTK errors are a lower bound on vehicle errors. The relation between probe-line XTE and pass-to-pass error has not been verified on a vehicle.
2. **Transfer assumptions.** Deploying a plan other than the reference plan relies on Theorem 2 or the closed-form $\kappa$ of Theorem 5; only the assumption-free CE row avoids this. The GNSS term of $\Delta$ requires a modulus of continuity of the error series, which may be large under DGPS.
3. **Theory assumptions.** L1 assumes a linear operating regime, extended by quasi-linearisation and describing functions; the leaky-integrator model is an approximation bracketed by a safe upper bound. Assumption A2 was withdrawn; L3 now rests only on the independence of non-adjacent pass pairs (Bonferroni sandwich, Theorem 4), whose bound is loose when the per-pair exceedance probabilities are not small. The Gumbel law (L5) is asymptotic while real fields have 10–150 pass pairs.
4. **Exchangeability of fields.** CE-EVT-R assumes calibration and target fields are drawn from one population. That population may mix machine configurations, as in the mixed-fleet experiments, provided each configuration is represented in the calibration pool; it does not cover a new field type or a configuration absent from the pool.
5. **Small test sets for efficiency.** Excess overlap at one calibration draw mixes efficiency with realised-coverage noise; the matched-coverage comparisons that separate the two are post hoc (v2) or secondary (v3). With 15 test fields per regime, within-regime efficiency differences of tenths of a point are not resolvable.
6. **Curve-grid floor.** In E-low v3 and the resampling check, coverage and overlap are read from per-field margin curves; deployments below the lowest grid point (frequent for raw, scale-law and CQR pivots in the mixed fleet) are read at that point.
7. **Comparability of main and secondary cost metrics.** The main-area overlap does not charge swath extending into the headland; we therefore also define applied overlap. A margin-maximising variant that keeps the pass count was withdrawn because it shifts overlap into the main area (e.g. one field: 8.1% to 13.9% main-area overlap).
8. **Confirmatory system comparison pending** (Section 6.3), and no real-vehicle validation yet (Section 6.10).

### 7.5 Practical guidance

- Replace a fixed vendor overlap by a certified margin: under RTK, twice the nominal pass-to-pass accuracy left a gap on essentially every run in our simulations (P(no miss) 0.000), and under DGPS on more than half of the runs (0.410–0.453).
- With ≥ 22 recorded operations on a field (or ≥ 9 for a marginal guarantee), use CE+ with the reference plan from training fields; choose PAC when a per-calibration guarantee is required.
- With many fields but one or two operations each, use cross-field conformal calibration; the coverage guarantee holds for any field-level scale. When the fields are worked by different machine configurations (widths, GNSS grades), use the theory pivot: configuration-blind pooled margins cost an order of magnitude more overlap, and a configuration-aware learned scale needs training data and was less efficient under the marginal rule. Within one configuration, the theory, the scale law and raw pooling are equally good to within tenths of a point at matched coverage; choose the simplest.
- The theory predictor takes seconds to a few minutes per field on one core (16–353 s in our runs) and is computed once, offline.
- Record the exact run score (covering radius per section) rather than per-pair or pointwise errors; it is the tightest valid score.
- Calibrate on a plan with at least as many passes as will be deployed; do not calibrate on the zero-margin nominal plan.

---

## 8. Conclusion

We cast coverage planning under execution uncertainty as a chance constraint on the missed area of a random set and showed that it reduces exactly to a scalar run score, the covering radius of the executed passes. Calibrating this score with conformal prediction on a dominating reference plan yields finite-sample, distribution-free zero-miss certificates; the score is the smallest valid one, and the effect of the plan on the error distribution is bounded multiplicatively. A five-layer extreme-value theory derived from the closed-loop vehicle model predicts the required margin from controller parameters and terrain to within about 1.4% without calibration runs. Used only as a pivot for cross-field conformal calibration, it certifies fields with no operation history; the guarantee does not depend on the theory's accuracy and was confirmed directly, over random field splits and redrawn historical runs, in all 26 pre-registered cells. A sequence of three pre-registered experiments locates the theory's value. The first failed for identified reasons; the second met both registered claims, but a post hoc matched-coverage analysis showed those gains to be mostly differences in realised coverage; the third met 5 of 8 comparisons on a mixed fleet and failed its 'never worse' claim. Within one machine configuration all field-level pivots sit at the information limit of Proposition 8 and differ by tenths of a percentage point; across configurations, and as a predictor that needs no run data, the theory is decisively better than configuration-blind scales and more accurate than learned predictors trained on one run per field (log error 0.047 vs 0.136), although its efficiency advantage over a configuration-aware learned scale was significant only for the marginal rule. Confirmatory system-level results and field validation on a real vehicle are pending.

---

## Data and code availability

Code, pre-registrations (with git timestamps) and raw results are in the project repository (`experiments/`, `scripts/`, `docs/prereg_lowdata*.md`, `docs/prereg_validity.md`, `results/`). TODO: archive with DOI; consider third-party registration (e.g. OSF) as noted in `docs/theory_v8.md` §7.

---

## References

*Entries verified against publisher, proceedings or repository records (October 2026). Remaining markers: [NOT FOUND] = the cited work could not be located; [CHECK] = a detail still to be confirmed.*

- Angelopoulos, A.N., Bates, S., Candès, E.J., Jordan, M.I., Lei, L., 2025. Learn then test: calibrating predictive algorithms to achieve risk control. Ann. Appl. Stat. 19(2), 1641–1662. https://doi.org/10.1214/24-AOAS1998
- Angelopoulos, A.N., Bates, S., Fisch, A., Lei, L., Schuster, T., 2024. Conformal risk control. In: The Twelfth International Conference on Learning Representations (ICLR 2024). arXiv:2208.02814.
- Azaïs, J.-M., Wschebor, M., 2009. Level Sets and Extrema of Random Processes and Fields. John Wiley & Sons, Hoboken, NJ. https://doi.org/10.1002/9780470434642
- Barber, R.F., Candès, E.J., Ramdas, A., Tibshirani, R.J., 2023. Conformal prediction beyond exchangeability. Ann. Stat. 51(2), 816–845. https://doi.org/10.1214/23-AOS2276
- Booton, R.C., 1954. Nonlinear control systems with random inputs. IRE Trans. Circuit Theory CT-1(1), 9–18.
- Campi, M.C., Garatti, S., 2008. The exact feasibility of randomized solutions of uncertain convex programs. SIAM J. Optim. 19(3), 1211–1230. https://doi.org/10.1137/07069821X
- Diquigiovanni, J., Fontana, M., Vantini, S., 2022. Conformal prediction bands for multivariate functional data. J. Multivar. Anal. 189, 104879. https://doi.org/10.1016/j.jmva.2021.104879
- Dunn, R., Wasserman, L., Ramdas, A., 2023. Distribution-free prediction sets for two-layer hierarchical models. J. Am. Stat. Assoc. 118(544), 2491–2502. https://doi.org/10.1080/01621459.2022.2060112
- European Space Agency, 2021. Copernicus Global Digital Elevation Model, GLO-30 Public (2021 release). Distributed via the AWS Open Data Registry (bucket copernicus-dem-30m). https://doi.org/10.5270/ESA-c5d3d65
- Everett, T. (rtklibexplorer), n.d. RTKLIB demo5: a fork of RTKLIB optimised for low-cost receivers. https://github.com/rtklibexplorer/RTKLIB (rnx2rtkp built from the repository in October 2026; the exact commit was not recorded).
- FAO, 2025. Pesticides use and trade – 1990–2023. FAOSTAT Analytical Briefs, No. 109. Food and Agriculture Organization of the United Nations, Rome. https://www.fao.org/statistics/highlights-archive/highlights-detail/pesticides-use-and-trade-1990-2023/en
- Galceran, E., Carreras, M., 2013. A survey on coverage path planning for robotics. Robot. Auton. Syst. 61(12), 1258–1276. https://doi.org/10.1016/j.robot.2013.09.004
- Global Market Insights, 2026. Autonomous Tractors Market report (forecast 2026–2035). Global Market Insights Inc. https://www.gminsights.com/industry-analysis/autonomous-tractors-market
- Hall, P., 1979. On the rate of convergence of normal extremes. J. Appl. Probab. 16(2), 433–439. https://doi.org/10.2307/3212912
- Hameed, I.A., la Cour-Harbo, A., Osen, O.L., 2016. Side-to-side 3D coverage path planning approach for agricultural robots to minimize skip/overlap areas between swaths. Robot. Auton. Syst. 76, 36–45.
- Hewing, L., Kabzan, J., Zeilinger, M.N., 2020. Cautious model predictive control using Gaussian process regression. IEEE Trans. Control Syst. Technol. 28(6), 2736–2743. https://doi.org/10.1109/TCST.2019.2949757
- Höffmann, M., Patel, S., Büskens, C., 2024. Optimal guidance track generation for precision agriculture: a review of coverage path planning techniques. J. Field Robot. 41(3), 823–844. https://doi.org/10.1002/rob.22286
- Kazakov, I.E., 1956. Approximate probability analysis of the operational precision of essentially nonlinear feedback control systems. Autom. Remote Control 17, 423–450.
- Leadbetter, M.R., Lindgren, G., Rootzén, H., 1983. Extremes and Related Properties of Random Sequences and Processes. Springer Series in Statistics. Springer, New York. https://doi.org/10.1007/978-1-4612-5449-2
- Lei, J., Rinaldo, A., Wasserman, L., 2015. A conformal prediction approach to explore functional data. Ann. Math. Artif. Intell. 74, 29–43. https://doi.org/10.1007/s10472-013-9366-6
- Lenain, R., Thuilot, B., Cariou, C., Martinet, P., 2006. High accuracy path tracking for vehicles in presence of sliding: application to farm vehicle automatic guidance for agricultural tasks. Auton. Robots 21(1), 79–97. https://doi.org/10.1007/s10514-006-7806-4
- Li, W.V., Shao, Q.-M., 2002. A normal comparison inequality and its applications. Probab. Theory Relat. Fields 122, 494–508. https://doi.org/10.1007/s004400100176
- Lindemann, L., Cleaveland, M., Shim, G., Pappas, G.J., 2023. Safe planning in dynamic environments using conformal prediction. IEEE Robot. Autom. Lett. 8(8), 5116–5123. https://doi.org/10.1109/LRA.2023.3292071
- Mayne, D.Q., Seron, M.M., Raković, S.V., 2005. Robust model predictive control of constrained linear systems with bounded disturbances. Automatica 41(2), 219–224. https://doi.org/10.1016/j.automatica.2004.08.019
- Mier, G., Fennema, R., Valente, J., de Bruin, S., 2025. Continuous curvature path planning for headland coverage with agricultural robots. J. Field Robot. 42(3), 641–656. https://doi.org/10.1002/rob.22489
- Mier, G., Valente, J., de Bruin, S., 2023. Fields2Cover: an open-source coverage path planning library for unmanned agricultural vehicles. IEEE Robot. Autom. Lett. 8(4), 2166–2172. https://doi.org/10.1109/LRA.2023.3248439
- Mohajerin Esfahani, P., Kuhn, D., 2018. Data-driven distributionally robust optimization using the Wasserstein metric: performance guarantees and tractable reformulations. Math. Program. 171(1–2), 115–166. https://doi.org/10.1007/s10107-017-1172-1
- NOAA Continuously Operating Reference Stations (CORS) network, AWS Open Data (noaa-cors-pds).
- Pannocchia, G., Rawlings, J.B., 2003. Disturbance models for offset-free model-predictive control. AIChE J. 49(2), 426–437. https://doi.org/10.1002/aic.690490213
- Perdomo, J., Zrnic, T., Mendler-Dünner, C., Hardt, M., 2020. Performative prediction. In: Proceedings of the 37th International Conference on Machine Learning (ICML 2020). Proc. Mach. Learn. Res. 119, 7599–7609. https://proceedings.mlr.press/v119/perdomo20a.html
- Piterbarg, V.I., 1996. Asymptotic Methods in the Theory of Gaussian Processes and Fields. Translations of Mathematical Monographs, vol. 148. American Mathematical Society, Providence, RI.
- Rice, S.O., 1944. Mathematical analysis of random noise. Bell Syst. Tech. J. 23(3), 282–332. https://doi.org/10.1002/j.1538-7305.1944.tb00874.x
- Romano, Y., Patterson, E., Candès, E., 2019. Conformalized quantile regression. In: Advances in Neural Information Processing Systems 32 (NeurIPS 2019), pp. 3543–3553.
- Sun, J., Jiang, Y., Qiu, J., Nobel, P.T., Kochenderfer, M., Schwager, M., 2023. Conformal prediction for uncertainty-aware planning with diffusion dynamics model. In: Advances in Neural Information Processing Systems 36 (NeurIPS 2023), pp. 80324–80337.
- Takasu, T., Yasuda, A., 2009. Development of the low-cost RTK-GPS receiver with an open source program package RTKLIB. In: International Symposium on GPS/GNSS, International Convention Center Jeju, Korea.
- Tang, H., Zhang, T., Niu, X., Fan, J., Liu, J., 2022. Impact of the Earth rotation compensation on MEMS-IMU preintegration of factor graph optimization. IEEE Sens. J. 22(17), 17194–17204. https://doi.org/10.1109/JSEN.2022.3192552 (vehicle GNSS/INS data: https://github.com/i2Nav-WHU/awesome-gins-datasets)
- Teng, H., Wang, Y., Song, X., Karydis, K., 2023. Multimodal dataset for localization, mapping and crop monitoring in citrus tree farms. In: Advances in Visual Computing (ISVC 2023), Lecture Notes in Computer Science. Springer, Cham, pp. 571–582. https://doi.org/10.1007/978-3-031-47969-4_44
- Tibshirani, R.J., Barber, R.F., Candès, E.J., Ramdas, A., 2019. Conformal prediction under covariate shift. In: Advances in Neural Information Processing Systems 32 (NeurIPS 2019), pp. 2530–2540.
- Vovk, V., 2012. Conditional validity of inductive conformal predictors. In: Proceedings of the Asian Conference on Machine Learning (ACML 2012). Proc. Mach. Learn. Res. 25, 475–490. https://proceedings.mlr.press/v25/vovk12.html
- Wang, H., Ning, C., 2025. Conformal prediction in the loop: a feedback-based uncertainty model for trajectory optimization. In: Advances in Neural Information Processing Systems 38 (NeurIPS 2025). arXiv:2510.16376.
- Wu, C., Li, D., Zhang, X., Pan, J., Quan, L., Yang, L., Yang, W., Ma, Q., Su, C., Zhai, W., 2023. China's agricultural machinery operation big data system. Comput. Electron. Agric. 205, 107594. https://doi.org/10.1016/j.compag.2022.107594
- Zhang, X., Davidson, E.A., Mauzerall, D.L., Searchinger, T.D., Dumas, P., Shen, Y., 2015. Managing nitrogen for sustainable development. Nature 528(7580), 51–59. https://doi.org/10.1038/nature15743
- Zhang, X., Zou, T., Lassaletta, L., Mueller, N.D., Tubiello, F.N., et al., 2021. Quantification of global and national nitrogen budgets for crop production. Nat. Food 2, 529–540. https://doi.org/10.1038/s43016-021-00318-5
- Zhao, Y., Yu, X., Sesia, M., Deshmukh, J.V., Lindemann, L., 2024. Conformal predictive programming for chance constrained optimization. arXiv:2402.07407.

---

## Appendix A. Proofs

Proofs are reproduced from the internal theory notes; items marked "sketch" are not complete in those notes.

**A.1 Lemma 1.** At a section, the executed footprints are equal-length intervals $[c_i-w/2,c_i+w/2]$. The chord $[\ell,u]$ is covered iff the left end is within $w/2$ of a centre, the right end likewise, and every gap between consecutive sorted centres whose midpoint lies in the chord has half-length at most $w/2$; this is the covering radius condition. Writing every term as a difference of footprint edges gives $S$; $M=0$ iff the maximum over sections of $r^\star-w/2$ is $\le0$, i.e. $S\le\lambda_{\rm ref}$. Numerically verified (`core.exact_scores`, `core.exact_pair_scores`).

**A.2 Lemma 2.** If $S'(e)<\bar\lambda(e)$, take $\lambda=S'(e)$; validity gives $M(\lambda,e)=0$, so $\bar\lambda(e)\le\lambda<\bar\lambda(e)$, a contradiction. $\square$

**A.3 Theorem 1.** Under shift-equivariant transfer, the needed erosion of any plan in the family equals the covering-radius excess measured at the reference plan, so $S^\star=\bar\lambda$; combine with Lemma 2. Corollary 1 follows because order statistics are monotone under pointwise order: $S^\star_i\le S'_i$ for all $i$ implies $S^\star_{(k)}\le S'_{(k)}$ for all $k$. $\square$

**A.4 Lemma 3.** If run $i$ has $\max_jS'_{ij}>\max_jq_j$, then some $j$ has $S'_{ij}>\max_{j'}q_{j'}\ge q_j$; count over runs and constraints; each $q_j$ at level $\varepsilon/J$ admits at most $n\varepsilon/J$ exceedances. $\square$

**A.5 Theorem 2.** *Lemma (coupling).* If $J(\pi_1)\subseteq J(\pi_0)$ then $\{U_{\pi_1}>t\}\subseteq\{U_{\pi_0}>t\}\cup\bigcup_{j\in J(\pi_1)}\{t-h_j<T_j^{(0)}\le t\}$: if $T_j^{(1)}>t$ then either $T_j^{(0)}>t$ or $t\ge T_j^{(0)}\ge T_j^{(1)}-h_j>t-h_j$. *Lemma (hazard).* $P(t-h<T\le t)=S(t-h)-S(t)\le(e^{hH}-1)S(t)$, since $S(t-h)=S(t)\exp(\int_{t-h}^t\text{hazard})$. *Lemma (extremal index identity).* $\sum_jP(T_j^{(0)}>t)=\mathbb E N_t=(1-F_{\pi_0}(t))/\theta_t$, because $\mathbb E N_t=\mathbb E[N_t\mid N_t\ge1]P(N_t\ge1)$. Combining the three gives the bound. The deployed guarantee uses independence of the test run from calibration and $\mathbb E[1-F_{\pi_0}(\hat\lambda)]\le\varepsilon$ (marginal) or $1-F_{\pi_0}(\hat\lambda)\le\varepsilon$ with probability $\ge1-\delta$ (PAC). $\square$

**A.6 Proposition 2.** $\{U_{\pi_1}\le t<U_{\pi_0}\}$ implies an extra pair exceeds $t$; union bound and the extremal-index identity with identically distributed pairs give $a/|J(\pi_0)|\cdot(1-F_{\pi_0})/\theta_t$. $\square$

**A.7 Proposition 4.** Linear system with Gaussian input gives Gaussian state; per-pass innovations are independent and passes interact only through deterministic functions of $C$; $\rho(A)<1$ (stable LQR closed loop) gives a unique positive semidefinite Lyapunov solution; $de/dx=\psi+\beta$ gives $\lambda_2$. The gap process inherits Gaussianity with halved variances because the two passes are independent given $C$. $\square$

**A.8 Theorem 3.** $\{\sup Z>t\}\subseteq\{Z(0)>t\}\cup\{N_t^+\ge1\}$, so $\mu_j\le P(Z(0)>t)+\mathbb E N_t^+$. For a $C^1$ Gaussian process, the Kac–Rice formula (Azaïs and Wschebor, 2009, Thm 3.4) gives $\mathbb E N_t^+=\int\mathbb E[(Z')^+\mid Z=t]\,p_{Z(x)}(t)\,dx$; conditionally on $Z(x)=t$, $Z'(x)$ is Gaussian with mean $\tilde m'$ and sd $\tilde\sigma'$, so $\mathbb E[(Z')^+\mid Z=t]=\tilde\sigma'\Psi(\tilde m'/\tilde\sigma')$. The discrete version follows from $\{\max_iZ_i>t\}\subseteq\{Z_0>t\}\cup\bigcup_i\{Z_i\le t<Z_{i+1}\}$. Tail exactness (ratio → 1) is the standard Rice-method result (Piterbarg, 1996; Azaïs and Wschebor, 2009, Ch. 4). $\square$

**A.9 Theorem 4.** First- and second-order Bonferroni inequalities give $1-M\le P(\cap_jA_j^c\mid C)\le1-M+\sum_{i<j}P(A_i\cap A_j\mid C)$; non-adjacent pairs are independent given $C$ (Proposition 1.1 of the theory notes), so $P(A_i\cap A_j\mid C)=\mu_i\mu_j$ for $|i-j|\ge2$, and $p_j\le\min(\mu_j,\mu_{j+1})$. Expanding $\prod_j(1-\mu_j)$ as an alternating sum with decreasing terms gives $1-M\le\prod_j(1-\mu_j)\le1-M+\sum_{i<j}\mu_i\mu_j$. Both quantities lie in an interval of length at most $\max(\sum_{i<j}\mu_i\mu_j,\ \sum_{|i-j|\ge2}\mu_i\mu_j+\sum_jp_j)\le M^2/2+\sum_j\min(\mu_j,\mu_{j+1})$. $\square$

**A.10 Theorem 5.** Integrate Theorem 4 over $C$. For the transfer bound: a mean shift $\Delta_j$ is equivalent to a threshold shift, $\mu_j^{(1)}(t)\le\mu_j^{(0)}(t-\Delta_j)$; by the Gaussian density identity $\varphi(\tfrac{t-\Delta-m}{s})=\varphi(\tfrac{t-m}{s})\exp(\tfrac{(t-m)\Delta}{s^2}-\tfrac{\Delta^2}{2s^2})$ the Rice bound scales by at most $\kappa$, so $M_{\pi_1}\le\kappa M_{\pi_0}$ (extra pairs only in $\pi_0$); for $\kappa\ge1$, $1-e^{-\kappa M}\le\kappa(1-e^{-M})$ by concavity; take expectations and absorb the product/exponential difference and Rice-ratio error into the $\mathbb E\mu_{\max}$ term. The extremal-index expression follows from Jensen's inequality for the concave $1-e^{-x}$. $\square$ (sketch for the constant 5)

**A.11 Theorem 6 (sketch).** Given $C$, Theorems 3–4 reduce $P(U\le t\mid C)$ to a product of stationary Gaussian sup-exceedances over total effective length $N$; the Cramér–Leadbetter theorem for maxima of continuous-parameter stationary Gaussian processes (Leadbetter, Lindgren and Rootzén, 1983, Thm 8.2.7) gives the Gumbel limit; inverting at $1-\varepsilon$ gives the scale law. Cross-field validity is the split-conformal lemma on exchangeable normalised scores (one per field); the $O(1/\log N)$ accuracy uses Hall (1979).

**A.12 Proposition 5.** See Section 5.4.

---

## Appendix B. Notes for the authors (remove before submission)

- Numbering map to internal notes: Theorem 1 = `theory_v8` Theorem 3; Theorem 2 = `theory_transfer` Theorem 5; Proposition 3 = `theory_v8` Proposition B; Proposition 4 = `theory_evt` Prop. 1.1; Theorem 3 = `theory_evt` Thms 2.1/2.3; Theorem 4 = `theory_evt` Thm 3.2′; Theorem 5 = `theory_evt` Thms 4.1/4.3; Theorem 6 = `theory_evt` Thms 5.1/5.3; Proposition 7 = `theory_v8` Proposition 4. The research proposal's Theorems 3–4 (weighted conformal fixed point, conformal risk control with a monotone surrogate) are not used in this paper.
- The v8 confirmatory comparison and E-low v2 both use fields 50–79 (different questions; the v8 method choice was fixed before E-low v2). State this explicitly in the final paper.
- E-low v3 test fields 5–19 also appeared in the v3–v6 system experiments (target-field data, a different question); `docs/prereg_lowdata_v3.md` §1 states this. The resampling check (Section 6.8) reuses v2 and v3 fields with new historical-run banks.
- The commit message of the resampling check says "all 28 cells PASS"; `results/lowdata_v3/validity_resample.txt` lists 26 cells (3 regimes × 3 methods × 2 classes + mixed fleet 4 × 2). The paper uses 26.

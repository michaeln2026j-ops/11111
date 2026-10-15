# Supplementary Material

**Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations**

<!-- Companion to docs/paper/manuscript.md. Material moved out of the main text of docs/paper/draft.md (the archive). Every number is copied from a file in this repository; each table carries an HTML comment naming its source. Theorem, proposition and figure numbers refer to the manuscript. -->

Contents

- Appendix A. Proofs
- Appendix B. Theory details (L1 refinements, field-edge terms, pivot sensitivity, layer validation)
- Appendix C. Experimental details (simulator, field splits, baselines, CE+)
- Appendix D. Full experimental tables (v7, v8 secondary metric, E-low v1–v3, matched coverage, information limit, feature predictors, resampling check, runtime, status of every result)
- Appendix E. Notes for the authors (remove before submission)

---

## Appendix A. Proofs

Items marked "sketch" are not complete proofs.

**A.1 Lemma 1 (exact covering radius).** At a section, the executed footprints are equal-length intervals $[c_i-w/2,c_i+w/2]$. The chord $[\ell,u]$ is covered iff the left end is within $w/2$ of a centre, the right end likewise, and every gap between consecutive sorted centres whose midpoint lies in the chord has half-length at most $w/2$; this is the covering-radius condition. Writing every term as a difference of footprint edges gives $S$; $M=0$ iff the maximum over sections of $r^\star-w/2$ is $\le0$, i.e. $S\le\lambda_\mathrm{ref}$. Verified numerically against exact interval union on the 1 m grid. $\square$

**A.2 Greedy planner.** Under a strictly monotone effective half-width, placing each pass as far as the gap condition allows from the previous one uses the fewest passes among all placements that satisfy the gap condition (standard exchange argument for interval covering: any feasible placement can be shifted pass by pass to the greedy one without increasing the count).

**A.3 Lemma 2.** If $S'(e)<\bar\lambda(e)$, take $\lambda=S'(e)$; validity gives $M(\lambda,e)=0$, so $\bar\lambda(e)\le\lambda<\bar\lambda(e)$, a contradiction. $\square$

**A.4 Theorem 1 and Corollary 1.** Under shift-equivariant transfer, the needed erosion of any plan in the family equals the covering-radius excess measured at the reference plan, so $S^\star=\bar\lambda$; combine with Lemma 2. Corollary 1: order statistics are monotone under pointwise order, so $S^\star_i\le S'_i$ for all $i$ implies $S^\star_{(k)}\le S'_{(k)}$ for all $k$; since $K(\lambda)$ is non-decreasing, the deployed pass count is no larger. $\square$

*Numerical check.* On 6 fields × 200 runs in three regimes: $\{M>0\}=\{S^\star>\lambda\}$ on 100% of runs; $S^\star\le S_\mathrm{pair}$ on 100% of runs; the pair score never declared a missing run miss-free; the gap between the two at the 90% quantile was 0.4–1.3 cm under RTK and 5.5–9.2 cm under DGPS.

**A.5 Lemma 3.** If run $i$ has $\max_jS'_{ij}>\max_jq_j$, then some $j$ has $S'_{ij}>\max_{j'}q_{j'}\ge q_j$. Count over runs and constraints: each $q_j$ at level $\varepsilon/J$ admits at most $n\varepsilon/J$ exceedances, so $\#\{i:\max_jS'_{ij}>\max_jq_j\}\le\sum_j\#\{i:S'_{ij}>q_j\}\le n\varepsilon$. $\square$

**A.6 Proposition 1.** For any fixed run, the maximum over the pass pairs of $\pi(\hat\lambda)$ dominates the maximum over the (fewer) pass pairs of $\pi(0)$ under the natural pairing; a quantile calibrated on the smaller maximum therefore does not bound the larger one, and no distribution-free statement transfers. $\square$

**A.7 Theorem 2 (multiplicative transfer).** *Coupling lemma.* If $J(\pi_1)\subseteq J(\pi_0)$ then $\{U_{\pi_1}>t\}\subseteq\{U_{\pi_0}>t\}\cup\bigcup_{j\in J(\pi_1)}\{t-h_j<T_j^{(0)}\le t\}$: if $T_j^{(1)}>t$ then either $T_j^{(0)}>t$ or $t\ge T_j^{(0)}\ge T_j^{(1)}-h_j>t-h_j$. *Hazard lemma.* $P(t-h<T\le t)=\bar F(t-h)-\bar F(t)\le(e^{hH}-1)\bar F(t)$, since $\bar F(t-h)=\bar F(t)\exp(\int_{t-h}^t\text{hazard})$. *Extremal-index identity.* $\sum_jP(T_j^{(0)}>t)=\mathbb E N_t=(1-F_{\pi_0}(t))/\theta_t$, because $\mathbb E N_t=\mathbb E[N_t\mid N_t\ge1]P(N_t\ge1)$. Combining the three gives the bound. The deployed guarantee uses independence of the test run from calibration and $\mathbb E[1-F_{\pi_0}(\hat\lambda)]\le\varepsilon$ (marginal) or $1-F_{\pi_0}(\hat\lambda)\le\varepsilon$ with probability at least $1-\delta$ (PAC). $\square$

**A.8 Proposition 2.** $\{U_{\pi_1}\le t<U_{\pi_0}\}$ implies that an extra reference pair exceeds $t$; a union bound and the extremal-index identity with identically distributed pairs give at most $a/|J(\pi_0)|\cdot(1-F_{\pi_0})/\theta_t$. $\square$

**A.9 Proposition 3.** The selected normalisation $\hat\sigma$ is a function of training fields only and hence independent of calibration and test runs. Conditionally on $\hat\sigma$, the pairs $(S_i,z_i)$ of calibration and test runs are exchangeable, so $S_i/\hat\sigma(z_i)$ are exchangeable and the split-conformal lemma applies. Corollary 1's pointwise dominance holds only for constant normalisation. $\square$

**A.10 Proposition 4.** A linear system with Gaussian input has a Gaussian state; per-pass innovations are independent and passes interact only through deterministic functions of $C$; $\rho(A)<1$ (stable closed loop) gives a unique positive semidefinite solution of the Lyapunov equation; $de/dx=\psi+\beta$ gives $\lambda_2=P_{\psi\psi}+2P_{\psi\beta}+P_{\beta\beta}$. The gap process inherits Gaussianity with halved variances because the two passes are independent given $C$. $\square$

**A.11 Theorem 3(a) (Kac–Rice).** $\{\sup Z>t\}\subseteq\{Z(0)>t\}\cup\{N_t^+\ge1\}$, so $\mu_j\le P(Z(0)>t)+\mathbb E N_t^+$. For a $C^1$ Gaussian process, the Kac–Rice formula (Azaïs and Wschebor, 2009, Thm 3.4) gives $\mathbb E N_t^+=\int\mathbb E[(Z')^+\mid Z=t]\,p_{Z(x)}(t)\,dx$; conditionally on $Z(x)=t$, $Z'(x)$ is Gaussian with mean $\tilde m'(x;t)=m_j'(x)+r(x)(t-m_j(x))/\sigma(x)^2$ and variance $\tilde\sigma'(x)^2=\sigma'(x)^2-r(x)^2/\sigma(x)^2$, so $\mathbb E[(Z')^+\mid Z=t]=\tilde\sigma'\Psi(\tilde m'/\tilde\sigma')$. In the stationary case the bound reduces to $\bar\Phi(u)+\tfrac{L_j}{2\pi}\tfrac{s'}{s}e^{-u^2/2}$. The discrete version follows from $\{\max_iZ_i>t\}\subseteq\{Z_0>t\}\cup\bigcup_i\{Z_i\le t<Z_{i+1}\}$, each term a bivariate normal integral with the lag-1 correlation from L1. Tail exactness (ratio → 1 as $t\to\infty$) is the standard Rice-method result (Piterbarg, 1996; Azaïs and Wschebor, 2009, Ch. 4). In the development checks the continuous version was about 29% loose at the 0.9 quantile and the discrete version 0–17%. $\square$

**A.12 Theorem 3(b) (field-edge terms).** Fix $C$ and a section $x$ with chord $[\ell(x),u(x)]$, and let $b$ be one of its ends. By Lemma 1, $b$ is uncovered iff every executed footprint misses it. For a pass $k$ whose planned footprint covers $b$, the footprint at erosion threshold $t$ fails to cover $b$ iff the single-pass process $S_k$ of the manuscript exceeds $t$ (the sign of $e_k$ enters according to whether the centre lies inside or outside $b$, i.e. whether the pass must recede inward or outward to uncover the edge). Hence $\{b\text{ missed at }t\}=\bigcap_{k\ \text{covering}\ b}\{S_k>t\}$. Given $C$, the random parts of different passes are independent (Proposition 4; the GNSS error common to all passes is part of the conditional mean), so $P(b\text{ missed}\mid C)=\prod_kP(S_k>t\mid C)$. Sections covered by a single pass give a supremum exceedance of one Gaussian process, bounded by the discrete Kac–Rice bound of (a) or computed by Gaussian Monte Carlo; sections covered by two passes are combined across $x$ by a union bound over the product probabilities. The resulting edge exceedance enters L3 as a boundary pseudo-pair. $\square$

**A.13 Theorem 4 (Bonferroni sandwich).** First- and second-order Bonferroni inequalities give $1-M\le P(\cap_jA_j^c\mid C)\le1-M+\sum_{i<j}P(A_i\cap A_j\mid C)$. Non-adjacent pairs are independent given $C$, so $P(A_i\cap A_j\mid C)=\mu_i\mu_j$ for $|i-j|\ge2$, and $p_j\le\min(\mu_j,\mu_{j+1})$. Expanding $\prod_j(1-\mu_j)$ as an alternating sum with decreasing terms gives $1-M\le\prod_j(1-\mu_j)\le1-M+\sum_{i<j}\mu_i\mu_j$. Both quantities lie in $[1-M,1-M+W]$ with $W=\max(\sum_{i<j}\mu_i\mu_j,\ \sum_{|i-j|\ge2}\mu_i\mu_j+\sum_jp_j)\le M^2/2+\sum_j\min(\mu_j,\mu_{j+1})$. $\square$

*Correlation of adjacent pairs.* With $Z_j=(e_{k+1}-e_k)/2$, $Z_{j+1}=(e_{k+2}-e_{k+1})/2$, single-pass variance $\sigma^2$ and autocorrelation $r(x,x')$: $\mathrm{Cov}(Z_j(x),Z_{j+1}(x'))=-\tfrac14\sigma^2r(x,x')$, $\mathrm{Var}\,Z_j=\tfrac12\sigma^2$, hence $\rho_{xx'}=-\tfrac12r(x,x')$. Because the closed loop is under-damped ($r\approx-0.24$ at about 10 m), the correlation changes sign with lag (small positive values of about $+0.12$ appear), so neither Slepian's inequality nor a small-correlation normal comparison applies. An earlier assumption of non-negative autocovariance (A2) was withdrawn for this reason.

**A.14 Lemma 4 (mixed representation) and the extremal index.** Integrate Theorem 4 over $C$. For the extremal index, $\theta_t=(1-F_\pi(t))/\mathbb E[N_t]$ with $1-F_\pi\approx\mathbb E_C[1-e^{-M}]$ and $\mathbb E N_t=\mathbb E_C[M]$; Jensen's inequality for the concave $1-e^{-x}$ gives $\theta_t<1$ whenever $M$ varies between runs. The formula requires true $\mu_j$; replacing them by Rice upper bounds far from the tail overstates $\mathbb E M$ and understates $\theta$ without affecting $F_\pi$ (there $e^{-M}\approx0$). $\square$

**A.15 Theorem 5 (exact transfer).** Fix $C$. Because the matched pair processes of $\pi_0$ and $\pi_1$ are jointly Gaussian with the same covariance, they can be realised on one probability space as $Z^{(1)}_j=Z^{(0)}_j+(m^{(1)}_j-m^{(0)}_j)$ with a common centred part. Then $Z^{(1)}_j(x)\le Z^{(0)}_j(x)+\Delta(C)$ at every section, so $\{T^{(1)}_j>t\}\subseteq\{T^{(0)}_j>t-\Delta(C)\}$, and taking the union over $j\in J(\pi_1)\subseteq J(\pi_0)$ gives $\{U_{\pi_1}>t\}\subseteq\{U_{\pi_0}>t-\Delta(C)\}$. Take probabilities (conditional form), use $\Delta(C)\le\bar\Delta$ and monotonicity of $F_{\pi_0}$, and integrate over $C$. *Closed form for $\kappa$.* If $1-F\propto Q(u)$ near the threshold, $\log Q(u-d)-\log Q(u)=\int_{u-d}^{u}h(v)\,dv\le d\,h(u)\le d(u+1/u)$, because the Gaussian hazard $h=\varphi/Q$ is increasing (log-concavity of $Q$) and $h(u)\le u+1/u$ by the Mills-ratio inequality $Q(u)\ge\varphi(u)u/(u^2+1)$. *Deployment.* Apply the inequality at $t=\hat\lambda$ and use $\mathbb E[1-F_{\pi_0}(\hat\lambda)]\le\varepsilon$ (marginal) or the PAC event. *Mean shift.* Under A1 with integral action, $\Delta_j\le\tfrac12h_\mathrm{ant}(1-c_{\min})\sup_x|\Delta g^{(1)}_{y,j}(x)-\Delta g^{(0)}_{y,j}(x)|$, with $\Delta g_{y,j}$ the cross-slope difference of the two passes of pair $j$, plus a GNSS timing term $\sup|\varepsilon(\tau^{(1)})-\varepsilon(\tau^{(0)})|$ bounded by the modulus of continuity of the CORS error series. $\square$ (This replaces an earlier sketch that used a Gaussian density ratio with a sign error in the $\Delta^2$ term and an unproven constant.)

*Price of an inflated reference plan, exact version.* By Lemma 4, $F_{\pi_1}(t)-F_{\pi_0}(t)\le\frac{a}{|J(\pi_0)|}\mathbb E_C[Me^{-M}]+O(\cdot)$, which replaces the estimated extremal index of Proposition 2 by a computable quantity.

**A.16 Theorem 6 (sketch).** Given $C$, Theorems 3–4 reduce $P(U\le t\mid C)$ to a product of stationary Gaussian supremum exceedances over total effective length $N$; the Cramér–Leadbetter theorem for maxima of continuous-parameter stationary Gaussian processes (Leadbetter et al., 1983, Thm 8.2.7) gives the Gumbel limit; inverting at $1-\varepsilon$ gives the scale law. Normal extremes converge at rate $O(1/\log N)$ (Hall, 1979), so a scale-law-normalised score is only approximately pivotal; cross-field validity does not need pivotality (Proposition 5).

**A.17 Proposition 5.** In the manuscript.

**A.18 Proposition 7.** For $n_t=200$ test runs, a field fails the one-sided binomial test at 0.05 iff at most 172 runs are miss-free; with true coverage exactly 0.9 this has probability 0.043. Given $n=100$ calibration runs, the coverage of the marginal rule with $k=91$ is Beta(91, 10) (mean 0.901), and of the PAC rule ($\delta=0.1$, $k=95$) Beta(95, 6) (mean 0.941); integrating the binomial failure probability over these distributions gives 14.5% and 1.2%. The general upper bound for a PAC method is $\delta+\alpha=14.3\%$; 9 or more failures among 30 fields is improbable under it. $\square$

**A.19 Proposition 8.** In the manuscript. The three consequences: (i) if normalised shapes coincide, $G_f(v\lambda^\star_f)=\Gamma(v)$, then $t=\Gamma^{-1}(B)$; (ii) under the ideal scale the spread of $\lambda_g/\lambda^\star_g$ across fields is zero, and any other field-level scale only adds between-field spread without changing the distribution of $B$; (iii) excess overlap is a nonlinear (pass-count) function of $\lambda$, so a common margin can be cheaper than the ideal scale when between-field spread is small and tails are heavy. *Prediction.* Replacing $G_f$ by the theory CDFs $\hat F_f$, drawing one run per field, normalising by its own $\hat q_f$ and taking the PAC order statistic, 2000 times, gives the predicted inflations of Fig. 7.

---

## Appendix B. Theory details

### B.1 Refinements of L1 forced by failed validation checks

(a) *Observation operator.* Misses are evaluated on offsets linearly interpolated to a 1 m grid with a pass-constant weight $f_k$, so $\mathrm{Var}\,\tilde e_k=(1-f)^2v_s+f^2v_{s+1}+2f(1-f)c_s$ (exact form). An earlier stationary approximation produced a negative variance on one R3 field, which caused the E-low v1 failure in R3. Ignoring the operator overestimates variance by 2–3% and tail probability by 15–30%.

(b) *Time-varying quasi-linearisation* along the noise-free closed-loop trajectory, with Jacobians of the kinematics and terrain feedback and random-input describing functions for steering saturation and rate limits (Booton, 1954; Kazakov, 1956); covariance propagates by $P_{t+1}=A_tP_tA_t^\top+B_tB_t^\top$.

(c) *Integrator clamp.* The anti-windup clamp $|I|\le0.3$ sits about 1.6 standard deviations from zero; it is replaced by a leaky integrator whose leak rate matches the stationary variance of the truncated Gaussian (Kazakov-type energy criterion). This is a best estimate; the unclamped linear model is a safe upper bound because clamping only reduces variance. In the three test conditions of the integrator model, the true variance lay between the best estimate and the safe upper bound.

*Assumption on terrain.* The simulator samples slope by nearest neighbour on a 1 m grid; at high slip, crossing a grid boundary makes slip jump, and the conditional distribution is no longer Gaussian. The theory therefore assumes a terrain gradient that is smooth on the operating scale (A1′); changing the simulator would break comparability with existing experiments and is left to a separate validation.

### B.2 Layer-by-layer validation (developmental)

Development fields: R1 wheat 440, R2 paddy 36 (144 passes), R3 paddy 40; L5 on 8 R1 fields.

<!-- source: docs/theory_evt.md (section 6) -->
| Layer | Quantity | R1 flat RTK | R2 hilly-wet RTK | R3 DGPS |
|---|---|---|---|---|
| 1 | RMS difference, noise-free closed-loop mean vs conditional sample mean | 0.07 cm | 0.20 cm | 0.09 cm |
| 1 | Pair standard deviation, sample / predicted | 1.00 | 0.999 (5–95%: 0.989–1.015) | agrees |
| 1 | Adjacent-section covariance, sample / predicted | — | 0.993 | — |
| 3 | Product form for $P(U\le t\mid C)$ at the 0.9 quantile (predicted / true) | 0.888 / 0.900 | 0.882 / 0.900 | 0.900 / 0.900 |
| 4 | Coverage after a plan change, predicted / simulated | 0.901 / 0.899 | 0.890 / 0.885 | 0.920 / 0.922 |
| 5 | Linearity of $q_{0.9}$ in $\sqrt{2\log N}$ over 8 fields | simulated $R^2=0.989$, predicted $R^2=0.964$; per-field error 0.1–0.7 cm | — | — |

*Table S5. Layer-by-layer validation after the first round of corrections (developmental).*

<!-- source: docs/theory_evt.md (section 6.2) -->
| Regime | First version | Fix 1 (product form, time-varying L1) | Fix 2 (integrator, hybrid exact L2) | Safe upper bound |
|---|---|---|---|---|
| R1 flat RTK | 11.03 / 11.01 | 11.02 / 11.01 | 10.94 / 11.01 (−0.6%) | 11.02 |
| R2 hilly-wet RTK | 15.75 / 15.26 | 15.76 / 15.26 | 15.39 / 15.26 (+0.9%) | 15.76 |
| R3 DGPS | 36.0 / 37.3 (−3.5%) | 37.97 / 37.09 | 37.61 / 37.09 (+1.4%) | 37.97 |

*Table S5a. Required margin $q_{0.9}$ (cm), predicted / simulated, all development versions (manuscript Table 3 shows first and final versions).*

After fix 2, coverage after a plan change is predicted to within 0.007 (R3: 0.9220 vs 0.9220). The extremal index agrees in R2 (0.30 vs 0.31) but is underpredicted in R3 (0.54 vs 0.66), which does not affect $F_\pi$ (A.14). A diagnostic in the hardest condition (R2, slip gain 1.23) showed conditional marginals that are Gaussian (skewness −0.002, excess kurtosis −0.012), and a Gaussian model with *sample* moments reproduced the simulated exceedance (0.1105 vs 0.1033), while L1's moments before the integrator fix overstated it by 25%; the residual bias was in L1's moments, which the integrator model removed.

*Product form versus $e^{-M}$* at a fixed DGPS condition (true no-miss probability / $e^{-M}$ / product): 0.3000 / 0.4851 / 0.2988 at the 0.3 quantile; 0.5000 / 0.6033 / 0.4999 at 0.5; 0.9000 / 0.9048 / 0.9000 at 0.9 (source: docs/theory_evt.md §3). Per-condition diagnostic in R3 (400 conditions × 4 runs): for the conditions that miss, predicted no-miss 0.220 before and 0.028 after the correction against 0.045 observed; overall 0.919 before, 0.900 after, 0.900 observed.

### B.3 Development of the field-edge terms (post hoc)

The edge terms of Theorem 3(b) went through three versions, each checked against the empirical 0.9 quantile of 200 independent runs on the reference plan (`scripts/check_boundary.py`):

1. Taking the *lowest* covering pass as the binding one overestimated the edge contribution about twofold: when the edge lies in the overlap band of two passes, the selected pass is about to lose coverage while its neighbour still covers the edge.
2. Taking the single covering pass with the centre *nearest* to the edge still overestimated by about 14%: inside an overlap band both passes must move apart for a miss, which common-mode error rarely produces.
3. The reported version takes the product of the two single-pass probabilities in overlap bands.

Per-field results of the final version (theory without edges $q_\mathrm{old}$, with edges $q_\mathrm{new}$, simulated 0.9 quantile, all in m):

<!-- source: results/lowdata_v3/check_boundary_R3.txt -->
| R3 field | Passes | $q_\mathrm{old}$ | $q_\mathrm{new}$ | Simulated |
|---|---|---|---|---|
| 119 | 18 | 0.322 | 0.322 | 0.298 |
| 54 | 20 | 0.485 | 0.499 | 0.387 |
| 32 | 15 | 0.346 | 0.346 | 0.400 |
| 44 | 24 | 0.334 | 0.340 | 0.338 |
| 212 | 11 | 0.368 | 0.391 | 0.395 |
| 74 | 23 | 0.382 | 0.390 | 0.398 |
| 211 | 21 | 0.321 | 0.329 | 0.327 |
| 181 | 14 | 0.304 | 0.323 | 0.372 |
| 24 | 10 | 0.335 | 0.357 | 0.397 |
| 182 | 20 | 0.378 | 0.381 | 0.372 |
| 215 | 7 | 0.288 | 0.300 | 0.319 |
| 225 | 12 | 0.352 | 0.407 | 0.333 |
| 28 | 13 | 0.403 | 0.424 | 0.430 |
| 48 | 8 | 0.299 | 0.363 | 0.349 |
| 21 | 15 | 0.386 | 0.388 | 0.381 |

*Table S5b. Field-edge terms on the 15 E-low v3 R3 test fields. log($q$/sim): without edges mean −0.040, sd 0.108; with edges mean +0.008, sd 0.106. On 4 R1 fields: +0.003 / 0.048 → +0.004 / 0.048; on 4 R2 fields: +0.009 / 0.046 → +0.018 / 0.047 (results/lowdata_v3/check_boundary_R1_R2.txt). The edge terms raise the prediction most on fields with few passes (e.g. 7–13 passes), where the boundary is a larger share of the field.*

**Scope.** E-low v1–v3 and v8 pre-registered results used the theory without edge terms. Validity is unaffected, because the guarantee comes from exchangeability, not from theory accuracy; only R3 efficiency comparisons could change.

### B.4 Pivot sensitivity (Proposition 6; heuristic, motivated post hoc)

Let the theory be exact up to a scale error, $\hat F_f(t)=F_f(t/(1+\delta_f))$.

- *Ratio pivot:* $\hat q_f=(1+\delta_f)q_f$, so $V_f=S_f/((1+\delta_f)q_f)$ and $\lambda_g=(1+\delta_g)q_gv^\star$. The deployed margin is affected linearly, $\partial\lambda_g/\partial\delta_g=q_gv^\star$, and the theory is evaluated only at the $(1-\varepsilon)$ quantile, which L1–L4 predict most accurately.
- *PIT pivot:* $\lambda_g=\hat F_g^{-1}(v^\star)$ with $v^\star$ close to 1, and $\partial\lambda_g/\partial v^\star=1/\hat f_g(\lambda_g)$. In the tail $\hat f_g\to0$, so small errors in $v^\star$ (from tail errors of $\hat F_{f_i}$ on calibration fields) become large errors in $\lambda_g$. With the PAC rule at $n\approx30$, $v^\star$ is near the largest PIT value, where this amplification is strongest. A non-finite $\hat F$ is additionally sorted to the top and drives $v^\star$ to the extreme tail (observed in E-low v1, R3).

Under the corrected theory in E-low v2, R3 PAC: the PIT pivot's excess overlap was +28.38 pp against +15.25 pp for the ratio pivot (Table S8).

---

## Appendix C. Experimental details

### C.1 Simulator

Vectorised over runs, $\Delta t=0.05$ s, speed 2 m/s. Kinematics $\dot d=v\sin(\psi+\beta)$, $\dot\psi=v\tan\delta/l$; first-order steering lag $\tau=0.25$ s with 35° saturation and 30°/s rate limit; terrain slip $\beta=-0.35\,k_s\,g_\mathrm{lat}$ plus Ornstein–Uhlenbeck roughness, with $k_s$ and roughness set by per-run soil moisture; antenna height 2.6 m with roll-compensation factor $c=0.85\pm0.05$; per-run mounting bias with $\sigma=1.5$ cm; GNSS error projected on the lateral axis, with passes executed in real time order including headland turns. Controllers: pure pursuit, Stanley, LQR and LQR with integral action (LQR-I, default, designed on the delay-augmented model, with conditional-integration anti-windup); external controllers plug into the same interface.

GNSS processing: the first 30 min of each day is removed; truth is IGS20/ITRF2020 coordinates propagated to the epoch; 30 s epochs are interpolated to 1 Hz and high-frequency residuals from the i2Nav vehicle dataset (Tang et al., 2022) are added. CitrusFarm RTK robot logs (Teng et al., 2023), 123 rows, are available for offline replay (`results/real.csv`, `results/real_aci.csv`; not summarised).

### C.2 Field splits

Fields are ordered by `core.load_fields(seed=0)`. Indices 0–4: training fields (CE+ fitting, farmer tuning, reference erosion). 5–19: earlier system experiments v3–v6 (which answer a different question with target-field data) and the E-low v3 test fields; no E-low design or analysis used them before E-low v3. 20–49: v7 system comparison. 50–79: v8 confirmatory system comparison, E-low v2 test fields and the E-low v3 calibration pool (the v8 method choice was fixed before E-low v2). 80 onward: E-low v1, all exploratory analyses that led to E-low v2, and the E-low v3 training pool (gate and CQR fitting only). The resampling check (manuscript Section 6.5) reuses the v2 and v3 fields with new historical-run banks.

### C.3 Baselines

About 25 published or industry systems, each implemented as a plug-in module reviewed against the original paper or source code: vendor-specification overlap (twice the nominal pass-to-pass accuracy) and farmer-tuned global overlap (tuned once on the training fields to P(no miss) ≥ 0.9), with and without vendor terrain compensation; Fields2Cover (Mier et al., 2023), Hameed 3D terrain spacing (Hameed et al., 2016) and follow-previous-pass guidance as planners; Lenain-type slip-observer control (Lenain et al., 2006), ESO sliding-mode control and offset-free MPC (Pannocchia and Rawlings, 2003) as controllers; tube-MPC radius margin (Mayne et al., 2005); Gaussian chance constraints (pointwise, Rice extreme-value correction, model-based Monte Carlo); GP cautious margins (Hewing et al., 2020); conformal planning with union bounds (Lindemann et al., 2023); conformal predictive programming (CPP; Zhao et al., 2024); the scenario approach (PAC, $\beta=0.01$; Campi and Garatti, 2008); Wasserstein DRO-CVaR (Mohajerin Esfahani and Kuhn, 2018). PAC versions of CPP and Lindemann were added for v8. The CE layers are applied on six stacks: BCD + LQR-I, Fields2Cover, Hameed 3D, follow-previous-pass, Lenain controller and offset-free MPC.

### C.4 E-low protocols

*Common.* Stack BCD + LQR-I; $\varepsilon=\delta=0.1$; leave-one-field-out; each calibration field contributes one historical run at its reference plan ($\lambda_0$ as in CE+, from training fields only); the deployed plan is evaluated on 200 fresh runs; per-field oracle as in the system comparison.

*v1* (`docs/prereg_lowdata.md`): PIT pivot; fresh fields R1 wheat 80–139, R2 paddy 80–136, R3 paddy 80–110; $n_\mathrm{cal}=\min(30,\text{pool}-1)$; claim: in every regime CE-EVT valid and at least 10% better than the strongest valid comparator of its class.

*v2* (`docs/prereg_lowdata_v2.md`, committed before any v2 result): ratio pivot with $+\infty$ rule; corrected theory; fields 50–79 (30 per regime), $n_\mathrm{cal}=29$; scale-law normalisation as comparator. Validity: pooled P(no miss) not below the 5% quantile of Beta($k$, $n_\mathrm{cal}+1-k$) (0.798 marginal, $k=27$; 0.902 PAC). Efficiency: relative improvement $(\text{comparator}-\text{ours})/\text{comparator}$ of excess overlap; if the comparator's mean excess is ≤ 0.5 pp, a non-inferiority test (ours ≤ comparator + 0.25 pp) is used; paired one-sided Wilcoxon, Holm over regime × class × comparator, level 0.05. Claims C1 and C2 only.

*v3* (`docs/prereg_lowdata_v3.md`, committed before any computation on its test fields): test fields 5–19 (3 × 15); calibration pool the 30 v2 fields of the same regime (same-regime scenario) or all v2 fields of the three regimes (mixed fleet; 45 test fields); training pool the v1 fields (147). Methods are scale pivots with $n_\mathrm{cal}=25$: raw pooling, scale law, spec × scale law ($\mathrm{p2p}_f\sqrt{2\log N_f}$), CQR-type ridge regression of $\log S$ on field features and machine configuration (log width, log p2p) trained with one run per training field (Romano et al., 2019), CE-EVT-R, and CE-EVT-R-G, which per scenario × regime × class chooses between the theory and the best classical pivot on the training pool only (leave-one-out with 200 random calibration subsets, common factor matching proxy coverage to $1-\varepsilon$, theory chosen only if its proxy excess overlap is at least 0.1 pp below the best classical pivot). Deployments are capped at $0.8\,w/2$. Each test field has a margin → P(no miss)/overlap curve (24 geometric grid points between $0.6\lambda^\star$ and $\min(8\lambda^\star,\text{cap})$, 200 runs per point, common random numbers); each scenario × method × class is evaluated over 400 calibration subsets. Validity: mean coverage ≥ 0.89 (marginal) or a fraction ≥ 0.85 of subsets with coverage ≥ 0.9 (PAC). Efficiency: per-field mean excess overlap, one-sided paired Wilcoxon over test fields, Holm over all C3 and C4 comparisons. Curves were later extended down to $0.25\lambda^\star$ with the same seeds (`scripts/extend_curves.py`).

*Matched coverage (v2, post hoc, `scripts/matched_coverage.py`).* Each pivot family is rescaled on the E-low v2 test fields by one common factor $c$ so that pooled realised P(no miss) over the 30 test fields is exactly 0.9; $c>1$ means the pivot under-covered at the registered draw.

*Resampling check* (`docs/prereg_validity.md`): see manuscript Section 6.5.

### C.5 CE+ details

$\lambda_0=1.25\times$ the largest $(1-\varepsilon)$ score quantile over five training fields. $\sigma(z)=\max(a+bz,0.3\bar\sigma)$ is fitted on training fields after dividing each field's scores by its median, so that $\sigma$ captures run-to-run, not field-size, variation. The gate requires a leave-one-field-out saving of at least 3% of mean erosion. Deployed erosions are rounded up to a 2 mm grid. Rounding, gating and the reference plan are fixed before any calibration run on the target field.

A margin-maximising variant that keeps the pass count was withdrawn because it shifts overlap into the main area (one field: 8.1% to 13.9% main-area overlap).

---

## Appendix D. Full experimental tables

### D.1 v7 system comparison (exploratory; fields 20–49)

The v7 results were used to diagnose and refine the method (v8 changes: training-only gating, PAC versions of CPP and Lindemann) and are therefore exploratory.

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

*Table S1. v7, R1 (rows with meet ≥ 0.5, sorted by overlap). Oracle meet rate 0.97.*

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

*Table S2. v7, R2. Oracle meet rate 0.90.*

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

*Table S3. v7, R3. Oracle meet rate 0.97. Negative regret is possible because the oracle targets exactly 0.9 per field while a method may undershoot it.*

<!-- source: results/v7/summary.txt -->
| Regime | Lowest-regret system with meet ≥ 0.9 | P | meet | overlap % | regret pp |
|---|---|---|---|---|---|
| R1 | Follow-previous-pass + Lenain ctrl + CE+ PAC | 0.946 | 0.967 | 7.471 | −1.406 |
| R2 | BCD + Lenain ctrl + CE+ | 0.907 | 0.900 | 20.301 | −5.251 |
| R3 | BCD + offset-free MPC + CE-q | 0.908 | 0.933 | 15.070 | 0.030 |

*Table S4. Best certified systems across all stacks (v7). Regret is relative to the BCD + LQR-I oracle, so stacks with better controllers can have negative regret.*

**Observations (exploratory).** Vendor-specification overlap reached a meet rate of 0.00 in all three regimes on every stack (BCD + LQR-I regret −7.07 pp in R1, −22.04 pp in R2, −7.45 pp in R3): it is cheap because it misses on almost every run. GP cautious margins without Bonferroni and pointwise Gaussian belief had meet rate 0.00 in R1 and R2; model-based MC and Rice-corrected Gaussian belief met the target on 0.43 and 0.30 of R2 fields. Within the conformal class on the same stack, every baseline with meet ≥ 0.9 was dominated (equal or higher meet rate and lower regret) by a CE variant, with two exceptions: CPP in R2 (meet 0.933, regret 0.96 pp; CE+ regret 0.003 pp at meet 0.900) and GP cautious margin with Bonferroni in R3 (meet 0.97, regret 2.00 pp; CE 2.16 pp at meet 1.00). In R3, CE-q (regret 0.409, meet 0.867) had lower regret than CE+ (0.957, meet 0.833); CE+'s R3 meet rate is at the level Proposition 7 predicts for an exactly calibrated marginal method.

### D.2 v8 secondary metric

<!-- source: results/v8/summary.txt -->
| Regime | Class | CE+ v8 | CPP | Lindemann pair-level | Reduction vs CPP / Lindemann | Holm p vs CPP / Lindemann |
|---|---|---|---|---|---|---|
| R1 | marginal | 30.05% | 31.04% | 31.46% | 3.2% / 4.5% | 0.0001 / 0.0000 |
| R1 | PAC | 30.52% | 32.45% | 34.33% | 6.0% / 11.1% | 0.0001 / 0.0000 |
| R2 | marginal | 36.54% | 37.58% | 39.22% | 2.8% / 6.8% | 0.0345 / 0.0000 |
| R2 | PAC | 39.04% | 40.17% | 55.22% | 2.8% / 29.3% | 0.0345 / 0.0000 |
| R3 | marginal | 46.29% | 50.30% | 53.74% | 8.0% / 13.9% | 0.0000 / 0.0000 |
| R3 | PAC | 48.87% | 54.79% | 68.46% | 10.8% / 28.6% | 0.0000 / 0.0000 |

*Table S22. v8 confirmatory comparison, secondary metric: applied overlap including swath reaching into the headland (Holm over 12). All comparisons met.*

v8 computation note: shards 15–44 were computed on three additional cloud machines with identical package versions (numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, shapely 2.2.0, scikit-learn 1.9.1); seeds are per field, so the split does not change any number. In R2, CE+ v8 chose constant normalisation (training-only gate), and its erosion (0.153 m) differs from CPP's (0.158 m) by only 3%, both close to the oracle (0.149 m).

### D.3 E-low v1 (pre-registered; claims not met)

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

*Table S6. E-low v1, all methods (pre-registered). R3 had 33 infeasible deployments in total; CE-EVT PAC could not deploy on any R3 field.*

<!-- source: results/lowdata/summary.txt -->
| Regime | Class | Comparator (valid, strongest) | CE-EVT excess pp | Comparator excess pp | Relative | Holm p | Claim |
|---|---|---|---|---|---|---|---|
| R1 | PAC | Pooled conformal, raw PAC | +5.35 | +3.22 | −66.3% | 1.0000 | not met |
| R2 | PAC | Pooled conformal, raw PAC | +3.98 | +3.26 | −21.9% | 1.0000 | not met |
| R3 | marginal | Pooled conformal, raw | +5.70 | +1.31 | −334.2% | 1.0000 | not met |

*Table S7. E-low v1 registered comparisons.*

**Why v1 failed (post hoc, exploratory; `docs/prereg_lowdata_v2.md` §0).** (1) The stationary approximation of the observation-operator variance gave a negative variance on one R3 field and an all-NaN predicted CDF; the NaN was ranked highest and pushed R3's PIT quantile to the extreme tail (31 PAC failures and the +5.70 pp marginal excess). (2) PIT pivot instability in the tail (B.4). (3) The registered field-clustered marginal validity test ignored that all test fields share almost the same calibration pool; given the calibration set, coverage is Beta($k$, $n+1-k$) with standard deviation about 0.05 at $n=30$, so even classical pooled conformal was judged invalid in R2 (0.869). This does not rescue v1: the efficiency claim failed in all three regimes regardless of validity. The exploratory analysis also concluded that field-level normalisation can remove only between-field differences, that the PAC rule at $n\approx30$ essentially takes the maximum, which is dominated by within-field randomness, and that an oracle normalisation could not beat the classical method in R2 PAC or R3 PAC; these conclusions were written into the v2 registration as predictions.

### D.4 E-low v2 (pre-registered; both claims met, with a post hoc caveat)

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

*Table S8. E-low v2, all methods and cells (30 test fields per regime, fields 50–79, no infeasible deployments). All methods except vendor-spec overlap passed the Beta validity check (marginal threshold 0.798, PAC 0.902). "Theory only" deploys $\hat F_g^{-1}(1-\varepsilon)$ without conformal calibration and has no guarantee; the summary file applies the marginal Beta check to it, which is not meaningful for a method without an order-statistic rule.*

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

*Table S9. E-low v2 pre-registered comparisons (excess overlap, pp; Holm over all rows). Relative improvement above 100% occurs when our excess is negative.*

<!-- source: docs/prereg_lowdata_v2.md (predictions); results/lowdata_v2/summary.txt (outcomes) -->
| Regime | Class | Predicted vs pooled raw | Observed | Predicted vs scale law | Observed |
|---|---|---|---|---|---|
| R1 | PAC | improve ≥ 10% (claim C1) | +82.6%, Holm p 0.0002 — as predicted | about equal (scale law slightly better) | +55.1%, not significant — direction not as predicted |
| R1 | marginal | no room → non-inferior | non-inferior — as predicted | non-inferior | non-inferior — as predicted |
| R2 | PAC | no improvement | +1.0%, n.s. — as predicted | no improvement | −2.0% — as predicted |
| R2 | marginal | no room → non-inferior | comparator +3.02 pp (room existed); ours worse (−74.2%) — prediction wrong | non-inferior | worse (−22.9%) — prediction wrong |
| R3 | marginal | improve ≥ 10% (claim C2) | +134.7%, Holm p 0.0012 — as predicted | improve | comparator +0.36 pp (no room); non-inferior — partly as predicted |
| R3 | PAC | no improvement | worse (−47.1%) — as predicted (no improvement) | no improvement | worse (−66.9%) — as predicted |

*Table S10. E-low v2 pre-registered predictions and outcomes.*

<!-- source: results/lowdata_v2/matched_coverage.txt -->
| Regime | Class | Raw (no pivot) | Scale law | CQR, one-run trained | Features, oracle-trained | Theory (CE-EVT-R) | Oracle (ideal) |
|---|---|---|---|---|---|---|---|
| R1 | marginal | +0.40 (c 1.019) | +0.14 (1.050) | +0.00 (1.066) | +0.12 (1.063) | +0.10 (1.086) | +0.19 (1.072) |
| R1 | PAC | +0.41 (0.906) | +0.12 (0.965) | −0.00 (1.014) | +0.08 (0.994) | +0.06 (0.984) | +0.16 (0.993) |
| R2 | marginal | −0.05 (0.913) | −0.13 (0.879) | −0.01 (0.850) | −0.07 (0.868) | −0.08 (0.860) | −0.06 (0.882) |
| R2 | PAC | −0.07 (0.814) | −0.15 (0.816) | −0.10 (0.829) | −0.10 (0.810) | −0.05 (0.817) | −0.09 (0.826) |
| R3 | marginal | +0.66 (0.973) | +0.48 (1.007) | +2.73 (1.030) | +0.42 (1.039) | +0.46 (1.049) | +0.32 (1.073) |
| R3 | PAC | +0.82 (0.671) | +0.49 (0.694) | +3.10 (0.605) | +0.40 (0.706) | +0.60 (0.586) | +0.41 (0.622) |

*Table S11. Excess overlap (pp) at matched pooled coverage 0.9 on the E-low v2 test fields, with the common factor $c$ in parentheses (post hoc). "CQR, one-run trained" is a ridge regression on field features trained with one run per training field; "features, oracle-trained" is the model of Table S13.*

Within a regime the pivots are nearly indistinguishable at matched coverage: excluding the one-run-trained CQR, all pivots, including the oracle, lie within 0.30 pp in R1 marginal, 0.35 pp in R1 PAC, 0.08–0.10 pp in R2 and 0.34–0.42 pp in R3; the theory pivot is never more than 0.20 pp from the best pivot of its cell. The registered gains shrink accordingly (C1: +0.06 vs +0.41 pp; C2: +0.46 vs +0.66 pp). A feature predictor trained on one run per field can fail badly under DGPS (+2.73 and +3.10 pp in R3). The factors $c$ show that CE-EVT-R under-covered in R1 marginal ($c=1.086$), matching its realised 0.844, and that every pivot over-covered in R2 ($c$ 0.81–0.91), matching the realised 0.95–0.98 of Table S8. Averaging over 400 calibration subsets of the v2 pool ($n_\mathrm{cal}=25$) still leaves R1 marginal coverage at 0.880 for the theory pivot and 0.889 for the scale law, because the historical runs are held fixed (resolved by the resampling check).

### D.5 Information limit and feature predictors (post hoc)

<!-- source: results/lowdata_v2/feature_pivot.txt -->
| Regime | Class | Raw (no pivot) | Scale law | Theory (CE-EVT-R) | Oracle (ideal) | Best possible relative gain over raw |
|---|---|---|---|---|---|---|
| R1 | marginal | +0.28 | −0.49 | −0.97 | −0.71 | no room |
| R1 | PAC | +1.56 | +0.61 | +0.27 | +0.24 | 84.6% |
| R2 | marginal | +3.02 | +4.28 | +5.26 | +4.22 | none (ideal worse than raw) |
| R2 | PAC | +7.51 | +7.29 | +7.44 | +6.81 | 9.3% |
| R3 | marginal | +1.10 | +0.36 | −0.38 | −0.91 | — (ideal below oracle) |
| R3 | PAC | +10.36 | +9.14 | +15.25 | +12.86 | none (ideal worse than raw) |

*Table S12. Mean excess overlap (pp) of field-level pivots on the E-low v2 fields; leave-one-field-out, $n_\mathrm{cal}=29$. The registered plan required reporting the oracle bound; the numbers come from the post hoc script `scripts/feature_pivot.py`, which reproduces the registered theory and raw rows exactly. Last column: (raw − ideal)/raw.*

- **R2 PAC is at the information limit.** Ideal normalisation reduces excess overlap by only 9.3% relative to raw pooling. The ratio $\lambda_g/\lambda^\star_g$ under the ideal pivot has standard deviation 0.000 across R2 test fields: the PAC rule picks the largest of 29 normalised scores ($k=29$, consistent with the Beta 5% bound $0.902=0.05^{1/29}$).
- **R3 PAC.** Ideal normalisation is worse than raw (+12.86 vs +10.36 pp) and the theory pivot worse still (+15.25): with DGPS, run-to-run variation dominates between-field variation.
- **R2 marginal.** Ideal normalisation is worse than raw (+4.22 vs +3.02) at the single draw; at matched coverage raw, theory and oracle differ by at most 0.03 pp. Between-field spread of $\lambda_g/\lambda^\star_g$ under raw pooling: sd 0.051 (R2), 0.088 (R1), 0.113 (R3).
- **Where the pivot helped at the registered draw** (R1 PAC, R3 marginal), the theory pivot comes close to or beats the ideal (R1 PAC 0.27 vs 0.24 pp).

<!-- source: docs/theory_limit.md (section 3) -->
| Regime | Theory tail ratio $\hat F^{-1}(0.97)/\hat F^{-1}(0.9)$ | Predicted ideal PAC margin ratio (mean ± sd) | Observed on v2 fields |
|---|---|---|---|
| R1 | 1.19 | 1.30 ± 0.35 | 1.018 |
| R2 | 1.16 | 1.26 ± 0.33 | 1.207 |
| R3 | 1.54 | 1.85 ± 0.74 | 1.645 |

*Table S12a. Information-limit prediction of Proposition 8 (post hoc; `scripts/predict_limit.py`). Underlying data of manuscript Fig. 7.*

<!-- source: results/lowdata_v2/feature_pivot.txt -->
| Regime | Train fields | Feature model train $R^2$ | corr(log q, log λ*): theory / features / scale law | log-error sd: theory / features | Excess pp marginal: features / theory | Excess pp PAC: features / theory |
|---|---|---|---|---|---|---|
| R1 | 60 | 0.92 | 0.95 / 0.98 / 0.97 | 0.029 / 0.020 | −0.66 / −0.97 | +0.16 / +0.27 |
| R2 | 57 | 0.85 | 0.80 / 0.89 / 0.88 | 0.029 / 0.021 | +4.89 / +5.26 | +7.68 / +7.44 |
| R3 | 30 | 0.58 | 0.87 / 0.70 / 0.70 | 0.056 / 0.080 | −0.23 / −0.38 | +8.73 / +15.25 |

*Table S13. Theory pivot vs a ridge regression of $\log\lambda^\star_f$ on six field features (log effective length, log area, log number of passes, mean slope, mean pass terrain feature, log lateral extent), trained on oracle targets on the E-low v1 pool (fields 80+, disjoint from the test fields) (post hoc). With oracle targets the feature model is slightly more accurate than the theory in R1 and R2; the theory is more accurate in R3.*

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

*Table S14. Standard deviation of $\log(q/\lambda^\star)$ on the 30 v2 test fields (lower is better), mean over 40 random training subsets (one subset for the full pool). Post hoc; underlying data of manuscript Fig. 6.*

### D.6 E-low v3 (pre-registered; claims partially met)

<!-- source: results/lowdata_v3/summary.txt -->
| Method | Marginal: coverage mean | P(cov ≥ 0.9) | Excess pp | Matched-cov. excess pp | PAC: coverage mean | P(cov ≥ 0.9) | Excess pp | Matched-cov. excess pp |
|---|---|---|---|---|---|---|---|---|
| Raw pooling | 0.935 | 0.83 | +24.80 | +12.89 | 0.967 | 0.98 | +54.02 | +13.47 |
| Scale law | 0.935 | 0.84 | +33.97 | +17.22 | 0.967 | 0.97 | +66.95 | +17.07 |
| Spec × scale law | 0.930 | 0.69 | +13.18 | +10.68 | 0.973 | 0.95 | +20.05 | +9.97 |
| CQR (one-run trained) | 0.931 | 0.82 | +3.16 | +1.30 | 0.963 | 0.96 | +9.01 | +2.43 |
| **CE-EVT-R** | 0.918 | 0.55 | **+1.87** | **+0.73** | 0.958 | 0.86 | **+7.91** | +2.64 |
| CE-EVT-R-G (gate chose theory) | 0.916 | 0.54 | +1.73 | +0.98 | 0.960 | 0.88 | +8.50 | +3.52 |

*Table S15. E-low v3, mixed fleet, registered reading (45 test fields from three machine configurations, 400 calibration subsets of $n_\mathrm{cal}=25$ from a pool of 90). All methods valid by the registered criteria. Deployments below the lowest point of a field's curve grid (raw 485 and 69, scale law 648 and 106, CQR 284 and 113, CE-EVT-R 1 and 0, marginal and PAC, out of 400 × 45) have their coverage and overlap read at that lowest point ($0.6\lambda^\star$), which overstates both; Table S18 removes this.*

<!-- source: results/lowdata_v3/summary.txt -->
| Claim | Scenario / cell | Comparison | Ours pp | Comparator pp | Relative | Holm p | Outcome |
|---|---|---|---|---|---|---|---|
| C3 | mixed, marginal | vs raw | +1.87 | +24.80 | +92.5% | 0.0000 | met |
| C3 | mixed, marginal | vs scale law | +1.87 | +33.97 | +94.5% | 0.0000 | met |
| C3 | mixed, marginal | vs CQR | +1.87 | +3.16 | +40.9% | 0.0029 | met |
| C3 | mixed, marginal | vs spec × scale law | +1.87 | +13.18 | +85.8% | 0.1805 | not met |
| C3 | mixed, PAC | vs raw | +7.91 | +54.02 | +85.4% | 0.0000 | met |
| C3 | mixed, PAC | vs scale law | +7.91 | +66.95 | +88.2% | 0.0000 | met |
| C3 | mixed, PAC | vs CQR | +7.91 | +9.01 | +12.3% | 0.0648 | not met |
| C3 | mixed, PAC | vs spec × scale law | +7.91 | +20.05 | +60.6% | 0.9555 | not met |
| C4 | R1, marginal | gated (raw) vs best (CQR) | +0.17 | −0.29 | — | 1.0000 | not met |
| C4 | R1, PAC | gated (scale law) vs best (scale law) | +0.39 | +0.37 | — | 0.0003 | met |
| C4 | R2, marginal | gated (scale law) vs best (raw) | +6.12 | +5.63 | — | 1.0000 | not met |
| C4 | R2, PAC | gated (theory) vs best (scale law) | +7.02 | +7.31 | — | 0.1912 | not met |
| C4 | R3, marginal | gated (theory) vs best (CQR) | +3.93 | +1.09 | — | 1.0000 | not met |
| C4 | R3, PAC | gated (raw) vs best (CQR) | +10.76 | +7.64 | — | 1.0000 | not met |

*Table S16. E-low v3 registered comparisons (mean excess overlap over 400 calibration subsets; Holm over all 14 rows). C3: 5 of 8 comparisons met; the claim as registered (every comparator, both classes) is not met. C4: met in 1 of 6 cells.*

<!-- source: results/lowdata_v3/summary.txt -->
| Regime | Class | Gate proxy excess pp (theory / raw / scale law) → choice | Raw | Scale law | CQR | CE-EVT-R | CE-EVT-R-G | C5 |
|---|---|---|---|---|---|---|---|---|
| R1 | marginal | +1.60 / +1.52 / +1.52 → raw | +0.18 / +0.24 (0.896) | −0.02 / +0.08 (0.893) | −0.29 / +0.26 (0.861, invalid) | −0.18 / +0.15 (0.877, invalid) | +0.17 / +0.24 (0.896) | miss |
| R1 | PAC | +2.44 / +2.99 / +2.20 → scale law | +0.81 / +0.23 (0.97) | +0.37 / +0.06 (0.96) | +0.68 / +0.27 (0.85) | +0.17 / +0.07 (0.98) | +0.39 / +0.05 (0.98) | miss |
| R2 | marginal | +3.89 / +3.98 / +3.52 → scale law | +5.63 / +0.34 (0.967) | +6.14 / +0.29 (0.970) | +10.02 / +0.87 (0.983) | +5.39 / +0.27 (0.967) | +6.12 / +0.24 (0.970) | hit |
| R2 | PAC | +3.49 / +3.96 / +4.03 → theory | +7.95 / +0.24 (1.00) | +7.31 / +0.13 (1.00) | +22.11 / +0.84 (1.00) | +7.09 / +0.20 (1.00) | +7.02 / +0.21 (1.00) | hit |
| R3 | marginal | +4.14 / +4.83 / +4.64 → theory | +2.46 / +0.62 (0.924) | +2.35 / +0.56 (0.922) | +1.09 / +1.34 (0.897) | +3.97 / +1.64 (0.931) | +3.93 / +1.57 (0.931) | miss |
| R3 | PAC | +17.37 / +6.19 / +8.90 → raw | +10.99 / +1.22 (1.00) | +9.03 / +1.22 (1.00) | +7.64 / +1.65 (0.96) | +13.04 / +1.16 (0.97) | +10.76 / +1.44 (1.00) | hit |

*Table S17. E-low v3, same-regime cells (15 test fields each). Each method cell: mean excess pp / excess pp at matched coverage (mean coverage for marginal, fraction of subsets with coverage ≥ 0.9 for PAC). C5 for the mixed fleet: the gate chose the theory in both classes and the theory gained ≥ 10% over raw (two hits); C5 total 5 of 8. C5 misses: R1 marginal and PAC, where the theory gained 201.2% and 79.6% over raw although the gate chose a classical pivot, and R3 marginal, where the gate chose the theory and the theory lost 61.4% to raw.*

**C3 details.** Against spec × scale law, the signed-rank test is driven by the per-field sign and rank of differences, so a large mean gain concentrated on part of the 45 test fields need not be significant (an interpretation; per-field differences are not tabulated). The CQR comparator already uses machine configuration as a feature; the classical scales that ignore the configuration are an order of magnitude worse, as the design probe predicted.

**C4 details.** The proxy difference between the theory and the best classical pivot was 0.08–0.50 pp in five of six cells. **Realised marginal coverage of CE-EVT-R in R1 was 0.877**, below the registered 0.89 threshold, so CE-EVT-R was formally invalid in that cell (as was CQR, 0.861), although coverage is averaged over 400 calibration subsets; these are all drawn from the same 30 fields with the same single historical run per field, so the luck of those runs is not averaged out (resolved by the resampling check, manuscript Section 6.5).

<!-- source: results/lowdata_v3/summary_extended_curves.txt -->
| Scenario | Class | Method | Coverage mean | P(cov ≥ 0.9) | Excess pp | Matched-cov. excess pp |
|---|---|---|---|---|---|---|
| R3 | marginal | CQR | 0.896 | 0.72 | +1.08 | +1.40 |
| R3 | marginal | CE-EVT-R | 0.931 | 0.71 | +3.97 | +1.67 |
| R3 | PAC | CQR | 0.948 | 0.96 | +7.64 | +1.72 |
| R3 | PAC | CE-EVT-R | 0.971 | 0.97 | +13.04 | +1.21 |
| Mixed | marginal | Raw pooling | 0.933 | 0.83 | +24.78 | +15.54 |
| Mixed | marginal | Scale law | 0.931 | 0.84 | +33.94 | +20.55 |
| Mixed | marginal | CQR | 0.930 | 0.77 | +3.15 | +1.41 |
| Mixed | marginal | CE-EVT-R | 0.918 | 0.55 | +1.87 | +0.73 |
| Mixed | PAC | Raw pooling | 0.967 | 0.98 | +54.01 | +18.61 |
| Mixed | PAC | Scale law | 0.966 | 0.97 | +66.94 | +21.46 |
| Mixed | PAC | CQR | 0.962 | 0.96 | +9.01 | +2.54 |

*Table S18. E-low v3 re-read with margin curves extended down to $0.25\lambda^\star$ (same seeds); only rows that differ from the registered reading are shown. No deployment falls below the curve grid any more. Every claim outcome is unchanged (C3 5 of 8, C4 1 of 6, C5 5 of 8); the C3 marginal comparison against CQR becomes +1.87 vs +3.15 pp (40.6%, Holm p 0.0029) and the PAC comparison against CQR 12.2% (Holm p 0.0648).*

### D.7 Resampling check with the registered curve grid

<!-- source: results/lowdata_v3/validity_resample.txt -->
| Scenario | Class | Raw pooling | Scale law | Spec × scale law | Theory (CE-EVT-R) |
|---|---|---|---|---|---|
| R1 | marginal | 0.9193 / 0.700 / +1.16 | 0.9205 / 0.707 / +0.92 | — | 0.9194 / 0.689 / +0.92 |
| R1 | PAC | 0.9597 / 0.911 / +3.99 | 0.9604 / 0.911 / +3.75 | — | 0.9607 / 0.917 / +3.77 |
| R2 | marginal | 0.9283 / 0.754 / +2.95 | 0.9282 / 0.767 / +2.90 | — | 0.9286 / 0.759 / +3.06 |
| R2 | PAC | 0.9655 / 0.946 / +11.15 | 0.9652 / 0.949 / +10.63 | — | 0.9641 / 0.935 / +10.56 |
| R3 | marginal | 0.9225 / 0.733 / +5.21 | 0.9214 / 0.717 / +4.74 | — | 0.9211 / 0.717 / +5.06 |
| R3 | PAC | 0.9605 / 0.932 / +21.68 | 0.9595 / 0.926 / +21.04 | — | 0.9603 / 0.930 / +21.45 |
| Mixed fleet | marginal | 0.9295 / 0.745 / +29.84 | 0.9283 / 0.750 / +37.21 | 0.9250 / 0.736 / +12.82 | 0.9243 / 0.747 / +2.96 |
| Mixed fleet | PAC | 0.9619 / 0.935 / +61.98 | 0.9631 / 0.942 / +73.86 | 0.9629 / 0.928 / +23.21 | 0.9625 / 0.931 / +14.69 |

*Table S19. Direct coverage check, registered reading with the $0.6\lambda^\star$ curve-grid floor (mean coverage / fraction of replicates with coverage ≥ 0.9 / mean excess overlap, pp). All 26 cells pass; manuscript Table 7 uses the extended curves, which change only the raw and scale-law mixed-fleet cells (mean coverage by at most 0.0044, mean excess by at most 0.04 pp) and R3 raw marginal (0.9225 → 0.9224, +5.21 → +5.20 pp).*

### D.8 Theory runtime

<!-- source: results/lowdata_v3/theory_runtime.txt -->
| Regime | Field (index) | Passes | Pass length (m) | Theory runtime (s) |
|---|---|---|---|---|
| R1 | 649 (5) | 16 | 2415 | 187 |
| R1 | 718 (10) | 10 | 1665 | 133 |
| R1 | 559 (15) | 90 | 3519 | 150 |
| R2 | 150 (5) | 73 | 5703 | 297 |
| R2 | 180 (10) | 83 | 5543 | 287 |
| R2 | 151 (15) | 41 | 5225 | 353 |
| R3 | 119 (5) | 18 | 458 | 23 |
| R3 | 74 (10) | 23 | 1016 | 51 |
| R3 | 215 (15) | 7 | 324 | 16 |

*Table S21. Single-core runtime of the theory predictor with 200 sampled operating conditions, three E-low v3 test fields per regime.*

### D.9 Status of every result

<!-- source: results/v7/summary.txt; results/v8/summary.txt; results/lowdata/summary.txt; results/lowdata_v2/summary.txt; results/lowdata_v2/matched_coverage.txt; results/lowdata_v2/feature_learning_curve.txt; docs/prereg_lowdata_v3.md; results/lowdata_v3/summary.txt; results/lowdata_v3/validity_resample_extended_curves.txt; results/lowdata_v3/check_boundary_R3.txt; docs/theory_evt.md -->
| Result | Status | Outcome |
|---|---|---|
| v7 system comparison, fields 20–49 | exploratory (used for method refinement) | CE variants dominate certified baselines on the same stack, two exceptions |
| v8 confirmatory system comparison, fields 50–79 | pre-registered | met: validity in all regimes (0/30 PAC failures); overlap below CPP and Lindemann in all 12 comparisons (4.0–54.7%) |
| v8 regret | post hoc reading of the registered run | CE+ regret 27–92% lower where positive; below the oracle in R1 marginal |
| Five-layer theory, $q_{0.9}$ prediction on development fields | developmental | −0.6% / +0.9% / +1.4% |
| Field-edge terms (Theorem 3(b)) | post hoc | R3 bias −4.0% → +0.8%; RTK unchanged |
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
| E-low v3 with extended curves | post hoc re-reading | all claim outcomes unchanged |
| Direct coverage check, both sources of randomness | pre-registered | all 26 cells pass |
| Efficiency over 4000 replicates | pre-registered as descriptive | mixed fleet: theory +2.96 / +14.69 pp vs spec × scale law +12.82 / +23.21 (marginal / PAC); within regimes tenths of a point |

*Table S20. Status of each result.*

---

## Appendix E. Notes for the authors (remove before submission)

- Numbering map to internal notes: Theorem 1 = `theory_v8` Theorem 3; Theorem 2 = `theory_transfer` Theorem 5; Proposition 3 = `theory_v8` Proposition B; Proposition 4 = `theory_evt` Prop. 1.1; Theorem 3(a) = `theory_evt` Thms 2.1/2.3; Theorem 3(b) = `theory_evt` Thm 2.4; Theorem 4 = `theory_evt` Thm 3.2″; Lemma 4 = `theory_evt` Thm 4.1 and Cor. 4.2; Theorem 5 = `theory_evt` Thm 4.3 and Cor. 4.4; Theorem 6 = `theory_evt` Thms 5.1/5.3; Proposition 7 = `theory_v8` Proposition 4; Proposition 8 = `docs/theory_limit.md`. The research proposal's weighted-conformal fixed point and conformal risk control with a monotone surrogate are not used.
- The v8 confirmatory comparison and E-low v2 both use fields 50–79 (different questions; the v8 method choice was fixed before E-low v2). E-low v3 test fields 5–19 also appeared in the v3–v6 system experiments (target-field data); `docs/prereg_lowdata_v3.md` §1 states this.
- The commit message of the resampling check says "all 28 cells PASS"; the result files list 26 cells (3 regimes × 3 methods × 2 classes + mixed fleet 4 × 2). The paper uses 26.
- Pre-registration is by git commit timestamp only; consider third-party registration (e.g. OSF) as noted in `docs/theory_v8.md` §7, and archive code and data with a DOI.
- Section 6.7 (real-vehicle validation) is a placeholder.

# Review R04: Probability and extreme-value theory of Gaussian processes

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (Computers and Electronics in Agriculture)

**Reviewer expertise:** extremes of Gaussian processes (Kac–Rice/Rice method, normal comparison, Bonferroni and Chen–Stein bounds, Gumbel limits, Leadbetter–Lindgren–Rootzén theory).

**Material examined:** manuscript.md; supplementary.md (Appendix A proofs, Appendix B, Tables S5, S5a, S5b, S12–S14, S20); docs/theory_evt.md; figures fig_theory_vs_sim.png and fig_information_limit.png. Code was read to check claims: experiments/core.py (`Condition`, `simulate`, `plan`, `exact_scores`, `exact_pair_scores`, `Field`), experiments/evt_theory.py (`predict_cdf`, `boundary_segments`) and scripts/check_evt.py (layer 4 and 5 checks). I also re-computed the binomial, Beta and Gumbel constants. No simulations were run.

---

## 1. Summary of the paper

The paper treats coverage planning as a chance constraint on the missed area when the machine does not follow the planned passes exactly. The zero-miss event is reduced to one scalar per run: the covering radius of the executed pass centres, section by section, including the field-edge terms. That score is calibrated by split-conformal or PAC quantiles on a "reference" plan with at least as many passes as the plan that is deployed (CE, CE+).

For fields with no operation history, the paper builds a "five-layer extreme-value theory" that predicts the run-score distribution of each field:
- L1: Lyapunov covariance of a linearised closed loop.
- L2: discrete Kac–Rice upcrossing bounds for pair-gap and field-edge processes.
- L3: a Bonferroni sandwich that justifies a product form.
- L4: a mixture over operating conditions, plus a coupling-based transfer inequality.
- L5: a Gumbel scale law.

The predicted 0.9 quantile is then used only as a ratio pivot for cross-field conformal calibration (CE-EVT-R). That method's validity follows from exchangeability across fields, not from the theory.

The experimental programme is extensive, pre-registered in stages and reported candidly, including failures. The theory's main measured benefit is efficiency in a mixed fleet of machine configurations. Within one configuration all pivots are equivalent, which the authors connect to an "information limit" (Proposition 8).

## 2. Recommendation

**Major revision.**

| Criterion | Score (1–10) |
|---|---|
| (a) Novelty | 6 |
| (b) Technical soundness | 4 |
| (c) Practical relevance | 6 |
| (d) Clarity | 5 |

The conformal part (Proposition 5, the resampling check) is sound, and the authors are commendably honest about what failed. Several pieces of the extreme-value theory are stated more strongly than their proofs support:
- The Theorem 4 bound is vacuous at the level where it is used.
- The "exact" Theorem 5 rests on a hypothesis that the authors' own refined L1 model violates, and it does not cover the edge terms non-vacuously.
- The extremal-index argument in Lemma 4 is a non sequitur.
- Theorem 6's hypotheses fail in two of the three regimes.

In addition, the "zero-data theory" is computed from a noise-free run of the same simulator, with the same condition distribution and GNSS error bank that generate the test data. This inflates every theory-versus-simulation and theory-versus-regressor comparison. None of these points threatens the validity of CE-EVT-R. They do threaten the paper's third contribution and the abstract's claims about the theory.

## 3. Strengths

- **Validity is separated from model accuracy.** CE-EVT-R uses the theory only through a field-measurable scale, so coverage rests on exchangeability (Proposition 5). The two-level resampling check (Section 6.5, Table 7) tests this guarantee over both sources of randomness, which is the right check and is rarely done.
- **The exact score is correct.** Lemma 1 (the covering radius on a section equals the maximum of the endpoint distances and the half-gaps whose midpoints lie in the chord) is correct, and the code in `core.exact_scores` implements it faithfully.
- **The L2 formula is right.** The non-stationary Rice bound in Theorem 3(a) is correct: the integrand is $p_{Z(x)}(t)\,\tilde\sigma'\Psi(\tilde m'/\tilde\sigma')$. Using the discrete upcrossing union bound on the 1 m grid is the right choice, because misses are evaluated on that grid.
- **Theorem 4 is correct as an inequality.** Replacing the earlier Slepian argument, which needed a sign assumption the closed loop violates, with a sign-free Bonferroni sandwich is a sound correction. The adjacent-pair correlation $\rho=-\tfrac12 r$ is computed correctly.
- **The core inclusion behind Theorem 5 is clean.** The coupling inclusion $\{U_{\pi_1}>t\}\subseteq\{U_{\pi_0}>t-\Delta(C)\}$ under equal covariance and bounded mean shift is correct. The Mills-ratio step in the $\kappa$ bound ($h(u)\le u+1/u$ for $u>0$) is also correct.
- **Proposition 8 is correct as stated.** Under the ideal scale, $V_{(k)}=H^{-1}(B)$ with $B\sim\mathrm{Beta}(k,n+1-k)$. It isolates the within-field order-statistic inflation of PAC certification in a useful way.
- **The constants check out.** I verified: $k=29=n$ for the PAC rule at $n=29$, $\varepsilon=\delta=0.1$; the Beta(29,1) 5% quantile is $0.05^{1/29}=0.902$; the Beta(27,3) standard deviation is 0.054; the binomial failure probability is 0.0434; the integrated failure rates are 14.5% and 1.2%; and $P(\mathrm{Bin}(30,0.143)\ge9)=0.021$.
- **The reporting is transparent.** Developmental, post hoc and pre-registered material is labelled, failed claims are reported, and the earlier errors in the theory notes (the Slepian sign condition, the $\Delta^2$ sign error) are disclosed.

## 4. Major issues

### M1. Theorem 4 (L3): the error bound is vacuous at the certified level, and the dependency structure is wrong once edge terms are included

*Location:* Theorem 4, the text after it ("first term of $\eta$ is about 0.0055"), Lemma 4, A.13, and `evt_theory.predict_cdf`.

1. **The second term of the bound is about $M$, so the bound is about $\varepsilon$.** $\eta=M^2/2+\sum_j\min(\mu_j,\mu_{j+1})$. For roughly homogeneous pairs, $\sum_j\min(\mu_j,\mu_{j+1})\approx M\approx0.105$ at $P\approx0.9$. The bound on $|P(U\le t\mid C)-\prod_j(1-\mu_j)|$ is therefore about 0.11, the same size as $\varepsilon$. The manuscript reports only the first term (0.0055) and so implies a tightness the theorem does not give. The authors' own validation shows errors of 0.012–0.018 at the 0.9 level (product 0.888 and 0.882 against a true 0.900, Table S5). That is already larger than the reported 0.0055 and is not explained by it.
2. **Mixing over $C$ makes it worse.** Lemma 4 inherits $|\rho_\pi|\le\mathbb E_C[\eta(t\mid C)]$. Under DGPS, the conditions in which a GNSS jump makes one pair dominate have $M\gtrsim1$ (theory notes §3: $\mu_{\max}\approx0.5$). There $\eta\ge M^2/2$ is trivial or exceeds 1. The statement "$M\approx0.105$ at the certified level" conflates the unconditional level with the conditional $M(t\mid C)$. $\mathbb E_C[\eta]$ at $t=\hat q_{0.9}$ is never reported, and I expect it is not small.
3. **The dependency graph is not a chain once edge terms are included.**
   - The proof uses "non-adjacent pairs are independent given $C$". The field-edge terms of Theorem 3(b) break this.
   - In two-pass sections the edge event depends on passes $k$ and $k+1$. In the convex but non-rectangular fields used here, the pass that holds an edge changes along $x$, so the edge pseudo-pair depends on passes $1,2,3,\dots$ and therefore on many interior pairs that are not adjacent to it in the index.
   - `evt_theory.predict_cdf` places each single-pass edge segment, and the union of two-pass sections, into the product as if they were independent of the interior pairs that share those passes.
   - The bound must be stated for a general dependency graph $G$: $|P-\prod|\le M^2/2+\sum_{(i,j)\in E(G)}\min(\mu_i,\mu_j)$.
4. **The proof in A.13 is mis-justified.** It argues that expanding $\prod(1-\mu_j)$ "as an alternating sum with decreasing terms" gives $1-M\le\prod(1-\mu_j)\le1-M+\sum_{i<j}\mu_i\mu_j$. The elementary symmetric sums need not decrease (take all $\mu_j$ close to 1). The inequality is still true, because it is Bonferroni applied to independent events. Fix the argument.

*Why it matters:* L3 is presented as a "Bonferroni-bounded product form" with a computable error that is "an order of magnitude smaller than $\varepsilon$" (theory notes §3). As it stands, the bound certifies nothing at the operating point.

*Fix:*
- (i) Replace or complement the sandwich with the Arratia–Goldstein–Gordon Chen–Stein bound on the conditional dependency graph. Given $C$, non-neighbours are independent, so $b_3=0$ and
  $$|P(U\le t\mid C)-e^{-M}|\le(b_1+b_2)\frac{1-e^{-M}}{M},\qquad b_1=\sum_j\sum_{i\in N_j}\mu_i\mu_j,\quad b_2=\sum_j\sum_{i\in N_j\setminus\{j\}}p_{ij}.$$
  The bound on $|e^{-M}-\prod(1-\mu_j)|$ is of order $\sum\mu_j^2$. The first-order part is then $O(\sum\mu_j^2)$, about $M^2/K$, instead of $M^2/2$.
- (ii) Compute $p_j=P(A_j\cap A_{j+1}\mid C)$; the authors already have exact Gaussian Monte Carlo for this. Alternatively, bound it by the two-parameter field $Z_j(x)+Z_{j+1}(x')$ using a Borell–TIS or expected-Euler-characteristic bound. The variance of this field is $\lambda_0(1-r(x,x')/2)$ at threshold $2t$, which gives a much faster exponential decay than $\mu_j$.
- (iii) Define the neighbourhoods $N_j$ to include the edge terms and every pair that shares a pass with them.
- (iv) Report $\mathbb E_C[\min\{\eta(t\mid C),\,1-\max_j\mu_j(t\mid C)\}]$ at $t=\hat q_{0.9}$ for every regime. The truncation is legitimate because both quantities lie in $[0,1-\max_j\mu_j]$.
- (v) State in Section 5.3 that $\mu_j$ in the product are a mixture of Rice upper bounds and Monte Carlo estimates. With that mixture, Theorem 4 bounds the error of an idealised predictor, not of the computed one.

### M2. Theorem 5 (exact transfer): the main hypothesis is contradicted by the refined L1, edges make $\bar\Delta$ vacuous, and the deployment corollary is misstated

*Location:* Theorem 5 and its deployment sentence; the $\kappa$ paragraph; A.15; Proposition 5's last sentence; the claim in Section 6.2 that Theorem 5 was validated (Table S5).

1. **The equal-covariance hypothesis fails for the model the authors actually use.** Proposition 4 makes the covariance plan-independent only for the stationary constant-coefficient L1. The refinements the authors found necessary all make the covariance plan- or field-dependent:
   - B.1(a): the interpolation weight $f_k$ depends on where each pass starts, so on the plan. It changes the variance by 2–3%, and the authors note this changes tail probabilities by 15–30%.
   - B.1(b): time-varying quasi-linearisation along a terrain-dependent trajectory, so $A_t$ depends on the lateral position of the pass.
   - B.1(c): a leak rate that depends on the condition.

   The theory notes (§1, Proposition 1.4) also state that under DGPS 96% of operating conditions briefly trigger steering saturation or rate limits, so the conditional law is not Gaussian. The word "exact" therefore applies to an idealisation that the paper itself discarded.
2. **A uniform $\bar\Delta$ over all sections, including edge pseudo-pairs, is vacuous.**
   - The edge term of a greedy plan contains a geometric slack (overshoot of the last pass) that varies between $0$ and one spacing $d=w-2\lambda$ from plan to plan.
   - Whenever $\pi_1$ has less slack than $\pi_0$, the mean shift of that pseudo-pair is up to about $d$ (metres). Then $\bar\Delta\gg s$ and $\kappa$ is astronomically large.
   - Matching edge segments between plans is also ill-defined when the pass that holds the edge changes along $x$.
   - The statement also silently needs the section domains to be nested, $I^{(1)}_j\subseteq I^{(0)}_j$. In a non-rectangular field the matched pair of $\pi_1$ sits at different $y$ and spans a different $x$-range.
3. **The deployment corollary is wrong for the marginal rule.** For the marginal rule, $\hat\lambda$ is random and $\mathbb E[1-F_{\pi_0}(\hat\lambda)]\le\varepsilon$, so
   $$P(\text{miss})\le\mathbb E[\kappa(\hat\lambda)(1-F_{\pi_0}(\hat\lambda))],$$
   which is not $\le\kappa(\hat\lambda)\varepsilon$. A random quantity cannot appear on the right of a marginal guarantee. Use $\sup_{t\in T}\kappa(t)\,\varepsilon$ over a set $T$ that contains $\hat\lambda$ with high probability, plus the probability of leaving $T$. The PAC statement is fine conditionally.
4. **$\kappa$ and $\bar\Delta$ are never computed.**
   - Even small values matter: $\bar\Delta/s=0.1$ at $u\in[3,4]$ gives $\kappa\approx1.40$–$1.53$ (my calculation from the paper's own bound), which turns $\varepsilon=0.1$ into about 0.15.
   - The GNSS timing component grows with the pass index, because the $k$-th pass of $\pi_1$ starts earlier than the $k$-th pass of $\pi_0$ by about $k$ pass-durations times the relative change in pass count. Under DGPS this term can be large, as the authors admit in Limitation 2.
5. **The "validation" of Theorem 5 is not a test of the inequality.** It is a comparison of the L4-predicted $F_{\pi_1}(\lambda)$ with simulation (`scripts/check_evt.py`, layer 4: "deployed coverage F_pi1(t): predicted … simulated mean(Ui <= lam)"). That comparison uses the interior-only score `interior_U`, not the exact score with edges.

*Fix:*
- (i) State a version with pair-specific shifts: $1-F_{\pi_1}(t)\le P\big(\bigcup_{j\in J(\pi_1)}\{T^{(0)}_{\phi(j)}>t-\Delta_j(C)\}\big)$, with explicit hypotheses on the matching $\phi$ and on domain inclusion.
- (ii) Treat the edge terms separately, for example by forcing $\pi_0$ and $\pi_1$ to share the edge geometry, or by including the slack in the threshold.
- (iii) Add a covariance-mismatch term, for example $+\,\mathbb E_C\,\mathrm{TV}\big(\mathcal N(0,\Sigma^{(1)}_C),\mathcal N(0,\Sigma^{(0)}_C)\big)$, computable from the Gaussian KL divergence on the 1 m grid. Without it the inequality applies only to the idealised model.
- (iv) Correct the marginal deployment statement as in item 3.
- (v) Report $\bar\Delta$, $\hat\kappa(\hat\lambda)$ and the fraction of deployments with $\lambda_g>\lambda_0$, where dominance fails and the cap applies, on all test fields.
- (vi) Present the closed-form $\kappa$ bound as a heuristic. A rigorous version is available for the pair and single-edge representation, which is a maximum of affine functionals of a Gaussian vector. There Ehrhard's inequality makes $g=\Phi^{-1}\circ F_C$ concave, so
  $$1-F_C(t-\Delta)\le\bar\Phi\big(g(t)-\Delta g'(t-\Delta)\big),$$
  and the Mills-ratio step then applies with $g'$ in place of $1/s$. This does not cover the two-pass "min" edge sections, whose sublevel sets are not convex.

### M3. Proposition 4 (conditional independence and Gaussianity) is a property of the simulator, not of field operations, yet Theorems 3(b), 4 and 5 all rest on it

*Location:* Proposition 4, A.10, Section 6.1 ("passes executed in real time order"), and `core.simulate`.

- **Independence is built into the simulator.** In `core.simulate` all passes of a run are simulated in parallel as separate columns $(R,K)$. Each column has its own initial lateral offset $d\sim\mathcal N(0,0.03)$ and heading draw, a zero integrator, a zero OU slip state and independent innovations. Passes are coupled only through the condition $C$ and the GNSS error read at the pass start time. Conditional independence across passes therefore holds by construction.
- **Real machines differ.** Soil roughness and slip are spatially indexed: the same soil patch, wheel ruts and moisture field act on adjacent passes 1.5–6 m apart. Controller state also carries through the headland turn. Spatially correlated slip would make adjacent and non-adjacent pairs dependent given $C$, and that removes the independence on which:
  - Theorem 4's sandwich relies;
  - the edge product in Theorem 3(b) relies;
  - the coupling in Theorem 5 relies.
- **Gaussianity is overstated.** Proposition 4 is stated as exact in the "linear regime". The theory is then applied to DGPS conditions in which, by the authors' account, saturation and rate limits are almost always briefly active. The supplement (B.1, the paragraph on A1′) still explains residual errors by non-Gaussianity from nearest-neighbour terrain. Theory notes §6.2 retracted that explanation, so the supplement and the notes are inconsistent.

*Fix:* State conditional independence as a modelling assumption (A0) and discuss its physical plausibility. Add a sensitivity experiment in which slip and roughness are a spatial random field shared by adjacent passes, with correlation length comparable to the implement width, and report how far Theorem 4's product form and the edge product degrade. Present Proposition 4 as "Gaussian approximation", with the describing-function and leaky-integrator steps as approximations.

### M4. Theorem 3(b) (field-edge terms): the "iff" is too strong, the two-pass treatment is an ad hoc union bound, and the physical claim may be an artefact of the evaluation domain

*Location:* Theorem 3(b), A.12, Table 4, Section 6.2 ("This is the physical mechanism…"), Section 7.4 bullet 6, the abstract, and `evt_theory.boundary_segments`.

1. **The "iff" ignores passes that can drift onto the edge.** The edge is missed iff $S_k>t$ for all passes. The theorem quantifies only over passes whose *planned* footprint covers $b$. An executed pass that does not cover $b$ on plan can cover it after drifting outward. Under DGPS, with 0.5–1.8 m tails (Table 1), this is not negligible. The statement is then a one-sided inclusion, not an equivalence.
2. **The two-pass treatment is not a Rice bound.** For sections held by two passes, the miss probability is computed pointwise as a product of normal tails and then summed over sections (`tot += pr` in `predict_cdf`). That is a union bound over 1 m sections of a smooth process, which can be arbitrarily loose, and it is not a Kac–Rice bound. The right object is the outcrossing of the bivariate process $(S_k,S_{k+1})$ from the safe set $\{\min(S_k,S_{k+1})\le t\}$. Belyaev's formula for vector-process outcrossings, or the discrete analogue $P(\text{none at } i,\ \text{both at } i+1)$ with independent components, gives a bound of the same quality as part (a).
3. **The evidence for "misses concentrate at field edges" is indirect and partly in-sample.**
   - The edge terms raise the predicted quantile by about 4.8% in R3. The spread across fields is unchanged (sd 0.108 to 0.106, Table S5b).
   - All three versions of the edge terms were developed and checked against the same 15 R3 fields (B.3), so the final version's fit is in-sample.
   - No result file reports where misses actually occur. I found no such measurement in results/.
4. **The edge may be an artefact of the evaluation domain.**
   - $W$ is the field inset by $2w$ (`Field.M = P.buffer(-2w)`). Its boundary adjoins the headland, which in practice is worked by perimeter passes.
   - The simulator and evaluator ignore those passes. An "edge miss" at $\partial W$ may therefore be covered by a headland pass in reality.
   - The headland pass is driven at a very different time, so its GNSS error is far less common-mode with the infield pass. The physics of the boundary gap is then closer to a long-lag interior gap.
   - The practical recommendation "boundary passes set the certified margin under DGPS" is not established by this model.
5. **Why don't edges dominate under RTK?** A single-pass edge process has standard deviation $\sqrt{\lambda_0}$, which is $\sqrt2$ times the pair standard deviation $\sqrt{\lambda_0/2}$. At equal threshold, edges should then dominate per unit length unless the geometric slack is positive. I suspect edges bind only on boundary segments nearly parallel to the passes. The paper should state this geometric explanation, because it, and not GNSS common mode alone, determines when edges matter.

*Fix:* Restate (b) as an inclusion, or include every pass within reach. Replace the union over sections by a bivariate Rice or discrete outcrossing bound. Report, per regime, the fraction of missing runs whose `exact_pair_scores` argmax is an edge column. Include headland passes in at least a sensitivity analysis. Validate the final edge model on fields not used to develop it.

### M5. Theorem 6 (Gumbel scale law): hypotheses fail in two of three regimes, the cited theorem does not cover a family of correlated processes, edges change the scale, and one number is wrong

*Location:* Theorem 6, A.16, the scale-law comparator pivot, and Section 5.3 ("about 15%").

1. **The hypotheses do not hold in R2 or R3.** The theorem needs fixed $C$, stationary pairs and a constant mean. Under hilly terrain (R2) and DGPS (R3) the conditional mean $m_j(x\mid C)$ is driven by terrain and the GNSS trajectory and is far from constant. A Gumbel limit needs a uniform-in-$x$ bound on the mean or an explicit non-stationary extension (e.g. Piterbarg's results for non-stationary processes with a unique point of maximum variance).
2. **The cited theorem covers only one process.** Leadbetter et al. (1983, Thm 8.2.7) is for the maximum of a single stationary Gaussian process. Here $U$ is the maximum over $K$ processes, where adjacent ones have cross-correlation $-\tfrac12 r(x,x')$. Asymptotic independence of the component maxima needs a normal-comparison argument: Berman's lemma with $\max|\rho|=\tfrac12<1$, plus Berman's condition $r(\tau)\log\tau\to0$ within each pair. The asymptotic regime must also be stated: $K\to\infty$, $L_j\to\infty$, or both. None of this appears in A.16.
3. **Edges change the leading scale.** Once edge terms are part of $U$ (Lemma 1, and the "boundary pseudo-pairs" of Section 5.2), the single-pass edge processes have twice the pair variance. Asymptotically the maximum is governed by the component of largest variance, so $s$ in Theorem 6 is the wrong scale unless the edge slack is positive and grows with the field.
4. **The "about 15%" figure is wrong.** With $\varepsilon=0.1$, $t_\varepsilon\propto a_N+2.250/a_N$. From $N=10^3$ to $10^4$ this ratio is 1.114, not 1.155 (1.155 is the ratio of $a_N$ alone). It is smaller still when $m>0$.
5. **The asymptotics are weak at this scale.** At $N\sim10^2$–$10^3$, Hall's $O(1/\log N)$ rate means the Gumbel quantile is a poor approximation. The penultimate (Weibull-type) correction is known to be much better for Gaussian maxima. The support offered is an $R^2=0.964$ fit on 8 development fields.

*Fix:* Downgrade Theorem 6 to a proposition for the idealised stationary, flat, RTK case with the normal-comparison step written out, or call it a heuristic scaling law. Correct the 15%. Note that the scale-law pivot is a heuristic comparator whose validity does not depend on the theorem (as the paper rightly says).

### M6. Lemma 4 and the extremal index: the clustering conclusion is a non sequitur

*Location:* Lemma 4 ("By Jensen's inequality … $\theta_t<1$: exceedances cluster because operating conditions differ between runs, not because of local pair dependence"), A.14, and theory notes Corollary 4.2.

- **$\theta_t<1$ is automatic.** For any $M>0$, $(1-e^{-M})/M<1$ because $1-e^{-x}<x$. So $\theta_t<1$ holds with a *constant* $C$ and has nothing to do with Jensen or with heterogeneity across runs. At $M=0.105$ the value is 0.949.
- **The correct dichotomy is the reverse of what is stated.** For fixed $C$ and $t\to\infty$, $M\to0$, so $\theta_t\to1$ and there is no clustering, since adjacent pairs are negatively correlated. A limit $\theta<1$ can survive only because $C$ is random. Jensen is not what shows this. What shows it is that $\mathbb E[1-e^{-M}]/\mathbb E[M]$ stays below 1 when $M(t\mid C)$ is not uniformly small across $C$ in the tail.
- **"Extremal index" is used loosely.** The Leadbetter–Lindgren–Rootzén extremal index is defined for stationary sequences under $D(u_n)$-type mixing. A run-level random environment $C$ shared by all pairs violates mixing. The limit is a mixture of Poisson (or Gumbel) laws, not a single law with an index $\theta$.
- **Consequence for Theorem 2 and Proposition 2.** Calling $1/\mathbb E[N_t\mid N_t\ge1]$ the "finite-threshold extremal index" is fine as a definition. Proposition 2 then uses $\theta\approx0.5$, an estimated value, inside an "at most" statement.

*Fix:* Call $\theta_t$ the reciprocal mean cluster size. Remove the Jensen claim. State the limit correctly: within a condition there is no clustering, and the apparent clustering is a mixing effect over $C$. Label Proposition 2's numerical bound as an estimate.

### M7. The "zero-data theory" has oracle access to the data-generating process; the theory-versus-simulation and theory-versus-regressor comparisons overstate its value

*Location:* Sections 4.3, 6.2, 6.6 (Table 9, Fig. 6), the abstract ("1.7–3.7 times more accurately than data-driven regressors"), and `evt_theory.predict_cdf`.

- **How the theory is computed.** `predict_cdf` draws operating conditions with the experiments' own `make_cond` (soil moisture, slip gain, roughness, roll compensation, mounting bias, and the GNSS station-pair-day segment from the same CORS bank). It then computes the conditional mean by running `core.simulate` with noise switched off (`ZeroRNG`).
- **Where the "theory" content actually lies.** The L1–L5 machinery only replaces the within-condition Gaussian fluctuation. Under DGPS the run-score variability is dominated by $C$, that is by GNSS, so the R3 "theory" is essentially a Monte Carlo over the same GNSS bank that drives the test simulations.
- **Why the comparisons are unfair.** A regressor trained on one noisy run per field is compared with a predictor that knows the true distribution of $C$ and the exact noise-free nonlinear dynamics. On a real farm neither is known. A user needs a calibrated vehicle model and a GNSS error model for their own receiver, and the paper validates neither.

*Fix:*
- (i) State in Section 4.3 and in the abstract that the theory uses the simulator's noise-free dynamics and condition distribution.
- (ii) Add misspecification experiments: a theory computed with a GNSS bank from different stations or seasons, perturbed soil and slip priors, and mis-identified controller gains (for example ±20%), and report the log-error of $\hat q_f$ and the mixed-fleet efficiency.
- (iii) Decompose, per regime, the variance of the run score (or of the 0.9 quantile) into a between-$C$ part and a within-$C$ part, so readers can see how much of the predictive accuracy comes from the extreme-value layers.
- (iv) Soften "1.7–3.7 times more accurate".

### M8. Validation targets and the "safe upper bound" are mislabelled

*Location:* Table 3 and its caption, Table S5/S5a, Section 6.2, B.1(c), and `scripts/check_evt.py`.

1. **The development checks used the interior-only score.** The checks in Table 3, Table S5 and S5a, and the Theorem 5 "coverage after a plan change" numbers compare the theory with `interior_U`, the maximum over interior pairs only. They do not use the exact run score with edges (`simulate_U` → `interior_U`; "0.9-quantile of the interior needed erosion"). The captions say "run score". In R3 the distinction is exactly the 4% edge effect discussed in Section 6.2.
2. **The "safe upper bound" is not a bound.**
   - Clamping the integrator reduces the variance of the *integrator state*. It does not in general reduce the variance of the lateral offset, because weaker integral action can increase low-frequency offset variance.
   - The argument "clamping only reduces variance" is therefore unproven for $e_k$, and three test conditions are not a proof.
   - Even with an over-dispersed L1, the predicted quantile mixes Rice upper bounds, Monte Carlo estimates and a product form whose error has no sign (M1). The resulting $\hat q$ has no one-sided guarantee.
3. **The R3 first-version numbers are inconsistent.** Table 3 gives "36.0 / 37.3 (−3.5%)", while theory notes §6.2 say the reference was unified to 37.09 (−2.9%).

*Fix:* Relabel Table 3 and S5 as interior-only, or redo them with the exact score. Rename the "safe upper bound" to "unclamped-model prediction (empirically conservative)". Harmonise the R3 figures.

### M9. Proposition 8 ("information limit") is stated beyond what it proves, and its empirical check is weak

*Location:* Proposition 8, the sentences that follow it, Section 6.6 ("The information limit"), and Fig. 7.

- **What the proposition actually shows.** It is an exact distributional identity for the *ratio-pivot / order-statistic* procedure under the ideal scale. It is not a lower bound over all procedures. "A property of run-to-run randomness that **no field-level prediction can remove**" is true only within that class.
- **What would make it a genuine limit.** A true information-limit statement is available and should be stated: any distribution-free PAC $(\varepsilon,\delta)$ upper tolerance bound built from $n$ i.i.d. scalars must be at least $V_{(k^\ast)}$ with $k^\ast$ the PAC index, and $k^\ast=n$ here. That is a minimax statement over all continuous $H$. A parametric shape model shared across fields could do better, and the paper should say so.
- **"Can be computed from the theory before any experiment" is overstated.** The between-field spread *relative to the theory error* needs the theory error, which needs data.
- **The check in Fig. 7 is weak.**
  - Fig. 7 summarises a strongly skewed distribution by mean ± sd; the lower bars fall below 1, although $\lambda_g/\lambda^\star_g\ge1$ with probability above 0.95 under $B\sim\mathrm{Beta}(29,1)$.
  - Each regime contributes one observation, and the observed R1 value (1.018) is near the lower tail.
  - "All observations lie within one predicted SD" is a weak test.

*Fix:* Report predictive quantiles and the predictive-CDF value (PIT) of each observation. Restate the scope of Proposition 8. Add the minimax remark.

### M10. Proposition 5 in the mixed fleet, and the end-to-end guarantee

*Location:* Proposition 5, Section 5.4, Section 6.5, and Table 7 (mixed-fleet rows).

1. **The mixed-fleet guarantee averages over configurations.** In the mixed fleet the guarantee is marginal over machine configurations. Over-coverage on RTK fields can mask under-coverage on DGPS fields (or the reverse). For a contractor the per-configuration guarantee is what matters. Report coverage per configuration within the mixed-fleet resampling, and consider a Mondrian (configuration-conditional) variant.
2. **The end-to-end zero-miss guarantee depends on transfer.** Proposition 5 certifies the score on the *reference* plan. The miss guarantee on $\pi_g(\hat q_gv^\star)$ needs Theorem 5, so it inherits all of M2, and it fails outright when $\hat q_gv^\star>\lambda_0$. Section 6.5 reads coverage from deployed-plan margin curves, which is good, but then the result is an empirical check of transfer, not a consequence of Proposition 5. Say so, and report how often the cap or $\lambda_g>\lambda_0$ is active.
3. **The Beta statement in Section 5.4 is about the population average.** "Given a fixed set of historical runs, the coverage of a new field is a draw from Beta" is true for coverage averaged over new fields, $H(v^\star)$, and not for a particular field $g$, whose coverage is $G_g(\hat q_gv^\star)$.

### M11. "Smallest valid score" (Theorem 1, Corollary 1, abstract, Highlights) rests on a transfer assumption that the paper says fails

*Location:* the abstract, contribution 1, Theorem 1, and the definition of validity in Section 5.1.

- Validity is defined by quantifying over all $\lambda$ with a fixed execution $e$. But $e$ for $\pi(\lambda)$ is a different object for each $\lambda$, with a different pass count.
- Theorem 1 holds "under shift-equivariant transfer". Section 3 and the code docstring of `exact_scores` say that this holds only for a shift-equivariant planner, which the greedy planner is not because of the pass-count jumps and the edge slack (M2.2).
- Without that assumption, Lemma 2 is a tautology, and $S^\star\le S'$ is shown only numerically (6 fields × 200 runs).
- The headline "the tightest valid one" needs this qualifier in the abstract and Highlights, or a restricted definition of validity at the reference plan only.

## 5. Minor issues

**Theorem 3(a) (L2)**
- The theorem statement mixes mathematics with algorithmic choices ("where the bound is loose (≥0.01) … Monte Carlo"). Move these choices to the method.
- The continuous formula needs $C^1$ paths and $\tilde\sigma'(x)>0$. The observed process is piecewise linear (1 m records, nearest-sample, then linear interpolation), so only the discrete version applies to it. Say so and drop the claim that the continuous formula is the one used.
- The tail-exactness claim (ratio → 1 as $t\to\infty$) is irrelevant at $u\approx3$–4 on long passes, where double crossings are not negligible. The paper reports 0–17% looseness, so present that empirical figure instead.

**Proofs and earlier theorems**
- A.13: the "alternating sum with decreasing terms" justification is false in general (see M1.4).
- A.7, Theorem 2:
  - needs absolutely continuous $T_j$;
  - $H$ and $\theta_t$ must hold uniformly over the random threshold $\hat\lambda$ for the deployed statement;
  - $\theta_t$ is defined over $J(\pi_0)$, which should be stated.
- Lemma 3: the proof uses empirical, not conformal ($n+1$) quantiles. State this.
- Lemma 1: `_chord_x` takes the min and max over all intersection pieces. That is fine for the convex fields used (the `Field` docstring says "convex polygon"), but the paper should say fields are convex.

**Naming, notation and stale text**
- Proposition 6 is a heuristic (B.4 says "heuristic, motivated post hoc"); do not call it a proposition.
- The supplement's Theorem 3(b) proof and the L3 text use "$\mu_j$" both for true probabilities and for computed surrogates. Use $\bar\mu_j$ for the surrogates.
- The docstring of `evt_theory.py` still says the predictor is "restricted to the interior pass pairs" and that L3 uses the "normal-comparison lemma". Both are stale.
- The theory notes still list "Chen–Stein" among the tools used, but it is not used. Either use it (see M1) or remove it.

**Monte Carlo and runtime details**
- Section 4.4 says 200 sampled operating conditions, but `predict_cdf` defaults to `n_cond=300`. State which was used, report the Monte Carlo standard error of $\hat q_f$ from the condition integral, and note that `rng=default_rng(0)` reuses the same condition sample for every field. That correlates errors across fields, which the ratio pivot partly absorbs.
- Section 6.5 / Table 7: the reported standard errors (0.0005–0.0008) treat the 4000 replicates as independent. The per-field margin curves (200 runs per grid point, standard error about 0.021 at 0.9) are shared by all replicates, so the effective standard error of mean coverage is closer to $0.021/\sqrt{45}\approx0.003$. The conclusions are unchanged, but report it correctly.

**Inconsistencies in the text**
- In Section 5.3, L3: "$M\approx0.105$ at the certified level" conflates conditional and unconditional quantities (see M1.2).
- Section 6.2: "coverage after a plan change (Theorem 5) was predicted as 0.901, 0.890 and 0.920". This validates the L4 prediction, not the Theorem 5 inequality (M2.5).
- Supplement B.1 retains the A1′ / non-Gaussianity explanation that theory notes §6.2 retracted.

**Fig. 7**
- Use quantile bars (for example 5–95%) and mark $1.0$ as the hard lower bound of the PAC ratio with probability above 0.95.

## 6. Questions to the authors

1. What are $\mathbb E_C[\eta(t\mid C)]$, $\sum_j p_j$ (computed, not bounded) and the share of conditions with $M(t\mid C)\ge1$ at $t=\hat q_{0.9}$, per regime?
2. On the v8 and E-low test fields, what are $\bar\Delta$, $\hat\kappa(\hat\lambda)$ and the fraction of deployments with $\lambda_g>\lambda_0$, or at the $0.8\,w/2$ cap? How large is the GNSS timing component of $\bar\Delta$ under DGPS?
3. In what fraction of missing runs is the argmax of `exact_pair_scores` an edge column (R1, R2, R3)? Does the answer change if headland perimeter passes are simulated?
4. Why do the edge terms, whose single-pass standard deviation is $\sqrt2$ times the pair standard deviation, hardly matter under RTK? Is it the geometric slack on oblique boundary segments? Please quantify the length of boundary within 1–2 standard deviations of binding.
5. How does the log-error of $\hat q_f$ (Table 9) change when the theory uses a GNSS bank from different stations or seasons, or mis-specified soil, slip and controller parameters?
6. What is the per-configuration coverage inside the mixed-fleet resampling check?
7. Were the three versions of the edge terms all tuned on the same 15 R3 fields that are used to validate the final one? If so, can the final version be validated on fresh DGPS fields?
8. Does the leaky-integrator model ever give a *larger* offset variance than the unclamped model? If so, the "safe upper bound" is not one.
9. With spatially correlated slip shared by adjacent passes, how much do the product form (Theorem 4) and the edge product degrade?
10. Can Theorem 6 be restated for $K$ correlated stationary processes with an explicit normal-comparison step, and in which asymptotic regime ($K\to\infty$ or $L\to\infty$)?

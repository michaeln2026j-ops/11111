# R15 — Mathematical proof check

Manuscript: *Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations* (Computers and Electronics in Agriculture).
Files checked: `docs/paper/manuscript.md` (all formal statements), `docs/paper/supplementary.md` (Appendix A proofs, Appendix B), `docs/theory_evt.md`, `docs/theory_limit.md`.
Scope: this review covers only whether every formal statement is correct. Experimental design and the literature are outside its scope, except where the text uses a theorem to read an experiment.
Numerical checks: `/tmp/claude-0/-home-user-11111/4d5f8718-15c2-54c4-b320-127eb47662e0/scratchpad/chk.py` (scipy; runs in under 1 s).

---

## 1. Summary

The paper has three parts:

1. **Exact score and conformal certificates.** The zero-miss event of a coverage plan is reduced exactly to a scalar covering-radius score, and that score is calibrated with conformal order statistics (CE, CE-q, CE+).
2. **Five-layer Gaussian extreme-value theory (L1–L5).** The theory predicts the run-score distribution. It also supplies a coupling inequality (Theorem 5) that transfers a certificate from the reference plan to the deployed plan.
3. **Cross-field calibration (CE-EVT-R).** Fields are calibrated against each other through a ratio pivot. The paper adds a characterisation of the ideal pivot that it calls an "information limit" (Proposition 8).

The probabilistic core is mostly correct. I checked these results line by line and found them sound: Lemma 1, Lemma 2, Lemma 3, Theorem 2 at a fixed threshold, Proposition 3, the Kac–Rice bound of Theorem 3(a), the two Bonferroni sandwiches of Theorem 4, the coupling step of Theorem 5, the Mills-ratio bound on κ, and the identity of Proposition 8. Every numerical constant I recomputed matches the paper:

- Minimum n: 9 for the marginal rule and 22 for the PAC rule.
- PAC k = n for 22 ≤ n ≤ 37.
- Proposition 7: the test fails iff at most 172 runs are miss-free, with probability 0.0434; failure rates are 14.5% and 1.2%.
- Beta(27,3): standard deviation 0.054, 5% quantile 0.798. Beta(29,1): 5% quantile 0.902.
- Proposition 2 bound: about 0.74%.

The problems lie in how the main text uses these results:

- **"Distribution-free" is applied to deployed plans.** The abstract, the contributions, Section 4.3 ("validity does not depend on the theory"), the Proposition 5 deployment clause and the Conclusion say the zero-miss guarantee is distribution-free. That holds only for the score on the reference plan. Every method except CE deploys a different plan, so its zero-miss guarantee depends on Theorem 2 or Theorem 5. Theorem 5 in turn depends on the linear-Gaussian theory, and it yields κ·ε rather than ε.
- **Theorem 5's hypotheses contradict the L1 model actually used.** Theorem 5 is called "exact", but it assumes a plan-independent covariance. The refined L1 (observation operator, time-varying quasi-linearisation, clamp) makes the covariance plan-dependent. In addition, A1 is violated in 96% of DGPS conditions (theory_evt §1.4).
- **Several labels go beyond what is proven.**
  - Theorem 1 rests on an undefined hypothesis ("shift-equivariant transfer").
  - The Theorem 4 error bound η is of first order in M, so it is vacuous at the certified level.
  - The Lemma 4 explanation of θ < 1 is a non sequitur.
  - Proposition 6 is cited but never stated.
  - Proposition 8 characterises only the ideal pivot, but the text sells it as a lower bound over all pivots.

All of these can be fixed, mostly by restating results rather than by new mathematics.

## 2. Recommendation and scores

**Recommendation: major revision.** No result is fatally wrong. However, the main theoretical selling points ("distribution-free zero-miss guarantee", "exact coupling inequality", "smallest valid score", "information limit") are each stated more strongly than what is proven.

| Criterion | Score (1–10) |
|---|---|
| Novelty | 6 |
| Soundness (of the formal statements) | 5 |
| Practical relevance | 7 |
| Clarity of the mathematics | 5 |

## 3. Verdict on every formal result

| # | Result (location) | Verdict | One-line reason |
|---|---|---|---|
| 1 | Marginal and PAC order-statistic rules and their coverage bounds (§4) | correct | Checked: P(U₍ₖ₎ ≥ 1−ε) = BinomCDF(k−1; n, 1−ε). Marginal bound is [1−ε, 1−ε+1/(n+1)]. Minimum n is 9 (marginal) and 22 (PAC). |
| 2 | Greedy planner optimality and monotone K(λ) (§3, A.2) | correct with gap | The exchange argument is standard. "Strictly monotone effective half-width" (A.2) is undefined, and the gap condition is never written down. |
| 3 | CE validity: deploy π(λ_ref) if q* ≤ λ_ref, else refuse (§4.1) | correct with gap | What is proven is P(deploy ∧ miss) ≤ ε. Under the marginal rule, P(miss \| deploy) = 1−F(λ_ref) can exceed ε. Only the PAC rule gives a conditional statement. The guarantee should be stated as such. |
| 4 | Lemma 1 (exact covering radius) | correct | The maximum of d(·,C) on [ℓ,u] is attained at the endpoints or at interior midpoints. It assumes closed footprints perpendicular to the working direction (no heading or hitch offset) and that misses are evaluated on the 1 m grid; both should be stated. |
| 5 | Lemma 2 (valid ⇒ S′ ≥ λ̄) | correct | One-line contradiction argument; valid as written. |
| 6 | Theorem 1 (S* = λ̄) | correct with gap / overclaimed | The hypothesis "shift-equivariant transfer" is never defined (§3 points to §5.2, which does not define it). For the greedy planner, changing λ changes K and the pass positions, so the hypothesis never holds exactly. The theorem then amounts to restating its assumption. |
| 7 | Corollary 1 (dominance under any order statistic) | correct given Theorem 1 | Monotonicity of order statistics is fine. Contribution 1 and the Abstract state it unconditionally. It does not cover CE+ (non-constant σ), as A.9 already notes. |
| 8 | Lemma 3 (union bounds are looser) | correct | I also checked the conformal version with k_j = ⌈(n+1)(1−ε/J)⌉; the inequality still holds. |
| 9 | Proposition 1 (nominal-plan calibration does not transfer) | correct with gap | A.6 is a heuristic. A non-existence claim needs a counterexample, e.g. i.i.d. pairs with K(λ̂) > K(0) give coverage near (1−ε)^{K₁/K₀} < 1−ε. "Natural pairing" is undefined. |
| 10 | Theorem 2 (multiplicative transfer) | correct at fixed t; gap at deployment | The coupling, hazard and extremal-index steps are all correct. The deployment step E[(1−F₀(λ̂))·c(λ̂)] ≤ ε·c(λ̂) is invalid because λ̂ is random (Major 3). |
| 11 | Proposition 2 (price of inflated reference) | correct with gap | The proof gives a/\|J(π₀)\|, not a/K. The expression for a uses w−2λ̂ where the derivation gives w−2λ₀. "At most 0.7%" relies on an estimated θ ≈ 0.5, and measured θ ranges over 0.30–0.66. |
| 12 | Proposition 3 (training-only gating) | correct | Standard argument; exchangeability given σ̂ holds. |
| 13 | Proposition 4 (conditional Gaussianity, gap variance ½λ₀) | correct with gap | (i) Independence of passes given C ignores state carried through the headland turn (integrator, OU slip, heading, steering). (ii) "Independent of the plan" is contradicted by B.1(a) (pass-specific f_k) and B.1(b) (A_t along a plan-dependent trajectory). (iii) The edge processes have variance λ₀, not ½λ₀. |
| 14 | Theorem 3(a) (Kac–Rice bound, discrete version) | correct | I checked the conditional slope mean and variance, Ψ, the stationary reduction L/(2π)·s′/s·e^{−u²/2}, and the discrete inclusion. Tail exactness (A.11) needs regularity conditions that should be stated, because Z′ contains OU slip and is not differentiable. |
| 15 | Theorem 3(b) (field-edge terms) | correct with gap | "Missed iff S_k > t for all passes covering it" is only "⊆" when the passes are restricted to those whose planned footprint covers b, since other passes can rescue the edge. The result is a conservative bound, not an identity. Using a union bound over 1 m sections is valid but can be loose. |
| 16 | Theorem 4 (Bonferroni sandwich) | correct but overclaimed in use | Both sandwiches and the bound by W are right. However, η = M²/2 + Σ min(μ_j, μ_{j+1}) ≈ M ≈ 0.10–0.11 at the certified level (computed for J = 10–50), which is the same size as ε. The text quotes only the M²/2 = 0.0055 term. |
| 17 | Lemma 4 (mixed representation) | correct | Follows by integrating Theorem 4 over C. |
| 18 | Lemma 4: θ_t < 1 "by Jensen", "because operating conditions differ" | incorrect reasoning | θ = (1−e^{−M})/M < 1 already for constant M (0.949 at M = 0.105). That is a property of the count conditioned on N ≥ 1, not clustering. Jensen only gives the stronger bound θ ≤ (1−e^{−EM})/EM. |
| 19 | Theorem 5 (decision-dependent transfer, "exact") | correct under its hypotheses; overclaimed | The coupling step is right. But (a) the hypotheses are violated by the L1 model actually used (Major 2); (b) the inclusion J(π₁) ⊆ J(π₀) must hold at the level of (pair, section) on non-rectangular fields; (c) the marginal deployment bound uses a random κ(λ̂). |
| 20 | Closed form κ ≤ exp(Δ̄(ū+1/ū)/s) | correct with gap | Monotone Gaussian hazard plus the Mills bound h(u) ≤ u+1/u (verified numerically). It assumes one Gaussian tail. For a mixture over C the bound is the supremum over C of the per-C bound, taken at the smallest s(C). u+1/u is increasing only for u ≥ 1, so "largest ū" is the correct choice only when all u ≥ 1. |
| 21 | Theorem 6 (Gumbel scale law) | sketch; overclaimed as a theorem | Inverting the Gumbel limit is correct. Leadbetter Thm 8.2.7 covers one stationary process; the extension to a maximum over K dependent pair processes plus edge processes of variance λ₀ is not proven. "Tenfold field ⇒ about 15%" is the a_N ratio (1.155). The margin ratio at m = 0 is 1.114. |
| 22 | Proposition 5 (CE-EVT-R validity) | correct for the score; deployment clause overclaimed | "S_new ≤ q̂_g v* ⇔ V_new ≤ v*" plus split conformal is fine, but it needs q̂_f > 0. "The miss guarantee for π_g follows by Theorem 5" gives κ·ε, not ε, and imports the Gaussian theory. The experiments deploy min(q_g t, cap), which the proposition does not cover. |
| 23 | Coverage given the calibration set ~ Beta(k, n+1−k) (§5.4) | correct | It is the population coverage H(v*), not the coverage of an individual field g. Standard deviation 0.0539 verified. |
| 24 | Proposition 6 (ratio vs PIT pivot) | overclaimed | Cited in §4.3 and §6.4 but never stated. B.4 calls it "heuristic, motivated post hoc". "Where it is most accurate" is unproven. |
| 25 | Proposition 7 (per-field test calibration) | correct | All numbers reproduced: 172 / 0.0434, 14.5%, 1.2%, δ+α = 14.3%. P(Bin(30, 0.143) ≥ 9) = 0.021. |
| 26 | Proposition 8 (ideal-scale inflation) | correct as an identity; overclaimed as an "information limit" | H(V₍ₖ₎) ~ Beta and λ_g/λ*_g = V₍ₖ₎ are fine. Nothing shows that other pivots cannot do better; the paper's own R3 PAC result has raw pooling beating the ideal pivot. A.19(ii) is asserted without proof. |
| 27 | Adjacent-pair correlation ρ = −½ r (A.13) | correct | Assumes equal single-pass variances, which fails under pass-specific f_k (minor). |
| 28 | §6.5 reading "between 1−ε and 1−ε+1/(n+1)" | correct but not sharp | The exact guarantee is ≥ k/(n+1) = 24/26 = 0.9231. Five marginal cells (0.9193–0.9214) lie 2–7 quoted standard errors below it. The quoted SE ignores the noise from the fixed fields and the 200-run banks. |

## 4. Major issues

**M1. "Distribution-free zero-miss guarantee" is claimed for plans whose guarantee is not distribution-free.**

- *Where:* the Abstract (CE+ "gives finite-sample, distribution-free zero-miss guarantees"); Contribution 4 ("validity does not depend on the theory"); §4.2 ("the guarantee holds for any fixed σ(·)"); §4.3 "Validity does not depend on the theory"; the last sentence of Proposition 5; §7.1 ("it holds independently of how accurate the theory is"); the Conclusion.
- *Why it fails:* conformal calibration certifies P(S_new ≤ λ̂) on the **reference plan** π(λ₀). By Lemma 1, that is the zero-miss event only for π(λ₀) itself, i.e. for CE. CE-q, CE+ and CE-EVT-R deploy π(λ̂) with λ̂ ≠ λ₀. For those plans the zero-miss probability is bounded only through Theorem 2 or Theorem 5, and the result is κ(λ̂)·ε with κ ≥ 1, not ε.
  - Theorem 2 needs h and H.
  - Theorem 5 needs the conditionally Gaussian, plan-independent-covariance model of L1, which is precisely "the theory".
  - The resampling check of §6.5 measures miss-freeness of deployed plans, so it supports the claim empirically, not formally.
- *Fix:*
  - Distinguish everywhere (a) the score-level guarantee, which is distribution-free, from (b) the deployed-plan zero-miss guarantee, which holds under the transfer assumptions with factor κ.
  - Rewrite the Abstract sentence along the lines of: "distribution-free guarantees on the reference plan, transferred to the deployed plan under an explicit coupling assumption."
  - In Proposition 5, replace "follows by Theorem 5" with the inequality P(miss) ≤ sup κ·ε, and list its hypotheses.
  - State plainly that only CE is assumption-free.

**M2. Theorem 5's hypotheses are inconsistent with the model the paper actually uses, so "exact" is overclaimed.**

- *Where:* §5.3 Theorem 5 ("with no approximation term"); Proposition 4 ("independent of the plan"); Contribution 2 ("an exact coupling inequality"); the Conclusion.
- *Why it fails:*
  - (a) The equal-covariance hypothesis rests on Proposition 4's plan-independence. That holds only for the time-invariant L1. The refinements adopted in §5.3 and B.1 make the covariance plan-dependent:
    - the observation-operator weight f_k depends on where the pass starts (B.1(a));
    - A_t is linearised along a noise-free trajectory over plan-dependent terrain (B.1(b));
    - the describing functions depend on the mean μ.
  - (b) theory_evt §1.4 states that saturation is triggered in 96% of DGPS conditions, so A1 fails in R3.
  - (c) Equality of each pair's covariance is not enough for the coupling Z^{(1)} = Z^{(0)} + shift. The whole joint law of all pairs and all sections must coincide after the mean shift.
  - (d) On non-rectangular fields, matched pairs of π₀ and π₁ span different section ranges. J(π₁) ⊆ J(π₀) therefore has to be an inclusion of (pair, section) index sets under an explicit pairing map, and that map is never defined.
  - (e) For the edge pseudo-pairs, the "mean" includes the geometric offset (y_k − w/2 − b), which differs between plans even on flat terrain. So Δ̄ = 0 on flat terrain is not automatic.
- *Fix:*
  - Restate Theorem 5 under the hypothesis that is actually needed: **superposition**. If e_k^{(1)} − e_k^{(0)} is a deterministic function of C for the coupled realisation (shared C and ξ_k), the pathwise inclusion follows directly. Gaussianity is then not needed at all.
  - Define the pairing map on (pair, section) and include the edge geometry in Δ(C).
  - Call the result exact *for the linear model*, and approximate (validated in Table S5) for the simulator.

**M3. The deployment corollaries of Theorems 2 and 5 use a random amplification factor.**

- *Where:* the Theorem 5 corollary ("P(miss) ≤ κ(λ̂)ε for the marginal rule"); A.7; A.15 "Deployment".
- *Why it fails:* under the marginal rule, P(miss) = E[1 − F_{π₁}(λ̂)] ≤ E[κ(λ̂)(1 − F_{π₀}(λ̂))]. This is not bounded by κ(λ̂)·ε, because κ(λ̂) is random and correlated with λ̂. The PAC version is fine, because it conditions on calibration.
- *Fix:* state P(miss) ≤ sup_{t ≤ λ₀} κ(t)·ε. If 1 − F_{π₀} is log-concave on the relevant range (κ is then non-decreasing), this becomes ≤ κ(λ₀)·ε on the event λ̂ ≤ λ₀. Make the same change in Theorem 2.

**M4. Theorem 1 rests on an undefined hypothesis, and the "smallest valid score" claim depends on it.**

- *Where:* the Abstract ("the smallest one that yields valid certificates"); Contribution 1; §3 (the shift-equivariance pointer); §5.1 Theorem 1; A.4.
- *Why it fails:* "shift-equivariant transfer" is never defined. Without it, S* is valid only at λ = λ_ref, and S* ≤ λ̄ does not follow, so Corollary 1 is unsupported. Under the greedy planner, K and the pass positions change with λ, so exact shift-equivariance never holds.
- *Fix:* define validity relative to the reference plan with a *virtual* erosion. Let M_ref(t, e) be the missed area of π(λ_ref) executed with footprint half-width w/2 − λ_ref + t. Then S* = inf{t : M_ref(t, e) = 0} holds exactly with no assumption, and Lemma 2, Theorem 1 and Corollary 1 go through verbatim. Alternatively, state the definition and admit the assumption.

**M5. The Theorem 4 error bound is vacuous at the operating point, and the text conceals this.**

- *Where:* §5.3 after Theorem 4 ("the first term of η is about 0.0055"); Lemma 4 (|ρ_π| ≤ E[η]); theory_evt §3 ("an order of magnitude smaller than ε").
- *Why it fails:* Σ_j min(μ_j, μ_{j+1}) is first order in M. With J homogeneous pairs it equals M(J−1)/J. At M = 0.105 this gives η ≈ 0.100, 0.105 and 0.108 for J = 10, 20 and 50 (my check). So η is as large as ε and gives no control of the product form. The product form's accuracy is supported only empirically (B.2).
- *Fix:* bound p_j directly. Under conditional Gaussianity it is a bivariate exceedance with same-section correlation −½, so it is O(μ²)-like up to a lag-dependent factor. Alternatively, compute Σ p_j by the Gaussian Monte Carlo already in L2 and report the realised η. At minimum, quote the full η value and say that the bound is vacuous at 0.9. Correct §7.3(3): the bound is loose even when the μ_j are small.

**M6. Proposition 8 is an identity for the ideal pivot, not an information limit for all pivots.**

- *Where:* Contribution 5; the §5.5 title; "no field-level prediction can remove"; §6.6 "Proposition 8 bounds what any field-level pivot can achieve"; §7.2 "a better pivot cannot"; A.19(ii).
- *Why it fails:* the proposition gives the distribution of λ_g/λ*_g under q_f = λ*_f only. For another pivot q, the deployed ratio is (q_g/λ*_g)·H_q^{-1}(B). Nothing proves that its distribution, or the excess overlap, is no better. The paper's own data contradict a lower-bound reading: in R3 PAC, raw pooling (+10.36 pp) beat the ideal pivot (+12.86 pp). A.19(ii) ("any other scale only adds between-field spread without changing the distribution of B") is asserted, not proven; the distribution of B is unchanged, but H changes.
- *Fix:* rename the result to "margin inflation under the ideal scale". Drop "bounds what any pivot can achieve", or prove a precise statement. For example, under the PAC rule with k = n and a common normalised shape Γ, every scale pivot has E_g[λ_g/λ*_g] ≥ … (with the conditions spelled out).

**M7. Proposition 4's independence of passes given C ignores state carried across passes.**

- *Where:* Proposition 4, A.10; it is used by Theorem 3(b) (product), Theorem 4 (independence of non-adjacent pairs) and Theorem 5.
- *Why it fails:* passes are driven consecutively. Integrator, OU slip, heading and steering states at the end of pass k are the initial state of pass k+1. Independent innovations do not make the passes independent unless the state is reset or decorrelates during the headland turn.
- *Fix:* add an explicit assumption (state reset, or a turn duration ≫ the closed-loop correlation time). Quantify the residual cross-pass correlation at the entry to W; W is inset 2w, so it is probably small. Alternatively, treat the initial state as part of C.

**M8. The algorithms and the experiments do not match the hypotheses of the theorems that certify them.**

- *Where and why:*
  - (a) Algorithm 2 (CE+) has no check that λ = t·σ(z_new) ≤ λ₀. If σ(z_new) is large, J(π₁) ⊄ J(π₀) and no transfer result applies. Algorithm 1 has the check.
  - (b) In CE+, λ depends on z_new, which is correlated with the test run's C. The κ factorisation of Theorem 5 is stated for a fixed plan. The pathwise coupling still works, but the bound becomes P(S_new > tσ(z_new) − Δ̄), not κ·ε.
  - (c) The experiments deploy min(q_g t, cap) (§6.5, C.4). Capping can reduce the margin below the conformal quantile, so Proposition 5 does not cover the method that was tested.
  - (d) λ < w/2 is needed for d > 0, but no refusal rule enforces it.
  - (e) Algorithm 1 line 4, "enlarge λ₀ and recalibrate": the guarantee after adaptive restarts, conditional on acceptance, needs the same P(deploy ∧ miss) caveat as in table row 3.
- *Fix:* add the λ ≤ λ₀ refusal to Algorithm 2. State the CE+ bound with a random threshold. Either remove the cap from the validity check or count any capped deployment as a potential failure. State the deploy/refuse semantics explicitly.

**M9. Results labelled as propositions or theorems are sketches or heuristics.**

- *Where:*
  - Proposition 6 is cited (§4.3, §6.4) but never stated; B.4 calls it heuristic.
  - Theorem 6 is a sketch (A.16): it applies a single-process theorem to a maximum over dependent pairs plus edge terms with variance λ₀ rather than ½λ₀. With edges included, the homogeneous-s Gumbel law can be dominated by the edge processes as N → ∞.
  - §5 says "complete proofs are in Appendix A", while Appendix A says that items marked "sketch" are not complete.
- *Fix:* relabel Proposition 6 as a "Remark (heuristic)". Restrict Theorem 6 to interior pairs with stated mixing conditions, or label it a conjecture/heuristic. Change the §5 sentence.

**M10. The extremal-index interpretation in Lemma 4 is a non sequitur.**

- *Where:* the §5.3 sentence after Lemma 4 ("By Jensen's inequality … θ_t < 1: exceedances cluster because operating conditions differ between runs, not because of local pair dependence"); A.14.
- *Why it fails:* the inequality θ = E[1−e^{−M}]/E[M] < 1 holds for any non-degenerate M, including a constant M (θ = 0.949 at M = 0.105), because 1−e^{−x} < x. It therefore cannot attribute clustering to heterogeneity across C. Jensen gives only θ ≤ (1−e^{−EM})/EM.
- *Fix:* state θ ≤ (1−e^{−E M})/E M, and say that heterogeneity in C lowers θ below the homogeneous value (1−e^{−M})/M. Separately, the Poisson approximation of N_t given C ignores the adjacent-pair dependence, so the claim "not because of local pair dependence" is unproven in any case.

## 5. Minor issues

1. **Notation clashes** (several are serious for readability):
   - λ₀ is both the reference erosion and the zeroth spectral moment (Proposition 4: "variance ½λ₀").
   - Ψ is both the generative map e_k = Ψ(C, φ_k, τ_k, ξ_k) and Ψ(a) = φ(a) + aΦ(a).
   - φ is both a terrain feature and the normal density.
   - T is the pair score T_j, the CE+ score T = S/σ(z), and the training set T in Algorithm 2.
   - M is both the missed area and Σμ_j.
   - S_k (single-pass edge process) clashes with the run score S and with S_i.
   - h is the coupling bound, h_ant, and the Gaussian hazard.
   - N is both the effective length and the count N_t.
   - δ is the PAC level, the steering angle and the scale error δ_f (B.4).
   - σ is the normalisation σ(z) and a standard deviation σ(x).
   - C is the set of centres in Lemma 1 and the operating condition.
   - ε is both the miss level and the GNSS error ε(τ) (A.15).
   - k is both the pass index and the order-statistic rank.
2. **Theorem 3(a):** "σ(x), σ′(x), r(x) the variance, slope variance and cross-covariance", but σ and σ′ are used as standard deviations in the formula.
3. **Proposition 2:**
   - The bound is ε·a/(\|J(π₀)\|·θ) (A.8), not ε·a/(Kθ).
   - a ≈ K·2(λ₀−λ̂)/(w−2λ₀) follows from K(λ) ∝ 1/(w−2λ) with K = K(λ̂); the text has w−2λ̂.
   - "At most" should read "approximately at most", because θ is estimated and the measured θ ranges over 0.30–0.66.
4. **Theorem 6 comment:** "a tenfold larger field raises it by about 15%" is the ratio of a_N alone (1.155). The ratio of t_ε/s at m = 0 is 1.114, i.e. about 11%.
5. **κ closed form:** say "u ≥ 1" or replace ū + 1/ū by max over the relevant u of (u + 1/u). Under a mixture over C, use the supremum over C.
6. **§6.5:** report the exact targets the theory gives:
   - marginal mean coverage ≥ k/(n+1) = 0.9231;
   - P(cov ≥ 0.9) for the marginal rule = 0.729 (Beta(24,2));
   - P(cov ≥ 0.9) for the PAC rule = 0.928 (Beta(25,1)).

   The observed values (0.689–0.767 and 0.911–0.949) agree well with the last two, and saying so would strengthen the check. Then explain why the marginal means sit 0.002–0.004 below 0.9231 (possible causes: finite banks, curve interpolation, the cap).
7. **§5.4 "the coverage of a new field is a draw from Beta(k, n+1−k)":** this is the population-averaged coverage H(v*) given the calibration set. A single field's coverage G_g(q_g v*) is not Beta-distributed.
8. **Proposition 5:**
   - Require q̂_f ∈ (0, ∞].
   - With the +∞ rule, ties at +∞ occur; the marginal bound still holds, but say so.
   - The PAC (training-conditional) statement needs i.i.d. fields. The resampling check samples without replacement from 45 fixed fields, which is exchangeable but not i.i.d.
9. **Theorem 3(b) and A.12:** replace "iff" by "⊆" (as in M-table row 15). State that the union over sections makes the edge term an upper bound.
10. **Lemma 1:** add "evaluated on the 1 m grid" and "footprint perpendicular to the working direction (no heading or hitch offset)". Misses between grid sections are not certified.
11. **A.11:** state the regularity conditions for Rice tail exactness (e.g. the Geman condition or a finite second factorial moment). The slope contains an OU component, so Z is C¹ but not C².
12. **A.15 / Theorem 5:** the mean-shift bound "under A1 with integral action" ignores the transient after each headland turn, where the integral action has not yet removed the slip bias.
13. **A.2:** "Under a strictly monotone effective half-width" is unclear; define the gap condition (consecutive spacing ≤ w − 2λ, extreme chords covered).
14. **Proposition 4:** after B.1(a), the per-pass variances differ (f_k), so "gap variance ½λ₀" and the adjacent-pair correlation ρ = −½ hold only approximately.
15. **§5.2:** T_j is defined "over the main area" as a pair difference, but after Theorem 3(b) the edge pseudo-pairs are minima of single-pass processes over overlap bands, not differences. Unify the definition of U_π.
16. **Missing number and source reference:** Proposition 6 is missing from the main-text sequence (Propositions 1–5, 7, 8 are stated). The HTML comment above Table 4 cites "Theorem 2.4" (an internal numbering) instead of Theorem 3(b).
17. **A.15 parenthetical** ("replaces an earlier sketch … with a sign error"): this belongs in the response letter, not in the proof.
18. **§4 marginal upper bound:** the bound 1−ε+1/(n+1) requires almost surely distinct scores. Scores rounded to the 2 mm grid (CE+) can tie, so the text should note this.

## 6. Questions to the authors

1. What exactly is "shift-equivariant transfer" (Theorem 1)? Does any planner–execution pair used in the paper satisfy it?
2. In Theorem 5, how are the pairs of π₁ mapped to pairs of π₀ on a non-rectangular field, where chords have different x-extents? Is the inclusion checked at the level of (pair, section)?
3. Is the covariance of the L1 model used to produce F̂ (time-varying, with observation operator and clamp model) plan-independent? If not, which version of Theorem 5 certifies CE-q and CE+ in R3, where A1 fails in 96% of conditions?
4. How large is the cross-pass correlation of e_k at the entry to W caused by the integrator and OU slip state carried through the headland turn?
5. What is the realised value of η(t | C), with Σ p_j computed by Gaussian Monte Carlo, at the certified level in R1–R3?
6. In the resampling check, how many deployments were capped? Does the guarantee still hold if every capped deployment is scored as a miss?
7. CE+ has no λ ≤ λ₀ check. How often did t·σ(z_new) exceed λ₀ in v8?
8. Do you claim any lower bound over *all* field-level pivots, as §6.6 and §7.2 imply? If so, what is the precise statement and proof?
9. Theorem 6: with edge processes of variance λ₀, which term dominates the Gumbel asymptotics, and does the scale law √(2 log N_f) still apply to the exact score?

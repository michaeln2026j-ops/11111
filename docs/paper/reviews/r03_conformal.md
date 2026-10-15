# Review R03: conformal prediction theory

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (Computers and Electronics in Agriculture)

**Reviewer expertise:** conformal prediction theory, including:
- split and full conformal prediction;
- training-conditional (PAC) guarantees;
- exchangeability;
- hierarchical (two-layer) conformal prediction;
- covariate shift;
- conformal risk control.

**Material examined:**
- `docs/paper/manuscript.md`, `docs/paper/supplementary.md` (Appendix A proofs in full) and the figures in `figures/paper/`;
- the code paths behind the validity claims: `experiments/ceplus.py`, `experiments/exp_lowdata.py`, `experiments/evt_theory.py`, `scripts/validity_resample.py`, `scripts/analyze_lowdata_v3.py`;
- the result files `results/v8/system_v8.csv`, `results/lowdata_v2/`, `results/lowdata_v3/`.

All quantities marked "reviewer check" below come from short read-only scripts on the cached result files: 400 resampling replicates and the existing run banks and margin curves. No simulations were rerun.

---

## 1. Summary of the paper

The paper treats agricultural coverage planning under path-tracking error as a chance constraint: a plan must leave no unworked strip with probability at least 1−ε.

**Score and CE+.** The authors show that the zero-miss event of a fixed executed plan equals the event that a scalar run score, the covering-radius excess over 1 m sections, lies below the planned margin. They calibrate this score with split conformal quantiles, marginal or PAC, on runs logged at an inflated "reference" plan, and then deploy a re-planned, eroded plan. The extended variant CE+ normalises the score by a probe-line cross-track statistic. Transfer from the reference plan to the deployed plan is justified by a coupling inequality (Theorems 2 and 5).

**CE-EVT-R.** For fields with no history, the authors build a five-layer Gaussian extreme-value approximation of the run-score distribution. They use its predicted (1−ε) quantile only as a ratio pivot for cross-field split conformal calibration with one historical run per field. Validity is argued from exchangeability of fields (Proposition 5).

**Experiments.** Everything is simulated: closed-loop runs driven by real field boundaries, DEMs and CORS GNSS error series. There is a pre-registered system comparison (v8), three pre-registered zero-data experiments (E-low v1–v3) and a pre-registered resampling check of the cross-field guarantee.

---

## 2. Recommendation

**Major revision.**

| Criterion | Score (1–10) |
|---|---|
| (a) Novelty | 6 |
| (b) Technical soundness | 4 |
| (c) Practical relevance | 5 |
| (d) Clarity | 5 |

**Why major revision.** The conformal core is used correctly as a quantile rule, and I verified the order-statistic indices and the Beta/binomial numbers. The pre-registration discipline and the honesty about failed claims are exemplary.

However, the paper's headline promise is a "finite-sample, distribution-free zero-miss guarantee", including for "fields without any operation history". It does not hold for the procedures as implemented and evaluated, for four reasons:

1. **Reference-plan dominance is not enforced.** In a large share of deployments the deployed plan has more passes than the calibrated reference plan. This is the situation the paper itself (Proposition 1) says carries no guarantee.
2. **Transfer is model-based.** The transfer from reference plan to deployed plan rests on a Gaussian model, not on exchangeability.
3. **The cross-field certificate is population-marginal, not field- or configuration-conditional.** In the mixed fleet this hides severe under-coverage of the DGPS sub-fleet.
4. **The resampling "confirmation" cannot fail under its own design.** It splits a fixed finite pool at random, so exchangeability holds by construction, and it differs from the stated algorithm in its +∞ and cap handling.

These issues are fixable, mostly by enforcing what the paper already says, reporting conditional coverage and restating claims. But they change what the paper may claim.

---

## 3. Strengths

**Score construction.**
- The reduction of the zero-miss event of a fixed executed plan to a scalar covering-radius score (Lemma 1) is clean and useful.
- It separates field-edge terms from interior terms, and the physical explanation of edge-concentrated misses under DGPS is a genuine insight.

**Correct conformal mechanics.**
- I verified the marginal index k = ⌈(n+1)(1−ε)⌉ (n = 9, 25, 29, 100 → k = 9, 24, 27, 91).
- The PAC index is the smallest k with BinomCDF(k−1; n, 1−ε) ≥ 1−δ (n = 22, 25, 29, 100 → k = 22, 25, 29, 95). This is the correct inversion of F(S₍ₖ₎) ~ Beta(k, n+1−k).
- I recomputed the Proposition 7 numbers exactly: 0.043, 14.5% and 1.2%. The threshold for declaring a PAC method invalid (9 or more failing fields) has P ≈ 0.021 under the δ+α bound.
- I also confirmed Beta(27, 3): standard deviation 0.054, 5% quantile 0.798.

**Within-class comparisons.**
- The insistence on comparing within a guarantee class (marginal vs marginal, PAC vs PAC; Section 5.1) is correct and too often ignored.
- So is the remark that the scenario approach applied to a scalar score is the PAC conformal rule.

**Correct location of the pivot's role.**
- The ratio-pivot idea is a legitimate instance of normalised split conformal across groups.
- The paper correctly states that validity cannot depend on the pivot and that the pivot affects only efficiency (Section 4.3).

**Reporting discipline.**
- Failed and partly met pre-registered claims are reported transparently: E-low v1 failed, C3 and C4 were not met.
- The post hoc matched-coverage analysis correctly identifies that "efficiency gains" at a single calibration draw were largely realised-coverage luck.
- This is a model of good practice.

**Information-limit argument.** Proposition 8 is a useful heuristic: under an ideal scale, PAC inflation is a within-field tail-ratio phenomenon that no field-level pivot can remove.

---

## 4. Major issues

### M1. The dominance condition λ_deployed ≤ λ₀ is stated but not enforced, and is violated in most R3 deployments

**Location:**
- Algorithm 1 line 4 (refuse if λ̂ > λ₀);
- Algorithm 2 (no such check);
- Algorithm 3 (no such check);
- Proposition 5, last sentence ("follows by Theorem 5 when q̂_g v* ≤ λ₀");
- Section 1, point (i);
- Proposition 1;
- code: `experiments/ceplus.py` (`dominated` flag computed but not acted on) and `scripts/validity_resample.py`, line 87.

**The problem.** The paper's argument against existing conformal planners (Introduction (i), Proposition 1) is that calibrating on a plan with fewer pass pairs than the deployed plan voids the guarantee. Accordingly, Algorithm 1 refuses when λ̂ > λ₀. But CE+ and CE-EVT-R deploy regardless.

Reviewer checks on the existing results:
- **v8 confirmatory run (BCD + LQR-I stack).** CE+ deployed an erosion above λ₀ on 9 of 30 R3 fields (marginal) and 19 of 30 (PAC). This is the q_cert > lam_ref column of `results/v8/system_v8.csv`. The `dominated` flag is False on 57% (marginal) and 80% (PAC) of R1 fields, because high-z days scale λ above λ₀.
- **Resampling check (Table 7), share of deployments with λ_g > λ₀:**
  - R3: 55–59% marginal, 82–85% PAC;
  - R2 PAC: 31–35%;
  - mixed fleet, theory pivot: 22% marginal, 57% PAC.

**Why it matters.** For those deployments the paper's own theory provides no guarantee. Proposition 5's guarantee concerns S at the reference plan; Theorem 5 requires J(π₁) ⊆ J(π₀). The empirical coverage happens to be fine in simulation, but that is a property of this simulator, not a distribution-free result. The paper commits exactly the error it criticises in Lindemann et al. and Zhao et al.

A related problem: the reference erosion λ₀ = 1.25 × the largest training quantile is supposed to guarantee dominance (Proposition 2). In R3 the theory's own q̂_f/λ₀ ranges up to 1.15, so the inflation factor is not sufficient there.

**Fix:**
1. Enforce refusal, or recalibration on fresh runs at a larger λ₀, whenever the deployed λ exceeds λ₀. Do this in all three algorithms and in all evaluations.
2. Report the refusal rate as a cost.
3. Alternatively, choose λ₀ per field from the theory, e.g. λ₀ = c · q̂_f with c tuned on training fields, so that dominance holds with high probability. This is a field-measurable choice and keeps Proposition 5 intact.
4. Re-run Table 5 and Table 7 under the enforced rule, or at minimum report results separately for dominated and non-dominated deployments.

### M2. The guarantee on the deployed plan is not distribution-free

**Location:** Abstract ("finite-sample, distribution-free zero-miss guarantees"), Contribution 2 ("exact coupling inequality"), Theorem 2, Theorem 5, Section 8.

**The problem.** Only CE, which deploys the reference plan itself, is distribution-free (Section 4.1). CE-q, CE+ and CE-EVT-R deploy π(λ̂) ≠ π(λ₀). Their miss guarantee is κ(λ̂)·ε, which rests on several model assumptions:
- **Theorem 5** assumes conditional Gaussianity and an equal covariance of matched gap processes across plans (Proposition 4).
- **The simulator violates these assumptions.** The time-varying quasi-linearisation of Supplementary B.1(b) makes the covariance depend on the terrain each pass traverses, so it is plan-dependent on hilly fields (R2, R3). Saturation and rate limits are non-Gaussian. B.1 itself concedes that nearest-neighbour terrain sampling makes the conditional law non-Gaussian at high slip.
- **Theorem 2** needs a hazard-rate bound H and a finite-threshold extremal index θ_t. Neither is known distribution-free.
- **No experiment reports κ.** κ is never computed or reported for any experimental field, so the reader cannot tell whether the deployed guarantee is 0.9 or, say, 0.85.

**Why it matters.** "Distribution-free" is the principal selling point and a term of art with a precise meaning. Using it for a model-dependent bound is a correctness issue, not a wording issue.

**Fix:**
1. Restrict "distribution-free" to (a) CE deploying π(λ₀) and (b) statements about S at the reference plan.
2. For the deployed plan, write "valid under the transfer conditions of Theorem 5", or better, report the computed κ̂(λ̂) per field and regime, together with the implied miss bound κ̂ε.
3. Alternatively, obtain a genuinely distribution-free deployed guarantee by calibrating on the plan that will be deployed. For example, use a small grid of candidate erosions with Learn-then-Test (Angelopoulos et al., 2025) and fixed-sequence testing over the monotone family π(λ). This controls P(miss of the selected deployed plan) without transfer assumptions. The authors cite LTT but do not use it, and this is precisely its use case.

### M3. Optimality of the exact score (Theorem 1, Corollary 1) is overstated; the definitions mix plans

**Location:** Abstract, Highlights 1, Contribution 1, Section 5.1 (definition of λ̄(e) and of validity), Theorem 1, Appendix A.4.

**The problem.**
- **Definitions mix plans.** λ̄(e) = inf{λ : M(λ, e) = 0} and the validity condition "for all λ, e" treat e as a single error realisation that is meaningful for every plan π(λ). But e is the execution error of a specific plan. Different λ give different pass counts, positions, traversal times and therefore different error processes. The definition only makes sense under a coupling across plans, which is never formalised in Section 5.1.
- **Theorem 1 holds only in an unrealised case.** It assumes "shift-equivariant transfer". The greedy planner is not shift-equivariant, because K(λ) is a step function, and Section 3 admits this.
- **The honest statement is weaker.** For the fixed reference plan, S* is the exact (minimal) score for the event {no miss at π(λ_ref)}.
- **The headline claim is too strong.** "No order-statistic rule applied to another valid score deploys fewer passes" (Contribution 1) is true only within the coupled, shift-equivariant idealisation. It also fails for CE+, whose normalised score T = S/σ(z) breaks pointwise dominance, as A.9 concedes.

**Fix:**
1. Define the plan family and the coupling explicitly, e.g. via the generative structure e_k = Ψ(C, φ_k, τ_k, ξ_k) with shared (C, ξ).
2. State Theorem 1 at the reference plan.
3. Downgrade the abstract and highlight wording from "the tightest valid one" to "exact for the calibrated plan".

### M4. The cross-field certificate is marginal over fields; per-field and per-configuration coverage are not guaranteed, and in the mixed fleet the DGPS sub-fleet is badly under-covered by a "valid" method

**Location:** Abstract ("Fields without history are certified"), Highlights 4–5, Proposition 5, Section 6.5, Table 7, Section 6.6, Table 8, Limitation 4.

**The problem.** Proposition 5 gives

P_{fields, calibration runs, new run}(S_new ≤ q̂_g v*) ≥ 1−ε.

This averages over which field is new. It says nothing about a given field g, nor about a sub-population such as one machine configuration. Section 5.4 makes things worse by saying "the coverage of a new field is a draw from Beta(k, n+1−k)". The Beta law describes the field-averaged conditional coverage H(v*) as a function of the calibration set. It describes neither the coverage of a given field, G_g(q̂_g v*), nor any per-field quantity.

**Reviewer check (mixed fleet, 400 resampling replicates, mean coverage of test fields by configuration):**

| Pivot | Rule | R1 | R2 | R3 |
|---|---|---|---|---|
| Raw pooling | marginal | 0.999 | 0.998 | **0.777** |
| Raw pooling | PAC | 0.999 | 0.999 | **0.873** |
| Theory | marginal | 0.935 | 0.939 | 0.907 |
| Theory | PAC | 0.973 | 0.976 | 0.946 |

Raw pooling is reported as "valid" in Table 7 and Fig. 4, yet a contractor running the DGPS machine receives about 78% zero-miss probability under a nominal 90% certificate. The headline efficiency comparison (29.8 → 3.0 pp) is therefore partly a comparison against a method that over-covers RTK fields and under-covers DGPS fields.

**Why it matters.** A practitioner reads "field certified at 90%" as a per-field or per-machine statement. The population-marginal nature must be explicit. The obvious remedy, Mondrian (group-conditional) conformal by configuration, is missing as a baseline.

**Fix:**
1. Report coverage conditional on configuration (and, ideally, the distribution of per-field coverage G_g(λ_g)) in Tables 7–8 and Fig. 4.
2. Add Mondrian conformal by configuration as a comparator in the mixed fleet. It is valid per configuration, but with 25 calibration fields shared by three configurations it may hit the n ≥ 9 / n ≥ 22 floors, which would itself be an argument for the theory pivot.
3. Rewrite Section 5.4 so that the Beta statement refers to H(v*), the coverage averaged over a new random field, conditional on calibration data.
4. Replace "Fields without history are certified" in the abstract and highlights by an explicit population-level wording.

### M5. The pre-registered resampling check cannot detect failure of the actual assumption, implements a different procedure, and uses a weak one-sided criterion

**Location:** Section 6.5, Table 7, Fig. 4, Highlight 4, `scripts/validity_resample.py`.

**Exchangeability holds by construction.** Each replicate randomly permutes a fixed pool of 45 (or 135) simulated fields into 25 calibration and 20 test fields, and draws historical runs i.i.d. from per-field banks. Under such a random split, (V₁, …, V_n, V_new) is exchangeable for any pivot. The check therefore verifies arithmetic and code, which is worth doing, but it cannot test Proposition 5's substantive assumption. The text acknowledges this ("tests the guarantee and its implementation"). Even so, the abstract and highlights present "held in 26 of 26 checks" as evidence that the guarantee holds. It is not evidence about real fleets.

**The implementation differs from the stated method.**
- Line 87 of `validity_resample.py` deploys `r["cap"]` (0.4w) whenever q·t is non-finite. The stated +∞ rule instead refuses and counts the field as a failure.
- Finite deployments are truncated at the same cap, min(q·t, cap). Algorithm 3 has no cap, and truncation can only lower coverage relative to the stated rule.
- In the v2/v3 data every theory CDF is finite (reviewer check: 0 of 135 fields not "ok"), so the substitution happens not to matter here. But the reported procedure is not the evaluated one.

**The criterion is one-sided and loose, while the sharp prediction goes untested.** With continuous scores and an exact random split, the marginal rule has expected coverage exactly k/(n+1) = 24/26 = 0.923 at the reference plan. The PAC rule with k = n = 25 has P(coverage ≥ 0.9) = 1 − 0.9²⁵ = 0.928. The observed values deviate measurably:
- R1 marginal: 0.9193 against 0.9231, i.e. 5–7 of the reported standard errors.
- R1 PAC: 0.911 against 0.928, about 4 standard errors.
- R2 PAC: 0.946–0.949.

These deviations measure the transfer loss of re-planning (M1, M2) and the Monte Carlo error of the margin curves. They are the informative part of the check and are hidden by a ≥ 0.895 / ≥ 0.88 pass rule. Moreover, the reported standard errors (0.0005–0.0008) capture only replicate variation. The margin curves (200 runs per point, common random numbers) are shared across all 4000 replicates, so their Monte Carlo error is not included.

**Fix:**
1. Report the exact expected values (k/(n+1); 1 − (1−ε)ⁿ for k = n) and two-sided deviations, with standard errors that include curve noise, e.g. a bootstrap over the curve runs.
2. Decompose coverage at the reference plan (pure conformal, should match k/(n+1)) from coverage after re-planning (transfer).
3. Make the evaluated rule identical to Algorithm 3: refusal as failure, explicit cap rule.
4. Most importantly, add stress tests that break exchangeability in realistic ways:
   - calibration on two configurations and test on the third;
   - calibration fields from one region or season and targets from another;
   - spatially clustered splits;
   - **shared-day dependence (see M6).**
5. Report how far coverage degrades, and consider the robust bound of Barber et al. (2023) or weighted conformal prediction (Tibshirani et al., 2019) with field-level covariates.

### M6. The independence and exchangeability assumptions behind "one run per field" are unrealistic in ways the simulation cannot reveal

**Location:** Sections 4.3, 5.4, 6.1 (each run draws an independent station-pair-day), Limitation 4.

**Shared operating conditions across fields.** In practice a farm or contractor works several fields on the same day, with the same GNSS conditions (ionosphere, correction-service outages, same base station), the same machine, mounting bias and soil-moisture regime. The run-level condition C is then shared across calibration fields and possibly with the target field. That makes V₁, …, V_n dependent, so they are not exchangeable with V_new conditional on the shared day.
- The marginal guarantee can survive if the target run is also exchangeable with the shared structure.
- The PAC guarantee, a Binomial argument over n independent units, does not survive: the effective sample size is the number of distinct days, not fields. Under DGPS, where the paper shows GNSS error dominates, this is first-order.

**Historical runs were not executed on the reference plan.** Proposition 5 needs one run per calibration field at π_f(λ₀). Real historical operations were executed with whatever overlap the farmer used. Computing S at π_f(λ₀) from a run executed on another plan requires the very transfer that M1 and M2 question. "Fields without any operation history" are certified only if the calibration fields' histories were recorded on the specific reference plans, which no existing farm data satisfy.

**Selecting one run among several.** The text says farms hold "one or two operations" per field, but the method uses one. If several exist, how is the one selected? The choice must not depend on the scores. Dunn et al. (2023) give valid procedures that use all within-group samples (subsampling, pooled-CDF/"double conformal"); these should be used or at least discussed.

**Temporal shift.** Calibration runs are past and target runs future. Receiver firmware, constellation, correction service and controller tuning drift over time. This is a covariate or label shift between calibration and test that the i.i.d.-fields assumption hides.

**Fix:**
1. Add a simulation in which calibration runs share days (clustered C) and report PAC coverage. Propose a cluster-level conformal rule (one pivot per day-cluster) if it fails.
2. State explicitly that historical data must be logged on reference plans.
3. Discuss selection among multiple runs and Dunn et al.'s multi-sample methods.
4. Expand Limitation 4 accordingly.

### M7. The theory pivot is the simulator's own model with noise switched off (inverse crime); the efficiency and accuracy claims for it are not transferable

**Location:** Abstract ("1.7–3.7 times more accurately than data-driven regressors"; "29.8 to 3.0 pp"), Section 6.2, Section 6.6, Tables 8–9, Figs. 2, 6.

**The problem.** `evt_theory.predict_cdf` draws its operating conditions from `exp_system.make_cond`, the simulator's own condition generator (same GNSS series pool, soil-moisture, slip, roll and mounting-bias laws). It then propagates the simulator's own closed-loop model (`core.simulate` with a zero-noise RNG). The "theory" is therefore a semi-analytic emulator of the data-generating process, given the exact generative distribution.

Consequences:
- A log error of 0.029–0.056 for λ*_f, and its superiority over one-run regressors that see only noisy single scores, is what one would expect from such an emulator.
- It says little about accuracy on a real tractor, whose controller, slip and GNSS laws are unknown and must be estimated.

This does not affect validity (Proposition 5 is pivot-agnostic, as the authors correctly stress). It does affect every efficiency claim for CE-EVT-R, including the mixed-fleet headline.

**Fix:**
1. Evaluate the theory with misspecified inputs. Examples: a condition distribution estimated from training fields only; GNSS statistics from different stations or years than those that drive the runs; controller parameters perturbed by realistic identification error; a simulator variant with physics the theory does not model.
2. Report how the excess-overlap advantage in Table 8 degrades.
3. Until then, temper the abstract and highlights.

### M8. Proposition 8 is not an "information limit"

**Location:** Section 5.5, Section 6.6 ("The information limit"), Fig. 7, Contribution 5, Section 7.2.

**The problem.** Proposition 8 characterises the distribution of λ_g/λ*_g for one specific procedure, ratio pivot with the ideal scale q_f = λ*_f. It is not a lower bound over procedures. The paper's own data contradict the "limit" reading: raw pooling beats the ideal pivot in R2 marginal and R3 PAC (Table S12).
- A limit statement would need a minimax or Bayes lower bound over all procedures that are valid for a class of populations, using one run per field. For example: any procedure with P(H(v*) ≥ 1−ε) ≥ 1−δ for all populations whose normalised shapes are in a class must have E[λ_g/λ*_g] ≥ ….
- The identity H(1) = 1−ε also requires continuity of G_f at λ*_f.

**Fig. 7 has little evidential value.** The prediction intervals are so wide (R3: 1.85 ± 0.74) that "all observations lie within one predicted standard deviation" is uninformative. Each observation is also a single calibration draw.

**Fix:**
- Either prove a lower bound, or rename the result, e.g. "inflation under the ideal scale pivot", and remove "no field-level prediction can remove" unless qualified by "within the class of ratio pivots with common normalised shape".
- For Fig. 7, compare observed and predicted over the resampling replicates rather than one draw.

### M9. The +∞ rule is valid but needlessly fragile, and interacts badly with PAC at k = n

**Location:** Section 4.3, Algorithm 3, Section 6.4 (E-low v1 R3: PAC deployed on none of 31 fields).

**The problem.** With n = 29 or 25 and ε = δ = 0.1, the PAC index is k = n, the sample maximum. A single calibration field with a non-finite theory CDF therefore sets v* = +∞ and blocks every target. The marginal rule (k = 27 of 29) is blocked by three such fields.

A better valid rule exists. The event A_f = {F̂_f finite} is field-measurable and independent of runs. Conditioning on it preserves exchangeability among fields in A: they are i.i.d. from the conditional population. One may therefore:
- drop bad calibration fields;
- refuse targets that are bad;
- claim the guarantee for the sub-population {A}.

This loses nothing in validity and avoids global blocking.

**Fix.** Adopt or discuss the conditional rule. Report the refusal rate. Make the evaluation code consistent with whichever rule is stated (see M5).

### M10. The calibration budgets evaluated are unrealistic for the stated use case

**Location:** Section 6.1 ("calibrated on 100 runs per field"), Table 5, Section 7.4, Introduction point (iii).

**The problem.** The introduction stresses that "a field is worked a few times per year" and that PAC needs n ≥ 22. Yet the confirmatory v8 comparison calibrates CE+ on 100 runs per target field, decades of operations. At realistic n (22–30), PAC uses the sample maximum, and the relative ranking against CPP and Lindemann, and the overlap levels, may differ substantially. Within-field runs over years are also unlikely to be exchangeable (see M6).

**Fix.** Re-run, or at least report, the v8 comparison at n ∈ {9, 22, 30} with fresh calibration draws. Discuss within-field temporal non-exchangeability.

---

## 5. Minor issues

**Theory and proofs**
- **Section 5.3, L4, Theorem 5, "exact form, with no approximation term".** The result is exact only within the Gaussian model. Remove "exact" or qualify it.
- **Section 5.3, Theorem 4.** The second term of η, Σ_j min(μ_j, μ_{j+1}), can be of order M ≈ 0.1 at the certified level. The sandwich can then be nearly vacuous; only the first term (0.0055) is quoted. Report the full η at the operating point.
- **Section 4 preamble.** The marginal upper bound 1−ε+1/(n+1) holds at the reference plan for continuous scores. Section 6.5 applies it to coverage of the re-planned deployment, where it need not hold.
- **Section 4.2 / Proposition 3.** The training-only gate and λ₀ are fine for validity. But σ(z) = max(a+bz, 0.3σ̄) must be strictly positive and fixed before calibration; please say how σ̄ is defined (training-only?).
- **Proposition 6** is cited in the main text but appears only in Supplementary B.4, labelled "heuristic". Do not call a heuristic a proposition, or move it.
- **Proposition 1 / A.6.** "No distribution-free statement transfers" is informal. A two-line counterexample would make it a result.
- **Theorem 2.** It needs absolute continuity of the pair-score distribution for the hazard-rate argument. State this.
- **Lemma 3 / A.5.** The count "at most nε/J exceedances" ignores the (n+1) correction and the ceiling. State it for empirical quantiles or adjust.
- **Lemma 1.** The guarantee is for misses on the 1 m evaluation grid, not on the continuous field. Say so in the formulation and in the abstract.

**Statistical reporting**
- **Section 5.4.** "At n = 29 and k = 27 this has standard deviation about 0.054" is correct for Beta(27, 3). The interpretation is wrong (see M4).
- **Section 6.3 / Table 5.** "Not significantly below 0.9 (p 0.70, 0.98, 0.29)" is non-rejection, not evidence of validity. Report the power, or a confidence interval for pooled coverage. R3 marginal pooled P = 0.896 is below target.
- **E-low v2 Holm–Wilcoxon tests.** Test fields share 28 of 29 calibration fields, so the per-field differences are strongly dependent and Wilcoxon p-values are anti-conservative. The paper notes the analogous issue for validity (Section 6.4) but not for efficiency tests.
- **Table 7 caption.** The quoted standard errors exclude margin-curve noise (see M5).
- **Section 6.5.** The registered PAC tolerance (1−δ−0.02) has no stated derivation. With 4000 replicates the binomial SE is about 0.004, so a 0.02 tolerance is loose.

**Wording, numbering and presentation**
- **Abstract and Highlight 2.** "4.0–54.7% less overlap" mixes main-area overlap and different comparators. Give regret in pp as well, since relative overlap is diluted in R2 (acknowledged in Section 6.3).
- **Fig. 4.** In the left panel the dashed line is drawn at 0.9 while the registered criterion is 0.895. Draw the expected value k/(n+1) = 0.923 instead or in addition.
- **Section 2.** Conformal risk control is cited but not used. Controlling the expected missed area (CRC) is arguably more agronomically relevant than the zero-miss event, and is distribution-free for monotone losses in λ. Please discuss why zero-miss was chosen.
- **Section 2.** Mondrian / group-conditional conformal prediction (Vovk et al.) and multi-group or conditional coverage work (e.g. Gibbs, Cherian and Candès, conformal prediction with conditional guarantees) are directly relevant to M4 and should be cited.
- **Section 7.4.** "With at least 22 recorded operations on a field … use CE+" needs a caveat: at n = 22 the PAC rule deploys the sample maximum.
- **Numbering.** Proposition numbering in the main text skips 6, and the numbering map in Supplementary Appendix E is internal.
- **Submission readiness.** Appendix E ("remove before submission"), the TODO in Section 6.7 and the TODO in Data availability must be removed or completed.
- **Reproducibility.** The RTKLIB demo5 commit was "not recorded", and pre-registration is by git timestamp only. Archive with a DOI and an external registry.
- **Section 4.4 / Algorithm 2 line 1.** Training fields use 40 runs each. State this budget alongside "budget-matched" in Section 4.2.

---

## 6. Questions to the authors

1. **Dominance.** For each experiment, what fraction of deployments had λ_deployed > λ₀? What happens to Table 5 and Table 7 if those deployments are refused, or recalibrated at a larger λ₀ as Algorithm 1 prescribes?
2. **κ in practice.** What is the computed κ̂(λ̂) of Theorem 5 on the v8 and E-low fields, and what deployed miss bound κ̂ε does it imply? On how many fields is κ̂ε > 0.1 materially?
3. **Coverage by configuration.** In the mixed fleet, what is the coverage conditional on configuration for each pivot? Did you consider Mondrian conformal by configuration?
4. **Shared days.** How does PAC coverage behave when calibration runs on different fields share the same day or GNSS condition C (cluster dependence)? Is the effective sample size the number of fields or the number of days?
5. **Logging on reference plans.** How would a farm obtain historical runs on the reference plan π_f(λ₀)? If historical runs come from other plans, which transfer assumption is used to compute S at π_f(λ₀), and how does validity degrade?
6. **Misspecified theory.** How does CE-EVT-R's efficiency advantage change when the theory is fed a condition distribution, GNSS statistics or controller parameters that differ from the simulator's?
7. **Implementation consistency.** Why does `validity_resample.py` deploy the cap on a non-finite threshold instead of refusing, and how often was the cap binding in any experiment?
8. **Learn-then-Test.** Have you considered LTT with fixed-sequence testing over the monotone plan family to obtain a distribution-free guarantee on the deployed plan, removing the need for Theorems 2 and 5?
9. **Matching the exact expected coverage.** Can you report the resampling-check coverage at the reference plan (pure conformal, before re-planning) and show that it matches k/(n+1) = 0.923 within Monte Carlo error? The gap to the re-planned coverage would then quantify the transfer effect directly.
10. **Information limit.** Is there a lower bound that justifies the term? Over what class of procedures is the ideal ratio pivot optimal?
11. **Zero-miss versus missed area.** Why is the zero-miss event preferred over a conformal-risk-control guarantee on expected missed area or on a missed-area quantile, which would be smoother in λ and agronomically more interpretable?

# Review R11: machine-learning baselines and uncertainty quantification

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (Computers and Electronics in Agriculture)
**Reviewer expertise:** ML baselines and uncertainty quantification (quantile regression, CQR, gradient boosting, meta-learning, transfer across sites)
**Material read:** manuscript.md (focus on Sections 1, 4, 5.4–5.5, 6.4–6.6, 7), supplementary.md (B.1–B.2, C.3–C.4, D.5, D.6), scripts/feature_pivot.py, scripts/feature_learning_curve.py, results/lowdata_v2/feature_pivot.txt and feature_learning_curve.txt.

---

## 1. Summary

The paper reduces zero-miss coverage of a parallel-pass plan to a scalar run score (the covering radius of the executed passes) and calibrates a footprint erosion with split conformal and PAC conformal rules (CE, CE+). For fields with no operation history it proposes CE-EVT-R. A five-layer extreme-value theory predicts each field's 0.9 score quantile $\hat q_f$ without run data. That prediction serves as a ratio pivot $V_i=S_i/\hat q_{f_i}$ for cross-field conformal calibration with one historical run per field. Validity follows from exchangeability across fields (Proposition 5) and does not depend on the theory. The theory affects only efficiency.

From my area, the relevant claims are these:
- (a) Across a mixed fleet of three machine configurations, the theory pivot beats configuration-blind pivots by an order of magnitude. It beats a "CQR-type" learned scale under the marginal rule and is comparable under the PAC rule (Table 8).
- (b) As a predictor of the per-field required margin $\lambda^\star_f$, the zero-data theory is "1.7–3.7 times more accurate than data-driven regressors" trained on one run per field (abstract, Table 9, Fig. 6).
- (c) Within one configuration, all field-level pivots sit at an information limit (Proposition 8) and are indistinguishable at matched coverage.

The statistical framing is careful and the evaluation is unusually honest. Pre-registered, post hoc and developmental results are labelled, and failed claims are reported. The data-driven baselines, however, are weak and untuned, and in places they are framed in a way that overstates the "theory beats learning" message. The paper's own supplementary numbers partly contradict that message.

## 2. Recommendation

**Major revision.**

| Criterion | Score (1–10) |
|---|---|
| Novelty | 7 |
| Soundness (of the ML/UQ comparisons specifically) | 5 |
| Practical relevance | 6 |
| Clarity | 6 |

The conformal machinery and the validity analysis are sound. The comparative efficiency claims against learned predictors are not yet adequately supported. The baselines are a single fixed-penalty ridge model on six hand-crafted features. They are not tuned. "CQR" is used as a name, not as a method. The most natural data-driven competitor, a predictor trained on simulation, is reported only as an "oracle" that the text describes as unattainable. Yet in the paper's own simulation-only evaluation it matches or beats the theory in two of three regimes.

## 3. Strengths

1. **The validity argument separates validity from efficiency.** Proposition 5 shows that any field-measurable scale gives a valid method. All competing pivots therefore compete on efficiency alone. This is the right frame for comparing physics-based and learned scales, and the paper uses it consistently.
2. **Matched-coverage analysis.** Rescaling each pivot family to equal realised coverage (Table S11, Table 8 middle column) is the correct way to compare conformal methods whose single calibration draw happens to over- or under-cover. Many conformal papers compare raw interval widths at unequal realised coverage. This paper does not, and it admits that the registered E-low v2 gains were mostly a matter of calibration luck.
3. **Proposition 8 (information limit).** This is a clean and useful result. Under one run per field, within-field tail randomness sets a floor that no field-level predictor, learned or physical, can remove. It correctly predicts that pivot choice within a configuration hardly matters. ML readers will recognise it as an irreducible-noise bound for normalised conformal scores.
4. **Two-level resampling check.** Section 6.5 checks the guarantee over both field sampling and historical-run sampling. It correctly treats coverage at a single calibration draw as a Beta-distributed quantity.
5. **Learning curves are reported at all**, with oracle-target and one-run-target variants. This lets a reader check the claims, and it lets this reviewer show below that the framing does not follow from them.
6. **Code and results are traceable.** Each table names its source file, and the scripts are short and readable.

## 4. Major issues

### M1. The learned baselines are a single untuned ridge model; the "theory + features" hybrid result is an artefact of a fixed penalty

**Location:** scripts/feature_learning_curve.py (`ridge(..., alpha=1.0)`, hybrid `alpha=10.0`); scripts/feature_pivot.py (`lam_ridge = 1.0`); Table 9 (lower block); Table S14; Section 6.6, "learning a feature correction of the theory from one run per field degrades it".

**Why it matters:**
- Every learned predictor is a linear ridge regression on six features (log length, log area, log passes, mean slope, a pass terrain feature, log lateral extent). The penalty is fixed a priori. There is no cross-validation, no feature selection and no alternative model class.
- The hybrid "theory + features ← one run" regresses the log residual $\log S - \log\hat q$ on features with $\alpha=10$. As $\alpha\to\infty$ the correction shrinks to an intercept. The metric is the *standard deviation* of the log ratio, which an intercept does not change, so the hybrid converges exactly to the theory (0.029/0.029/0.056).
- A hybrid whose penalty is chosen by cross-validation, by empirical Bayes or by a James–Stein-type rule therefore cannot be materially worse than the theory alone. At worst it matches it, up to CV noise.
- The reported degradation (0.091 vs 0.029 in R1; 0.177 at m = 5) shows under-regularisation, not a property of learning. The sentence "learning a feature correction of the theory from one run per field degrades it" is therefore not supported.

**Fix:**
- (i) Tune $\alpha$ by nested leave-one-field-out CV within the training pool for every predictor and every m in the learning curve.
- (ii) Report the hybrid with a tuned penalty, including the $\alpha\to\infty$ limit as an explicit candidate.
- (iii) Add at least one non-linear learner suited to small n: gradient boosting with strong shrinkage and monotone constraints (e.g. monotone in log passes, slope and GNSS error), a random forest or a Gaussian-process regression. Report CV-selected hyperparameters in the Supplement.
- (iv) Remove or rewrite the "degrades it" sentence unless it survives (i)–(ii).

### M2. "CQR" is a misnomer; the learned scale is neither quantile regression nor conformalised quantile regression

**Location:** Section 4.3 ("a learned CQR-type scale"); Section 2 (Romano et al., 2019 "the template of our learned (CQR-type) baseline"); Table 8; Supplementary C.4 ("CQR-type ridge regression of $\log S$ on field features...").

**Why it matters:**
- CQR fits conditional quantiles with the pinball loss and conformalises the residual $\max(\hat q_{lo}-Y, Y-\hat q_{hi})$.
- What is implemented is a least-squares regression of $\log S$, i.e. a conditional log-mean, used as a multiplicative scale inside a ratio score. That is *normalised* or *locally weighted* split conformal (Papadopoulos et al., 2008; Lei et al., 2018), not CQR.
- The distinction is substantive. The relevant target is the 0.9 quantile of a heavy-tailed, configuration-dependent score distribution. A mean model of $\log S$ is the wrong estimand whenever the shape of the score distribution (not just its scale) varies with features.
- This is exactly the case in the mixed fleet, where the DGPS tail ratio is 1.54 against 1.16–1.19 under RTK (Table S12a).
- Readers who see "CQR" will believe the paper beat a standard, strong UQ baseline. It did not.

**Fix:**
- Rename the current baseline (e.g. "learned normalised conformal, ridge on $\log S$").
- Add a genuine CQR/quantile baseline: linear quantile regression or quantile gradient boosting at $\tau=1-\varepsilon$, or quantile regression forests (Meinshausen, 2006), trained on the one-run pool, used as $q_f$ in the same ratio pivot. Optionally also use it as a CQR-style additive score.
- Add a distributional-regression baseline: a location–scale model such as GAMLSS or NGBoost on $\log S$, with scale and shape depending on configuration. This is the natural learned analogue of what the theory provides.

### M3. The strongest data-driven competitor, a predictor trained on simulation, is labelled "oracle" and dismissed, although it uses the same information as the theory

**Location:** Table 9 rows "trained on oracle $\lambda^\star_f$ (hundreds of runs per field)"; Fig. 6 caption ("oracle targets that require hundreds of runs per field"); Section 6.6 ("which requires hundreds of runs per field, the very data whose absence motivates the setting"); Section 7.1; Table S13.

**Why it matters:**
- The theory needs the closed-loop vehicle model, controller parameters, the DEM and GNSS error statistics, and its developers checked it against the simulator. Anyone with those inputs can *simulate* hundreds of runs per field. The "oracle" targets in Table S13 and Fig. 6 are exactly such simulated runs.
- "Hundreds of runs per field" therefore means hundreds of *simulated* runs, which cost compute, not field operations. They are as available as the theory itself.
- On that basis the simulation-trained feature predictor is the *more* accurate zero-field-data predictor in R1 and R2: 0.020/0.021 vs 0.029/0.029 (Table S13). It matches the theory from about 10 training fields (Table S14). It loses only in R3 (0.080 vs 0.056).
- The downstream numbers agree. In feature_pivot.txt the simulation-trained features gave lower PAC excess than the theory in R1 (+0.16 vs +0.27 pp) and R3 (+8.73 vs +15.25 pp). At matched coverage it was within 0.06 pp of the theory in every cell (Table S11).
- An even simpler competitor is missing: **direct Monte Carlo** of the target field's 0.9 quantile with the nominal model. In the paper's evaluation it would reproduce $\lambda^\star_f$ up to Monte Carlo error. Its cost should be compared with the theory's 16–353 s per field (Section 4.4).
- The real case for the theory over simulation-trained ML or direct Monte Carlo is therefore *not* data efficiency. It could be speed, interpretability, extrapolation beyond the training domain, or robustness to model misspecification. None of these is tested.

**Fix:**
- (i) Relabel the "oracle-trained" predictor as "simulation-trained" and discuss it as a legitimate zero-field-data competitor.
- (ii) Add a direct-Monte-Carlo pivot (simulated 0.9 quantile from N = 50/100/200 simulated runs per field) and report accuracy against compute, alongside the theory's runtime.
- (iii) Add a simulation-trained surrogate with domain randomisation, trained on synthetic fields with physics-informed inputs (see M5) and amortised across fields, which reduces per-field cost to milliseconds.
- (iv) Revise the abstract claim "1.7–3.7 times more accurately than data-driven regressors". Restrict it explicitly to regressors trained on one *observed* run per field, and state that simulation-trained regressors match or beat the theory under RTK.

### M4. The entire comparison is in-model: theory and evaluation share the same simulator, so "theory beats learning" cannot be distinguished from "the model is known"

**Location:** Sections 6.2, 6.6, 7.1; Supplementary B.1–B.2 (theory refined until it matched the simulator).

**Why it matters:**
- The theory was derived from, and iteratively corrected against, the same closed-loop simulator used for all evaluations. Supplementary B.1 records the observation-operator fix, the integrator clamp model and the product form.
- The field-edge terms were developed after observing simulation bias (Section 6.2).
- In this setting a model-based predictor has zero misspecification by construction, apart from its approximations. A data-driven predictor trained on real runs would see no such advantage or disadvantage.
- The fair test of "theory beats learning" is under **model mismatch**, where the deployment process differs from the model handed to the theory. Examples:
  - perturbed slip gain or steering lag;
  - an unmodelled actuator delay;
  - GNSS series from held-out stations, or from a vehicle rather than a static CORS antenna;
  - non-Gaussian roughness.
- There, learning from real runs can correct bias the theory cannot see, and the hybrid in M1 becomes meaningful.
- Moreover, the theory's development consumed many-run "oracle" information from development fields (Table S5). The label "zero data" holds for deployment, not for development. This should be acknowledged.

**Fix:**
- Add a misspecification experiment. Give the theory and any simulation-trained surrogate the *nominal* model. Evaluate on a perturbed simulator, with several perturbation magnitudes. Compare against (a) one-run learned scales and (b) a tuned theory + learned-correction hybrid.
- Report where each pivot's efficiency breaks down. Validity is preserved throughout by Proposition 5, which is itself a nice demonstration.
- At minimum, state the in-model limitation explicitly in Section 7.3. Also state that Section 6.7 (real-vehicle validation, currently TODO) is where the theory-versus-learning question will actually be decided.

### M5. Physics-informed and configuration-aware features are missing from the learned baselines

**Location:** `features()` in scripts/feature_pivot.py; Supplementary C.4 (CQR features: field features + log width + log p2p).

**Why it matters:**
- The learned models see only geometric and terrain summaries, plus, in the mixed fleet, log width and the log vendor pass-to-pass spec.
- They do not see the quantities that the theory itself shows to be decisive:
  - steering lag and saturation, and the controller gains;
  - soil-moisture or slip-gain range;
  - GNSS error spectrum or autocorrelation over a pass duration (which, by Theorem 3(b), determines common-mode cancellation);
  - number of field-edge passes;
  - the scale law $\sqrt{2\log N}$;
  - the theory's own intermediate outputs (Lyapunov stationary pair variance, Kac–Rice crossing rate).
- A reviewer in ML will ask whether a learner given these physics-informed inputs closes the gap. If so, the contribution is the *features* (the theory), and the full five-layer EVT machinery may be unnecessary. If not, that is a much stronger argument for the theory.
- In R3, where one-run CQR "fails badly" (Table S11: +2.73/+3.10 pp), the learner lacks precisely the edge-pass and common-mode GNSS information that explains DGPS misses.

**Fix:**
- Add a "physics-informed learner": the same learner classes as in M1/M2, with inputs extended by L1 quantities (stationary pair standard deviation), $\sqrt{2\log N}$, edge-pass count, the GNSS autocorrelation at one pass duration and $\log \hat q_f$ itself as a feature.
- Report it in the learning curve and in the mixed-fleet comparison.
- Include an ablation that removes theory layers one at a time (L1 only; L1 + Kac–Rice; full), to show which layers carry the accuracy.

### M6. The mixed-fleet headline (29.8 → 3.0 pp) is driven by a configuration-blind straw man; a stratified (Mondrian) baseline is missing

**Location:** Abstract; Highlights ("cut excess overlap from 29.8 to 3.0 pp"); Table 8; Section 7.1.

**Why it matters:**
- Raw pooling and the scale law ignore the machine configuration, and no practitioner would pool RTK 1.5 m and DGPS 6 m fields under a common margin. They are not credible competitors for the headline.
- The obvious simple baselines are absent:
  - (a) **Mondrian / configuration-conditional conformal**: calibrate separately within each configuration (Vovk, 2012; Romano et al., 2020 on class-conditional coverage).
  - (b) **A configuration-level empirical scale**: $q_f$ = median of the one-run scores of the other calibration fields of the same configuration, optionally × scale law.
- With 25 calibration fields from three configurations (about 8 per configuration), (a) is infeasible for PAC but feasible for the marginal rule. It also gives a stronger, configuration-conditional guarantee.
- (b) is field-measurable after cross-fitting. It requires no theory and would likely remove most of the 25–60 pp gap that the headline attributes to the theory.
- The only configuration-aware learned competitor (the "CQR" ridge) already reduces the gap to +1.41 pp (marginal) and +2.54 pp (PAC) at matched coverage. Against it the theory's PAC advantage is nil (+2.64 vs +2.54 pp) and was not significant in the registered test (Holm p 0.0648).
- The CQR row is also missing from the resampling column of Table 8 ("—"). The abstract figure (29.8 → 3.0) comes from that column, so the strongest learned comparator is absent from the very analysis quoted in the abstract.

**Fix:**
- (i) Add Mondrian-by-configuration conformal (marginal) and a configuration-median scale pivot to Table 8 and Fig. 5.
- (ii) Run the CQR (and the improved learned baselines of M1–M2, M5) through the same 4000-replicate resampling check.
- (iii) Report the headline in the abstract and highlights relative to the strongest configuration-aware comparator, not relative to raw pooling. For example: "0.73 vs 1.41 pp at matched coverage, marginal; no significant difference, PAC".

### M7. The accuracy metric (log-error sd) is not the efficiency-relevant quantity; accuracy gains do not translate into overlap gains, and the paper's own data show it

**Location:** Table 9; Fig. 6; abstract ("1.7–3.7 times more accurately"); Section 6.6.

**Why it matters:**
- The standard deviation of $\log(\hat q_f/\lambda^\star_f)$ is a reasonable proxy for pivot quality. It ignores, however:
  - the shape mismatch that drives the PAC rule (Proposition 8);
  - the nonlinear, pass-count-quantised mapping from margin to overlap.
- The paper's own numbers show the disconnect:
  - In R3, the theory has the better log-error sd (0.056 vs 0.080 for simulation-trained features), yet much worse single-draw PAC excess (+15.25 vs +8.73 pp, feature_pivot.txt).
  - In R1, one-run "CQR" has a 3× worse log-error sd than the theory, yet it was the *best* pivot at matched coverage (+0.00 vs +0.10 pp marginal; −0.00 vs +0.06 pp PAC; Table S11).
- The text says "excluding the one-run-trained CQR" when summarising within-regime spreads. That hides the fact that this baseline led in R1 and failed only in R3.
- The abstract's 1.7–3.7× accuracy factor is therefore not evidence of practical superiority within a configuration.

**Fix:**
- Lead with downstream metrics: excess overlap at matched coverage, with confidence intervals over test fields and calibration subsets.
- Present log-error sd as a secondary diagnostic.
- Report the CQR column of Table S11 in the main text without exclusion, and say plainly where it wins (R1) and where it fails (R3).
- Rephrase the abstract accordingly.

### M8. Statistical resolution: no uncertainty on the predictor-accuracy comparisons, and the oracle target is itself noisy

**Location:** Table 9; Table S13; Table S14; Fig. 6.

**Why it matters:**
- The log-error sd is computed on 30 test fields. Its sampling standard error is roughly sd/√(2·29) ≈ 13%, i.e. ±0.004 at 0.029.
- The reference $\lambda^\star_f$ is itself a Monte Carlo quantile. Table 4 states that in R3 about 0.066 of the 0.108 spread is estimation noise of the 200-run reference. That is larger than the theory's reported 0.056 against $\lambda^\star_f$, and comparable to the simulation-trained feature model's 0.080.
- Differences such as 0.020 vs 0.029 (R1/R2) or 0.056 vs 0.080 (R3) may therefore be partly or wholly within noise. The noise floor also contaminates training targets for the "oracle" learner.
- For full-pool rows the learning curve uses a single fit (no variability). The 40-subset rows report means without dispersion.

**Fix:**
- Report bootstrap CIs over test fields for every log-error sd, and paired differences (theory minus learner) with CIs.
- Estimate and subtract the Monte Carlo noise floor of $\lambda^\star_f$ (e.g. by split-half replication of the 200 runs), or increase the number of runs per oracle.
- Show dispersion across training subsets in Fig. 6.

### M9. Meta-learning and transfer settings that a practitioner would actually face are not evaluated

**Location:** Section 4.2 (CE+ uses five training fields with 40 runs each); Section 4.3; Section 7.4.

**Why it matters:**
- The deployment story assumes "many fields with one or two runs each, none on the target". But Algorithm 2 itself assumes five training fields with 40 runs each. Realistic farms or contractors will typically have a *few* well-logged fields plus many sparsely logged ones.
- That is a classic hierarchical / meta-learning setting. Relevant tools include:
  - hierarchical Bayes or mixed-effects location–scale models that pool many one-run fields with a few many-run fields;
  - transfer of a simulation-pretrained model, fine-tuned on a few real fields;
  - weighted conformal prediction (Tibshirani et al., 2019) when the target field's covariates are atypical of the calibration pool.
- The paper cites Tibshirani et al. and Dunn et al. but evaluates neither the hierarchical model nor the weighting.
- Table S14 already shows that with m = 5 many-run fields the simulation-trained learner is worse than the theory (0.044/0.034/0.123 vs 0.029/0.029/0.056). This is the realistic regime, and the most favourable honest result for the theory. It is not highlighted.

**Fix:**
- Add a "few rich + many sparse fields" scenario with a hierarchical location–scale model (or empirical-Bayes shrinkage toward the theory) as the learned competitor.
- Highlight the m = 5 result as the realistic comparison.
- Discuss the transfer to unseen configurations as an explicit limitation of every pivot, theory included: exchangeability breaks there (Section 7.3, item 4).

## 5. Minor issues

1. **Abstract and highlights rely on post hoc analyses.** "1.7–3.7 times more accurately" comes from post hoc Table 9 (lower block) and a developmental design probe (upper block). The abstract should flag this status, as the main text does.
2. **The Table 9 upper block (mixed fleet, 0.047 vs 0.136) is a developmental probe** on v1/v2 fields, whose training/test split is not specified. Please state the split, whether the ridge penalty was fixed, and whether this probe influenced the v3 registration (it appears it did).
3. **Training target for the one-run learner.** `one_tr = log(max(S_hist, 1e-3))`. Please report how many scores were clipped. A floor at 1 mm could bias log-scale fits for RTK fields with small scores.
4. **Inconsistent training pools.** feature_pivot.py drops fields with non-finite $\hat F$ (`load()` filters on `np.isfinite(r["Fhat"])`). The learned predictors therefore never see the fields on which the theory fails, a selection that favours the theory's comparison set. Report the number of excluded fields per regime and evaluate learners on all fields.
5. **R3 training pool of 30 fields with train $R^2=0.58$** (Table S13). This is too small to assess any learner fairly. Say so, or augment it with simulated fields.
6. **Fig. 6 log-scale y-axis** visually exaggerates the gap at small m. Consider a linear inset, or report the ratio to the theory.
7. **Table 8 mixes three different evaluation protocols** (registered, matched coverage, resampling) across columns with different missing entries. Add a CQR resampling entry (see M6) or explain its absence.
8. **Matched-coverage factors $c$** differ substantially between pivots (e.g. R3 PAC 0.586 for the theory vs 0.706 for simulation-trained features). Discuss what a $c$ far below 1 means for a PAC deployment: the PAC rule is very conservative under DGPS with one run per field, and this is a practical message.
9. **Terminology.** Use "normalised conformal" or "locally weighted conformal" for scale pivots in general. Reserve "CQR" for pinball-loss quantile models. Cite Papadopoulos et al. (2008) and Lei et al. (2018).
10. **Section 7.1 wording.** "learned predictors trained on the one run per field ... do not reach it (Fig. 6)" should add "...when trained on observed runs; simulation-trained predictors do reach it under RTK".
11. **The gate CE-EVT-R-G** (C4, met in 1 of 6 cells) is effectively a model-selection procedure trained on 30–60 noisy one-run fields. It would be worth relating its failure explicitly to Proposition 8: selecting among pivots that differ by less than the noise floor is impossible. This is a nice negative result, worth one sentence.
12. **Remove Appendix E ("Notes for the authors")** before submission.

## 6. Questions to the authors

1. What is the wall-clock cost of estimating $\lambda^\star_f$ (or the 0.9 quantile at $\pi(\lambda_0)$) by direct simulation with 50, 100 and 200 runs on the R1/R2/R3 test fields, and what log-error sd does it achieve? How does that compare with the theory's 16–353 s?
2. Was the ridge penalty, the feature set or the hybrid's $\alpha=10$ chosen before or after looking at test-field results? Were any alternatives tried and not reported?
3. With $\alpha$ selected by leave-one-field-out CV, does the "theory + features ← one run" hybrid still underperform the theory alone?
4. Does a learner given $\log\hat q_f$ (or the L1 stationary pair variance and $\sqrt{2\log N}$) as input, trained on one run per field, reach the theory's accuracy? If so, which theory layers are necessary?
5. In the mixed fleet, how does a configuration-median scale pivot, or Mondrian conformal by configuration (marginal rule), compare with CE-EVT-R at matched coverage and in the resampling check?
6. Why is the "CQR" baseline absent from the 4000-replicate resampling column of Table 8?
7. How sensitive are the theory's advantages to model misspecification, for example a 20% error in slip gain or steering lag, or GNSS series from held-out stations? Is there any regime where a one-run learned correction then improves on the theory?
8. In R1, one-run CQR was the best pivot at matched coverage (Table S11). How do you reconcile this with the claim that the theory is "more accurate than learned predictors trained on one run per field"?
9. How many training and test fields were dropped by the finite-$\hat F$ filter in `load()`, and how do the learners perform on those fields?

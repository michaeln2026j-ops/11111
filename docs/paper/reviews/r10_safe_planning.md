# Review R10: chance-constrained and safe planning

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (Computers and Electronics in Agriculture)

**Reviewer expertise:** chance-constrained and safe planning (scenario approach, conformal predictive programming, conformal planning with STL, robust/tube MPC, Wasserstein DRO).

**Material inspected:** manuscript.md, supplementary.md (C.3, D.1, D.2), `experiments/baselines/uncertainty.py`, `experiments/exp_lib.py` (`scenario_lambda`, `dro_cvar_lambda`), `experiments/exp_system.py` (how baselines are invoked), `experiments/ceplus.py` (`dominated` flag), and `results/v8/summary.txt` / `system_v8.csv`. The numbers marked "from system_v8.csv" below are field means that I computed from the authors' released results file. They are not in the manuscript.

---

## 1. Summary

The paper treats the zero-miss requirement of an agricultural coverage plan as a chance constraint on the missed area of a random set. It reduces this constraint exactly to a scalar run score, the covering radius of the executed passes (Lemma 1), and shows that this score is the smallest valid score (Theorem 1 and Corollary 1). Three certification layers are built on it:

- **CE / CE-q:** split-conformal calibration of the score on a dominating reference plan, with transfer to the deployed plan through Theorems 2 and 5.
- **CE+:** a reference plan derived from training fields, plus an optional normalisation by a headland-probe cross-track-error statistic.
- **CE-EVT-R:** cross-field conformal calibration with one run per field. Fields are put on a common scale by the predicted quantile of a five-layer Gaussian extreme-value model (Lyapunov covariance, Kac–Rice, Bonferroni product, mixture over conditions, Gumbel law).

The confirmatory experiment (v8; 90 fresh fields, three regimes) reports that CE+ uses 4.0–54.7% less main-area overlap than conformal predictive programming (CPP; Zhao et al., 2024) and a pair-level adaptation of Lindemann et al. (2023), in both the marginal and the PAC class. An exploratory experiment (v7) also covers the scenario approach, Wasserstein DRO-CVaR, tube MPC and Gaussian or GP chance constraints. The zero-data experiments (E-low v1–v3) and a 4000-replicate resampling check support the validity of CE-EVT-R. They also show, honestly, that within one machine configuration all field-level pivots are equivalent.

My review concentrates on the comparison with the safe-planning and chance-constrained baselines. Two parts are good: the exact score and the decision-dependence argument are clean and useful, and the pre-registration discipline is exemplary. However, the headline claim — "4–55% less overlap than conformal planners, **same guarantee**" — is, in my reading, largely a product of the comparison setup and not of a methodological advantage over these methods. Specifically:

- the comparators are evaluated at a different realised coverage;
- they are calibrated on a plan that the authors themselves argue is invalid;
- they use different data and side information;
- two of the "stronger" baselines run at a stricter guarantee level (β = 0.01);
- one Lindemann variant has no finite-sample guarantee at all, which the manuscript does not disclose.

The authors' own E-low analysis demonstrates the issue: there, "gains were mostly realised-coverage differences". The same lens has not been applied to the v8 headline.

## 2. Recommendation and scores

**Recommendation: Major revision.**

| Criterion | Score (1–10) | Comment |
|---|---|---|
| Novelty | 6 | The exact covering-radius score, the dominating reference plan and the EVT pivot are new for agricultural coverage. For a scalar decision, however, the certification rule is the standard split-conformal / scenario order statistic, as the authors acknowledge (Section 5.1). |
| Soundness | 5 | The theory is careful, and the validity checks for CE-EVT-R are convincing. The efficiency comparison against CPP, Lindemann, the scenario approach and DRO is not at equal guarantee, equal realised coverage or equal information. CE+'s own deployment leaves the dominance condition of Theorem 5 on many fields. |
| Practical relevance | 6 | The problem is relevant and the practical guidance is sensible. The target-field setting (n = 100 runs per field) is unrealistic for field operations, and there is no real-vehicle validation (Section 6.7 is a TODO). |
| Clarity | 6 | The writing is dense but precise, and the status labels (pre-registered, post hoc, and so on) are excellent. The manuscript is very long for CEA, and the baseline adaptations are described only in the code. |

## 3. Strengths

1. **Exact reduction of the chance constraint.** Lemma 1 reduces a chance constraint on the measure of a random set to a scalar covering-radius score. Theorem 1 and Corollary 1 then show it is the pointwise-smallest valid score, so it dominates any other valid score under any order-statistic rule. The safe-planning literature mostly accepts union-bound or max-of-normalised-score conservatism; this result is useful well beyond agriculture.
2. **Decision dependence handled explicitly.** Most conformal planning work, CPP and Lindemann et al. (2023) included, assumes that the uncertainty is exogenous to the decision. The dominating reference plan (Proposition 1, Theorems 2 and 5) is a principled response for a monotone scalar decision. The exact coupling inequality of Theorem 5 is elegant.
3. **Clear statement of guarantee classes.** Section 5.1 states that, for a 1-D decision, the scenario approach applied to S* is CE PAC, and marginal conformal applied to S* is CE-q, so comparisons must be made within a guarantee class. This is the right framing (but see Major issues 1–3, which ask the authors to follow it consistently).
4. **Exemplary transparency.** Failed claims (E-low v1, C3, C4) are reported, pre-registered and post hoc analyses are kept separate, every table names its source file, and the resampling check (Table 7) tests the guarantee over both sources of randomness.
5. **Careful baseline engineering.** The code documents its adaptation choices and picks the less conservative option where it can: the signed (one-sided) score instead of the two-sided norm ball, pair-level instead of point-level Lindemann, and the CPP "Max" joint encoding instead of "Union". It also cross-checks CPP-MIP against the conformal quantile. I credit the authors for this.

## 4. Major issues

### M1. The headline comparison is not at equal realised coverage; most of the reported advantage is over-coverage by the comparators.

**Location:** Abstract; Highlights ("same guarantee"); Section 6.3, Table 5; Fig. 3; Conclusion.

**Why it matters.** In Table 5, CE+ marginal realises P(no miss) of 0.903, 0.911 and 0.896, while CPP realises 0.944, 0.923 and 0.946 and Lindemann realises 0.959, 0.944 and 0.960. In the PAC class, Lindemann reaches 0.988 and 0.991. The comparators therefore sit at a different point of the risk–cost trade-off, and part of their extra overlap simply buys extra reliability. The authors concede this in Section 6.3 ("this over-coverage is what their extra overlap buys").

In Section 6.4 the authors showed that, in E-low v2, registered relative gains were "mostly differences in realised coverage". They then introduced a matched-coverage analysis to separate efficiency from coverage. That analysis is not applied to v8, which provides the abstract's headline number.

A rough cross-class reading of Table 5 already shows how much the gain shrinks at comparable coverage:

| Regime | CE+ PAC | Comparator | CE+ advantage |
|---|---|---|---|
| R1 | 9.04% overlap at P 0.941 | CPP marginal: 10.35% at P 0.944 | 12.7% less overlap |
| R2 | 28.14% at P 0.944 | Lindemann marginal: 28.38% at P 0.944 | 0.8% less overlap |
| R3 | 19.30% at P 0.933 | CPP marginal: 20.63% at P 0.946 | 6.4% less overlap, at lower coverage |

The quoted "54.7%" in R3 PAC compares 0.933 against 0.983 realised coverage.

**Fix.**
1. Report a matched-coverage comparison for v8 with the same procedure as Section 6.4: rescale each method's deployed margin by one common factor so that pooled P(no miss) equals 0.9 (and the PAC analogue).
2. Better still, show overlap against realised P(no miss) for each method, sweeping ε from 0.02 to 0.2, and compare overlap at equal realised coverage.
3. State in the abstract and highlights that the 4.0–54.7% figures are at equal *nominal* ε and δ, not at equal realised coverage, and give the matched-coverage range next to them.

### M2. "Same guarantee level" is not true in either direction.

**Location:** Highlights; Abstract; Section 6.3; Proposition 1; Theorem 5.

**Why it matters.**

*The comparators.* By the authors' own Proposition 1, CPP and Lindemann, calibrated on the nominal plan π(0) and deployed on π(λ̂) with more passes, have **no** distribution-free guarantee on the deployed plan. The comparison is therefore not "at the same guarantee level". The manuscript's own theory says the comparators have no guarantee; only the nominal ε and δ match.

*CE+.* Its guarantee on the deployed plan also holds only through Theorem 5:
- it requires λ_deployed ≤ λ0;
- under non-flat terrain it gives P(miss) ≤ κ·ε, not ε.

κ is not reported for any v8 field.

The released `system_v8.csv` contains a `dominated` flag, defined in `experiments/ceplus.py` line 161 as t · max σ(z_cal) ≤ λ0. It is **true on only 43% of R1 fields for CE+ marginal, 20% for CE+ PAC, and 37% for CE+ PAC in R3**. On the remaining fields, CE+'s deployed erosion can exceed the reference erosion for some operations. Larger erosion means *more* passes, so this is exactly the wrong dominance direction that the paper criticises in CPP (Proposition 1). Algorithm 1, line 4 prescribes refusal or recalibration in this case. Algorithm 2 (CE+) has no such step, and the code deploys regardless.

The manuscript should also state how often an actual deployment had λ > λ0, as opposed to the conservative flag. With the R1 values in `system_v8.csv` (mean deployed λ about 0.115 m, sd 0.021 m, λ0 = 0.175 m), this may be rare per operation, but it must be quantified.

**Fix.**
1. Report, per regime, the fraction of fields and of operations with λ_deployed > λ0, and κ(λ̂) for each field (Theorem 5 makes κ computable from the L4 prediction).
2. Either add a refusal or recalibration step to Algorithm 2 and re-run v8, or present CE+'s guarantee as "transfer-based, valid when λ ≤ λ0 and with factor κ".
3. Replace "same guarantee" with "same nominal (ε, δ)" throughout.

### M3. The scenario-approach and Wasserstein DRO baselines run at a stricter confidence level and are, in part, straw men.

**Location:** Section 6.1; Supplementary C.3; Tables S1–S3; `exp_lib.scenario_lambda`, `exp_lib.dro_cvar_lambda`; `exp_system.py` lines 366–378.

**Why it matters.**

*Scenario approach.* It is run with β = 0.01, whereas CE+ PAC and the PAC versions of CPP and Lindemann use δ = 0.1. With n = 100 and ε = 0.1, β = 0.01 discards 3 samples and returns the 97th order statistic; the PAC conformal rule at δ = 0.1 returns about the 94th.

More fundamentally, the code applies the scenario rule to **CE's own exact scores on CE's own reference plan** (`c_bcd["S"]`). Section 5.1 correctly notes that this is CE PAC up to an off-by-one. The "scenario approach" row therefore measures only the cost of β = 0.01 versus δ = 0.1, not a competing method. Presenting it in Tables S1–S3 as an independent published baseline that CE "dominates" is misleading.

*Wasserstein DRO-CVaR.* The implementation is CVaR_ε + ρ/ε with ρ = sd·sqrt(log(1/β)/n) and β = 0.01. This combines three sources of conservatism that are choices, not properties of DRO:
- a CVaR surrogate for a VaR chance constraint;
- a heuristic radius, which is neither the Mohajerin Esfahani–Kuhn concentration bound (its light-tail assumption is violated by the RTK tail of Table 1) nor a radius tuned by cross-validation or bootstrap, as those authors recommend;
- β = 0.01.

The exact Wasserstein distributionally robust chance constraint (Xie, 2021; Chen, Kuhn and Wiesemann, 2024), with a tuned radius, converges to the SAA quantile as ρ → 0 and would be far less conservative.

*Tube MPC.* The tube-MPC "W99 radius" is a robust (worst-case) method compared on a chance-constraint metric. The appropriate counterpart is stochastic or probabilistic tube MPC (for example, Cannon, Kouvaritakis and Wu; Hewing and Zeilinger, 2018, on stochastic MPC with probabilistic reachable sets).

**Fix.**
1. Run the scenario approach at β = δ = 0.1, ideally on the comparators' own scores and plans as well as on S*, and label it explicitly as "CE PAC with the scenario order statistic".
2. Implement the DRO baseline as a Wasserstein DR chance constraint (VaR form) with a cross-validated radius, and report a ρ sweep.
3. Replace or supplement the robust tube with a stochastic tube.
4. Otherwise, drop the language that CE "dominates" these baselines.

### M4. The CPP and Lindemann adaptations remove what makes them competitive, and the gain is not decomposed into its sources.

**Location:** Section 6.3; Supplementary C.3; `uncertainty.py` (docstring, `cpp_lambda`, `lindemann_cp_lambda`).

**Why it matters.** For a scalar decision, CPP-MIP is exactly the split-conformal quantile (the authors' own selftest asserts this). The CPP comparator therefore differs from CE-q / CE+ (with constant σ) in only two respects:
- (a) the score: the pair-based run score from `core.pair_scores` versus the exact covering-radius score;
- (b) the calibration plan: nominal π(0) versus the dominating π(λ0).

In R2 and R3 the training-only gate selected constant σ: `scale_b` = 0 in `system_v8.csv`, and the manuscript confirms this for R2. There, **CE+ is literally CPP with a different score and a different calibration plan.** The paper should say so and quantify the contribution of each factor.

Both factors are adaptation choices. Calibrating CPP on π(0) is not a property of CPP: CPP only requires decision-independent samples, and a practitioner could equally calibrate it on any fixed plan, including one chosen from training fields, as CE+ does. The R2 v8 erosions are 0.153 m (CE+) against 0.158 m (CPP), against an oracle of 0.149 m. In other words, CPP is already near-oracle there, and the "4%" is a pass-count rounding effect of a 3% margin difference.

There is also a puzzle. Proposition 1 predicts that nominal-plan calibration should *under*-cover, because more pairs give a stochastically larger maximum. Yet CPP *over*-covers in all three regimes (0.923–0.946). So the mechanism the paper credits ("calibrated on the nominal plan … over-cover", Section 6.3) is not the one its own theory predicts. The over-coverage must come from somewhere else, such as the pair score versus the exact score near the field edges, the boundary handling in `pair_scores` at λ = 0, or a systematic plan-geometry effect. This needs explaining.

For Lindemann et al., the method is designed for MPC among exogenous dynamic agents, with per-time-step regions joined by a union bound. The baseline sets one "time step" per pass pair. The authors' own follow-up line already removes the union bound by calibrating a single normalised max score (Lindemann et al., 2023, ICCPS, STL runtime verification; Cleaveland et al., AAAI 2024, linear complementarity programming; Tumu et al., 2024). These would be the natural "Lindemann-family" comparators in 2026. Comparing against the union-bound variant tests Lemma 3 (union bounds are looser), which is not in doubt. It does not test whether CE is better than the current state of conformal safe planning.

**Fix.** Add an ablation grid on the v8 fields, within each class: {pair score, exact score} × {π(0), π(λ0) from training fields} × {constant σ, probe-normalised σ}. The cell (pair score, π(λ0), constant σ) is "CPP with a sensible calibration plan". The cell (exact score, π(0)) isolates decision dependence. Add a normalised-max-score conformal planner (Cleaveland et al., 2024) as the Lindemann-family comparator. Explain the direction of CPP's over-coverage (for example, by reporting its coverage on π(0) itself and on π(λ̂), using common random numbers).

### M5. The pooled Lindemann variant has no finite-sample guarantee, and this is not disclosed.

**Location:** Section 6.3, Table 5; Supplementary C.3; `uncertainty.py`, lines 69–79 (`pool=True` default).

**Why it matters.** The default `pool=True` takes one quantile over all T·n per-constraint scores. The code's own docstring states that "what is lost is the exact finite-sample conformal guarantee, because the T pooled scores of one run are dependent, not exchangeable draws". The paper calls this method a "conformal planner" with a matching guarantee class without stating this.

The PAC version then splits δ over T as well (δ/T per constraint, on top of ε/T). The pooled quantile does not satisfy the PAC premise, and the double split is an authors' construction, not the published method. Its very high realised coverage (0.988–0.991) reflects that construction.

**Fix.** Disclose `pool=True` and its consequence in the main text. Report the paper-faithful `pool=False` variant where it is finite. Treat the "Lindemann PAC" row as an authors' construction and do not count it as a published-method comparison, or justify the δ/T split formally.

### M6. The comparison is not at an equal data and information budget.

**Location:** Section 4.2 ("the same budget as all comparators"); Algorithm 2; Section 6.3.

**Why it matters.** "Budget-matched" covers only target-field runs. CE+ additionally uses:
- (i) five training fields × 40 runs = 200 extra runs, to set λ0 and fit σ(z);
- (ii) a headland probe drive and its XTE statistic on every calibration and deployment run, which is side information the comparators never receive;
- (iii) the gate's leave-one-field-out (LOFO) cross-validation on the training fields.

CE and CE-q use a pilot fixed point that spends additional batches before the certificate batch. In `system_v8.csv`, `pilot_iters` averages 2.9, 2.5 and 4.7 per field in R1, R2 and R3 (maximum 10). The code itself notes that "the v6 two-stage CE spends 3–5x the calibration budget". The scenario baseline inherits CE's reference plan, which was chosen with these extra batches.

None of this is reported. In R1 (the only regime where σ is adaptive) part of CE+'s gain can be attributed to the probe covariate. Any comparator given the same z could exploit it, for example through normalised or Mondrian conformal, or a CQR-style local scale.

**Fix.**
1. Tabulate, for every method, the target-field runs, training-field runs, pilot runs and side information used.
2. Give CPP and Lindemann the same training-field access (to choose their calibration plan) and the same covariate z (normalised score).
3. Report CE and CE-q with the pilot runs counted, or with a pilot drawn from training fields only.

### M7. The target-field setting is evaluated at a data budget where the comparators' weaknesses do not show, and that is unrealistic in practice.

**Location:** Section 1, item (iii); Section 6.1 (n = 100); Section 7.4.

**Why it matters.** The introduction motivates the work by noting that conformal planners need ≥ 9 (marginal) or ≥ 22 (PAC) runs while a field is worked a few times per year. Yet the confirmatory comparison gives every method 100 runs on the target field. At n = 100 the union-bound baselines are finite only because of pooling (M5). The relevant regime is n ∈ {9, 15, 22, 30}, where:
- the order statistic is close to the maximum;
- CE+'s λ0-from-training-fields could matter more;
- per-constraint Lindemann (`pool=False`) is infeasible.

**Fix.** Repeat the v8 comparison (or at least a post hoc version) at n ∈ {9, 15, 22, 30} and report how often each method refuses or is infinite. Discuss explicitly that n = 100 is a laboratory budget.

### M8. Missing related work on decision-dependent and closed-loop conformal guarantees.

**Location:** Section 2.

**Why it matters.** The paper's central argument is decision dependence. It cites performative prediction but omits the directly relevant conformal literature:
- conformal prediction under feedback covariate shift (Fannjiang et al., PNAS 2022);
- conformal decision theory (Lekeufack et al., ICRA 2024);
- adaptive conformal prediction for motion planning (Dixit et al., L4DC 2023);
- shrinking-horizon MPC with conformal guarantees (Stamouli, Lindemann and Pappas, 2024);
- STL control synthesis with conformal prediction (Yu et al., 2023).

On the scenario side it omits risk-and-complexity / wait-and-judge results for non-convex or multi-dimensional decisions (Campi and Garatti, 2018; Garatti and Campi, 2022). On DRO it omits Wasserstein DR chance constraints (Xie, 2021; Chen, Kuhn and Wiesemann). Without these, the novelty claim — that conformal planning methods "do not address the decision-dependent maximum" — is overstated.

**Fix.** Discuss these methods, and state precisely what the dominating-reference-plan construction adds beyond weighted or feedback-shift conformal approaches. A plausible answer is that it is assumption-free for a monotone scalar decision, without density-ratio estimation.

## 5. Minor issues

1. **Abstract, "4.0–54.7% less overlap than two conformal planners."** Add "at equal nominal ε and δ", and report regret (pp above the oracle) or matched-coverage figures alongside. Relative overlap in R2 is diluted by the 24.9% oracle overlap, as the authors note.
2. **Section 6.1 and C.3.** The Lindemann adaptation choices (signed score, pair granularity, pooling, T counted on the reference plan with `t_count='ref'`) and the CPP choices (Max encoding, λ_ref = 0) are documented only in code. Move a compact table of these choices to the Supplementary.
3. **Table 5.** Add a column with the mean deployed erosion λ for each method, and the oracle λ. In R2 it shows CE+ 0.153 m vs CPP 0.158 m vs oracle 0.149 m, which tells the reader much more than "4.1%".
4. **Tables S1–S3.** "Scenario approach (PAC, β = 0.01)" sits in a list headed "published baselines" although it is applied to S* on CE's reference plan. Label it accordingly (see M3).
5. **Lemma 3.** This is the standard Bonferroni comparison and should be stated as known, with a citation.
6. **Proposition 7.** The 14.5% theoretical failure rate for an exactly calibrated marginal method should be shown next to the v8 meet rates of the comparators. Otherwise a reader may read CE+'s meet rate of 0.83–0.90 as weaker than CPP's 0.93–1.00, when it is the expected behaviour.
7. **Theorem 5.** κ is "computable" but never computed for any reported deployment (see M2). A histogram of κ over the v8 fields would substantiate the transfer claim.
8. **Section 5.2, Proposition 2.** The 0.7% bound assumes h = 0 and identically distributed pairs; R2 and R3 are hilly. State the bound actually attained there.
9. **DRO radius.** The formula ρ = sd·sqrt(log(1/β)/n) does not appear in Mohajerin Esfahani and Kuhn (2018) in this form. Cite its source or call it a heuristic.
10. **Terminology.** "CPP" is used both for coverage path planning (Introduction) and for conformal predictive programming (Section 6). Rename one.
11. **Length.** The paper is very long for CEA. The five-layer theory and the E-low sequence could be shortened in the main text, and the space used for the ablations requested above.

## 6. Questions to the authors

1. Proposition 1 predicts under-coverage for nominal-plan calibration, yet CPP over-covers (P 0.923–0.946) in every regime. What is the empirical source of this over-coverage? What is CPP's realised coverage if it is calibrated on π(λ0) instead of π(0)?
2. On how many v8 operations did CE+ deploy λ > λ0? What were the realised coverage on those operations and the field-wise κ(λ̂)?
3. With β = δ = 0.1, does the scenario row coincide with CE PAC, and what overlap does it give?
4. If CPP and Lindemann receive the probe statistic z and use a normalised score S/σ(z), with σ fitted on the same training fields, how much of CE+'s R1 advantage remains?
5. How do CE+ and the comparators behave at n = 9, 15 and 22 target-field runs, and how often does each refuse?
6. Was any baseline hyper-parameter (granularity, pooling, score sign, joint encoding, β, Wasserstein radius) selected after inspecting v7 results? If so, which ones, and in which direction relative to the CE variants?
7. Would a normalised-max-score conformal planner (Cleaveland et al., 2024), calibrated on a dominating plan, differ from CE-q at all, given Theorem 1? If not, the contribution should be framed as the exact score and the reference plan, not as a superiority over "conformal planners".

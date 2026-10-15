# Review R02: Coverage path planning perspective

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (submitted to *Computers and Electronics in Agriculture*)

**Reviewer expertise:** coverage path planning for field robots (boustrophedon decomposition, Fields2Cover, swath-angle optimisation, headland planning, 3D terrain coverage)

**Material checked:** manuscript.md, supplementary.md, figures in `figures/paper/`, and selected repository files: `experiments/core.py` (planner, simulator, evaluator, exact score), `experiments/data_fields.py` (field extraction), `experiments/baselines/f2c_planner.py`, `experiments/baselines/terrain3d.py`, `experiments/baselines/uncertainty.py` (CPP and Lindemann baselines), `results/v8/system_v8.csv`. I ran small read-only summaries of the v8 CSV and of the field metadata. I ran no simulations.

---

## 1. Summary of the paper

The paper models execution error in parallel-swath coverage plans and asks how much "erosion" (half the overlap between adjacent swaths) is needed so that, with probability at least 1-ε, an operation leaves no uncovered spot in the field's main area. The authors show that zero miss is equivalent to a scalar run score, the covering radius of the executed pass centres, and calibrate that score with split-conformal and PAC order statistics on a reference plan that has at least as many passes as the deployed one (CE, CE-q, CE+). For fields with no history, a five-layer Gaussian extreme-value model (Lyapunov covariance, Kac–Rice, Bonferroni product form, mixture over conditions, Gumbel law) predicts each field's required margin. That prediction is then used as a ratio pivot for cross-field conformal calibration with one run per field (CE-EVT-R). All evidence comes from a closed-loop simulator driven by real GNSS error series, GLO-30 terrain and field polygons taken from harvester trajectories. The results include a pre-registered comparison on 90 fields against two conformal planners and a sequence of pre-registered zero-data experiments, several of which did not meet their registered claims.

## 2. Recommendation

**Major revision.** The idea is solid: an exact covering-radius score, a dominating reference plan and a cross-field conformal pivot. The reporting of failed pre-registered claims is unusually honest. From a coverage-planning standpoint, however, the problem is set up in a way that inflates its practical relevance: the zero-miss criterion, the headland-excluded main area with an artificial "field edge", trivial convex fields with a fixed driving direction, no headland or turn geometry, and nearly flat "hilly" terrain. The headline efficiency claims are relative to baselines that are weaker than the obvious practical alternatives. There is no field validation (Section 6.7 is a TODO). Several of these problems can be fixed with re-analysis of existing data. Others need new experiments.

| Criterion | Score (1–10) |
|---|---|
| (a) Novelty | 6 |
| (b) Technical soundness | 5 |
| (c) Practical relevance | 3 |
| (d) Clarity | 4 |

## 3. Strengths

- It frames coverage under execution error clearly as a chance constraint on missed area, and gives an exact, cheap reduction to a covering-radius score (Lemma 1). The score is implemented exactly as stated (`core.exact_scores`), and the paper reports a numerical check against interval-union coverage.
- It correctly identifies the decision-dependence problem: calibrating on the nominal plan and deploying a plan with more pass pairs (Proposition 1). The fix, a dominating reference plan, is simple and practical.
- The cross-field "scale pivot" construction (Proposition 5) suits the realistic situation of many fields with little history per field. Its validity does not depend on the accuracy of the theory, and this is checked directly over both sources of randomness (Table 7).
- Reporting is unusually transparent: pre-registered vs. exploratory vs. post hoc labels, failed claims reported (E-low v1, C3, C4), matched-coverage re-analyses that weaken the authors' own gains (Section 6.4), and an information-limit argument (Proposition 8) that explains when no pivot can help.
- It uses real inputs where it can: CORS-derived GNSS error series with a realistic heavy RTK tail (Table 1), real field polygons and a public DEM.
- The baseline set is broad (about 25 systems across six planner/controller stacks), including Fields2Cover-style and Hameed-style planners.

## 4. Major issues

### M1. The zero-miss criterion is not agronomically justified, and it drives every efficiency number

**Location:** Section 3 (objective), Section 1 paragraph 2, Section 6.3, Section 7.4 bullet 1, Abstract and Highlights.

**Problem.** The constraint is P(M = 0) ≥ 0.9, where M is the missed area on a 1 m along-track grid. A gap of a few millimetres on a single 1 m section anywhere in the field counts as a failed operation. I summarised `results/v8/system_v8.csv`:

| Regime | Vendor rule: overlap | Vendor rule: mean missed area | Vendor rule: P(no miss) | CE+: overlap | CE+: mean missed area |
|---|---|---|---|---|---|
| R1 | 1.8% | 0.22% (95th percentile 0.51%) | 0.00 | 8.4% | about 0.001% |
| R2 | 3.5% | 0.64% | 0.00 | 25.6% | about 0.001% |
| R3 | 7.6% | 0.12% | 0.40 | 15.7% | 0.027% |

So the certified margin applies inputs twice on an extra 6.6 pp of the main area (R1) or 22 pp (R2) to avoid missing about 0.2–0.6% of it. For spraying, fertilising or seeding this trade-off is the wrong way round under almost any agronomic or economic weighting. Boom spray-pattern tails, spreader patterns and drift also make sub-centimetre "gaps" irrelevant. The statements "the vendor rule … left a gap on essentially every run" (Section 1) and "P(no miss) 0.000" (Section 7.4) are technically true, but they mislead practitioners without the missed-area figures. The oracle margins (mean λ* = 11.9 cm on flat RTK with a 3 m implement, and 14.9 cm on RTK with a 1.5 m implement) are 4–6 times the RTK RMS. They mainly reflect the maximum of a heavy-tailed process over a whole field, and probably rare wrong-fix events (Table 1, 99.9% = 24 cm).

**Fix.**
- Report missed area (mean, 95th and 99th percentiles) and applied overlap for every system in the main text.
- Add a tolerance-based formulation: P(M ≤ m_tol) ≥ 1-ε, or zero gaps wider than g_tol (for example 5–10 cm) or longer than l_tol. Conformal risk control on E[M], which the paper already cites, is a natural alternative. The exact-score machinery extends directly: shift the covering-radius threshold by g_tol/2.
- Show a Pareto curve of overlap against missed area (or expected cost with stated prices for inputs and yield loss), and position the vendor rule, the farmer-tuned rule, CE+ and the oracle on it.
- State how much of λ* in RTK is driven by wrong-fix or float events. Rerun R1 with the fix-flag events removed, or with an INS-aided fix-validation model, to show the sensitivity.

### M2. "Field edge" is the inner boundary of an un-simulated headland, so Theorem 3(b) and the "misses concentrate at field edges" finding may be artefacts

**Location:** Section 3 ("main area W is P inset by 2w"), Fig. 1, Theorem 3(b), Section 6.2 paragraph after Table 4, Section 7.1, Section 7.4 bullet 6, Conclusion, Highlights.

**Problem.** In `core.Field`, M = P.buffer(-2w) and coverage is evaluated on M only. The planner `core.plan` starts the first pass so that its eroded footprint touches M's boundary. In any real operation, and in Fields2Cover's ConstHL generator, the band between M and P is worked by perimeter headland passes. A point at M's boundary that the first infield pass misses is then covered by the headland lap (and vice versa), unless the two drift apart. So the true boundary miss is a two-pass gap between the infield pass and the headland lap, not a single-pass absolute error.

Fig. 1 labels the region below the edge "outside the field", which does not match the experiments. The physical insight that "DGPS common-mode error cancels in interior pairs but not at the edge" therefore rests on a modelling choice. In reality the headland lap is driven at a very different time (the start or end of the operation, often tens of minutes from the adjacent infield pass). Common-mode error would then not cancel there either, but the governing quantity is a difference of two passes with a long time lag, not a single-pass offset.

The headland is also large: in the v8 fields M covers a median of 70% (R1), 86% (R2) and only 50% (R3) of the field polygon. So in R3, half of each field is never evaluated. The applied-overlap metric (Table S22: 30–55%) shows that the swath reaching into the headland is a larger cost than the main-area differences being optimised. That cost is not modelled sensibly: there is no section control and no headland passes.

**Fix.** Simulate headland laps (at least one or two perimeter passes of width w, driven before or after the infield passes) with the same error model. Evaluate coverage on the whole polygon P, and redefine the edge terms as infield–headland pair terms with the correct time lag. Re-derive Theorem 3(b) for this case. Then re-test whether DGPS misses still concentrate at the boundary. Until then, remove the "boundary passes set the certified margin" guidance (Section 7.4) and the corresponding highlight and conclusion sentences, or label them clearly as conditional on the no-headland-lap model. Redraw Fig. 1 to show the headland.

### M3. Pass order, turn geometry and timing are physically inconsistent, yet they drive the central GNSS-correlation mechanism

**Location:** Section 3 (execution model), Section 6.1 (Simulator), Supplementary C.1. Code: `core.simulate` (`t_turn = π·4.5/v + 6`, passes driven in index order 0, 1, 2, …).

**Problem.** Adjacent passes are driven consecutively with a semicircular U-turn of radius 4.5 m, that is 9 m between the centres of consecutive passes. That geometry is incompatible with pass spacings of 1.5 m (R2), 3 m (R1) and 6 m (R3) unless the vehicle uses Ω- or fishtail turns, which take longer and need a wider headland. A 2w = 3 m headland in R2 cannot accommodate a 4.5 m-radius turn at all. Real route planners (Fields2Cover's SnakeOrder, which the authors themselves implemented in `f2c_planner.py`; B-patterns, Bochtis and Vougioukas, 2008) often skip passes precisely to allow continuous turns. That changes the time lag between physically adjacent passes from about one pass duration to two or more.

Because the paper's main physical claim is that GNSS error is common-mode across adjacent passes and cancels in the interior gaps, and because Proposition 4 and Theorem 5 treat pass start times τ_k as inputs, the route order is a first-order factor, not a detail. Speed is also fixed at 2 m/s for every machine, which is low for a 6 m sprayer, and the lag scales with it. Turns are not simulated (`f2c_planner.py`: "Turns are not executed by core.simulate"), so line acquisition after a turn is reduced to N(0, 3 cm) on initial offset.

**Fix.**
- Use a feasible turn model, consistent with headland width and minimum turning radius, to compute pass start times.
- Run at least one sensitivity experiment with skip-row orderings (for example F2C SnakeOrder) and with realistic speeds (2–7 m/s depending on operation), and report how λ*, the interior/edge split and the theory's accuracy change.
- State explicitly which conclusions depend on adjacent-pass sequential driving.

### M4. The CPP side of the problem is essentially absent: trivial convex fields, fixed driving direction, no decomposition, and no joint swath-angle choice

**Location:** Sections 3, 6.1 ("Data"), Section 2 (CPP related work), Title. Code: `data_fields.py` (fields are `MultiPoint(...).convex_hull` of DBSCAN clusters; heading = mode of harvester heading), `core.plan` (1D greedy placement on a single cell).

**Problem.**
- Every field is a convex hull of harvester GNSS points. So "boustrophedon decomposition" is trivially a single cell, there are no obstacles or concavities, and the polygon is not the real field boundary (a convex hull of combine centre-line points under-estimates the field by about half a header width and over-estimates concave fields). The phrase "real field boundaries" (Abstract, Section 6) overstates this.
- The driving direction is taken from the harvester trajectories, not optimised. One v3 field (index 559, R1) has 90 passes with a mean length of 39 m, which suggests the working direction is far from the length-minimising one. Fields are small: median main-area extent 0.6–0.7 ha and as few as 4–6 passes. The paper uses "Fields2Cover (opt. heading)" only as a fixed-overlap baseline.
- My summary of `results/v8/system_v8.csv` shows that choosing the swath angle as F2C does, with CE+ on top, reduces applied overlap by 6.0 pp (R1: 24.1% vs 30.1%), 1.7 pp (R2) and 4.3 pp (R3), and reduces path length by 5–8%. Those differences are as large as, or larger than, the CE+ vs CPP applied-overlap differences that form the paper's confirmatory claim (1.0, 1.0 and 4.0 pp; Table S22). For a practitioner, the certified margin is a second-order effect next to basic planning choices, and the paper does not say so.
- The margin is uniform over the field. The planner supports per-pass σ, but nothing exploits the most obvious CPP lever: the certified λ depends on heading (side-slope slip, antenna roll, pass length, number of pass pairs N, GNSS direction-dependent error). Choosing the swath angle that minimises *certified* cost is a natural, novel contribution that is missing.
- The cost J ignores path length, number of turns, time and non-working distance, which are standard CPP objectives (Fields2Cover's NSwath and SwathLength, Spekken and de Bruin, 2013). Adding passes to gain margin costs turns and time, which are not charged.

**Fix.**
- Use surveyed or cadastral field boundaries (for example public parcel datasets) that include non-convex shapes, and apply a real decomposition (F2C, or BCD with cell merging).
- Optimise the swath angle per field, and add an experiment that chooses the angle by minimising certified overlap plus path or turn cost.
- Report path length, turn count and field efficiency alongside overlap.
- Either reduce "coverage planning" in the title and framing to "margin certification for parallel-swath plans", or add the planning contributions above.

### M5. "Hilly", "3D terrain" and the Hameed baseline are not tested meaningfully

**Location:** Table 2, Section 6.1, Supplementary C.3. Code: `baselines/terrain3d.py`, `core.Field._load_dem`.

**Problem.**
- The v8 fields have a median mean slope of 0.8° in both R1 ("flat") and R2 ("hilly"), and 1.2° in R3. On 0.4–3 ha fields the GLO-30 DEM provides only a handful of 30 m cells per field, so the lateral gradient is essentially one plane per field. For hilly paddies in southern China, which are typically terraced and levelled within each terrace, a 30 m DEM gradient across terraces does not represent the slope under the wheels. The differences between R1 and R2 are therefore driven by the wet-soil slip and Ornstein–Uhlenbeck roughness parameters and by implement width, not by terrain.
- Coverage is evaluated in horizontal projection with a constant footprint w (`core.evaluate`). A 3D-aware planner such as Hameed et al. (2016), whose purpose is to account for the surface width on slopes, can then only lose: its cos θ spacing reduction is counted as pure overlap.
- The module docstring of `terrain3d.py` states that the publisher full text "could not be fetched" and that the method "follows the abstract and secondary descriptions". This contradicts Supplementary C.3, which says each baseline was "reviewed against the original paper or source code".

**Fix.**
- Relabel R2 honestly (for example "RTK, wet soil, narrow implement"), or use fields with real side slopes (5–15°) and a high-resolution DEM (≤ 5 m, LiDAR where available).
- Evaluate coverage on the terrain surface, or at least model the implement footprint as w cos θ in projection.
- Re-implement Hameed from the full text, or state the limitation in the paper and drop "reviewed against the original paper" for that baseline.
- Model implement drift for trailed implements on side slopes, which is often the dominant source of pass-to-pass error in practice and is absent from the simulator.

### M6. The calibration data assumed by CE/CE+/CE-EVT-R are not observable on a farm

**Location:** Section 4.2 (CE+ uses "logged runs" and a headland probe line), Section 4.3 ("one historical score S_i" per field), Section 7.4 (practical guidance), Section 6.7.

**Problem.** The run score requires the true executed footprint positions. Farm logs record the autosteer's GNSS position. Because steering follows that same GNSS solution, the recorded cross-track error excludes exactly the GNSS error that dominates λ* under DGPS and a large share under RTK (wrong fixes, float drift). A "historical operation" from a farm's records therefore does not give S. Obtaining S needs an independent ground truth (a PPK rover with a different base, as Section 6.7 plans, or post-operation imaging of the treated strips), which farms do not have. The practical guidance ("With at least 22 recorded operations on a field…", "many fields with one or two operations each") assumes data that, as far as I can tell, does not exist in the form required. Exchangeability across seasons, crops, implements and soil states (the same field worked "a few times per year") is also asserted rather than examined.

**Fix.** Specify exactly which sensor data are needed to compute S, and discuss how it could be obtained routinely: as-applied maps plus imagery, PPK logging, or implement-mounted sensing. Rewrite Section 7.4 accordingly. Add an experiment in which calibration uses only *observable* data (for example, S computed from logged positions with the GNSS error removed) to show how much the guarantee degrades. Discuss non-exchangeability across seasons, and test a weighted or non-exchangeable conformal variant (Barber et al., 2023, already cited).

### M7. The headline efficiency claims rest on weak or strawman comparators, while the strongest practical baseline is left out of the confirmatory test

**Location:** Abstract ("4.0–54.7% less overlap"), Highlights, Table 5, Section 6.3. Code: `baselines/uncertainty.py::cpp_lambda`, `lindemann_cp_lambda`.

**Problem.**
- The CPP baseline is the authors' adaptation. It calibrates on the nominal plan π(0) and uses the pair score, which the paper itself shows is looser than the exact score by 0.4–1.3 cm (RTK) and 5.5–9.2 cm (DGPS) at the 90% quantile (Supplementary A.4). As the paper notes in Section 5.1, CPP applied to the exact score on a dominating reference plan *is* CE-q. The confirmatory comparison therefore mostly measures "exact score vs. pair score" plus nominal-plan calibration, which is a design choice inside the authors' own adaptation of CPP. The largest numbers (37–55%) come from a union-bound baseline that is conservative by construction (Lemma 3).
- Relative reductions of an overlap ratio are a misleading headline. In absolute terms the main-area reductions are 1.1–4.9 pp in the marginal class, and the applied-overlap reductions are 1.0–4.0 pp (CPP) and 1.4–6.0 pp (Lindemann marginal).
- The most relevant practical baseline, a farmer-tuned global overlap, is not part of the confirmatory claims. In v8 it reaches pooled P = 0.897 with 9.2% overlap in R1, against 0.903 and 8.4% for CE+. CE+'s advantage there is 0.8 pp. In R2 and R3 the farmer-tuned rule under-covers (P 0.83), so a fair comparison needs the matched-coverage analysis that the paper already uses for E-low.

**Fix.**
- Report absolute pp differences in the Abstract and Highlights instead of "4–55%".
- Add CPP and Lindemann variants that use the exact score and a dominating reference plan as an ablation, so that readers can see how much of the gain is the score and how much is the reference plan.
- Include the farmer-tuned rule and a "vendor rule × tuned factor" rule in a matched-coverage comparison.
- State plainly in the Abstract that the 54.7% figure is against a union-bound method.

### M8. The paper is simulation-only, yet it is titled and framed as "certified" coverage for field operations

**Location:** Title, Abstract, Section 6.7 (TODO), Section 7.3(1), Data availability (TODO), Supplementary Appendix E ("Notes for the authors (remove before submission)").

**Problem.** All guarantees hold only with respect to the simulator's distribution. The simulator rests on several unvalidated choices: static CORS antennas as the RTK error source (acknowledged as a lower bound), US CORS errors combined with Chinese fields, a kinematic model with no implement dynamics, a fixed speed and an infeasible turn model. Section 6.7 is an explicit TODO. The relation between probe-line XTE and pass-to-pass error, which CE+ relies on, is untested. So is the DGPS edge-concentration claim. For a CEA submission, a "certified" claim with no vehicle data is an overclaim. The manuscript also contains unfinished material: a TODO in Section 6.7, a TODO in Data availability, and Appendix E internal notes.

**Fix.** Provide at least a small real-vehicle data set before acceptance: the planned RTK autosteer tractor with a PPK rover on 20–40 fields, or as a minimum the offline CitrusFarm replay. If that is impossible, retitle (for example "…: a simulation study") and move the certification language to "certified under the simulator's error model". Remove the TODOs and Appendix E.

### M9. The theory contribution is large, developmental and only weakly tied to the CPP decision

**Location:** Section 5.3 (L1–L5), Table 3, Section 6.2, Section 6.4–6.6.

**Problem.** By the authors' own analysis, within one machine configuration the five-layer theory brings no efficiency gain over raw pooling or a one-line scale law ("equivalent to within tenths of a percentage point", Section 7.2). Its value is shown only on a mixed fleet built from three configurations that differ in implement width by a factor of 4 and in GNSS grade by a factor of 10, which is a contrived pooling. A per-configuration pooled calibration (pooling only fields of the same machine configuration), which any contractor could implement trivially, is missing as a baseline. It would likely remove most of the 29.8 → 3.0 pp gap. The C3 claim as registered was not met. The theory was also adjusted repeatedly after failed validation checks (Section 6.2, Supplementary B), the field-edge terms are post hoc, and every pre-registered result used the version without edge terms. Roughly half the paper (Sections 5.3–5.5 and 6.4–6.6) therefore supports a component whose practical benefit is narrow.

**Fix.**
- Add stratified per-configuration raw pooling and a per-configuration scale law as baselines for the mixed fleet.
- Move most of L1–L5 to the supplement and keep in the main text only what the decision needs (a predictor of q_f and its accuracy).
- Justify the mixed-fleet construction with an example of a realistic farm or contractor fleet.

## 5. Minor issues

- **Section 3, "greedy rule uses the fewest passes":** true for a single convex cell with straight lines. State the scope explicitly (no decomposition, no curved swaths, no headland).
- **Lemma 1 / Theorem 1:** "Shift-equivariant transfer" is the key assumption behind "the smallest valid score" (Highlights: "the tightest valid one"). On non-rectangular fields the greedy plan anchored to M's boundary is not shift-equivariant. Qualify the highlight.
- **Section 3, evaluation grid:** coverage is checked on 1 m along-track sections only. Gaps shorter than 1 m along-track can be missed or exaggerated. Report sensitivity to the grid step (0.25 m).
- **Section 3:** footprints are modelled as rigid rectangles of width w attached to the vehicle reference point. Spray-pattern tails, implement yaw and trailed-implement offset are ignored. Say so in Section 7.3.
- **Table 2 / Section 6.1:** add field-size statistics (area, main-area share, number of passes, pass length) for each regime. The fields are small (median about 0.6–0.7 ha in v8, some with 4–6 passes), which limits generalisation to large mechanised fields and affects Theorem 6's large-N asymptotics.
- **Table 1:** RTK on 5–30 km single baselines with a "max 1.39 m" error is not typical of modern network-RTK or INS-aided autosteer, which reject most wrong fixes. Discuss how representative the series is, and give the fraction of epochs in the fixed and float states.
- **Section 6.1:** 30 s CORS epochs are interpolated to 1 Hz. This smooths the error at exactly the time scale of adjacent-pass lags and may artificially increase common-mode cancellation. Quantify the effect.
- **Section 6.3:** "regret" is relative to an oracle computed on the BCD + LQR-I stack. When other stacks are compared (Table S4), negative regret is an artefact. Use a stack-specific oracle.
- **Table 5:** give absolute λ (cm) and pass counts next to the overlap percentages, so that readers can judge practical size.
- **Section 4.2:** the 1.25 inflation factor, the 3% gate, the 0.3 σ̄ floor and the 2 mm rounding look tuned on development data. Give a sensitivity analysis or a justification for each.
- **Section 4.4:** 16–353 s per field of theory runtime is reported for fields of 324–5703 m of passes. Extrapolate to a 50–100 ha field (tens of km of passes).
- **Fig. 1:** the area below y = 0 is labelled "outside the field". In the experiments it is headland (see M2).
- **Fig. 3:** add the oracle P and overlap, plus the farmer-tuned rule, for context.
- **Related work (Section 2):** missing core agricultural CPP and guidance-overlap literature: Oksanen and Visala (2009) on coverage path planning algorithms for agricultural field machines; Jin and Tang (2010, 2011) on optimal coverage path planning on 2D and 3D terrain (their NSwath approximation is in the authors' own F2C code); Bochtis and Vougioukas (2008) on B-patterns; Spekken and de Bruin (2013) on routing with manoeuvring cost; Hameed et al. (2013) on 3D-terrain CPP. Economic studies on guidance-related overlap and section control (for example Batte and Ehsani, 2006; Shockley et al., 2012; Luck et al., 2010) are directly relevant to the cost metric.
- **Supplementary C.3:** "each implemented as a plug-in module reviewed against the original paper or source code" contradicts the Hameed module docstring (M5).
- **Supplementary C.3 / f2c_planner.py:** the F2C baseline modifies swath placement ("placement='full'") and does not execute turns. State this in the paper, so that readers do not take it to be an unmodified Fields2Cover run.
- **Section 5.4, Proposition 7:** the numbering skips Proposition 6 in the main text (it appears only by reference to Supplementary B). Renumber, or state it in the main text.
- **Abstract:** the abstract is overloaded with method names and numbers. It mentions "five-layer extreme-value theory" with its parts but not that all results are simulated.
- **Throughout:** internal project-history labels (v7, v8, E-low v1/v2/v3, "developmental", field index ranges) make the paper hard to read for a CEA audience. Consolidate them into one design-and-status table, and use descriptive names in the text.
- **References:** the RTKLIB demo5 entry notes that "the exact commit was not recorded". Record it for reproducibility. The Global Market Insights market report is not a scholarly source for the autonomy trend.
- **Data availability:** "TODO: archive with a DOI". Pre-registration by git timestamp only is weak (Appendix E acknowledges this). Consider OSF.

## 6. Questions to the authors

1. What is the distribution of missed area (and of maximum gap width and length) under the vendor rule, the farmer-tuned rule and CE+? Which tolerance would an agronomist accept for spraying, fertilising and seeding, and how do λ* and the comparisons change under a gap-width tolerance of, say, 5 cm?
2. What fraction of R1/R2 runs have their exact score set by RTK wrong-fix or float episodes? How large is λ* if those epochs are removed or flagged, as a commercial receiver would do?
3. If perimeter headland laps are simulated and coverage is evaluated on the whole field P, do DGPS misses still concentrate at the boundary? How does Theorem 3(b) change when the boundary term is a pair (infield pass, headland lap) with a long time lag?
4. How do λ*, the theory's accuracy and the CE+/CPP comparison change with a skip-pass route (for example F2C SnakeOrder), with a feasible turn model for r_min = 4.5 m at 1.5–6 m spacing, and with realistic working speeds?
5. Does the certified margin depend materially on the driving direction? If so, what is the gain from choosing the swath angle by certified overlap plus path or turn cost, compared with F2C's default objective?
6. How would a farm obtain the run score S of a historical operation, given that its logs record the steering GNSS solution and not ground truth?
7. In the mixed fleet, how does CE-EVT-R compare with per-configuration pooled calibration (raw or scale law within each configuration)?
8. Why were the R2/R3 "hilly" paddies chosen when their median slope (0.8–1.2°) equals that of the "flat" wheat fields? Were terraced paddies screened out, and is a 30 m DEM appropriate for them?
9. Was the Hameed et al. (2016) baseline checked against the full text, or only against secondary descriptions as the code comment states?
10. Is the 1.25 reference-plan inflation for CE+ chosen independently of the v8 fields? How sensitive are the v8 results to it (1.1, 1.5)?
11. Can you provide any real-vehicle result, even a small one (for example the CitrusFarm replay mentioned in Supplementary C.1), that checks the predicted relation between probe-line XTE and pass-to-pass error?

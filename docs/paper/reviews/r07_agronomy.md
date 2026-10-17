# Review R07: precision agronomy (input application, overlap and skip costs, farm practice)

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (Computers and Electronics in Agriculture)

**Reviewer expertise:** precision agronomy: sprayer, fertiliser-spreader and seeding operations; overlap and skip costs; environmental impact of input application; farm and contractor practice.

---

## 1. Summary

The authors want the lateral overlap between adjacent passes to come with a stated reliability instead of being fixed by rule of thumb. They define a run as "miss-free" if the infield passes leave no uncovered point anywhere in the field's main area $W$, which is the field inset by $2w$. They show that this event is equivalent to a scalar run score: the covering radius of the executed pass centres, including the field-edge terms (Lemma 1). They then use conformal prediction to choose the smallest margin $\lambda$ for which $P(\text{no miss})\ge 1-\varepsilon$, with $\varepsilon=0.1$ throughout. Three variants are proposed:

- **CE / CE+** calibrate on 9–22 or more logged runs on the target field.
- **CE-EVT-R** calibrates across fields with one historical run each. A five-layer extreme-value model of the closed-loop guidance system acts as a scale pivot.

All results come from simulation. The simulator uses real field boundaries (Chinese paddy and wheat fields extracted from combine-harvester trajectories), Copernicus DEM terrain and CORS-derived GNSS error series. It covers three regimes: RTK with a 3 m implement, RTK with a 1.5 m implement on wet hilly terrain, and DGPS with a 6 m implement. In a pre-registered comparison on 90 fields, CE+ used 4.0–54.7% less main-area overlap, in relative terms, than two conformal planners at the same guarantee level. In a mixed-fleet zero-data setting, the theory pivot cut excess overlap from 29.8 to 3.0 pp compared with raw pooling. The authors also say plainly where the method cannot help, and they report failed pre-registered claims.

From an agronomic point of view, the paper is statistically careful and unusually honest. However, it optimises an objective (no uncovered point anywhere in the field, with probability 0.9) that does not match how input application is costed or judged in practice. It reports overlap savings without converting them into input, cost or environmental terms. It does not show the size of the misses it guards against. And it never says which field operations the hard-edged footprint model actually describes. As a result, the paper's practical relevance, which is the main criterion for this journal, is not yet established.

## 2. Recommendation

**Major revision.**

| Criterion | Score (1–10) | Comment |
|---|---|---|
| Novelty | 7 | The exact covering-radius score, calibration on a dominating reference plan and the theory-pivoted cross-field calibration are new for agricultural coverage. |
| Technical soundness | 6 | The statistics and pre-registration are rigorous. However, the agronomic model behind the objective (binary zero-miss, rectangular footprint, main-area-only cost, no headland passes) is weak, and all results are simulated. |
| Practical relevance | 4 | The savings are not translated into inputs or money. The realistic baseline (farmer-tuned overlap) is as cheap or cheaper. Implement widths and GNSS/implement pairings are atypical. Calibration needs ground-truth executed paths, which farm logs do not contain. |
| Clarity | 6 | The paper is dense and statistically precise. Agronomic readers will struggle with the notation. Key practical quantities (margin in cm, missed area, gap widths) are missing or buried. |

## 3. Strengths

1. **It treats overlap as a reliability decision.** Fixed overlaps with no stated reliability are common practice, and the paper is right to criticise them. Showing that the vendor rule (twice the nominal pass-to-pass accuracy) almost never yields a gap-free run is a useful provocation, although it needs to be qualified (see Major issue 2).
2. **Exact, tight score.** Lemma 1 and Theorem 1 tie the certificate to the actual covered/uncovered geometry rather than to per-pair surrogates or union bounds. This explains most of the advantage over the published conformal planners (Fig. 3).
3. **Physical insight about field edges.** Common-mode GNSS error (DGPS) cancels in the gap between adjacent passes but not at the field boundary. This is agronomically meaningful, because boundary strips are where under-application, drift and buffer-zone rules interact. It needs to be checked against how headlands are actually worked (Major issue 4).
4. **Fits real data structures.** "Many fields, one or two operations each" is how farms and contractors actually hold data. The mixed-fleet result, where a configuration-blind common margin is very costly, is a relevant warning for contractors running heterogeneous machinery.
5. **Exemplary reporting discipline.** Pre-registration, labelling of developmental and post hoc results, and reporting of failed claims (E-low v1, C3, C4) go well beyond the norm in this field.
6. **Real GNSS error tails.** Wrong fixes and float drift in the RTK series are included, rather than a Gaussian model with the same RMS.

## 4. Major issues

### M1. "Zero miss with probability $1-\varepsilon$" is not an agronomically justified objective

**Location:** Section 3 (Objective); Abstract; Section 1, paragraph 2; Section 7.4.

**Why it matters.**

- **Miss size is ignored.** The constraint $P[M(\lambda,e)=0]\ge 1-\varepsilon$ treats a 1 cm × 1 m sliver and a 50 cm × 500 m unworked strip as the same failure. Agronomically, the damage from a skip scales with its area and, for some operations, with its width relative to a biological length scale:
  - Weed escape strips matter when they exceed roughly the crop's row spacing or canopy-closure distance.
  - N-deficient strips matter when their width exceeds the lateral root-foraging distance (about 10–20 cm for cereals). Narrower deficits are partly compensated by neighbouring plants.
  - For seeding, a "gap" of a few cm is simply a slightly wider guess row, and yield compensation in cereals is substantial.
- **Large fields are penalised.** Because the score is a field-wide supremum, the needed margin grows like $\sqrt{2\log N}$ with field size (Theorem 6). The method therefore applies more overlap over the entire field to guard against one transient event. Examples are an RTK wrong fix (0.3–0.6 m for seconds to minutes, Table 1) or a single slip episode. This is agronomically perverse: a bigger field receives a higher input rate per hectare everywhere to protect a few square metres. Table 3 illustrates the scale of the problem. Under RTK-fixed with 2.7 cm RMS, the required margin in R1 is about 11 cm per side, so about 22 cm of overlap on a 3 m implement (oracle main-area overlap 8.65%). That is far above the 0–5 cm that RTK users typically apply. The tail, not typical pass-to-pass performance, drives the cost.
- **$\varepsilon=0.1$ is never justified.** It is unclear whether 0.1 is a sensible per-field-per-operation level for spraying, top-dressing or seeding, or how it compares with the agronomic losses at stake.

**Concrete fix.**

1. Report, for every method and regime, the distribution of **missed area** (m² and % of $W$), **maximum gap width** and **gap length** on the runs that do miss. Do this especially for the vendor-specification and farmer-tuned baselines, so readers can see what "P(no miss) = 0.000" actually means on the ground.
2. Add at least one agronomically graded objective and show that the framework handles it. Two candidates:
   - A **tolerance-based** constraint, $P(\text{max gap width} > g_\text{tol}) \le \varepsilon$, where only gaps wider than an operation-specific $g_\text{tol}$ count. This simply shifts the score to $S-g_\text{tol}$, so the existing machinery applies directly.
   - An **expected-missed-fraction** constraint, $E[M/|W|]\le\alpha$, using conformal risk control (already cited: Angelopoulos et al., 2024).
3. Discuss why a *field-wide supremum* is the right event rather than a *per-hectare* or *per-section* exceedance rate, which would not grow with field size.

### M2. The cost trade-off between misses and overlap is never made explicit, and the realistic baseline is cheaper

**Location:** Section 3 (Objective); Section 6.3; Supplementary Tables S1–S3; Section 7.4, first bullet.

**Why it matters.**

- **The trade-off is implicit.** The chance constraint encodes an implicit miss/overlap price ratio but never states it. The two kinds of error carry different, operation-specific costs:
  - Overlap: double dose, possible crop injury from herbicides and growth regulators, lodging and leaching from N, seed wasted in crowded rows, extra fuel and time.
  - Miss: yield loss, weed seed-bank increase, resistance selection, re-work trips.

  A decision-maker needs the full trade-off curve, not a single point at $\varepsilon=0.1$.
- **The comparison that matters for adoption is against the farmer-tuned overlap, and there the method costs more input.** In the exploratory v7 tables:
  - R1: farmer-tuned overlap 8.72% (meet rate 0.733) vs CE+ 8.86% (0.967).
  - R3: farmer-tuned 13.82% (0.700) vs CE+ 16.00% (0.833) and CE-q 15.45% (0.867).

  The method therefore buys reliability with *more* input than current good practice. It does not save input. The vendor rule is cheaper still because it misses almost everywhere. The headline "4–55% less overlap" is measured only against other conformal planners that over-cover by construction, which is not the competitor a farm or contractor faces.
- **The practical guidance overstates the case.** Section 7.4's first bullet, "Replace a fixed vendor overlap by a certified margin", implies a benefit. In input terms it is a cost, and its worth depends on the unreported size of the avoided misses (M1).

**Concrete fix.**

1. Plot **Pareto frontiers**: main-area (and applied) overlap against P(no miss), and against expected missed area, for $\varepsilon\in\{0.02, 0.05, 0.1, 0.2, 0.3\}$. Overlay the vendor and farmer-tuned operating points.
2. Add an **expected-cost analysis**: $c_o\cdot\text{overlap area}\cdot\text{dose} + c_m\cdot E[\text{missed area}]\cdot\text{loss per m}^2$, for at least three operations (herbicide spraying, N top-dressing, cereal drilling), with literature-based prices and loss functions. State for which cost ratio $c_m/c_o$ the chosen $\varepsilon$ is optimal.
3. Move the farmer-tuned comparison into the confirmatory main text, or explicitly limit the efficiency claim to "among certified methods", including in the Abstract and Highlights.

### M3. The reported overlap savings are small when converted to input, and the conversion is never made

**Location:** Abstract; Highlights; Table 5; Supplementary Table S22; Section 1 (pesticide and nitrogen-use-efficiency motivation).

**Why it matters.**

- **Relative reductions of an excess quantity look large but are small in input terms.** Input applied to the main area is proportional to $1+J$, so the input saving is $(J_\text{comp}-J_\text{CE+})/(1+J_\text{comp})$. From Table 5:

| Regime / class | vs CPP | vs Lindemann pair-level |
|---|---|---|
| R1 marginal | 1.8% | 2.2% |
| R1 PAC | 2.2% | 4.1% |
| R2 marginal | 0.9% | 2.2% |
| R2 PAC | 0.9% | 11.5% |
| R3 marginal | 4.1% | 6.8% |
| R3 PAC | 5.2% | 16.3% |

- **Over the whole field the savings shrink further.** Using applied overlap including the headland (Table S22), the saving against CPP falls to **0.8–3.8% of applied input** (for example, R1 marginal 31.04% → 30.05%, about 0.8%).
- **The money involved is small.** As an order of magnitude, a 1–2% saving on herbicide (about €40–80 ha⁻¹) or N (about €120–200 ha⁻¹) is roughly €0.5–4 ha⁻¹ per operation. That is not negligible at farm scale, but it is far from what "up to 55% less overlap" suggests.
- **The comparison is again against conformal planners, not practice.** Against farmer-tuned overlap the sign is reversed (M2).
- **The environmental framing is not supported.** The Introduction invokes global pesticide use (3.73 Mt) and nitrogen use efficiency of 40–46%, but no environmental quantity is computed.
- **The overlap metric itself is ambiguous.** $J$ (swath area / $|W|$ − 1) includes waste from the final partial pass, which does not depend on $\lambda$. The applied-overlap figures of 30–55% suggest a large share of the cost lies in headland and boundary geometry that the method does not address. The reader cannot tell how much of $J$ is actually controllable by $\lambda$.

**Concrete fix.**

1. Report savings as **% of applied product** and as **kg or L or € per ha** for representative operations. Report them both in the main area and over the whole field including headland.
2. Decompose $J$ into (a) inter-pass overlap $\approx 2\lambda(K-1)L$, (b) partial-last-pass waste and (c) headland and boundary overlap, and state which part the method controls.
3. Either remove the pesticide and nitrogen-use-efficiency figures from the motivation, or add a quantitative (even indicative) environmental estimate, such as surplus N kg ha⁻¹ or active ingredient g ha⁻¹ on overlap strips. In that estimate, distinguish operations where overlap means a true double dose from those where it does not (M4).
4. Rephrase the Abstract and Highlights so that relative reductions of overlap are not read as reductions of input use.

### M4. Which operations does the method suit? The footprint model fits some operations and not others

**Location:** Section 1, first paragraph; Section 3 (Execution model); Table 2; Section 6.1.

**Why it matters.**

The paper claims applicability to "spraying, fertilising, seeding and tillage". The model, however, assumes a **hard-edged rectangular footprint of width $w$, binary coverage and a double dose on the overlap strip**. That is only partly true across operations:

- **Boom sprayers.** Nozzle patterns overlap by design (often 100% at the boom ends). A small lateral deviation changes the dose profile smoothly (CV of deposit) rather than producing a zero-dose strip. Overlap of a few cm does not double the dose. Wide booms (24–48 m) also make the relative overlap tiny, and boom sections plus individual nozzle control modulate overlap independently of pass spacing.
- **Spinning-disc fertiliser spreaders.** The working width is defined by the overlap of triangular or trapezoidal spread patterns. "Miss" and "overlap" here are changes in the transverse CV, so the binary model does not apply.
- **Seed drills and planters.** A gap is a wider guess row and an overlap is a narrower or duplicated row. Costs come in row-spacing quanta and are asymmetric. Continuous erosion $\lambda$ makes little sense when the relevant decision is the guess-row width.
- **Operations that fit well:** sharp-edged footprints such as mowing, mechanical tillage and cultivation, rolling, pneumatic boom spreaders, band application, and possibly harvesting. For harvesting, though, "miss" means unharvested crop and "overlap" means reduced header fill, a very different cost structure.

**Machine pairings are atypical.**

- The 1.5 m (R2) and 3 m (R1) widths and the 6 m DGPS implement (R3) do not match common precision-application machinery. DGPS-grade guidance is used mainly on wide sprayers and spreaders (≥ 18 m), where a 37 cm margin (Table 3) would be about 2% overlap rather than 15–20%.
- R2's 24.9% oracle overlap on a 1.5 m implement is a property of the chosen width, and it dominates the relative numbers.
- The field data come from **combine-harvester** trajectories. Harvest working directions and boundaries may not represent spraying or drilling layouts, for example tramlines or controlled-traffic systems.

**Concrete fix.**

1. Add a short section or table mapping operations to model fit (good / partial / poor). For "partial" operations, explain how the footprint would be replaced by a dose-profile model with a dose-deficit tolerance.
2. Re-run, or at least extrapolate with the theory, for realistic combinations: RTK with a 6 m drill or 9 m cultivator; RTK and DGPS with a 24–36 m sprayer or spreader. Report the margin in cm and the overlap in %.
3. Discuss tramline and controlled-traffic systems, where pass spacing is fixed by the tramline module and RTK repeatability. Discuss section and nozzle control. Explain where a certified margin fits in these workflows.

### M5. Field-edge misses may be an artefact of evaluating infield passes only

**Location:** Section 3 (main area $W$ = $P$ inset by $2w$); Theorem 3(b); Section 6.2; Section 7.4 (bullet "Under DGPS, pay particular attention to boundary passes").

**Why it matters.**

- **In practice, field edges are worked by headland or boundary passes.** Headlands are usually worked as one or more perimeter passes, often driven first for spraying and spreading. The outermost infield pass is therefore bordered by a headland pass, not by an unworked edge. Coverage is evaluated on $W$ only, and the headland passes do not appear to be simulated. If so, the "field-edge miss" at the boundary of $W$ would be covered in practice by the headland pass whenever the headland runs along the sides of the field. This is precisely the DGPS finding emphasised in the Abstract and Conclusion.
- **Some edge misses are deliberate.** At the real field boundary, under-application is often intentional or legally required: spray buffer zones near water courses, border-spreading devices, and setbacks along hedges. Penalising every edge miss is not always correct.
- **Metric gaming toward the headland.** The main-area metric does not charge swath that crosses into the headland. Supplementary C.5 already notes that a margin-maximising variant shifted overlap around. A planner can lower $J$ by pushing overlap into the headland, where it becomes a real double dose because the headland is also treated.

**Concrete fix.**

1. Simulate headland passes, both perimeter and end-only headland patterns, and evaluate coverage of the whole field $P$.
2. Show whether the DGPS edge effect survives.
3. Treat the field boundary as a separate constraint with its own tolerance, such as a buffer zone or border-spread setting.
4. Make applied overlap, including headland double-treatment, a co-primary cost metric.

### M6. Calibration data are not available from farm logs

**Location:** Sections 4.2–4.3; Section 7.4, bullets 4–5; Section 6.7.

**Why it matters.**

- **The score needs true executed implement positions.** A machine's own log records its GNSS-estimated position, which contains the very error being certified. Under DGPS and under RTK wrong fixes, the log cannot reveal a gap. As-applied maps share the same limitation. "Recorded operations" or "historical runs" therefore require independent ground truth: a PPK or RTK reference on the implement, plus implement-offset sensing.
- **The CE+ budget implies a long history.** CE+ needs 9–22 such runs per field, each with the same machine configuration. At one to a few operations per year, that is roughly a decade of history.
- **CE-EVT-R still needs ground truth.** Even with one run per field, that run must have ground-truth tracking. Section 6.7 acknowledges that a PPK rover is needed, but Section 7.4 presents the method as if ordinary records would suffice.
- **Exchangeability across operations is doubtful.** Runs of the "same field" by different operations (drilling in autumn, spraying in spring, top-dressing on soft soil) differ in implement, speed, soil condition and terrain response.

**Concrete fix.** State explicitly what must be logged and with what sensor (implement-mounted PPK, or RTK with integrity monitoring). Estimate the cost and practicality of collecting it. Define a "run" as an operation × implement × field triple. Discuss whether calibration can transfer across operation types.

### M7. Implement dynamics and operating conditions limit the agronomic validity of the simulation

**Location:** Section 6.1 (Simulator); Supplementary C.1; Limitations.

**Why it matters.**

- **Implement drift is missing.** The simulator models the tractor antenna, with roll compensation and mounting bias, but not the lateral offset between a trailed or three-point-linkage implement and the tractor. Implement drift on side slopes is a dominant source of pass-to-pass error in hilly terrain, which is regimes R2 and R3. Its omission bears directly on the terrain-related claims.
- **Speed is fixed at 2 m/s (7.2 km/h).** This is plausible for drilling but low for spraying (10–25 km/h), where steering-loop bandwidth, boom yaw and boom sway matter.
- **Machine-sensor RTK errors are larger than the simulated ones.** The authors note that the static CORS antennas give a lower bound on RTK error. This matters for the extreme tail that drives the margin.

**Concrete fix.** Add implement-drift dynamics (at least a passive trailed-implement model with a slope-dependent offset) and a speed sensitivity analysis. Report how the certified margin changes.

## 5. Minor issues

1. **Abstract and Highlights.** "4–55% less overlap" should state that it is a relative reduction of main-area overlap against two conformal planners. Add the absolute pp and the % input equivalent.
2. **Section 1, paragraph 2.** "Under RTK left a gap on essentially every run" needs the gap size alongside it (see M1); otherwise it is alarmist.
3. **Margins in cm.** Report the deployed margins $\lambda$ in cm per regime and method in the main tables. Agronomists think in cm of overlap, not in % main-area overlap. Supplementary C.5 gives only the R2 values (0.153 vs 0.158 m).
4. **1 m along-track grid.** Gaps shorter than 1 m along-track may be missed, and gaps of 1 mm width count as misses ("up to floating-point ties"). State both resolutions and their agronomic meaning.
5. **Probe line in CE+.** The headland probe line costs time and is driven on headland soil, which may not represent infield slip. Discuss its operational feasibility and its time cost.
6. **R2 terminology.** The "paddy (hilly)" fields with "wet (moisture 0.6–0.9)" soil: clarify which operation is imagined. Paddy-field puddling, rice transplanting and spraying in flooded fields have very different footprint and slip characteristics.
7. **Variable-rate application and section control.** These are mainstream on sprayers, spreaders and planters and interact with overlap in the interior (nozzle-level control at about 0.5 m resolution). They are not mentioned.
8. **Fig. 1.** The vertical exaggeration is not stated. Readers may infer deviations of about 0.5–1 m, which is DGPS-like, for any regime.
9. **Negative regret (Table 5, R1 marginal −0.26 pp).** Explain for agronomic readers that this means coverage slightly below the oracle's target, not "better than optimal".
10. **Section 7.4, last bullet (runtime).** This is irrelevant to the farmer. Instead state what the user must supply: controller gains, a DEM, a GNSS-grade error model and an implement width. Say whether a farm-management information system or a contractor could realistically assemble these inputs.
11. **Commercial guidance accuracy specs.** Vendor "pass-to-pass" specifications usually refer to a 15-minute window at 95%. Explain whether the "twice the nominal accuracy" baseline reflects any manufacturer recommendation, or whether it is a straw man.
12. **Outdated reference.** Global Market Insights (2026) is a market report. Use peer-reviewed sources on autonomy adoption, or soften the claim.
13. **Draft material left in.** Section 6.7 (field validation) and the DOI archiving are TODO placeholders, and Supplementary Appendix E ("Notes for the authors") is still present. These must be completed or removed before the paper is reviewable as final.

## 6. Questions to the authors

1. For the vendor-specification and farmer-tuned baselines, what are the mean missed area (% of $W$), the 95th percentile of maximum gap width, and the mean gap length on runs with a miss?
2. What fraction of runs that fail at the CE+ certified margin have a miss explained by a single RTK wrong-fix or float episode? Would a real-time integrity monitor that triggers re-work be cheaper than a field-wide margin?
3. If headland passes are simulated and coverage is evaluated on the whole field $P$, does the DGPS field-edge effect persist?
4. What is the certified margin, in cm, for RTK with a 24–36 m boom, or for a 6–9 m drill, at 10–15 km/h, as predicted by the theory?
5. At what cost ratio $c_m/c_o$ is $\varepsilon=0.1$ optimal for herbicide spraying, N top-dressing and cereal drilling, given your simulated missed-area distributions?
6. How should a contractor obtain ground-truth executed paths for calibration? Is an implement-mounted PPK receiver assumed? Could RTK logs with fix-status filtering serve as a proxy, and with what bias?
7. Can calibration runs from one operation type (for example drilling) certify another (for example spraying) on the same field and tractor, or must they be kept separate?
8. How much of the main-area overlap $J$ at the oracle margin is partial-last-pass waste that no choice of $\lambda$ can remove?

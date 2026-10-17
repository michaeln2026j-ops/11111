# Review R20 — Agricultural economics and technology adoption

**Manuscript:** Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations (Computers and Electronics in Agriculture)
**Reviewer expertise:** agricultural economics and technology adoption (cost of overlap and skips, input prices, farm size, return on investment of guidance systems, adoption barriers)
**Material reviewed:** `docs/paper/manuscript.md` (full), `docs/paper/supplementary.md` (Appendices A–E)

---

## 1. Summary

The authors formulate coverage path planning under execution error as a chance constraint on the event "no part of the main area is missed" and show that this event is equivalent to a scalar run score (the covering radius of the executed passes) falling below the planned margin. The margin is calibrated by split conformal prediction on logged runs (CE, CE-q, CE+), with marginal and PAC variants. For fields without operation history, a five-layer extreme-value theory predicts each field's required margin from the controller, the DEM and GNSS error statistics. This prediction is used as a ratio pivot for cross-field conformal calibration with one historical run per field (CE-EVT-R). Evaluation is entirely in simulation. Real field boundaries (Chinese wheat and paddy fields), Copernicus DEMs and real CORS GNSS error series drive a closed-loop tractor simulator in three regimes: RTK 3 m flat, RTK 1.5 m hilly-wet, and DGPS 6 m hilly. In a pre-registered comparison on 90 fresh fields, CE+ used 4.0–54.7% less main-area overlap than two conformal planners at the same guarantee class. A pre-registered resampling check confirms the cross-field guarantee in 26/26 cells. In a mixed fleet, the theory pivot reduces mean excess overlap from 29.8 pp (raw pooling) to 3.0 pp. The experimental reporting is unusually honest: failed pre-registered claims, post hoc status and matched-coverage caveats are stated explicitly.

From an economic point of view the paper does something unusual: it changes how overlap is decided, from a rule of thumb to a stated reliability level. But it does not show that this change is worth money to any farm. All efficiency results are in percentage points of geometric overlap. Neither the overlap itself nor the "zero-miss" event is translated into a per-hectare cost or benefit. The cost of a miss (missed area, agronomic damage) is never reported. The cost of obtaining the calibration data, which requires ground-truth executed paths, is not discussed. The simulated machine configurations (1.5–6 m implements on 0.2–2 ha fields) also do not match the operations where overlap is economically material (24–36 m sprayers and spreaders, high-value seed). As a result, the practical-guidance section (7.4) makes recommendations to farmers whose economic sign is unknown, and in several cases probably negative.

## 2. Recommendation and scores

**Recommendation: Major revision.** The methodological core appears sound and is relevant to CEA. However, a paper in an applied agricultural journal that presents itself as practical guidance for overlap decisions must show, at least with a transparent partial-budget analysis, when the certified margin pays off relative to current practice. That analysis is feasible with data the authors already have (missed area $M$ is computed in every simulated run). It should be added before acceptance.

| Criterion | Score (1–10) | Comment |
|---|---|---|
| Novelty | 7 | Exact score, dominating reference plan, and the theory pivot for zero-history fields are new for agricultural guidance. The economic framing is not new and is absent. |
| Soundness (of the claims as they bear on practice) | 5 | The statistics are carefully done. The practical claims ("replace a fixed vendor overlap by a certified margin") are not supported by any cost–benefit evidence, and the miss criterion is not agronomically calibrated. |
| Practical relevance | 4 | Simulation only. The implement widths and field sizes are atypical for the operations where overlap costs most. Calibration requires ground-truth trajectories that farms do not have. Controller parameters are proprietary. |
| Clarity | 6 | The writing is clear and the status labelling is exemplary. It is heavy for the CEA readership, and no reader-facing quantity (EUR/ha, USD/ha, hours/ha) appears anywhere. |

## 3. Strengths

1. **Reliability is made explicit.** Replacing "twice the pass-to-pass spec" by a margin with a stated probability of complete coverage is the right type of quantity for a risk-based economic decision. The paper supplies the probability side of an expected-cost calculation that the precision-agriculture economics literature usually assumes away.
2. **Honest comparison with current practice.** The paper reports that the vendor rule never meets a 0.9 zero-miss target (P(no miss) = 0.000 under RTK) and that farmer-tuned overlap meets it on only 27–73% of fields (Section 6.3; Table S1–S3). Both are useful facts for the adoption discussion.
3. **The mixed-fleet result matches how farms and contractors operate.** Several machine configurations share one set of fields, and each field has one or two operations per year. This scenario (Section 6.6, Table 8) is the one where the method's value is largest and most credible.
4. **Low marginal computational cost.** The predictor takes 16–353 s per field offline (Table S21), so it imposes no hardware cost beyond standard guidance equipment. This matters for adoption.
5. **Transparent reporting of failures and post hoc analyses** (Tables 6, S20). This makes the evidence base easy to audit, including for an economic re-analysis.

## 4. Major issues

### M1. No monetary valuation of the overlap reduction (whole paper; Abstract; Tables 5, 7, 8; Section 7.4)

**Problem.** Every efficiency result is in percentage points of main-area overlap. The Introduction motivates the work with global pesticide tonnage (FAO, 2025) and nitrogen-use efficiency (Zhang et al., 2015, 2021). It never links a percentage point of overlap to a cost per hectare, per operation, or per farm and year. Readers of CEA, including extension staff, machinery dealers and farm managers, cannot judge whether a 1.96 pp reduction (R1 marginal, CE+ vs CPP) is worth €0.30/ha or €5/ha. The answer depends almost entirely on the operation: tillage, drilling, spraying or fertilising.

**Why it matters.** The guidance literature (Batte and Ehsani, 2006; Shockley et al., 2011, 2012; Lowenberg-DeBoer and Erickson, 2019) shows that adoption is driven by realised input and time savings per hectare relative to the annualised cost of the system. Without this conversion the paper's "4–55% less overlap" headline cannot be compared with the 5–10% overlap savings typically attributed to autosteer itself, or with automatic section control.

**Concrete fix.** Add a partial budget (see the proposed analysis at the end of this section). The overlap cost per hectare and operation is approximately

$$c_\text{ov}(\lambda)=J(\lambda)\,\big(p_\text{in}+c_\text{var}\big),$$

where $p_\text{in}$ is the input cost per hectare applied at full rate on overlap and $c_\text{var}$ is the variable machine, fuel and labour cost per hectare that scales with the number of passes. Report $\Delta c_\text{ov}$ for every row of Tables 5 and 8 under three or four operation profiles.

### M2. The value of the zero-miss guarantee is not quantified, and the missed area is never reported (Sections 3, 6.3, 7.4)

**Problem.** The objective treats any $M>0$ as failure, regardless of whether the missed area is one 1 m × 2 mm sliver or a 5 cm strip over the whole field. The paper never reports the distribution of missed area, $\mathbb E[M]$, $\mathbb E[M\mid M>0]$, or gap widths, for any method. This is true even for the vendor rule, which "misses on almost every run", and for the farmer-tuned rule. The Data section shows that $M$ is computed exactly on a 1 m grid in every run, so these numbers exist.

**Why it matters.** This is the central economic question. CE+ uses **more** overlap than the realistic practice baselines. In R1 it uses about 8.4% versus about 1.7% for the vendor rule: 6.7 pp more overlap, which costs roughly €7–17/ha per operation at the input profiles below. In v7 R3 it uses 16.0% versus 13.8% for farmer-tuned (Table S3). The certified margin is therefore an **insurance premium**. Its value depends on the expected damage of the misses it prevents.

A back-of-envelope calculation shows the answer can go either way. A wheat N skip with 30–50% yield loss on the missed strip, at 8 t/ha × €200/t, costs about €480–800 per missed hectare. The extra 6.7 pp overlap (about €10/ha) is therefore worth paying only if the vendor rule misses roughly ≥1.3–2% of the field area. That is a 4–6 cm mean gap on a 3 m implement. If vendor misses are millimetre slivers concentrated in a few sections, the certified margin destroys value. If they are centimetre-scale strips, it creates value. The paper cannot currently tell which.

**Concrete fix.**
- (a) For every method in Tables 5, S1–S3 and S8, report $\mathbb E[M/|W|]$, the 90th/99th percentile of $M/|W|$, and the mean and maximum gap width.
- (b) Report the break-even damage $D^\star=\Delta c_\text{ov}/\Delta\mathbb E[M/|W|]$ (€ per missed hectare) at which CE+ beats the vendor rule and the farmer-tuned rule. Compare it with literature yield-loss values for each operation.
- (c) Discuss whether the choice of $\varepsilon=0.1$ on a binary event is economically meaningful. The cost-optimal margin solves $\min_\lambda\ c_\text{ov}(\lambda)+D\cdot\mathbb E[M(\lambda)]/|W|$, a newsvendor-type problem. The authors already cite conformal risk control (Angelopoulos et al., 2024), which certifies $\mathbb E[\ell]\le\alpha$ for a monotone loss such as the monetised missed area. A cost-weighted variant would be a natural and short extension.

### M3. The geometric miss definition is not agronomically calibrated (Section 3, Lemma 1; Fig. 1)

**Problem.** A miss is any section where the executed footprints, modelled as hard intervals of width $w$, leave a gap of any size. Real operations differ:
- Sprayers and fertiliser spreaders have soft lateral deposition profiles with designed tail overlap, so a few-centimetre geometric gap does not mean zero dose.
- For drills, a gap smaller than the row spacing (12.5–25 cm) only widens one inter-row, and yield is largely compensated.
- For tillage, small skips are often agronomically irrelevant.

**Why it matters.** The zero-miss constraint determines the margin, and the margin determines overlap cost. A criterion that counts a 2 mm gap as a failure inflates the required margin in every regime. Theorem 6's $\sqrt{2\log N}$ scaling also means that this inflation grows with field size. This is the probable reason why the certified RTK margins are about 12 cm (R1, implied by the 8.65% oracle overlap at $w=3$ m) and 15 cm (R2, Table D.2 note), roughly 5× the 2.5 cm vendor pass-to-pass specification and well above field practice with RTK autosteer.

**Concrete fix.** Introduce an operation-specific tolerance $\tau$, so that a miss is counted only for a gap wider than $\tau$ (or a dose below a threshold under a deposition profile). In the score this is simply $S_\tau=S-\tau$, so all guarantees carry over. Report the margin and overlap for $\tau\in\{0,\ 2.5,\ 5,\ 10\}$ cm, linked to row spacing or nozzle spacing. This will probably change the practical conclusions more than any pivot choice in Sections 6.4–6.6.

### M4. The cost of collecting calibration runs is ignored, including the need for ground truth (Sections 4.2, 4.3, 6.7, 7.4)

**Problem.** Section 7.4 recommends CE+ "with at least 22 recorded operations on a field (at least 9 for a marginal guarantee)" and says that the field "is worked a few times per year" (Section 1). Three cost elements are absent.

1. **Time to certification.** At 2–4 operations per year with the same machine configuration, 9–22 runs take 3–10 years. The calibration is also only valid if the machine, controller, receiver and correction service stay unchanged throughout. The present value of savings that start years later should be discounted.
2. **Overlap cost during calibration.** Calibration runs must be driven at the inflated reference plan $\pi(\lambda_0)$, with $\lambda_0=1.25\times$ the largest training quantile. Every calibration operation therefore incurs the extra overlap $J(\lambda_0)-J(\hat\lambda)$. The headland probe line of CE+ also adds field time on every operation.
3. **Ground truth.** The exact score requires the **true** executed lateral offsets. A farm's as-applied log records the receiver's own position estimate, which contains the very GNSS error being certified. For example, RTK wrong fixes with a fix flag set (Table 1) are invisible in the machine's log. Section 6.7 plans a PPK rover as ground truth. This means every calibration run needs a second, independent positioning system: hardware or service at roughly €2–10k plus post-processing labour, or an equivalent contractor service. The same applies to the "one historical run per field" of CE-EVT-R: historical as-applied logs, which a farm actually has, are not the scores the method needs.

**Why it matters.** These are the dominant adoption costs. A guarantee that requires PPK ground truth on 25 fields before deployment has a very different return on investment from a software update.

**Concrete fix.**
- (a) State explicitly what data a farm must collect, with which equipment, and whether machine-log data (receiver position plus XTE) is sufficient. If it is not, quantify the bias of scores computed from receiver positions; the simulator can produce both.
- (b) Add the calibration costs to the partial budget: number of runs × extra overlap at $\lambda_0$, probe-line time, and the ground-truth system amortised over the fields calibrated.
- (c) Report a payback period or net present value for a representative farm.

### M5. The simulated configurations are not the ones where overlap costs most, and farm-size effects are not discussed (Table 2; Section 6.1; Table S21)

**Problem.** The regimes use implement widths of 1.5, 3 and 6 m. Overlap from a margin $\lambda$ is approximately $2\lambda/(w-2\lambda)$, so it scales inversely with implement width.

- **Width mismatch.** The operations where overlap is costly are spraying (€30–80/ha product per pass, several passes per year) and N fertilisation (€150–250/ha). These typically use 24–36 m booms or spread widths. With a 12 cm certified margin, overlap at $w=36$ m is about 0.7%, against 8.4% at $w=3$ m. Every pp figure in Tables 5, 7 and 8, and hence its economic value, would shrink by roughly an order of magnitude. Conversely, the 1.5 m R2 configuration has 24.9% oracle overlap. That is economically implausible for paddy operations in practice, and it shows the margin is large relative to the implement.
- **Field-size mismatch.** The R3 fields have 7–23 passes and 324–1016 m of total pass length (Table S21), i.e. roughly 0.2–0.6 ha. This is typical of hilly-south-China paddies, where RTK autosteer is rarely economic and where overlap is dominated by headlands. The main-area metric excludes headlands by construction (a 2w inset).
- **Geographic mismatch.** The GNSS series come from US CORS stations and the fields from China.

**Why it matters.** The paper's statements of which "farm types and operations benefit" are not supported. They cannot be, because the economically relevant configurations were not simulated.

**Concrete fix.**
- (a) Add at least one regime representative of a high-value broad-acre operation: a 24–36 m sprayer or spreader under RTK, ideally with section control modelled so that overlap at boundaries is partly removed.
- (b) Report applied overlap including headlands as a co-primary metric in the economic analysis.
- (c) Provide a table by farm archetype, for example a 100 ha mixed farm, a 1000 ha arable farm, a contractor with a mixed fleet over 3000 ha, and a smallholder paddy cooperative. Each archetype should state its operations per year, implement widths and input costs, and the resulting €/ha/yr and €/farm/yr.

### M6. Comparisons with current practice are not the ones that matter economically (Section 6.3, Table 5; Section 7.4)

**Problem.** The confirmatory efficiency claims compare CE+ only with two other **conformal** planners (CPP, Lindemann). Farmers do not use those. The relevant counterfactuals are the vendor rule, an operator-tuned fixed overlap, and autosteer with section control. Against these, CE+ is more expensive in overlap: vendor rule always, and farmer-tuned in R1/R3 of v7. Its benefit lies in reliability (M2). The mixed-fleet headline ("29.8 to 3.0 pp") is against raw pooling across configurations. No farm would do that, because the configurations are known and a per-configuration margin is trivial. The realistic configuration-aware comparators (spec × scale law: 12.8 pp; CQR: about 1.3 pp gap in v3, comparable under PAC) give much smaller or non-significant differences (Table S16).

**Why it matters.** The abstract and highlights could lead practitioners to expect large input savings from adoption. Relative to their current practice they may instead face higher overlap costs, compensated by an unquantified reduction in skips.

**Concrete fix.**
- (a) In the abstract, highlights and Section 7.4, state the overlap change relative to the vendor rule and the farmer-tuned rule, together with the change in expected missed area.
- (b) Present the mixed-fleet saving relative to the best configuration-aware comparator, with raw pooling as a secondary reference.
- (c) Add a per-configuration pooled conformal baseline (raw pooling within each configuration of the fleet). It is the obvious low-tech alternative a contractor could implement.

### M7. Adoption barriers are not discussed (Sections 7.3–7.4)

**Problem.** Several barriers are visible from the method description but are not discussed:
- **Proprietary controllers.** CE-EVT-R needs the closed-loop matrices $(A_t,B_t)$ of the autosteer controller, steering lag, saturation and rate limits. OEM autosteer controllers are closed, so a farmer or independent software vendor cannot obtain them without OEM cooperation.
- **Signal access.** CE+ needs the XTE of a headland probe line on every operation. XTE is available on most terminals but rarely exportable in real time.
- **Planning-software integration.** Fields2Cover-type planners and FMIS (farm management information systems) need an API through which the margin can be set per operation.
- **Liability and trust.** A "certified" margin that fails on 10% of operations by design may be harder to accept than a vendor rule whose failures are invisible.
- **Labour and skills.** Someone has to maintain a calibration pool and pre-registration-grade data hygiene.

The adoption literature (Lowenberg-DeBoer and Erickson, 2019; Schimmelpfennig, 2016) identifies data interoperability, skills and unclear ROI as the main barriers to precision-agriculture software. This method touches all three.

**Concrete fix.** Add a subsection "Implementation and adoption" covering: required data and who owns it; which components can run on existing ISOBUS terminals or FMIS; an OEM-integration pathway versus a retrofit pathway; and a simplified CE-EVT-R that uses only publicly specified quantities (vendor pass-to-pass accuracy, implement width, DEM), with its efficiency penalty quantified from the existing results (spec × scale law vs theory, Table 8).

### M8. Proposed economic analysis (to be added as a new Section 6.8 or 7.x, with a supplementary spreadsheet)

The following is a simple partial budget. It requires no new experiments beyond re-reading stored runs.

**Step 1 — Per-operation cost profiles (literature-based, to be refined by the authors with regional sources, e.g. KTBL for Germany, Iowa State Ag Decision Maker A3-29 for the US, China Agricultural Product Cost-Benefit Compilation for paddy).** Inputs are applied at full rate on overlap; $c_\text{var}$ scales with pass count.

| Operation | Typical width | Input cost $p_\text{in}$ (€/ha/op) | Variable machine + labour $c_\text{var}$ (€/ha/op) | Cost of 1 pp overlap (€/ha/op) | Damage per missed ha $D$ (€/ha) |
|---|---|---|---|---|---|
| Primary/secondary tillage | 3–6 m | 0 | 40–80 | 0.4–0.8 | low (≈ re-pass cost) |
| Cereal drilling | 3–6 m | 70–110 (seed) | 30–50 | 1.0–1.6 | low if gap < row spacing; 300–800 if strip |
| Maize/soybean planting | 6–12 m | 180–280 (seed) | 25–40 | 2.0–3.2 | 500–1500 |
| Herbicide/fungicide spraying | 24–36 m | 30–80 | 8–15 | 0.4–1.0 | 150–600 (weed escape / disease loss, seed-bank cost) |
| N fertiliser spreading | 24–36 m | 150–250 (≈180 kg N/ha × €0.9–1.3/kg N) | 8–15 | 1.6–2.7 | 400–800 (30–50% yield loss × 8 t/ha × €200/t) |
| Paddy operations (transplanting, fertiliser, pesticide) | 1.5–6 m | 50–150 | 20–60 | 0.7–2.1 | 300–900 |

Over-application also has an environmental cost. For N, an external cost of roughly €1–10/kg N surplus from the European Nitrogen Assessment range can be added as a sensitivity case.

**Step 2 — Overlap savings per hectare and operation.**
$\Delta c_\text{ov}=\Delta J\,(p_\text{in}+c_\text{var})$, applied to each row of Table 5, using the main-area overlap and the applied overlap from Table S22. Illustrative values from the paper's own numbers:
- **R1 (3 m drill profile, about €1.3/pp):** CE+ vs CPP, marginal (1.96 pp) gives about €2.5/ha/op. CE+ vs the vendor rule (+6.7 pp) costs about €8.7/ha/op.
- **R3 (6 m, paddy fertiliser/pesticide profile, about €1.4/pp):** CE+ vs CPP, marginal (4.9 pp) gives about €6.9/ha/op; PAC (6.6 pp) gives about €9.2/ha/op.
- **Mixed fleet (about €1.5/pp):** theory vs spec × scale law (9.9 pp marginal) gives about €15/ha/op. Theory vs one-run CQR (about 1.3 pp in v3) gives about €2/ha/op.
- **Wide-boom check:** rescale with $2\lambda/(w-2\lambda)$ to $w=24$–36 m. The same margins give roughly 0.5–1 pp overlap, i.e. savings below €1–2/ha/op even for N.

**Step 3 — Value of the miss reduction.** Using the stored runs, compute $\Delta\mathbb E[M/|W|]$ between CE+ and the vendor and farmer-tuned rules. The expected skip cost is $D\cdot\mathbb E[M/|W|]$. The net benefit per hectare and operation is
$$\text{NB}=-\Delta c_\text{ov}+D\,\Delta\mathbb E[M/|W|]-c_\text{cal},$$
and the break-even damage is $D^\star$. Present $D^\star$ by regime and compare it with column 6 of the table above.

**Step 4 — Calibration and adoption costs ($c_\text{cal}$).**
- Extra overlap of $n$ calibration operations at $\lambda_0$.
- Probe-line time per operation (perimeter share × $c_\text{var}$).
- Ground-truth system, e.g. PPK rover and processing at €3–10k, or contractor service per field, amortised over the calibrated fields and years.
- Software and integration, if any.

Discount the savings at 4–6% over a 5–7-year machine life.

**Step 5 — Farm archetypes and sensitivity.**
- Archetypes: 100 ha, 500 ha, 2000 ha, contractor 3000 ha with a mixed fleet, smallholder paddy cooperative.
- Report €/farm/yr, NPV and payback.
- Show a tornado chart over input price, implement width, $D$, $\tau$ (M3) and $\varepsilon$.
- Add the cost-optimal $\varepsilon^\star$ as a function of $D/(p_\text{in}+c_\text{var})$ (M2c), to show when a 0.9 target is economically justified and when 0.5 or 0.99 would be.

I expect this analysis to show the following, and the authors should report it either way. The method pays off mainly for contractors or large farms with mixed fleets and high-value, narrow-implement operations (seeding, paddy fertilisation), and where skips are costly (N, fungicide). Its value is small for wide-boom spraying with section control, and for any farm that would need to buy ground-truth equipment specifically for calibration.

## 5. Minor issues

1. **Introduction, paragraph 1.** Global pesticide tonnage and NUE motivate the problem but are not connected to overlap. Cite field evidence on overlap rates with and without guidance and on input savings from guidance and section control (e.g. Batte and Ehsani, 2006; Shockley et al., 2011, 2012) and state typical overlap percentages in practice.
2. **Introduction, last sentence of paragraph 1.** A market-research report (Global Market Insights, 2026) is weak support for the autonomy trend. Use peer-reviewed sources (e.g. Lowenberg-DeBoer et al., 2020, *Precision Agriculture* 21, 278–299, on the economics of autonomous field machines). That paper also argues that small autonomous machines (narrow implements) can be economic, which would partly rehabilitate the 1.5–6 m widths if the authors frame them that way.
3. **Section 3, objective.** $J$ counts overlap geometrically. State whether overlapping strips are assumed to receive the full double dose, i.e. no section control and no rate compensation. With nozzle-level section control, interior overlap of the outermost nozzle can be switched off, which changes the economic meaning of $J$.
4. **Section 4.2.** The headland probe line adds non-productive time on every operation. Report its length or time share per field.
5. **Section 4.4.** Runtime is reported, but not the analyst time or skills needed to parameterise the theory (controller model, slip model, DEM processing). This is an adoption cost.
6. **Section 6.1.** The speed of 2 m/s (7.2 km/h) is low for spraying (typically 8–15 km/h) and for modern drills. Error dynamics, and hence margins, depend on speed. State the expected direction of the effect.
7. **Table 2.** Add the typical operation each regime represents (e.g. "3 m drill", "1.5 m paddy transplanter", "6 m spreader"), with field size statistics (mean and range in ha).
8. **Table 5 / Fig. 3.** Add columns for the vendor and farmer-tuned rules from the same v8 fields, if they were run. The economically relevant contrast is missing from the confirmatory table.
9. **Section 6.6, "Configuration-blind pooling pays for the widest-error configuration on every field."** True, but a practitioner would never pool across a known configuration. Rephrase so that raw pooling is not presented as a realistic comparator.
10. **Section 7.4, bullet 1.** "Replace a fixed vendor overlap by a certified margin" is an economic recommendation. Qualify it with the net-benefit condition from M2 and M8, or rephrase as "where the cost of a skip exceeds $D^\star$".
11. **Section 7.4, bullet 4.** "At least 22 recorded operations on a field" should be accompanied by the calendar time this implies and by the requirement that the configuration be unchanged.
12. **Section 7.3, limitation 6.** Promote applied overlap including headlands to a co-primary cost metric for small fields. For 0.2–0.6 ha R3 fields, headlands are a large share of the area and of the overlap.
13. **Section 6.1, Data.** Using US CORS GNSS errors for Chinese fields is defensible for RTK. For DGPS, regional correction services (e.g. BeiDou-based SBAS, BDSBAS) differ, and the economic conclusions for R3 depend on this. Note it.
14. **Abstract and highlights.** "4–55% less overlap" is a relative reduction of a quantity that is itself a few percent. Give the absolute pp range (about 1.1–23.4 pp in Table 5) to avoid overstating savings.
15. **Appendix E** is still in the supplementary file and must be removed before submission. The "TODO" in Section 6.7 and the Data availability section must also be resolved.

## 6. Questions to the authors

1. What is the distribution of missed area (fraction of $|W|$, gap width) under the vendor rule, the farmer-tuned rule, CE+ and CE+ PAC in each regime? Are the vendor rule's misses millimetre slivers or centimetre strips?
2. Can the exact run score be computed from data a commercial tractor already logs (receiver position, XTE, implement state)? If not, what equipment and cost per field are needed to obtain one calibration run?
3. How does the certified margin, in cm and as overlap, change with implement width at 12, 24 and 36 m under RTK? Is the margin approximately width-independent, so that overlap scales as $1/w$?
4. How sensitive are the margins to an agronomic tolerance $\tau$ (M3)? What $\tau$ would you consider appropriate for drilling, spraying and spreading?
5. Is $\varepsilon=0.1$ motivated by any cost consideration? Would a cost-weighted risk-control formulation (expected monetised missed area) give materially different margins?
6. In the mixed-fleet scenario, what is the efficiency of a per-configuration pooled conformal margin? It is the simplest alternative a contractor would use.
7. For the "many fields, one or two operations each" use case, how long (in seasons) does a typical contractor need to assemble a calibration pool of 25 fields with ground truth? Does a change of receiver, correction service or controller firmware invalidate the pool?
8. Would OEMs need to expose controller parameters for CE-EVT-R? How much efficiency is lost if only public specifications (width, vendor pass-to-pass accuracy, DEM) are used? Table 8 suggests about 10 pp in the mixed fleet; is this the right reading?
9. Do you see the method primarily as a planning-software feature (FMIS/terminal), an OEM controller feature, or a contractor service? Who captures the value and who bears the calibration cost?

---

*References suggested in this review (for the authors to verify and use as appropriate):* Batte, M.T., Ehsani, M.R., 2006. The economics of precision guidance with auto-boom control for farmer-owned agricultural sprayers. Comput. Electron. Agric. 53, 28–44. — Shockley, J.M., Dillon, C.R., Stombaugh, T.S., 2011. A whole farm analysis of the influence of auto-steer navigation on net returns, risk, and production practices. J. Agric. Appl. Econ. 43(1), 57–75. — Shockley, J., Dillon, C.R., Stombaugh, T., Shearer, S., 2012. Whole farm analysis of automatic section control for agricultural machinery. Precis. Agric. 13, 411–420. — Lowenberg-DeBoer, J., Erickson, B., 2019. Setting the record straight on precision agriculture adoption. Agron. J. 111, 1552–1569. — Lowenberg-DeBoer, J., Huang, I.Y., Grigoriadis, V., Blackmore, S., 2020. Economics of robots and automation in field crop production. Precis. Agric. 21, 278–299. — Schimmelpfennig, D., 2016. Farm profits and adoption of precision agriculture. USDA ERS Economic Research Report 217. — Edwards, W., Iowa State University Extension, Ag Decision Maker A3-29, Estimating farm machinery costs. — KTBL, Betriebsplanung Landwirtschaft (current edition).

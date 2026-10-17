# Associate Editor report, round 2: Computers and Electronics in Agriculture

**Manuscript:** "A calibration method for setting pass overlap with a guaranteed probability of no missed strips in agricultural coverage path planning"
**Article type:** Research paper (methods)
**Files assessed:** `docs/paper/manuscript.md`, `docs/paper/latex/manuscript.pdf` (37 pp.), `figures/paper/fig_workflow.png` (Fig. 1), `figures/paper/fig_schematic.png` (Fig. 2), plus the remaining main-text figures and tables.

---

## 1. Recommendation

**Send to reviewers after a minor technical return.** The paper does not need a rejection or another full restructuring.

The move from a theorem-centred paper to a method paper has largely worked. A CEA reader can now see from the abstract, Fig. 1 and Section 3.2 that the paper offers a four-step procedure that takes logged runs and returns a pass margin. The problem statement (3.1) and Fig. 2 are clear, and the honest reporting of failed and partly met claims is a strength. Before reviewers see the paper, however, I want the authors to fix the following:

1. **Step 4 is defined inconsistently, and the fallback may be invalid.** The transfer check is described in three different ways, and the headline numbers were computed without it (M1).
2. **Section 3 is incomplete as a method description.** The step structure has no Step 1 or Step 4 subsection. Results are mixed into the method section. The paper has no algorithm box, no worked example and no table of the inputs a user needs (M2, M3).
3. **Revision-process residue remains.** The text contains "(revision)" tags, repository names, a "Pivot" table header and the B1–B3 history table. These make the paper read like a response letter (M4).
4. **The paper is too long.** The main text, tables included, is about 10,400 words, and Results alone is 4,500 words. About 2,000 words and one figure should go to the Supplement (M5).

None of these items requires new experiments, apart from recomputing the CE+ R3 summaries with the transfer check applied, and those data already exist (Section 4.2, "Transfer check").

---

## 2. Is the contribution clear? (title, abstract, highlights, introduction, Fig. 1)

**Overall, yes.** The abstract gives the problem, the method in three sentences, the two data settings, the results and the boundary conditions, and it is 249 words long. All five highlights are within 85 characters. Fig. 1 is the right figure to put first.

### Title

The current title has 24 words and is too long. It also states the product before the problem, and "guaranteed" overclaims. The guarantee is marginal or PAC and is averaged over runs, and for fields without history it is averaged over fields. For every deployed variant except CE it also rests on assumption (S). Reviewers from the statistics side will object to "guaranteed", and reviewers from the agricultural engineering side will object to a guarantee demonstrated only in simulation. The title also omits the method's name, which is a pity because the name is used everywhere else.

Suggested titles, in order of preference:

- **"Calibrating pass overlap from logged runs to bound the probability of missed strips in agricultural field coverage"** (17 words)
- "Conformal erosion: setting pass overlap with a stated probability of missed strips for agricultural coverage planning"
- "How much overlap is enough? Conformal calibration of pass margins for complete field coverage"

If "guarantee" is kept, it should be qualified, for example "with a finite-sample guarantee", and the abstract should then say "in probability, averaged over runs (or fields)".

### Abstract

- **Sentence 2:** "conformal erosion" appears without a gloss. Add "(conformal prediction applied to an eroded, i.e. narrowed, implement footprint)". CEA readers will not know the term.
- **"held its target miss probability in every check under the nominal simulator":** B2 and B3 each realised one coverage value below 0.9 (0.844 and 0.877). B4 shows that these values are draws of the calibration data, but a reviewer will find them and cite the abstract back at the authors. Suggested wording: "...held its target miss probability on average over calibration data in every check (Experiment B4)...".
- **"1.2–4.4 for configuration-aware baselines":** the vendor-specification scale is also configuration-aware, and it cost 9.9 pp (Table 6). Either write "learned, empirical and per-configuration baselines" or widen the range.
- **"4–55%":** with the transfer check that the method now requires, the R3 figures change (see M1). The abstract must report the method as defined.
- **Last sentence:** "30–100 times" does not match Section 4.5. The break-even values there are 43/58/88 on the margin curves and 31–35/88–117 on A1, so the A1 DGPS range exceeds 100. Write "about 30–120 times", or state which analysis the range comes from.

### Highlights

They are acceptable. Highlight 4 should say what "target held" means, for example "Simulation: miss level held; 4–55% less overlap than conformal planners". In Highlight 5, "30–100x an overlap" should read "30–100 times an over-applied area".

### Introduction

- **Paragraph 1:** the last sentence ("Autonomous machines remove the operator who used to correct visible gaps by eye") is the strongest motivation for the paper but reads as an afterthought. Move it up. A suggested ending for the paragraph: "...Both errors carry a cost (...). On autonomous machines no operator is present to see and correct a gap, so the margin must be right in advance."
- **Paragraph 2:** this paragraph repeats Section 2 almost citation for citation (Galceran, Höffmann, Mier, Hameed, Lenain, Pannocchia, Mayne, Lindemann, Zhao). Cut the citations here to one sentence per field ("CPP assumes perfect execution; control reduces error but does not state a miss probability; conformal planners do not handle...") and leave the detail to Section 2. That saves about 120 words.
- **The three-feature gap statement** (worst of many pairs; reference vs deployed plan; few runs per field) is the core of the paper and is buried at the end of a long paragraph. Make it a separate short paragraph, or a three-item list, and map each gap explicitly to a contribution.
- **Contribution order:** the contributions are listed as 1 = CE, 2 = XCE, 3 = score, but the workflow order is score, then CE, then XCE. Put the score first, because the other two depend on it. This also matches Section 3.
- **Contribution 3:** "no other score that certifies complete coverage is smaller" is a theorem-style claim. Rephrase it as a benefit: "...so the calibrated margin is never larger than with per-pair scores used by earlier conformal planners."

### Fig. 1 (workflow)

The concept is good, but the figure needs four fixes.

1. **Data flow.** The "calibration data" arrows from the two grey boxes go directly into box 3. Data first pass through box 2 (scoring), so the arrows should enter box 2 or the line between boxes 2 and 3. As drawn, scoring looks as if it applies only to some other stream.
2. **Box 4.** Box 4 says "if λ̂ > λ_ref, keep the reference plan". This contradicts Section 3.2 ("refuses the deployment") and Section 3.4 ("fall back to CE"), and it may be invalid (see M1).
3. **XCE box.** The XCE box should state that the model needs no run data. That is the key point and is currently only implicit.
4. **Typography.** "k⋆-th" renders with a detached star. Use plain text, for example "margin = k-th smallest score, k = ⌈(n+1)(1−ε)⌉".

### Fig. 2 (schematic)

This is a clear, effective figure. Specific fixes:

- **Panel (c).** The formula reads S = λ + max_x(...), but the text (Eq. for S, Section 3.3) uses λ_ref. Use λ_ref in the figure.
- **Panel (b).** The label "widest gap 12 cm" sits at the top right, next to a footprint-edge line at y ≈ 4.2 m that belongs to a pass outside the panel, and not next to the red strip at y ≈ 0. Move the label next to the red strip. The dotted edges at +4.2 and −5.1 m belong to passes that are not shown. Either show those centrelines or crop the y-axis to about [−4, 4] so that the reader sees only the two passes involved. The empty band below −5 m and the legend overlapping data can then be removed.
- **Panel (a).** The planned overlap is λ = 0.39 m on a 6 m implement, so the figure looks gapless except for the red strip. That is fine, but the caption should give λ, to link it to Tables 7 and 8.

---

## 3. Major issues

### M1. Step 4 (transfer check) is inconsistent across the paper and was not applied to the headline results

The transfer check is now part of the method (Section 3.2, step 4; Section 5.5; Conclusion item 3), but it is described in three incompatible ways:

- Section 3.2: "refuses the deployment if λ̂ > λ_ref";
- Fig. 1, box 4, and its caption: "keep the reference plan" / "falls back to the reference plan";
- Section 3.4: "must refuse ... and fall back to CE".

These are not equivalent. If the calibrated margin exceeds λ_ref, the reference plan itself is likely to have a miss probability above ε, so "keep the reference plan" is not a valid fallback. Falling back to CE requires CE's pilot and certificate batches, that is, additional runs that a CE+ user may not have. It is also not stated how the check works for XCE. A target field without history has no logged reference plan, so the paper must say what λ_ref means for field g, and whether the check is λ_g ≤ λ_ref,g.

**Required:**

- One precise definition of Step 4 for every variant, in the new Section 3.6 (see M2) and in the algorithm box.
- Fig. 1 and its caption corrected to match.
- Results for the method as now defined. Table 4 reports CE+ in R3 without the check, although 9 of 30 fields (marginal) and 19 of 30 (PAC) would have triggered it. Add a row "CE+ with transfer check" to Table 4, using the CE fallback reported in Section 4.2 (17.77%, P 0.928), and recompute the R3 reductions quoted in the abstract, highlights and conclusion. The original pre-registered row should stay, labelled as such.
- The same applies to C1/T1 in Table 7. Report what the check would have refused, and what the refused fields would cost under the fallback.

The authors can do this from existing results. Without it, a reviewer will rightly say that the headline numbers belong to a method that is not the one described.

### M2. Section 3 is incomplete as a method description

The order of problem, overview, steps, assumptions and simulation design is right, but the step sections do not match the four steps of Section 3.2 and Fig. 1.

| Fig. 1 step | Current location | Proposed |
|---|---|---|
| 1 Reference plan | no subsection; choice of λ_ref is scattered (×1.10 in CE, ×1.25 in CE+, "generous" in 3.2) | 3.3 "Steps 1–2: reference plan and coverage score", including a rule for choosing λ_ref |
| 2 Coverage score | 3.3 | same, with tolerated gap width τ (currently 3.6) folded in as a variant of the score |
| 3a/3b Calibration | 3.4, 3.5 | 3.4, 3.5 |
| 4 Plan and deploy, transfer check | paragraph "Transfer check (revision)" in 3.4, and a bullet in 3.7 | **new 3.6 "Step 4: deployment and transfer check"** |
| Assumptions | 3.7 | 3.7, shortened (see below) |
| Computational cost | in 3.7 | move to the end of 3.6 or to 4.x/5 |

The following material in Section 3 is misplaced:

- **Results inside the method.** The following belong in Section 4 or the Supplement:
  - 3.3: "On 6 fields × 200 runs the score reproduced the missed-area outcome on every run";
  - 3.5, step 3: "(0.888, 0.882 and 0.900 against a true 0.900; Table S5)";
  - 3.5, "Why the field-edge terms matter": binding shares of 1%/10% and 0.1%/1.9%, which duplicate C2 verbatim;
  - 3.7: "predicted coverage after a plan change was 0.901, 0.890 and 0.920...";
  - 3.7: timings, which also disagree with 4.1. Section 3.7 gives 16–353 s for XCE-T, while 4.1 says a median of 271 s and up to 40 min with edge terms.
- **XCE-T in five steps (3.5).** The method needs only "a model that predicts q̂_f from field properties without run data". The five-step analytic recipe, with its Lyapunov recursion, Kac–Rice sums, product over pairs, mixture and scale law, is a component, not the method. Reduce it to three or four sentences plus a pointer to Appendix B. Step 5 (scale law) is "used only for a comparator scale" and should not be in the method at all. The "Why the field-edge terms matter" paragraph should become two sentences in 3.3 (edge terms are part of the score) plus a pointer to C2. The ratio-vs-PIT sentence ("failed in the first zero-data experiment") is history and belongs in the Supplement.
- **CE+ (3.4)** is a long paragraph of tuning constants: 1.25×, 0.3 σ̄, the 3% gate, median normalisation. Move the constants to a table of settings, which could be part of the inputs table below. Say plainly in the text that CE-q is the core variant and CE+ an optional refinement. The results support this: "Most of the gain comes from the exact score and the reference plan, not from the probe-line normalisation".
- **3.7, "What no scale can remove"** and the Beta(k⋆, n+1−k⋆) standard-deviation discussion are theorem-centred residue (see M4). Keep one sentence each and move the rest to Appendix A.
- **3.1 Objective.** The optimisation problem min J s.t. P ≥ 1−ε is never actually solved. The method returns a data-driven margin that is feasible in probability. Add one sentence: "The method does not compute the minimiser, which needs the unknown distribution of e; it returns the smallest margin that the logged data certify (the oracle λ⋆_f of Section 3.8 is the minimiser)." This also introduces regret.

The following are missing, and CEA readers expect them in a methods paper:

1. **An algorithm box** ("Algorithm 1. Conformal erosion"), giving the inputs; steps 1–4 with the marginal and PAC k⋆; the branch for fields with and without history; the transfer check and fallback; and the output (deployed plan, or refusal). About 15 lines. It replaces much of the prose in 3.2 and 3.4.
2. **A worked numerical example.** Take one R1 field, n = 29 logged runs and ε = δ = 0.1. Show k⋆ = 27 (marginal) and k⋆ for PAC, the 27th score (e.g. 4.1 cm), the resulting λ̂, K(λ̂) passes against K(λ_ref), and the overlap J. Then show one XCE case: q̂_g = 3.6 cm, v⋆ = 1.12, so λ_g = 4.0 cm. This takes half a page or a small table, and it is the single most effective way to make reviewers "get" the method.
3. **A table of inputs and requirements**, with one row per variant: data required (number of runs, on which plan); ground-truth requirement (implement track with independent reference such as a PPK rover, currently stated only in Limitation 2); model inputs for XCE (controller parameters, DEM, GNSS grade, simulator or analytic model); settings (ε, δ, τ, the λ_ref rule, CE+ constants); computing time; and output. This also answers the question a practitioner will ask first: what do I need to log?
4. **Questions mapped to experiments.** Section 3.8 lists experiments by repository history (A1, A2, B1–B6, C1, C2). State instead the questions the study answers, for example: Q1, is the score exact (3.3 check); Q2, with history, is calibration valid and tighter than conformal planners, and what does it cost with few runs (A); Q3, without history, is cross-field calibration valid per configuration and efficient (B); Q4, how sensitive are validity and efficiency to model error (C); Q5, when is the certified margin worth its cost (cost analysis). Then use the same Q-numbers as the subsection titles of Section 4.

### M3. Results and Discussion do not follow the order of the method section

- **4.1 "How accurate is the model scale?"** comes first, but the model scale matters only for XCE (step 3b, Experiment B). Opening Results with model-versus-simulator scatter (Fig. 3), which the authors themselves call "internal consistency, not realism", foregrounds the weakest part of the paper. Move it into 4.3 as its first subsection ("4.3.1 Accuracy of the model scale"), and merge it with B6 (learned predictors), which asks the same question.
- **Proposed Results order:** 4.1 score exactness (short, moved from 3.3); 4.2 fields with history (A1, A2, transfer check, other stacks); 4.3 fields without history (model accuracy with B6, then B4 validity, then B5 per-configuration and efficiency, with B1–B3 summarised in one paragraph and Table 5 moved to the Supplement); 4.4 robustness (C1, C2); 4.5 cost.
- **Discussion 5.1 "What is guaranteed, and by what"** is a near-duplicate of Section 3.7, written in the three-layer language of the old version. Cut it to three or four sentences that state what the *experiments* showed about each layer, and leave the assumptions themselves to 3.7.
- **The Discussion has no comparison with agricultural engineering practice or literature.** CEA reviewers will look for:
  - typical overlaps reported in practice and in overlap and skip studies, against the 8–25% main-area overlaps found here (R2 at 25% will raise eyebrows);
  - **automatic section control and boom shut-off**, which reduce the cost of overlap and so change r in Section 4.5;
  - whether the method fits into ISOBUS or task-controller workflows (the margin as a guidance-line spacing parameter);
  - how a contractor would obtain the independent ground truth that the score requires.

  Add a short subsection "5.x Relation to practice", of about 250 words.
- **5.2:** "the farmer-tuned margin was within a few tenths of a point in R1" is wrong. Table 4 gives 9.22% against 8.39%, which is 0.83 pp. Write "0.8 pp above CE+ in R1".
- **5.3 versus 5.5 and the abstract:** 5.3 says a zero-miss margin "is not cost-optimal for RTK guidance unless a missed unit costs several hundred times an over-applied one", while 5.5 and the abstract give 30–100 as the break-even. The two numbers answer different questions: break-even against the vendor rule, and the point where the cost-optimal margin approaches the 0.9 level. Name the comparison in each place, or readers will think the numbers contradict each other.

### M4. Residue of the old theorem-centred and revision-history structure

- **"(revision)" / "(revision, pre-registered)" tags:** there are 15 in the md and 11 in the compiled tex. Examples are "Transfer check (revision)" in 3.4, A2, B5, C1, C2, and in 4.1. A reader of the published paper does not know there was a revision. Use "pre-registered" or "exploratory" only, and keep the timing history in Table S20 and the response letter.
- **Internal names:**
  - "(repository 'v8')" and "('E-low v1–v3')" in 3.8;
  - "In the pre-registrations XCE-T is called CE-EVT-R" (Table 2 caption);
  - the file name `fig_v8_regret`;
  - the table header **"Pivot"** in Table 6 (the method text says "scale"; the old paper said "pivot").

  Move the name mapping to the Supplement next to the pre-registration links, and rename the header "Scale".
- **Source comments:** `<!-- source: ... -->` comments remain in the md. They are invisible in the PDF, but they must not reach the submission system; the previous AE report asked for them to be removed.
- **Terminology:** both "regret" (Table 4, Fig. 4) and "excess overlap" (Tables 5–7, Fig. 5) are used for the same quantity. Pick one; "excess overlap" is clearer for CEA readers. Define it once in 3.8 and use it in the nomenclature.
- **Table 5 (B1–B3):** this is the history of how the zero-data method was found. It includes a failed scale that is not part of the method. It is honest and must stay available, but in the Supplement, with a single summarising paragraph in 4.3: "Three earlier pre-registered zero-data experiments (Supplement D) led to the ratio scale used here; one failed, one was met, one was partly met."
- **Section 2, "Extremes of Gaussian processes":** this related-work paragraph supports only the analytic component. Move it to Appendix B.

### M5. Length and balance

| Part | Words (incl. tables) | Comment |
|---|---|---|
| Introduction | ~890 | could lose ~150 (para. 2 duplicates Section 2) |
| Related work | ~300 | fine; move the Gaussian-extremes paragraph |
| Materials and methods | ~3,600 | should be ~2,800 after moving results and XCE-T detail out, *plus* the algorithm box, worked example and inputs table |
| Results | ~4,480 | should be ~3,000 |
| Discussion | ~910 | ~800 after cutting 5.1, plus ~250 for "relation to practice" |
| Conclusion | ~275 | fine |

The target is about 8,000 words of main text including tables, with 6 figures and 8 tables. Specific candidates to move to the Supplement:

1. **Table 5 (B1–B3)** and its paragraph (~250 words). See M4.
2. **Fig. 4 (A1 excess-overlap bars)** duplicates the Regret column and P(no miss) of Table 4. Either drop the Regret column from Table 4 and keep Fig. 4, or move Fig. 4 to the Supplement. I prefer moving the figure. This frees a slot for the algorithm box, if the authors count it as a figure.
3. **B6 (learned predictors, post hoc)** (~180 words). Merge two sentences into the new model-accuracy subsection and move the numbers to Table S25.
4. **C1 paragraph (~520 words in one paragraph).** Split it under three run-in heads (Validity / Model accuracy / Per-configuration coverage), and move the P4.1–P4.4 bookkeeping (last sentence) to Table S27.
5. **XCE-T five-step description and scale law (3.5)**, ~300 words, to Appendix B.
6. **"Other stacks" and "practice rules" paragraphs in 4.2.** Keep them, but cut each to two sentences.
7. **Table 3** could be merged into Table 1 as extra columns, or Table 1 shortened to three grades (Single point is unused). This makes room for the inputs table without increasing the table count.

With these moves, the figure count stays at 6 if the algorithm is set as a box (Elsevier allows algorithm boxes outside the figure count), and the table count stays at 8: Table 5 out, inputs table in.

---

## 4. Minor issues and flow (location, then fix)

1. **Nomenclature, κ:** it points to "Section 3.7", but κ is never given a value or formula in the main text. Give its expression or a range ("κ ≤ 1.02 on the R1 fields").
2. **Nomenclature, "pp":** define it in the abstract, where it first appears ("percentage points").
3. **§1 para. 2, "a conformal margin at a miss level of 10% needs at least 9 (marginal) or 22 (PAC) logged runs":** add "on the same field". Otherwise the motivation for XCE is unclear.
4. **§1 para. 4 (pre-registration sentence):** this sentence interrupts the move from contributions to roadmap. Put it after the contribution list as its own short paragraph, or into 3.8.
5. **§3.1 "Execution", last sentence ("Coverage is evaluated on 1 m sections across W"):** "across" suggests transverse. Write "along the working direction, in sections 1 m long".
6. **§3.1 "Objective":** "(here 0.1)" should be "(0.1 in all experiments)".
7. **§3.2 step 3:** "chosen so that a new run exceeds it with probability at most ε" should be "...at most ε, on average over the calibration data (marginal rule) or with confidence 1−δ (PAC rule)". The distinction matters later and should be introduced here.
8. **Table 2:** "Score scale" for CE+ says "probe-line XTE, gated", and "gated" is undefined at this point. Also, "assumption-free (Appendix A.4)" in the last column should read "exchangeable runs only".
9. **§3.3, first sentence:** "the executed centres of the passes relevant to the chord" is vague. Define "relevant" as "whose footprint intersects the chord, or the nearest pass on each side".
10. **§3.3, last paragraph:** "deploys no more passes with this score than with any other such score" is a dense double negative. Rewrite: "Because it is the smallest valid score, any order-statistic rule gives a margin at least as small with it as with any other valid score, including the per-pair maxima of earlier conformal planners."
11. **§3.4 CE paragraph:** the long sentence "CE iterates pilot batches, λ_ref ← 1.10 q ... (refusing otherwise)" packs four steps into one. Make it a four-item list, or move it into the algorithm box.
12. **§3.5, "Why the field-edge terms matter":** the sentence "in the 1 Hz DGPS series, the correlation at the 13–113 s between adjacent passes at one section is 0.91–0.41" is ungrammatical. Rewrite: "in the 1 Hz DGPS series, the correlation of the lateral error at lags of 13–113 s (the time between adjacent passes at one section) is 0.91–0.41; for RTK it is 0.71–0.54."
13. **§3.5 step 3:** "approximated by the product over pairs; this product was accurate in validation" should give the validation in the Supplement, not here (M2).
14. **§3.7, bullet 2:** "(1−ε)^{K1/K0}" assumes i.i.d. pair scores. Say that it is an illustration, not a bound.
15. **§3.8 "Data":** "density-based clustering extracts 964 fields, of which 137 paddy fields ... and 162 wheat fields ... are used" does not explain why the other 665 are unused. Add the selection criterion.
16. **§3.8 "Metrics", meet rate:** "a correctly calibrated marginal method meets it on about 85% of fields". Explain in one clause why this is not 100%; otherwise reviewers will read 0.90 meet rates as failures.
17. **§3.8, last paragraph:** "All registered zero-data experiments used the extreme-value model without the field-edge terms; validity is unaffected" belongs in 4.3, where readers meet the two XCE-T rows of Table 6.
18. **§4.1, sentence 3:** "its own error, net of the reference noise, is therefore about 2–3% under RTK" should show the arithmetic (√(0.039² − 0.030²) ≈ 0.025) or drop "therefore".
19. **§4.1:** the sentence on timing (16–353 s, 271 s, 40 min) duplicates and contradicts 3.7. Keep one version (M2).
20. **§4.2 A1, first sentence:** the claim definitions V and E run to 70 words before any result. Lead with the outcome: "Both registered claims, validity (V) and lower overlap than CPrP and UBCP in both guarantee classes (E), were met in every configuration (Table 4)", and put the exact criteria in the table footnote.
21. **§4.2, "What the gain is made of":** "at equal realised coverage they would deploy the same plan" overstates the case, because different λ choices give the same plan only when coverage is matched on every field. Write "...differ only in how λ is chosen; the gain is therefore calibration tightness, not a better plan family."
22. **§4.2, "Transfer check":** "on those fields the guarantee rests on no theorem" is a theorem-centred phrase. Write "on those fields the transfer assumption is not met, so coverage is not guaranteed".
23. **§4.2 A2, last sentence:** "With fewer than about 20 logged operations per field, cross-field calibration (Experiment B) is the practical route" is a good bridge. Make it the first sentence of 4.3 as well, to motivate Experiment B.
24. **§4.3 B4 heading, "does the guarantee hold?":** use the same heading style as the other subsections (no question marks inside run-in heads, or questions throughout).
25. **Table 6 caption:** "values below 0.88 are in bold" conflicts with Table 7's "below 0.895 overall, or below 0.85 for one configuration". Use one rule in both.
26. **Table 7, T3 row:** "(R3 under-covered)" in a numeric column is hard to read. Give the numbers, flagged with a footnote symbol.
27. **§4.4 C2, first sentence:** "The main experiments evaluate the main-area boundary as a hard edge reached only by the outermost pass" reads awkwardly. Write "In the main experiments, only the outermost pass can cover the edge of the main area; C2 adds one headland lap per side, planned to overlap the main area by λ and driven after the infield passes."
28. **§4.5, first sentence:** "The certified event ... counts a 1 cm sliver like a 1 m strip" is a good opening. Keep it, but put the definition of r before Table 8 is mentioned, and give r* the symbol r_be (break-even), because r* collides with r⋆(x) of Section 3.3.
29. **§4.5, "Three conclusions follow" paragraph:** each conclusion is several sentences long. Use an enumerated list, as in the Conclusion.
30. **§4.5, last paragraph:** the illustration "a fertiliser strip whose omission loses a third of a crop worth five times the fertiliser cost gives r ≈ 1.7" is useful but should cite a source for the yield loss, or be labelled hypothetical.
31. **§5.4, item 2:** "Field validation ... is in preparation (logging and certification tools are in the repository)". Reviewers may ask for it. Either give a timeline, or drop "in preparation" and state that field validation is outside the scope of this paper.
32. **§5.5:** the bullets are good. Order them as the algorithm runs: (1) decide r, ε and τ; (2) log runs with ground truth; (3) choose a reference plan; (4) calibrate (with or without history); (5) apply the transfer check; (6) headland laps. Currently the reference-plan rule (bullet 3) comes before the choice between CE and XCE.
33. **§6, item 2:** "was the only scale that served every machine configuration of a mixed fleet efficiently" needs qualification. Under T2, T4 and T6 it did not (DGPS coverage 0.78–0.81). Add "under the nominal simulator".
34. **Fig. 3 caption:** say in the caption that both axes compare the model with the simulator it was built from. Section 4.1 says this, but figures are read in isolation.
35. **Fig. 5 caption:** it is long and mixes n = 60 and n = 25 panels. State the n in each panel title as well.
36. **Fig. 6 caption:** "The vertical line marks where the certified margin becomes cheaper than the vendor rule" should add "(r_be)" to link it to the text.

---

## 5. What reviewers will most likely raise (for the authors' preparation)

- **Simulation only.** Ground truth requires an independent implement-position reference, and the GNSS series come from US CORS stations while the fields are in China. The limitation is stated clearly, but at least one CEA reviewer will want a small field demonstration, even a single field with a PPK rover and about 10 runs, to show that the score can be computed from real logs. If this exists by resubmission, include it.
- **R2 overlap of about 25%.** This will look implausible to practitioners. Explain it in the text: 1.5 m implement, hilly and wet terrain, and an absolute margin comparable to a much larger relative share of the swath.
- **The cost analysis undercuts the zero-miss objective for most operations.** That is honest, but the Discussion should then say clearly which operations the method targets: those with high r, such as quarantine treatments, herbicide-resistance management and seeding gaps in high-value crops. Or reposition the method as "states the miss probability of any margin", which the data support.

---

## 6. Summary for the authors

The paper is close to being reviewable as a methods paper. The key actions are:

- **(i)** make Step 4 unambiguous and report results with it applied;
- **(ii)** give Section 3 one subsection per workflow step, plus an algorithm box, a worked numerical example and a table of inputs;
- **(iii)** move model accuracy into the no-history results and reorder Results to follow the method;
- **(iv)** remove revision and repository residue, and the B1–B3 table, from the main text;
- **(v)** cut about 2,000 words, mainly the XCE-T recipe, results quoted inside Section 3, C1 detail and Discussion 5.1;
- **(vi)** add a short comparison with practice, covering section control, typical overlaps and ground-truth logging;
- **(vii)** shorten and qualify the title.

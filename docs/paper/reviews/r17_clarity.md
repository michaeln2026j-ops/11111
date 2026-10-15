# Review R17: Scientific writing and clarity

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations"
**Journal:** Computers and Electronics in Agriculture (COMPAG)
**Reviewer role:** Scientific writing and clarity (native English academic editor, engineering background)
**Material reviewed:** `docs/paper/manuscript.md` (all 523 lines), the eight PNGs in `figures/paper/` (Figs. 1-7 and the graphical abstract)

---

## 1. Summary

The paper asks how much overlap between adjacent passes a field operation needs so that, with a stated probability, no strip is left unworked. It makes three moves. (i) The "no missed area" event is reduced exactly to a scalar run score: the covering radius of the executed passes, field edges included. (ii) That score is calibrated with split-conformal or PAC quantiles on a reference plan with at least as many passes as the plan that will be deployed (CE, CE-q, CE+). (iii) For fields with no history, a five-layer extreme-value model of closed-loop tracking error predicts each field's required margin, and that prediction is used only as a normalising "pivot" in cross-field conformal calibration (CE-EVT-R). The experiments run in a closed-loop simulator driven by real field boundaries, DEMs and CORS GNSS error series. They include a pre-registered comparison on 90 fields, a three-stage pre-registered zero-data sequence (E-low v1-v3) and a pre-registered resampling check of validity.

The English is generally correct, precise and unusually honest about negative and post hoc results. The text is very dense, though. It is written for a reader who already knows conformal prediction, Gaussian extreme-value theory and the project's internal history (v7, v8, E-low v1/v2/v3, "CE+ v8", field index ranges). Notation is overloaded in several places that matter, a few acronyms clash, and Sections 6.1 and 6.4 read like a lab notebook rather than a journal results section. An agricultural engineer, who is COMPAG's core reader, will understand the problem statement and the practical guidance (Section 7.4). That reader will struggle with Sections 4-6, and the abstract will not tell them what CE+, CE-EVT-R or "26 cells" mean.

## 2. Recommendation and scores

**Recommendation: Major revision (on presentation grounds).** I see no language barrier to publication. The barrier is the cognitive load placed on a non-specialist reader. Every issue below can be fixed without new experiments.

| Criterion | Score (1-10) | Comment |
|---|---|---|
| Clarity (sentence- and paragraph-level) | 6 | Sentences are grammatical and precise but often overloaded, with 3-5 clauses joined by semicolons. Notation collisions harm clarity in Sections 4-5. |
| Structure (organisation of sections and arguments) | 6 | The macro-structure (problem, method, theory, experiments, discussion) is sound. Section 5 is too long for the main text, Section 6.4 is a chronology, and the role of each method variant is hard to track. |
| Readability for an agricultural engineer | 4 | The problem and the guidance are accessible. Everything between is written for a statistician or control theorist. There is no worked numerical example in agronomic units. |
| Figure/table quality | 7 | Figures are clean, consistently coloured and well captioned. Tables 5-9 are overpacked (several numbers per cell separated by slashes). The graphical abstract has a mislabelled quantity and mixes guarantee classes without saying so. |

## 3. Strengths

1. **Clear practical motivation.** The first two paragraphs of the Introduction state the agronomic problem and quantify it with simulation evidence (vendor rule meets the target on 0% of fields). That is exactly what COMPAG readers need.
2. **Honest reporting.** Every result is labelled as pre-registered, exploratory, developmental or post hoc. Failed claims (E-low v1, C3, C4) are reported in the main text, and qualifications are stated next to each headline number ("Two qualifications apply", Section 6.3). This is a model for the field.
3. **Fig. 1 is an excellent schematic.** It shows both failure modes (interior gap and field-edge miss) in physical units. Its caption ties it to Lemma 1.
4. **Captions are self-contained.** Most figure captions state what is plotted, sample sizes and the data source, and give a one-sentence take-home message.
5. **Section 7.2 and the limitations list (7.3) are explicit and well organised.** The practical guidance (7.4) is concrete and actionable.
6. **Consistent British spelling** (fertilising, optimisation, modelled, centreline, normalisation, colours) throughout the body text.
7. **Highlights respect the 85-character limit** (75-80 characters each) and the abstract is just under 250 words (246).

## 4. Major issues

### M1. Overloaded and colliding notation (Sections 3-5): the single biggest clarity problem

The same symbol carries different meanings, sometimes within one paragraph:

| Symbol | Meaning 1 | Meaning 2 (and 3) | Where |
|---|---|---|---|
| $\lambda_0$ | reference erosion (Sec. 4, Alg. 1-3, Thm. 5) | zeroth spectral moment ("variance $\tfrac12\lambda_0$") | Prop. 4, line 181 |
| $\lambda_2$ | - | second spectral moment | Prop. 4 |
| $\sigma$ | normaliser $\sigma(z)=\max(a+bz,0.3\bar\sigma)$ | standard deviation of $Z_j$, $\sigma(x)$ | Sec. 4.2 vs Thm. 3 |
| $T$ | normalised score $T=S/\sigma(z)$ | pair supremum $T_j$ | Sec. 4.2, Sec. 5.2, Thm. 4 |
| $T$ | (above) | set of training fields ("training fields T") | Algorithm 2 |
| $\Psi$ | generative map $e_k=\Psi(C,\phi_k,\tau_k,\xi_k)$ | $\Psi(a)=\varphi(a)+a\Phi(a)$ | Sec. 5.2 vs Thm. 3 |
| $M$ | missed area $M(\lambda,e)$ | $M=\sum_j\mu_j$ | Sec. 3 vs Thm. 4 |
| $J$ | cost $J(\pi)$ | pair index set $J(\pi)$; number of constraints $J$ | Sec. 3, Sec. 5.2, Lemma 3 |
| $a$ | slope intercept in $\sigma(z)=a+bz$ | number of extra pairs $a=\lvert J(\pi_0)\setminus J(\pi_1)\rvert$; $a_N$ | Sec. 4.2, Prop. 2, Thm. 6 |
| $K,k$ | number of passes $K(\lambda)$; pass index $k$ | order-statistic index $k$ | throughout |
| $C$ | operating condition | set of executed centres $C(x)$ | Lemma 1 vs Sec. 5.2 |
| $B$ | input matrix | Beta variable $B$ | L1 vs Prop. 8 |
| $w$ | implement width | innovations $w_t$ | Sec. 3 vs L1 |
| $P$ | field polygon | stationary covariance $P$ | Sec. 3 vs Prop. 4 |
| $e$ | execution error | Euler's number in $e^{hH}$, $e^{-M}$ | Thm. 2, L3 |

Several symbols are also used without definition at the point of use. $q$ in Section 4.1 ("$\lambda_\mathrm{ref}\leftarrow1.10\,q$ until $q\le\lambda_\mathrm{ref}$") is never defined. $\bar\sigma$ in Section 4.2 is not defined. $d(\ell,C)$ in Lemma 1 (distance from a point to a set) is undefined. $\ell(x),u(x)$ appear before they are explained. $m,s,s'$ in Theorem 6 are not defined. $\theta$ in Proposition 2 is undefined until the reader recalls $\theta_t$ from Theorem 2.

**Fix.** (a) Rename the spectral moments to $\nu_0,\nu_2$; the normaliser to $\rho(z)$ or $g(z)$; the normalised score to $\tilde S$; the training set to $\mathcal F_\mathrm{tr}$; the generative map to $G$ (or keep $\Psi$ there and rename the Kac-Rice function to $\psi$); the expected exceedance sum to $\bar\mu$; the pair set to $\mathcal J(\pi)$; the executed centre set to $\mathcal C(x)$. (b) Add a notation table (Table A0, one column per symbol) either at the end of Section 3 or as the first item of the Supplementary Material, and cite it in Section 3. (c) In Section 4.1 write: "where $q$ is the $(1-\varepsilon)$ empirical quantile of pilot scores at $\pi(\lambda_\mathrm{ref})$".

### M2. Acronym clash: "CPP" means two different things

Line 27 introduces "Coverage path planning (CPP)". Line 144 ("the pass-pair score of CPP-style methods"), Table 5, Fig. 3 and the graphical abstract use "CPP" for **conformal predictive programming** (Zhao et al., 2024), which is the main comparator. A reader from agricultural robotics will read "CPP" as coverage path planning and be confused at the paper's central comparison.

**Fix.** Keep CPP = coverage path planning (the standard in this journal) and rename the comparator throughout as "CPPr (Zhao et al.)" or, better, "Conformal predictive programming (CPrP; Zhao et al., 2024)". Update Table 5, Fig. 3 legend, the graphical abstract and the abstract ("two conformal planners").

### M3. Internal project labels used as if they were reader-facing names (Sections 6.1-6.6, Tables 5-8)

"v7", "v8", "CE+ v8", "E-low v1/v2/v3", "C1-C5", "V", "E", "R1-R3", "regime", "cell", "the v3 calibration pool", and the field-index paragraph ("indices 0-4 are training fields; 5-19 are the E-low v3 test fields ...; 20-49 ...; 50-79 ...; 80 onward ...") are the authors' bookkeeping. A reader meets "v8" for the first time in the abstract-level claims of Section 6.3 with no explanation of why it is version 8 or what v1-v6 were.

**Fix.**
- Drop version numbers from method names in the main text. Use "CE+" (not "CE+ v8") and explain once in Section 6.1: "The confirmatory comparison (called v8 in the repository) ...".
- Rename the experiments descriptively: **Experiment A** (with target-field data, confirmatory), **Experiment B1-B3** (zero target-field data), **Experiment C** (resampling validity check). Keep the repository names in a footnote or the Supplementary.
- Replace the field-index paragraph with a small table or diagram (Field split: Training 0-4 | Zero-data test set 1 ... ) and move the details of why each split is clean to the Supplementary.
- Define "cell" at first use (Section 6.5): "a cell is one combination of scenario, guarantee class and pivot". The abstract and Highlight 4 ("26 of 26 checks") also rely on it.

### M4. Too many method variants without a map

The reader must track CE, CE-q, CE+, CE+ PAC, CE+ v8, CE-EVT (PIT pivot), CE-EVT-R, CE-EVT-R-G, plus the pivot comparators "raw pooling", "scale law", "spec × scale law", "CQR". Some appear only once (CE-EVT-R-G, line 341).

**Fix.** Add a one-table summary at the start of Section 4 (Table 0, "Method variants"). Columns: Name | Calibration data needed | Normalisation/pivot | Transfer assumption needed | Guarantee rule | Where evaluated. Example rows:

| Variant | Data needed | Score normalisation | Deployed plan | Used in |
|---|---|---|---|---|
| CE | ≥9 (marginal) / ≥22 (PAC) runs on target field | none | reference plan itself (no transfer assumption) | Supplementary |
| CE-q | same | none | $\pi(\hat\lambda)$ (Thm. 5) | Sec. 6.3 (v7) |
| CE+ | same, plus 5 training fields | probe-line XTE, gated | $\pi(\hat\lambda)$ | Sec. 6.3 |
| CE-EVT-R | 1 run on each of ≥9/22 other fields, 0 on target | theory ratio pivot | $\pi(\hat q_g v^\star)$ | Secs. 6.4-6.6 |

Then refer to the table whenever a new variant appears.

### M5. Section 5 (Theory) is too long and too technical for the main text of COMPAG

Section 5 contains 6 theorems, 4 lemmas, 8 propositions (Proposition 6 is cited but **never stated** in the main text, which breaks the numbering) and 1 corollary in roughly 100 lines of dense mathematics. An agricultural engineer cannot tell which results are needed to *use* the method and which explain *why* it works.

**Fix.**
- Keep in the main text: Lemma 1, Theorem 1/Corollary 1 (exact score is smallest), Proposition 1 (nominal-plan calibration fails), Theorem 5 (transfer), Proposition 5 (CE-EVT-R validity), Proposition 8 (information limit). Each should get one plain-English sentence of interpretation.
- Move to an appendix: the formal statement of Theorems 2, 3, 4 and 6, Lemmas 2-4, and Propositions 2, 3 and 7. The main text should give a half-page verbal description of the five-layer chain, ideally as a **figure** (block diagram L1→L5 with inputs: controller gains, DEM slope, GNSS error statistics, soil moisture; output: predicted 0.9-quantile per field). The graphical abstract already has the beginning of this figure.
- Either state Proposition 6 in the main text or renumber so that the main text never cites an invisible proposition ("Proposition 6, Supplementary B" → "Proposition S1").
- Open each subsection of Section 5 with a one-sentence "What this means in practice" statement, e.g. for 5.2: "In practice: if you calibrate on a plan with fewer passes than you deploy, the guarantee can fail; calibrate on a plan with at least as many passes."

### M6. Overlong, multi-claim paragraphs in Section 6

- **Section 6.4, "E-low v3 met its claims in part"** (line 349) is about 370 words in one paragraph and carries more than 20 numbers, four Holm p-values, a non-inferiority margin, an argument about selection noise and a parenthetical caveat. Split it into three paragraphs: (i) what v3 tested; (ii) mixed-fleet result (C3); (iii) within-configuration result (C4/C5) and why it failed. Move the "extended margin curves" sentence to the table footnote.
- **Section 6.1, "Protocol with target-field data"** (line 272) packs definitions of system, calibration, metrics (pooled P(no miss), meet rate, overlap, regret), oracle and about 25 baselines into one paragraph. Use a short bulleted list of metrics with one-line definitions each.
- **Section 6.4, "E-low v2 met both claims, but mostly through realised coverage"** (line 347) mixes registered outcomes, post hoc matched-coverage analysis and a Beta-distribution aside. Put the post hoc material in its own paragraph headed "Post hoc: matched coverage".
- **Section 6.1, "Field splits"** (line 270): see M3.

### M7. Abstract and highlights are written for specialists

The abstract (246 words, close to the limit) contains three method acronyms (CE+, CE-EVT-R, plus implicit CE), five named mathematical tools ("Lyapunov covariance, Kac–Rice exceedance, a Bonferroni-bounded product form, a mixture over operating conditions and a Gumbel scale law"), "PAC"-type language, "two-level resampling check", "26 cells" and "pp". None is explained. It never states the practical headline in agricultural terms: how much overlap is saved and in what units. "Coverage plan" vs "zero-miss event" vs "certificates" also needs one clarifying clause.

**Suggested rewrite (about 230 words):**

> Coverage path planners assume that machines follow the planned passes exactly. In practice, cross-track errors between adjacent passes leave unworked strips, and the fixed overlap used to prevent them carries no stated reliability. We show that "no strip is missed" is equivalent to a single number per run, the largest gap between executed passes or between the outermost pass and the field edge, and that this is the tightest score that can certify complete coverage. Conformal erosion (CE+) calibrates the overlap margin on logged runs and guarantees, without distributional assumptions, that the probability of a missed strip stays below a chosen level such as 10%. For fields without operation history, an extreme-value model of the steering loop predicts each field's required margin from controller settings, terrain and GNSS accuracy; used only to put fields on a common scale for cross-field calibration (CE-EVT-R), it certifies new fields while the guarantee remains independent of the model's accuracy. In simulations driven by real field boundaries, elevation models and GNSS error series, a pre-registered comparison on 90 unseen fields met every validity and efficiency claim: CE+ needed 4-55% less overlap than two conformal planners at the same guarantee. A pre-registered resampling check confirmed the guarantee in all 26 tested combinations. For a fleet mixing three machine configurations, the model reduced overlap above the per-field optimum from 29.8 to 3.0 percentage points relative to pooled calibration. Under DGPS, the model shows that misses concentrate at field edges.

**Highlights.** Highlight 1 ("the tightest valid one") and Highlight 4 ("26 of 26 checks") are opaque out of context. Suggested set (each ≤85 characters):
- Missed-strip risk reduces exactly to one number per run: the largest coverage gap
- Conformal calibration certifies overlap margins with a chosen miss probability
- On 90 unseen fields: 4-55% less overlap than conformal planners, same guarantee
- A steering-error model sets margins for fields with no history of operations
- Under DGPS, missed strips concentrate at field edges, not between passes

### M8. Inconsistent terminology for the central quantities

The paper's key quantities each have several names:
- **The decision variable $\lambda$:** "erosion", "margin", "footprint margin", "certified margin", "overlap" (graphical abstract: "certified overlap λ"). On plan, the overlap is $2\lambda$, not $\lambda$ (Fig. 1 caption). Choose **"margin $\lambda$"** (with "erosion" defined once as a synonym) and always write "overlap $2\lambda$" or "overlap ratio $J$".
- **$\lambda^\star_f$:** "per-field required margin", "per-field optimum", "true optimum" (Fig. 6 axis), "oracle" (Section 6.1). Choose one ("required margin $\lambda^\star_f$") and use "oracle" only for the oracle plan.
- **Excess overlap vs regret:** both mean "overlap minus oracle overlap (pp)". Section 6.3 says "regret", Section 6.4 onward says "excess overlap", and the figures say "overlap above oracle" or "overlap above optimum". Use one term.
- **Pooling comparators:** "raw pooling", "pooled raw", "pooled conformal (raw)" (Fig. 5), "raw" (Fig. 4), "pooled" (graphical abstract), "classical pooled conformal". Use "raw pooling" everywhere.
- **Theory pivot:** "theory", "theory pivot", "CE-EVT-R", "CE-EVT-R (theory)", "the five-layer theory", "EVT_predict_cdf", "the theory predictor". Fix "theory pivot (CE-EVT-R)" at first use and then use "CE-EVT-R" for the method and "theory" for the predictor.
- **Coverage:** "P(no miss)", "coverage", "zero-miss probability", "realised coverage", "meet rate". Define once that coverage = P(no miss) and use "coverage" thereafter.
- **Machine configuration vs regime vs scenario:** Table 2 says each regime is one configuration, and Table 7 uses "Scenario". Use "regime" for R1-R3 and "mixed fleet" for the pooled case. Drop "scenario".
- **Field edge vs boundary vs headland:** Section 6.2 says "headland and boundary passes ... set the certified margin". But the main area excludes the headland (Section 3), so the field-edge term refers to the main-area boundary, not the headland. Clarify.

### M9. Lack of an agronomic anchor for numbers

A reader who manages sprayers will want to know what "+2.96 pp excess overlap" or "λ = 37 cm" means in practice. The paper never translates.

**Fix.** Add one worked example (a box in Section 6.3 or 7.4). For example: "For a 3 m implement under RTK (R1), the vendor rule plans 5 cm of overlap; CE+ certifies a margin of X cm (overlap 2X cm, Y% of the area), i.e. Z L/ha of spray mix saved relative to the hand-tuned overlap at the same 90% no-miss probability." Also state somewhere in Section 3 what main-area overlap of 8.4% (R1) means: 8.4% of the area receives a double dose.

### M10. Figure and table readability

**Tables.**
- **Table 5:** Seven columns, two of which combine three numbers and a parenthetical P. Split it into two tables, or move regret to a separate table, and give P(no miss) its own columns. Column header "Overlap %: CE+ v8" is awkward. Use a two-level header: Main-area overlap (%) | Pooled P(no miss) | Reduction (%) | Regret (pp), each with sub-columns CE+ / CPrP / Lindemann.
- **Table 6:** Too much prose in cells, e.g. "Post hoc: at matched coverage +0.06 vs +0.41 pp and +0.46 vs +0.66 pp; all pivots within ≤ 0.42 pp per cell". Reduce each cell to the claim and a Met / Partly / Not met verdict, and move numbers to the text or the Supplementary.
- **Table 7:** Each cell holds three numbers separated by slashes ("0.9193 / 0.700 / +1.16"). Readers cannot scan this. Use three sub-tables, or three columns per pivot, or drop excess overlap (it is "descriptive" and already in Table 8 / Fig. 5). Four decimal places in mean coverage are unnecessary given SE 0.0005-0.0008. Use three.
- **Table 3:** The column header "Final (product form, time-varying L1, integrator model, hybrid exact L2)" is internal jargon. Percentage errors appear in some cells only (R3 first version has one, R1/R2 do not). Use "Predicted / simulated" columns plus a separate "Error (%)" column.
- **Table 8:** The first header ("v3 mean excess pp, marginal / PAC (registered)") is hard to parse. Use a two-level header. Note in the caption why the CQR row has no resampling value.
- **Table 9:** Empty first-column cells make the blocks hard to follow in some renderers. Repeat the setting or use horizontal rules. "log-error sd" should be "SD of log(predicted/λ*)".

**Figures.**
- **Fig. 1:** Very good. Minor: the "darker band" label box covers part of the footprint. Add "main-area boundary" to the thick black line at y=0, and note that the area below is headland/outside the main area (currently labelled "outside the field", which conflicts with Section 3, where the headland lies inside the field but outside $W$).
- **Fig. 2:** Clear. The legend says "R1 (45 fields)", which matches the caption. Add "(log-log)" and "1:1 line" to the legend, and make the open-circle colour distinct from the filled green or label it "R3, with field-edge terms (15 fields)".
- **Fig. 3:** The in-figure title duplicates the caption. Remove it. The P(no miss) labels are rotated 90° and small, so place them horizontally or below the axis. Use the same y-axis range in both panels, or state clearly that they differ (12 vs 40 pp), because readers compare bar heights across panels. "95% intervals" should be "95% confidence intervals of the mean over 30 fields (field bootstrap)" or whatever was used.
- **Fig. 4:** The y-axis does not start at zero and spans only 0.90-0.93, which visually exaggerates differences that the caption says are negligible. That is acceptable but should be stated. The marginal-panel dashed line is at 0.900 while the registered criterion is 0.895. Draw the criterion line (0.895) and, if desired, a dotted line at 0.9, otherwise the caption and figure disagree. Legend labels ("raw", "spec x scale law") differ from Table 7 ("Raw pooling", "Spec × scale law"); use the multiplication sign × consistently. The horizontal positions of points within each group are uneven because the spec × scale law slot is empty in R1-R3. Centre the groups.
- **Fig. 5:** The bar order (theory, spec, raw, scale law) differs from Table 8 (raw, scale law, spec, CQR, theory). Use the same order. CQR, described as "the strongest comparator", is missing from the figure. Say why in the caption (no resampling run). The label "pooled conformal (raw)" differs from the rest of the paper.
- **Fig. 6:** The y-axis label "true optimum" should be "required margin $\lambda^\star_f$". The legend "100s of runs" should be "hundreds of runs". Panels have different y ranges on log axes. Fine, but mark this in the caption. The horizontal theory line has no uncertainty band.
- **Fig. 7:** Observed values carry no uncertainty indication. Add a sentence to the caption saying that each observation is a single calibration draw. The y-label "PAC margin / per-field optimum (ideal scale)" should use the paper's term ("deployed PAC margin / $\lambda^\star_g$").
- **Graphical abstract:**
  (a) The left bar panel shows the **PAC** class (2.5 / 5.9 / 17.4 pp, averages over regimes that appear nowhere in the text). The right panel shows the **marginal** class (3.0 / 12.8 / 29.8) without saying so. State the class in both panels, preferably the same class, and use numbers that appear in the paper.
  (b) Box 4 says "certified overlap λ", but λ is the margin and the overlap is 2λ.
  (c) The flow chart implies every method passes through the five-layer theory. Only CE-EVT-R does. Show a branch: "target-field runs → CE+" vs "other fields' runs + theory → CE-EVT-R".
  (d) The arrow between boxes 3 and 4 is clipped and almost invisible.
  (e) "Lyapunov → Kac–Rice → product → mixture → Gumbel" means nothing to the target audience. Use "steering model → per-pass error → field-level margin".

### M11. Manuscript-preparation artefacts

- Section 6.7 is a **TODO** block, and the Data availability statement contains "TODO: archive with a DOI". Both must be resolved or rephrased ("Field validation is ongoing; see Limitations") before submission.
- The HTML comments (`<!-- source: ... -->`) and repository paths in captions ("Data: results/v8/system_v8.csv") suit an internal draft. COMPAG captions should not contain file paths. Move them to the data-availability statement or a supplementary index.
- The Everett (n.d.) reference says "built from the repository in October 2026; the exact commit was not recorded". Record the commit, or remove the clause. As written it reads as an admission of irreproducibility.

## 5. Minor issues

### 5.1 Sentence-level rewrites (location → original → suggested)

1. **Abstract, l.7:** "We reduce the zero-miss event of a coverage plan exactly to a scalar run score, the covering radius of the executed passes, and show that this score is the smallest one that yields valid certificates."
   → "We show that a run leaves no strip unworked if and only if a single scalar score, the covering radius of the executed passes, stays below the planned margin, and that no valid score is smaller."
2. **Abstract, l.7:** "a coupling inequality bounds the effect of re-planning."
   → "a coupling inequality bounds how much changing the plan can change the miss probability."
3. **Abstract, l.7:** "The theory also predicts where no method can help (an information limit) and shows that field-edge misses must be modelled under DGPS."
   → "The theory also predicts a limit below which no field-level calibration can reduce the margin, and shows that under DGPS most misses occur at field edges."
4. **Sec. 1, l.23:** "Overlap set to absorb this deviation applies inputs twice on the overlapped strip."
   → "Any overlap added to absorb this deviation doubles the application rate on the overlapped strip."
5. **Sec. 1, l.23:** "The trend towards autonomous tractors (Global Market Insights, 2026) removes the operator who used to correct visible gaps by eye."
   → "As tractors become autonomous (Global Market Insights, 2026), no operator is present to spot and correct visible gaps." Also consider citing a peer-reviewed source rather than a market report.
6. **Sec. 1, l.27:** "Three features of these methods are problematic for field coverage. (i) They calibrate on the nominal plan and then deploy a different, more conservative plan; ..."
   → Use an inline list with a lead-in colon, or a bulleted list: "These methods have three shortcomings for field coverage: (i) ...; (ii) ...; and (iii) ...". Also explain in (iii) where 9 and 22 come from: "(the smallest $n$ for which $\lceil (n+1)(1-\varepsilon)\rceil\le n$)".
7. **Sec. 1, l.35:** "show that the theory is decisive across machine configurations and as a zero-data predictor, but that within one configuration all field-level pivots are equivalent to within tenths of a percentage point"
   → "show that the theory pays off when fields are worked by different machine configurations and when no run data exist, but that within a single configuration all field-level pivots perform within a few tenths of a percentage point of each other".
8. **Sec. 1, l.37:** "The evaluation is transparent about status:"
   → "Throughout the evaluation, we label each result as pre-registered, exploratory or post hoc, and we report failed claims alongside met ones."
9. **Sec. 3, l.55:** "the evaluated **main area** $W\subset P$ is $P$ inset by twice the implement width $w$ (the remainder is headland)."
   → "the **main area** $W\subset P$, on which coverage is evaluated, is $P$ shrunk inward by $2w$; the strip between $W$ and the field boundary is the headland."
10. **Sec. 3, l.55:** "by a standard exchange argument for interval covering the greedy rule uses the fewest passes among placements that satisfy the gap condition."
    → "the greedy rule uses the fewest passes of any placement that satisfies the spacing condition (a standard exchange argument for interval covering)."
11. **Sec. 3, l.75:** "The score is the growth of the footprint half-width that would close the worst gap."
    → "Intuitively, $S-\lambda_\mathrm{ref}$ is how much wider each footprint would need to be, on each side, to close the worst gap."
12. **Sec. 4, l.81:** "if $k>n$ the quantile is $+\infty$ and nothing is deployed."
    → "if $k>n$, the quantile is $+\infty$: there are too few runs to certify any margin, and the method declines to deploy."
13. **Sec. 4.1, l.85:** "**CE** (assumption-free) runs a pilot fixed point $\lambda_\mathrm{ref}\leftarrow1.10\,q$ until $q\le\lambda_\mathrm{ref}$, ..."
    → "**CE** (assumption-free) first iterates $\lambda_\mathrm{ref}\leftarrow1.10\,q$, where $q$ is the conformal quantile of pilot-run scores at $\pi(\lambda_\mathrm{ref})$, until $q\le\lambda_\mathrm{ref}$. It then ..." Split this 70-word sentence into three.
14. **Sec. 4.2, l.99:** "the autosteer's cross-track-error (XTE) RMS $z$ is a noisy reading of the day's roughness and slip."
    → "the root-mean-square cross-track error (XTE) $z$ reported by the autosteer on this line serves as a noisy indicator of the day's soil roughness and slip."
15. **Sec. 4.3, l.116:** "A farm or contractor more typically holds **many fields with one or two historical operations each**, and the new field has none."
    → "More typically, a farm or contractor has logs of one or two operations on each of many fields, and none on the new field."
16. **Sec. 4.3, l.130:** "A first version used the probability-integral-transform (PIT) pivot ..."
    → "An earlier version (E-low v1, Section 6.4) used ..." The reader otherwise does not know that "first version" refers to a failed experiment.
17. **Sec. 5.1, l.144:** "i.e. it never declares a missing run miss-free."
    → "i.e. it never certifies a run that actually misses area." ("missing run" is ambiguous: it suggests a run that is absent.)
18. **Sec. 5.1, l.156:** "The contribution of CE is therefore not the quantile rule but the score and the reference plan, and comparisons must be made **within a guarantee class** (marginal vs marginal, PAC vs PAC)."
    → "CE's contribution is therefore the score and the reference plan, not the quantile rule. For the same reason, we compare methods only within a guarantee class (marginal with marginal, PAC with PAC)."
19. **Sec. 5.2, l.166:** "Under the Gaussian structure of Section 5.3 it is replaced by the exact inequality of Theorem 5."
    → "Section 5.3 sharpens it to an exact inequality (Theorem 5) under a Gaussian model." (This is a forward reference to a theorem not yet introduced. Signal it.)
20. **Sec. 5.3, l.183:** "Three refinements were introduced because earlier validation checks failed:"
    → "Three refinements, each prompted by a failed validation check, are needed:"
21. **Sec. 5.3, l.205:** "exceedances cluster because operating conditions differ between runs, not because of local pair dependence."
    → "exceedances cluster mainly because operating conditions vary from run to run, not because neighbouring pairs are dependent."
22. **Sec. 5.3, l.221:** "a tenfold larger field raises it by about 15% at $N\sim10^3$"
    → "at $N\approx10^3$, a field ten times larger needs only about 15% more margin".
23. **Sec. 5.4, l.229:** "so one realised coverage can fall well below $1-\varepsilon$ without contradicting the guarantee."
    → "so the coverage achieved with any single set of historical runs can fall well below $1-\varepsilon$ without contradicting the guarantee, which holds on average."
24. **Sec. 6.1, l.247:** "DBSCAN extracts 964 fields, of which 137 paddy fields (hilly south of China) and 162 wheat fields (North China Plain) are used."
    → "Density-based clustering (DBSCAN) of the trajectories yields 964 fields; we use 137 paddy fields in the hilly south of China and 162 wheat fields on the North China Plain." State the selection criterion.
25. **Sec. 6.1, l.274:** "Stack BCD + LQR-I."
    → "All E-low experiments use boustrophedon decomposition (BCD) with the LQR-I controller." (This is currently a sentence fragment.)
26. **Sec. 6.2, l.304:** "The practical consequence is that headland and boundary passes, not the field interior, set the certified margin under sub-metre GNSS."
    → "In practice, under DGPS-grade (decimetre) positioning, the outermost passes, not the interior, determine the certified margin." ("Sub-metre GNSS" includes RTK, for which the paper says the opposite.)
27. **Sec. 6.3, l.328:** "Measured as regret, CE+ is 27–92% below the comparators in the ten comparisons where its regret is positive, and below the oracle in R1 marginal"
    → "In regret, CE+ is 27-92% lower than the comparators in the ten comparisons where its regret is positive. In R1 marginal its overlap is even below the oracle's, because its realised coverage (0.903) is marginally above target while the oracle's is exactly at target." (Explain how a method can beat an oracle; readers will otherwise suspect an error.)
28. **Sec. 6.4, l.345:** "which was ranked highest and pushed the PIT quantile to the extreme tail"
    → "which was treated as the largest pivot value and pushed the PIT quantile into the extreme tail".
29. **Sec. 6.5, l.373:** "The marginal rule is correct on average over calibration data; a per-calibration statement requires the PAC rule."
    → "The marginal rule is valid on average over calibration sets; to guarantee coverage for the particular calibration set in hand, use the PAC rule."
30. **Sec. 7.4, l.459:** "With at least 22 recorded operations on a field (at least 9 for a marginal guarantee), use CE+ ..."
    → "If a field has at least 22 logged operations (9 for a marginal guarantee at $\varepsilon=0.1$), use CE+ ..." (Add $\varepsilon$: the numbers are level-specific.)
31. **Sec. 8, l.468:** "whereas across configurations, and as a predictor that needs no run data, the theory pivot is decisively better than configuration-blind scales"
    → "Across machine configurations, by contrast, the theory pivot clearly outperforms configuration-blind scales, and as a zero-data predictor it is more accurate than regressors trained on one run per field."

### 5.2 Grammar, style and punctuation

- **"Notice that ..." in six figure captions.** This imperative is unusual in journal captions. Use declarative statements: "RTK regimes lie on the diagonal; ..." or "The key observation is ...".
- **"iff"** (Lemma 1, Section 5.2, Theorem 3b) is informal for COMPAG. Write "if and only if" in the main text.
- **Semicolon chains.** Many sentences link four or more clauses with semicolons (e.g. l.45, l.47, l.49, l.259, l.272). Lines 47 and 49 in Related Work are lists without verbs ("Kac–Rice formulas and Rice's method (...); maxima of stationary sequences ...; ..."). Turn them into full sentences stating what each line of work contributes.
- **Sentence fragments:** "Stack BCD + LQR-I." (l.274); "Criteria: marginal, mean coverage ..." (l.353). Rewrite as full sentences.
- **Hyphenation:** "cross-track-error (XTE) RMS" → "cross-track error (XTE) RMS"; "3D-terrain-equivalent spacing" → "3D terrain-equivalent spacing"; "one-run-trained CQR scale" → "CQR scale trained on one run per field".
- **Ranges:** The abstract uses "4.0–54.7%" while Highlight 2 uses "4-55%" (hyphen instead of en dash). Use en dashes and consistent precision.
- **Quotation marks:** "'never worse'" uses single straight quotes. COMPAG uses double quotes.
- **Bold mid-sentence** (e.g. "**All pre-registered results ... were computed with the theory without the field-edge terms**", "**no field-level prediction can remove**", "**every**") is overused. Reserve bold for defined terms at first use.
- **Numbers:** Mixing "0.733" and "0.27" in one sentence (l.330) looks careless. Use the same precision ("0.73, 0.27 and 0.70").
- **"pp"** is used in the highlights and abstract before it is defined (Section 6.1). Write "percentage points" in the abstract and highlights.
- **"P(no miss)"** and "$\Pr[\cdot]$" and "$P(\cdot)$" are used for the same operator. Choose one ($\Pr$).

### 5.3 Acronyms and definitions

Define at first use in the main text (after the abstract), and consider an abbreviation list:

| Acronym | Status | Action |
|---|---|---|
| GNSS, RTK, DGPS | used from the Introduction, never expanded | expand: global navigation satellite system; real-time kinematic; differential GPS |
| PAC | "training-conditional" given, but "probably approximately correct" never expanded | expand at l.27 |
| CPP | clash (see M2) | rename the comparator |
| MPC, LQR, GP, DRO, CVaR | used in Sec. 1-2 without expansion | expand: model predictive control; linear-quadratic regulator; Gaussian process; distributionally robust optimisation; conditional value-at-risk |
| CQR | introduced only as "conformalized quantile regression (Romano et al.)" in a list | define explicitly: "conformalised quantile regression (CQR)" |
| EVT | appears in "CE-EVT-R" and Algorithm 3, never expanded | "extreme-value theory (EVT)" in Sec. 1 |
| DEM | used in the abstract wording and Sec. 4.3; defined only in Sec. 4.3 | define at first use in Sec. 1 or 3 |
| BCD | defined in Sec. 2, used in Sec. 3 as "boustrophedon decomposition" | fine; keep consistent |
| CORS, PPK, INS | used in Sec. 6.1 and 6.7 | expand: Continuously Operating Reference Stations; post-processed kinematic; inertial navigation system |
| DBSCAN | not expanded | "density-based spatial clustering of applications with noise" |
| LOO | Algorithm 2 only | "leave-one-field-out (LOO)" in the text |
| XTE, RMS | XTE defined, RMS not | expand RMS once |
| OU | "Ornstein–Uhlenbeck" written out | fine |
| PIT | defined | fine |
| i.i.d., NaN | not expanded | write "independent and identically distributed"; replace "all-NaN" with "undefined (not-a-number)" |
| CE, CE-q, CE+, CE-EVT-R, CE-EVT-R-G | see M4 | method table |

### 5.4 Cross-referencing and numbering

- Proposition 6 is cited (l.130, l.345) but not stated in the main text (see M5).
- Theorem 5 is cited in Section 5.2 before it is stated. This is acceptable with a forward-reference cue.
- "Supplementary Sx" and "Appendix A" are mixed. "Supplementary B" (l.130, l.183, l.304) and "Appendix A of the Supplementary Material" coexist. Use one scheme (Appendix A-D in the Supplementary Material, tables S1-S22).
- Contribution 5 (l.35) cites Section 6.4, and Section 6.6 refers to Table 9, which is introduced in Section 6.6 but already cited in Section 6.2 (l.289). Reorder the tables or cite forward explicitly.
- Fig. 1 is cited for the DGPS edge concentration in Section 6.2 (l.304), but Fig. 1 is illustrative, not data. Cite Table 4 instead.

## 6. Overall advice

The science is carefully argued and transparently reported, and the writing is grammatically sound. The problem is density and audience fit. To make the paper work for *Computers and Electronics in Agriculture*:

1. **Write for the agricultural engineer first.** Lead each section with what it means for a sprayer or seeder operator. Add one worked numerical example in physical and agronomic units (cm of margin, % of area double-dosed, L/ha). Rewrite the abstract and highlights as in M7.
2. **Clean up notation and naming.** Resolve every symbol collision in M1, rename the CPP comparator (M2), drop internal version labels (M3), and add a method-variant table (M4) and a notation table. This alone will remove most of the friction for every reader, specialist or not.
3. **Shorten the main text.** Move most formal statements of Section 5 to an appendix, replace them with a block-diagram figure of the five-layer predictor, and split the long Section 6 paragraphs. Reduce Tables 5-8 to one quantity per cell.
4. **Fix the graphical abstract** (class mismatch, "overlap λ", misleading flow) and harmonise figure labels with the text.
5. **Remove draft artefacts** (TODO blocks, file paths in captions, HTML comments) before submission.

Once these presentation changes are made, the paper should be clear to COMPAG's readership without losing its rigour.

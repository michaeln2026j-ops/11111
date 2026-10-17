# Associate Editor assessment (R12): Computers and Electronics in Agriculture

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations"
**Article type:** Research Paper
**Files assessed:** manuscript.md, supplementary.md, cover_letter.md, title_page.md, figures/paper/*.png (7 figures and the graphical abstract)

---

## 1 Summary

The authors ask how much pass-to-pass overlap a field operation needs so that the probability of leaving *any* unworked strip in the main area is at most epsilon (0.1 in the paper). The paper makes three contributions.

1. **An exact run score.** The score is the covering radius of the executed passes per 1 m section, including the field-edge terms. Its threshold event is exactly the zero-miss event (Lemma 1), and no valid score is smaller (Theorem 1, Corollary 1).
2. **Conformal calibration of the margin (CE, CE-q, CE+).** The score is calibrated on a "dominating" reference plan, which has at least as many passes as the deployed plan. A coupling inequality (Theorem 5) bounds the effect of re-planning. CE+ adds normalisation by the cross-track error (XTE) of a headland probe line, and a training-only gate decides whether that normalisation is used.
3. **CE-EVT-R for fields with no history.** A five-layer extreme-value theory predicts each field's required margin (Lyapunov covariance, then Kac–Rice exceedance, then a Bonferroni product, then a mixture over operating conditions, then a Gumbel scale law). This prediction is used only as a ratio pivot for cross-field conformal calibration with one historical run per field. Validity does not depend on the theory.

All evaluation is simulated. The simulated machine runs over real field boundaries (Chinese combine trajectories), Copernicus DEM terrain and NOAA CORS GNSS error series processed with RTKLIB at several receiver grades. There are three machine configurations (R1 RTK flat 3 m, R2 RTK hilly-wet 1.5 m, R3 DGPS hilly 6 m). The main results are as follows.

- **Comparison with conformal planners (v8, pre-registered).** On 90 fresh fields CE+ was valid and used 4.0–54.7% less main-area overlap than two conformal planners in the same guarantee class.
- **Coverage check (pre-registered).** A two-level resampling check confirms the coverage guarantee in 26 of 26 cells.
- **Mixed fleet.** The theory pivot reduces excess overlap from 29.8 to 3.0 pp compared with configuration-blind pooling.
- **Single configuration.** Within one machine configuration, all field-level pivots are equivalent to within tenths of a percentage point. This is an "information limit" (Proposition 8).

The authors are unusually candid. Of the three zero-data experiments, one failed, one succeeded mainly through differences in realised coverage, and one was only partly met. The real-vehicle section (6.7) is a TODO placeholder.

---

## 2 Desk decision and predicted outcome

**Desk decision: send to review, after a technical return.** I would not desk-reject. The problem is real and relevant to the journal: overlap and skip control in guidance and autosteer is core CEA territory. The statistical work is serious and, as far as an editor can judge, careful. The experimental design (pre-registration, fresh-field splits, reporting of failed claims) is better than most of what this journal receives.

However, the submission **is not reviewable in its present state**, and I would return it to the authors for technical correction before assigning reviewers. These items must be fixed before the paper goes out:

- the "TODO" Section 6.7 in the main text;
- the "TODO: archive with a DOI" in the Data availability statement;
- the empty generative-AI declaration;
- placeholder authors, affiliations and funding;
- an "Appendix E. Notes for the authors (remove before submission)" in the Supplementary Material, which includes internal numbering maps and a note on a commit message that reported 28 cells instead of 26;
- HTML comments and repository file paths throughout the manuscript and in the figure captions.

**Predicted final outcome:** major revision after first review. If no real-machine evidence is added, I expect at least one agricultural-engineering reviewer to recommend rejection. I estimate acceptance in this journal at roughly 40–50%, conditional on these changes:

- a shorter, more accessible main text;
- some validation against real machine data (see Major issue 3);
- the zero-miss criterion addressed from an agronomic point of view.

Without these changes, I would expect the paper to end up in a statistics or robotics venue instead.

**Scores (1–10)**

| Criterion | Score | Comment |
|---|---|---|
| Novelty | 7 | Agriculture has seen no previous certified-coverage formulation with an exact score and decision-dependent calibration. The conformal machinery itself is borrowed. |
| Soundness | 7 | The guarantees are sound and the guarantee is checked directly. The theory was partly developed after the fact. All results are from simulation, and the zero-miss criterion and the configuration-blind baseline are open to challenge. |
| Practical relevance | 5 | The question is relevant. The answer is not yet translated into machine settings, input savings or a workflow that a contractor could follow, and it has not been validated on a vehicle. |
| Clarity (for the CEA readership) | 4 | It is precise but very dense, full of theorems, and uses internal experiment names (v7, v8, E-low v1–v3). |
| Fit to CEA | 6 | The topic fits well. The register currently reads like a statistics or robotics paper. |

---

## 3 Strengths

1. **A relevant, well-posed problem.** Fixed overlap with no stated reliability is a real practice in spraying, fertilising and seeding. The move to autonomous machines, which removes the operator who corrected visible gaps, strengthens the motivation.
2. **Clean core result.** The reduction of zero-miss coverage to a scalar covering-radius score (Lemma 1), and the proof that it is the tightest valid score, are elegant and immediately useful. The practical message "record the covering radius, not per-pair errors" is concrete.
3. **Physically interpretable theory.** The field-edge terms (Theorem 3(b)) show that common-mode DGPS error cancels between adjacent passes but not at the boundary. Under sub-metre GNSS, the boundary passes therefore set the margin. A CEA reader can act on this.
4. **Exemplary transparency.** The paper separates pre-registered, exploratory, developmental and post hoc results (Table S20) and reports failed claims in the main text (E-low v1; C3 and C4 of E-low v3). It also gives a matched-coverage reanalysis that weakens its own registered E-low v2 gains. The editor values this, and it will help the paper with careful reviewers.
5. **Strong baselines.** About 25 published or industry systems were run in the exploratory study, and the confirmatory comparison uses two recent conformal planners in the same guarantee class with Holm correction.
6. **Realistic inputs.** The paper uses real field polygons, real DEMs and real multi-station GNSS error series, including RTK wrong fixes and float drift. Table 1 shows that a Gaussian error model with the same RMS badly underestimates the tail, which is useful in its own right.
7. **The guarantee is checked directly.** The 4000-replicate check over both sources of randomness (Table 7, Fig. 4) is the right experiment and is well executed.
8. **Honest scope statement.** Section 7.2, "When it cannot help", together with the information limit (Proposition 8), is a mature piece of self-criticism.

---

## 4 Major issues

### M1. The paper is not written for an agricultural-engineering readership

- **Location:** Abstract; Sections 3–5 (about 4,000 words, 6 theorems, 8 propositions and 4 lemmas in the main text); Sections 6.4–6.6; and the internal names throughout: v7, v8, E-low v1/v2/v3, CE / CE-q / CE+ / CE+ PAC / CE-EVT / CE-EVT-R / CE-EVT-R-G, "pivot", "marginal vs PAC class", "matched coverage".
- **Why it matters:** The typical CEA reader is an engineer working on agricultural machines or precision agriculture. That reader will understand pass-to-pass accuracy, RTK and autosteer, but not Kac–Rice upcrossings, Bonferroni sandwiches, extremal indices or Beta-distributed conditional coverage.
  - The abstract alone names Lyapunov, Kac–Rice, Bonferroni and Gumbel.
  - Section 5.3 reads like an applied-probability paper.
  - A reader who wants to know "what overlap should I set on my 3 m sprayer with RTK, and how many logged runs do I need?" has to get through roughly 25 pages to find out.
  - Internal version names (v7, v8, E-low v1–v3) record the project's history and mean nothing to a reader.
- **Concrete fix:**
  1. Keep only the results the method needs in the main text: Lemma 1, Theorem 1 (stated in words), Theorem 5 (one sentence), Proposition 5 and Proposition 8. Move Theorems 2–4 and 6, Lemmas 2–4 and Propositions 2–4, 6 and 7 to Appendix A.
  2. Replace Section 5.3 with a one-page, physically worded description of what the predictor takes as input (controller gains, DEM, GNSS grade), what it returns (the 0.9 quantile of the run score) and how accurate it is.
  3. Add a **nomenclature table** of symbols and acronyms.
  4. Rename the experiments descriptively. For example: "Experiment 1: fields with operation history", "Experiment 2: new fields, single machine configuration", "Experiment 3: new fields, mixed fleet", "Experiment 4: coverage check". The v-numbers can go in the Supplementary Material.
  5. Add a **worked numerical example** early on, for example in Section 1 or 4: one R1 field and a 3 m sprayer with RTK, showing the vendor rule (2 × 2.5 cm), the hand-tuned overlap, the CE+ margin in cm, the overlap in %, the number of passes, and the area double-dosed per 100 ha.
  6. Add a **workflow figure** for practitioners covering what to log, when to drive the probe line, and when to use the target-field method or the cross-field method.
  7. Rewrite the abstract without layer names, and state the agronomic outcome in units an agronomist recognises.

### M2. Length and structure

- **Location:** The whole paper. The body has about 11,500 words, 9 tables, 7 figures and 44 references. The Supplementary Material adds about 10,700 words and around 22 supplementary tables.
- **Why it matters:** This is well above a typical CEA research article of about 7,000–9,000 words. Much of the main text is project history:
  - three refinements of L1 introduced "because earlier validation checks failed";
  - two earlier versions of the edge terms;
  - the PIT-pivot failure;
  - re-reading v3 with extended curve grids;
  - the registered C5 gate predictions.

  The transparency is welcome, but the narrative of how the method was found hides the result.
- **Concrete fix:** Aim for about 8,000 words in the body.
  - Make the narrative "method, then evidence", not "sequence of experiments".
  - Condense Section 6.4, which covers the E-low sequence, into one table plus one paragraph that states honestly what was and was not confirmed. Move the narrative of v1 and v2 to the Supplementary Material.
  - Keep Table S20 (status of every result) and point to it from the main text.
  - Merge Sections 7.1 and 7.2 and shorten them.
  - Table 3 (theory version history) and Table 4 can go to the Supplementary Material, with Fig. 2 kept in the main text.
  - Section 6.3, "Exploratory comparison (v7)", can be reduced to two sentences.

### M3. No real-vehicle evidence: not fatal at desk, but likely fatal at review if nothing is added

- **Location:** Section 6.7 (TODO); Limitations item 1; Table 1 caption ("these RTK errors are a lower bound on machine errors"); Section 6.1 (the simulator).
- **Why it matters:** CEA publishes simulation studies, but in guidance and autosteer papers reviewers routinely expect field data. Here every number comes from a simulated vehicle with these settings:
  - assumed steering lag, saturation and slip model;
  - 2 m/s on every field;
  - a 2.6 m antenna with an assumed roll-compensation factor;
  - US Midwest static CORS errors overlaid on Chinese paddy and wheat field geometry.

  CE and CE+ are distribution-free, so their *validity* does not depend on the simulator. Their *efficiency claims* do, and so do all claims about the theory: the 1–4% accuracy of the predicted margin, the edge-concentration of DGPS misses, and the 0.047 log error across configurations. The theory is validated against the same simulator from whose model it is derived, which is circular for a practical reader. The relation between the XTE of the headland probe line and the pass-to-pass error, on which CE+ depends, is admitted to be unverified. A TODO section in a submitted manuscript is not acceptable in any form.
- **My judgement:** A purely simulation-based paper is **not automatically fatal** for CEA, because the guarantee is distribution-free and the inputs are real. But in its present form I expect at least one reviewer to recommend rejection on this ground. The minimum that would make the paper defensible is one of the following options, in decreasing order of value:
  1. **Real operation logs replayed offline.** Use auto-steer logs (XTE, GNSS position and fix status) from commercial machines on several fields, compute exact run scores from logged as-applied passes, and show that CE+ or CE-EVT-R margins computed on some fields cover the held-out fields. The PPK-ground-truth tractor campaign planned in Section 6.7 is ideal. Even 10–20 fields would materially change the paper.
  2. **Validation of the simulator's pass-to-pass statistics.** Compare against published standardised pass-to-pass tests of guidance systems (for example ISO 12188-2 straight-path tests) and against vendor or extension-service field trials. This would show that the simulated pass-to-pass error distributions, at least their 95% and 99% quantiles, match real autosteer tractors at comparable GNSS grade and speed.
  3. **At the very least**, a sensitivity study in which the simulated error model is perturbed beyond the fitted settings (vehicle multipath, a heavier RTK tail, a different controller bandwidth, speed 1–4 m/s). It should show how CE+ efficiency and the theory pivot degrade, so that readers can see how robust the efficiency conclusions are. The CitrusFarm robot logs (123 rows of an orchard robot) are not a substitute for tractor data and should not be presented as validation.

  If no real data can be added, Section 6.7 must be deleted. The title, abstract and highlights must then say "simulation study", and the claims about the edge concentration of DGPS misses must be framed as hypotheses for future testing.

### M4. The agronomic meaning of the zero-miss criterion

- **Location:** Section 3 (Objective); Section 6.3; Section 7.4, first bullet ("twice the nominal pass-to-pass accuracy left a gap on essentially every simulated run").
- **Why it matters:** The certified event is "no uncovered 1 m section anywhere in the main area". A sliver 1 cm wide and 1 m long counts as a failure in the same way as a 50 cm strip down a 500 m pass. This is why the vendor rule "never" meets the target and why the oracle overlaps are 8.7% (R1, about 13 cm per side on a 3 m implement with RTK) and 24.9% (R2). These overlaps are far larger than typical RTK practice, and practitioners will find the numbers implausible.
  - Many implements, such as spreaders with overlapping spread patterns and sprayers with boom-end taper, tolerate small gaps agronomically.
  - The economic and agronomic cost lies in the area missed or double-dosed, not in the event.

  The paper does not show the distribution of missed *area* or missed-strip *width* under the competing methods, so readers cannot judge whether the comparators' "misses" matter.
- **Concrete fix:**
  1. Report the distribution of missed area (m²/ha) and maximum gap width for CE+, the vendor rule and the hand-tuned overlap.
  2. Generalise the score to a tolerance, i.e. the miss event "gap wider than g_tol" or "missed area greater than A_tol". This should be trivial: shift the covering-radius threshold by g_tol/2, or apply conformal risk control to missed area. Then show results for an agronomically motivated tolerance, for example 5–10 cm or the implement's spread-pattern taper.
  3. Translate the overlap differences into input cost, for example kg N/ha or EUR/ha for a typical spray or fertiliser programme. Without this, "4.0–54.7% less overlap" has no practical scale. Relative reductions of 4% (R2) and regret differences of tenths of a pp are agronomically negligible and should be presented as such.

### M5. The mixed-fleet headline (29.8 to 3.0 pp) is measured against a weak baseline

- **Location:** Abstract; Highlight 5; Section 6.6; Table 8; Fig. 5; graphical abstract.
- **Why it matters:** Raw pooling across a 1.5 m RTK implement, a 3 m RTK implement and a 6 m DGPS implement charges every field the margin of the worst configuration. A sensible contractor would never do this; they would at least **stratify calibration by machine configuration**. The paper's own within-configuration results show that stratified raw pooling is as efficient as the theory pivot, to within tenths of a pp.
  - The fair comparators are therefore (a) per-configuration pooling, with its data cost (fewer calibration fields per configuration) made explicit, and (b) the configuration-aware learned scale (CQR).
  - Against CQR the theory's gain is modest and mixed: 1.87 vs 3.16 pp registered and 0.73 vs 1.41 pp at matched coverage in the marginal class, and comparable in the PAC class (2.64 vs 2.54 pp).
  - Against the spec × scale-law pivot the registered difference was not significant.

  The headline number therefore overstates the practical value of the theory.
- **Concrete fix:**
  1. Add a stratified (per-configuration) raw-pooling baseline. Show its efficiency as a function of the number of fields available per configuration; this is where the theory pivot can genuinely help.
  2. Use CQR or the stratified baseline, not configuration-blind pooling, as the headline comparator in the abstract, the highlights and the graphical abstract.
  3. State in the abstract that within a single configuration the theory brings no efficiency gain.

### M6. Compliance with Elsevier and CEA guidelines (blocking for review)

- **Generative-AI declaration (title_page.md):** placeholder. This is mandatory and must be completed, and it must appear in the manuscript before the references, as Elsevier requires.
- **Data availability:** The manuscript says "TODO: archive with a DOI before publication". The cover letter says code "will be made openly available upon publication", while the title page says the material is "available at [repository URL / DOI]". These statements contradict each other.
  - Provide a working, reviewer-accessible link, or a private review link, at submission.
  - Archive with a DOI (Zenodo or Mendeley Data).
  - Make the three statements consistent.
- **Section 6.7 TODO:** must be removed or completed (see M3).
- **Supplementary Material, Appendix E "Notes for the authors (remove before submission)":** must be removed. It exposes internal file names and the discrepancy between 26 and 28 cells.
- **HTML comments and repository paths:** The manuscript contains `<!-- source: ... -->` comments and "Data: results/..." paths in figure captions. Remove them from submission files; the repository README can carry the mapping from tables to files.
- **Title page:** Authors, affiliations, corresponding e-mail and funding are placeholders. The CRediT statement has to be completed with real names.
- **Abstract:** About 246 words, which is at the usual 250-word ceiling (check the current Guide for Authors). It is dense with jargon (M1). Shorten it to about 200 words in plain language.
- **Highlights:** Five bullets of at most 80 characters, which is compliant.
  - Highlight 1 ("the tightest valid one") and Highlight 4 ("26 of 26 checks") mean nothing to a reader who has not read the paper.
  - Highlight 5 repeats the configuration-blind headline of M5.
  - Rewrite them in practical terms, for example: "Certified overlap guarantees ≥90% probability of no unworked strip".
- **Graphical abstract:** It is supplied as a file and its size is fine (3134 × 1314 px). However:
  - (a) It is never mentioned or listed in the submission files.
  - (b) The two bar panels mix guarantee classes. The left panel is labelled PAC (mean regret 2.5/5.9/17.4 pp averaged over R1–R3). The right panel shows the *marginal* mixed-fleet resampling values (3.0/12.8/29.8 pp) without saying so.
  - (c) The right panel uses the weak configuration-blind baseline (M5).
  - (d) The left half is a text flowchart with no agricultural imagery. The arrow from box 3 to box 4 collides with the box border.
  - (e) "Lyapunov → Kac–Rice → product → mixture → Gumbel" is meaningless to the target reader.

  Redesign it around a field picture: passes, a gap, the certified margin and a single number for the saving.
- **Figures:**
  - The PNGs are 1000–2150 px wide. For double-column width (190 mm), Figs. 3, 4 and 6 fall below 300 dpi. Supply the existing PDF (vector) versions as the production files.
  - Captions use a "Notice that ..." style and include data paths; trim them to a description of the content.
  - Fig. 4 (left): the registered criterion is 0.895 but the dashed line is at 0.900, which is confusing. Draw the criterion line itself.
  - Fig. 1 is labelled "illustrative, not data", which is good.
  - Check colour-vision safety of the orange and green pairs in Figs. 3, 5 and 6, or add hatching.
- **Numbering:** Proposition 6 is cited in the main text but stated only in the Supplementary Material (B.4), so the main text jumps from Proposition 5 to Propositions 7 and 8. Either state Proposition 6 in the main text or renumber.
- **References:**
  - "Global Market Insights, 2026" is a commercial market report; replace it with peer-reviewed or official sources.
  - Zhao et al. (2024) is cited as arXiv only; check for a published version.
  - Everett (n.d.) "exact commit not recorded" is not acceptable for reproducibility; record the commit or release tag.
  - Use the journal's reference style throughout, and give full details for Takasu and Yasuda (2009) and the NOAA CORS entry.
  - The reference list is heavily weighted towards statistics and robotics, with only one CEA paper (M7).

### M7. Positioning in the agricultural-engineering literature is thin

- **Location:** Sections 1–2 and the references.
- **Why it matters:** The related-work section covers conformal prediction, extreme-value theory and robust MPC in depth. It barely touches the agricultural literature that CEA readers know and that reviewers will be drawn from:
  - pass-to-pass and guidance accuracy testing (for example ISO 12188-1/-2 and published evaluations of commercial autosteer);
  - overlap and skip economics and automatic section control (for example Batte and Ehsani, 2006, CEA);
  - agricultural coverage planning beyond Fields2Cover (for example Oksanen and Visala, 2009; Spekken and de Bruin, 2013; the work of Bochtis and colleagues);
  - GNSS error modelling for agricultural vehicles.

  Without these references, a reviewer pool from agricultural engineering will see the paper as foreign to the journal, and a reviewer pool from statistics will not judge the practical claims.
- **Concrete fix:** Add a paragraph on guidance accuracy testing and on the economics of overlap and section control, with about 8–12 agricultural references, including CEA and Biosystems Engineering papers. Explain explicitly why existing vendor pass-to-pass specifications (a 95% or 2-sigma statistic of a short test) do not translate into a field-level zero-miss probability. The paper's own Table 1 and Gumbel scale law make this case well, so put it up front.

### M8. Practical deployability is under-specified

- **Location:** Sections 4.2, 4.3 and 7.4.
- **Why it matters:** Several things a practitioner would need are not addressed:
  - **Data requirements.** CE+ needs at least 9 (marginal) or 22 (PAC) logged operations on the same field with the same machine configuration, and the paper itself says a field is worked "a few times per year". This is several years of data, during which the receiver, the controller firmware or the implement may change.
  - **Ground truth.** It is not stated how a farmer would obtain the exact run score of a past operation. The executed footprint must be known to centimetre level, but the autosteer's own GNSS cannot see its own GNSS error. The common-mode error that the paper shows dominates the DGPS edge misses is invisible in the machine's own logs. This is perhaps the most important practical gap: the method assumes run scores that real logs do not contain, unless an independent reference (PPK, or RTK on a DGPS machine) is used.
  - **Operating details.** Curved passes, contour operations, headland coverage and section control are excluded, and so is the dependence on speed.
- **Concrete fix:** Add a "Deployment" subsection that states:
  - what must be measured and with what reference accuracy;
  - which operations it applies to;
  - how a contractor would obtain scores for the CE-EVT-R calibration pool;
  - which of the method's components can run on existing terminals.

  Be explicit that the guarantee is with respect to *measured* scores, so the validity of the guarantee in practice depends on the reference positioning.

---

## 5 Minor issues

1. **Title.** At 19 words with "Conformal Erosion with Theory-Pivoted Calibration", it is opaque to the readership. Consider something like "Certified overlap for agricultural field operations: guaranteeing complete coverage under GNSS and steering errors".
2. **Section 1, paragraph 1.** The FAO pesticide figure and the nitrogen-use-efficiency figure motivate input costs, but they are never connected to the size of the overlap savings. Either connect them (see M4.3) or drop them.
3. **Section 3.** Define "erosion" in plain words where it first appears ("margin by which the planned footprint is shrunk"). "Erosion" is a morphological term and readers will associate it with soil erosion. Consider "safety margin".
4. **Section 3, Lemma 1.** "Up to floating-point ties" is unnecessary in a journal statement.
5. **Section 4.2.** The probe-line idea is practically attractive but under-motivated. Report the measured correlation between probe-line XTE and the run score in the simulator, and say how sensitive CE+ is to it. Since CE+ reduces to CE-q when b ≈ 0, which happens under GNSS-dominated error, state for which regimes the normalisation was actually selected.
6. **Section 4.4.** Runtimes of 16–353 s per field are fine. State the hardware, and whether the run time scales with the number of operating-condition samples.
7. **Section 5.2, Proposition 2.** Give the numbers behind "about 0.7%" explicitly, or move the proposition to the appendix.
8. **Section 6.1.** Paddy-field geometry from China is combined with GNSS errors from US Midwest stations. State why this combination is reasonable, for example by discussing ionospheric latitude and multipath.
   - The combine-harvester trajectories define the field boundaries, but the operations simulated are spraying and seeding. This is fine, but say so.
   - The 1.5 m implement in R2 (oracle overlap 24.9%) is unusual. Name a real implement it represents.
9. **Section 6.1, field splits.** The reuse of fields 50–79 for both v8 and E-low v2 and the earlier use of fields 5–19 are correctly disclosed. They are hard to follow, though. A small diagram of the field-index splits in the Supplementary Material would help.
10. **Section 6.3, Table 5.** Overlap is reported with P in parentheses inside the same cell, which makes the table hard to read. Use separate columns. "CE+ v8" should simply be "CE+".
11. **Section 6.3.** "CE+ is below the oracle in R1 marginal" (regret −0.26 pp) needs a sentence of explanation: the method under-covers slightly (P = 0.903 vs the oracle's 0.9 target, with sampling noise). Otherwise a reader will think the oracle is not an oracle.
12. **Section 6.4.** Excess-overlap results in "pp above the per-field oracle" mix efficiency with realised coverage. The matched-coverage idea is good, but explain it in one plain sentence before using it.
13. **Fig. 7 / Section 6.6.** The predicted ideal inflation of 1.30 ± 0.35 (R1) is so wide that the agreement "within one predicted sd" has little power. Say this explicitly, or present the result more modestly.
14. **Section 7.4, practical guidance.** Good idea, but it is phrased in method names. Rewrite it as a short decision table: data available × machine fleet → method, with expected overlap.
15. **Section 8.** "Validation on a real vehicle is the next step" is in tension with a TODO Section 6.7 (see M3).
16. **Pre-registration.** It relies only on git commit timestamps, which can be rewritten. Provide the commit hashes and a third-party archive such as OSF or Zenodo snapshots, or describe it more modestly as "internally pre-specified".
17. **Units and notation.** The paper switches between cm and m for margins (Table 3 is in cm, Fig. 2 in m). λ is used for both the erosion and the spectral moments λ0 and λ2 (Proposition 4). Rename the spectral moments.
18. **Reference details.** Hameed et al. (2016) lacks a DOI. Rice (1944) and Booton (1954) are fine but probably unnecessary in the main text after M1.
19. **Cover letter.**
    - Claims of the form "certifies fields that have never been worked" need the qualifier "provided the field comes from the same population as the calibration fields".
    - The cover letter says the method "can be used directly with standard guidance hardware, auto-steer logs". This conflicts with M8, because standard auto-steer logs do not contain the ground-truth run score.
    - Address the letter to the editor by name, and suggest potential reviewers from both communities.
20. **Supplementary Material.** About 10,700 words is acceptable for an online supplement, but number its tables and appendices consistently with the main text (S1–S22). Make sure every supplementary item cited in the main text exists.

---

## 6 Advice to the authors

You have a genuinely good idea, a careful statistical treatment and an unusually honest experimental record. The current manuscript, however, is written for reviewers of a statistics or robotics conference. CEA readers want to know three things:

- how much overlap to set;
- how sure they can be that nothing is missed;
- what data they need to collect to get there.

My recommendations, in order of priority:

1. **Clean the submission** (M6). Remove every TODO, the author notes, the HTML comments and the repository paths. Complete the AI declaration, the data availability statement with a DOI or review link, the authors and the funding. Without this I cannot send the paper to reviewers.
2. **Get real machine data** (M3, M8), even a modest amount. Replaying logs from an RTK autosteer tractor with a PPK reference on 10–20 fields would turn this from a simulation paper into an engineering paper. If that is impossible in the revision time frame, add the simulator-validation and sensitivity analyses of M3, remove Section 6.7, and label the work clearly as a simulation study.
3. **Make the criterion agronomically meaningful** (M4). Add a gap-width or missed-area tolerance, report missed area, and express overlap savings in input cost.
4. **Re-centre the headline on a fair comparator** (M5). Use stratified per-configuration pooling and CQR in the abstract, the highlights and the graphical abstract.
5. **Cut the main text to about 8,000 words** (M1, M2). Move most theorems to the appendix and explain the theory physically in one page. Add a worked example, a workflow figure and a nomenclature table, and rename the experiments.
6. **Connect to the agricultural guidance literature** (M7).

If you do this, I expect a constructive review and a realistic route to acceptance. If the revision stays in its present register and remains simulation-only, I would advise you to consider a statistics or robotics venue, where the theory would be valued more and the missing field data would matter less.

*Handling Associate Editor*

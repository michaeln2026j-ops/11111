# Round 2: language and structure review (English manuscript)

**Reviewed:** `docs/paper/manuscript.md`, and the typeset `docs/paper/latex/manuscript.pdf` via `pdftotext -layout`.
**Role:** senior language and structure editor, *Computers and Electronics in Agriculture*.

## Overall assessment

The restructure has mostly worked. The title, abstract, Section 1 and the new Section 3.2 now tell the story "problem, proposed method, how it works, how well it works", and the four-step workflow (Fig. 1, Section 3.2) gives an agricultural engineer a clear way into the method. The weak points are in the details. Several leftovers of the old theorem paper remain in the text, tables and figures: the "Pivot" column header, "the theorem", "rests on no theorem", "certificate batch", "certified margin" and "run score" printed inside Figs. 2 and 3. Table numbering in the PDF does not match the Markdown. The transfer check is described in three incompatible ways (refuse / fall back to CE / keep the reference plan) and is defined in the wrong section. Sections 3.4, 3.5 and 3.7 are still written in dense, statistician-oriented prose (one-sentence algorithms, Kac–Rice, Lyapunov recursions, "within-field tail ratio"). The word "coverage" is used for both area coverage and statistical coverage, which will confuse a CEA reader. Fixing the 15 highest-ranked items below would remove most reviewer friction; the rest are polish.

Items are ordered by severity: A = consistency errors a reviewer will flag; B = readability and storyline; C = grammar, style, Elsevier conventions.

---

## A. Consistency errors and leftovers from the restructure

**1. Table numbering differs between the Markdown and the PDF, and the PDF nomenclature points to the wrong table.**
*Location:* Nomenclature, row "CE, CE-q, CE+ … (Table 2)"; Table 1 (GNSS) and Table 2 (variants) in the Markdown.
*Problem:* In the Markdown, the GNSS error table is Table 1 and the variants table is Table 2. The variants table appears first (Section 3.2), but Table 1 is cited first (Section 2), so this order is defensible. LaTeX numbers floats by position, so the PDF prints the variants table as **Table 1** and the GNSS table as **Table 2**. The hard-coded "(Table 2)" in the PDF nomenclature therefore points to the GNSS table. Elsevier requires tables to be numbered in the order they are first cited, and the PDF order now conflicts with the first citation (Section 2 cites the GNSS table first).
*Fix:* Replace the hard-coded nomenclature reference with `\ref{tab:2}`. Then either (a) move the Section 2 citation so the variants table is cited first, or (b) place the GNSS table float before Section 3.2. Make the Markdown follow the PDF numbering. Nomenclature row: "CE, CE-q, CE+ | conformal erosion calibrated on the field's own runs (Table 1)".

**2. The transfer check is described in three incompatible ways.**
*Location:* Section 3.2, step 4 ("A transfer check refuses the deployment if…"); Fig. 1 caption ("The transfer check falls back to the reference plan…"); Fig. 1 panel 4 ("keep the reference plan"); Section 3.4 ("CE+ must refuse … and fall back to CE"); Section 5.5 ("refuse or fall back to CE").
*Problem:* "Refuse", "fall back to the reference plan" and "fall back to CE" are different actions. Falling back to CE means new pilot and verification batches; keeping $\pi(\lambda_\mathrm{ref})$ does not.
*Fix:* Choose one action and use it everywhere. For example, in Section 3.2 step 4: "If $\hat\lambda>\lambda_\mathrm{ref}$, the transfer check rejects $\pi(\hat\lambda)$ and deploys the reference plan $\pi(\lambda_\mathrm{ref})$ instead, which is covered by the assumption-free guarantee of CE (Section 3.7)." Use the same wording in the Fig. 1 caption, Fig. 1 panel 4, Section 3.4 and Section 5.5.

**3. The transfer check is defined under CE+, but it applies to CE-q and XCE too, and it is cited from two different sections.**
*Location:* Section 3.4, paragraph "**Transfer check (revision).** CE+ must refuse…"; Section 3.2 step 4 points to "Section 3.7"; Sections 4.2, 4.4 and 5.1 point to "Section 3.4".
*Problem:* Section 4.4 applies the check to XCE ("The transfer check of Section 3.4 would have refused these deployments"), but Section 3.4 defines it for CE+ only. The label "(revision)" records editing history and does not belong in a method description.
*Fix:* Move the paragraph into step 4 of Section 3.2 (or into Section 3.7) and make it general: "**Transfer check.** For every variant that deploys a plan other than the reference plan (CE-q, CE+, XCE), the deployed margin must not exceed $\lambda_\mathrm{ref}$; otherwise the deployed plan has more passes than the plan on which the scores were recorded, and the guarantee does not apply. The pre-registered experiments ran without this check; Sections 4.2 and 4.4 report how often it would have been triggered." Then point every later citation to that one section.

**4. Theorem-era leftovers in the text.**
*Location:* (a) Section 4.2, *Transfer check*, "on those fields the guarantee rests on no theorem"; (b) Table 6 caption, "Per-configuration coverage is not guaranteed by the theorem"; (c) Table 6 header, "Pivot".
*Fix:*
(a) "…on those fields the guarantee of Section 3.7 does not apply, although the measured P(no miss) still met the target (pooled 0.896 and 0.933; meet rate 0.90 and 1.00)."
(b) "Per-configuration coverage is not part of the guarantee (Section 3.7); values below 0.88 are in bold."
(c) Rename the column header "Pivot" to "Scale" in both `manuscript.md` and `manuscript.tex` (line 426).

**5. "Run score" (the old name) is printed inside the figures.**
*Location:* Fig. 2(c), panel text "Run score at this section: r⋆ = …"; Fig. 3, both x-axes "Simulated 0.9-quantile of run score (m)".
*Problem:* The text says "coverage score" throughout. Fig. 2(c) also prints $S=\lambda+\max_x(\cdot)$ and "no strip missed ⇔ S ≤ λ", which conflicts with Section 3.3, where the definition uses $\lambda_\mathrm{ref}$.
*Fix:* Regenerate both figures. Fig. 2(c): "Coverage score: $r^\star$ = largest half-gap or edge distance; $S=\lambda_\mathrm{ref}+\max_x(r^\star(x)-w/2)$; no strip missed ⇔ $S\le\lambda_\mathrm{ref}$." Fig. 3 x-axis: "Simulated 0.9 quantile of the coverage score (m)"; y-axis: "Predicted 0.9 quantile of the coverage score (m)".

**6. "Certificate" and "certified" survive as names for the method's outputs.**
*Location:* Table 2, "(pilot + certificate batch)"; Section 3.4 CE, "draws a fresh certificate batch, … if the certificate quantile $q^\star$…"; Section 4.5 heading "What a certified margin costs" and its text; Table 8 rows "certified, $\varepsilon=0.1$ (ideal)" and caption "the target of an exactly calibrated certificate"; Fig. 6 legend and caption "Certified, ε = 0.1"; Section 5.4 item 2, "logging and certification tools"; Section 3.3, "no other score that certifies complete coverage".
*Problem:* The rest of the paper speaks of a "calibrated margin". For a CEA reader, "certified" suggests a regulatory certification.
*Fix:* Use "verification batch", "verification quantile", "calibrated zero-miss margin" and "calibration tools". Section 4.5 heading: "What a calibrated zero-miss margin costs". Table 8 row: "calibrated, $\varepsilon=0.1$ (ideal)". Table 8 caption: "…each field's own 0.9 margin, the margin an exactly calibrated method would deploy". Section 3.3: "and no other score that guarantees complete coverage is smaller".

**7. The assumption (S) has three names, and its label clashes with the score $S$.**
*Location:* Table 2, "under the coupling assumption (S)"; Section 3.4 CE-q, "the coupling assumption of Section 3.7"; Section 3.7, "(assumption S)"; Sections 4.2, 5.1 and 5.4, "the transfer assumption (S)".
*Problem:* "Coupling", "transfer" and "S" all name one assumption, and $S$ is already the coverage score.
*Fix:* Use one name and a label that does not clash, for example "the transfer assumption (A1)". Section 3.7: "…by at most a noise-independent amount (transfer assumption A1)." Use "transfer assumption (A1)" in Table 2, Section 3.4, Section 4.2, Section 5.1 and Section 5.4.

**8. The symbol $r$ / $r^\star$ has two meanings.**
*Location:* Section 3.3, "$r^\star(x)=\max\{\dots\}$" (covering radius); Section 3.6, "$2(r^\star-w/2)$"; Section 4.5, "$r$ be the cost…" and "break-even ratio of $r^\star\approx43$"; Nomenclature, "$\tau$, $r$".
*Problem:* $r^\star$ is the covering radius in Section 3.3 and the break-even cost ratio in Section 4.5. Neither use of $r^\star$ is in the nomenclature.
*Fix:* Rename the covering radius $\rho(x)$ (or $R(x)$), or call the break-even ratio $r_\mathrm{be}$. Section 4.5: "…pays off only above a break-even ratio of $r_\mathrm{be}\approx43$ (R1)…". Add both symbols to the nomenclature.

**9. The labels "C1"–"C4" mean both registered claims and experiments.**
*Location:* Table 5, "C1: R1 PAC, and C2: R3 marginal…", "C3: mixed fleet…; C4: gated variant…"; Section 3.8 and Section 4.4, "C1, model mismatch; C2, headland laps".
*Problem:* A reader of Section 4.4 who has just seen Table 5 will take "C1" to be a claim.
*Fix:* Relabel the claims in Table 5 as "H1–H4" (and "V", "E" in A1 as "H-V", "H-E" if you want a uniform style). Also explain "P4.1–P4.4" in Section 4.4 on first use: "None of the four registered predictions (P4.1–P4.4; Table S27) was met in every variant: overall validity (P4.1) and CE-q validity (P4.4) failed in T1 only…".

**10. "Calibrated plan" is used where "reference plan" is meant.**
*Location:* Section 3.2 step 4, "a plan with more passes than the calibrated one"; Section 3.4, "more passes than the calibrated one"; Section 4.4 C1, "the deployed plan had more passes than the calibrated one"; Section 6 item 3, "when the deployed margin exceeded the calibrated one".
*Problem:* The calibrated margin *is* the deployed margin, so in Section 6 the sentence is self-contradictory. What is meant is the reference plan or margin.
*Fix:* Section 6 item 3: "The guarantee itself fell short only when the deployed margin exceeded the reference margin, a case the transfer check excludes." Elsewhere: "…a plan with more passes than the reference plan on which the scores were recorded…".

**11. Bold formatting in Table 6 does not follow the caption's rule.**
*Location:* Table 6, caption "values below 0.88 are in bold"; rows "Per-configuration scale … 0.842" and "CQR … 0.866".
*Problem:* Only 0.779 and 0.840 are bold; 0.842 and 0.866 are also below 0.88 but are not. Table 7 uses a different threshold ("below 0.85 for one configuration"), and its bold "0.895" is not "below 0.895".
*Fix:* Bold 0.842 and 0.866 in Table 6. Use one threshold in both tables, or state why they differ. Table 7 caption: "Bold: at or below 0.895 overall, or below 0.85 for one configuration."

**12. One metric has two names, and the oracle has five.**
*Location:* "Regret" (Section 3.8 *Metrics*, Table 4, Fig. 4, Section 4.2) and "excess overlap" (Tables 5–7, Section 4.3, Fig. 5). The oracle is also called "per-field optimum" (Abstract, Section 5.2, Section 6), "field's own requirement $\lambda^\star_f$" (Nomenclature), "each field's own 0.9 margin" (Fig. 2, Table 8) and "certified (ideal)" (Table 8).
*Fix:* Use "excess overlap (pp above the field's oracle margin)" everywhere and drop "regret". Define the oracle once in Section 3.8: "The **oracle margin** $\lambda^\star_f$ of a field is the smallest margin whose P(no miss) on test runs is 0.9; it requires the test distribution and is a reference, not a method." Then write "oracle margin" in Fig. 2, Table 8, Section 5.2 and Section 6. The abstract may say "the per-field oracle" once.

**13. The overlap reduction is reversed in Section 5.2.**
*Location:* Section 5.2, "CE+ reached its target while two conformal planners over-covered at 4–55% more overlap."
*Problem:* Table 4 reports that CE+ used 4.0–54.7% *less* overlap than the comparators. In the other direction this is 4–121% *more*, not 4–55%.
*Fix:* "CE+ reached its target with 4–55% less overlap than two conformal planners, which over-covered."

**14. The cost break-even is rounded inconsistently and conflicts with Section 5.3.**
*Location:* Abstract, "30–100 times"; Highlights, "30–100x"; Section 4.5, "43 (R1), 58 (R2) and 88 (R3); … 31–35 (RTK) and 88–117 (DGPS)"; Section 5.3, "unless a missed unit costs several hundred times an over-applied one"; Section 5.5, "about 30–100".
*Problem:* 117 lies outside "30–100". Section 5.3 ("several hundred") answers a different question (cost-optimality, not break-even against the vendor rule), but reads as a contradiction.
*Fix:* Abstract: "A zero-miss margin paid off against the vendor rule only when a missed unit area cost about 30–120 times an over-applied one." Section 5.3: "And a zero-miss margin at $\varepsilon=0.1$, although cheaper than the vendor rule above a cost ratio of about 30–120, is the cost-optimal choice under RTK only when a missed unit costs several hundred times an over-applied one (Section 4.5)…".

**15. The thresholds for when to calibrate on the field itself disagree.**
*Location:* Section 4.2 A2, "With fewer than about 20 logged operations per field, cross-field calibration (Experiment B) is the practical route."; Section 5.5, "With at least 9 (marginal) or 22 (PAC) logged operations per field, calibrate on the field (CE-q/CE+)."
*Fix:* Section 5.5: "With at least 22 logged operations per field (9 under the marginal rule, at a cost of 1–8 pp of extra overlap; Section 4.2), calibrate on the field (CE-q/CE+); with fewer, calibrate across fields."

**16. Experiment B6 appears in Results but not in the list of experiments in Section 3.8.**
*Location:* Section 3.8 *Experiments*, "*Experiment B, fields without history*: B1–B3, … B5, …"; Section 4.3, "**B6, model accuracy against learned predictors (post hoc).**"
*Fix:* Add to the Section 3.8 list: "…; B6, accuracy of the model scale against learned predictors (post hoc)."

**17. The fourth "step" of XCE-T is not a step of XCE-T.**
*Location:* Section 3.5, list item 5, "**Scale law.** The required margin grows like $\sqrt{2\log L}$ … this heuristic is used only for a comparator scale."
*Problem:* The text announces "five steps" of XCE-T, but step 5 is not used by XCE-T.
*Fix:* Change "in five steps" to "in four steps", delete item 5, and add after the list: "A by-product of the analysis is a scale law: the required margin grows like $\sqrt{2\log L}$ in the effective length $L$ of the field (a tenfold larger field raises the margin by about 11%); it is used only for the 'specification × scale law' comparator."

**18. Content is duplicated between the Methods, Results and Discussion.**
*Location:* (a) Section 3.5 "Why the field-edge terms matter" ends with C2 results ("binding term … 1% (RTK) and 10% (DGPS) … 0.1% and 1.9%"), repeated in Section 4.4 C2. (b) Section 3.7 "Computational cost" repeats the runtimes in Section 4.1 ("16–353 s per field … median of 8–21 s"). (c) "within a few tenths of a point" is stated in Section 3.7, Table 5, Section 4.3 (B2) and Section 5.3. (d) Section 5.1 restates Section 3.7 almost point by point.
*Fix:* (a) End the Section 3.5 paragraph at "…when adjacent passes share part of the GNSS error." and add "Section 4.4 (C2) reports how often they set the score." (b) Keep runtimes only in Section 4.1, and leave a one-line pointer in Section 3.7: "The model scale is computed once per field, offline; runtimes are reported in Section 4.1." (c) Give the number once (Section 4.3) and refer to it elsewhere. (d) Shorten Section 5.1 to the empirical findings: "Section 3.7 lists the assumptions. Empirically, plans deployed below the reference margin met the target in every experiment (A2, B4, B5, C2), plans above it fell slightly short (0.891–0.895 in C1-T1), and the model scales affected only efficiency…".

**19. Repository code names and internal field indices remain in the main text.**
*Location:* Section 3.8, "(repository 'v8')", "('E-low v1–v3')"; Table 2 caption, "In the pre-registrations XCE-T is called CE-EVT-R."; Section 4.2, "two claims on fields 50–79 of each configuration".
*Fix:* Move the mapping to Supplementary Table S20 and add one sentence to Section 3.8: "Supplementary Table S20 maps each experiment to its pre-registration and repository name." Section 4.2: "The registration fixed two claims on 30 fresh fields per configuration:".

**20. The appendices are called both "Appendix" and "Supplementary", and some headings still use the old vocabulary.**
*Location:* "Appendix A.4", "Appendix B.4" versus "Supplementary D.3–D.6" (Section 4.3) and "Table S19a" (Section 4.3, B4). In `supplementary.md`, headings read "Appendix A. Proofs and formal status…", "B. Theory details", "B.4 … pivot (Remark…)", "C.4 E-low protocols", and D.7a/D.10 are out of order.
*Fix:* In the main text, use "Appendix X (Supplementary material)" on first mention and then "Appendix X" consistently: "(details in Appendix D.3–D.6)". Rename B.4 to "Ratio versus probability-integral-transform scale" and B to "Model-scale details". Renumber D.7a/D.7/D.9/D.10 in order, and replace "Table S19a" with a regular number.

**21. The variants share fewer steps than Section 3.2 claims.**
*Location:* Section 3.2, "They share steps 1, 2 and 4 and differ in where the calibration scores come from and how they are scaled."
*Problem:* CE iterates step 1 and deploys $\pi(\lambda_\mathrm{ref})$, not $\pi(\hat\lambda)$. CE+ sets $\lambda_\mathrm{ref}$ from training fields. Step 4 as written ("The planner generates $\pi(\hat\lambda)$") does not apply to CE.
*Fix:* "They share step 2. They differ in how the reference margin is chosen (step 1), where the calibration scores come from and how they are scaled (step 3), and whether the deployed plan is the reference plan itself (CE) or a plan with a smaller margin (CE-q, CE+, XCE; step 4)."

**22. Ranges in Section 4.3 (B5) cannot be found in Table 6.**
*Location:* Section 4.3, "The model scales covered every configuration at 0.885–0.936"; "…instead of 0.834–0.904 (Table S26)"; "and 4.2–4.4 pp (PAC) against 6.2–6.4 and 12.2 pp".
*Problem:* Table 6 shows model-scale coverage of 0.904–0.936 only, and Mondrian PAC at $n=60$ is listed as "refuses on 74%" with no 12.2 pp value.
*Fix:* "Across both calibration sizes and rules, the model scales covered every configuration at 0.885–0.936 (Table S26; Table 6 shows $n=25$, marginal) … and 4.2–4.4 pp (PAC) against 6.2–6.4 pp for the configuration-aware scales and 12.2 pp for Mondrian on the 26% of fields it did not refuse."

**23. The B2 value 0.844 appears without having been introduced.**
*Location:* Section 4.3 B4, "The sub-0.9 values of B2 (0.844) and B3 (0.877) are therefore draws of the calibration data."
*Problem:* 0.844 is not in Table 5 or anywhere earlier in the text, and "are draws of" is a loose phrase.
*Fix:* "The realised coverages below 0.9 in B2 (0.844, R3 marginal; Appendix D.4) and B3 (0.877) are therefore consistent with the sampling variation of a single calibration draw."

---

## B. Readability, storyline and accessibility for a CEA reader

**24. "Coverage" carries two meanings, area coverage and statistical coverage.**
*Location:* Throughout: "coverage path planning", "coverage score" and "complete coverage" (area) versus "coverage 0.9", "mean coverage", "per-configuration coverage", "realised coverage" and "over-cover" (probability). The worst cases are in Section 4.3 ("The model scales covered every configuration at 0.885–0.936") and Section 5.1 ("the DGPS fields … were covered at 0.78").
*Problem:* An agricultural engineer will read "DGPS fields covered at 0.78" as 78% of the area worked.
*Fix:* Define once in Section 3.8 *Metrics*: "P(no miss), also called *reliability*, is the fraction of runs without any missed strip." Then replace statistical "coverage" with "reliability" or "P(no miss)". Section 4.3: "The model scales gave every configuration a P(no miss) of 0.885–0.936." Section 5.1: "with configuration-blind pooling, the DGPS fields of a mixed fleet reached a P(no miss) of only 0.78…".

**25. The Section 2 paragraph on conformal prediction has no main verb.**
*Location:* Section 2, *Conformal prediction*, "Split conformal prediction and its training-conditional (PAC) variant (Vovk, 2012); … and functional conformal bands (…), of which a sup-normalised coverage score is an instance."
*Fix:* "The method builds on split conformal prediction and its training-conditional (PAC) variant (Vovk, 2012), on conformal prediction under covariate shift and beyond exchangeability (Tibshirani et al., 2019; Barber et al., 2023), on conformalized quantile regression (CQR; Romano et al., 2019), on conformal risk control (Angelopoulos et al., 2024, 2025), on hierarchical conformal prediction with one sample per group (Dunn et al., 2023), and on functional conformal bands (Lei et al., 2015; Diquigiovanni et al., 2022), of which the coverage score is an instance."

**26. The CE algorithm is packed into a single sentence.**
*Location:* Section 3.4, "**CE.** CE iterates pilot batches, $\lambda_\mathrm{ref}\leftarrow1.10\,q$ with $q$ the … until $q\le\lambda_\mathrm{ref}$, freezes the plan, draws a fresh certificate batch, and deploys…".
*Fix:* "**CE.** CE first searches for a sufficient reference margin: it logs a pilot batch of runs on $\pi(\lambda_\mathrm{ref})$, computes the $(1-\varepsilon)$ quantile $q$ of their scores, and sets $\lambda_\mathrm{ref}=1.10\,q$, repeating until $q\le\lambda_\mathrm{ref}$. It then freezes the plan, logs a fresh verification batch, and deploys $\pi(\lambda_\mathrm{ref})$ if the verification quantile $q^\star$ does not exceed $\lambda_\mathrm{ref}$; otherwise it deploys nothing. Because the deployed plan is the plan on which the runs were scored, no further assumption is needed."

**27. The CE+ normalisation sentence is too long.**
*Location:* Section 3.4, "The normalised score is $\tilde S=S/\sigma(z)$ with $\sigma(z)=\max(a+bz,\ 0.3\,\bar\sigma)$, $(a,b)$ fitted on training fields after … and a new operation deploys…".
*Fix:* "Each score is divided by a predicted scale, $\tilde S=S/\sigma(z)$, where $\sigma(z)=\max(a+bz,\ 0.3\,\bar\sigma)$ is a linear function of the probe-line XTE, floored at 30% of its mean $\bar\sigma$. The coefficients $(a,b)$ are fitted on the training fields after each field's scores are divided by their median. For a new operation, the machine drives the probe line, and the margin $\lambda=t\,\sigma(z_\mathrm{new})$ is deployed, where $t$ is the conformal quantile of the calibration values $\tilde S_i$." Also explain "gated" in Table 2: "probe-line XTE (used only if it passes a cross-validation check)".

**28. Step 1 of XCE-T is heavy with jargon.**
*Location:* Section 3.5, item 1, "**Closed-loop covariance.** Linearised along the noise-free closed-loop path of each pass, with describing functions for steering saturation…".
*Fix:* Add a plain-language lead sentence and shorten the rest: "**Closed-loop covariance.** For a given operating condition (soil moisture, slip and roughness gains, roll compensation, mounting bias and GNSS error trajectory), the lateral offset of one pass is approximated as a Gaussian process. Its covariance is obtained by linearising the closed loop along the noise-free path, with describing functions for steering saturation and rate limits and a leaky integrator for the anti-windup clamp (Appendix B)."

**29. Step 2 of XCE-T contains a contradiction ("computed exactly by … Monte Carlo").**
*Location:* Section 3.5, item 2, "…and computed exactly by Gaussian Monte Carlo where that bound is loose."
*Fix:* "The probability that the gap between two passes exceeds a threshold anywhere along the pass is bounded by a discrete Kac–Rice upcrossing sum; where this bound is loose, it is replaced by a Gaussian Monte Carlo estimate."

**30. The correlation sentence in "Why the field-edge terms matter" is garbled.**
*Location:* Section 3.5, "(in the 1 Hz DGPS series, the correlation at the 13–113 s between adjacent passes at one section is 0.91–0.41; for RTK 0.71–0.54)".
*Fix:* "(adjacent passes cross a given point 13–113 s apart, and at these lags the lateral GNSS error has a correlation of 0.91–0.41 for DGPS and 0.71–0.54 for RTK)".

**31. The second property of the coverage score reads like a leftover proof.**
*Location:* Section 3.3, "Second, it is the smallest score that never declares a run with a missed strip miss-free, so any calibration rule built on order statistics deploys no more passes with this score than with any other such score, including…".
*Fix:* "Second, it is the tightest such score: any other score that never labels a run with a missed strip as miss-free is at least as large on every run. For the same logged runs and the same calibration rule, it therefore gives the smallest margin, smaller in particular than the per-pass-pair maxima used by earlier conformal planners."

**32. The symbols $c_i$, $g$ and the index of $V$ are not defined, or are inconsistent.**
*Location:* Section 3.3, "let $Y(x)$ be the executed centres … sorted" (then $c_i$ appears); Section 3.5, "$V_i=S_i/\hat q_{f_i}$" and then "gets $V_f=+\infty$"; Table 2, "$\pi(\hat q_g v^\star)$" (where $g$ is not yet defined).
*Fix:* Section 3.3: "…let $c_1<c_2<\dots$ be the executed centres of the passes that reach the chord $[\ell(x),u(x)]$ of $W$, and $Y(x)$ their set." Section 3.5: "A calibration field whose prediction fails ($\hat q_{f_i}$ not finite) gets $V_i=+\infty$." Table 2: "$\pi(\hat q_g v^\star)$, $g$ = target field".

**33. "Section" is easily confused with sprayer section control.**
*Location:* Section 3.1, "Coverage is evaluated on 1 m sections across $W$."; Section 3.3, "At section $x$…", "in each 1 m section"; Section 5.5, "covering radius per section".
*Problem:* In agricultural engineering, "section" usually means a boom or planter section.
*Fix:* "Coverage is evaluated on cross-sections of $W$ spaced 1 m apart along the working direction." Then use "cross-section" throughout.

**34. "Marginal" and "PAC" are used in the Introduction before they are explained.**
*Location:* Section 1, paragraph 2, "…while a conformal margin at a miss level of 10% needs at least 9 (marginal) or 22 (PAC) logged runs."
*Fix:* "…while a conformal margin at a miss level of 10% needs at least 9 logged runs, or 22 if the guarantee must hold with high confidence for the particular runs logged (Section 3.4)."

**35. The Introduction's first paragraph has a misused "Both errors" and a dangling final sentence.**
*Location:* Section 1, "Overlap set to absorb this error applies inputs twice on the overlapped strip. Both errors carry a cost:… Autonomous machines remove the operator who used to correct visible gaps by eye."
*Fix:* "Overlap set to absorb this error applies inputs twice on the overlapped strip. Both outcomes carry a cost: missed strips lose yield or leave weeds and pests untreated, and overlap wastes seed, fertiliser and pesticide (FAO, 2025; Zhang et al., 2015, 2021). The problem is sharper for autonomous machines, which have no operator to correct visible gaps by eye."

**36. "Guarantee class" and "in both classes" are undefined jargon.**
*Location:* Section 4.2 A1, "**E** (efficiency within the guarantee class) … in both classes"; Fig. 4 caption, "marginal (a) and PAC (b) guarantee classes"; Section 4.2, "*What the gain is made of.*… design meet rates".
*Fix:* "**E** (efficiency): CE+ has lower main-area overlap than CPrP and UBCP under both the marginal and the PAC rule, by one-sided paired Wilcoxon tests with Holm correction over 12 comparisons." Fig. 4: "…under the marginal (a) and PAC (b) rule". "Design meet rates" → "the expected meet rates (about 0.85 marginal, 0.99 PAC; Section 3.8)".

**37. "Zero-data" is misleading, since the method uses data from other fields.**
*Location:* Section 3.5, "first zero-data experiment"; Section 3.8, "three pre-registered zero-data experiments"; Section 4.3 heading text and Table 5 caption.
*Fix:* Use "experiments without target-field data" or "cross-field experiments": "**B1–B3, pre-registered cross-field experiments.**"

**38. The results open with a model-accuracy check instead of the main comparison.**
*Location:* Section 4.1, "How accurate is the model scale?", placed before Experiment A.
*Problem:* For a method paper, the reader expects the main comparison first. The model scale is used only by XCE (Experiment B), and Section 3.8 does not list Section 4.1 as an experiment.
*Fix:* Move Section 4.1 to the start of Section 4.3 (as "B0, accuracy of the model scale") or after Experiment A. Alternatively, add a bridging sentence at the top of Section 4: "Section 4.1 first checks the model scale used by XCE; Sections 4.2–4.4 then report Experiments A–C."

**39. Experiment C1 is described in a single paragraph of about 450 words.**
*Location:* Section 4.4 C1, "Table 7 shows the result. **Validity.** … **Model accuracy.** … **Per-configuration coverage.** …".
*Fix:* Split it into three paragraphs at the bold run-in headings. Explain the log-bias on first use: "with a trailed implement the model over-predicted the margin by about 50% (log bias +0.42), because the implement low-pass filters the tractor's lateral error…". Also define "28-point margin curve": "…and P(no miss) and overlap were simulated at 28 margins per field (the margin curve)."

**40. "0.9 margin" in the Fig. 2 caption is cryptic.**
*Location:* Fig. 2 caption, "planned with that field's own 0.9 margin".
*Fix:* "planned with that field's oracle margin (the smallest margin with P(no miss) = 0.9)".

**41. Statistical shorthand in Section 4.1.**
*Location:* Section 4.1, "differs from it by a log standard deviation of 0.030 (R1)…"; "its own error, net of the reference noise, is therefore about 2–3% under RTK".
*Fix:* "…the twin's prediction differs from it by a standard deviation of the log ratio of 0.030 (R1), 0.032 (R2) and 0.083 (R3), roughly 3%, 3% and 8%, which is essentially the sampling noise of the 200-run quantile."

**42. A2 opens with a parenthesis that contains three clauses separated by semicolons.**
*Location:* Section 4.2 A2, "A2 replaces the 100 calibration runs by $n=9$–100 runs drawn from 200-run banks on 45 fields per configuration (2000 replicates per field; CE-q, the variant CE+ reduces to under constant normalisation; deployed plans evaluated on independent test runs)."
*Fix:* "A2 repeats the target-field calibration with $n=9$–100 runs instead of 100. For each of 45 fields per configuration, $n$ runs were drawn 2000 times from a bank of 200 runs, CE-q was calibrated on them (CE-q is what CE+ reduces to when the probe-line normalisation is not used), and the deployed plan was evaluated on independent test runs." Also remove the redundancy in "0.896–0.943, never below 0.895".

**43. Section 3.7, last bullet: the jargon "within-field tail ratio" and the vague "point".**
*Location:* Section 3.7, "**What no scale can remove.** … inflated by a within-field tail ratio set by $n$ and the PAC rule; … within a few tenths of a point of each other".
*Fix:* "**What no scale can remove.** Even a perfect scale cannot remove the run-to-run randomness within a field: with one logged run per calibration field, the order statistic must also cover how far a single run can fall above its field's 0.9 quantile, and this inflation depends only on $n$ and the rule. As a result, within one machine configuration all field-level scales gave overlaps within a few tenths of a percentage point of each other (Appendix A.20; Section 4.3)." The "information limit" in Section 5.2 should then point to this paragraph: "…and the limit on what any scale can achieve (Section 3.7)."

**44. The title is long and does not name the method.**
*Location:* Title, "A calibration method for setting pass overlap with a guaranteed probability of no missed strips in agricultural coverage path planning" (22 words).
*Fix:* "Conformal erosion: calibrating pass overlap from logged runs to guarantee a chosen probability of no missed strips in agricultural coverage planning". A shorter option: "Calibrating pass overlap in agricultural coverage path planning for a guaranteed probability of no missed strips".

**45. Ambiguous phrases in the Abstract.**
*Location:* Abstract, "the widest gap or edge recession of the executed passes"; "covering every machine configuration. This held under implement dynamics…".
*Problem:* "Edge recession" is coined jargon. "Covering" plays on "coverage". "This" has no clear referent, and the guarantee and the efficiency advantage behaved differently in C1.
*Fix:* "…one coverage score: the margin the run would have needed, set by the widest gap between adjacent passes or the largest retreat of the outermost pass from the field edge." And: "…against 1.2–4.4 for configuration-aware baselines, while meeting the target in every machine configuration. This efficiency advantage held with a trailed implement, degraded GNSS and levelled terrain, but not with heavy-tailed slip or unstable steering." Use "trailed implement", as in Section 6, rather than "implement dynamics". The abstract is now 249 words; stay at or below the journal limit after these edits.

---

## C. Grammar, punctuation and Elsevier style

**46. Citation separators and order in the PDF.**
*Location:* PDF Section 1, "(FAO, 2025, Zhang et al., 2015, 2021)", "(Galceran and Carreras, 2013, Höffmann et al., 2024, Mier et al., 2025, 2023)".
*Problem:* `elsarticle-harv` with default natbib settings prints commas between references. Elsevier Harvard style uses semicolons, as the Markdown does. The Mier years are also reversed.
*Fix:* Add `\setcitestyle{semicolon}` (or load natbib with `[authoryear,semicolon]`) and order `\citep{mier2023,mier2025}` → "(Galceran and Carreras, 2013; Höffmann et al., 2024; Mier et al., 2023, 2025)".

**47. The Highlights use "x" and the vague "an overlap".**
*Location:* Highlights, "A zero-miss margin pays off only if a miss costs 30–100x an overlap".
*Fix:* "Zero-miss margins pay off only if misses cost about 30–120 times overlap" (77 characters, within the 85-character limit).

**48. The figure label "(ours)" is informal.**
*Location:* Fig. 4 legend, "CE+ (ours)".
*Fix:* "CE+ (proposed)".

**49. A redundant heading in Section 3.2, step 1.**
*Location:* Section 3.2, "1. **Plan a reference plan.**"
*Fix:* "1. **Generate a reference plan.**"

**50. An elliptical "without," in Section 3.2, step 3.**
*Location:* Section 3.2, "With field history the scores come from the field itself (Section 3.4); without, from one run on each of many other fields, divided by a model-predicted scale (Section 3.5)."
*Fix:* "For a field with operation history, the scores come from the field itself (Section 3.4); for a field without history, they come from one run on each of many other fields, each divided by a model-predicted scale (Section 3.5)."

**51. "Therefore less overlap" should be "no more overlap", and the passive voice obscures who acts.**
*Location:* Section 3.4 CE-q, "which has no more passes than the reference plan and therefore less overlap"; Section 3.5, "the ratio $V_i=S_i/\hat q_{f_i}$ is formed".
*Fix:* "which has no more passes than the reference plan and therefore no more overlap"; "XCE forms the ratio $V_i=S_i/\hat q_{f_i}$ for each calibration field $f_i$…".

**52. Missing articles.**
*Location:* Section 3.4, "on average over calibration data"; Section 3.5 step 3, "against a true 0.900"; Section 4.2, "(P 0.92–0.99 at a nominal 0.9)".
*Fix:* "on average over the calibration data"; "against a simulated 0.900"; "(P(no miss) 0.92–0.99 at a nominal 0.9)".

**53. Colloquial phrasing in Section 4.2.**
*Location:* Section 4.2, "*What the gain is made of.*… which is what their extra overlap buys"; Section 4.5, "the same data bound $P(S>\lambda)$ for every $\lambda$".
*Fix:* "*Source of the gain.*… and this over-coverage accounts for their extra overlap"; "(the same logged runs give an upper bound on $P(S>\lambda)$ for every $\lambda$)".

**54. "Point" should be "percentage point".**
*Location:* Section 4.3, "within a few tenths of a point"; Section 5.2, "within a few tenths of a point in R1"; Section 5.3, "within a few tenths of a point".
*Problem:* Section 5.2 is also inaccurate: Table 4 shows the farmer-tuned margin 0.8 pp above CE+ in R1.
*Fix:* Use "pp" consistently. Section 5.2: "the farmer-tuned margin used 0.8 pp more overlap than CE+ in R1 and 2.2–2.6 pp less in R2 and R3, at lower reliability (it met the target on 20–70% of fields)."

**55. The tail sentence in the Table 1 caption is imprecise.**
*Location:* Table 1 caption, "a Gaussian with the same RMS underestimates it by orders of magnitude."
*Fix:* "a Gaussian with the same RMS underestimates the probability of errors beyond the 99.9th percentile by orders of magnitude."

**56. The nomenclature is incomplete.**
*Location:* Nomenclature.
*Problem:* Missing entries: $c_i$, $\ell$, $u$, the covering radius ($r^\star$ or its new symbol), $n$, $q$, $q^\star$, $V_i$, $v^\star$, $t$, $\sigma(z)$, $z$, $L$, $B$, the break-even ratio, and the acronyms RTK, DGPS, CORS, PPK, MPC, CQR, CVaR, RMS and XCE (as a family name). The entry for XCE-T should also say what "T" stands for, or the name should be changed to XCE-A (analytic) to pair with XCE-MC.
*Fix:* Add these rows, for example: "$v^\star$ | order statistic of the scaled scores $V_i=S_i/\hat q_{f_i}$ (Section 3.5)"; "XCE-T | cross-field conformal erosion with the analytic (theory-based) model scale".

**57. Experiment labels "(revision)" and "(revision, pre-registered)".**
*Location:* Section 3.4 heading "Transfer check (revision)", and Section 3.8 / Sections 4.1–4.4, "(revision, pre-registered)".
*Problem:* Status tags are useful, but "revision" refers to the editorial history, which a reader of the published article will not know.
*Fix:* Use "(pre-registered, second round)" or "(pre-registered addendum)", define it once in Section 3.8 ("Experiments marked 'addendum' were registered after the first set of results and before they were run"), and drop the tag from method paragraphs entirely.

**58. Minor wording fixes.**
- Section 3.1: "The task is to choose the smallest overlap whose probability of a run without any missed strip is at least $1-\varepsilon$" → "The task is to choose the smallest overlap for which the probability of a run without any missed strip is at least $1-\varepsilon$".
- Section 3.5, XCE-MC: "takes the 0.9 quantile of 1000 Monte Carlo runs" → "takes the $(1-\varepsilon)$ quantile (here 0.9) of the scores of 1000 Monte Carlo runs".
- Section 4.4 C2: "a boundary term was the binding term of a run" → "a field-edge term set the coverage score of a run". Keep "field-edge term" throughout (currently also "edge term", "boundary term", "edge recession").
- Section 5.2: "a model scale is the only configuration-aware scale that covered every configuration and was efficient" → "the model scale was the only scale that met the target in every configuration while remaining efficient".
- Section 4.3 B6: "did not reach the model's accuracy within the available pools" → "did not reach the model's accuracy even with the largest training pool available".

---

*End of report: 58 items. Items 1–23 are consistency errors, items 24–45 concern readability and storyline, and items 46–58 concern language and style.*

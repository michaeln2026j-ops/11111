# Round 2: changes to the English manuscript (`manuscript.md`) and supplement (`supplementary.md`)

Binding decisions D1–D10 (`decisions.md`) were implemented first; where a reviewer's suggestion conflicted with a decision, the decision was followed (noted per item). No result changed. New numbers come only from `results/revision/rv8_transfer_check.txt`, `results/revision/worked_example.txt` and existing result files (reference margins 17.5/19.4/43.4 cm from `rv1_v8_reanalysis.txt`; oracle margins 0.121/0.149/0.391 m from `rv5_laps.txt`; vendor margin 2.5 cm from `rv3_small_n.txt`; T3 excess values from `rv4_mismatch_edges45.txt`; predictions P2.1–P2.4 from `docs/prereg_revision.md`). Scripts and figures were not edited.

**Word counts.** Abstract 250 words. Main text (Introduction to Conclusion): 6,772 words of running text; 8,651 words including tables, table and figure captions (punctuation-only tokens and display equations not counted). Previous version: about 7,950 running text / 10,400 including tables.

**Build.** `python scripts/md2elsarticle.py` and `latexmk` on `manuscript` and `supplementary` run without errors or undefined references; highlights pass the 85-character assertion; all 40 listed references are cited and the list is unchanged.

## Decisions

| Item | Status |
|---|---|
| D1 title | Done. |
| D2 storyline (both directions, bound under exchangeability, no "guaranteed"/"assumption-free") | Done in abstract, highlights, Introduction (contribution paragraph), Conclusion; "distribution-free, given exchangeable runs/fields" throughout. |
| D3 one transfer-check definition | Done: Section 3.6 (new), step 4 of 3.2, Fig. 1 caption ("Transfer check: if λ̂ > λ_ref, recalibrate on a larger reference plan"), Table 2 caption, 4.1, 4.3, 5.5. "(revision)" removed. |
| D4 transfer-check results | Done: Table 6 has a row "CE+ / CE+ PAC, transfer check" for R3 (registered row kept and labelled); caption and text give 9/30, 19/30, 0.901/0.921, 16.06/17.40%, +0.78/+2.12 pp, reductions 22.2/33.7% and 32.8/59.2%; headline "4–55% (registered); 4–59% with the transfer check" in 4.1 and Conclusion; abstract "at the same nominal level". Meet rate of the check rows is not in rv8 and is shown as "—". |
| D5 validity claims | Done: abstract/5.1/Conclusion state where the target failed (follow-previous-pass 0.850; C1 wet patches 0.891–0.895); single draws 0.844/0.877 explained by B4; "observed 0.885–0.936 per configuration"; CE+ bound per A.9 in Table 2 and 3.8; ideal-scale identity, with "raw pooling was cheaper in one cell"; edge exceedance an upper bound under A3 (A.10, A.12); Gaussian Monte Carlo "estimated"; ε, τ fixed before the scores (3.7, Table 1, 5.5). |
| D6 terms | Done: "miss-free rate" for the probability, "coverage" only for area (tables, captions, text); "coupling assumption" (label (S) only in Appendix A); r_be; H1–H4 (in moved Table S30); "calibrated" (Table 9, Fig. 5 caption, 4.4 heading); "excess overlap" everywhere; no "(revision)", v8, E-low or CE-EVT-R in the main text (map kept in the supplement). |
| D7 structure | Done: 3.1–3.9 as specified, with Table 1 "inputs the user provides", the terminal line-spacing sentence, worked example in 3.4, one-paragraph analytic model in 3.5, 3.6 deployment/transfer check, 3.7 tolerance/ε, 3.8 assumptions (no results), 3.9 with Table 5 "question → experiment". Results 4.1–4.4 as specified; C1 split into validity / model accuracy / per-configuration paragraphs; Table 5 (B1–B3) and B6 moved to the supplement (Table S30, Appendix D.12) with a short summary in 4.2; Discussion has no repetition of 3.8 and a new 5.3 "Relation to practice"; one runtime statement (3.5, Table S21 and RV6). |
| D8 worked example | Done (Section 3.4) with the numbers of `worked_example.txt`. |
| D9 tables and figures | Done in the source: tables numbered by first appearance (1 inputs, 2 variants, 3 GNSS, 4 configurations, 5 questions, 6 A1, 7 B5, 8 C1, 9 cost) and the PDF numbering now matches; the nomenclature's hard-coded "Table 2" now points to the variants table. A `\ref` in the nomenclature needs a script change and was not made. Figure content (Figs. 1, 2, 3, 6) had already been regenerated in commit 5585aab. |
| D10 break-even wording | Done: abstract and highlight "roughly 40–90 times"; 4.4 gives 43/58/88 and 31–117; 5.2 and 5.5 use the same numbers; cost-optimal margin reaches 0.9 only at r of several hundred (R3 0.888, R1 0.495). |

## Associate editor

| Item | Status |
|---|---|
| Title | Done (D1). |
| Abstract: gloss of "conformal erosion" | Done (margin λ, overlap 2λ, line spacing). |
| Abstract: "every check" | Replaced (D5). |
| Abstract: "1.2–4.4 configuration-aware" | Done: "learned, empirical and per-configuration baselines". |
| Abstract: 4–55% with transfer check | Abstract keeps 4–55% "at the same nominal level" per D4; 4–59% in 4.1 and Conclusion. |
| Abstract: 30–100 | Replaced by "roughly 40–90" (D10). |
| Highlights 4 and 5 | Done ("miss level met"; "40–90 times overlap"). |
| Intro para 1: autonomous sentence up | Done (end of paragraph as suggested). |
| Intro para 2: cut citations | Done (one sentence per field). |
| Three-feature gap as list mapped to contributions | Done. |
| Contribution order (score first) | Done. |
| Contribution 3 rephrased as benefit | Done. |
| Fig. 1 data flow, box 4, XCE "no run data", k⋆ typography | Arrows and box 4 already fixed in the figure (commit 5585aab); XCE "no run data" and plain k are in the caption/text only, because figures were not to be edited. |
| Fig. 2 (c) λ_ref | Already fixed in the figure. Panel (b) label position and cropping: not done (figure edits not allowed). Caption λ value: not done, no result file gives the margin of that field. |
| M1 transfer check | Done (D3, D4). C1/T1: text states the check would have refused the RTK deployments; the overlap of the recalibration was not computed (no result file), and this is said. |
| M2 Section 3 structure | Done (D7). Results moved out of Section 3 (score check, layer validation, binding shares, plan-change numbers, timings). Five-step XCE-T and scale law moved to one paragraph + Appendix B. CE+ constants in Table 1 / Appendix C.5; CE-q named the core variant. Objective sentence on the oracle minimiser added. |
| M2 algorithm box | Partly: no algorithm environment exists in the build conventions; replaced by the four-step list (3.2), the CE four-item list (3.4), Tables 1–2 and the worked example. |
| M2 worked example | Done for CE-q. PAC rank and the XCE example were not added: the suggested XCE numbers are hypothetical and no result file gives them. |
| M2 inputs table, questions → experiments | Done (Tables 1 and 5). |
| M3 results order, model accuracy into no-history section with B6 | Done (4.2). |
| M3 5.1 shortened | Done (empirical findings only). |
| M3 relation to practice (overlap levels, section control, ISOBUS/terminal, ground truth) | Done (5.3). No literature on measured overlap levels was added (no source in the reference list). |
| M3 5.2 "few tenths in R1" | Fixed (0.8 pp). |
| M3 5.3 vs abstract numbers | Done (comparison named in each place). |
| M4 revision tags, internal names, "Pivot" header | Done ("Scale"). |
| M4 source comments | Not done: the build conventions require the `<!-- source -->` comments; the script strips them, so they do not reach the PDF. |
| M4 regret vs excess overlap | Done. |
| M4 Table 5 to supplement | Done (Table S30, Appendix D.12). |
| M4 Gaussian-extremes paragraph out of Section 2 | Done (cited once in 3.5; details in Appendix B). |
| M5 length | Done (see word counts). Fig. 4 (A1 bars) moved to the supplement as Fig. S4; B6 moved; C1 split; "Other stacks"/"practice rules" shortened. Table 3 (configurations) not merged into the GNSS table. |
| Minor 1 κ | Nomenclature points to 3.8; κ was not estimated (stated), so no range is given. |
| Minor 2 pp in abstract | Done ("percentage points"). |
| Minor 3 "on the same field" | Done. |
| Minor 4 pre-registration sentence | Done (own paragraph after the figure). |
| Minor 5 sections along the working direction | Done ("cross-sections ... spaced 1 m apart along the working direction"). |
| Minor 6 "(0.1 in all experiments)" | Done. |
| Minor 7 step 3 marginal/PAC | Done. |
| Minor 8 Table 2 "gated", "assumption-free" | Done. |
| Minor 9 relevant passes | Done. |
| Minor 10 double negative | Done. |
| Minor 11 CE as list | Done. |
| Minor 12 correlation sentence | Rewritten and moved to Appendix D.12 (the main text keeps the √2 argument). |
| Minor 13 validation numbers out of Section 3 | Done. |
| Minor 14 (1−ε)^{K1/K0} illustration | Done. |
| Minor 15 field selection criterion | Not done: the repository records only "after filtering" (docs/experiments_report.md), not the criterion; "after filtering" is now stated. |
| Minor 16 meet rate explanation | Done. |
| Minor 17 edge-term sentence to results | Done (4.2). |
| Minor 18 arithmetic | Done (√(0.039²−0.030²) ≈ 0.025). |
| Minor 19 timing duplicate | Done (3.5 only). |
| Minor 20 A1 lead with outcome | Done; criteria in the Table 6 caption. |
| Minor 21 "same plan" overstatement | Done. |
| Minor 22 "rests on no theorem" | Done. |
| Minor 23 bridge sentence | Done (opens 4.2). |
| Minor 24 B4 heading | Done. |
| Minor 25 bold rule | Done: one rule in Tables 7 and 8 (below 0.88 per configuration; at or below 0.895 overall); 0.842, 0.866, 0.853 and raw-pooling DGPS values now bold. |
| Minor 26 T3 numbers | Done (values with † footnote). |
| Minor 27 C2 first sentence | Done. |
| Minor 28 r definition first, r_be | Done. |
| Minor 29 enumerated conclusions | Done. |
| Minor 30 r ≈ 1.7 source | Labelled hypothetical. |
| Minor 31 field validation | "Outside the scope of this paper". |
| Minor 32 guidance order | Done (5.5 follows the algorithm). |
| Minor 33 "under the nominal simulator" | Done (Conclusion item 2, 5.1). |
| Minor 34 Fig. 3 caption | Done. |
| Minor 35 Fig. 5 (now Fig. 4) caption n per panel | Caption done; panel titles already state n. |
| Minor 36 Fig. 6 (now Fig. 5) r_be | Done. |
| §5 field demonstration; R2 25% explanation; target operations | Field demo not possible (no data). R2 explained in 5.3; high-r operations named in 4.4; the "states the miss probability of any margin" framing adopted (D2). |

## English editor

| Item | Status |
|---|---|
| 1 table numbering / nomenclature | Done by renumbering in source order (D9); `\ref` in the nomenclature not possible without a script change. |
| 2 transfer-check wording | Done, but following D3 (recalibrate on a larger reference plan), not the suggested "deploy the reference plan", which D3 forbids. |
| 3 transfer check general, own section | Done (3.6). |
| 4 theorem leftovers, "Pivot" | Done. |
| 5 "run score" in figures | Already fixed in the figures (commit 5585aab). |
| 6 certificate/certified | Done ("verification batch", "calibrated"). |
| 7 one name for (S) | Done as "coupling assumption" per D6 (not "transfer assumption (A1)"). |
| 8 r⋆ clash | Done (r_be; both in nomenclature). |
| 9 C1–C4 vs C1/C2 experiments | Done (H1–H4 in Table S30; P4.1–P4.4 now only in Table S27). |
| 10 "calibrated" vs "reference" plan | Done. |
| 11 bold rule | Done (see AE 25). |
| 12 regret/oracle names | Done ("excess overlap", "oracle margin"). |
| 13 direction error in 5.2 | Fixed ("4–55% less overlap than..."). |
| 14 break-even rounding | Done per D10 (40–90; 31–117). |
| 15 thresholds 9/22 vs 20 | Done (5.5 item 4). |
| 16 B6 in experiment list | Done (Table 5). |
| 17 scale law not a step | Done (scale law no longer in the main text). |
| 18 duplications | Done. |
| 19 code names, field indices | Done. |
| 20 Appendix naming and order | Done: "Appendix B. Model-scale details", B.4 renamed, D-subsections renumbered in order (D.7–D.11) plus D.12. "Table S19a" kept to avoid renumbering every supplementary table. |
| 21 shared steps | Done. |
| 22 B5 ranges | Done (sources named; Mondrian 12.2 pp on 26% of fields). |
| 23 0.844 introduced | Done; note: 0.844 is R1 marginal (Table S8, D.4), not R3 as the report says. |
| 24 coverage double meaning | Done with "miss-free rate" (D6) instead of "reliability". |
| 25 Section 2 verb | Done. |
| 26 CE algorithm | Done. |
| 27 CE+ sentence; "gated" | Done. |
| 28–29 XCE-T steps | Superseded by the one-paragraph description (D7); "estimated by Gaussian Monte Carlo". |
| 30 correlation sentence | Done (moved to Appendix D.12). |
| 31 second property | Done (with the statistics #9 validity notion). |
| 32 c_i, g, V_i | Done. |
| 33 "section" | Done ("cross-section"). |
| 34 marginal/PAC in Introduction | Done. |
| 35 "Both errors" | Done. |
| 36 "guarantee class" | Done. |
| 37 "zero-data" | Done ("cross-field"). |
| 38 results order | Done (D7). |
| 39 C1 paragraph split, log bias, margin curve | Done. |
| 40 "0.9 margin" | Done ("oracle margin"). |
| 41 statistical shorthand 4.1 | Done. |
| 42 A2 opening | Done. |
| 43 "within-field tail ratio" | Rewritten per statistics #5. |
| 44 title | D1 title used. |
| 45 abstract phrases | Done ("trailed implement" etc.; efficiency-advantage sentence moved to the Conclusion for length). |
| 46 citation separators in PDF | Not done: requires a change of the LaTeX preamble in the build script. |
| 47 highlight | Done (D10 wording). |
| 48 "(ours)" in Fig. 4 | Figure moved to the supplement (Fig. S4); the legend cannot be changed without editing the figure; the caption explains it. |
| 49 "Generate a reference plan" | Done. |
| 50 "without," | Done. |
| 51 "no more overlap"; active voice | Done. |
| 52 articles | Done. |
| 53 colloquial phrasing | Done. |
| 54 "percentage point" | Done. |
| 55 Gaussian tail sentence | Done. |
| 56 nomenclature entries | Done for c_i, ℓ, u, r⋆, n, q⋆, V_i, v⋆, t, σ(z), z, r_be, RTK, DGPS, PPK, CORS, MPC, CQR, RMS, XCE; "T" explained. q, L, B, CVaR not added (q is defined in place, L and B are local, CVaR appears once). XCE-T not renamed (figures use XCE-T). |
| 57 "(revision)" tags | Removed entirely (D6). |
| 58 minor wording | Done. |

## Statistics

| Item | Status |
|---|---|
| 1 "every check" | Done (D5 wording in abstract, highlights, 5.1, Conclusion). |
| 2 "same guarantee" | Done ("same nominal level"); the transfer-check rows and 4–59% address the R3 PAC fields. |
| 3 "fell short only when..." | Done (5.1, Conclusion item 3). |
| 4 CE+ bound | Done (Table 2, 3.8). |
| 5 "what no scale can remove" | Done (3.8 "Ideal scale"; 5.2 "at matched miss-free rate, post hoc, consistent with"). |
| 6 "assumption-free" | Done. |
| 7 Fig. 1 fallback | Done (D3). |
| 8 model accuracy and per-configuration | Done (abstract, 3.5, 5.1, Conclusion). |
| 9 minimality notion, ≤ | Done (3.3, contribution 1). |
| 10 virtual erosion reading | Done (3.3). |
| 11 standing conditions, main area | Done (3.3, 3.8, abstract "in the main area"). |
| 12 PAC needs i.i.d., 1−δ, exchangeability examples | Done (3.8); A.4 in the supplement now says i.i.d. for PAC. |
| 13 κ statements | Done (not estimated; linear-loop condition; the 0.901/0.890/0.920 check removed from the main text). |
| 14 data-dependent ε/τ | Done (3.7, 4.4, 5.5, Table 1). |
| 15 empirical per-configuration scale not covered | Done (3.5). |
| 16 edge upper bound under A3 | Done (3.5). |
| 17 q⋆ = S_(k⋆) | Done. |
| 18 Proposition 1 generality | Done ("typically", illustration). |
| 19 small fixes | Done (λ⋆_f "≥"; δ = 0.1 / confidence 0.9 in the Introduction; Beta "for i.i.d. fields"; 0.885–0.936; highlight "bound the chance"). |
| 20 Chinese wording | Not applicable to the English version. |
| 21 supplement front matter | Done (comment, "Names used" paragraph, A.17 "pivot" glossed). Title not changed: `md2elsarticle.py` extracts the supplement title with the pattern `**Certified...**`, so the new title would break the build; the "Names used" paragraph now gives the manuscript title. Changing the script's regex is needed to fix this. |
| Pointer table (A.9, A.10 pointers) | Done. |

## Practitioner (Chinese report; English counterparts applied)

| Item | Status |
|---|---|
| One-sentence summary; λ vs overlap vs line spacing; "one run = one complete operation" | Done (abstract, Introduction, nomenclature). |
| Score defined as "margin needed"; order statistic in plain words | Done (abstract, 3.3, 3.4 with "28th of 30"). |
| Model sentence | Done. |
| Abstract number load | Reduced. |
| Contributions without variant abbreviations; feature (2) plain | Done. |
| Output into the terminal | Done (Introduction, 3.2, 5.3, 5.5). |
| Ground truth in the method, implement vs tractor, pooling rules, loss of fix | Done (Table 1). Accuracy requirement given qualitatively ("much more accurate than the margin"); a numerical rule (1/5) has no source. |
| How many runs (table) | Done in text (A2 costs) and Table 1; "100 runs unrealistic" stated in 4.1. |
| λ_ref initial values | Done (17.5/19.4/43.4 cm; 1.10 and 1.25 rules). Why 1.10 and 1.25 were chosen is not documented; not added. |
| Probe line length/speed; XTE excludes GNSS error | XTE point done; length and speed are not documented in the repository; not added. |
| Curved lines, obstacles | Limitation 5. |
| 2w, "greedy", plain-language score, rule example, 3.8 user meaning | Done. |
| CE+ and XCE-T to the appendix | XCE-T done; CE+ shortened, constants in Appendix C.5 (kept in the main text as optional refinement because it is the registered method of A1). |
| Remove process information | Done. |
| Why margins are large; GNSS representativeness; terrain | Done (5.3, Table 3 caption). Margin decomposition and an RTK run without float/wrong fixes would need new simulations: not done. |
| T5 absolute margins and overlaps | Not done: `rv4_mismatch_edges45.txt` reports accuracy, miss-free rates and excess only. |
| Speed recalibration | Done (Table 1, 5.5). |
| Vendor rule naming and source | Defined as a representative practice rule, not a vendor prescription (Table 6 caption). |
| Farmer-tuned definition | Done (Table 6 caption: tuned with simulated ground truth). |
| τ = 2/5 cm miss-free rates for the vendor rule | Not done: no result file. |
| No manual patching | Done (5.3). |
| Vendor-rule values 1.75% vs 2.12% | Explained (Table 9 caption). |
| Time/machine cost; agronomic overlap loss; non-linear miss loss | Discussed qualitatively in 4.4. |
| Footprint scope (seeding, spinner spreaders); boom example | Done (3.7). |
| Splitting paragraphs, C1, B1–B3, farmer-tuned sentence, 5.1 repetition, abstract/5.2 consistency, guidance to front, Conclusion (3) | Done. |

## Self-read

| Item | Status |
|---|---|
| 1 CE abbreviation in 3.2 | English already fine. |
| 2 step headings | Done ("Coverage score of a run (step 2)", etc.; steps 1–4 all covered: 3.2, 3.3, 3.4/3.5, 3.6). |
| 3 XCE-T one paragraph | Done. |
| 4 "no theorem" | Done. |
| 5 long A2 sentence | Done. |
| 6 inputs list | Done (Table 1). |

## Chinese editor (content errors that also existed in English)

| Item | Status |
|---|---|
| A1 "<" vs "≤" | Fixed (contribution 1, 3.3). |
| A2 direction in 5.2 | Fixed. |
| A3 Conclusion "calibrated" → reference margin | Fixed. |
| A4 abstract subject of "held" | Fixed (efficiency vs guarantee separated). |
| A5 table order | Fixed (D9). |
| A6 B5 predictions | Listed in 4.2. |
| A7 "per-operation" → per-configuration | Fixed. |
| A8, A9 "no assumption" | Fixed. |
| A10 Monte Carlo "exact" | Fixed. |
| A11 "less tight" | Rephrased ("decides how tight the margins are"). |
| A12 "only scale" | Qualified ("under the nominal simulator"). |
| C2–C3, C5, C9, C10 | Fixed (forward references, "zero-data", "gated", "cells", "margin curve", 0.844, thresholds, break-even comparison). |

## Other corrections found during the revision

- The previous C1 text said the deployed RTK margin exceeded the reference margin on "91–100% of fields"; no result file contains this figure. It now says "on most fields", as in the Table S27 caption.
- The B2 value 0.844 belongs to R1 marginal (Table S8, D.4), not R3.

## Supplement changes

- Front matter: comment, contents, "Names used" paragraph (miss-free rate, excess overlap, verification batch, calibrated, coupling assumption, H1–H4, manuscript title).
- A.4 PAC i.i.d.; A.17 "pivot" glossed; B and B.4 headings; pointers to manuscript Sections/Tables updated (3.8, 4.2, Tables 7–8, Proposition 4).
- D-subsections renumbered in order (D.7–D.11); Table S20 gains the round-2 transfer-check row and source.
- New D.12 "Material moved from the manuscript": Table S30 (B1–B3, claims H1–H4) with its paragraph, the B6 paragraph, the correlation sentence on field-edge terms, and Fig. S4 (A1 excess-overlap bars, formerly Fig. 4).
- Not changed: supplement title (build-script constraint, see Statistics 21); Table S19a numbering.

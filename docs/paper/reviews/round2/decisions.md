# Round 2: decisions for the revision

Reports: `associate_editor.md`, `en_editor.md`, `practitioner.md`, `statistics.md`, `zh_editor.md`, `self_read.md`.
All concrete items in these reports are to be applied unless they conflict with a decision below or would change a result.
No result may change except where a new analysis below says so. Every number must come from a file in `results/`.

## D1 Title
"Calibrating pass overlap from logged runs to bound the probability of missed strips in agricultural field coverage" (AE).
Chinese: "基于作业记录校准行间重叠量以控制农田全覆盖作业的漏作业概率".

## D2 Storyline (practitioner, statistics)
The method sets the margin for a chosen miss level and, equally, states the miss probability of any margin the user picks
(including a tolerance τ). Abstract, introduction and conclusion say both. The guarantee is a bound under stated assumptions
(exchangeable runs or fields), shown in simulation; no "guaranteed", no "assumption-free" without "distribution-free, given
exchangeable runs". Chinese: never "无需假设/完全不依赖假设"; use "不需要对误差分布作假设（只要求各次作业可交换）".

## D3 Transfer check: one definition everywhere
If the calibrated margin exceeds the reference margin, the calibrated margin is not deployed; the field is re-calibrated on a
reference plan with a larger margin (CE: new pilot batch with λ_ref raised), or, for XCE, the reference plans are re-planned
with a larger margin and the model scale recomputed. It applies to CE-q, CE+ and XCE. It never means "deploy the reference
plan anyway". Fig. 1 text: "transfer check: if λ̂ > λ_ref, recalibrate on a larger reference plan". Remove "(revision)".

## D4 Transfer check results (new analysis, `results/revision/rv8_transfer_check.txt`, post hoc, descriptive)
Field-level reading: fields whose mean deployed CE+ margin exceeds λ_ref use the CE result of the same field (conservative,
the operation-level check would fall back on fewer operations). R1, R2: no field affected. R3 marginal: 9/30 fields,
pooled P 0.901, overlap 16.06%, regret +0.78 pp, reduction 22.2% vs CPrP and 33.7% vs UBCP. R3 PAC: 19/30 fields, P 0.921,
overlap 17.40%, regret +2.12 pp, reduction 32.8% and 59.2%. Add rows "CE+ with transfer check" for R3 in Table 4 (the
registered result stays). Headline range: "4–55% (registered; 4–59% with the transfer check)".
Abstract: "4–55% less overlap than two conformal planners at the same nominal level" (not "same guarantee").

## D5 Validity claims (statistics #1, #3)
Replace "held its target in every check" with what is true: the target was met in the confirmatory checks of the final
methods (A1 with the transfer check, A2, B4, B5, C2); single calibration draws can fall below (B2 0.844, B3 0.877), which
B4 shows are draws of the calibration data; it failed when passes were coupled (follow-previous-pass guidance, 0.850) and
when the deployed margin exceeded the reference margin (C1 wet patches, 0.891–0.895).
Per-configuration coverage is not guaranteed; say "observed 0.885–0.936 per configuration" not "covered every configuration".
CE+ guarantee: as stated in Appendix A.9 (bound on P(S_new > tσ(z_new) − Δ̄)), not κε; Table 2 row accordingly.
"What no scale can remove": an identity for the ideal scale, not a lower bound; raw pooling beat the ideal scale in one cell.
Edge exceedance: an upper bound (product of single-pass probabilities) under assumption A3 (Appendix A.10).
Gaussian Monte Carlo "estimates", not "computes exactly".
Choosing ε or τ after looking at the calibration scores voids the marginal guarantee: choose them first (practical guidance).

## D6 Terms (one name each; also inside figures)
- probability of a run without missed strip: "miss-free rate" (EN), "无漏作业率" (ZH). "coverage" only for area.
- "coupling assumption" everywhere (drop "transfer assumption"); keep the label (S) only in Appendix A, call it
  "the coupling assumption" in the main text.
- break-even cost ratio: r_be (not r*). r* stays the covering radius.
- registered claims of Table 5: H1–H4 (not C1–C4).
- "certified/certificate" → "calibrated" (EN), "具有概率保证的" (ZH) – including Table 8, Fig. 6 legend.
- "regret" → "excess overlap" everywhere (Fig. 4 axis already says overlap above oracle).
- ZH: 实验 (not 试验) for experiments, 标称 (not 名义), 重叠率 for J, 重叠量 for 2λ, 联合界 (not 并集界),
  "wet patches" = 局部湿软区, "farmer-tuned margin" = 农户经验裕量 (tuned once on 5 training fields).
- Remove "(revision)", "修订阶段", repository names (v8, E-low, CE-EVT-R) from the main text; the supplement keeps the map.

## D7 Structure (AE, practitioner)
Section 3: 3.1 Problem; 3.2 Method overview (four steps, Fig. 1) + Table 1 "inputs the user provides" (planner that accepts a
margin; logged runs with the true implement track from an independent reference such as a PPK rover on the implement; n ≥ 9
or 22; ε, δ, τ chosen before calibration; for XCE: controller settings, terrain model, GNSS grade per field) and the line
"set the line spacing in the guidance terminal to w − 2λ̂"; 3.3 Coverage score (step 2); 3.4 Calibration with field history
(step 3a) incl. the worked example; 3.5 Calibration without field history (step 3b) – the analytic model in ONE paragraph,
its five steps moved to Appendix B; 3.6 Deployment and transfer check (step 4); 3.7 Gap tolerance and choice of ε;
3.8 Assumptions behind the guarantee (short list; no results in it); 3.9 Simulation study (data, simulator, configurations,
metrics, experiments as a table "question → experiment").
Results 4.1 Fields with history (A1, A2); 4.2 Fields without history (model accuracy, B1–B4 summary in 3 sentences with
Table S, B5); 4.3 Robustness (C1 split into validity / model accuracy / per-configuration paragraphs; C2); 4.4 Cost.
Table 5 (B1–B3 history) and the B6 paragraph go to the supplement (two-sentence summary stays).
Discussion: no repetition of 3.8; add a short paragraph on practice: why margins are larger than field experience
(zero-miss event over a whole field; CORS series with 16% float epochs and wrong fixes, which terminals would flag) and that
the vendor rule's misses were 0.12–0.64% of the area.
Results contain no runtimes that contradict 3.x: one runtime statement (Section 3.5) with the values of Table S21 and RV6.

## D8 Worked example (`results/revision/worked_example.txt`)
R1 field 440, w = 3 m, reference margin 17.5 cm, n = 29 logged runs, k* = 27. Scores 4.5–16.5 cm (median 7.0 cm); the
27th smallest is 9.4 cm, so the margin is 9.4 cm, line spacing 281.1 cm, overlap 6.97%. The field's own 0.9 margin is
10.7 cm (overlap 7.58%). This particular set of 29 runs gives a miss-free rate of 0.745 on test runs; over 2000 redraws of
29 runs the mean is 0.890 (10th–90th percentile 0.811–0.963): the bound holds on average over the logged runs, which is why
the PAC rule exists.

## D9 Tables and figures
Number tables in order of first appearance in the source too (method/inputs tables first). The nomenclature refers to
tables by \ref in LaTeX. Fig. 1 arrows from the two calibration-data boxes go into step 2. Fig. 2(c) uses λ_ref. Figs. 2/3
say "coverage score". Fig. 6 legend "Calibrated, ε = 0.1".

## D10 Break-even wording
Nominal-curve means: r_be ≈ 43 (R1), 58 (R2), 88 (R3) (Table 8); with the per-operation A1 results 31–117. The cost-optimal
margin itself reaches a 0.9 miss-free rate only for r of several hundred (R3: 0.888 at r = 300; R1: 0.495). Abstract: "only when
a missed area cost roughly 40–90 times an over-applied one". Practical guidance uses the same numbers.

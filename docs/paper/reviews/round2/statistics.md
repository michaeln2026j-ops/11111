# Round 2 review: statistical guarantees after the plain-language rewrite

Scope: `manuscript.md` (abstract, highlights, Sections 1, 3.2–3.7, 4.2–4.5, 5.1–5.5, 6), `manuscript_zh.md` (same places) and `supplementary.md` Appendix A. Files were read only.

**Summary.** The Appendix A pointers are correct. A.1, A.3, A.4, A.6, A.12, A.15, A.17, A.19 and A.20 each point to the intended result. The problems are in what the plain-language text says those results guarantee. Eight issues are high severity:

- Several summary claims ("held its target in every check", "at the same guarantee", "fell short only when ...", "at or above target whenever ...") are contradicted by the paper's own results.
- CE+ is said to have the κ-guarantee, but A.9 gives it a different bound.
- "What no scale can remove" contradicts A.20.
- "Assumption-free" is used for results that need exchangeability.
- The Fig. 1 fallback is not covered by any guarantee.
- "Model accuracy does not affect the guarantee" is true only for the field-averaged guarantee on the score.

In the Chinese version the same errors appear, and three places are stronger than the English (摘要 "均达到覆盖要求", 5.1 "完全不依赖假设", 5.1 "均满足要求").

Severity: **H** = wrong or contradicted by the paper's own results or appendix; **M** = a condition is missing or the claim is stronger than the theorem; **L** = imprecise wording or a consistency problem.

---

## High

### 1. (H) "Held its target miss probability in every check" is false
**Location:** Abstract ("the method held its target miss probability in every check under the nominal simulator"); Highlights ("Simulation: target held"); zh 摘要 ("该方法在每项检验中均达到目标漏作业概率"), 亮点 ("仿真中达到目标水平").

**Problem:** Under the nominal simulator, several checks did not meet their target:

- B1 failed its registered validity tests (S D.3: R1 and R2 marginal "NO"; R3 PAC 31 failures).
- B2 realised 0.844.
- B3 realised 0.877, below its registered 0.89.
- CE+ with follow-previous-pass guidance in R2 reached P 0.850 with a meet rate of 0.70 (Section 4.2, "Other stacks").

B4 explains B2 and B3 as draws of the calibration data. It does not explain B1, which was a scale/implementation failure, or the follow-previous-pass case, which violates (S). "Every check" therefore overclaims.

**Corrected (EN):** "In a pre-registered simulation study ..., the coverage guarantee was confirmed when both the calibration fields and their logged runs were resampled (all 26 cells of the pre-registered check) and in the target-field experiments, provided that the deployed plan had no more passes than the calibrated one. It failed when guidance coupled successive passes."

**Corrected (ZH):** "……预注册仿真表明：在同时重抽校准田块及其作业记录的检验中（全部 26 个单元）以及目标田块实验中，只要实施规划的行程数不多于校准所用规划，保证均得到验证；当导航方式使相邻行程相互耦合时，保证不成立。"

Highlights: "Simulation: guarantee confirmed by resampling; 4–55% less overlap than conformal planners at the same nominal level" / "仿真：重抽样检验验证了保证；在相同名义水平下重叠量比共形规划少 4%～55%".

### 2. (H) "4–55% less overlap ... at the same guarantee" is not a like-for-like guarantee comparison
**Location:** Abstract; Conclusion item 1 ("at the same guarantee level"); Section 5.2; zh 摘要 ("相同保证水平下"), 结论（1）.

**Problem:**

- The upper end, 54.7%, comes from R3 PAC. There the deployed CE+ margin exceeded λ_ref on 19 of 30 fields, and Section 4.2 itself says that "on those fields the guarantee rests on no theorem".
- The comparators calibrate on the nominal plan. By Prop. 1 (A.6), they have no guarantee on the plan they deploy.
- Pooled UBCP loses its finite-sample guarantee (S C.3).

The methods share a nominal level (ε, δ), not a guarantee.

**Corrected (EN):** "With 100 logged runs per field it used 4–55% less overlap than two conformal planners calibrated at the same nominal level (ε = δ = 0.1). In the DGPS configuration the larger reductions include fields on which the deployed margin exceeded the reference margin, where no theorem applies."

**Corrected (ZH):** "每块田有 100 次作业记录时，在相同名义水平（ε = δ = 0.1）下，其重叠量比 2 种共形规划方法少 4%～55%；DGPS 配置中较大的降幅包含实施裕量超过基准裕量、无定理支撑的田块。"

### 3. (H) "The guarantee fell short only when the deployed margin exceeded the calibrated one" and "at or above the target whenever ..." are contradicted by the results
**Location:** Conclusion item 3; Section 5.1 (iii); zh 结论（3）, 5.1（iii）.

**Problem:**

1. The follow-previous-pass stack (Section 4.2) under-covered (0.850) because (S) was violated, not because the deployed margin exceeded λ_ref.
2. The measured coverage was *not* always "at or above the target". A2 marginal reached 0.896 and B5 0.896. C2 reached 0.897 and its PAC fraction 0.885. These values are consistent with the target within resampling error, which is a different statement.
3. "Calibrated one" should be "reference margin". The calibrated margin λ̂ is the deployed margin.

**Corrected (EN), Section 5.1 (iii):** "Deploying a plan with fewer passes than the reference plan (CE-q, CE+, XCE) needs the transfer assumption (S) and inflates the miss level by up to a factor κ. When the deployed margin stayed below the reference margin and passes were guided independently, the measured coverage was consistent with the target (marginal means 0.896–0.943; Experiments A2, B4, B5, C2). Coverage fell below the target in two cases: when the deployed margin exceeded the reference margin (0.891–0.895, wet-patch variant of C1), which the transfer check prevents, and when guidance coupled passes and violated (S) (0.850, follow-previous-pass in R2), which no check in the method detects."

**Corrected (EN), Conclusion 3:** "The guarantee itself fell short when the deployed margin exceeded the reference margin, which the transfer check excludes, and when follow-previous-pass guidance violated the transfer assumption."

**Corrected (ZH), 5.1（iii）:** "……实施裕量低于基准裕量且各行程独立导航时，实测覆盖率与目标值相符（边际均值 0.896～0.943；试验 A2、B4、B5 和 C2）；以下两种情形覆盖率低于目标：实施裕量超过基准裕量（C1 湿陷区变体 0.891～0.895，推广检查可避免）；导航方式耦合各行程而违背 (S)（R2 跟随上一行程导航 0.850，本方法中没有检查能发现）。"

**Corrected (ZH), 结论（3）:** "可靠性保证本身仅在两种情形下未能满足：实施裕量超过基准裕量（推广检查可排除），以及跟随上一行程导航违背推广假设。"

### 4. (H) CE+ is given the κε guarantee, but Appendix A.9 gives it a different bound
**Location:** Table 2, CE+ row ("as CE-q"); Section 3.7 bullet "CE-q, CE+ and XCE ... inflated by at most a factor κ"; Section 5.1 (iii); zh 表 2 ("同 CE-q"), 3.7.

**Problem:** A.9 states that the deployed CE+ plan π(tσ(z_new)) is random through z_new, which is correlated with the test run's condition. For CE+ the bound is therefore P(S_new > tσ(z_new) − Δ̄), *not* κε, because κ is defined through the marginal F_{π0}. The split-conformal step holds for S/σ(z), and the transfer is pathwise, but the clean "factor κ" statement does not apply. The constant-σ case, where CE+ = CE-q, is the exception.

**Corrected (EN), Table 2 CE+ cell:** "score guarantee on S/σ(z) given exchangeable runs; for the deployed plan, P(S_new > tσ(z_new) − Δ̄) under (S) (Appendix A.9); requires tσ(z) ≤ λ_ref"

**Corrected (EN), Section 3.7:** "... The miss level is then inflated by at most a factor κ for CE-q and XCE. For CE+ with a non-constant normaliser, the deployed margin depends on the probe-line reading of the same run, and the bound is P(S_new > tσ(z_new) − Δ̄) rather than κε (Appendix A.9)."

**Corrected (ZH):** "……对 CE-q 和 XCE，漏作业水平至多放大 κ 倍；对采用非常数归一化系数的 CE+，实施裕量依赖同一次作业的探测线读数，界为 P(S_new > tσ(z_new) − Δ̄)，而非 κε（附录 A.9）。" 表 2 CE+："归一化分数 S/σ(z) 的保证要求作业可交换；实施规划在 (S) 下满足 P(S_new > tσ(z_new) − Δ̄)（附录 A.9）；要求 tσ(z) ≤ λ_ref".

### 5. (H) "What no scale can remove" contradicts Appendix A.20
**Location:** Section 3.7, last bullet; Section 5.3 ("including the ideal one, ... because the remaining inflation is set by run-to-run randomness"); zh 3.7 "任何尺度都无法消除的部分", 5.3.

**Problem:** A.20 states in bold: "This is an identity for the ideal pivot, **not a lower bound over all pivots**". It adds that in R3 PAC raw pooling was cheaper than the ideal scale (+10.36 vs +12.86 pp, a difference of 2.5 pp, not "a few tenths"). The bullet title and "no scale can remove" assert the lower bound that the appendix disclaims. In addition:

- the inflation depends on n, the rank k⋆ (marginal *or* PAC) and the within-field score distribution H, not on "n and the PAC rule" alone;
- "within a few tenths of a point" holds only *at matched coverage* (B2 post hoc; S D.9 "0.08–0.42 pp").

The causal "this is why" is a post hoc interpretation (S D.3 exploratory).

**Corrected (EN):** "**Inflation under an ideal scale.** Even with an ideal scale (each field's own requirement), the margin of a new field is its requirement multiplied by an order statistic of within-field tail ratios, whose distribution is set by n, the rank k⋆ and the within-field score distribution (Appendix A.20). This is an identity for the ideal scale, not a lower bound for every scale: in one cell raw pooling was cheaper than the ideal scale. It is consistent with the post hoc finding that, at matched coverage, all field-level scales within one machine configuration lay within 0.1–0.4 pp of each other (Section 4.3)."

**Corrected (ZH):** "**理想尺度下的裕量放大。** 即使采用理想尺度（各田块自身所需裕量），新田块的裕量也等于其所需裕量乘以田块内尾部比值的某一次序统计量，其分布由 n、秩 k⋆ 和田块内分数分布决定（附录 A.20）。这是理想尺度下的恒等式，并非对所有尺度成立的下界：在一个单元中，直接合并比理想尺度更省。这与事后分析结果一致：在相同覆盖率下，同一机型配置内各田块级尺度相差 0.1～0.4 pp（第 4.3 节）。" Section 5.3 should likewise add "at matched coverage (post hoc)" and drop "because ...", or replace it with "consistent with Appendix A.20".

### 6. (H) "Assumption-free" is used for results that require exchangeability
**Location:** Table 2 (CE: "assumption-free (Appendix A.4)"; XCE: "score guarantee assumption-free"); Section 4.2 ("the assumption-free CE", twice); Section 5.1 (ii) ("only CE deploys that plan itself and is assumption-free"; the same sentence first says "given exchangeable runs"); zh 表 2 "无需假设", 4.2 "无需假设的 CE", 5.1 "因而完全不依赖假设". The Chinese wording ("does not depend on any assumption at all") is even stronger than the English.

**Problem:** A.4 and A.17 require exchangeable runs or fields (and i.i.d. for PAC). For XCE, exchangeability *of fields* is a strong, untestable assumption: Section 4.3 says B4 "cannot detect a failure of exchangeability", and Section 5.4 lists it as limitation 4. What is assumption-free is the score's exactness (Lemma 1 / Theorem 1), and that holds only under the standing footprint and grid conditions F1–F2. "Assumption-free" is accurate only in the sense "no assumption on the error distribution".

**Corrected (EN), Table 2:** CE: "distribution-free; needs exchangeable runs only (Appendix A.4)". XCE: "score guarantee distribution-free given exchangeable fields (A.17); plan via (S)".

**Corrected (EN), Section 5.1 (ii):** "... is distribution-free given exchangeable runs (target-field calibration) or exchangeable fields (cross-field calibration); only CE deploys that plan itself and so needs no further assumption." In Section 4.2, replace "assumption-free CE" with "CE, which needs no transfer assumption".

**Corrected (ZH):** 表 2 CE "无需分布假设，仅要求作业可交换（附录 A.4）"；XCE "在田块可交换的前提下，覆盖分数的保证无需分布假设（A.17）；实施规划依赖 (S)"；5.1 "……其中只有 CE 直接实施基准规划本身，因而不需要额外的推广假设"；4.2 "退回无需推广假设的 CE".

### 7. (H) The Fig. 1 caption describes a fallback that no guarantee covers
**Location:** Fig. 1 caption ("The transfer check falls back to the reference plan when the calibrated margin exceeds the reference margin"); zh 图 1 ("推广检查将退回到基准规划").

**Problem:** If λ̂ > λ_ref, the calibration itself says that the reference plan's margin λ_ref is *smaller* than needed: P(S > λ_ref) may well exceed ε. Deploying π(λ_ref) is therefore not covered and is anti-conservative. Section 3.2 says "refuses", and Sections 3.4 and 5.5 say "refuse ... or fall back to CE". CE requires *new* pilot and certificate runs on the target field at a larger λ_ref, so XCE fields without history have no fallback at all.

**Corrected (EN):** "The transfer check refuses the deployment when the calibrated margin exceeds the reference margin; with target-field runs, CE can then recalibrate on a reference plan with a larger margin."

**Corrected (ZH):** "若校准所得裕量超过基准规划裕量，推广检查将拒绝实施；有目标田块作业记录时，可改用 CE 在裕量更大的基准规划上重新校准。"

### 8. (H) "The model's accuracy does not affect the guarantee" and "covering every machine configuration" overreach
**Location:** Abstract ("whose accuracy does not affect the guarantee"; "covering every machine configuration"); Section 1, contribution 2 ("so the guarantee does not depend on the model's accuracy"); Section 3.5 ("If it is inaccurate, the margins become less tight but the guarantee is unaffected"); Section 5.1 ("The extreme-value model and the Monte Carlo twin affect only efficiency"); zh 摘要 ("模型精度不影响保证"; "且各机型配置均达到覆盖要求"), 贡献（2）, 3.5, 5.1 ("各机型配置均满足要求（0.89～0.94）").

**Problem:** A.17 makes model accuracy irrelevant only for the guarantee on the *score at the reference plan, averaged over fields and over the calibration draw*. The model does affect three things:

- (a) how coverage is distributed across fields and configurations: raw pooling covered DGPS at 0.779, and the model scale under mismatch at 0.78–0.85 (C1);
- (b) how often the transfer check refuses (λ̂_g = q̂_g v⋆ versus λ_ref);
- (c) efficiency.

Per-configuration coverage is not guaranteed; Table 6 itself says so. The model scale reached 0.885–0.936, not "every configuration covered". The Chinese abstract's "均达到覆盖要求" ("all met the coverage requirement") is stronger still. Section 5.1 says in one sentence that the model affects only efficiency, and in the next that the model scale is what achieves per-configuration coverage.

**Corrected (EN), Abstract:** "..., put on a common scale by a vehicle–terrain–GNSS model (analytic, or a Monte Carlo digital twin). The model's accuracy does not affect the guarantee averaged over fields, only how tight the margins are and how evenly coverage is spread across fields." Later in the abstract: "... against 1.2–4.4 for configuration-aware baselines, and kept the coverage of each machine configuration between 0.885 and 0.936 under the nominal simulator, which the guarantee alone does not ensure."

**Corrected (EN), Section 5.1:** "The extreme-value model and the Monte Carlo twin do not affect the field-averaged guarantee; they affect efficiency, how often the transfer check refuses, and how coverage is distributed across configurations."

**Corrected (ZH), 摘要:** "……归一到统一尺度；模型精度不影响对田块平均的保证，只影响裕量的紧致程度以及覆盖率在各田块间的分布。……而考虑机型配置的基线方法高 1.2～4.4 个百分点；在标称仿真模型下，各机型配置的覆盖率为 0.885～0.936（这一点并非保证本身所能确保）。"

**Corrected (ZH), 5.1:** "极值模型和蒙特卡洛数字孪生不影响对田块平均的保证，但影响效率、推广检查的拒绝频率以及覆盖率在各机型配置间的分布。……采用模型尺度后，标称仿真下各机型配置的覆盖率为 0.885～0.936。"

---

## Medium

### 9. (M) The minimality of the score is stated with the wrong validity notion, and "as tight as the data allow" overclaims
**Location:** Section 3.3 ("the smallest score that never declares a run with a missed strip miss-free"); Section 1, contribution 3 ("A coverage score that makes the calibration exact"; "score is below the planned margin"; "so the calibrated margin is as tight as the data allow"); zh 3.3 ("在从不把存在漏作业带的作业判定为无漏作业的分数中，它是最小的"), 贡献（3）("使校准精确成立", "小于规划裕量", "在数据允许的范围内最紧").

**Problem:**

1. In A.3 a score is *valid* if S′(e) ≤ t ⇒ M_ref(t,e) = 0 for **every** virtual erosion t. The plain-language version checks only the planned margin. Under that one-threshold reading, the indicator score (0 if miss-free, +∞ otherwise) is valid and smaller than S⋆ on miss-free runs, so the claim as stated is false.
2. Corollary A1 compares *the same order-statistic rule at the same rank* applied to different valid scores. It does not say that no other procedure (other ranks, normalisation, or pooling) could give a smaller margin. Hence "as tight as the data allow" is too strong.
3. Miss-free holds iff S ≤ λ_ref, not S < λ_ref.
4. The score is exact; the calibration is not "exact".

**Corrected (EN), Section 3.3:** "Second, among all scores that certify complete coverage at every margin (every virtual widening or narrowing of the executed footprints), it is the smallest; so an order-statistic rule of a given rank deploys no more passes with this score than with any other such score, including ..."

**Corrected (EN), contribution 3:** "**An exact coverage score** (Section 3.3). ... A run leaves no strip unworked if and only if its score is at most the planned margin, and no other score that certifies complete coverage at every margin is smaller, so the same calibration rule applied to any other such score yields a margin at least as large."

**Corrected (ZH):** "第二，在对任意裕量（即实际作业带任意虚拟加宽或收窄）都能判定完全覆盖的分数中，它是最小的；因此对给定秩的次序统计量规则……" 贡献（3）："**精确的覆盖分数**……当且仅当其覆盖分数不大于规划裕量时，一次作业不留漏作业带；在对任意裕量都能判定完全覆盖的分数中没有比它更小的，因此把同一校准规则用于任何其他此类分数，所得裕量都不会更小。"

### 10. (M) "The margin that the executed run would have needed" mixes up virtual erosion with re-planning
**Location:** Section 3.3 ("It is the margin that the executed run would have needed to leave no strip unworked"); zh ("该次实际作业要不留任何漏作业带所需的裕量").

**Problem:** A.3 defines S as the *virtual* erosion of the executed reference plan. The plan is not changed. A.3 explicitly says that reading it as the needed margin of another plan "is the transfer step of A.7 and A.15". The plain sentence invites exactly that reading, which is how the CE-q, CE+ and XCE guarantees end up sounding assumption-free.

**Corrected (EN):** "It measures, on the plan actually driven, how far every executed footprint could be narrowed (S < λ_ref) or would have to be widened (S > λ_ref) before a strip is missed; the run is miss-free if and only if S ≤ λ_ref. Interpreting S as the margin needed by a different plan requires the transfer assumption of Section 3.7."

**Corrected (ZH):** "覆盖分数衡量的是：在实际行驶的规划上，各实际作业带可同时收窄多少（S < λ_ref），或须同时加宽多少（S > λ_ref），才会出现漏作业。一次作业无漏作业，当且仅当 S ≤ λ_ref。将 S 理解为另一规划所需的裕量，需要第 3.7 节的推广假设。"

### 11. (M) "With no assumption" omits the standing conditions, the main-area scope and the ground-truth requirement
**Location:** Section 3.3 ("it decides complete coverage exactly, with no assumption on the error process"); Section 5.1 (i) ("with no assumption"); Abstract and Section 1 ("probability of any missed strip"); zh 3.3, 5.1（i）, 摘要.

**Problem:** Exactness holds under the standing assumptions F1 (rigid interval footprint of width w perpendicular to the working direction, with heading and hitch offsets absorbed into the reference point) and F2 (1 m section grid; narrower strips are not certified). It also holds only for the main area W; the headland is not certified. The score needs the *true* implement position (limitation 2). "No assumption on the error process" is correct; "no assumption" in Section 5.1 is not.

**Corrected (EN), Section 5.1 (i):** "The coverage score is exact and the smallest valid score whatever the error process, for interval footprints evaluated on the 1 m section grid of the main area (Appendix A, F1–F2), provided that the implement position is measured with independent ground truth." Abstract: "... so that the probability of a run with any missed strip in the main area stays at most a chosen level".

**Corrected (ZH):** "（i）对于在作业主区 1 m 截面网格上评估的区间作业带（附录 A，F1–F2），无论误差过程如何，覆盖分数都是精确的，且是最小的有效分数；前提是农机具位置有独立真值。" 摘要："……使一次作业在作业主区内出现任何漏作业带的概率不超过给定水平".

### 12. (M) The PAC rule needs i.i.d. runs; the paraphrase of exchangeability is loose; the CE conditional statement is missing 1−δ
**Location:** Section 3.7, CE bullet ("If the logged runs and the new run of the field are exchangeable (drawn from the same conditions in random order), the marginal rule gives ... and the PAC rule bounds the miss probability given deployment"); zh 3.7 ("可交换（即在相同条件下产生、顺序随机）"; "PAC 规则则对给出实施规划条件下的漏作业概率给出上界"). (A.4 also says "under exchangeability" for both rules. A.17 correctly says "i.i.d. for the PAC statement".)

**Problem:** Training-conditional (PAC) validity (Vovk, 2012) needs i.i.d. scores, not just exchangeable ones. The PAC bound holds only on an event of probability at least 1−δ over the calibration data, and the CE text drops that qualifier. "Drawn from the same conditions in random order" reads like a sampling procedure. A reader needs the conditions that would *break* exchangeability: seasonal trends, receiver or firmware changes, and runs that share a GNSS day.

**Corrected (EN):** "If the logged runs and the new run are exchangeable (for the PAC rule, independent and identically distributed); for example, the new run comes from the same mix of seasons, soil states and GNSS conditions as the logged ones, with no trend or equipment change in between. The marginal rule then gives P(deploy and miss) ≤ ε, averaged over the calibration data. The PAC rule gives, with probability at least 1−δ over the calibration data, a miss probability of at most ε given deployment."

**Corrected (ZH):** "若该田块的作业记录与新一次作业可交换（PAC 规则要求独立同分布），例如新一次作业与历史作业来自相同的季节、土壤状态和 GNSS 条件组合，其间没有趋势变化或设备更换：则边际规则在对校准数据取平均的意义下保证 P(给出裕量且漏作业) ≤ ε；PAC 规则以不低于 1−δ 的概率（对校准数据而言）保证给出实施规划条件下的漏作业概率不超过 ε。"

Fix A.4 to "under exchangeability (marginal) or i.i.d. runs (PAC)".

### 13. (M) The κ statements are not supported as written
**Location:** Section 3.7 ("factor κ, which is close to 1 on flat fields; (S) holds exactly for a linear closed loop"; the development numbers cited as support); zh 3.7 (same).

**Problem:**

1. κ is never estimated or reported, and Appendix A contains no numerical support for "close to 1 on flat fields". The A.15 mean-shift bound includes a GNSS timing term, bounded only through the modulus of continuity of the error series, and that term does not vanish on flat fields.
2. In A.15 the condition is "d_j(x;C) ≤ Δ(C) ≤ Δ̄". The shift may depend on the operating condition (which includes the GNSS trajectory) but must be uniformly bounded. A linear loop satisfies (S) exactly only when both plans see the same noise at matched positions. Re-timing the passes shifts which part of the GNSS series each pass reads, so the "exactly" applies only to the deterministic part.
3. The figures 0.901/0.890/0.920 against 0.899/0.885/0.922 test the analytic model's prediction of coverage after a plan change (Table S5, layer 4). They do not test (S) or the κ bound.

The abstract's "stays below a chosen level" also hides that, for all variants except CE, the deployed-plan bound is κε with κ unknown.

**Corrected (EN):** "The miss level is then inflated by at most a factor κ, which depends on how much a plan change can shift each gap and edge term (Appendix A.15). κ was not estimated here; it is small when terrain and timing effects of the plan change are small. (S) holds for a linear closed loop when the deterministic part of the response is the only part that changes with the plan, and only approximately once re-timing shifts the GNSS error each pass reads. In development checks, the analytic model predicted coverage after a plan change to within 0.005 (0.901, 0.890, 0.920 against simulated 0.899, 0.885, 0.922; Table S5)."

**Corrected (ZH):** "此时漏作业水平至多放大 κ 倍，κ 取决于规划改变对各漏缝项和边界项的最大偏移（附录 A.15）；本文未估计 κ，当规划改变带来的地形和时序影响较小时，κ 较小。对线性闭环系统，若随规划改变的只是响应的确定性部分，(S) 成立；若行程时序改变导致各行程读取的 GNSS 误差不同，(S) 仅近似成立。开发阶段检验中，解析模型对规划改变后覆盖率的预测误差在 0.005 以内（……；表 S5）。"

### 14. (M) "The same data bound P(S > λ) for every λ" ignores data-dependent choice of ε, τ or λ
**Location:** Section 4.5 ("the calibration then still states the miss probability of a cheaper margin (the same data bound P(S>λ) for every λ), and ε and τ can be chosen by cost"); Section 5.3 ("which the same calibration supports"); Section 5.5, first bullet; Conclusion item 4 ("the same calibration states its miss probability"); zh 4.5, 5.3, 5.5, 结论（4）.

**Problem:** The conformal statement P(S_new > S_(k)) ≤ 1 − k/(n+1) holds for a rank fixed in advance. If ε, τ or λ is chosen after seeing the scores (for example by minimising the empirical expected cost), the marginal guarantee no longer applies to the chosen value. A bound that holds simultaneously for all λ needs a uniform band, for example DKW or a Bonferroni/Simes correction over a grid. The bound also refers to the reference plan, and a margin λ < λ_ref deployed as π(λ) inherits it only through (S)/κ.

**Corrected (EN):** "... the calibration then states the miss probability of a cheaper margin, provided ε (or τ) is fixed before the calibration scores are examined; choosing it by cost from the same scores requires a bound that holds simultaneously for all margins (for example a DKW band)."

**Corrected (ZH):** "……只要在查看校准分数之前确定 ε（或 τ），校准结果即可给出较小裕量的漏作业概率；若依据同一组分数按成本选取，则需要对所有裕量同时成立的界（如 DKW 置信带）。"

### 15. (M) Some compared scales are not covered by A.17, yet validity is stated for all of them
**Location:** Section 3.5 ("Any scale computed from field properties alone gives a valid method of the same form; the evaluation compares ... an empirical per-configuration scale"); Table 6 caption and Section 4.3 ("Overall validity held for every non-refusing scale"); zh 3.5, 表 6.

**Problem:** S C.6 defines the empirical per-configuration scale as "the median of the single-run scores of those [calibration] fields". It is a function of the calibration data, not of field properties, so A.17 does not cover it. Its measured validity is empirical, not a theorem. Similarly, CE+'s σ(z) depends on the run (A.9, not A.17). The text should say which rows have a theorem behind them.

**Corrected (EN), Section 3.5 add:** "The empirical per-configuration scale, the median of the calibration fields' own scores, is estimated from the calibration data and is therefore not covered by this argument; its validity is only checked empirically."

**Corrected (ZH):** "按机型配置的经验尺度取校准田块自身分数的中位数，由校准数据估计，因而不在上述论证范围内，其有效性仅经过实证检验。"

### 16. (M) The edge-term description states an upper bound as an equality and omits A3
**Location:** Section 3.5, step 2 ("A field edge is missed only if every pass that covers it has receded, so its exceedance is a product of single-pass probabilities (Appendix A.12)"); step 3 ("Given the condition, non-adjacent pairs are independent"); zh steps 2–3 ("因此边界超限概率为各单行程概率之积").

**Problem:** A.12 gives an *inclusion*: passes outside 𝒦_b can rescue the edge. The product is therefore an upper bound, valid given C and under the additional assumption A3 (pass-start state reset or contained in C; A.10). Sections covered by two passes are combined across x by a union bound. The same A3 assumption is needed for "non-adjacent pairs are independent". "Computed exactly by Gaussian Monte Carlo" means exact up to Monte Carlo error.

**Corrected (EN):** "A field edge can be missed only if every pass planned to cover it has receded, so, given the condition and with the state at the start of each pass treated as known (Appendix A.10), its exceedance is bounded above by the product of single-pass probabilities (Appendix A.12)."

**Corrected (ZH):** "只有计划覆盖该边界的所有行程都向内偏离时才可能漏作业，因此在给定作业条件且将各行程起始状态视为已知的前提下（附录 A.10），边界超限概率不超过各单行程概率之积（附录 A.12）。"

---

## Low

### 17. (L) The CE certificate quantile must be the conformal order statistic
**Location:** Section 3.4, CE paragraph.

**Problem:** The pilot step uses the empirical (1−ε) quantile q. The text then names q⋆ "the certificate quantile" without saying that it is S_(k⋆), the conformal or PAC rank. The A.4 bound P(S_new > q⋆) ≤ ε holds only for that rank.

**Corrected (EN):** "... deploys π(λ_ref) itself if the conformal order statistic q⋆ = S_(k⋆) of the certificate batch (marginal or PAC rank) satisfies q⋆ ≤ λ_ref." The Chinese text needs the same change ("保证批次分数的共形次序统计量 q⋆ = S_(k⋆)").

### 18. (L) Proposition 1 and the "stochastically larger" claim are stated too generally
**Location:** Section 3.7, second bullet.

**Problem:** In A.6, "(1−ε)^{K1/K0}" is approximate (≈), and it is a counterexample under i.i.d. pair scores. "A plan with more passes has a stochastically larger score" is not shown in general; it follows under the i.i.d. counterexample or under a coupling.

**Corrected (EN):** "... typically has a stochastically larger score. A threshold calibrated on the nominal plan π(0) has no distribution-free guarantee on a plan with more passes: if pair scores are i.i.d., its coverage is about (1−ε)^{K1/K0} < 1−ε (Appendix A.6)."

**Corrected (ZH):** "……覆盖分数通常在随机序意义下更大……若行程对分数独立同分布，该阈值的覆盖率约为 (1−ε)^{K1/K0} < 1−ε（附录 A.6）。"

### 19. (L) Small wording and number fixes
- **Nomenclature λ⋆_f:** "the smallest margin with P(no miss) = 1−ε" should be "≥ 1−ε" (zh likewise).
- **Section 1** ("needs at least 9 (marginal) or 22 (PAC) logged runs"): add "(with δ = 0.1)".
- **Section 3.7, XCE bullet:** "the mean coverage on new fields is one draw of Beta(k⋆, n+1−k⋆)" is exact for i.i.d. fields with continuous scores; under mere exchangeability it is a mixture. Add "(for i.i.d. fields)".
- **Section 5.1** "(0.89–0.94)": Table 6 gives 0.885–0.936. Use the unrounded range, because 0.885 rounds up across the 0.89 line used as a criterion elsewhere. zh: "（0.885～0.936）".
- **Highlights** "occur with a chosen probability": should be "at most a chosen probability" / "不超过给定概率".

### 20. (L) The Chinese version reads stronger than the English in three places
- **4.2 and 5.2,** "CE+ 则恰好达到目标覆盖率" / "CE+ 恰好达到目标覆盖率": "恰好" means "exactly". The English says "reaches/reached its target". Use "CE+ 达到目标覆盖率".
- **摘要** "且各机型配置均达到覆盖要求" and **5.1** "各机型配置均满足要求" / "完全不依赖假设": see items 6 and 8.
- **贡献（3）** "小于规划裕量": see item 9 ("不大于").

### 21. (L) The supplement's front matter is stale
**Location:** `supplementary.md` front-matter comment, the "Names used" paragraph and the title.

**Problem:**

- The comment says "Theorem, proposition and figure numbers refer to the manuscript". The "Names used" paragraph says "Theorem and proposition numbers in this supplement follow the manuscript". The manuscript no longer numbers theorems; Appendix A now defines them.
- The supplement title ("Certified Coverage Planning under Execution Uncertainty: ...") differs from the manuscript title.
- A.17 still says "pivot" where the main text says "scale".

**Corrected:** "Theorem and proposition numbers are defined in Appendix A; the manuscript refers to them by item (A.1, A.3, ...)". Also use the manuscript title.

---

## Pointer check (main text to Appendix A)

| Main-text pointer | Intended content | Supplement item | Status |
|---|---|---|---|
| 3.3 "proofs in Appendix A.1 and A.3" | exactness; minimality, corollary | A.1 Lemma 1; A.3 Theorem 1, Corollary A1 | correct (but see item 9 on the validity notion) |
| 3.3 "6 fields × 200 runs (Appendix A.3)" | numerical check | A.3 "Numerical check" | correct |
| 3.5 step 2, 4.1 "Appendix A.12" | field-edge terms | A.12 Theorem A2(b) | correct (see item 16: upper bound, needs A3) |
| 3.7 CE "Appendix A.4" | CE guarantee | A.4 | correct (A.4 should say i.i.d. for PAC; item 12) |
| 3.7 "Appendix A.6" | nominal-plan calibration does not transfer | A.6 Proposition 1 | correct |
| 3.7 "Table S5; Appendix A.15" | transfer under (S), κ | A.15 Theorem 2 (numbers in B.2 Table S5) | correct target; the numbers test the model, not (S) (item 13) |
| 3.7 XCE "Appendix A.17" | cross-field validity | A.17 Proposition 3 | correct |
| 3.7 "Appendix A.20" | inflation under ideal scale | A.20 Proposition 4 | correct target; the main text contradicts it (item 5) |
| 3.8 meet rate "Appendix A.19" | per-field criteria 85% / 99% | A.19 (14.5% / 1.2% failure) | correct |
| (missing) CE+ guarantee | training-only gating; CE+ bound | A.9 Proposition A2 | **add a pointer to A.9** in Table 2 and Section 3.7 (item 4) |
| (missing) Gaussianity / A3 | conditional Gaussianity, extra assumption | A.10 Proposition A3 | add to Section 3.5, steps 1–3 (item 16) |

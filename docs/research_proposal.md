# 研究方案：执行不确定下的可认证覆盖规划

**Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Decision-Dependent Calibration**

> 版本：v0.1（2026-10）｜ 状态：问题建模 + 定理草案 + 合成数据验证完成；理论证明细节、高保真仿真和实地数据待完成。

---

## 0. 一句话概括

覆盖路径规划（耕、播、喷、施、割草、清扫、测绘）默认机器能**完美执行**规划路径，而实际执行误差会造成漏作业和重叠。本文把"在执行误差下保证覆盖质量"抽象为一个**约束作用于随机集测度、分布未知且依赖决策的机会约束优化问题**，提出**共形腐蚀（Conformal Erosion）**：用共形预测校准执行误差，再对机具作用范围做 Minkowski 腐蚀，把概率约束精确转化为确定性的几何规划问题。由此得到**与分布无关、有限样本成立的覆盖证书**，并处理"规划改变误差分布"的决策依赖性。

## 1. 命名与定位

| 层次 | 名称 |
|---|---|
| 问题 | **执行不确定下的可认证覆盖规划问题**（Certified Coverage Planning under Execution Uncertainty, CCP-EU） |
| 方法 | **共形腐蚀**（Conformal Erosion） |
| 理论产出 | **覆盖证书**（Coverage Certificate）：零漏证书 / 漏作业风险证书 |
| 关键技术点 | 行间误差分数（pass-to-pass score）、计划一致支配校准、决策依赖的不动点校准 |

**学科交叉**：覆盖路径规划 × 共形预测 / 共形风险控制 × 机会约束优化 × 数学形态学（Minkowski 腐蚀）× 鲁棒控制（管道 MPC）。

## 2. 研究背景（大背景 → 科学问题）

1. **全球问题**：2023 年全球农业农药用量 373 万吨有效成分（FAO）；氮肥利用率仅 40%–46%（Nature 2015；Nature Food）；重型农机碾压造成最高 50% 的减产。
2. **直接原因**：田间实测显示喷药机平均重叠约 15.7%，其中约 2/3 来自行驶偏离预定线（爱沙尼亚 17 块田、4 年 GNSS 实测）。
3. **趋势放大问题**：农机加速无人化（自动驾驶拖拉机市场 2025 年约 27 亿美元，年增长约 19%），原本由驾驶员经验弥补的执行偏差失去了兜底。
4. **科学问题**：现有覆盖规划假设执行完美，跟踪控制与规划目标脱节。**在执行误差分布未知、相关、且随规划变化的条件下，能否给覆盖质量提供可证明的保证？**

（数据来源见 §10。引言中"减少重叠 → 节省投入品"的推算必须以本文实验数据为准。）

## 3. 问题建模

### 3.1 一般形式

- 作业区域 $W\subset\mathbb R^2$ 为紧集，机具作用范围为 $F\subset\mathbb R^2$。
- 规划 $\pi$ 给出参考路径 $\gamma_\pi$，执行路径为 $x=\gamma_\pi\boxplus e$。误差过程 $e\sim\mathcal D(\pi)$，**其分布未知且依赖于 $\pi$**。
- 实际覆盖区域是随机集 $C(\pi,e)=\bigcup_s \big(x(s)\oplus R(\theta(s))F\big)$。
- 漏作业比例 $M(\pi,e)=\mu(W\setminus C)/\mu(W)$。

$$
\textbf{(P)}\quad \min_{\pi\in\Pi} J(\pi)\quad \text{s.t.}\quad
\underbrace{\Pr_{e\sim\mathcal D(\pi)}\big[M(\pi,e)=0\big]\ge 1-\varepsilon}_{\text{零漏证书}}
\quad\text{或}\quad
\underbrace{\mathbb E_{e\sim\mathcal D(\pi)}\big[M(\pi,e)\big]\le\alpha}_{\text{漏作业风险证书}}
$$

其中 $J$ 是重叠测度（$\int_W(\text{覆盖重数}-1)_+$）、作业行数或路径长度。

**三个难点**：
1. 约束作用于**随机集的测度**，而不是标量。
2. $\mathcal D$ **未知**，且沿路径**时间相关**。
3. $\mathcal D$ **依赖决策** $\pi$。

### 3.2 结构化情形：往返式平行作业行（本文主线）

经过 Boustrophedon 分解后，每个单元是一个矩形 $[0,L]\times[0,S]$。设机具幅宽为 $w$，第 $k$ 行的中心为 $y_k$。在参考线的 Frenet 坐标下，第 $k$ 行的横向误差为 $e_k(s)$。在弧长 $s$ 处，覆盖区间为

$$I_k(s)=[\,y_k+e_k(s)-w/2,\; y_k+e_k(s)+w/2\,].$$

**假设**：
- **A1（小误差 / Frenet 图 / 保序）**：$|e_k(s)|<w/2$，执行路径可以表示为参考线上的图，误差定义良好；并且 $|e_{k+1}(s)-e_k(s)|<y_{k+1}-y_k$，即相邻行执行后不交换次序。
- **A2（条件不变性）**：给定行特征 $\phi_k$（该行的地形、坡度、行驶方向、速度），$e_k$ 的条件分布与规划无关。规划只通过改变 $\phi$ 的分布来影响误差，因此**决策依赖可以化为协变量偏移**。
- **A3（可交换性）**：校准作业与测试作业可交换（例如 i.i.d. 作业）。
- **A4（行序平稳）**：在 A2 下，行误差序列 $(e_k)$ 关于 $k$ 平稳。

## 4. 主要结果（定理草案）

### 引理 1（行间间隙刻画）
对于腐蚀参数 $\lambda$ 和每行尺度 $\hat\sigma_k$，取有效半幅宽 $h_k=w/2-\lambda\hat\sigma_k$，并按贪心方式布行：$y_{k+1}-h_{k+1}=y_k+h_k$。在 A1 下，弧长 $s$ 处无漏作业，**当且仅当**

$$e_{k+1}(s)-e_k(s)\le\lambda(\hat\sigma_k+\hat\sigma_{k+1})\ \ \forall k,\qquad e_1(s)\le\lambda\hat\sigma_1,\qquad -e_N(s)\le\lambda\hat\sigma_N.$$

（若末行被夹紧到边界，上式变为充分条件。）

**含义**：造成漏作业的是**相邻行的相对误差**，不是绝对误差。场内相关的共同误差（坡度漂移、GNSS 偏差）不会造成漏作业。这正对应行业中的"行间精度"指标（pass-to-pass accuracy），也是本文分数设计的出发点。仿真已经证实：用绝对误差设计分数会导致自适应方法失效（见 §7）。

### 定理 1（零漏证书：共形腐蚀）
定义每次作业的行间分数

$$S=\sup_s\max\Big\{\max_k\frac{e_{k+1}(s)-e_k(s)}{\hat\sigma_k+\hat\sigma_{k+1}},\ \frac{e_1(s)}{\hat\sigma_1},\ \frac{-e_N(s)}{\hat\sigma_N}\Big\}.$$

设校准作业的分数为 $S_1,\dots,S_n$，取 $q$ 为第 $\lceil (n+1)(1-\varepsilon)\rceil$ 小的分数。在 A1–A3 下，按 $\lambda=q$ 规划时

$$1-\varepsilon\ \le\ \Pr[M=0]\ \le\ 1-\varepsilon+\tfrac{1}{n+1}\quad(\text{上界在分数无结时成立}).$$

**证明要点**：由引理 1，$\{M=0\}\supseteq\{S_{n+1}\le q\}$；再用 split conformal 的分位数引理即可。

### 定理 2（计划一致的支配性证书：处理行数的决策依赖）
腐蚀量 $\lambda$ 改变作业行数 $N(\lambda)$，而 $S$ 是对行对取最大值，所以测试分数的分布随决策变化，标准的可交换性被破坏。

**做法**：校准时用一个参考计划，行数 $N_{\mathrm{ref}}\ge\sup_{\lambda\in\Lambda}N(\lambda)$。在 A2、A4 下，任意 $\lambda\in\Lambda$ 的测试分数在随机序意义上被参考分数支配：$S^{(N(\lambda))}\preceq_{st}S^{(N_{\rm ref})}$，因为对子集取最大值不大于对全集取最大值。因此

$$\Pr[M(\pi_\lambda,e)=0]\ge1-\varepsilon\qquad\text{对 }\lambda\ge q\text{ 一致成立}.$$

即**一次校准，对整个计划族同时有效**。

### 定理 3（地形异质：协变量偏移下的加权证书与不动点校准）
地形不均匀时，规划决定各行落在哪里，从而改变特征分布（决策依赖）。

- 改用**行对级**分数 $T_j$，配合 Tibshirani 等（2019）的加权共形预测。权重为似然比 $\frac{dP^{\pi}_\phi}{dP^{\rm cal}_\phi}$，其中**分子由计划和地形图精确确定，无需估计**。
- 对 $N(\lambda)+1$ 个约束做并集界，**不需要行间独立**。
- 定义映射 $\mathcal T(\lambda)=q^{\rm w}_{1-\varepsilon/(N(\lambda)+1)}$。可以证明 $\mathcal T$ 单调不减，且 $\lambda^\star=\inf\{\lambda:\mathcal T(\lambda)\le\lambda\}$ 存在（可行时），在 $\lambda^\star$ 处 $\Pr[M>0]\le\varepsilon$。

**待解决**：校准行对之间存在作业内相关性，严格证明要么每次作业只抽一个行对，要么引用非可交换共形预测的覆盖间隙界（Barber 等，2023）。

### 定理 4（漏作业风险证书：共形风险控制）
取代理损失

$$\bar\ell(\lambda)=\frac1{LS}\int_0^S\sum_{k<N_{\rm ref}}\big(e_{k+1}-e_k-\lambda(\hat\sigma_k+\hat\sigma_{k+1})\big)_+ds\ +\ \text{边界项}.$$

它满足两点：（i）$\bar\ell\ge M$，因为有序区间并集的间隙不大于相邻间隙之和；（ii）$\bar\ell$ 关于 $\lambda$ **逐样本单调不增**。

于是可以套用共形风险控制（Angelopoulos 等，2022）：取 $\hat\lambda=\inf\{\lambda:\frac{n}{n+1}\hat R_n(\lambda)+\frac{B}{n+1}\le\alpha\}$，则 $\mathbb E[M]\le\mathbb E[\bar\ell(\hat\lambda)]\le\alpha$。

**注意**：真实损失 $M$ 在行数跳变时不单调，必须用代理损失 $\bar\ell$，这是一个技术贡献点。

**推论（与控制的耦合）**：管道 MPC 把误差约束在鲁棒不变集 $\mathcal E$ 内，从而给出 $\bar\ell\le B(\mathcal E)\ll1$，显著收紧 $B/(n+1)$ 项。仿真显示 $B=1$ 时风险证书偏保守（§7），这正是控制端可以介入的地方。

### 命题 5（贪心布行最优）
若 $y\mapsto y\pm h(y)$ 严格递增（$|h'|<1$），则"每次延伸到最远"的贪心布行在所有满足引理 1 条件的布行中**作业行数最少**。证明用区间覆盖问题的标准交换论证。

## 5. 算法框架

```
离线：  采集 n 次作业的误差轨迹 → 拟合尺度模型 σ̂(φ)（独立数据）
        → 计算行间分数 → 定理 1/2：分位数 q；或定理 3：不动点 λ*；或定理 4：λ̂
在线：  地形图 + σ̂ → 有效半幅宽 h_k = w/2 − λσ̂_k → 贪心布行（命题 5）
        → 管道 MPC 跟踪（保证 A1 和有界损失 B）
        → 可选：自适应共形预测（ACI）在线更新 λ，应对季节和土壤湿度漂移
```

## 6. 创新点（写给审稿人）

1. **新问题**：首次把覆盖路径规划的作业质量表述为"随机集测度上的分布无关机会约束"，并区分零漏证书与风险证书两类保证。
2. **新方法（共形腐蚀）**：把共形预测与 Minkowski 腐蚀结合，概率约束精确转化为确定性几何规划，不需要误差分布假设，保证在有限样本下成立。
3. **理论**：
   - 行间分数刻画（引理 1）；
   - 计划一致的支配性证书，处理行数的决策依赖（定理 2）；
   - 协变量偏移的加权证书和不动点校准（定理 3）；
   - 基于单调代理损失的风险控制（定理 4）；
   - 贪心最优性（命题 5）。
4. **规划与控制耦合**：管道 MPC 为证书提供假设条件并收紧界，把"规划不知道控制误差"的断层在数学上接起来。
5. **普适性**：方法适用于一切覆盖类任务（农业作业、割草、清扫、光伏清洗、无人机或水下测绘航带）。

## 7. 初步验证（合成数据，`sim/conformal_erosion_sim.py`）

**设置**：60 m × 100 m 田块，幅宽 3 m。误差 = 场内共同成分（ρ=0.5）+ 每行独立成分；坡地带（y≈40 m）的误差尺度是平地的 5 倍；每次作业有对数正态的工况因子（土壤湿度等）。$n_{\rm cal}=400$，$n_{\rm test}=1000$，3 个随机种子。

| 方法 | 作业行数 | 指标 | 实测（3 个种子） | 目标 |
|---|---|---|---|---|
| 不腐蚀（现状） | 20 | 漏作业比例 | 1.7%，P(有漏)=1.00 | — |
| 定理 1，均匀 $\hat\sigma$ | 30 | P(无漏) | 0.922 / 0.919 / 0.911 | ≥ 0.90 |
| 定理 1+3，地形自适应 $\hat\sigma$ | **26** | P(无漏) | 0.910 / 0.901 / 0.894 | ≥ 0.90 |
| 定理 4，均匀 | 25 | E[漏作业比例] | 0.0004 / 0.0004 / 0.0005 | ≤ 0.003 |
| 定理 4，地形自适应 | **23** | E[漏作业比例] | 0.0004 / 0.0004 / 0.0005 | ≤ 0.003 |

**结论**：
- 零漏证书成立且很紧：自适应版的均值约 0.902，理论区间为 [0.90, 0.9025]；0.894 在 1000 次测试的标准误差（约 0.01）内。
- 在保证相同的前提下，地形自适应比均匀腐蚀少用 **13%**（零漏）/ **8%**（风险）的作业行。
- 风险证书在 $B=1$ 时偏保守，这推动了定理 4 推论中的控制耦合。
- **建模教训**：第一版仿真只有场内共同误差，此时自适应方法反而更差。原因是漏作业由行间相对误差决定，这直接推动了引理 1 的分数设计。

*以上是合成数据的完整性检验，不是论文结果。论文需要高保真仿真和真实数据（§8）。*

## 8. 实验设计（论文版）

1. **校准性实验**：在 ε 和 α 的网格上，画经验覆盖率与目标的对比曲线；做 $n_{\rm cal}$ 敏感性分析。
2. **高保真仿真**：Project Chrono（SCM 地面力学）或 Gazebo + 拖拉机/机具模型，DEM 坡地地形，土壤湿度扰动。控制器对比纯跟踪、MPC、管道 MPC。
3. **真实数据**（决定能否上一区）：RTK 农机或机器人的作业轨迹日志，至少涵盖平地和坡地两类田块、多个工况。如果没有实车，可以先用小型移动机器人在草地或坡地做缩比实验。
4. **基线方法**：
   - 固定重叠量（行业常用 10–30 cm）；
   - 高斯机会约束（假设误差服从正态）；
   - 鲁棒最坏情况（按最大误差腐蚀）；
   - GP / 贝叶斯不确定性（未校准）；
   - 本文的均匀版与自适应版。
5. **指标**：P(无漏)、E[漏作业比例]、重叠率、作业行数、路径长度、等效投入品节省、计算时间。
6. **分布偏移实验**：跨田块、跨季节；加权版与 ACI 在线版的对比。
7. **泛化实验**：割草机器人或无人机测绘航带，证明方法普适。

## 9. 投稿策略与一区可行性（客观评估）

**首选期刊**：
- **IEEE Transactions on Automation Science and Engineering（TASE）**：看重"理论 + 自动化应用"，农业自动化在其收稿范围内。
- **Computers and Electronics in Agriculture（CEA）**：农业工程主流期刊，偏应用。

**冲刺期刊**：IEEE T-RO / RA-L（需要实地实验）。

（各刊最新 JCR / 中科院分区请投稿前核实。）

**为什么具备一区潜力**：
- 问题是新的：检索中未发现用共形预测为覆盖规划给保证的工作，也未发现决策依赖下的共形机会约束。
- 有定理，而不只是"改进算法 + 仿真对比"。
- 有清晰的定量收益（同保证下更少重叠）。
- 和热点（共形预测、可认证 AI）以及大问题（农业减量、无人化）都有连接。

**一区的硬门槛（必须做到）**：
1. 定理 1、2、4 的严格证明（工作量可控）；定理 3 至少给出并集界版本。
2. 至少一组真实或高保真数据，并与 4 类以上基线公平对比。
3. 动笔前在 Web of Science 和 Google Scholar 复核新颖性（"conformal" × "coverage path planning" / "swath" / "pass-to-pass"；"decision-dependent" × "conformal"），中文文献也要查。

**不能保证的事**：没有任何选题能保证录用。录用取决于证明的严谨性、实验的说服力和写作质量。

## 10. 参考文献（核心）

- FAO, *Pesticides use and trade 1990–2023*. https://www.fao.org/statistics/highlights-archive/highlights-detail/pesticides-use-and-trade-1990-2023/en
- Zhang X. et al., Managing nitrogen for sustainable development, *Nature* 2015（Princeton 新闻稿）. https://cpree.princeton.edu/news/2018/save-earth-better-nitrogen-use-hungrier-planet-must-be-addressed
- 氮利用率指数（Nature Food）. https://eos.org/articles/index-suggests-that-half-of-nitrogen-applied-to-crops-is-lost
- 农机重叠田间实测（爱沙尼亚生命科学大学）. https://agronomy.emu.ee/tag/gps/
- Höffmann et al., Coverage path planning review, *J. Field Robotics* 2024. https://onlinelibrary.wiley.com/doi/full/10.1002/rob.22286
- Mier et al., Continuous-curvature headland coverage, *J. Field Robotics* 2025. https://onlinelibrary.wiley.com/doi/full/10.1002/rob.22489
- Fields2Cover. https://ar5iv.labs.arxiv.org/html/2210.07838
- Tibshirani R. et al., Conformal prediction under covariate shift, *NeurIPS* 2019.
- Angelopoulos A. et al., Conformal risk control, 2022；Learn then Test, 2021.
- Barber R. F. et al., Conformal prediction beyond exchangeability, *Ann. Statist.* 2023.
- Zhao Y. et al., Conformal Predictive Programming for chance-constrained optimization, 2024. https://arxiv.org/pdf/2402.07407
- Lindemann L. et al., Safe planning in dynamic environments using conformal prediction, *IEEE RA-L* 2023.
- Sun J. et al., PlanCP（Stanford MSL）. https://msl.stanford.edu/papers/sun_conformal_2023.pdf
- Feedback-based conformal prediction for trajectory optimization, NeurIPS 2025. https://arxiv.org/html/2510.16376
- 自动驾驶拖拉机市场（GMI）. https://www.gminsights.com/industry-analysis/autonomous-tractors-market

（Barber 2023、Tibshirani 2019、Angelopoulos 2021/2022 来自作者已知文献，引用前请核对卷期页码。）

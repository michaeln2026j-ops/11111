# 中文稿写作规范（第三版，按《农业工程学报》《农业机械学报》体例）

中文稿要读起来像国内农业工程期刊上的论文，而不是译文，更不能有"AI 腔"。内容（数字、公式、结论、限定条件）与英文稿一致；表达、结构、格式按中文期刊习惯。

## 一、篇章结构（中文期刊体例，与英文稿不同）

- 题目 → 摘要 → 关键词 → `## 0 引言` → `## 1 材料与方法` → `## 2 结果与分析` → `## 3 讨论` → `## 4 结论` → `## 数据可用性`。
- 不设"研究亮点"，不设"符号与缩写"表：符号在首次出现处定义，公式后用"式中"逐一说明（含单位）。
- 引言包含国内外研究现状（英文稿第 2 节的内容并入引言），最后一段写本文做了什么、"以期为……提供参考"。不写"本文的贡献如下"。
- 小标题用二级、三级编号：`### 1.1 问题描述`、`#### 1.4.1 ……`（源文件中写 `##`/`###`/`####` 加编号和空格，不加句点）。

## 二、句式与用词

**应当这样写（期刊常用表达）**
- 摘要："针对……问题，提出了一种……方法。该方法……。……结果表明：……。该研究可为……提供参考。"
- 文献综述："国内外学者在……方面开展了大量研究。XX 等[]……；YY 等[]……。上述研究……，但……。"（外国作者写姓 + "等"，如"Lindemann 等 (Lindemann et al., 2023)"——见三、2）
- 方法："首先……；然后……；最后……。""其计算方法为"；公式后"式中：$w$ 为作业幅宽，m；$\lambda$ 为裕量，m。"
- 结果："由表 4 可知，……。""如图 3 所示，……。""与……相比，……降低了……。""这是由于……。"
- 讨论："……的原因可能是……。""本研究尚存在以下不足：……。"
- 结论用"1）……。2）……。"编号，每条一段，结论性陈述加关键数字。
- 用"该方法""本研究""该研究"，少用"本文提出的方法"反复出现。

**禁止（AI 腔与翻译腔）**
- 段首粗体小标签（如"**数据来源。**""**CE。**""**推广检查。**"）。需要分段落讨论时改用三级小标题或自然段首句。
- 正文中的项目符号列表（结论和局限性用 1）2）编号段落，其余一律写成连贯段落）。
- "不是……而是……""值得注意的是""需要指出的是""换言之""这意味着""从而""进而"连用、"既……又……"排比、三连排比。
- 冒号引出一串分号并列；一句话里套多层括号；括号里再写英文缩写和数字。
- 英文括注：只在首次出现的核心术语后括注一次英文（共形预测（conformal prediction）），其余一律不加。
- 引号强调术语（“收缩”“覆盖”）；破折号只用于题目或"即"的解释，全文不超过 3 处。
- "本文的贡献""主线""落地""赋能""闭环"等口语或时髦词。
- 每段都以"因此""由此可见"收尾的套路。

## 三、格式

1. 数字与汉字之间、英文与汉字之间不加空格（"100 次"写"100次"，"GNSS 误差"写"GNSS误差"）；数字与单位之间加一个空格（3 m、0.05 s、2 m/s），百分号紧跟数字。
2. 引用一律写成括号形式，由排版程序转成上标编号：并列引用 `(Galceran and Carreras, 2013; Höffmann et al., 2024)`；叙述性引用写作者姓 + "等" 再接括号：`Lindemann 等 (Lindemann et al., 2023)`，两位作者写 `Takasu 和 Yasuda (Takasu and Yasuda, 2009)`。括号内必须是英文原样。
3. 图表："图 1""表 3"（源文件中写空格，排版后由程序处理），表题在表上方 `*表 3　……*`，图题在图下方 `**图 3**　……`。
4. 数值范围用"~"写成"4%~55%""1.2~4.4"，从小到大；"个百分点"不缩写成 pp（表格表头可用 pp 并在表注说明）。
5. 公式：显示公式写 `$$...$$`，排版时自动编号；文中引用"式（1）"。
6. 标点用全角；引号用“”；不用半角括号括中文。

## 四、术语表

| 英文 | 中文 |
|---|---|
| pass | 作业行（相邻作业行、最外侧作业行） |
| line spacing | 作业行距 |
| implement width $w$ | 作业幅宽 |
| overlap (2λ) / overlap ratio $J$ | 重叠量 / 重叠率 |
| margin $\lambda$ | 裕量 |
| missed strip / miss | 漏作业带 / 漏作业 |
| run, logged run / operation | 一次作业；作业记录 |
| miss-free rate | 无漏作业率 |
| coverage score $S$ | 覆盖分数 |
| covering radius | 覆盖半径 |
| conformal prediction | 共形预测 |
| conformal erosion | 共形收缩法 |
| calibration, calibrate | 校准 |
| reference plan / reference margin | 基准规划 / 基准裕量 |
| deployed plan / margin | 实施规划 / 实施裕量 |
| coupling assumption | 耦合假设 |
| transfer check | 推广检查 |
| marginal rule / PAC rule | 边际规则 / PAC规则 |
| model scale | 模型尺度 |
| cross-field calibration | 跨田块校准 |
| exchangeable | 可交换 |
| oracle margin | 理想裕量 |
| excess overlap | 超额重叠率 |
| meet rate | 达标率 |
| headland / main area | 地头 / 作业主区 |
| field edge, edge terms | 田块边界，边界项 |
| headland lap | 地头绕行 |
| mixed fleet / machine configuration | 混合机队 / 机型配置 |
| Monte Carlo twin | 蒙特卡洛数字孪生 |
| analytic (extreme-value) model | 解析极值模型 |
| vendor rule / farmer-tuned margin | 厂商经验规则 / 农户经验裕量 |
| cost ratio $r$ / break-even $r_\mathrm{be}$ | 成本比 / 盈亏平衡成本比 |
| gap tolerance $\tau$ | 漏缝容许宽度 |
| wet patches / trailed implement / levelled terrain | 局部湿软区 / 牵引式农机具 / 平整地形 |
| experiment (simulation) | 仿真试验 |
| pre-registered | 预注册 |
| guidance terminal | 导航终端 |
| cross-track error (XTE) | 横向偏差 |

方法缩写（CE、CE-q、CE+、XCE-T、XCE-MC、CPrP、UBCP、CQR、Mondrian、RTK、DGPS、GNSS、LQR-I、BCD、PPK）和试验编号（A1、A2、B1~B5、C1、C2、R1~R3、T1~T6）保留。

禁止用词：无需假设、完全不依赖、保证达到、恰好、覆盖率（指概率时）、名义、块田块。

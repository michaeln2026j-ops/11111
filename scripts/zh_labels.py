"""Chinese text for the paper figures (used by make_paper_figures.py with PAPER_LANG=zh).

EXACT maps a whole text object; PHRASES are applied in order to the non-math parts of any other text.
"""
EXACT = {
    # Fig. schematic
    "$2\\lambda_\\mathrm{ref}$ overlap": "重叠量$2\\lambda_\\mathrm{ref}$",
    "Along-pass position (m)": "沿作业方向位置/m",
    "Lateral position (m)": "横向位置/m",
    "Coverage score of the run:\n$r^\\star$ = largest half-gap or edge distance\n"
    "$S=\\lambda_\\mathrm{ref}+\\max_x\\,(r^\\star(x)-w/2)$\nno strip missed $\\Leftrightarrow S\\leq\\lambda_\\mathrm{ref}$":
        "该次作业的覆盖分数：\n$r^\\star$为最大半漏缝或边界距离\n$S=\\lambda_\\mathrm{ref}+\\max_x\\,(r^\\star(x)-w/2)$\n"
        "无漏作业带$\\Leftrightarrow S\\leq\\lambda_\\mathrm{ref}$",
    "Cross-section at one along-pass position (schematic): footprints of width $w$": "某一横截面示意（作业带宽度为$w$）",
    "Detail of the framed area": "方框区域局部放大",
    "Executed centreline": "实际中心线",
    "Executed path": "实际轨迹",
    "Footprint edge": "作业带边缘",
    "Headland": "地头",
    "Main-area boundary": "作业主区边界",
    "Missed": "漏作业",
    "Missed strip (width exaggerated)": "漏作业带（宽度已放大）",
    "Planned centreline": "规划中心线",
    "Simulated run on a real field (DGPS, 6 m)": "真实田块上的一次仿真作业（DGPS，6 m）",
    "Worked swath": "作业带",
    "coverage": "覆盖",
    "gap": "漏缝",
    "widest gap 12 cm": "最宽漏缝12 cm",
    # theory vs simulation
    "Analytic extreme-value model": "解析极值模型",
    "Monte Carlo twin (1000 runs)": "蒙特卡洛数字孪生（1000次）",
    "Predicted 0.9-quantile (m)": "0.9分位数预测值/m",
    "Simulated 0.9-quantile of coverage score (m)": "覆盖分数0.9分位数仿真值/m",
    # A1
    "CE+ (ours)": "CE+（本文）",
    "CPrP (Zhao et al.)": "CPrP（Zhao等）",
    "UBCP (Lindemann et al.)": "UBCP（Lindemann等）",
    "Marginal guarantee": "边际规则",
    "PAC guarantee (δ = 0.1)": "PAC规则（δ = 0.1）",
    "Overlap above per-field oracle (pp)": "超额重叠率/百分点",
    "Numbers above bars: pooled P(no miss); error bars: 95% confidence intervals over 30 fields.":
        "柱上数字为无漏作业率；误差线为30块田的95%置信区间",
    # B4
    "Marginal rule": "边际规则", "PAC rule": "PAC规则",
    "Mean miss-free rate": "无漏作业率均值",
    "Mixed fleet": "混合机队",
    "Pooled conformal (raw)": "直接合并",
    "Scale law": "尺度律",
    "Spec. × scale law": "厂商标称精度×尺度律",
    "XCE-T (analytic model)": "XCE-T（解析模型）",
    "Share with miss-free rate ≥ 0.9": "无漏作业率≥0.9的比例",
    "registered criterion 0.88": "预注册判定标准0.88",
    "registered criterion 0.895": "预注册判定标准0.895",
    # B5
    "CQR (learned, config.-aware)": "CQR（学习方法）",
    "DGPS fields, 25 calib.": "DGPS田块，25块校准田",
    "Excess overlap (pp)": "超额重叠率/百分点",
    "Marginal rule, 60 fields": "边际规则，60块校准田",
    "PAC rule, 60 fields": "PAC规则，60块校准田",
    "Mean miss-free rate, DGPS fields": "DGPS田块无漏作业率均值",
    "Mondrian (per configuration)": "Mondrian（分机型配置）",
    "Per-cfg": "按配置", "Per-configuration scale": "按机型配置经验值",
    "Raw": "直接合并", "Raw pooling": "直接合并", "Spec.": "厂商标称",
    "XCE-MC (Monte Carlo twin)": "XCE-MC（数字孪生）",
    "XCE-T (analytic, edge terms)": "XCE-T（解析模型，含边界项）",
    # learning curve / information limit
    "Analytic model (no run data)": "解析模型（无需作业数据）",
    "Feature regression, 1 run per field": "特征回归，每块田1次作业",
    "Feature regression, oracle targets (100s of runs per field)": "特征回归，理想目标值（每块田数百次作业）",
    "Number of training fields": "训练田块数",
    "SD of log(predicted / true margin)": "log(预测裕量/真实裕量)的标准差",
    "Model prediction, mean ± SD": "模型预测（均值±标准差）",
    "Observed on fresh fields": "新田块实测",
    "PAC margin / per-field optimum": "PAC裕量/逐田块理想裕量",
    "per-field optimum": "逐田块理想值",
    # cost
    "Calibrated, ε = 0.1": "校准裕量，ε = 0.1",
    "Cost ratio $r$": "成本比$r$",
    "Cost-optimal margin (reference)": "成本最优裕量（参照）",
    "Expected cost (% of main area)": "期望成本/%",
    "Farmer-tuned": "农户经验裕量",
    "Vendor rule": "厂商经验规则",
    "R1  RTK, flat, 3 m": "R1  RTK，平原，3 m",
    "R2  RTK, hilly-wet, 1.5 m": "R2  RTK，丘陵水田，1.5 m",
    "R3  DGPS, hilly, 6 m": "R3  DGPS，丘陵，6 m",
    "R1\nRTK, flat\n3 m": "R1\nRTK，平原\n3 m",
    "R2\nRTK, hilly-wet\n1.5 m": "R2\nRTK，丘陵水田\n1.5 m",
    "R3\nDGPS, hilly\n6 m": "R3\nDGPS，丘陵\n6 m",
    # A1 system map
    "Probability of a missed strip": "漏作业概率",
    "above\n$\\varepsilon$": "超过\n$\\varepsilon$",
    "Conformal erosion (ours)": "共形收缩法（本文）",
    "Conformal planning": "共形规划方法",
    "Model-based / chance-constrained": "基于模型/机会约束方法",
    "Learning-based (GP)": "学习方法（高斯过程）",
    "Robust (tube MPC)": "鲁棒方法（管道MPC）",
    "Field practice": "生产经验规则",
    "Planner/controller + vendor overlap": "路径规划或控制改进+厂商重叠量",
    # A2
    "Excess overlap": "超额重叠率",
    "Logged runs on the target field, $n$": "目标田块作业记录数$n$",
    # C1
    "Nominal": "标称",
    "Miss-free rate, DGPS fields": "DGPS田块无漏作业率",
}

PHRASES = [
    ("pass ", "作业行"),
    ("break-even\nr = ", "盈亏平衡\nr = "),
    ("(refuses ", "（无法给出"), ("%)", "%）"),
    ("bias ", "偏差"), (", sd ", "，标准差"), (": ", "："),
    (" (RTK)", "（RTK）"), (" (DGPS)", "（DGPS）"),
]

# 实验统计表（make_tables.py 自动生成）

### E2 主对比（仿真执行）— paddy：60 块真实田块 × 每方法 300 次执行，目标 P(无漏) ≥ 0.90

| 方法 | P(无漏) [95% CI] | 不显著低于目标的田块 | E[漏] (‱) | 重叠 % [95% CI] | 不可行 | vs CE-U 重叠 (Holm p) |
|---|---|---|---|---|---|---|
| Nominal (no margin) | 0.000 [0.000, 0.000] | 0% | 76.44 | 0.1 ± 0.1 | 0 | 2.6e-10 |
| Fixed overlap 5 cm | 0.000 [0.000, 0.000] | 0% | 21.04 | 1.9 ± 0.1 | 0 | 2.6e-10 |
| Fixed overlap 10 cm | 0.020 [0.018, 0.022] | 0% | 4.20 | 3.9 ± 0.2 | 0 | 2.6e-10 |
| Slope-compensation rule | 0.028 [0.025, 0.030] | 0% | 13.18 | 2.6 ± 0.3 | 0 | 2.6e-10 |
| Gaussian, pointwise | 0.000 [0.000, 0.001] | 0% | 9.66 | 2.9 ± 0.2 | 0 | 2.6e-10 |
| Empirical quantile, pointwise | 0.000 [0.000, 0.001] | 0% | 10.43 | 2.8 ± 0.2 | 0 | 2.6e-10 |
| Conformal, pointwise | 0.000 [0.000, 0.000] | 0% | 10.27 | 2.8 ± 0.2 | 0 | 2.6e-10 |
| Gaussian chance constr. | 0.929 [0.925, 0.932] | 95% | 0.04 | 9.2 ± 0.2 | 0 | 3.7e-01 |
| Cantelli bound | 0.991 [0.989, 0.992] | 100% | 0.02 | 12.9 ± 0.4 | 0 | 2.6e-10 |
| Scenario approach | 0.972 [0.970, 0.975] | 100% | 0.04 | 11.1 ± 0.4 | 0 | 2.6e-10 |
| CVaR | 0.971 [0.968, 0.973] | 100% | 0.03 | 10.9 ± 0.4 | 0 | 2.6e-10 |
| Wasserstein DRO-CVaR | 0.997 [0.996, 0.997] | 100% | 0.01 | 15.7 ± 0.6 | 0 | 2.6e-10 |
| Robust worst-case | 0.994 [0.993, 0.995] | 100% | 0.01 | 15.1 ± 1.1 | 0 | 2.6e-10 |
| **CE-pair (ours)** | 0.960 [0.957, 0.963] | 98% | 0.03 | 10.2 ± 0.3 | 0 | 9.3e-10 |
| **CE-U (ours)** | 0.925 [0.921, 0.929] | 92% | 0.05 | 9.1 ± 0.2 | 0 | — |
| **CE-A (ours)** | 0.925 [0.922, 0.929] | 93% | 0.05 | 9.3 ± 0.2 | 0 | 1.4e-01 |
| **CE-R (ours)**（风险证书：E[漏] ≤ 30‱） | 0.004 [0.003, 0.005] | 0% | 6.84 | 3.4 ± 0.2 | 0 | 2.6e-10 |

### E2 主对比（仿真执行）— wheat：60 块真实田块 × 每方法 300 次执行，目标 P(无漏) ≥ 0.90

| 方法 | P(无漏) [95% CI] | 不显著低于目标的田块 | E[漏] (‱) | 重叠 % [95% CI] | 不可行 | vs CE-U 重叠 (Holm p) |
|---|---|---|---|---|---|---|
| Nominal (no margin) | 0.000 [0.000, 0.000] | 0% | 76.63 | 0.2 ± 0.1 | 0 | 2.6e-10 |
| Fixed overlap 5 cm | 0.000 [0.000, 0.000] | 0% | 21.61 | 1.8 ± 0.2 | 0 | 2.6e-10 |
| Fixed overlap 10 cm | 0.017 [0.015, 0.019] | 0% | 4.24 | 3.5 ± 0.3 | 0 | 2.6e-10 |
| Slope-compensation rule | 0.000 [0.000, 0.001] | 0% | 15.05 | 2.2 ± 0.2 | 0 | 2.6e-10 |
| Gaussian, pointwise | 0.000 [0.000, 0.001] | 0% | 9.99 | 2.6 ± 0.2 | 0 | 2.6e-10 |
| Empirical quantile, pointwise | 0.000 [0.000, 0.001] | 0% | 10.62 | 2.5 ± 0.2 | 0 | 2.6e-10 |
| Conformal, pointwise | 0.000 [0.000, 0.001] | 0% | 10.40 | 2.5 ± 0.2 | 0 | 2.6e-10 |
| Gaussian chance constr. | 0.940 [0.936, 0.943] | 100% | 0.04 | 10.1 ± 0.4 | 0 | 3.2e-02 |
| Cantelli bound | 0.993 [0.991, 0.994] | 100% | 0.01 | 14.3 ± 0.7 | 0 | 2.6e-10 |
| Scenario approach | 0.976 [0.974, 0.979] | 100% | 0.03 | 11.9 ± 0.6 | 0 | 2.6e-10 |
| CVaR | 0.977 [0.975, 0.979] | 100% | 0.03 | 12.0 ± 0.5 | 0 | 2.6e-10 |
| Wasserstein DRO-CVaR | 0.997 [0.996, 0.998] | 100% | 0.02 | 17.4 ± 0.9 | 0 | 2.6e-10 |
| Robust worst-case | 0.994 [0.993, 0.995] | 100% | 0.01 | 19.1 ± 2.4 | 0 | 2.6e-10 |
| **CE-pair (ours)** | 0.959 [0.956, 0.962] | 100% | 0.04 | 10.9 ± 0.5 | 0 | 8.8e-10 |
| **CE-U (ours)** | 0.930 [0.926, 0.934] | 97% | 0.07 | 9.8 ± 0.4 | 0 | — |
| **CE-A (ours)** | 0.934 [0.930, 0.937] | 97% | 0.04 | 9.9 ± 0.4 | 0 | 5.8e-01 |
| **CE-R (ours)**（风险证书：E[漏] ≤ 30‱） | 0.007 [0.006, 0.008] | 0% | 6.43 | 3.1 ± 0.3 | 0 | 2.6e-10 |

### E8 真实机器人（CitrusFarm）随机划分 300 次，3 行作业带，ε = 0.1

| 方法 | P(无漏) 均值 | 5–95% 区间 | 重叠 % | 校准单元数 | 测试单元数 |
|---|---|---|---|---|---|
| Nominal (no margin) | 0.000 | [0.000, 0.000] | 0.0 | 53 | 53 |
| Fixed overlap 10 cm | 0.000 | [0.000, 0.000] | 1.7 | 53 | 53 |
| Fixed overlap 30 cm | 0.000 | [0.000, 0.000] | 5.3 | 53 | 53 |
| Gaussian, pointwise | 0.126 | [0.057, 0.189] | 10.4 | 53 | 53 |
| Empirical quantile, pointwise | 0.161 | [0.075, 0.245] | 11.3 | 53 | 53 |
| Conformal, pointwise | 0.164 | [0.075, 0.264] | 11.3 | 53 | 53 |
| Gaussian chance constr. | 0.894 | [0.830, 0.962] | 31.4 | 53 | 53 |
| Cantelli bound | 0.988 | [0.943, 1.000] | 53.1 | 53 | 53 |
| Scenario approach | 0.980 | [0.943, 1.000] | 49.7 | 53 | 53 |
| CVaR | 0.937 | [0.868, 0.982] | 39.7 | 53 | 53 |
| Wasserstein DRO-CVaR | 1.000 | [1.000, 1.000] | 88.9 | 53 | 53 |
| Robust worst-case | 0.980 | [0.943, 1.000] | 49.7 | 53 | 53 |
| **CE-pair (ours)** | 0.912 | [0.811, 0.981] | 34.7 | 53 | 53 |
| **CE-U (ours)** | 0.910 | [0.811, 0.981] | 34.6 | 53 | 53 |

**分布外留出（3 行）**：P(无漏)

| 留出 | CE-U (ours) | Scenario approach | CVaR | Gaussian chance constr. | Robust worst-case | Cantelli bound |
|---|---|---|---|---|---|---|
| LOBO:13B | 0.896 (32%) | 0.994 (55%) | 0.957 (42%) | 0.883 (31%) | 0.994 (55%) | 0.994 (55%) |
| LOBO:13D | 0.922 (36%) | 0.969 (46%) | 0.969 (43%) | 0.922 (32%) | 0.984 (55%) | 0.984 (55%) |
| LOBO:14B | 0.909 (32%) | 0.970 (45%) | 0.939 (39%) | 0.909 (30%) | 0.985 (46%) | 0.985 (50%) |
| LODO:07-16 | 0.894 (32%) | 0.985 (46%) | 0.915 (36%) | 0.879 (30%) | 0.985 (46%) | 0.985 (47%) |
| LODO:07-18 | 0.936 (36%) | 0.979 (46%) | 0.979 (42%) | 0.915 (32%) | 0.989 (55%) | 0.989 (56%) |

### E8 真实机器人（CitrusFarm）随机划分 300 次，5 行作业带，ε = 0.1

| 方法 | P(无漏) 均值 | 5–95% 区间 | 重叠 % | 校准单元数 | 测试单元数 |
|---|---|---|---|---|---|
| Nominal (no margin) | 0.000 | [0.000, 0.000] | 0.0 | 29 | 30 |
| Fixed overlap 10 cm | 0.000 | [0.000, 0.000] | 1.7 | 29 | 30 |
| Fixed overlap 30 cm | 0.000 | [0.000, 0.000] | 5.3 | 29 | 30 |
| Gaussian, pointwise | 0.048 | [0.000, 0.100] | 10.3 | 29 | 30 |
| Empirical quantile, pointwise | 0.074 | [0.000, 0.167] | 11.2 | 29 | 30 |
| Conformal, pointwise | 0.076 | [0.000, 0.168] | 11.2 | 29 | 30 |
| Gaussian chance constr. | 0.909 | [0.767, 1.000] | 29.7 | 29 | 30 |
| Cantelli bound | 0.972 | [0.900, 1.000] | 48.4 | 29 | 30 |
| Scenario approach | 0.964 | [0.867, 1.000] | 56.3 | 29 | 30 |
| CVaR | 0.948 | [0.867, 1.000] | 38.2 | 29 | 30 |
| Wasserstein DRO-CVaR | 0.984 | [0.967, 1.000] | 104.8 | 29 | 30 |
| Robust worst-case | 0.964 | [0.867, 1.000] | 56.3 | 29 | 30 |
| **CE-pair (ours)** | 0.931 | [0.800, 1.000] | 33.7 | 29 | 30 |
| **CE-U (ours)** | 0.897 | [0.767, 1.000] | 28.8 | 29 | 30 |

**分布外留出（5 行）**：P(无漏)

| 留出 | CE-U (ours) | Scenario approach | CVaR | Gaussian chance constr. | Robust worst-case | Cantelli bound |
|---|---|---|---|---|---|---|
| LOBO:13B | 0.890 (32%) | 0.904 (33%) | 0.877 (30%) | 0.760 (24%) | 0.904 (33%) | 0.925 (36%) |
| LOBO:13D | 0.972 (33%) | 1.000 (81%) | 1.000 (41%) | 0.944 (32%) | 1.000 (81%) | 1.000 (53%) |
| LOBO:14B | 0.897 (32%) | 1.000 (81%) | 0.923 (41%) | 0.897 (32%) | 1.000 (81%) | 1.000 (53%) |
| LODO:07-16 | 0.816 (27%) | 0.816 (27%) | 0.803 (26%) | 0.816 (27%) | 0.816 (27%) | 0.925 (39%) |
| LODO:07-18 | 0.959 (33%) | 1.000 (81%) | 1.000 (42%) | 0.959 (31%) | 1.000 (81%) | 1.000 (54%) |

**真实时间序列上的在线部署**（目标漏作业频率 0.10）

| K | 方法 | 漏作业频率 | 重叠 % | 作业带数 |
|---|---|---|---|---|
| 3 | ACI (ours, online) | 0.088 | 31.9 | 34 |
| 3 | static (first day) | 0.059 | 35.8 | 34 |
| 5 | ACI (ours, online) | 0.056 | 30.5 | 18 |
| 5 | static (first day) | 0.000 | 33.1 | 18 |

### E9 消融 — 默认工况（CORS RTK fix，3 m 幅宽）

| 作物 | 变体 | P(无漏) | 重叠 % | 腐蚀量 (cm) | 田块数 |
|---|---|---|---|---|---|
| paddy | absolute-error score | 0.995 | 13.8 | 18.0 | 30 |
| paddy | full (ours) | 0.931 | 9.3 | 12.6 | 30 |
| paddy | naive calibration (no fixed point) | 0.930 | 9.3 | 12.6 | 30 |
| paddy | pointwise quantile (no sup) | 0.000 | 2.8 | 3.6 | 30 |
| wheat | absolute-error score | 0.995 | 14.5 | 18.9 | 30 |
| wheat | full (ours) | 0.931 | 9.7 | 13.1 | 30 |
| wheat | naive calibration (no fixed point) | 0.933 | 9.9 | 13.3 | 30 |
| wheat | pointwise quantile (no sup) | 0.000 | 2.6 | 3.7 | 30 |

### E9 消融 — 困难工况（CORS RTK fix，湿土，1.5 m 幅宽）

| 作物 | 变体 | P(无漏) | 重叠 % | 腐蚀量 (cm) | 田块数 |
|---|---|---|---|---|---|
| paddy | absolute-error score | 0.996 | 45.4 | 23.4 | 20 |
| paddy | full (ours) | 0.912 | 26.4 | 15.6 | 20 |
| paddy | naive calibration (no fixed point) | 0.928 | 27.3 | 16.1 | 20 |
| paddy | pointwise quantile (no sup) | 0.000 | 6.1 | 4.3 | 20 |

### E3b 跨田块（新田块无历史）— paddy：学习类与鲁棒类对照

| 方法 | P(无漏) 均值 ± 95% CI（按重复） | 重叠 % | 重复次数 |
|---|---|---|---|
| Quantile regression (GBM) | 0.835 ± 0.038 | 8.4 | 10 |
| Gaussian chance constr. | 0.939 ± 0.024 | 10.0 | 10 |
| Scenario approach | 0.993 ± 0.006 | 19.9 | 10 |
| CVaR | 0.979 ± 0.010 | 12.3 | 10 |
| Wasserstein DRO-CVaR | 0.998 ± 0.001 | 20.9 | 10 |
| Robust worst-case | 0.994 ± 0.006 | 19.9 | 10 |
| CQR | 0.911 ± 0.028 | 9.5 | 10 |
| **CE-U (ours)** | 0.953 ± 0.018 | 10.0 | 10 |

### E3b 跨田块（新田块无历史）— wheat：学习类与鲁棒类对照

| 方法 | P(无漏) 均值 ± 95% CI（按重复） | 重叠 % | 重复次数 |
|---|---|---|---|
| Quantile regression (GBM) | 0.849 ± 0.030 | 9.1 | 10 |
| Gaussian chance constr. | 0.949 ± 0.018 | 10.9 | 10 |
| Scenario approach | 0.989 ± 0.006 | 16.3 | 10 |
| CVaR | 0.977 ± 0.010 | 13.0 | 10 |
| Wasserstein DRO-CVaR | 0.999 ± 0.001 | 21.2 | 10 |
| Robust worst-case | 0.994 ± 0.004 | 21.8 | 10 |
| CQR | 0.968 ± 0.013 | 12.4 | 10 |
| **CE-U (ours)** | 0.946 ± 0.017 | 10.6 | 10 |

### E4 灵敏度（控制器 / 横滚补偿 / 幅宽 / 真实 GNSS 接收机等级）

| 因素 | 取值 | 认证腐蚀 q (cm) | P(无漏) | 重叠 % | 无余量时 P(无漏) | 田块数 |
|---|---|---|---|---|---|---|
| controller | pure_pursuit | 18.5 | 0.925 | 14.4 | 0.000 | 10 |
| controller | stanley | 13.4 | 0.917 | 10.1 | 0.000 | 10 |
| controller | lqr | 11.2 | 0.929 | 8.5 | 0.000 | 10 |
| controller | lqr_i | 12.6 | 0.939 | 9.6 | 0.000 | 10 |
| roll compensation | 0.0 | 13.7 | 0.948 | 10.4 | 0.000 | 10 |
| roll compensation | 0.5 | 12.8 | 0.930 | 9.7 | 0.000 | 10 |
| roll compensation | 0.85 | 12.6 | 0.934 | 9.5 | 0.000 | 10 |
| roll compensation | 0.95 | 12.7 | 0.936 | 9.6 | 0.000 | 10 |
| implement width (m) | 1.5 | 13.3 | 0.911 | 21.6 | 0.000 | 10 |
| implement width (m) | 3.0 | 12.5 | 0.929 | 9.5 | 0.000 | 10 |
| implement width (m) | 6.0 | 12.2 | 0.939 | 5.3 | 0.000 | 10 |
| implement width (m) | 12.0 | 12.0 | 0.983 | 0.6 | 0.058 | 10 |
| GNSS receiver grade | rtk_fix | 12.7 | 0.938 | 9.6 | 0.000 | 10 |
| GNSS receiver grade | rtk_float | 12.5 | 0.932 | 9.4 | 0.000 | 10 |
| GNSS receiver grade | dgps | 52.0 | 0.912 | 54.0 | 0.000 | 10 |

### E2b 系统级对比（system_v5）— R1 RTK flat 3 m：16 块田 × 每系统 200 次执行，目标 P(无漏) ≥ 0.90

| 系统 | 类别 | P(无漏) [95% CI] | 达标田块 | 漏作业 (m²/ha) | 重叠 % | 相对 oracle 多付重叠 (pp) | 行数 | 路径 (m) |
|---|---|---|---|---|---|---|---|---|
| **BCD + Lenain ctrl + CE (ours)** | ours | 0.954 [0.946, 0.961] | 100% | 0.1 | 8.3 | -1.0 | 32.8 | 3838 |
| **BCD + offset-free MPC + CE (ours)** | ours | 0.953 [0.946, 0.960] | 100% | 0.1 | 8.7 | -0.6 | 32.9 | 3845 |
| **Follow-previous-pass + LQR-I + CE (ours)** | ours | 0.972 [0.965, 0.977] | 100% | 0.0 | 9.6 | +0.3 | 33.1 | 3880 |
| **BCD + LQR-I + CE (ours)** | ours | 0.952 [0.944, 0.959] | 100% | 0.0 | 10.0 | +0.7 | 33.2 | 3894 |
| **Hameed 3D + LQR-I + CE (ours)** | ours | 0.954 [0.946, 0.961] | 100% | 0.0 | 10.1 | +0.8 | 33.3 | 3898 |
| **Fields2Cover + LQR-I + CE (ours)** | ours | 0.962 [0.955, 0.968] | 100% | 0.1 | 10.3 | +1.0 | 21.4 | 3594 |
| Hameed 3D terrain spacing (0 overlap) | planner | 0.000 [0.000, 0.001] | 0% | 75.6 | 0.3 | -9.1 | 30.4 | 3538 |
| BCD + ESO sliding-mode ctrl + spec overlap | controller | 0.000 [0.000, 0.001] | 0% | 14.6 | 1.9 | -7.4 | 30.9 | 3609 |
| BCD + LQR-I + spec overlap (2x vendor p2p) | industry | 0.000 [0.000, 0.001] | 0% | 21.1 | 1.9 | -7.4 | 30.9 | 3609 |
| BCD + Lenain sideslip-observer ctrl + spec overlap | controller | 0.000 [0.000, 0.001] | 0% | 14.5 | 1.9 | -7.4 | 30.9 | 3609 |
| BCD + offset-free MPC + spec overlap | controller | 0.000 [0.000, 0.001] | 0% | 15.8 | 1.9 | -7.4 | 30.9 | 3609 |
| BCD + vendor terrain comp. + spec overlap | industry | 0.000 [0.000, 0.001] | 0% | 21.4 | 1.9 | -7.4 | 30.9 | 3609 |
| Follow-previous-pass guidance + spec overlap | planner | 0.000 [0.000, 0.001] | 0% | 15.3 | 1.9 | -7.4 | 30.9 | 3609 |
| Hameed 3D terrain spacing + spec overlap | planner | 0.000 [0.000, 0.001] | 0% | 20.9 | 1.9 | -7.4 | 30.9 | 3609 |
| Fields2Cover (opt. heading) + spec overlap | planner | 0.000 [0.000, 0.001] | 0% | 21.0 | 2.0 | -7.3 | 19.8 | 3333 |
| GP cautious margin (Hewing et al.) | learning | 0.001 [0.000, 0.003] | 0% | 8.0 | 2.9 | -6.4 | 31.3 | 3651 |
| Gaussian belief, pointwise | model-based | 0.048 [0.040, 0.055] | 0% | 3.9 | 3.7 | -5.6 | 31.4 | 3669 |
| GP cautious margin, Bonferroni (Hewing et al.) | learning | 0.877 [0.865, 0.888] | 56% | 0.1 | 8.7 | -0.6 | 32.8 | 3835 |
| Model-based MC chance constraint | model-based | 0.888 [0.877, 0.899] | 88% | 0.1 | 8.8 | -0.5 | 32.9 | 3846 |
| BCD + LQR-I + farmer-tuned global overlap | industry | 0.922 [0.912, 0.931] | 94% | 0.1 | 9.0 | -0.3 | 33.2 | 3869 |
| BCD + vendor terrain comp. + farmer-tuned | industry | 0.912 [0.901, 0.921] | 88% | 0.1 | 9.2 | -0.1 | 33.1 | 3857 |
| Gaussian chance constraint | chance-rule | 0.920 [0.910, 0.929] | 94% | 0.1 | 9.3 | -0.0 | 33.0 | 3868 |
| Conformal predictive programming (Zhao et al.) | conformal | 0.920 [0.910, 0.929] | 94% | 0.1 | 9.3 | +0.0 | 33.1 | 3867 |
| Gaussian belief, Rice extreme-value | model-based | 0.907 [0.897, 0.917] | 94% | 0.1 | 9.4 | +0.1 | 33.1 | 3871 |
| Conformal planning, pair-level union bound (Lindemann et al.) | conformal | 0.955 [0.948, 0.962] | 100% | 0.0 | 10.4 | +1.1 | 33.5 | 3923 |
| Scenario approach (PAC, beta=0.01) | chance-rule | 0.971 [0.965, 0.977] | 100% | 0.0 | 11.2 | +1.9 | 33.6 | 3935 |
| Conformal planning, union bound (Lindemann et al.) | conformal | 0.981 [0.976, 0.985] | 100% | 0.0 | 12.5 | +3.2 | 34.1 | 3990 |
| Wasserstein DRO-CVaR | chance-rule | 0.997 [0.995, 0.999] | 100% | 0.0 | 16.0 | +6.7 | 34.9 | 4115 |
| Tube-MPC radius margin (W99) | robust | 1.000 [0.999, 1.000] | 100% | 0.0 | 48.0 | +38.7 | 43.8 | 5254 |
| Tube-MPC radius margin (Wmax) | robust | 1.000 [0.991, 1.000] | 100% | 0.0 | 310.1 | +301.5 | 171.0 | 11500 |

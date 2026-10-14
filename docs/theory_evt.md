# 执行误差的极值结构与决策依赖下的共形保证

**Lyapunov 协方差 → Kac–Rice 超限界 → Slepian/Chen–Stein Poisson 逼近 → 混合 Poisson 迁移定理 → Gumbel 渐近与跨田块枢轴**

本文件取代 `theory_transfer.md` 中定理 5 的初等证明。结论更强：放大因子不需要估计危险率或极值指数，而是由闭环系统和地形**直接计算**；并且推出了余量随田块规模的增长律，以及跨田块校准的保证。

---

## 0. 记号与对象

| 记号 | 含义 |
|---|---|
| $\pi=(y_1<\dots<y_K)$ | 往返布行计划，间距 $d=w-2\lambda$ |
| $x\in I_k$ | 第 $k$ 行在主作业区内的弧长坐标（行程 1 m 采样） |
| $e_k(x)$ | 第 $k$ 行在田块坐标下的实际横向偏差 |
| $Z_j(x)=\tfrac12\big(e_{k+1}(x)-e_k(x)\big)$ | 行对 $j=(k,k+1)$ 的"间隙过程"；边界伪行对 $Z_0=e_1$，$Z_K=-e_K$ |
| $T_j=\sup_{x\in I_j}Z_j(x)$ | 行对分数；$I_j$ 为两行共同覆盖的截面 |
| $U_\pi=\max_jT_j$ | 作业级分数，等于 `core.exact_scores` |
| $M=0\iff U_\pi\le\lambda$ | 引理 1（精确版），`core.exact_pair_scores` 已在数值上验证 |
| $C$ | 一次作业的条件：侧滑增益 $k_s$、粗糙度、侧倾补偿系数、安装偏置、GNSS 误差轨迹 |
| $\mu_j(t\mid C)$ | $P(T_j>t\mid C)$ |
| $M_\pi(t\mid C)$ | $\sum_{j\in J(\pi)}\mu_j(t\mid C)$，给定条件下超限行对的期望个数 |

---

## 1. 第一层：闭环线性结构与 Lyapunov 协方差

**假设 A1（线性工作区）。** 转角不饱和，转角速率不受限，小角度近似成立（$\sin\approx\mathrm{id}$，$\tan\approx\mathrm{id}$）。地形梯度沿车辆的微小横向偏移不变。

在 A1 下，单行的离散闭环（步长 $\Delta t$）可写为
$$\xi_{t+1}=A\,\xi_t+B\,w_t+b_t(C),\qquad \xi=(d,\psi,\delta,\iota,\beta_{\rm OU})^\top,$$
其中：

- $\iota$ 是积分器状态，$\beta_{\rm OU}$ 是 OU 侧滑；
- $w_t\sim N(0,\Sigma_w)$ 是 OU 新息和航向测量噪声，各行独立；
- $b_t(C)$ 是**给定条件下的确定性输入**：GNSS 误差投影、侧倾天线偏置 $h_{\rm ant}(1-c)\,g_y$、平均侧滑 $-0.35\,k_sg_y$、安装偏置；
- $A,B$ 由 LQR-I 增益、执行器时间常数 $\tau$、轴距 $l$、车速 $v$ 决定，与计划无关。

**命题 1.1（条件高斯性与 Lyapunov 协方差）。** 在 A1 下，给定 $C$：

1. 各行的偏差 $e_k(\cdot)$ 是相互独立的高斯过程。
2. 均值 $m_k(x\mid C)$ 是确定性输入经过闭环线性滤波后的响应。
3. 进入稳态后，协方差 $P=\mathrm{Cov}(\xi)$ 是离散 Lyapunov 方程的唯一解：
$$P=APA^\top+B\Sigma_wB^\top\qquad(\rho(A)<1).$$
4. 关于弧长 $x=vt$，单行的谱矩为
$$\lambda_0=P_{dd},\qquad \lambda_2=\mathrm{Var}\Big(\frac{de}{dx}\Big)=\mathrm{Var}(\psi+\beta)=P_{\psi\psi}+2P_{\psi\beta}+P_{\beta\beta}.$$

**证明。** 线性系统受高斯输入驱动，所以状态是高斯的。各行的噪声 $w_t$ 独立，行与行之间只通过 $C$ 中的确定性量联系。$\rho(A)<1$（LQR 闭环稳定）保证 Lyapunov 方程有唯一的半正定解。由 $\dot d=v\sin(\psi+\beta)$ 得 $de/dx=\psi+\beta$。$\square$

**推论 1.2。** 两行独立，因此间隙过程 $Z_j$ 在给定 $C$ 时也是高斯过程：
$$s^2=\mathrm{Var}(Z_j(x)\mid C)=\tfrac12\lambda_0,\qquad s'^2=\mathrm{Var}(Z_j'(x)\mid C)=\tfrac12\lambda_2,$$
均值为 $m_j=\tfrac12(m_{k+1}-m_k)$。方差和谱矩只取决于控制器和噪声参数，**与计划无关**。计划只通过均值 $m_j$ 影响行对，而均值是行位置和作业时刻的函数。

---

## 2. 第二层：Kac–Rice 公式给出单行对的超限界

**定理 2.1（Kac–Rice 上界，非平稳高斯版）。** 给定 $C$，$Z_j$ 是区间 $I_j=[0,L_j]$ 上 $C^1$ 的高斯过程。记

- $\sigma(x)^2=\mathrm{Var}Z_j(x)$，$\sigma'(x)^2=\mathrm{Var}Z_j'(x)$，$r(x)=\mathrm{Cov}(Z_j(x),Z_j'(x))$；
- 条件斜率均值 $\tilde m'(x;t)=m_j'(x)+\dfrac{r(x)}{\sigma(x)^2}\big(t-m_j(x)\big)$；
- 条件斜率标准差 $\tilde\sigma'(x)^2=\sigma'(x)^2-r(x)^2/\sigma(x)^2$；
- $\Psi(a)=\varphi(a)+a\Phi(a)$，即 $E[(a+N(0,1))^+]$。

则
$$\boxed{\;\mu_j(t\mid C)\ \le\ \bar\Phi\Big(\frac{t-m_j(0)}{\sigma(0)}\Big)+\int_0^{L_j}\frac{\tilde\sigma'(x)}{\sigma(x)}\,\varphi\Big(\frac{t-m_j(x)}{\sigma(x)}\Big)\,\Psi\Big(\frac{\tilde m'(x;t)}{\tilde\sigma'(x)}\Big)\,dx\;}=: \bar\mu_j(t\mid C).$$

进入稳态（$r\equiv0$，$\sigma\equiv s$，$\sigma'\equiv s'$）且均值为常数时，上式化为经典形式
$$\bar\mu_j(t)=\bar\Phi(u)+\frac{L_j}{2\pi}\frac{s'}{s}e^{-u^2/2},\qquad u=\frac{t-m_j}{s}.$$

**证明。** 若 $\sup_xZ_j(x)>t$，则要么 $Z_j(0)>t$，要么在 $(0,L_j)$ 内至少有一次向上穿越 $t$。因此
$$\mu_j\le P(Z_j(0)>t)+E[N_t^+].$$
$C^1$ 高斯过程满足 Kac–Rice 公式的正则性条件（Azaïs & Wschebor 2009，定理 3.4），所以
$$E[N_t^+]=\int E\big[(Z_j')^+\mid Z_j=t\big]\,p_{Z_j(x)}(t)\,dx.$$
在 $Z_j(x)=t$ 的条件下，$Z_j'(x)$ 是高斯的，均值为 $\tilde m'$、标准差为 $\tilde\sigma'$，所以 $E[(Z_j')^+\mid Z_j=t]=\tilde\sigma'\,\Psi(\tilde m'/\tilde\sigma')$。$\square$

**命题 2.2（尾部精确性）。** 当 $t\to\infty$ 时 $\bar\mu_j/\mu_j\to1$。这是 Rice 方法对光滑高斯过程的标准结论（Piterbarg 1996；Azaïs & Wschebor 2009，第 4 章）：两次及以上穿越的概率是高阶小量。

我们关心的阈值都在 $u\approx3$–$4$ 的尾部，所以 $\bar\mu_j$ 可以直接当作 $\mu_j$ 的**可计算替代**。第 6 节会做数值检验。

---

## 3. 第三层：Slepian 不等式与 Chen–Stein Poisson 逼近

行对之间并不独立：

- 相邻行对 $j$ 和 $j+1$ 共用第 $k+1$ 行；
- 边界伪行对与第一个（或最后一个）行对共用一行；
- 不相邻的行对给定 $C$ 后独立（命题 1.1）。

**假设 A2（单行自协方差非负）。** 给定 $C$，单行偏差的自协方差 $\mathrm{Cov}(e_k(x),e_k(x'))\ge0$ 对所有 $x,x'$ 成立。闭环过阻尼时成立；数值检验见第 6 节。

**引理 3.1（Slepian：相邻行对负相关）。** 在 A2 下，对相邻行对 $j,j+1$：
$$P(T_j>t,\ T_{j+1}>t\mid C)\ \le\ \mu_j(t\mid C)\,\mu_{j+1}(t\mid C).$$

**证明。** 两者共用第 $k+1$ 行，但符号相反：
$$\mathrm{Cov}\big(Z_j(x),Z_{j+1}(x')\mid C\big)=-\tfrac14\mathrm{Cov}\big(e_{k+1}(x),e_{k+1}(x')\big)\le0.$$
把这对过程和"两者独立、边际分布相同"的版本比较：独立版本的交叉协方差为 0，不小于原交叉协方差，而各自内部的协方差相同。由 Slepian 不等式（对可分高斯过程成立，Adler & Taylor 2007，定理 2.2.1），交叉协方差越小，$P(\text{两个上确界都}\le t)$ 越小：
$$P(T_j\le t,T_{j+1}\le t)\le P(T_j\le t)\,P(T_{j+1}\le t).$$
展开 $P(T_j>t,T_{j+1}>t)=1-P(T_j\le t)-P(T_{j+1}\le t)+P(T_j\le t,T_{j+1}\le t)$ 即得。$\square$

**定理 3.2（条件 Poisson 逼近）。** 在 A1、A2 下，给定 $C$，令 $W_t=\sum_j\mathbf 1\{T_j>t\}$，$M=M_\pi(t\mid C)$。则
$$\Big|P(U_\pi\le t\mid C)-e^{-M}\Big|\ \le\ \big(1\wedge M^{-1}\big)\Big(\sum_j\mu_j^2+4\sum_j\mu_j\mu_{j+1}\Big)\ \le\ 5\,\mu_{\max}(t\mid C).$$

**证明。** 取依赖邻域 $B_j=\{j-1,j,j+1\}$。邻域外的指标与 $\mathbf 1\{T_j>t\}$ 独立（给定 $C$），所以 Arratia–Goldstein–Gordon（1989）定理 1 中的 $b_3=0$，并且
$$\big|P(W_t=0)-e^{-M}\big|\le(1\wedge M^{-1})(b_1+b_2),$$
其中 $b_1=\sum_j\sum_{i\in B_j}\mu_i\mu_j=\sum_j\mu_j^2+2\sum_j\mu_j\mu_{j+1}$，$b_2=\sum_j\sum_{i\in B_j\setminus\{j\}}P(I_iI_j=1)\le2\sum_j\mu_j\mu_{j+1}$（由引理 3.1）。最后，由 $\sum_j\mu_j\mu_{j+1}\le\mu_{\max}M$ 和 $\sum_j\mu_j^2\le\mu_{\max}M$，并且 $(1\wedge M^{-1})M\le1$，得到 $5\mu_{\max}$。$\square$

**意义。** 逼近误差是**单个行对**的超限概率量级，大约 $\varepsilon/K$，比目标风险 $\varepsilon$ 小一个行数的倍数。行对相依并不破坏 Poisson 结构：共用一行带来的是负相关，Slepian 把它变成了有利方向。

---

## 4. 第四层：混合 Poisson 表示与决策依赖迁移定理

**定理 4.1（混合 Poisson 表示）。** 对条件 $C$ 积分：
$$F_\pi(t)=P(U_\pi\le t)=\mathbb E_C\big[e^{-M_\pi(t\mid C)}\big]+\rho_\pi(t),\qquad|\rho_\pi(t)|\le5\,\mathbb E_C\big[\mu_{\max}(t\mid C)\big].$$

**推论 4.2（极值指数的来源）。** 记 $\theta_t=(1-F_\pi(t))/E[W_t]$。则
$$\theta_t=\frac{\mathbb E_C\big[1-e^{-M}\big]}{\mathbb E_C[M]}+O\big(\mathbb E\,\mu_{\max}/\mathbb E M\big)\ <\ 1,$$
小于 1 来自 Jensen 不等式（$1-e^{-x}$ 是凹函数）。

**含义。** 超限的成簇，也就是 $\theta<1$，**并不是**由行对之间的局部相依造成的；它来自作业条件 $C$ 在作业之间的异质性。上一版小实验测得的 $\theta\approx0.33$–$0.76$ 应该能由 $M$ 在作业之间的分布预测出来，这一点可以检验。

**定理 4.3（决策依赖迁移，闭式放大因子）。** 设参考计划 $\pi_0$ 和部署计划 $\pi_1$ 满足：

- 行对可以配对，$J(\pi_1)\subseteq J(\pi_0)$；
- 给定 $C$，配对行对的间隙过程协方差相同（推论 1.2：协方差与计划无关），均值之差满足 $m^{(1)}_j(x\mid C)-m^{(0)}_j(x\mid C)\le\Delta_j(C)$。

记 $\bar u=\sup_{j,x}\big(t-m^{(0)}_j(x)\big)/s$ 为阈值的最大标准化水平。则
$$\boxed{\;1-F_{\pi_1}(t)\ \le\ \kappa\,\big(1-F_{\pi_0}(t)\big)+(\kappa+1)\,5\,\mathbb E\mu_{\max},\qquad \kappa=\sup_C\exp\Big(\frac{\bar u\,\Delta(C)}{s}+\frac{\Delta(C)^2}{2s^2}\Big)\;}$$

**证明要点。**

1. 均值上移 $\Delta_j$ 等价于阈值下移 $\Delta_j$，所以 $\mu^{(1)}_j(t)\le\mu^{(0)}_j(t-\Delta_j)$。
2. 用定理 2.1 的上界 $\bar\mu$（尾部精确）。高斯密度满足
$$\varphi\Big(\frac{t-\Delta-m}{s}\Big)=\varphi\Big(\frac{t-m}{s}\Big)\exp\Big(\frac{(t-m)\Delta}{s^2}-\frac{\Delta^2}{2s^2}\Big)\le\varphi\Big(\frac{t-m}{s}\Big)\exp\Big(\frac{\bar u\Delta}{s}+\frac{\Delta^2}{2s^2}\Big).$$
   于是 $M_{\pi_1}(t\mid C)\le\kappa M_{\pi_0}(t\mid C)$。多出的行对只出现在 $\pi_0$ 中，不会增大 $M_{\pi_1}$。
3. 对 $\kappa\ge1$ 有 $1-e^{-\kappa M}\le\kappa(1-e^{-M})$（凹性）。取期望，再用定理 4.1 处理误差项。$\square$

**推论 4.4（部署保证）。** 设 $\hat\lambda$ 为参考计划上 $n$ 次校准作业的共形分位数（边际版或 PAC 版），部署 $\pi(\hat\lambda)$，并且 $\lambda_0\ge\hat\lambda$。则：

- **边际版：** $P(\text{部署后漏作业})\le\kappa\,\varepsilon+O(\varepsilon/K)$；
- **PAC 版：** 以至少 $1-\delta$ 的概率，$P(\text{漏}\mid\text{校准})\le\kappa\,\varepsilon+O(\varepsilon/K)$。

**$\kappa$ 的每一项都可以计算：**

- $s=\sqrt{\lambda_0/2}$：由 Lyapunov 方程从闭环参数算出（命题 1.1）。
- $\bar u\approx\sqrt{2\log N}$：由第 5 节的 Gumbel 渐近给出，$N=\sum_jL_j s'/(2\pi s)$。
- $\Delta$：配对行对的**确定性均值偏移**，由 DEM 算出。在 A1 和积分作用下，均值偏移主要来自侧倾天线偏置：
$$\Delta_j\le\tfrac12h_{\rm ant}(1-c_{\min})\,\sup_x\big|\Delta g^{(1)}_{y,j}(x)-\Delta g^{(0)}_{y,j}(x)\big|,$$
  其中 $\Delta g_{y,j}$ 是行对两条行的横坡差。另外加上 GNSS 时刻错位造成的 $\sup|\varepsilon(\tau^{(1)})-\varepsilon(\tau^{(0)})|$，它可以由 CORS 误差序列的连续性模给出上界。

**平地特例。** 地形均匀时 $\Delta=0$，$\kappa=1$，严格得到 $P(\text{漏})\le\varepsilon+O(\varepsilon/K)$。原来的定理 2 由此成为本定理的推论，误差项也是显式的。

**放大余量的代价（效率端）。** 同样由定理 4.1，参考计划多出 $a$ 个行对时：
$$F_{\pi_1}(t)-F_{\pi_0}(t)\le\mathbb E_C\Big[e^{-M_{\pi_1}}\big(1-e^{-\sum_{\rm 多出}\mu_j}\big)\Big]+O(\cdot)\le\frac{a}{K}\,\mathbb E_C\big[M e^{-M}\big]\cdot\frac{K}{|J(\pi_0)|}+O(\cdot).$$
这是命题 5.4 的严格版本：分母上不再是估计出来的极值指数，而是可以计算的 $\mathbb E[Me^{-M}]$。

---

## 5. 第五层：Gumbel 渐近、规模律与跨田块枢轴

**定理 5.1（给定条件下的 Gumbel 极限）。** 设 $C$ 固定，各行对均值为常数 $m$ 并进入稳态，记有效长度
$$N=\frac{s'}{2\pi s}\sum_jL_j=\frac{s'}{2\pi s}\cdot\frac{K\,\bar L}{1},$$
即田块面积除以行距，再乘以误差的"每米独立次数"。当 $N\to\infty$ 时，由定理 2.1–3.2 和 Cramér–Leadbetter 关于连续参数平稳高斯过程上确界的结果（Leadbetter, Lindgren & Rootzén 1983，定理 8.2.7）：
$$P\Big(a_N\big(\tfrac{U-m}{s}-a_N\big)\le z\ \Big|\ C\Big)\ \to\ \exp(-e^{-z}),\qquad a_N=\sqrt{2\log N}.$$

**推论 5.2（所需余量的规模律）。**
$$t_\varepsilon(C)=m+s\Big[a_N-\frac{\log(-\log(1-\varepsilon))}{a_N}\Big]+o\big(s/a_N\big).$$

**含义。**

- 所需余量随田块规模只以 $\sqrt{2\log N}$ 增长。面积扩大 10 倍，在 $N\sim10^3$ 时余量只增加约 $\sqrt{2\log10^4}/\sqrt{2\log10^3}-1\approx15\%$。
- 主要由每次作业的噪声尺度 $s(C)$ 决定。这给 CE+ 的 XTE 归一化提供了理论依据：地头探测行的 XTE 是 $s(C)$ 的含噪读数，用它归一化正是在消掉 Gumbel 尺度参数。

**定理 5.3（跨田块枢轴与分层共形）。** 定义归一化分数
$$\tilde U=a_{\hat N}\Big(\frac{U-\hat m}{\hat s}-a_{\hat N}\Big),$$
其中 $\hat s,\hat N$ 由计划和训练数据（Lyapunov 参数、XTE 探测）计算，与校准、测试作业无关。

1. **有效性（不依赖枢轴性）：** 田块从同一总体独立抽取、每块田只用一次作业时，各田的 $(\tilde U_i)$ 可交换。在 $F$ 块田上做分割共形，对新田块有
$$P(\text{漏})\ge1-\varepsilon.$$
这就是 Dunn、Wasserman 和 Ramdas（2022）的两层模型，每组抽一个。
2. **逐田准确性（来自枢轴性）：** 由定理 5.1，不同田块的 $\tilde U$ 逐渐趋于同一个 Gumbel 分布。正态极值的收敛速度是 $O(1/\log N)$（Hall 1979）。因此对每块田，条件覆盖率与 $1-\varepsilon$ 的偏差为 $O(1/\log N_{\min})$，再加上 $\hat s$ 的估计误差项。

**意义。** 这回答了"每块田 100 次在田校准不现实"的质疑。在理论上，只需要许多田块各一次历史作业，而一个农场或合作社正好有这样的数据。

---

## 6. 数值检验（`scripts/check_evt.py`，本机几分钟）

| 编号 | 检验内容 | 理论来源 |
|---|---|---|
| E1 | 给定 $C$，用大量作业的样本方差检验 Lyapunov 预测的 $s$ 和 $s'/s$ | 命题 1.1 |
| E2 | 给定 $C$，单行对的经验超限概率 $\hat\mu_j(t)$ 与 Rice 上界 $\bar\mu_j(t)$ 比较，$u\approx2$–$4$ | 定理 2.1、命题 2.2 |
| E3 | 给定 $C$，经验 $P(U\le t)$ 与 $e^{-\sum\hat\mu_j}$ 比较，误差应 $\le5\hat\mu_{\max}$ | 定理 3.2 |
| E4 | 单行自协方差是否非负 | 假设 A2 |
| E5 | 条件随作业变化时，经验 $\theta_t$ 与 $\mathbb E[1-e^{-M}]/\mathbb E[M]$ 比较 | 推论 4.2 |
| E6 | 不同面积田块上 $t_\varepsilon$ 与 $\sqrt{2\log N}$ 的线性关系 | 推论 5.2 |

## 7. 本理论在论文中的位置

- **定理 4.3** 取代原定理 2 的平移等变假设：决策依赖的影响被量化为闭式放大因子 $\kappa$，平地上 $\kappa=1$。
- **推论 5.2** 给出所需余量的规模律，并为 XTE 自适应提供理论解释。
- **定理 5.3** 给出跨田块校准，回应"在田校准次数不现实"的质疑。
- 用到的工具：Lyapunov 方程、Kac–Rice 公式、Slepian 不等式、Chen–Stein 方法、Cramér–Leadbetter 极值理论、分层共形。它们构成一个从控制系统到共形保证的完整链条，每一层都有数值检验。

## 8. 假设的边界（如实说明）

- **A1（线性工作区）**：转向饱和、速率限制或大角度会破坏条件高斯性。RTK 工况下很少触发；DGPS 的大误差下需要检验。
- **A2（自协方差非负）**：只在过阻尼闭环下成立，需要数值检查。若不成立，引理 3.1 改用 $b_2\le2\sum\min(\mu_j,\mu_{j+1})$，界会变松。
- **GNSS 误差的处理**：整条 GNSS 轨迹被放进条件 $C$，因此 GNSS 的重尾和错误固定只影响均值 $m_j$，不破坏条件高斯性。但定理 4.3 中 $\Delta$ 的 GNSS 部分需要误差序列的连续性模，在 DGPS 下可能偏大。
- 定理 5.1 是渐近结论。实际行对数 $K\sim10$–$150$，有限样本误差要靠 E6 检验。

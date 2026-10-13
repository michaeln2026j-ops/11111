# 在 AutoDL 上运行全部实验

这些实验是**纯 CPU 计算**（numpy 仿真），不需要 GPU。选机器时看 **CPU 核数**和内存，GPU 型号无所谓。

## 1. 租机器（需要你本人在网页上操作）

1. 打开 https://www.autodl.com ，注册或登录，然后充值。
2. 进入「算力市场」，按 **CPU 核数**筛选或排序。
   - 建议 **≥ 32 核、≥ 64 GB 内存**。
   - 有的机器每张 GPU 只配少量 CPU 核，以页面上显示的 CPU 数为准。
   - 价格和配置以页面为准。
3. 镜像选任意带 Python ≥ 3.10 的基础镜像，例如 Miniconda 或 PyTorch 基础镜像。
4. 开机后，用 JupyterLab 的终端，或页面给出的 SSH 命令登录。

> 账号密码、SSH 密码请不要发给我。这个会话没法主动连接你的服务器，所以由你在服务器上跑，我这边负责分析结果。

## 2. 拉代码、装依赖

```bash
# 如果 GitHub 访问慢，可以先打开 AutoDL 的学术资源加速（具体以 AutoDL 帮助文档为准）：
# source /etc/network_turbo
git clone -b claude/quirky-fermat-nr94ww https://github.com/michaeln2026j-ops/11111.git
cd 11111
pip install -r requirements.txt
```

仓库是私有的：clone 时用户名填 GitHub 用户名，密码处填 GitHub Personal Access Token（勾选 repo 权限）。

## 3. 一键运行

```bash
JOBS=$(nproc) nohup bash scripts/run_all.sh > run_all.log 2>&1 &
tail -f run_all.log          # 查看进度；各任务的日志在 results/logs/
```

- `scripts/run_all.sh` 会把主实验、扫描实验、消融实验按田块切成分片，同时运行 JOBS 个进程。
- 每个进程只用 1 个核（已设置 `OMP_NUM_THREADS=1`）。
- 关闭终端或断开 SSH 不影响运行，因为用了 nohup。

## 4. 合并结果并推回 GitHub

```bash
python3 scripts/merge_shards.py
python3 experiments/make_tables.py
git add results && git commit -m "Run results from AutoDL" && git push origin claude/quirky-fermat-nr94ww
```

推上来之后，告诉我一声，我会拉取结果、出图并更新报告。

## 5. 预计耗时（粗略）

| 机器 | 全部实验 |
|---|---|
| 4 核（当前云会话） | 约 10 小时以上 |
| 32 核 | 约 1.5–2 小时 |
| 64 核 | 约 1 小时 |

系统级对比实验 `exp_system.py` 会在基线算法审查完成后推送到同一分支。届时 `git pull` 后重新运行 `scripts/run_all.sh` 即可：脚本会自动带上它，其他实验也会重跑一遍。

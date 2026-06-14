# 定时自动化 — Shell + launchd

本指南说明如何用 **纯 shell 脚本 + macOS launchd** 自动跑 M1/M2 联调与 day/week/month 报表，**不依赖 Cursor**。

---

## 1. 脚本一览

| 脚本 | 作用 | 何时跑 |
|------|------|--------|
| `scripts/daily_run.sh` | M1 `make check` + M2 5 策略 paper + EOD snapshot + sync + **日报** | 建议港股收盘后 |
| `scripts/weekly_report.sh` | sync（若 OpenD 在线）+ **周报** | 建议周日 |
| `scripts/monthly_report.sh` | sync（若 OpenD 在线）+ **月报** | 建议每月 1 日 |
| `scripts/install_launchd.sh` | 安装/卸载 launchd 定时任务 | 一次性 |

共享逻辑：`scripts/lib/common.sh`

---

## 2. 前置条件

| # | 项目 |
|---|------|
| 1 | `make install-dev` 已完成 |
| 2 | `config/settings.yaml` 存在（含 `journal.enabled: true`） |
| 3 | **Futu OpenD** 已启动并登录（`daily_run.sh` 必需） |
| 4 | Mac 在计划时间 **开机且未睡眠**（或允许唤醒） |
| 5 | 建议 macOS 时区设为 **Asia/Hong_Kong**（与 journal 一致） |

---

## 3. 手动试运行

```bash
cd "/Users/pkwok/Projects/20. Algo/myAlgo2"

# 赋予执行权限（首次）
chmod +x scripts/daily_run.sh scripts/weekly_report.sh scripts/monthly_report.sh scripts/install_launchd.sh

# 完整日流程（M1 + M2 + journal + day report）
./scripts/daily_run.sh

# 跳过单元测试（更快，仅验证 OpenD 路径）
SKIP_M1=1 ./scripts/daily_run.sh

# 周报 / 月报（不跑策略，只读 journal）
./scripts/weekly_report.sh
./scripts/monthly_report.sh
```

### 日志位置

| 路径 | 内容 |
|------|------|
| `logs/daily_run_YYYYMMDD_HHMMSS.log` | 每次 daily 运行详细日志 |
| `logs/reports/report_day_YYYYMMDD.json` | 日报 JSON 归档 |
| `logs/reports/report_week_YYYYMMDD.json` | 周报 JSON |
| `logs/reports/report_month_YYYYMMDD.json` | 月报 JSON |
| `logs/launchd-*.stdout.log` | launchd 外层 stdout |

终端只会看到很少输出；**详细内容在 log 文件**。

---

## 4. daily_run.sh 做了什么

```
1. 检查 .venv、settings.yaml、OpenD :11111
2. M1 — make check（lint + pytest + compile）
3. M2 — status.py --market HK
4. M2 — 5 个 Tier 1 策略各 run_paper.py --once
5. snapshot_account.py --type eod
6. sync_fills.py
7. report.py --period day（终端 + JSON）
```

策略列表在 `scripts/lib/common.sh` 的 `TIER1_STRATEGIES`，与 `registry.py` 保持一致。

---

## 5. 安装 launchd（推荐）

```bash
cd "/Users/pkwok/Projects/20. Algo/myAlgo2"
chmod +x scripts/install_launchd.sh
./scripts/install_launchd.sh
```

### 默认时间表（macOS **本地时区**）

| Job | 时间 | 脚本 |
|-----|------|------|
| `com.myalgo2.daily` | **周一至五 16:30** | `daily_run.sh` |
| `com.myalgo2.weekly-report` | **周日 18:00** | `weekly_report.sh` |
| `com.myalgo2.monthly-report` | **每月 1 日 09:00** | `monthly_report.sh` |

> 16:30 HKT ≈ 港股收盘后，适合日 K 策略与 EOD snapshot。

### 卸载

```bash
./scripts/install_launchd.sh uninstall
```

### 修改时间

编辑安装后的 plist（路径含你的项目根目录）：

```text
~/Library/LaunchAgents/com.myalgo2.daily.plist
~/Library/LaunchAgents/com.myalgo2.weekly-report.plist
~/Library/LaunchAgents/com.myalgo2.monthly-report.plist
```

改完后：

```bash
launchctl bootout "gui/$(id -u)/com.myalgo2.daily" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.myalgo2.daily.plist
```

（weekly / monthly 同理，替换 label。）

### 查看是否加载

```bash
launchctl list | grep myalgo2
```

期望输出三行（第一列 `-` 表示当前未在跑，正常）：

```text
-  0  com.myalgo2.daily
-  0  com.myalgo2.weekly-report
-  0  com.myalgo2.monthly-report
```

| 列 | 含义 |
|----|------|
| 第 1 列 | PID；`-` = 未运行 |
| 第 2 列 | 上次退出码；`0` = 成功 |
| 第 3 列 | Label |

详细日志在 `logs/daily_run_*.log`（成功时 stdout 可能被重定向到该文件）。

### 立即触发一次（测试 launchd）

```bash
launchctl kickstart -k "gui/$(id -u)/com.myalgo2.daily"
```

---

## 6. Makefile 快捷命令

```bash
make daily-run       # ./scripts/daily_run.sh
make weekly-report   # ./scripts/weekly_report.sh
make monthly-report  # ./scripts/monthly_report.sh
make install-scheduler   # ./scripts/install_launchd.sh
make uninstall-scheduler # ./scripts/install_launchd.sh uninstall
```

---

## 7. OpenD 开机自启

launchd 只负责 **到点跑脚本**；OpenD 需你自行保证在线：

1. 将 Futu OpenD 加入 macOS **登录项**
2. 或登录后手动启动 OpenD
3. `daily_run.sh` 若检测不到 `:11111` 会 **失败退出** 并写 log

周报/月报在 OpenD 离线时仍会跑，但会 **跳过 sync_fills**（仅用本地 journal）。

---

## 8. 故障排查

| 现象 | 处理 |
|------|------|
| `OpenD not listening` | 启动 OpenD 并登录 Futu HK |
| `.venv not found` | `make install-dev` |
| `settings.yaml missing` | `cp config/settings.example.yaml config/settings.yaml` |
| launchd 报 OpenD 未启动但终端可连 | launchd PATH 缺 `/usr/sbin`；已修复于 plist 与 `common.sh`，重新 `make install-scheduler` |
| kickstart 后无新 log | 看 `logs/launchd-daily.stderr.log`；确认 OpenD 在线 |
| make check 太慢 | 日常用 `SKIP_M1=1 ./scripts/daily_run.sh`；M1 仍可由 GitHub Actions 覆盖 |
| 报表 Return 0% | 无成交/无资产变化，见 [TESTING.md Phase H](TESTING.md#phase-h--交易日志与绩效报表journal) |

---

## 9. 与 TESTING.md 对应关系

| TESTING Phase | daily_run | weekly/monthly |
|---------------|-----------|----------------|
| A (make check) | ✅ | — |
| B (status) | ✅ | — |
| C (日 K paper) | ✅ | — |
| H (snapshot/sync/report) | day | week / month |

Phase D–G 未纳入定时任务；需要时手动跑。

---

## 10. 相关文档

| 文档 | 内容 |
|------|------|
| [TESTING.md](TESTING.md) | 逐步验收 |
| [README.md](../README.md) | Journal 与快速开始 |
| [TASKS.md](../TASKS.md) | 里程碑 |

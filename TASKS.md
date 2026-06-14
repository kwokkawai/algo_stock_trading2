# TASKS — 项目任务看板

> **Agent 须知：** 开始任务前读此文件；完成任务后更新状态并运行 `make check`。
>
> 图例：⬜ 待办 | 🔄 进行中 | ✅ 完成 | ⏸ 阻塞

**当前阶段：** M2 + Journal + Automation 完成 → **M3 Intraday + 风控**

---

## 里程碑总览

| 里程碑 | 目标 | 状态 |
|--------|------|------|
| **M1** | Scaffold + Skills + 文档 + CI 骨架 | ✅ |
| **M2** | 日 K Runner + SMA + 模拟盘联调 | ✅ |
| **M3** | 1m intraday Runner + Risk Guard 验证 | ⬜ |
| **M4** | Tick Runner + 频率风控 | ⬜ |
| **M5** | 实盘路径 + 可观测性 | 🔄 |
| **M6** | 回测模块（Phase 2） | ⬜ |
| **M7** | Web UI（Phase 2） | ⬜ |

---

## M2 — 模拟盘联调 ✅

| ID | 任务 | 状态 | 负责人 | 备注 |
|----|------|------|--------|------|
| M2-1 | 安装 OpenD，复制 `config/settings.yaml` | ✅ | User | OpenD 127.0.0.1:11111 |
| M2-2 | `pip install -r requirements.txt` + `make install-dev` | ✅ | Agent | .venv 已就绪 |
| M2-3 | `run_paper.py --once` 连接 OpenD 成功 | ✅ | Agent | quote + trade context OK |
| M2-4 | SMA 策略产生信号并模拟下单 | ✅ | Agent | 模拟买单 order_id=7783826；最新 K 无交叉时不信号属正常 |
| M2-5 | `status.py` 显示账户与持仓 | ✅ | Agent | 模拟账户 1,000,000 HKD |
| M2-6 | 修复联调中发现的问题 | ✅ | Agent | 见 Changelog |

---

## M3 — Intraday + 风控

| ID | 任务 | 状态 |
|----|------|------|
| M3-1 | 1m bar feed 在交易时段稳定 polling | ⬜ |
| M3-2 | Risk Guard 白名单 / 单笔上限实测 | ⬜ |
| M3-3 | 冷却时间与重复信号去重 | ⬜ |
| M3-4 | 补充 risk 相关单元测试 | ⬜ |

---

## M4 — Tick

| ID | 任务 | 状态 |
|----|------|------|
| M4-1 | 实现 tick 示例策略 scaffold | ⬜ |
| M4-2 | `run_tick.py` 独立进程联调 | ⬜ |
| M4-3 | tick_max_orders_per_minute 实测 | ⬜ |

---

## M5 — 实盘与可观测性

| ID | 任务 | 状态 |
|----|------|------|
| M5-1 | `run_live.py --confirm` 端到端验证 | ⬜ |
| M5-2 | 结构化 JSON 日志 | 🔄 |
| M5-2a | SQLite journal + report/sync/snapshot CLI | ✅ |
| M5-3 | 订单失败告警（日志级别 / 可选 webhook） | ⬜ |

---

## 基础设施（持续）

| ID | 任务 | 状态 |
|----|------|------|
| INF-1 | GitHub Actions CI（lint + test） | ✅ |
| INF-2 | Cursor Rules + AGENTS.md | ✅ |
| INF-3 | 安全 Hooks（拦截危险实盘命令） | ✅ |
| INF-4 | 初始化 git remote 并 push | ✅ |
| INF-5 | PR template + branch protection 建议 | ✅ |
| INF-6 | Shell + launchd 定时自动化 | ✅ |

---

## Next（Agent 优先处理）

1. 用户按 [docs/TESTING.md](docs/TESTING.md) Phase A–H 验收
2. 定时任务：`launchctl list | grep myalgo2` 确认已加载（见 [docs/AUTOMATION.md](docs/AUTOMATION.md)）
3. **M3-1** — 交易时段跑 `run_paper.py --mode intraday --data 1m --once`
4. **M3-2** — 验证 Risk Guard 白名单与 notional 上限

---

## Changelog

| 日期 | 变更 |
|------|------|
| 2026-06-14 | M1 scaffold：代码、Skills、README、PRD |
| 2026-06-14 | 添加 AGENTS.md、TASKS.md、CI、Cursor Rules/Hooks |
| 2026-06-14 | INF-4: push 至 github.com/kwokkawai/algo_stock_trading2 |
| 2026-06-14 | M2 联调：修复 config ROOT 路径；K 线仅对最新 bar 下单；无持仓拒绝 SELL；notional 上限 100k；status.py 无需 --strategy |
| 2026-06-14 | **第一梯队策略**：ema_crossover、donchian_breakout、bollinger_rsi、momentum_rotation + indicators + 单元测试；STRATEGY_GUIDE 第 2 节 |
| 2026-06-14 | **M5 journal**：SQLite 交易日志、Futu 订单/成交同步、日终 snapshot、report.py 日/周/月报表 |
| 2026-06-14 | **Automation**：daily_run / weekly_report / monthly_report + launchd + docs/AUTOMATION.md；launchd PATH 修复 |

---

## 如何添加新任务

Agent 或 User 发现新需求时：

1. 在对应里程碑表格加一行（ID 递增）
2. 若属 Phase 2，放 M6/M7 或新建里程碑
3. 在 PRD.md 同步功能 ID（如有）

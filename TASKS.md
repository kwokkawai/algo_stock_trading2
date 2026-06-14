# TASKS — 项目任务看板

> **Agent 须知：** 开始任务前读此文件；完成任务后更新状态并运行 `make check`。
>
> 图例：⬜ 待办 | 🔄 进行中 | ✅ 完成 | ⏸ 阻塞

**当前阶段：** M1 完成 scaffold → **M2 模拟盘联调**

---

## 里程碑总览

| 里程碑 | 目标 | 状态 |
|--------|------|------|
| **M1** | Scaffold + Skills + 文档 + CI 骨架 | ✅ |
| **M2** | 日 K Runner + SMA + 模拟盘联调 | 🔄 |
| **M3** | 1m intraday Runner + Risk Guard 验证 | ⬜ |
| **M4** | Tick Runner + 频率风控 | ⬜ |
| **M5** | 实盘路径 + 结构化日志 | ⬜ |
| **M6** | 回测模块（Phase 2） | ⬜ |
| **M7** | Web UI（Phase 2） | ⬜ |

---

## M2 — 模拟盘联调（当前）

| ID | 任务 | 状态 | 负责人 | 备注 |
|----|------|------|--------|------|
| M2-1 | 安装 OpenD，复制 `config/settings.yaml` | ⬜ | User | 需 Futu HK 登录 |
| M2-2 | `pip install -r requirements.txt` + `make install-dev` | ⬜ | User/Agent | |
| M2-3 | `run_paper.py --once` 连接 OpenD 成功 | ⬜ | Agent | 验证 quote + trade context |
| M2-4 | SMA 策略产生信号并模拟下单 | ⬜ | Agent | 检查 order_id 日志 |
| M2-5 | `status.py` 显示账户与持仓 | ⬜ | Agent | |
| M2-6 | 修复联调中发现的问题 | ⬜ | Agent | |

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
| M5-2 | 结构化 JSON 日志 | ⬜ |
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

---

## Next（Agent 优先处理）

1. **M2-1 ~ M2-3** — 用户准备 OpenD 后，Agent 协助跑通 `--once` 模拟盘
2. 联调问题记录在此文件底部 **Changelog**

---

## Changelog

| 日期 | 变更 |
|------|------|
| 2026-06-14 | M1 scaffold：代码、Skills、README、PRD |
| 2026-06-14 | 添加 AGENTS.md、TASKS.md、CI、Cursor Rules/Hooks |
| 2026-06-14 | INF-4: push 至 github.com/kwokkawai/algo_stock_trading2 |

---

## 如何添加新任务

Agent 或 User 发现新需求时：

1. 在对应里程碑表格加一行（ID 递增）
2. 若属 Phase 2，放 M6/M7 或新建里程碑
3. 在 PRD.md 同步功能 ID（如有）

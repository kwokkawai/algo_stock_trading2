# AGENTS.md — Cursor Agent 指南

本文件是 Cursor Agent 的**项目级入口**。开始任何任务前请先读此文件，再按需加载 Skills 与 Rules。

## 项目是什么

**myAlgo2** 是基于 Futu HK OpenAPI 的港美股算法交易系统。策略与执行分离，Phase 1 为 CLI。

| 文档 | 用途 |
|------|------|
| [README.md](README.md) | 快速开始、架构概览 |
| [PRD.md](PRD.md) | 功能需求、接口契约 |
| [TASKS.md](TASKS.md) | **当前任务看板**（完成工作后必须更新） |

## Agent 分工

| 场景 | 使用 Skill | 可改文件 |
|------|-----------|----------|
| Futu 下单、OpenD、持仓查询 | `futu-order-execution` | `src/broker/`, `scripts/run_live.py`, `scripts/status.py` |
| 策略、指标、算法 | `algo-strategy` | `src/strategies/`, `config/strategies/`, `src/strategy/registry.py` |
| CI/CD、测试、发布 | `ci-cd` | `.github/`, `tests/`, `pyproject.toml`, `Makefile` |
| 里程碑推进、任务更新 | `project-evolution` | `TASKS.md`, `PRD.md` 里程碑勾选 |

## 架构边界（必须遵守）

```
src/strategies/     ← LLM 主要改这里（策略）
src/strategy/       ← 策略框架（谨慎改）
src/data/           ← 行情 feed（谨慎改）
src/engine/         ← 调度（谨慎改）
src/risk/           ← 风控（不改，除非用户明确要求）
src/broker/         ← 执行层（不改策略逻辑）
config/settings.yaml ← 本地密钥，不进 Git
```

**禁止：** 策略代码直接调用 Futu API；运行 `run_live.py`；使用 `--env real`；在未获用户明确许可时设置 `paper_only: false`；提交含密码的配置。

## 模拟盘强制策略（Paper Only）

**当前策略：所有交易必须走 Futu 模拟盘，直到用户明确说「切换实盘」。**

| 机制 | 说明 |
|------|------|
| `config/settings.yaml` | `trading.paper_only: true`（硬锁） |
| `src/trading_policy.py` | 强制 `TrdEnv.SIMULATE`，拒绝 real |
| `run_paper.py` / `run_tick.py` | 唯一允许的下单入口 |
| `run_live.py` | `paper_only` 为 true 时直接 BLOCKED |
| Cursor Hook | 拦截 `run_live.py` 与 `--env real` |

**Agent 不得：** 改 `paper_only: false`、运行 `run_live.py`、或绕过 policy 下单。

**用户切换实盘时（仅当其明确指示）：** 将 `config/settings.yaml` 中 `paper_only: false`，然后才可用 `run_live.py --confirm`。

## 标准工作流

1. **读 TASKS.md** — 确认当前里程碑与 in-progress 任务
2. **小步改动** — 一次 PR / 一次会话聚焦一个任务 ID（如 M2-3）
3. **本地验证** — `make check`（lint + test）
4. **更新 TASKS.md** — 完成后移动 checkbox 并注明日期
5. **模拟盘优先** — 任何涉及下单的改动先在 `TrdEnv.SIMULATE` 验证

## 常用命令

```bash
make install-dev    # 创建 .venv + 安装开发依赖
make check          # lint + test（CI 同款）
make test           # pytest
make lint           # ruff

# 模拟盘单次运行
.venv/bin/python scripts/run_paper.py --strategy sma_crossover --mode daily --market HK --once
```

## CI/CD

- GitHub Actions: `.github/workflows/ci.yml`
- 每次 push/PR 自动跑 lint + unit tests
- Futu/OpenD 集成测试不在 CI 中运行（需本地 OpenD）
- 合并前：`make check` 必须通过

## 任务 ID 命名

与 [TASKS.md](TASKS.md) 一致：`M{里程碑}-{序号}`，例如 `M2-1`。

## 进化原则

Agent 协助演进项目时：

1. 优先完成 TASKS 中 **Next** 列的任务
2. 新功能先更新 PRD/TASKS，再写代码
3. 新策略必须：py 文件 + yaml 配置 + registry 注册 + 单元测试
4. 不扩大 scope（不加 Web UI、回测除非 TASKS 明确要求）

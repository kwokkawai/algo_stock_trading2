# myAlgo2 — 港美股算法交易 Agent

基于 [Futu OpenAPI](https://openapi.futunn.com/futu-api-doc/) 的模块化算法交易系统，支持香港与美国股票市场。策略与执行分离，便于根据不同 LLM 的建议快速迭代算法，而不影响稳定的下单通道。

**账户类型：** Futu HK（`FUTUSECURITIES`）Universal Securities Account  
**Phase 1：** CLI only（无 Web UI）

## 架构概览

```
LLM / 策略 Agent  →  Strategy (signals)  →  Engine + Risk  →  Futu Broker  →  OpenD  →  交易所
                              ↑
                    Data Layer (1d / 1m / tick)
```

| 组件 | 说明 |
|------|------|
| **Strategy Layer** | 可插拔策略，声明数据订阅，输出买卖信号（LLM 主要修改区域） |
| **Data Layer** | 统一 Futu 行情订阅，支持日 K、1 分钟、Tick |
| **Engine** | 按粒度调度策略、聚合信号、调用风控 |
| **Risk Guard** | 仓位、亏损、标的白名单、Tick 频率限制 |
| **Futu Broker** | 封装 futu-api，Futu HK 港/美股下单 |
| **Cursor Skills** | `futu-order-execution` 与 `algo-strategy` 两个 Agent 分工 |

## 前置条件

1. 安装并登录 [Futu OpenD](https://www.futunn.com/download/openAPI)
2. Python 3.10+
3. Futu HK 证券账户（Universal Account，支持港美股）
4. 安装依赖：`pip install -r requirements.txt`

## 快速开始

```bash
# 1. 启动 OpenD 并登录 Futu HK 账户

# 2. 创建虚拟环境并安装依赖
python3 -m venv .venv
make install-dev

# 3. 复制并编辑配置
cp config/settings.example.yaml config/settings.yaml

# 4. 验证 CI（可选）
make check

# 5. 模拟盘 — 日 K 策略
.venv/bin/python scripts/run_paper.py --strategy sma_crossover --mode daily --market HK --once

# 5. 模拟盘 — 1 分钟策略
python scripts/run_paper.py --strategy sma_crossover --mode intraday --market HK --data 1m

# 6. 查看账户状态
python scripts/status.py --market HK
```

## 支持市场

| 市场 | 代码格式 | 示例 | TrdMarket |
|------|----------|------|-----------|
| 香港 | `HK.{5位代码}` | `HK.00700` | `HK` |
| 美国 | `US.{Ticker}` | `US.AAPL` | `US` |

多标的 watchlist 配置见 [docs/WATCHLIST.md](docs/WATCHLIST.md)（策略 `symbols` + 风控白名单两处）。

## 行情粒度

策略通过 `DataSubscription` 声明所需数据，Engine 自动合并订阅：

| 粒度 | 策略方法 | Runner 模式 | 脚本 |
|------|----------|-------------|------|
| 日 K | `on_bar(bar, "1d")` | `daily` | `run_paper.py --mode daily` |
| 1 分钟 | `on_bar(bar, "1m")` | `intraday` | `run_paper.py --mode intraday` |
| Tick | `on_tick(tick)` | `tick` | `run_tick.py`（独立进程） |

Tick 策略使用独立 runner，并启用更严格的风控（冷却时间、每分钟最大订单数）。

## 如何修改策略（LLM 工作流）

1. 在 `src/strategies/` 新建或修改策略，继承 `BaseStrategy`
2. 声明 `subscription: DataSubscription(...)`
3. 在 `config/strategies/` 添加 YAML 参数
4. 在 `src/strategy/registry.py` 注册策略名
5. 使用 **algo-strategy** Skill 的 Agent 协助实现与审查
6. 先在模拟盘验证：`python scripts/run_paper.py --strategy <name> --mode daily`
7. 确认风控参数后，才切换实盘

**LLM 可改：** `src/strategies/`、`config/strategies/`  
**LLM 不应改：** `src/broker/`、`src/risk/`、`src/engine/`

## Cursor Agent Skills

| Skill | 路径 | 用途 |
|-------|------|------|
| `futu-order-execution` | `.cursor/skills/futu-order-execution/` | OpenD 连接、下单、查持仓、Futu HK 配置 |
| `algo-strategy` | `.cursor/skills/algo-strategy/` | 实现/修改策略、对接 Signal 接口 |

在对话中提及「Futu 下单」「改策略」「SMA 交叉」等关键词时，Agent 会加载对应 Skill。

## CLI 命令

```bash
# 模拟盘（默认）
python scripts/run_paper.py --strategy sma_crossover --mode daily --market HK

# 1 分钟 intraday
python scripts/run_paper.py --strategy sma_crossover --mode intraday --data 1m

# Tick 策略（独立 runner）
python scripts/run_tick.py --strategy <tick_strategy> --market HK

# 查状态
python scripts/status.py --market HK

# 实盘（仅 paper_only: false 后可用）
# python scripts/run_live.py --strategy sma_crossover --mode daily --market HK --confirm
```

## 配置

| 文件 | 说明 |
|------|------|
| `config/settings.example.yaml` | 配置模板（复制为 `settings.yaml`） |
| `config/strategies/*.yaml` | 各策略参数 |
| 环境变量 `FUTU_TRADE_PASSWORD` | 实盘交易解锁密码（不进 Git） |

## 安全须知

- 交易密码通过环境变量 `FUTU_TRADE_PASSWORD` 传入，不要提交到 Git
- 默认 **模拟盘**（`TrdEnv.SIMULATE`）且 **`paper_only: true` 硬锁**
- 所有下单请用 `run_paper.py` / `run_tick.py`；`run_live.py` 在 paper_only 开启时会被拒绝
- 切换实盘：须你明确指示后，将 `config/settings.yaml` 中 `paper_only: false`
- 生产环境务必配置 Risk Guard 熔断参数
- Tick 策略受 `tick_max_orders_per_minute` 和 `signal_cooldown_seconds` 限制

## 项目结构

```
myAlgo2/
├── README.md
├── PRD.md
├── .cursor/skills/          # Cursor Agent Skills
├── config/                  # 配置（settings.yaml gitignored）
├── scripts/                 # CLI 入口
└── src/
    ├── models/              # Signal, Order, Bar, Tick
    ├── data/                # 行情订阅与 feed
    ├── broker/              # Futu 执行层
    ├── strategy/            # BaseStrategy + registry
    ├── strategies/          # ← LLM 主要改这里
    ├── risk/                # 风控
    └── engine/              # Runner 调度
```

详细功能设计见 [PRD.md](./PRD.md)。

## Cursor 协作（Agent / CI/CD）

| 文件 | 用途 |
|------|------|
| [AGENTS.md](./AGENTS.md) | Agent 入口：架构边界、工作流、常用命令 |
| [TASKS.md](./TASKS.md) | **任务看板** — 里程碑、当前 Next 任务 |
| `.cursor/rules/` | 自动加载的项目规则（策略层 / 执行层 / CI） |
| `.cursor/skills/` | 专用 Skills（执行、策略、CI/CD、项目演进） |
| `.cursor/hooks/` | 安全 Hook（拦截危险实盘命令） |

```bash
make install-dev   # 开发依赖
make check         # 本地 CI（与 GitHub Actions 一致）
```

GitHub Actions：push/PR 时自动跑 lint + unit tests（见 `.github/workflows/ci.yml`）。

**功能测试：** 逐步验证模拟盘、策略、风控，见 [docs/TESTING.md](docs/TESTING.md)。

**策略说明：** 第一梯队 5 个日 K 策略（SMA/EMA/Donchian/Bollinger+RSI/动量轮动），见 [docs/STRATEGY_GUIDE.md](docs/STRATEGY_GUIDE.md)。

**Watchlist：** 添加多只股票，见 [docs/WATCHLIST.md](docs/WATCHLIST.md)。

**绩效分析：** SQLite 交易日志与日/周/月报表，见下方「Journal」一节。

## Journal（交易日志与绩效）

所有 `run_paper.py` 运行会自动写入 SQLite（`data/journal/trades.db`），记录信号、风控拒绝、下单与账户快照。

```bash
# 日终手动 snapshot（建议收盘后 cron）
.venv/bin/python scripts/snapshot_account.py --type eod --market HK

# 从 Futu 同步订单/成交
.venv/bin/python scripts/sync_fills.py

# 日 / 周 / 月 报表
.venv/bin/python scripts/report.py --period day
.venv/bin/python scripts/report.py --period week --strategy sma_crossover
.venv/bin/python scripts/report.py --period month --export json
```

配置见 `config/settings.yaml` → `journal:` 段。

**定时自动化（shell + launchd）：** 自动跑 M1/M2 与日/周/月报表，见 [docs/AUTOMATION.md](docs/AUTOMATION.md)。

```bash
make daily-run          # 手动跑完整日流程
make install-scheduler  # 安装 macOS 定时任务
```

## 路线图

- [x] 项目 scaffold + Skills + 文档
- [x] Cursor 协作（AGENTS.md、TASKS.md、Rules、Hooks、CI）
- [x] Futu Broker 模拟盘联调（M2）
- [x] 第一梯队 5 策略 + Journal + 日/周/月报表
- [x] Shell + launchd 定时自动化
- [ ] 1m intraday Runner 联调（M3）
- [ ] Tick Runner + 频率风控（M4）
- [ ] 实盘路径 + 结构化 JSON 日志（M5 剩余）
- [ ] 回测模块（Phase 2）
- [ ] Web UI（Phase 2）

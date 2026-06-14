# 功能测试指南 — myAlgo2

逐步验证当前已实现的能力。**所有交易测试均在 Futu 模拟盘（paper account）进行**，除非你日后明确关闭 `paper_only`。

---

## 测试前准备（一次性）

### 清单

| # | 项目 | 如何确认 |
|---|------|----------|
| 1 | Python 3.10+ | `python3 --version` |
| 2 | 项目目录 | `cd "/Users/pkwok/Projects/20. Algo/myAlgo2"` |
| 3 | 虚拟环境 | `make install-dev` |
| 4 | 本地配置 | `config/settings.yaml` 存在（从 example 复制） |
| 5 | Futu OpenD | 已启动并登录 **Futu HK** |
| 6 | OpenD 端口 | `lsof -i :11111` 有 `Futu_Open` 监听 |

### 初始化命令

```bash
cd "/Users/pkwok/Projects/20. Algo/myAlgo2"

# 虚拟环境 + 依赖
python3 -m venv .venv
make install-dev

# 本地配置（若尚未创建）
cp config/settings.example.yaml config/settings.yaml
```

确认 `config/settings.yaml` 包含：

```yaml
trading:
  env: simulate
  paper_only: true

journal:
  enabled: true
  db_path: data/journal/trades.db
  timezone: Asia/Hong_Kong
```

> **说明：** `settings.yaml` 不会提交到 Git；密钥与本地改动放此文件。

### OpenD

1. 打开 [Futu OpenD](https://www.futunn.com/download/openAPI)
2. 登录 Futu HK 账户
3. 保持运行（默认 `127.0.0.1:11111`）

---

## 测试路线图概览

```
Phase A  无需 OpenD     →  make check（单元测试 + lint）
Phase B  连接与账户     →  status.py
Phase C  日 K 模拟策略   →  run_paper.py --mode daily --once
Phase D  1 分钟模拟策略 →  run_paper.py --mode intraday --once
Phase E  风控行为       →  改配置 / 观察日志
Phase F  安全锁         →  run_live 应被阻止
Phase G  Tick runner    →  run_tick.py（需 tick 策略，当前为骨架）
Phase H  交易日志/报表   →  snapshot / sync_fills / report.py
```

建议 **按 A → H 顺序** 执行；每步「预期结果」均满足后再进行下一步。

---

## Phase A — 代码质量（无需 OpenD）

验证策略逻辑、风控、配置解析等单元测试。

```bash
make check
```

### 预期结果

- `ruff check` 无错误
- `pytest` 全部 PASSED（约 26 个测试）
- `compileall` 无报错

### 若失败

- 缺依赖：`make install-dev`
- 单测失败：看 `tests/` 对应文件，或把报错贴给 Agent

---

## Phase B — OpenD 连接与模拟账户

查询 **Futu 模拟盘** 资金与持仓。

```bash
.venv/bin/python scripts/status.py --market HK
```

### 预期结果

```
=== Account ===
  Environment : simulate
  Total assets: 1,000,000.00   （或你的模拟账户金额）
  Cash        : ...
  Market val  : ...

=== Positions (HK) ===
  (none)                       （或已有持仓列表）
```

### 通过标准

- [ ] 无 `Connection refused` / 连接错误
- [ ] `Environment` 为 **simulate**
- [ ] 能打印账户数字（非全 0 异常）

### 查美股

```bash
.venv/bin/python scripts/status.py --market US
```

### 若失败

| 现象 | 处理 |
|------|------|
| Connection refused | 启动 OpenD 并登录 |
| 找不到 settings | `cp config/settings.example.yaml config/settings.yaml` |
| 显示 real | 检查 `settings.yaml` 中 `paper_only: true` |

---

## Phase C — 日 K 策略（SMA 交叉）

使用内置策略 `sma_crossover`，标的 `HK.00700`（腾讯）。

```bash
.venv/bin/python scripts/run_paper.py \
  --strategy sma_crossover \
  --mode daily \
  --market HK \
  --once \
  --log-level INFO
```

### 预期结果（两种均正常）

**情况 1 — 无信号（常见）**

```
Connected to OpenD at 127.0.0.1:11111 (env=simulate, paper_only=True)
Disconnected from OpenD
```

最新一根日 K **没有** SMA 金叉/死叉时，不会产生订单。

**情况 2 — 有信号并下单**

```
Order placed: BUY HK.00700 x100 @ ... (id=...) — SMA crossover BUY ...
```

或风控/无持仓拒绝：

```
Signal rejected [...]: notional ... exceeds max ...
Signal rejected [...]: insufficient position to sell ...
```

### 通过标准

- [ ] 成功连接 OpenD（有 `Connected` 日志）
- [ ] `env=simulate, paper_only=True`
- [ ] 进程正常退出（exit code 0）
- [ ] 若有 `Order placed`，记下 `order_id`

### 下单后复查账户

```bash
.venv/bin/python scripts/status.py --market HK
```

若有成交，可能看到 `HK.00700` 持仓；模拟盘撮合可能有延迟，也可在 **Futu App → 模拟交易** 查看订单。

### 策略参数位置

- 代码：`src/strategies/sma_crossover.py`
- 配置：`config/strategies/sma_crossover.yaml`

---

## Phase D — 1 分钟 Intraday（M3 能力）

在 **港股交易时段** 测试效果最佳。

```bash
.venv/bin/python scripts/run_paper.py \
  --strategy sma_crossover \
  --mode intraday \
  --data 1m \
  --market HK \
  --once \
  --log-level INFO
```

### 预期结果

- 与 Phase C 类似：连接成功 → 拉 1 分钟 K 线 → 仅对**最新一根** bar 评估信号
- `--once` 只跑一轮后退出（不会 sleep 60 秒循环）

### 通过标准

- [ ] 无连接/订阅致命错误
- [ ] 日志中 `paper_only=True`

### 注意

- 非交易时段可能 K 线更新少，无信号属正常
- 不加 `--once` 时会每 60 秒轮询（长时间运行用 Ctrl+C 停止）

---

## Phase E — 风控（Risk Guard）

当前风控在 `config/settings.yaml` 的 `risk:` 段。可通过日志验证是否 **拒绝** 非法信号。

### E1 — 标的白名单

白名单仅允许：`HK.00700`, `HK.09988`, `US.AAPL`, `US.MSFT`。

若策略 config 改用非白名单标的，应看到：

```
Signal rejected [HK.xxxxx]: symbol not in whitelist
```

（需改 `config/strategies/sma_crossover.yaml` 的 `symbols` 做实验，测完改回。）

### E2 — 单笔金额上限

`max_notional_per_order: 100000`。价 × 量超过上限时：

```
Signal rejected [...]: notional ... exceeds max 100000
```

### E3 — 无持仓卖出

无持仓时 SMA 死叉产生 SELL 信号：

```
Signal rejected [...]: insufficient position to sell (have 0, need 100)
```

### E4 — 冷却时间

同一标的 60 秒内重复信号：

```
Signal rejected [...]: cooldown (60s) not elapsed
```

### 通过标准

- [ ] 至少观察到一种 `Signal rejected`（证明风控在工作）
- [ ] 或通过 Phase C 成功下一笔模拟单后再测 SELL 拒绝

---

## Phase F — Paper-only 安全锁

确认 **无法误触实盘**。

### F1 — run_live 应被阻止

```bash
.venv/bin/python scripts/run_live.py --strategy sma_crossover --confirm
```

### 预期结果

```
BLOCKED: Cannot run live trading: paper_only mode is active. ...
```

退出码非 0。

### F2 — Cursor Hook（若在 Cursor 内运行）

Agent 执行 `run_live.py` 时应被 Hook 拒绝（见 Cursor Settings → Hooks）。

### 通过标准

- [ ] `run_live.py` 无法完成实盘流程
- [ ] 日常只用 `run_paper.py` / `run_tick.py`

---

## Phase G — Tick Runner（可选，当前有限）

`run_tick.py` 已存在，但 **尚未注册 tick 专用示例策略**。若直接运行：

```bash
.venv/bin/python scripts/run_tick.py --strategy sma_crossover --once
```

SMA 策略未订阅 tick，`on_tick` 为空，主要验证 **连接 + 订阅不崩溃**。

### 通过标准（当前阶段）

- [ ] 能连接并运行约 5 秒（`--once`）后退出
- [ ] 无未捕获异常

完整 Tick 联调在 **M4** 里程碑。

---

## Phase H — 交易日志与绩效报表（Journal）

验证 SQLite journal、Futu 订单/成交同步、日终 snapshot 与日/周/月报表。

**前置：** OpenD 已启动；`config/settings.yaml` 中 `journal.enabled: true`（见 `settings.example.yaml`）。

### H1 — 单元测试（无需 OpenD）

Journal 相关测试已包含在 `make check` 中：

```bash
make check
# 或单独跑
.venv/bin/pytest tests/test_journal.py -v
```

### 预期结果

- `tests/test_journal.py` 全部 PASSED
- 覆盖：信号/拒绝写入、订单/成交 upsert、snapshot、报表聚合

### H2 — 日终账户 snapshot

```bash
.venv/bin/python scripts/snapshot_account.py --type eod --market HK
```

### 预期结果

```
Snapshot saved (eod) — assets=1,000,000.00 → .../data/journal/trades.db
```

### 通过标准

- [ ] 无连接错误
- [ ] 打印 `assets=` 与合理金额
- [ ] `data/journal/trades.db` 文件已创建（首次运行）

### H3 — 从 Futu 同步订单/成交

```bash
.venv/bin/python scripts/sync_fills.py
```

### 预期结果

```
Synced N orders, M deals → .../data/journal/trades.db
```

`N`、`M` 取决于模拟盘历史；**限价未成交时 M=0 属正常**。

可选：指定日期范围（含历史查询）

```bash
.venv/bin/python scripts/sync_fills.py --start 2026-06-01 --end 2026-06-14
```

### H4 — run_paper 自动写入 journal

```bash
.venv/bin/python scripts/run_paper.py \
  --strategy sma_crossover \
  --mode daily \
  --market HK \
  --once \
  --log-level INFO
```

### 预期结果

- 连接成功并正常退出
- 日志中可见 `Synced ... orders, ... deals`（run 结束时自动 sync）
- 若有信号：journal 中会有 `signal` / `order_submitted` 事件；无信号时仅 `run_start` / `run_end` snapshot

### H5 — 日 / 周 / 月 报表

```bash
# 日报
.venv/bin/python scripts/report.py --period day

# 周报（可筛策略）
.venv/bin/python scripts/report.py --period week --strategy sma_crossover

# 月报 JSON 导出
.venv/bin/python scripts/report.py --period month --export json
```

### 预期结果（示例）

```
Performance Report — 2026-06-14 (day)
────────────────────────────────────────────────
Assets        : 1,000,000.00 → 1,000,000.00
Return        : +0.00%
Signals       : 0
Rejected      : 0
Orders sent   : 0
Deals (fills) : 0  (BUY 0 / SELL 0)
Snapshots     : 1
```

### 通过标准

- [ ] 报表正常打印，无 Traceback
- [ ] `Snapshots` ≥ 1（至少跑过 H2 或 H4）
- [ ] `--export json` 输出合法 JSON

### H6 — 建议的日常流程

```
收盘后:
  snapshot_account.py --type eod
  sync_fills.py
  report.py --period day

周末:  report.py --period week
月初:  report.py --period month
```

### 若失败

| 现象 | 处理 |
|------|------|
| `Journal is disabled` | 检查 `settings.yaml` → `journal.enabled: true` |
| 无 `trades.db` | 先跑 H2 或 H4；确认 `data/journal/` 目录可写 |
| Deals 始终为 0 | 模拟盘限价单可能未成交；在 Futu App 查看或改用 closer 限价 smoke test |
| Return 为 N/A | 该周期内无 snapshot；先跑 H2 |

---

## 手动模拟下单（可选 smoke test）

不经过策略，直接验证 Broker 模拟下单（与 M2 联调相同）：

```bash
.venv/bin/python -c "
from src.config import load_settings
from src.broker.futu_broker import FutuBroker
from src.models.order import OrderRequest, OrderSide, OrderType

broker = FutuBroker.from_config(load_settings())
broker.connect()
r = broker.place_order(OrderRequest(
    symbol='HK.00700', side=OrderSide.BUY, qty=100,
    order_type=OrderType.LIMIT, price=400.0,
    reason='manual smoke test',
))
print('success:', r.success, 'order_id:', r.order_id)
broker.disconnect()
"
```

### 预期

`success: True` 且 `order_id` 有值。然后在 Futu 模拟交易或 `status.py` 查看。

---

## 总验收清单

完成以下即表示 **当前 Phase 1 能力已测通**：

| # | 测试项 | 命令/方式 | ✓ |
|---|--------|-----------|---|
| A | 单元测试 | `make check` | |
| B | 模拟账户查询 | `status.py --market HK` | |
| C | 日 K paper run | `run_paper.py --mode daily --once` | |
| D | 1m paper run | `run_paper.py --mode intraday --data 1m --once` | |
| E | 风控日志 | 观察 `Signal rejected` 或成功下单 | |
| F | paper_only 锁 | `run_live.py` → BLOCKED | |
| G | 手动下单（可选） | Python smoke test | |
| H | Journal 日志/报表 | `snapshot_account.py` + `sync_fills.py` + `report.py` | |

---

## 常见问题

### Q: 为什么策略从不产生信号？

SMA 只在 **快线上穿/下穿慢线** 时信号。最新一根 K 无交叉则无信号，属正常。可用「手动 smoke test」验证下单通道。

### Q: 在哪里看模拟盘订单？

- Futu 牛牛 / OpenD → **模拟交易** → 订单、成交
- 本项目 CLI：
  - `scripts/sync_fills.py` — 同步到本地 SQLite
  - `scripts/report.py` — 日/周/月绩效汇总
  - `status.py` — 账户 + 持仓（不含订单列表）

### Q: 交易日志存在哪里？

默认 `data/journal/trades.db`（不进 Git）。详见 [Phase H](#phase-h--交易日志与绩效报表journal) 与 README「Journal」一节。

### Q: 能测美股吗？

```bash
.venv/bin/python scripts/run_paper.py --strategy sma_crossover --mode daily --market US --once
```

需将 `config/strategies/sma_crossover.yaml` 中 `symbols` 改为 `US.AAPL` 等白名单标的。

### Q: 如何切换实盘？（现在不要）

1. 你 **明确口头指示** 切换实盘  
2. `settings.yaml` → `paper_only: false`  
3. `export FUTU_TRADE_PASSWORD='...'`  
4. `run_live.py --confirm`  

**在你说切换之前，请保持 `paper_only: true`。**

---

## 相关文档

| 文档 | 内容 |
|------|------|
| [STRATEGY_GUIDE.md](STRATEGY_GUIDE.md) | **当前 SMA 策略说明 + 如何请 Agent 改策略** |
| [WATCHLIST.md](WATCHLIST.md) | **多标的 watchlist 配置** |
| [README.md](../README.md) | 架构与快速开始 |
| [AGENTS.md](../AGENTS.md) | Agent 工作流 |
| [TASKS.md](../TASKS.md) | 里程碑与 Next 任务 |
| [PRD.md](../PRD.md) | 功能设计 |

---

## 测完后建议

1. 在 [TASKS.md](../TASKS.md) 勾选你完成的 M3/M5 项（若做了 Phase D/E/H）
2. 把异常日志保存，方便 Agent 排查
3. 下一步：自定义策略，或 cron 自动化 Phase H 日终流程

如有测试结果，可在 Agent 模式说：「我完成了 Phase C，日志如下…」以便继续 M3/M4。

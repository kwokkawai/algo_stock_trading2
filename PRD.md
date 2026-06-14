# PRD — myAlgo2 算法交易 Agent

**版本:** 0.1  
**日期:** 2026-06-14  
**范围:** 港美股证券（Phase 1 不含期货、期权）

---

## 1. 背景与目标

### 1.1 背景

用户希望通过 Futu HK 执行港美股算法订单，并使用 Cursor Agent + LLM 辅助策略开发与迭代。不同 LLM 可能给出不同策略建议，系统需足够通用，使策略层可独立替换而不影响执行稳定性。

### 1.2 目标

- 提供稳定的 Futu HK 订单执行通道（模拟盘 + 实盘）
- 支持日 K、1 分钟、Tick 三种行情粒度，由策略声明驱动
- 提供可插拔的策略框架，LLM 只需改策略模块
- 内置风控，防止策略 bug 或 LLM 幻觉导致异常下单
- Phase 1 仅 CLI；两个专用 Cursor Skill 分工：执行 vs 策略

### 1.3 非目标（Phase 1）

- Web UI / 移动端
- 高频 / 亚毫秒级交易
- 期权、期货、加密货币
- 完整回测平台
- 分布式多机部署
- 自建行情服务器

---

## 2. 用户角色

| 角色 | 描述 |
|------|------|
| **Trader** | 配置账户、审批实盘、设定风控 |
| **Strategy Agent** | 根据 LLM 建议编写/修改策略代码（algo-strategy skill） |
| **Execution Agent** | 处理 Futu 连接、下单、订单查询（futu-order-execution skill） |

---

## 3. 功能需求

### 3.1 Futu 执行模块（P0）

| ID | 功能 | 说明 |
|----|------|------|
| F-001 | OpenD 连接 | 可配置 host/port，连接状态检测 |
| F-002 | 交易解锁 | 实盘 `unlock_trade`，密码来自 `FUTU_TRADE_PASSWORD` |
| F-003 | 下单 | 限价/市价，BUY/SELL |
| F-004 | 撤单 | 按 order_id 撤销 |
| F-005 | 查持仓 | 按 market 过滤 |
| F-006 | 查订单 | 当日订单列表与状态 |
| F-007 | 环境切换 | SIMULATE / REAL，默认 SIMULATE |
| F-008 | Futu HK 适配 | `SecurityFirm.FUTUSECURITIES`，Universal Account |
| F-009 | 港美股代码映射 | `HK.00700` / `US.AAPL`，TrdMarket 自动选择 |

**Futu HK 默认配置：**

```yaml
broker:
  security_firm: FUTUSECURITIES
  host: 127.0.0.1
  port: 11111
```

**港美股差异：**

| 项 | 港股 | 美股 |
|----|------|------|
| 代码 | `HK.00700` | `US.AAPL` |
| TrdMarket | `HK` | `US` |
| 盘前盘后 | Phase 1 常规时段 | `fill_outside_rth` 可选（Phase 2） |

### 3.2 行情数据模块（P0）

| ID | 功能 | 说明 |
|----|------|------|
| D-001 | DataSubscription | 策略声明 symbols + intervals + tick |
| D-002 | 订阅合并 | Engine 合并多策略订阅，避免重复 |
| D-003 | 日 K Feed | `SubType.K_DAY` |
| D-004 | 1 分钟 Feed | `SubType.K_1M` |
| D-005 | Tick Feed | `SubType.TICKER`，独立 runner |
| D-006 | Futu SubType 映射 | interval → SubType 统一转换 |

### 3.3 策略模块（P0）

| ID | 功能 | 说明 |
|----|------|------|
| S-001 | BaseStrategy 接口 | `on_bar` + `on_tick` + `subscription` |
| S-002 | 策略注册 | registry 按 name 加载 |
| S-003 | 外部配置 | YAML 参数，不硬编码 |
| S-004 | StrategyContext | 注入行情、持仓、参数 |
| S-005 | Signal 模型 | side, symbol, qty, order_type, reason |
| S-006 | 示例策略 | SMA 交叉（日 K + 1m 均可） |

### 3.4 引擎与风控（P0）

| ID | 功能 | 说明 |
|----|------|------|
| E-001 | daily runner | 日 K 策略，定时或手动触发 |
| E-002 | intraday runner | 1 分钟，交易时段 loop |
| E-003 | tick runner | 独立进程，Tick 策略专用 |
| E-004 | 信号去重 | 同一 bar/tick 窗口不重复下单 |
| R-001 | 标的白名单 | 仅允许 config 内 symbols |
| R-002 | 单笔上限 | max_qty / max_notional |
| R-003 | 仓位上限 | 单标的 + 总仓位 |
| R-004 | 日亏损熔断 | 达到阈值停止交易 |
| R-005 | 实盘二次确认 | `--env real --confirm` |
| R-006 | Tick 频率限制 | cooldown + max orders/minute |

### 3.5 Cursor Skills（P0）

| Skill | 职责 | 禁止 |
|-------|------|------|
| `futu-order-execution` | OpenD、下单、查询、Futu HK 配置 | 写策略逻辑 |
| `algo-strategy` | 策略实现、参数、信号格式 | 直接调用 Futu API |

### 3.6 CLI（P0）

| 命令 | 说明 |
|------|------|
| `run_paper.py` | 模拟盘，支持 daily / intraday 模式 |
| `run_tick.py` | Tick 策略独立模拟盘 |
| `run_live.py` | 实盘，需 `--confirm` |
| `status.py` | 查账户、持仓、订单 |

---

## 4. 数据流

```
1. CLI 启动 → 加载 settings.yaml + strategy yaml
2. Registry 实例化 Strategy
3. 合并 DataSubscription → 订阅 Futu 行情
4. Broker.connect() → OpenD
5. [REAL] Broker.unlock(FUTU_TRADE_PASSWORD)
6. Loop (按 mode):
   a. Data feed 推送 bar/tick
   b. Strategy.on_bar / on_tick → List[Signal]
   c. RiskGuard.validate → List[OrderRequest]
   d. Broker.place_order(each)
   e. 结构化日志
7. on_stop → 关闭连接
```

---

## 5. 配置 Schema

### settings.yaml

```yaml
broker:
  host: 127.0.0.1
  port: 11111
  security_firm: FUTUSECURITIES

trading:
  env: simulate          # simulate | real
  markets: [HK, US]

risk:
  max_notional_per_order: 50000
  max_position_pct: 0.2
  daily_loss_limit: 10000
  signal_cooldown_seconds: 60
  tick_max_orders_per_minute: 10
  allowed_symbols:
    HK: [HK.00700, HK.09988]
    US: [US.AAPL, US.MSFT]
```

### strategies/sma_crossover.yaml

```yaml
name: sma_crossover
market: HK
symbols: [HK.00700]
params:
  fast_period: 10
  slow_period: 30
  qty: 100
  interval: "1d"        # "1d" | "1m"
```

---

## 6. 接口契约

### DataSubscription

```python
@dataclass
class DataSubscription:
    symbols: list[str]
    intervals: list[str] = field(default_factory=list)  # "1d", "1m"
    tick: bool = False
```

### Signal

```python
@dataclass
class Signal:
    symbol: str
    side: Literal["BUY", "SELL"]
    qty: int
    order_type: Literal["LIMIT", "MARKET"] = "LIMIT"
    price: float | None = None
    reason: str = ""
```

### BaseStrategy

```python
class BaseStrategy(ABC):
    subscription: DataSubscription

    def on_start(self, ctx: StrategyContext) -> None: ...
    def on_bar(self, bar: Bar, interval: str) -> list[Signal]: ...
    def on_tick(self, tick: Tick) -> list[Signal]: ...
    def on_stop(self, ctx: StrategyContext) -> None: ...
```

---

## 7. 错误处理

| 场景 | 行为 |
|------|------|
| OpenD 未启动 | 启动失败，提示检查 OpenD |
| unlock 失败 | 中止，不下单 |
| place_order 失败 | 日志记录，可选重试 |
| 风控拒绝 | 记录 reason，跳过信号 |
| 日熔断触发 | 停止 loop，不自动平仓 |
| Tick 超频 | 拒绝信号，记录警告 |

---

## 8. 安全与合规

- 交易密码：`FUTU_TRADE_PASSWORD` 环境变量
- `.gitignore`：`config/settings.yaml`、`.env`
- 实盘：`--env real --confirm` 双因子
- 日志不记录密码

---

## 9. 里程碑

| Phase | 交付 |
|-------|------|
| **M1** | Scaffold + Skills + FutuBroker 骨架 + CLI |
| **M2** | 日 K Runner + SMA 示例 + 模拟盘联调 |
| **M3** | 1m intraday Runner + Risk Guard |
| **M4** | Tick Runner + 频率风控 |
| **M5** | 实盘路径 + 结构化日志 |

---

## 10. 成功指标

- 模拟盘完整跑通：行情 → 信号 → 风控 → 下单 → 查持仓
- 新增策略只需：1 py + 1 yaml + registry 一行
- LLM 在 algo-strategy skill 指导下可独立产出合法策略
- 无 `--confirm` 不下实盘单
- Tick 策略独立 runner，不影响日 K 策略

---

## 11. 已决 / 开放问题

**已决：**

- 行情粒度：日 K / 1m / Tick 均支持，策略声明驱动
- 账户：Futu HK（FUTUSECURITIES）
- Phase 1：仅 CLI
- Tick：独立 `run_tick.py` 进程

**开放（Phase 2）：**

- 是否引入本地行情缓存（CSV/SQLite）？
- 美股盘前盘后是否默认开启？
- 多策略并行 vs 单策略单进程？

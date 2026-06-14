---
name: futu-order-execution
description: >-
  Executes Hong Kong and US stock orders via Futu OpenAPI and OpenD for Futu HK
  accounts. Handles connect, unlock, place/cancel orders, positions, and
  market-specific code formats (HK.00700, US.AAPL). Use when the user mentions
  Futu, OpenD, order execution, HK/US trading, broker operations, or trading
  unlock. Never implement strategy logic here.
---

# Futu Order Execution (Futu HK)

Execute orders through Futu OpenAPI. This skill covers the **broker layer only** — no strategy or indicator logic.

## Prerequisites

1. [Futu OpenD](https://www.futunn.com/download/openAPI) running locally (default `127.0.0.1:11111`)
2. Logged into **Futu HK** account in OpenD
3. `pip install futu-api`
4. Real trading password in env: `FUTU_TRADE_PASSWORD`

## Account Configuration (Futu HK)

Always use these defaults unless user explicitly overrides:

| Setting | Value |
|---------|-------|
| security_firm | `SecurityFirm.FUTUSECURITIES` |
| account type | Universal Securities |
| default env | `TrdEnv.SIMULATE` |

## Market & Code Format

| Market | TrdMarket | Code format | Example |
|--------|-----------|-------------|---------|
| Hong Kong | `TrdMarket.HK` | `HK.{5-digit}` | `HK.00700` |
| US | `TrdMarket.US` | `US.{ticker}` | `US.AAPL` |

Infer `TrdMarket` from symbol prefix: `HK.` → HK, `US.` → US.

## Workflow Checklist

```
- [ ] Confirm OpenD is running
- [ ] Confirm trading env (SIMULATE default; REAL needs explicit user approval)
- [ ] Use src/broker/futu_broker.py — do not duplicate broker code inline
- [ ] For REAL: unlock via env password, never hardcode
- [ ] Place order → log order_id → verify via order_list_query
- [ ] Close context when done
```

## Execution Rules

1. **Never** place REAL orders without user explicitly requesting `--env real --confirm`
2. **Never** implement strategy signals in this skill — return/use `OrderRequest` from engine
3. **Never** commit trading passwords
4. Use `src/broker/futu_broker.py` and `src/models/order.py` — extend there if API gaps exist
5. Quote subscription belongs in `src/data/` — not here

## Common Operations

Use the project's `FutuBroker` class:

```python
from src.broker.futu_broker import FutuBroker
from src.models.order import OrderRequest, OrderSide, OrderType

broker = FutuBroker.from_config(config)
broker.connect()
broker.unlock()  # REAL only
result = broker.place_order(OrderRequest(
    symbol="HK.00700",
    side=OrderSide.BUY,
    qty=100,
    order_type=OrderType.LIMIT,
    price=350.0,
))
positions = broker.get_positions(market="HK")
broker.disconnect()
```

## Error Handling

| Error | Action |
|-------|--------|
| Connection refused | Tell user to start OpenD |
| unlock failed | Stop; check `FUTU_TRADE_PASSWORD` |
| place_order ret != OK | Log error data; do not retry blindly |
| Wrong security_firm | Use `FUTUSECURITIES` for Futu HK |

## Files to Modify

| Task | File |
|------|------|
| Broker logic | `src/broker/futu_broker.py` |
| Order models | `src/models/order.py` |
| Broker config | `config/settings.example.yaml` |
| CLI scripts | `scripts/run_live.py`, `scripts/status.py` |

## Do NOT Modify

- `src/strategies/` — strategy agent's domain
- `src/strategy/base.py` — strategy interface
- `src/risk/guard.py` — risk rules (unless user asks)

## Reference

For Futu API details and HK/US differences, see [reference.md](reference.md).

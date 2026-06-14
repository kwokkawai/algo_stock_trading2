# Futu OpenAPI Quick Reference (Futu HK)

## Connection

```python
import futu as ft

# Trade context — filter by market
trd_ctx = ft.OpenSecTradeContext(
    filter_trdmarket=ft.TrdMarket.HK,
    host="127.0.0.1",
    port=11111,
    security_firm=ft.SecurityFirm.FUTUSECURITIES,
)

# Quote context — shared for all markets
quote_ctx = ft.OpenQuoteContext(host="127.0.0.1", port=11111)
```

## Unlock (Real Trading Only)

```python
ret, data = trd_ctx.unlock_trade(password=os.environ["FUTU_TRADE_PASSWORD"])
```

## Place Order

```python
ret, data = trd_ctx.place_order(
    price=350.0,
    qty=100,
    code="HK.00700",
    trd_side=ft.TrdSide.BUY,
    order_type=ft.OrderType.NORMAL,
    trd_env=ft.TrdEnv.SIMULATE,
)
```

## Query

```python
trd_ctx.position_list_query(trd_env=ft.TrdEnv.SIMULATE)
trd_ctx.order_list_query(trd_env=ft.TrdEnv.SIMULATE)
trd_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
```

## Quote Subscription Mapping

| Interval | Futu SubType |
|----------|--------------|
| `1d` | `SubType.K_DAY` |
| `1m` | `SubType.K_1M` |
| tick | `SubType.TICKER` |

```python
quote_ctx.subscribe(["HK.00700"], [ft.SubType.K_DAY, ft.SubType.K_1M])
quote_ctx.subscribe(["HK.00700"], [ft.SubType.TICKER])
```

## HK vs US Notes

- HK codes are zero-padded to 5 digits: `00700` not `700`
- US supports `fill_outside_rth=True` for extended hours (Phase 2)
- HK market orders only support DAY time-in-force
- Always close contexts: `trd_ctx.close()`, `quote_ctx.close()`

## Docs

- https://openapi.futunn.com/futu-api-doc/en/
- Python SDK: https://github.com/FutunnOpen/py-futu-api

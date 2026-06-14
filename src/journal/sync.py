"""Sync Futu orders and deals into the local journal."""

from __future__ import annotations

import logging

from src.broker.futu_broker import FutuBroker
from src.journal.store import JournalStore

logger = logging.getLogger(__name__)


def sync_fills(
    broker: FutuBroker,
    journal: JournalStore,
    *,
    start: str = "",
    end: str = "",
    include_history: bool = True,
) -> tuple[int, int]:
    """Pull orders/deals from Futu and upsert into SQLite."""
    orders = broker.get_orders(start=start, end=end, history=False)
    deals = broker.get_deals(start=start, end=end, history=False)

    if include_history and (start or end):
        orders.extend(broker.get_orders(start=start, end=end, history=True))
        deals.extend(broker.get_deals(start=start, end=end, history=True))

    # Deduplicate by id (history + today may overlap)
    unique_orders = {o.order_id: o for o in orders if o.order_id}
    unique_deals = {d.deal_id: d for d in deals if d.deal_id}

    order_count = journal.upsert_orders(list(unique_orders.values()))
    deal_count = journal.upsert_deals(list(unique_deals.values()))
    logger.info("Synced %d orders, %d deals into %s", order_count, deal_count, journal.db_path)
    return order_count, deal_count

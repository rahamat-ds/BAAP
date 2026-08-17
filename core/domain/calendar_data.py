"""Order-date sampling helpers for the bundled Indian retail domain."""
from __future__ import annotations

import random
from datetime import datetime, timedelta

ORDER_START_DATE = datetime(2024, 1, 1)
ORDER_END_DATE = datetime(2025, 12, 31)


def random_order_date(rng: random.Random | None = None) -> datetime:
    """Return a uniformly random datetime within the sample order window."""
    r = rng or random
    delta = ORDER_END_DATE - ORDER_START_DATE
    return ORDER_START_DATE + timedelta(days=r.randint(0, delta.days))

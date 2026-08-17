"""Financial reference data for the bundled Indian retail domain."""
from __future__ import annotations

DISCOUNT_RANGE: tuple[int, int] = (0, 35)
GST_RATE: float = 0.18

PLATFORM_FEE_RANGE: tuple[int, int] = (10, 50)
PACKAGING_COST_RANGE: tuple[int, int] = (15, 80)

PAYMENT_GATEWAY_FEE: dict[str, float] = {
    "UPI": 0.005,
    "Credit Card": 0.020,
    "Debit Card": 0.015,
    "Net Banking": 0.012,
    "Cash on Delivery": 0.0,
}

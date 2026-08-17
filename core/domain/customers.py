"""Customer reference data for the bundled Indian retail domain."""
from __future__ import annotations

GENDERS: list[str] = ["Male", "Female"]

LOYALTY_TIERS: list[str] = ["Bronze", "Silver", "Gold", "Platinum"]
LOYALTY_WEIGHTS: list[int] = [50, 30, 15, 5]

PAYMENT_METHODS: list[str] = [
    "UPI", "Credit Card", "Debit Card", "Net Banking", "Cash on Delivery",
]
PAYMENT_WEIGHTS: list[int] = [45, 20, 15, 10, 10]

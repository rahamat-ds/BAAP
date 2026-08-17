"""Logistics reference data for the bundled Indian retail domain."""
from __future__ import annotations

DELIVERY_PARTNERS: dict[str, dict[str, float]] = {
    "East": {"Delhivery": 0.45, "Ekart": 0.30, "Blue Dart": 0.15, "XpressBees": 0.10},
    "West": {"Delhivery": 0.30, "Blue Dart": 0.30, "Shadowfax": 0.20, "Ekart": 0.20},
    "South": {"Blue Dart": 0.40, "Delhivery": 0.25, "DTDC": 0.20, "Shadowfax": 0.15},
    "North": {"Delhivery": 0.40, "Blue Dart": 0.25, "DTDC": 0.20, "Ekart": 0.15},
}

RTO_REASONS: list[str] = [
    "Customer Not Available",
    "Wrong Address",
    "Customer Refused",
    "COD Rejected",
    "Damaged Package",
    "Fake Order",
    "Duplicate Order",
]

SHIPPING_MODES: dict[str, float] = {"Standard": 0.60, "Express": 0.30, "Same Day": 0.10}

DELIVERY_DAYS: dict[str, tuple[int, int]] = {
    "Standard": (4, 8),
    "Express": (2, 4),
    "Same Day": (0, 1),
}

RTO_RATE: float = 0.08
RETURN_RATE: float = 0.05

FESTIVALS: list[str] = [
    "None", "Diwali", "Great Indian Festival", "Big Billion Days", "New Year Sale",
]

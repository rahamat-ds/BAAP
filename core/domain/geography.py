"""Geographic reference data for the bundled Indian retail/e-commerce domain.

This preserves InsightFlow's original identity: a realistic Indian
e-commerce dataset generator used for demos, onboarding and testing.
"""
from __future__ import annotations

REGIONS: dict[str, list[str]] = {
    "North": ["Delhi", "Punjab", "Haryana", "Uttar Pradesh", "Rajasthan"],
    "South": ["Karnataka", "Tamil Nadu", "Kerala", "Telangana", "Andhra Pradesh"],
    "East": ["West Bengal", "Odisha", "Bihar", "Jharkhand"],
    "West": ["Maharashtra", "Gujarat", "Goa"],
}

CITIES: dict[str, list[str]] = {
    "West Bengal": ["Kolkata", "Howrah", "Siliguri", "Durgapur"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Udupi"],
    "Delhi": ["New Delhi"],
    "Tamil Nadu": ["Chennai", "Madurai", "Coimbatore", "Ooty"],
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat"],
    "Uttar Pradesh": ["Lucknow", "Noida", "Kanpur", "Varanasi"],
    "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode"],
    "Telangana": ["Hyderabad", "Warangal"],
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada"],
    "Odisha": ["Bhubaneswar", "Cuttack"],
    "Bihar": ["Patna", "Gaya"],
    "Jharkhand": ["Ranchi", "Jamshedpur"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
    "Goa": ["Panaji", "Margao"],
}

WAREHOUSES: dict[str, str] = {
    "East": "Kolkata FC",
    "West": "Mumbai FC",
    "North": "Delhi FC",
    "South": "Bengaluru FC",
}


def get_region(state: str) -> str:
    """Return the macro-region for a given state, raising if unknown."""
    for region, states in REGIONS.items():
        if state in states:
            return region
    raise ValueError(f"Unknown state: {state!r}")

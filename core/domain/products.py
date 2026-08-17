"""Product catalog reference data for the bundled Indian retail domain."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductRef:
    """A single sellable SKU in the synthetic catalog."""

    name: str
    brand: str
    sku: str
    base_price: int


CATALOG: dict[str, dict[str, list[ProductRef]]] = {
    "Electronics": {
        "Smartphones": [
            ProductRef("Apple iPhone 16", "Apple", "ELE-SP-001", 79_999),
            ProductRef("Samsung Galaxy S25", "Samsung", "ELE-SP-002", 74_999),
            ProductRef("OnePlus 13", "OnePlus", "ELE-SP-003", 54_999),
            ProductRef("Google Pixel 10", "Google", "ELE-SP-004", 69_999),
        ],
        "Laptops": [
            ProductRef("MacBook Air M4", "Apple", "ELE-LP-001", 109_999),
            ProductRef("Dell Inspiron 15", "Dell", "ELE-LP-002", 64_999),
            ProductRef("HP Pavilion 14", "HP", "ELE-LP-003", 58_999),
            ProductRef("Lenovo ThinkPad E16", "Lenovo", "ELE-LP-004", 72_999),
        ],
        "Accessories": [
            ProductRef("Wireless Mouse", "Logitech", "ELE-AC-001", 1_299),
            ProductRef("Mechanical Keyboard", "Keychron", "ELE-AC-002", 5_499),
            ProductRef("USB-C Hub", "Anker", "ELE-AC-003", 2_499),
            ProductRef("Noise Cancelling Headphones", "Sony", "ELE-AC-004", 12_999),
        ],
    },
    "Fashion": {
        "Men": [
            ProductRef("Cotton T-Shirt", "Levi's", "FAS-MN-001", 799),
            ProductRef("Slim Fit Jeans", "Wrangler", "FAS-MN-002", 1_999),
            ProductRef("Running Shoes", "Puma", "FAS-MN-003", 3_499),
        ],
        "Women": [
            ProductRef("Kurti", "Biba", "FAS-WM-001", 1_499),
            ProductRef("Handbag", "Lavie", "FAS-WM-002", 2_499),
            ProductRef("Sneakers", "Nike", "FAS-WM-003", 4_299),
        ],
    },
    "Home & Kitchen": {
        "Kitchen": [
            ProductRef("Mixer Grinder", "Prestige", "HM-KT-001", 3_999),
            ProductRef("Pressure Cooker", "Hawkins", "HM-KT-002", 2_499),
            ProductRef("Air Fryer", "Philips", "HM-KT-003", 6_999),
        ],
        "Home Decor": [
            ProductRef("Wall Clock", "Ajanta", "HM-HD-001", 899),
            ProductRef("Table Lamp", "Wipro", "HM-HD-002", 1_499),
            ProductRef("Indoor Plant", "Ugaoo", "HM-HD-003", 599),
        ],
    },
    "Books": {
        "Programming": [
            ProductRef("Python Crash Course", "No Starch Press", "BK-PR-001", 899),
            ProductRef("Hands-On Machine Learning", "O'Reilly", "BK-PR-002", 1_099),
            ProductRef("Designing Data-Intensive Applications", "O'Reilly", "BK-PR-003", 1_199),
        ],
        "Fiction": [
            ProductRef("The Hobbit", "HarperCollins", "BK-FC-001", 499),
            ProductRef("1984", "Penguin", "BK-FC-002", 399),
            ProductRef("The Alchemist", "HarperOne", "BK-FC-003", 350),
        ],
    },
}

CATEGORY_COST_RATIO: dict[str, float] = {
    "Electronics": 0.72,
    "Fashion": 0.45,
    "Home & Kitchen": 0.60,
    "Books": 0.55,
}

"""Synthetic Indian retail/e-commerce order dataset generator.

This is BAAP's signature demo dataset generator, ported from the
original project and meaningfully improved:

* Adds ``order_id`` — the original generator never produced this column,
  which meant its *own* bundled dataset failed its *own* hard-coded schema
  check. The new dataset-agnostic mapping engine no longer needs a fixed
  schema, but ``order_id`` is still useful, so it's now generated properly.
* Reproducible via a ``seed`` argument.
* Optionally injects a small, realistic amount of missing values,
  duplicate rows and price outliers, so the bundled sample actually
  exercises the cleaning / validation / profiling features instead of
  being suspiciously perfect data.
* Mild seasonality: order volume increases toward Diwali / year-end sales.
"""
from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pandas as pd

from core.domain.calendar_data import random_order_date
from core.domain.customers import GENDERS, LOYALTY_TIERS, LOYALTY_WEIGHTS, PAYMENT_METHODS, PAYMENT_WEIGHTS
from core.domain.finance import DISCOUNT_RANGE
from core.domain.geography import CITIES, WAREHOUSES, get_region
from core.domain.logistics import (
    DELIVERY_DAYS,
    DELIVERY_PARTNERS,
    RTO_RATE,
    RTO_REASONS,
    SHIPPING_MODES,
)
from core.domain.products import CATALOG, CATEGORY_COST_RATIO
from core.logging_config import get_logger

logger = get_logger(__name__)

try:
    from faker import Faker
except ImportError:  # pragma: no cover - faker is a listed dependency
    Faker = None

_SEASONAL_BOOST = {10: 1.25, 11: 1.45, 12: 1.15}  # Diwali / festive season / year-end


def _weighted_choice(rng: random.Random, options: dict[str, float]) -> str:
    return rng.choices(list(options.keys()), weights=list(options.values()))[0]


def _generate_customer(rng: random.Random, fake) -> dict:
    state = rng.choice(list(CITIES.keys()))
    city = rng.choice(CITIES[state])
    region = get_region(state)
    return {
        "customer_id": f"CUST-{rng.randint(1, 99_999):05d}",
        "customer_name": fake.name() if fake else f"Customer {rng.randint(1, 99999)}",
        "gender": rng.choice(GENDERS),
        "age": rng.randint(18, 70),
        "state": state,
        "city": city,
        "region": region,
        "loyalty_tier": rng.choices(LOYALTY_TIERS, weights=LOYALTY_WEIGHTS)[0],
        "payment_method": rng.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0],
    }


def _generate_product(rng: random.Random) -> dict:
    category = rng.choice(list(CATALOG.keys()))
    subcategory = rng.choice(list(CATALOG[category].keys()))
    product = rng.choice(CATALOG[category][subcategory])
    qty = rng.randint(1, 4)
    selling = int(product.base_price * rng.uniform(0.95, 1.05))
    cost = int(selling * CATEGORY_COST_RATIO[category])
    return {
        "category": category,
        "subcategory": subcategory,
        "product_name": product.name,
        "manufacturer": product.brand,
        "sku": product.sku,
        "quantity": qty,
        "selling_price": selling,
        "unit_cost": cost,
    }


def _generate_shipping(rng: random.Random, region: str) -> dict:
    warehouse = WAREHOUSES[region]
    partners = DELIVERY_PARTNERS[region]
    courier = _weighted_choice(rng, partners)
    mode = _weighted_choice(rng, SHIPPING_MODES)
    days = rng.randint(*DELIVERY_DAYS[mode])
    is_rto = rng.random() < RTO_RATE
    return {
        "warehouse": warehouse,
        "courier": courier,
        "shipping_mode": mode,
        "delivery_days": days,
        "rto": is_rto,
        "rto_reason": rng.choice(RTO_REASONS) if is_rto else None,
    }


def _calculate_finance(rng: random.Random, product: dict) -> dict:
    discount = rng.randint(*DISCOUNT_RANGE)
    gross = product["selling_price"] * product["quantity"]
    revenue = int(gross * (100 - discount) / 100)
    cost = product["unit_cost"] * product["quantity"]
    return {"discount_percent": discount, "revenue": revenue, "cost": cost, "profit": revenue - cost}


def _generate_dates(rng: random.Random, shipping: dict) -> dict:
    order_date = random_order_date(rng)
    dispatch = order_date + pd.Timedelta(days=1)
    delivery = dispatch + pd.Timedelta(days=shipping["delivery_days"])
    return {
        "order_date": order_date.date(),
        "dispatch_date": dispatch.date(),
        "delivery_date": delivery.date(),
    }


def _generate_order(rng: random.Random, fake, order_seq: int) -> dict:
    customer = _generate_customer(rng, fake)
    product = _generate_product(rng)
    shipping = _generate_shipping(rng, customer["region"])
    finance = _calculate_finance(rng, product)
    dates = _generate_dates(rng, shipping)

    # Mild seasonal demand boost: bias order month toward festive season by
    # occasionally re-rolling a non-festive date into one.
    month = dates["order_date"].month
    if month not in _SEASONAL_BOOST and rng.random() < 0.18:
        boosted_month = rng.choice(list(_SEASONAL_BOOST))
        year = dates["order_date"].year
        day = min(dates["order_date"].day, 28)
        new_order_date = dates["order_date"].replace(month=boosted_month, day=day, year=year)
        dispatch = pd.Timestamp(new_order_date) + pd.Timedelta(days=1)
        delivery = dispatch + pd.Timedelta(days=shipping["delivery_days"])
        dates = {"order_date": new_order_date, "dispatch_date": dispatch.date(), "delivery_date": delivery.date()}

    return {"order_id": f"ORD-{100000 + order_seq}", **customer, **product, **shipping, **finance, **dates}


def _inject_quality_issues(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Sprinkle realistic messiness so the sample showcases cleaning tools."""
    out = df.copy()
    n = len(out)

    for col, frac in (("customer_name", 0.012), ("age", 0.01), ("city", 0.008), ("courier", 0.006)):
        idx = rng.choice(n, size=int(n * frac), replace=False)
        out.loc[out.index[idx], col] = np.nan

    dup_idx = rng.choice(n, size=max(1, int(n * 0.01)), replace=False)
    out = pd.concat([out, out.iloc[dup_idx]], ignore_index=True)

    outlier_idx = rng.choice(len(out), size=max(1, int(len(out) * 0.003)), replace=False)
    boosted = (out.loc[out.index[outlier_idx], "revenue"] * rng.uniform(6, 12)).round(0).astype(out["revenue"].dtype)
    out.loc[out.index[outlier_idx], "revenue"] = boosted

    return out.sample(frac=1.0, random_state=int(rng.integers(0, 1_000_000))).reset_index(drop=True)


def generate_dataset(n_orders: int = 6000, seed: int = 42, inject_quality_issues: bool = True) -> pd.DataFrame:
    """Generate ``n_orders`` synthetic Indian e-commerce orders."""
    rng = random.Random(seed)
    fake = Faker("en_IN") if Faker else None
    if fake:
        fake.seed_instance(seed)

    rows = [_generate_order(rng, fake, i) for i in range(n_orders)]
    df = pd.DataFrame(rows)

    if inject_quality_issues:
        df = _inject_quality_issues(df, np.random.default_rng(seed))

    logger.info("Generated synthetic retail dataset: %d rows", len(df))
    return df


def generate_and_save(path: Path, n_orders: int = 6000, seed: int = 42) -> pd.DataFrame:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_dataset(n_orders=n_orders, seed=seed)
    df.to_csv(path, index=False)
    logger.info("Saved sample dataset to %s (%d rows)", path, len(df))
    return df


if __name__ == "__main__":
    from config import SAMPLE_DIR

    generate_and_save(SAMPLE_DIR / "retail_orders.csv", n_orders=6000)

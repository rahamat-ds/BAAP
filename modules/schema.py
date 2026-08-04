REQUIRED_COLUMNS = {
    "order_id",
    "order_date",
    "dispatch_date",
    "delivery_date",
    "customer_id",
    "customer_name",
    "age",
    "gender",
    "loyalty_tier",
    "product_name",
    "category",
    "manufacturer",
    "quantity",
    "selling_price",
    "unit_cost",
    "revenue",
    "profit",
    "discount",
    "payment_method",
    "region",
    "courier",
    "shipping_mode",
    "delivery_days",
    "rto",
    "rto_reason",
}


def validate_schema(df):

    present = set(df.columns)

    missing = sorted(REQUIRED_COLUMNS - present)

    extra = sorted(present - REQUIRED_COLUMNS)

    matched = len(REQUIRED_COLUMNS) - len(missing)

    completeness = round(
        matched / len(REQUIRED_COLUMNS) * 100,
        1
    )

    return {
        "valid": len(missing) == 0,
        "matched": matched,
        "required": len(REQUIRED_COLUMNS),
        "completeness": completeness,
        "missing": missing,
        "extra": extra,
    }
import pandas as pd


def validate_dataset(df):

    report = {}

    # -----------------------------
    # Duplicate Rows
    # -----------------------------

    duplicates = df.duplicated().sum()

    report["Duplicate Rows"] = {
        "passed": duplicates == 0,
        "count": int(duplicates),
    }

    # -----------------------------
    # Missing Values
    # -----------------------------

    missing = int(df.isna().sum().sum())

    report["Missing Values"] = {
        "passed": missing == 0,
        "count": missing,
    }

    # -----------------------------
    # Negative Revenue
    # -----------------------------

    negative_revenue = (df["revenue"] < 0).sum()

    report["Negative Revenue"] = {
        "passed": negative_revenue == 0,
        "count": int(negative_revenue),
    }

    # -----------------------------
    # Negative Profit
    # -----------------------------

    negative_profit = (df["profit"] < 0).sum()

    report["Negative Profit"] = {
        "passed": negative_profit == 0,
        "count": int(negative_profit),
    }

    # -----------------------------
    # Quantity
    # -----------------------------

    bad_quantity = (df["quantity"] <= 0).sum()

    report["Invalid Quantity"] = {
        "passed": bad_quantity == 0,
        "count": int(bad_quantity),
    }

    # -----------------------------
    # Selling Price
    # -----------------------------

    bad_price = (df["selling_price"] <= 0).sum()

    report["Selling Price"] = {
        "passed": bad_price == 0,
        "count": int(bad_price),
    }

    # -----------------------------
    # Unit Cost
    # -----------------------------

    bad_cost = (df["unit_cost"] <= 0).sum()

    report["Unit Cost"] = {
        "passed": bad_cost == 0,
        "count": int(bad_cost),
    }

    # -----------------------------
    # Selling Price < Cost
    # -----------------------------

    below_cost = (
        df["selling_price"] < df["unit_cost"]
    ).sum()

    report["Selling Below Cost"] = {
        "passed": below_cost == 0,
        "count": int(below_cost),
    }

    # -----------------------------
    # Date Order
    # -----------------------------

    bad_dates = (
        pd.to_datetime(df["delivery_date"])
        <
        pd.to_datetime(df["dispatch_date"])
    ).sum()

    report["Delivery Before Dispatch"] = {
        "passed": bad_dates == 0,
        "count": int(bad_dates),
    }

    # -----------------------------
    # Future Orders
    # -----------------------------

    future = (
        pd.to_datetime(df["order_date"])
        >
        pd.Timestamp.today()
    ).sum()

    report["Future Orders"] = {
        "passed": future == 0,
        "count": int(future),
    }

    return report




def invalid_rows(df):

    return {

        "Selling Below Cost":
        df[df["selling_price"] < df["unit_cost"]],

        "Negative Revenue":
        df[df["revenue"] < 0],

        "Negative Profit":
        df[df["profit"] < 0],

        "Invalid Quantity":
        df[df["quantity"] <= 0],

        "Delivery Before Dispatch":
        df[
            pd.to_datetime(df["delivery_date"])
            <
            pd.to_datetime(df["dispatch_date"])
        ],
    }


def quality_score(report):

    total = len(report)

    passed = sum(
        item["passed"]
        for item in report.values()
    )

    score = round(
        (passed / total) * 100
    )

    return score
"""Tests for analytics.kpis, analytics.customers, analytics.products."""
from __future__ import annotations


def test_compute_core_kpis(clean_sample_df, mapping):
    from analytics.kpis import compute_core_kpis

    kpis = compute_core_kpis(clean_sample_df, mapping)
    names = {k.name for k in kpis}
    assert "Total Revenue" in names
    assert "Total Orders" in names
    revenue_kpi = next(k for k in kpis if k.name == "Total Revenue")
    assert revenue_kpi.value == clean_sample_df[mapping["revenue"]].sum()


def test_revenue_by_period(clean_sample_df, mapping):
    from analytics.kpis import revenue_by_period

    trend = revenue_by_period(clean_sample_df, mapping, freq="M")
    assert not trend.empty
    assert {"period", "value"}.issubset(trend.columns)


def test_top_n(clean_sample_df, mapping):
    from analytics.kpis import top_n

    top = top_n(clean_sample_df, mapping["category"], mapping["revenue"], n=3)
    assert len(top) <= 3
    assert top[mapping["revenue"]].is_monotonic_decreasing


def test_rfm_analysis(clean_sample_df, mapping):
    from analytics.customers import churn_risk, customer_lifetime_value, rfm_analysis

    rfm = rfm_analysis(clean_sample_df, mapping)
    assert not rfm.empty
    assert {"recency", "frequency", "monetary", "segment"}.issubset(rfm.columns)

    rfm = customer_lifetime_value(rfm)
    assert "estimated_clv" in rfm.columns

    rfm = churn_risk(rfm, recency_threshold_days=30)
    assert "churn_risk" in rfm.columns


def test_abc_classification(clean_sample_df, mapping):
    from analytics.products import abc_classification

    abc = abc_classification(clean_sample_df, mapping)
    assert set(abc["class"].unique()).issubset({"A", "B", "C"})
    assert abc["cum_pct"].iloc[-1] > 99.0


def test_product_performance(clean_sample_df, mapping):
    from analytics.products import product_performance

    perf = product_performance(clean_sample_df, mapping)
    assert not perf.empty
    assert mapping["product"] in perf.columns


def test_retail_ops_detection(clean_sample_df, mapping):
    from analytics import retail

    retail_mapping = retail.detect(clean_sample_df, mapping)
    assert retail.is_applicable(retail_mapping)
    perf = retail.courier_performance(clean_sample_df, mapping, retail_mapping)
    assert not perf.empty

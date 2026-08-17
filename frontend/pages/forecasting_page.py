"""Forecasting — project revenue forward with Ridge, Random Forest or moving average."""
import streamlit as st

from forecasting.models import forecast
from frontend.common import bootstrap, mapping_hint, require_dataset
from visualization import charts

bootstrap("Forecasting", "Project your revenue metric forward with confidence bands.")

name, df, mapping = require_dataset()

if not (mapping.get("date") and mapping.get("revenue")):
    mapping_hint(["date", "revenue"])
    st.stop()

c1, c2, c3 = st.columns(3)
method = c1.selectbox("Method", ["ridge", "random_forest", "moving_average"],
                       format_func=lambda m: {"ridge": "Ridge Regression", "random_forest": "Random Forest",
                                               "moving_average": "Moving Average"}[m])
freq = c2.selectbox("Frequency", ["D", "W", "M"], index=0,
                     format_func=lambda f: {"D": "Daily", "W": "Weekly", "M": "Monthly"}[f])
periods = c3.slider("Periods to forecast", 7, 180, 30)

if st.button("Run forecast", type="primary"):
    try:
        with st.spinner("Fitting model..."):
            result_df, metrics = forecast(df, mapping, periods=periods, freq=freq, method=method)
        st.session_state["_last_forecast"] = (result_df, metrics)
    except ValueError as exc:
        st.error(str(exc))

if "_last_forecast" in st.session_state:
    result_df, metrics = st.session_state["_last_forecast"]
    st.plotly_chart(charts.forecast_chart(result_df, title=f"{mapping['revenue']} Forecast"), use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Historical Total", f"{metrics.historical_total:,.0f}" if metrics.historical_total else "\u2014")
    c2.metric("Forecast Total", f"{metrics.forecast_total:,.0f}" if metrics.forecast_total else "\u2014")
    c3.metric("Expected Change", f"{metrics.expected_growth_pct:+.1f}%" if metrics.expected_growth_pct is not None else "\u2014")
    c4.metric("Holdout MAPE", f"{metrics.mape_pct:.1f}%" if metrics.mape_pct == metrics.mape_pct else "\u2014")

    with st.expander("Forecast data"):
        st.dataframe(result_df, use_container_width=True)

    st.caption(
        "Confidence bands are approximate (\u00b11.28 standard deviations of historical residuals, ~80% interval) "
        "and should be treated as directional, not a guarantee."
    )

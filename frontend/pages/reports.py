"""Reports — one-click PDF, Excel and PowerPoint report generation."""
from datetime import datetime

import streamlit as st

from analytics.customers import rfm_analysis
from analytics.insights import generate_insights
from analytics.kpis import compute_core_kpis, revenue_by_period
from analytics.products import abc_classification
from database import repository
from frontend.common import bootstrap, require_dataset
from services import report_service, session_service
from visualization import charts

bootstrap("Reports", "Generate a shareable report bundling KPIs, charts, and insights.")

name, df, mapping = require_dataset()
sid = session_service.session_id()

title = st.text_input("Report title", f"{name} \u2014 Business Performance Report")
include_insights = st.checkbox("Include AI / rule-based insights", value=True)
include_tables = st.multiselect(
    "Include data tables",
    ["Top Products / Categories", "Customer RFM Segments", "Raw Data Sample"],
    default=["Top Products / Categories"],
)

kpis = compute_core_kpis(df, mapping)

if st.button("Generate report", type="primary"):
    tables = {}
    figures = []

    if mapping.get("date") and mapping.get("revenue"):
        trend = revenue_by_period(df, mapping, freq="M")
        if not trend.empty:
            figures.append(charts.area(trend, "period", "value", title="Revenue Trend"))

    if "Top Products / Categories" in include_tables and mapping.get("product"):
        tables["Top Products"] = abc_classification(df, mapping).head(20)
    if "Customer RFM Segments" in include_tables and mapping.get("customer_id"):
        tables["Customer Segments"] = rfm_analysis(df, mapping).head(20)
    if "Raw Data Sample" in include_tables:
        tables["Data Sample"] = df.head(50)

    insights_md = ""
    if include_insights:
        insight_list, _source = generate_insights(df, mapping)
        insights_md = "\n\n".join(f"### {t}" if not t.startswith("#") else t for t in insight_list)

    with st.spinner("Building report..."):
        pdf_bytes = report_service.build_pdf(df, kpis, title=title, insights_md=insights_md, tables=tables, figures=figures)
        excel_bytes = report_service.build_excel({**tables, "Raw Data": df.head(50_000)}, kpis=kpis)
        pptx_bytes = report_service.build_pptx(title, kpis, insights_md)

    st.session_state["_report_files"] = {"pdf": pdf_bytes, "excel": excel_bytes, "pptx": pptx_bytes, "title": title}

if "_report_files" in st.session_state:
    files = st.session_state["_report_files"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    st.success("Report generated.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("\U0001f4c4 Download PDF", files["pdf"], file_name=f"report_{stamp}.pdf", mime="application/pdf",
                            use_container_width=True)
    with c2:
        st.download_button("\U0001f4ca Download Excel", files["excel"], file_name=f"report_{stamp}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)
    with c3:
        if files["pptx"]:
            st.download_button("\U0001f5bc\ufe0f Download PowerPoint", files["pptx"], file_name=f"report_{stamp}.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                use_container_width=True)
        else:
            st.caption("Install `python-pptx` to enable PowerPoint export.")

    path = report_service.save(files["pdf"], f"report_{stamp}.pdf")
    repository.add_report(sid, files["title"], "pdf", str(path))

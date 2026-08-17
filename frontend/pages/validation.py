"""Data Validation — business-rule checks with severity levels and drill-down."""
import streamlit as st

from frontend.common import bootstrap, require_dataset
from models import Severity
from pipelines import validation
from services import report_service

bootstrap("Data Validation", "Business-rule checks generalized from your column mapping — not a fixed schema.")

name, df, mapping = require_dataset()

report = validation.validate_dataset(df, mapping)

c1, c2, c3 = st.columns(3)
c1.metric("Validation Score", f"{report.score}/100")
c2.metric("Checks Passed", f"{sum(1 for c in report.checks if c.passed)}/{len(report.checks)}")
c3.metric("Critical Failures", sum(1 for c in report.checks if not c.passed and c.severity == Severity.CRITICAL))

st.progress(report.score / 100)
st.divider()

icon = {Severity.CRITICAL: "\U0001f534", Severity.WARNING: "\U0001f7e1", Severity.INFO: "\U0001f7e2"}
for check in report.checks:
    status = "\u2705" if check.passed else icon[check.severity]
    with st.container():
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"{status} **{check.name}** \u2014 {check.description}")
        c2.markdown(f"`{check.count:,}` rows" if not check.passed else "`0` rows")

st.divider()
st.markdown("#### Drill down into failing rows")
bad = validation.invalid_rows(df, mapping)
if not bad:
    st.success("No offending rows found for any check.")
else:
    check_name = st.selectbox("Check", list(bad.keys()))
    subset = bad[check_name]
    st.caption(f"{len(subset):,} row(s)")
    st.dataframe(subset, use_container_width=True)
    csv = report_service.build_csv(subset)
    st.download_button("Download these rows as CSV", csv, file_name=f"{check_name.replace(' ', '_').lower()}.csv",
                        mime="text/csv")

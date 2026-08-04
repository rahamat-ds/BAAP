import streamlit as st
import pandas as pd

from utils.session import (
    initialize_session,
    get_dataset,
)

from modules.validation import (
    validate_dataset,
    quality_score,
    invalid_rows,
)

st.set_page_config(
    page_title="Data Validation",
    page_icon="✅",
    layout="wide"
)
st.title("✅ Data Validation")

initialize_session()

df = get_dataset()

if df is None:
    st.warning("⚠️Please upload or generate a dataset from the Home page.")
    st.stop()

report = validate_dataset(df)
score = quality_score(report)
bad = invalid_rows(df)

passed = sum(
    item["passed"]
    for item in report.values()
)

failed = len(report) - passed

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Rows", len(df))
c2.metric("Columns", len(df.columns))
c3.metric("Passed", passed)
c4.metric("Failed", failed)
c5.metric("Quality Score", f"{score}/100")

st.divider()

SEVERITY = {

    "Duplicate Rows": "Warning",

    "Missing Values": "Warning",

    "Negative Revenue": "Critical",

    "Negative Profit": "Warning",

    "Invalid Quantity": "Critical",

    "Selling Price": "Critical",

    "Unit Cost": "Critical",

    "Selling Below Cost": "Critical",

    "Delivery Before Dispatch": "Critical",

    "Future Orders": "Warning",
}


for check, result in report.items():

    severity = SEVERITY[check]

    if result["passed"]:

        st.success(f"✅ {check}")

    else:

        if severity == "Critical":

            st.error(
                f"❌ {check} ({result['count']} issues)"
            )

        else:

            st.warning(
                f"⚠️ {check} ({result['count']} issues)"
            )

        if check in bad and not bad[check].empty:

            with st.expander(
                f"View affected rows ({len(bad[check])})"
            ):

                st.dataframe(
                    bad[check],
                    use_container_width=True
                )


non_empty = [
    frame
    for frame in bad.values()
    if not frame.empty
]

if non_empty:

    all_bad = (
        pd.concat(
            non_empty,
            ignore_index=True
        )
        .drop_duplicates()
    )

    csv = all_bad.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇ Download Invalid Records",
        csv,
        "invalid_records.csv",
        "text/csv"
    )
import streamlit as st

from utils.session import (
    initialize_session,
    get_dataset,
)

from modules.schema import (
    validate_schema,
)

st.set_page_config(
    page_title="Schema Check",
    page_icon="🧩",
    layout="wide"
)

initialize_session()

df = get_dataset()

if df is None:

    st.warning(
        "Upload or generate a dataset first."
    )

    st.stop()

st.title("🧩 Dataset Schema")

result = validate_schema(df)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Required",
    result["required"]
)

c2.metric(
    "Matched",
    result["matched"]
)

c3.metric(
    "Completeness",
    f"{result['completeness']}%"
)

st.divider()

if result["valid"]:

    st.success(
        "Dataset matches the InsightFlow retail schema."
    )

else:

    st.error(
        "Dataset is missing required columns."
    )

st.subheader("Missing Columns")

if result["missing"]:

    st.write(result["missing"])

else:

    st.success("None")

st.subheader("Extra Columns")

if result["extra"]:

    st.write(result["extra"])

else:

    st.success("None")
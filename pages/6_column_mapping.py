import streamlit as st

from utils.session import (
    initialize_session,
    get_dataset,
    update_dataset,
)

from modules.schema import REQUIRED_COLUMNS
from modules.column_mapper import apply_mapping

initialize_session()

df = get_dataset()

if df is None:

    st.warning(
        "Upload a dataset first."
    )

    st.stop()

st.title("🗂 Column Mapping")

mapping = {}

for expected in sorted(REQUIRED_COLUMNS):

    mapping_choice = st.selectbox(

        f"{expected}",

        options=["-- Ignore --"] + list(df.columns),

        key=expected
    )

    if mapping_choice != "-- Ignore --":

        mapping[mapping_choice] = expected

st.divider()

if st.button("Apply Mapping"):

    mapped_df = apply_mapping(df, mapping)

    update_dataset(mapped_df)

    st.success("Column mapping applied successfully.")
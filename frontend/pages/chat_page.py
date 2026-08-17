"""Chat with Data — ask natural-language questions about the active dataset."""
import streamlit as st

import llm
from chat import conversation, nlq
from frontend.common import bootstrap, require_dataset
from services import session_service

bootstrap("Chat with Data", "Ask questions in plain English \u2014 works fully offline.")

name, df, mapping = require_dataset()
sid = session_service.session_id()

if llm.is_available():
    st.caption(f"\U0001f7e2 Answers narrated by **{llm.active_provider_name().title()}**.")
else:
    st.caption("\u26aa Offline mode: deterministic pattern-matching answers computed directly from your data.")

st.markdown("**Try asking:**")
cols = st.columns(3)
for i, q in enumerate(nlq.SUGGESTED_QUESTIONS):
    if cols[i % 3].button(q, key=f"suggest_{i}", use_container_width=True):
        st.session_state["_chat_pending"] = q

for msg in conversation.history(sid, limit=50):
    with st.chat_message(msg.role):
        st.markdown(msg.content)

pending = st.session_state.pop("_chat_pending", None)
question = pending or st.chat_input(f"Ask something about {name}...")

if question:
    with st.chat_message("user"):
        st.markdown(question)
    conversation.record(sid, name, "user", question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer_text, table = nlq.answer(df, mapping, question)
        st.markdown(answer_text)
        if table is not None and not table.empty:
            st.dataframe(table, use_container_width=True)
    conversation.record(sid, name, "assistant", answer_text)
    st.rerun()

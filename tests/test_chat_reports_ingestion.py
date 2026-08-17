"""Tests for chat.nlq, services.report_service, and pipelines.ingestion."""
from __future__ import annotations

import pandas as pd


def test_nlq_total_revenue(clean_sample_df, mapping):
    from chat.nlq import answer

    text, table = answer(clean_sample_df, mapping, "What is the total revenue?")
    assert "revenue" in text.lower() or str(int(clean_sample_df[mapping["revenue"]].sum())) in text


def test_nlq_top_n(clean_sample_df, mapping):
    from chat.nlq import answer

    text, table = answer(clean_sample_df, mapping, "Show me the top 5 by revenue")
    assert table is not None
    assert len(table) <= 5


def test_nlq_row_count(clean_sample_df, mapping):
    from chat.nlq import answer

    text, _ = answer(clean_sample_df, mapping, "How many rows are there?")
    assert str(len(clean_sample_df)) in text


def test_nlq_unknown_question_graceful(clean_sample_df, mapping):
    from chat.nlq import answer

    text, table = answer(clean_sample_df, mapping, "what is the meaning of life")
    assert isinstance(text, str) and text


def test_build_pdf_report(clean_sample_df, mapping):
    from analytics.kpis import compute_core_kpis
    from services.report_service import build_pdf

    kpis = compute_core_kpis(clean_sample_df, mapping)
    pdf_bytes = build_pdf(clean_sample_df, kpis, title="Test Report", insights_md="### Insight one\nDetails here.")
    assert pdf_bytes[:4] == b"%PDF"


def test_build_excel_report(clean_sample_df, mapping):
    from analytics.kpis import compute_core_kpis
    from services.report_service import build_excel

    kpis = compute_core_kpis(clean_sample_df, mapping)
    excel_bytes = build_excel({"Data": clean_sample_df.head(20)}, kpis=kpis)
    assert excel_bytes[:2] == b"PK"  # xlsx is a zip archive


def test_build_csv():
    from services.report_service import build_csv

    df = pd.DataFrame({"a": [1, 2]})
    out = build_csv(df)
    assert b"a" in out


def test_ingestion_csv_roundtrip():
    from pipelines.ingestion import read_csv_bytes

    raw = b"a,b\n1,2\n3,4\n"
    df, meta = read_csv_bytes(raw)
    assert len(df) == 2
    assert meta["encoding"]


def test_ingestion_detect_delimiter():
    from pipelines.ingestion import detect_delimiter

    assert detect_delimiter("a;b;c\n1;2;3") == ";"


def test_validate_upload_flags_issues():
    from pipelines.ingestion import validate_upload

    df = pd.DataFrame({"a": [1, 1], "b": [1, 1]})  # duplicate row + constant columns
    findings = validate_upload(df)
    messages = " ".join(m for _, m in findings)
    assert "duplicate" in messages.lower() or "constant" in messages.lower()

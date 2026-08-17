"""File ingestion: CSV / Excel / JSON / ZIP / SQL with encoding and delimiter
auto-detection, plus lightweight post-load validation messages.
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect

from config import SAMPLE_DIR
from core.logging_config import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = (".csv", ".txt", ".xlsx", ".xls", ".xlsm", ".json", ".zip",
                         ".db", ".sqlite", ".sqlite3")
ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "utf-16"]


def detect_encoding(raw: bytes) -> str:
    """Best-effort character-encoding detection with a safe fallback chain."""
    try:
        import chardet  # optional dependency

        guess = chardet.detect(raw[:200_000])
        if guess and guess.get("encoding") and (guess.get("confidence") or 0) > 0.6:
            return guess["encoding"]
    except ImportError:
        pass
    for enc in ENCODINGS:
        try:
            raw[:200_000].decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def detect_delimiter(text: str) -> str:
    """Sniff the field delimiter from a text sample, defaulting to comma."""
    sample = "\n".join(text.splitlines()[:20])
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        counts = {d: sample.count(d) for d in [",", ";", "\t", "|"]}
        return max(counts, key=counts.get) if max(counts.values()) else ","


def read_csv_bytes(raw: bytes, encoding: str | None = None, delimiter: str | None = None):
    enc = encoding or detect_encoding(raw)
    text_data = raw.decode(enc, errors="replace")
    sep = delimiter or detect_delimiter(text_data)
    df = pd.read_csv(io.StringIO(text_data), sep=sep, engine="python")
    return df, {"encoding": enc, "delimiter": repr(sep)}


def read_excel_bytes(raw: bytes, sheet: int | str = 0):
    xls = pd.ExcelFile(io.BytesIO(raw))
    sheet_name = xls.sheet_names[sheet] if isinstance(sheet, int) else sheet
    return xls.parse(sheet_name), {"sheets": xls.sheet_names, "sheet": sheet_name}


def read_json_bytes(raw: bytes):
    enc = detect_encoding(raw)
    payload = json.loads(raw.decode(enc, errors="replace"))
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                payload = value
                break
    return pd.json_normalize(payload), {"encoding": enc}


def read_zip_bytes(raw: bytes) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            if info.is_dir() or info.filename.startswith("__MACOSX"):
                continue
            ext = Path(info.filename).suffix.lower()
            data = archive.read(info)
            try:
                if ext == ".csv":
                    out[Path(info.filename).name], _ = read_csv_bytes(data)
                elif ext in (".xlsx", ".xls"):
                    out[Path(info.filename).name], _ = read_excel_bytes(data)
                elif ext == ".json":
                    out[Path(info.filename).name], _ = read_json_bytes(data)
            except Exception as exc:  # noqa: BLE001 - keep scanning remaining files
                logger.warning("Skipping %s inside zip: %s", info.filename, exc)
                continue
    return out


def load_any(filename: str, raw: bytes) -> tuple[dict[str, pd.DataFrame], dict]:
    """Load any supported file type. Returns (dict_of_dataframes, meta)."""
    ext = Path(filename).suffix.lower()
    if ext in (".csv", ".txt"):
        df, meta = read_csv_bytes(raw)
        return {Path(filename).stem: df}, meta
    if ext in (".xlsx", ".xls", ".xlsm"):
        xls = pd.ExcelFile(io.BytesIO(raw))
        return {s: xls.parse(s) for s in xls.sheet_names}, {"sheets": xls.sheet_names}
    if ext == ".json":
        df, meta = read_json_bytes(raw)
        return {Path(filename).stem: df}, meta
    if ext == ".zip":
        frames = read_zip_bytes(raw)
        return frames, {"files": list(frames)}
    if ext in (".db", ".sqlite", ".sqlite3"):
        tmp = Path("/tmp") / Path(filename).name
        tmp.write_bytes(raw)
        return sql_tables(f"sqlite:///{tmp}"), {"uri": f"sqlite:///{tmp}"}
    raise ValueError(f"Unsupported file type: {ext}")


def sql_tables(uri: str, limit: int | None = None) -> dict[str, pd.DataFrame]:
    """Load every table from a SQLAlchemy-compatible database URI."""
    eng = create_engine(uri)
    frames: dict[str, pd.DataFrame] = {}
    for table_name in inspect(eng).get_table_names():
        query = f"SELECT * FROM {table_name}" + (f" LIMIT {int(limit)}" if limit else "")
        frames[table_name] = pd.read_sql(query, eng)
    return frames


def sql_query(uri: str, sql: str) -> pd.DataFrame:
    """Run a raw SQL query against an external database and return the result."""
    return pd.read_sql(sql, create_engine(uri))


def validate_upload(df: pd.DataFrame) -> list[tuple[str, str]]:
    """Return a list of (level, message) findings for a freshly loaded frame."""
    findings: list[tuple[str, str]] = []
    if df.empty:
        findings.append(("error", "Dataset contains 0 rows."))
        return findings

    findings.append(("ok", f"Loaded {len(df):,} rows x {df.shape[1]} columns."))

    unnamed = [c for c in df.columns if str(c).startswith("Unnamed")]
    if unnamed:
        findings.append(("warn", f"{len(unnamed)} unnamed column(s) detected — consider renaming or dropping."))

    dupes = int(df.duplicated().sum())
    if dupes:
        findings.append(("warn", f"{dupes:,} duplicate row(s) found."))

    null_pct = float(df.isna().mean().mean() * 100)
    if null_pct > 20:
        findings.append(("warn", f"High missingness: {null_pct:.1f}% of all cells are empty."))
    elif null_pct > 0:
        findings.append(("ok", f"Missing values: {null_pct:.1f}% of cells."))

    constant_cols = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
    if constant_cols:
        findings.append(("warn", f"{len(constant_cols)} constant column(s): {', '.join(map(str, constant_cols[:5]))}"))

    return findings


def load_sample() -> tuple[str, pd.DataFrame]:
    """Load (or lazily generate) the bundled Indian-retail demo dataset."""
    path = SAMPLE_DIR / "retail_orders.csv"
    if not path.exists():
        from services.sample_data_service import generate_and_save

        generate_and_save(path, n_orders=6000)
    return "Indian_Retail_Orders.csv", pd.read_csv(path)

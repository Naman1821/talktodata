"""
Hackathon Streamlit entrypoint: Theme 1 Talk to Data — verified analytics + optional Gemini.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

# Streamlit runs this file as a script, so we expose `src/` on sys.path for
# absolute `talk_to_data.*` imports. `PROJECT_ROOT` is two parents up:
#   src/talk_to_data/app.py -> src/ -> <repo root>
_HERE = Path(__file__).resolve().parent
_SRC_DIR = _HERE.parent
_PROJECT_ROOT = _SRC_DIR.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

try:
    from dotenv import load_dotenv

    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass

import streamlit as st

from talk_to_data.data_utils import infer_schema
from talk_to_data.document_loader import load_uploaded_file
from talk_to_data.semantic_layer import build_metric_definition
from talk_to_data.views import (
    get_google_api_key,
    inject_styles,
    render_gemini_api_panel,
    render_hero,
    render_pdf_talk,
    render_schema_summary,
    render_sidebar,
    render_talk_tab,
)


_DOC_SESSION_KEYS = (
    "doc_file_key",
    "loaded_filename",
    "doc_kind",
    "doc_df",
    "pdf_text",
    "doc_schema",
    "doc_metric_def",
)


def _session_has_loaded_document() -> bool:
    """True if a file was loaded earlier in this session (survives browser refresh; uploader resets to empty)."""
    if not st.session_state.get("doc_file_key"):
        return False
    kind = st.session_state.get("doc_kind")
    if kind == "csv":
        return st.session_state.get("doc_df") is not None
    if kind == "pdf":
        return "pdf_text" in st.session_state
    return False


def _clear_loaded_document_state() -> None:
    for k in _DOC_SESSION_KEYS:
        st.session_state.pop(k, None)


def _on_hackathon_doc_upload_change() -> None:
    """User cleared the file picker — drop cached doc so the main column does not keep showing old data."""
    if st.session_state.get("hackathon_doc_upload") is None:
        _clear_loaded_document_state()


st.set_page_config(page_title="Talk to Data", page_icon="📊", layout="wide")

inject_styles()

render_hero()
api_key = get_google_api_key()

# Uploader runs before the two-column layout so the upload handshake is not blocked
# behind other widgets (helps with stuck spinners on some Streamlit versions).
uploaded = st.file_uploader(
    "Upload PDF or CSV",
    type=["csv", "pdf"],
    key="hackathon_doc_upload",
    on_change=_on_hackathon_doc_upload_change,
)

main_col, gemini_col = st.columns([3.2, 1], gap="large")

with gemini_col:
    render_gemini_api_panel()

with main_col:

    def _file_key(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    if uploaded:
        raw = uploaded.getvalue()
        key = _file_key(raw)
        if st.session_state.get("doc_file_key") != key:
            try:
                with st.spinner("Reading file…"):
                    loaded = load_uploaded_file(uploaded.name, raw)
            except Exception:
                st.error("Error: Could not read file.")
                st.stop()
            if loaded.kind == "csv" and loaded.df is not None:
                try:
                    with st.spinner("Detecting columns…"):
                        _schema = infer_schema(loaded.df)
                        _metric_def = build_metric_definition(_schema)
                except Exception as exc:
                    st.error(
                        f"Could not infer schema from CSV: {exc}\n\n"
                        "Please ensure the file has at least one parseable numeric metric column."
                    )
                    st.stop()
                st.session_state["doc_schema"] = _schema
                st.session_state["doc_metric_def"] = _metric_def
            else:
                st.session_state.pop("doc_schema", None)
                st.session_state.pop("doc_metric_def", None)
            st.session_state["doc_file_key"] = key
            st.session_state["loaded_filename"] = loaded.filename
            st.session_state["doc_kind"] = loaded.kind
            st.session_state["doc_df"] = loaded.df
            st.session_state["pdf_text"] = loaded.pdf_text
    elif not _session_has_loaded_document():
        render_sidebar(None)
        st.info(
            "Upload a CSV (date + metric columns) for analytics, or a PDF for line search / AI Q&A. "
            "Add a Gemini key in the panel on the right if you want AI text (optional)."
        )
        st.stop()
    else:
        st.caption(
            f"Showing **{st.session_state.get('loaded_filename', 'your file')}** from this session. "
            "The picker is empty after a refresh — choose a file again to replace it."
        )

    filename = st.session_state["loaded_filename"]
    kind = st.session_state["doc_kind"]
    st.success(f"File {filename} Loaded Successfully")

    render_sidebar(kind)

    if kind == "csv":
        df = st.session_state["doc_df"]
        assert df is not None
        schema = st.session_state.get("doc_schema")
        metric_def = st.session_state.get("doc_metric_def")
        if schema is None or metric_def is None:
            try:
                with st.spinner("Detecting schema…"):
                    schema = infer_schema(df)
                    metric_def = build_metric_definition(schema)
            except Exception as exc:
                st.error(
                    f"Could not infer schema from CSV: {exc}\n\n"
                    "Please ensure the file has at least one parseable numeric metric column."
                )
                st.stop()
            st.session_state["doc_schema"] = schema
            st.session_state["doc_metric_def"] = metric_def
        render_schema_summary(df, schema, metric_def)
        render_talk_tab(df, schema, api_key)
    else:
        render_pdf_talk(
            st.session_state["pdf_text"],
            api_key,
            doc_key=st.session_state.get("doc_file_key") or "",
            filename=st.session_state.get("loaded_filename") or "document.pdf",
        )

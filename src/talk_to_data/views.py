"""
Streamlit layout for Theme 1 — Talk to Data.

Verified analytics first (pandas); optional free-tier Gemini for grounded narratives.
"""

from __future__ import annotations

import hashlib
import json
import os
import pandas as pd
import streamlit as st

from . import gemini_embeddings, pgvector_store
from .assistant import answer_talk_to_data
from .data_utils import DataSchema
from .llm_layer import (
    answer_pdf_grounded_llm,
    clear_gemini_model_cache,
    enrich_csv_insight,
)
from .pdf_qa import answer_from_pdf_text
from .semantic_layer import MetricDefinition


def inject_styles() -> None:
    st.markdown(
        """
    <style>
    .main > div {
        padding-top: 1.2rem;
    }
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0ea5e9 100%);
        color: #ffffff;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 14px;
        box-shadow: 0 10px 30px rgba(2, 6, 23, 0.25);
    }
    .hero h1 {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .hero p {
        margin: 6px 0 0 0;
        opacity: 0.95;
        font-size: 0.95rem;
    }
    .section-title {
        font-weight: 650;
        margin-bottom: 6px;
    }
    .muted {
        color: #64748b;
        font-size: 0.9rem;
    }
    .insight-card {
        border: 1px solid rgba(30, 64, 175, 0.20);
        border-radius: 12px;
        padding: 12px 14px;
        background: rgba(30, 64, 175, 0.06);
        margin-bottom: 10px;
    }
    .insight-card strong {
        font-size: 0.95rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
    <div class="hero">
      <h1>Talk to Data — Theme 1</h1>
      <p>Numbers and charts come from your file (pandas). Gemini only adds a short plain-English summary when you turn it on (same numbers).</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _session_get(name: str, default=None):
    try:
        return st.session_state.get(name, default)
    except Exception:
        return default


def get_google_api_key() -> str | None:
    """
    Effective key for Gemini calls.
    Priority: session-saved key (if Use Gemini is on) → GOOGLE_API_KEY env / Streamlit secrets.
    """
    stored = _session_get("gemini_api_key_stored")
    if stored:
        if _session_get("gemini_use_ai", True):
            return str(stored).strip() or None
        return None
    k = os.environ.get("GOOGLE_API_KEY")
    if k:
        return k.strip() or None
    try:
        sec = st.secrets
        if sec and "GOOGLE_API_KEY" in sec:
            return str(sec["GOOGLE_API_KEY"]).strip() or None
    except Exception:
        pass
    return None


def _friendly_gemini_api_error(message: str | None) -> str:
    if not message:
        return ""
    m = str(message)
    if "API_KEY_INVALID" in m or "API key not valid" in m or (
        "400" in m and "API key" in m
    ):
        return (
            "Google rejected this API key (invalid, revoked, or restricted). "
            "Use a current key from Google AI Studio (aistudio.google.com) or set GOOGLE_API_KEY in `.env`."
        )
    return m if len(m) <= 600 else m[:597] + "…"


def render_gemini_api_panel() -> None:
    """Right column: Gemini key in Streamlit session only (no extra JS iframes). Use `.env` for refresh-stable key."""
    with st.container(border=True):
        st.markdown("##### Gemini API")
        st.caption(
            "Paste your Google AI (Gemini) key for **this session** (RAM only — not saved to Git). "
            "A full page refresh clears it unless you set **GOOGLE_API_KEY** in `.env` or cloud secrets."
        )

        has_stored = bool(_session_get("gemini_api_key_stored"))

        with st.form("gemini_key_form", clear_on_submit=True):
            key_input = st.text_input(
                "Google API key",
                type="password",
                placeholder="Paste key from aistudio.google.com",
                help="Same as GOOGLE_API_KEY. Never committed to the repo.",
            )
            save = st.form_submit_button("Save key", use_container_width=True)
        st.caption(
            "**Save key** — Keeps the key in this Streamlit session and enables AI summaries after verified results."
        )

        if save and key_input.strip():
            new_k = key_input.strip()
            prev_k = st.session_state.get("gemini_api_key_stored")
            if prev_k and prev_k != new_k:
                clear_gemini_model_cache(str(prev_k))
            st.session_state["gemini_api_key_stored"] = new_k
            st.session_state["gemini_use_ai"] = True
            st.rerun()

        if has_stored:
            raw = st.session_state["gemini_api_key_stored"]
            tail = raw[-4:] if len(raw) >= 4 else "****"
            st.caption(f"Active session key (masked): `…{tail}`")

            st.session_state.setdefault("gemini_use_ai", True)

            st.toggle(
                "Use Gemini AI",
                key="gemini_use_ai",
                help="Off = show verified pandas results only; your key stays in this session until you remove it.",
            )
            st.caption(
                "**Use Gemini AI** — On: call Gemini for the extra summary. Off: no API calls; key remains for later."
            )

            remove = st.button("Remove saved key", use_container_width=True, type="secondary")
            st.caption(
                "**Remove saved key** — Deletes the key from this browser and session. "
                "App falls back to `.env` / cloud secrets if present."
            )
            if remove:
                old = st.session_state.get("gemini_api_key_stored")
                if old:
                    clear_gemini_model_cache(str(old))
                st.session_state.pop("gemini_api_key_stored", None)
                st.session_state.pop("gemini_use_ai", None)
                st.rerun()
        else:
            if os.environ.get("GOOGLE_API_KEY"):
                st.info("Using **GOOGLE_API_KEY** from environment. Save a key above to override for this session.")


def render_sidebar(kind: str | None) -> None:
    with st.sidebar:
        if kind is None:
            st.markdown("### Talk to Data")
            st.caption("Use the Gemini panel on the right to add a key, or rely on tables only.")
            return
        if kind == "csv":
            st.markdown("### Example questions (CSV)")
            st.code(
                "Why did revenue change last month?\n"
                "North vs South performance\n"
                "Show breakdown by region\n"
                "Weekly summary for leadership"
            )
        else:
            st.markdown("### PDF")
            st.caption("Line search works offline. Add a key on the right for AI Q&A.")
        st.markdown("### Privacy")
        st.caption(
            "Processing stays in this browser session. Do not upload confidential data in public demos."
        )


def render_schema_summary(df: pd.DataFrame, schema: DataSchema, metric_def: MetricDefinition) -> None:
    colk1, colk2, colk3 = st.columns(3)
    colk1.metric("Rows", len(df))
    colk2.metric("Primary Metric", schema.metric_col)
    colk3.metric("Category Dimension", schema.category_col or "N/A")

    with st.expander("Detected dataset schema", expanded=False):
        st.write(
            {
                "date_column": schema.date_col,
                "metric_column": schema.metric_col,
                "category_column": schema.category_col or "Not detected",
                "rows": len(df),
            }
        )
        st.markdown("### Metric definition (semantic layer)")
        st.write(
            {
                "metric_name": metric_def.metric_name,
                "formula": metric_def.formula,
                "grain": metric_def.grain,
                "caveats": metric_def.caveats,
            }
        )
        st.dataframe(df.head(10), use_container_width=True)


def render_talk_tab(df: pd.DataFrame, schema: DataSchema, api_key: str | None) -> None:
    st.markdown('<div class="section-title">Natural language analytics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">First you get <strong>verified tables and charts</strong> from your CSV. '
        "If Gemini is enabled (right panel or <code>.env</code>), a <strong>short summary</strong> uses the same numbers only.</div>",
        unsafe_allow_html=True,
    )
    if not api_key:
        st.info(
            "Gemini is off or no key set — you still get full verified results. "
            "Turn on **Use Gemini AI** in the right panel after **Save key**, or set **GOOGLE_API_KEY** in `.env`."
        )

    with st.container(border=True):
        q = st.text_input(
            "Ask a question",
            placeholder="Why did revenue change last month? | Region A vs Region B | Weekly summary for leadership",
        )
    if st.button("Generate Insight", type="primary", use_container_width=True):
        if not q.strip():
            st.warning("Enter a question first.")
        else:
            try:
                out = answer_talk_to_data(q, df, schema)
                st.markdown("### Verified result")
                st.markdown(f"#### {out.result.title}")
                st.markdown(
                    f"""
                    <div class="insight-card">
                      <strong>Computed narrative</strong><br/>
                      {out.result.narrative}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                c1, c2 = st.columns([1, 2])
                c1.metric("Routing confidence", f"{out.confidence:.2f}")
                c2.caption(f"Detected intent: {out.intent}")

                if out.result.assumptions:
                    with st.expander("Assumptions used", expanded=False):
                        for item in out.result.assumptions:
                            st.write(f"- {item}")

                st.dataframe(out.result.table, use_container_width=True)
                if "date" in out.result.table.columns and "value" in out.result.table.columns:
                    chart_df = out.result.table.copy()
                    chart_df = chart_df.set_index("date")
                    st.line_chart(chart_df["value"])
                elif schema.category_col and schema.category_col in out.result.table.columns:
                    metric_candidate = schema.metric_col if schema.metric_col in out.result.table.columns else None
                    if metric_candidate:
                        chart_df = out.result.table[[schema.category_col, metric_candidate]].set_index(
                            schema.category_col
                        )
                        st.bar_chart(chart_df)
                st.markdown("#### Source transparency")
                for src in out.result.sources:
                    st.write(f"- {src}")
                st.caption("Tables and metrics above are computed only from your uploaded CSV in this session.")

                if api_key:
                    st.markdown("### AI explanation (Gemini, grounded)")
                    with st.spinner("Waiting for AI response — Gemini can take a few seconds…"):
                        ai_result = enrich_csv_insight(q, out, api_key)
                    if ai_result.text:
                        st.success(ai_result.text)
                        if ai_result.model_used:
                            st.caption(f"Model: `{ai_result.model_used}` (auto-selected for your API key)")
                    elif ai_result.error:
                        st.warning(_friendly_gemini_api_error(ai_result.error))
                    else:
                        st.warning("No AI text returned. Showing verified block only.")
                else:
                    ai_result = enrich_csv_insight(q, out, None)
                    st.caption("Add a key on the right (or `.env`) and turn **Use Gemini AI** on to show the summary here.")

                st.markdown("Recommended next action")
                if out.intent in {"drivers", "breakdown", "entity_compare"}:
                    st.write("- Drill down by product/channel and validate top contributors for intervention.")
                elif out.intent == "summary":
                    st.write("- Share this summary in leadership update and monitor next 7-day trend shift.")
                else:
                    st.write("- Compare same metric across another segment to validate consistency.")

                report_payload = {
                    "question": q,
                    "intent": out.intent,
                    "confidence": out.confidence,
                    "narrative": out.result.narrative,
                    "sources": out.result.sources,
                    "assumptions": out.result.assumptions,
                    "ai_explanation": ai_result.text,
                    "ai_error": ai_result.error,
                    "gemini_model": ai_result.model_used,
                }
                st.download_button(
                    "Download Insight Report (JSON)",
                    data=json.dumps(report_payload, indent=2, default=str),
                    file_name="insight_report.json",
                    mime="application/json",
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"Could not answer query: {exc}")


def render_pdf_talk(
    pdf_text: str,
    api_key: str | None,
    doc_key: str = "",
    filename: str = "document.pdf",
) -> None:
    st.markdown('<div class="section-title">PDF: ask or search</div>', unsafe_allow_html=True)

    doc_id = doc_key or hashlib.sha256((pdf_text or "")[:12000].encode()).hexdigest()

    def pgvector_panel() -> None:
        st.markdown(
            '<div class="muted">Chunk PDF text, embed with Gemini <code>text-embedding-004</code> (768-d), '
            "store in <strong>Postgres + pgvector</strong>, then run cosine similarity search.</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            f"Set **DATABASE_URL** (e.g. Docker Compose `db` service). "
            f"Indexed chunks for this document: **{pgvector_store.count_chunks(doc_id)}**."
        )
        if not api_key:
            st.info("Add a **Gemini API key** (right panel) to index and query embeddings.")
            return
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Index PDF into database", type="secondary", use_container_width=True, key="pgv_index_btn"):
                ok, err = pgvector_store.ensure_schema()
                if not ok:
                    st.error(f"Schema error: {err}")
                else:
                    chunks = pgvector_store.chunk_text_for_indexing(pdf_text)
                    if not chunks:
                        st.warning("No text to index.")
                    else:
                        with st.spinner(f"Embedding {len(chunks)} chunks (Gemini)…"):
                            all_vecs: list[list[float]] = []
                            batch = 40
                            failed = False
                            for i in range(0, len(chunks), batch):
                                sub = chunks[i : i + batch]
                                vecs, emsg = gemini_embeddings.embed_documents(sub, api_key)
                                if emsg or not vecs:
                                    st.error(f"Embedding failed: {emsg or 'empty'}")
                                    failed = True
                                    break
                                all_vecs.extend(vecs)
                            if not failed and len(all_vecs) == len(chunks):
                                rows = [(j, chunks[j], all_vecs[j]) for j in range(len(chunks))]
                                ok2, err2 = pgvector_store.replace_pdf_chunks(doc_id, filename, rows)
                                if ok2:
                                    st.success(f"Stored {len(rows)} chunks for `{filename}`.")
                                else:
                                    st.error(f"Database write failed: {err2}")
        with c2:
            qv = st.text_input(
                "Semantic search query",
                placeholder="Concepts from the document…",
                key="pgv_semantic_q",
            )
            if st.button("Search vectors", type="primary", use_container_width=True, key="pgv_search_btn"):
                if not (qv or "").strip():
                    st.warning("Enter a query.")
                else:
                    qe, qerr = gemini_embeddings.embed_query(qv.strip(), api_key)
                    if qerr or not qe:
                        st.error(f"Query embedding failed: {qerr}")
                    else:
                        hits, serr = pgvector_store.search_similar_chunks(doc_id, qe, top_k=6)
                        if serr:
                            st.error(serr)
                        elif not hits:
                            st.info("No chunks — index the PDF first.")
                        else:
                            st.markdown("#### Top similar chunks (cosine distance — lower is closer)")
                            for content, cidx, dist in hits:
                                with st.expander(f"Chunk {cidx} — distance {dist:.4f}", expanded=False):
                                    st.text(content[:4000] + ("…" if len(content) > 4000 else ""))

    if pgvector_store.is_configured():
        with st.expander("Postgres + pgvector (semantic search)", expanded=False):
            pgvector_panel()

    def line_search_ui() -> None:
        if len(pdf_text) > 8000:
            with st.expander("Text preview (first ~8k characters)", expanded=False):
                st.text(pdf_text[:8000])
        else:
            with st.expander("Extracted text", expanded=False):
                st.text(pdf_text or "(empty)")
        q = st.text_input("Search / keywords", placeholder="Words that appear in the PDF", key="pdf_line_q")
        if st.button("Find matching lines", type="primary", use_container_width=True, key="pdf_line_btn"):
            if not (q or "").strip():
                st.warning("Enter a search first.")
            else:
                answer = answer_from_pdf_text(q, pdf_text)
                st.markdown("#### Matching lines")
                st.write(answer)

    def ai_pdf_ui() -> None:
        st.markdown(
            '<div class="muted">Answers only from extracted PDF text. Otherwise: Not present.</div>',
            unsafe_allow_html=True,
        )
        q2 = st.text_input("Your question", placeholder="What does the document say about …?", key="pdf_ai_q")
        if st.button("Ask AI", type="primary", use_container_width=True, key="pdf_ai_btn"):
            if not (q2 or "").strip():
                st.warning("Enter a question first.")
            else:
                with st.spinner("Waiting for AI response — Gemini can take a few seconds…"):
                    res = answer_pdf_grounded_llm(q2, pdf_text, api_key)
                if res.text:
                    st.markdown("#### Answer")
                    st.write(res.text)
                    if res.model_used:
                        st.caption(f"Model: `{res.model_used}` (auto-selected for your API key)")
                elif res.error:
                    st.warning(_friendly_gemini_api_error(res.error))
                else:
                    st.warning("AI call failed. Try line search or check API key.")

    if api_key:
        tab_ai, tab_lines = st.tabs(["AI Q&A (document only)", "Line search (offline)"])
        with tab_ai:
            ai_pdf_ui()
        with tab_lines:
            line_search_ui()
    else:
        st.caption("Add a Gemini key on the **right** and turn **Use Gemini AI** on for PDF Q&A. Line search works below.")
        line_search_ui()

"""
Optional free-tier LLM (Gemini) for Theme 1 — only explains pre-verified facts or PDF text.

Model id is chosen via ListModels for the caller's API key (avoids hardcoded 404s like gemini-1.5-flash).
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime
from typing import Any, NamedTuple

from google import genai
from google.genai import types

from .assistant import AssistantOutput

MAX_TABLE_ROWS_FOR_LLM = 50
MAX_PDF_CHARS_FOR_LLM = 100_000

_MODEL_ID_PREFERENCE: tuple[str, ...] = (
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.5-pro-preview",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-thinking-exp-01-21",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest",
    "gemini-1.5-pro",
)

_model_id_cache: dict[str, str] = {}
_client_cache: dict[str, genai.Client] = {}

CSV_ENRICH_SYSTEM = """You are a business writing assistant for a data analytics app.
You receive a USER QUESTION and a VERIFIED COMPUTED RESULT (JSON) from the user's CSV (title, computed_narrative, table_rows, sources, intent, etc.).

Write a short, clear answer in plain English (2–6 sentences) summarizing what the JSON contains.

Rules:
- You MUST use computed_narrative and table_rows when non-empty. Align with the user question when possible; if the question is broad, still summarize the verified result.
- Use ONLY facts and numbers from the JSON. No outside knowledge.
- Say exactly "Not present." ONLY if table_rows is empty AND computed_narrative has no usable facts.

Do not say you are an AI. Sound like a concise analyst."""

PDF_QA_SYSTEM = """You are a document Q&A assistant. Your ONLY source is the DOCUMENT TEXT provided.
Answer using only that text in plain English (2–8 sentences).
If the answer is not contained in or cannot be derived from the text, respond exactly with: Not present.
Do not use outside knowledge."""


class GeminiEnrichResult(NamedTuple):
    text: str | None
    error: str | None
    model_used: str | None = None


def clear_gemini_model_cache(api_key: str | None = None) -> None:
    """Drop cached model id and client for this key, or clear all caches."""
    global _model_id_cache, _client_cache
    if api_key is None:
        _model_id_cache.clear()
        _client_cache.clear()
        return
    ck = _cache_key(api_key)
    _model_id_cache.pop(ck, None)
    _client_cache.pop(ck, None)


def _cache_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def _get_client(api_key: str) -> genai.Client:
    ck = _cache_key(api_key)
    if ck not in _client_cache:
        _client_cache[ck] = genai.Client(api_key=api_key)
    return _client_cache[ck]


def _collect_generate_content_model_ids(client: genai.Client) -> list[str]:
    out: list[str] = []
    for m in client.models.list():
        methods = list(getattr(m, "supported_generation_methods", None) or [])
        if "generateContent" not in methods:
            continue
        raw = getattr(m, "name", "") or ""
        mid = raw.rsplit("/", 1)[-1] if raw else ""
        if mid:
            out.append(mid)
    return out


def resolve_generate_content_model_id(api_key: str) -> str:
    """
    Pick a model id that supports generateContent for this key (ListModels).
    Result is cached per key until clear_gemini_model_cache or 404 retry.
    """
    ck = _cache_key(api_key)
    if ck in _model_id_cache:
        return _model_id_cache[ck]

    client = _get_client(api_key)
    valid = _collect_generate_content_model_ids(client)
    if not valid:
        raise RuntimeError(
            "No models with generateContent found for this API key. "
            "Enable the Generative Language API and check the key in Google AI Studio."
        )

    valid_set = set(valid)
    chosen: str | None = None
    for pref in _MODEL_ID_PREFERENCE:
        if pref in valid_set:
            chosen = pref
            break

    if chosen is None:
        scored: list[tuple[int, str]] = []
        for mid in valid:
            mlow = mid.lower()
            if "embed" in mlow:
                continue
            score = 0
            if "2.5" in mid and "flash" in mlow:
                score = 100
            elif "2.5" in mid:
                score = 95
            elif "2.0" in mid and "flash" in mlow:
                score = 85
            elif "flash" in mlow:
                score = 75
            elif "gemini" in mlow:
                score = 60
            else:
                score = 40
            scored.append((score, mid))
        scored.sort(key=lambda x: (-x[0], x[1]))
        chosen = scored[0][1] if scored else valid[0]

    _model_id_cache[ck] = chosen
    return chosen


def _generate_with_resolved_model(
    api_key: str, system_instruction: str, user_block: str
) -> tuple[Any, str]:
    client = _get_client(api_key)
    ck = _cache_key(api_key)
    last_err = ""

    for attempt in range(2):
        try:
            model_id = resolve_generate_content_model_id(api_key)
            response = client.models.generate_content(
                model=model_id,
                contents=user_block,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                ),
            )
            return response, model_id
        except Exception as exc:
            last_err = str(exc)
            err_low = last_err.lower()
            is_404 = "404" in last_err or "not found" in err_low or "is not found" in err_low
            if attempt == 0 and is_404:
                _model_id_cache.pop(ck, None)
                continue
            raise RuntimeError(last_err) from exc

    raise RuntimeError(last_err or "Gemini generateContent failed.")


def _sanitize_for_json(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (str, bool, int)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(x) for x in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "item"):
        try:
            return _sanitize_for_json(obj.item())
        except Exception:
            return str(obj)
    return str(obj)


def _payload_json(payload: dict) -> str:
    clean = _sanitize_for_json(payload)
    return json.dumps(clean, ensure_ascii=False, indent=2, allow_nan=False)


def _extract_gemini_text(response: Any) -> tuple[str | None, str | None]:
    if not getattr(response, "candidates", None):
        pf = getattr(response, "prompt_feedback", None)
        if pf is not None:
            br = getattr(pf, "block_reason", None)
            if br is not None:
                return None, f"Prompt blocked: {br}"
        return None, "No response candidates (quota, safety, or empty generation)."

    try:
        t = (response.text or "").strip()
        if t:
            return t, None
    except (ValueError, AttributeError):
        pass

    try:
        cand = response.candidates[0]
        parts = getattr(getattr(cand, "content", None), "parts", None) or []
        chunks: list[str] = []
        for p in parts:
            if hasattr(p, "text") and p.text:
                chunks.append(p.text)
        merged = "".join(chunks).strip()
        if merged:
            return merged, None
        fr = getattr(cand, "finish_reason", None)
        return None, f"No text in response (finish_reason={fr})."
    except Exception as exc:
        return None, str(exc)


def insight_payload_for_llm(out: AssistantOutput, max_rows: int = MAX_TABLE_ROWS_FOR_LLM) -> dict:
    table = out.result.table.head(max_rows)
    return {
        "title": out.result.title,
        "computed_narrative": out.result.narrative,
        "sources": out.result.sources,
        "assumptions": out.result.assumptions or [],
        "intent": out.intent,
        "confidence": out.confidence,
        "table_rows": table.to_dict(orient="records"),
    }


def enrich_csv_insight(question: str, out: AssistantOutput, api_key: str | None) -> GeminiEnrichResult:
    if not api_key or not question.strip():
        return GeminiEnrichResult(None, None, None)
    try:
        payload = insight_payload_for_llm(out)
        user_block = (
            f"USER QUESTION:\n{question.strip()}\n\n"
            f"VERIFIED RESULT (JSON, from uploaded CSV only):\n{_payload_json(payload)}"
        )
        response, used_model = _generate_with_resolved_model(api_key, CSV_ENRICH_SYSTEM, user_block)
        text, err = _extract_gemini_text(response)
        if text:
            return GeminiEnrichResult(text, None, used_model)
        msg = (err or "Empty model response") + f" (model: {used_model})"
        return GeminiEnrichResult(None, msg, used_model)
    except Exception as exc:
        return GeminiEnrichResult(None, str(exc), None)


def answer_pdf_grounded_llm(question: str, pdf_text: str, api_key: str | None) -> GeminiEnrichResult:
    if not api_key or not question.strip():
        return GeminiEnrichResult(None, None, None)
    doc = (pdf_text or "").strip()
    if not doc:
        return GeminiEnrichResult("Not present.", None, None)
    doc = doc[:MAX_PDF_CHARS_FOR_LLM]
    try:
        user_block = f"DOCUMENT TEXT:\n{doc}\n\n---\nUSER QUESTION:\n{question.strip()}"
        response, used_model = _generate_with_resolved_model(api_key, PDF_QA_SYSTEM, user_block)
        text, err = _extract_gemini_text(response)
        if text:
            return GeminiEnrichResult(text, None, used_model)
        msg = (err or "Empty model response") + f" (model: {used_model})"
        return GeminiEnrichResult(None, msg, used_model)
    except Exception as exc:
        return GeminiEnrichResult(None, str(exc), None)

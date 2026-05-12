"""
Talk-to-data orchestration: maps free-text questions to deterministic analytics on CSV.

All metrics and tables are computed locally (pandas). Optional Gemini narration lives in
`llm_layer` and may only paraphrase the verified JSON payload — it does not compute numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .analytics import (
    InsightResult,
    breakdown_by_category,
    change_drivers,
    compare_entities,
    compare_latest_periods,
    leadership_summary,
    weekly_summary,
)
from .data_utils import DataSchema, prepare_timeseries
from .query_parser import extract_vs_entities, parse_query_meta


@dataclass
class AssistantOutput:
    result: InsightResult
    intent: str
    confidence: float


def detect_intent(query: str) -> str:
    """Rough intent bucket from keywords; used before specialized parsers run."""
    q = query.lower()
    if any(k in q for k in ["forecast", "predict", "next", "future", "scenario", "anomaly"]):
        return "compare"
        
    # Added keywords: "top", "best", "highest", "most", "largest"
    if any(k in q for k in ["breakdown", "decompose", "share", "contributor", "top", "best", "highest", "most", "largest"]):
        return "breakdown"
        
    if any(k in q for k in ["compare", "vs", "versus", "changed"]):
        return "compare"
    if any(k in q for k in ["summary", "summarize", "weekly", "monthly", "daily"]):
        return "summary"
    return "compare"


def estimate_confidence(query: str, intent: str, has_category: bool) -> float:
    score = 0.62
    q = query.lower()
    if intent in q:
        score += 0.12
    if any(k in q for k in ["why", "cause", "driver", "breakdown", "compare", "summary"]):
        score += 0.1
    if intent in {"breakdown"} and not has_category:
        score -= 0.2
    return max(0.0, min(0.95, score))


def answer_talk_to_data(query: str, df: pd.DataFrame, schema: DataSchema) -> AssistantOutput:
    """Run the full routing pipeline and return a single insight package for the UI."""
    ts = prepare_timeseries(df, schema)
    intent = detect_intent(query)
    meta = parse_query_meta(query)

    vs_entities = extract_vs_entities(query, df, schema.category_col)
    
    # --- FAILSAFE: Handle dateless datasets ---
    if not schema.date_col and intent in ["compare", "summary"]:
        if schema.category_col:
            intent = "breakdown"
        else:
            raise ValueError("This dataset doesn't have a date column for time-based comparisons.")
    # ------------------------------------------

    if vs_entities:
        result = compare_entities(df, schema, vs_entities[0], vs_entities[1])
        intent = "entity_compare"
    elif any(k in query.lower() for k in ["why", "caused", "driver"]) and schema.category_col:
        result = change_drivers(df, schema)
        intent = "drivers"
    elif intent == "breakdown":
        result = breakdown_by_category(df, schema)
    elif intent == "summary":
        if any(k in query.lower() for k in ["leadership", "executive", "management"]):
            result = leadership_summary(ts)
        else:
            result = weekly_summary(ts)
    else:
        result = compare_latest_periods(ts)

    assumptions = list(result.assumptions or [])
    assumptions.extend(meta.ambiguities)
    result.assumptions = assumptions
    confidence = estimate_confidence(query, intent, bool(schema.category_col))
    return AssistantOutput(result=result, intent=intent, confidence=confidence)
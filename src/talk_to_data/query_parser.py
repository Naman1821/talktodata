from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class QueryMeta:
    is_ambiguous: bool
    ambiguities: list[str]
    normalized_text: str


def parse_query_meta(query: str) -> QueryMeta:
    q = query.lower().strip()
    ambiguities: list[str] = []
    if "last cycle" in q:
        ambiguities.append("Interpreted 'last cycle' as the immediately previous period.")
    if "this month" in q:
        ambiguities.append("Interpreted 'this month' using calendar month boundaries.")
    if "last month" in q:
        ambiguities.append("Interpreted 'last month' using calendar month boundaries.")
    if "recently" in q:
        ambiguities.append("Interpreted 'recently' as the latest available periods in the dataset.")
    return QueryMeta(is_ambiguous=bool(ambiguities), ambiguities=ambiguities, normalized_text=q)


def extract_vs_entities(query: str, df: pd.DataFrame, category_col: str | None) -> tuple[str, str] | None:
    """
    Extract 'X vs Y' entities from query by matching category values.
    """
    if not category_col or "vs" not in query.lower():
        return None

    values = [str(v) for v in df[category_col].dropna().unique().tolist()]
    values_lower = {v.lower(): v for v in values}

    parts = query.lower().split("vs")
    if len(parts) != 2:
        return None
    left, right = parts[0], parts[1]

    left_match = None
    right_match = None
    for v_lower, original in values_lower.items():
        if v_lower in left:
            left_match = original
        if v_lower in right:
            right_match = original
    if left_match and right_match and left_match != right_match:
        return left_match, right_match
    return None


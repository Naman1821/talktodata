from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Optional

import pandas as pd

# Schema inference scans columns with pd.to_datetime / nunique — use a cap so large
# CSVs (e.g. millions of rows) stay responsive in Streamlit instead of “stuck loading”.
_SCHEMA_INFER_MAX_ROWS = 15_000


def _schema_infer_sample(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) <= _SCHEMA_INFER_MAX_ROWS:
        return df
    return df.iloc[:_SCHEMA_INFER_MAX_ROWS]


@dataclass
class DataSchema:
    date_col: Optional[str]
    metric_col: str
    category_col: Optional[str]


def load_csv(uploaded_file) -> pd.DataFrame:
    """Load uploaded CSV into DataFrame with safe defaults."""
    raw = uploaded_file.getvalue()
    df = pd.read_csv(io.BytesIO(raw))
    if df.empty:
        raise ValueError("Uploaded file has no rows.")
    return df


def infer_schema(df: pd.DataFrame) -> DataSchema:
    """Infer likely date, metric, and category columns."""
    sample = _schema_infer_sample(df)
    date_col = _pick_date_column(sample)
    metric_col = _pick_metric_column(sample, exclude=[date_col] if date_col else [])
    category_col = _pick_category_column(sample, exclude=[date_col, metric_col])
    
    if not metric_col:
        raise ValueError("Could not infer numeric metric column.")
    return DataSchema(date_col=date_col, metric_col=metric_col, category_col=category_col)


def _clean_financial_numbers(series: pd.Series) -> pd.Series:
    """Safely converts financial strings (e.g., '£1,000.50') to pure floats."""
    if pd.api.types.is_numeric_dtype(series):
        return series
    
    # Strip spaces, commas, and common currency symbols
    cleaned = series.astype(str).str.replace(r'[£$€,\s]', '', regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def prepare_timeseries(df: pd.DataFrame, schema: DataSchema) -> pd.DataFrame:
    """Build canonical time-series DataFrame sorted by date."""
    if not schema.date_col:
        return pd.DataFrame(columns=["date", "value"])
        
    ts = df[[schema.date_col, schema.metric_col]].copy()
    ts.columns = ["date", "value"]
    ts["date"] = pd.to_datetime(ts["date"], errors="coerce")
    ts["value"] = _clean_financial_numbers(ts["value"])
    
    ts = ts.dropna(subset=["date", "value"]).sort_values("date")
    if ts.empty:
        return pd.DataFrame(columns=["date", "value"])
    return ts


def _pick_date_column(df: pd.DataFrame) -> Optional[str]:
    n = len(df)
    need = max(3, int(0.5 * n))
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().sum() >= need:
                return col
    for col in df.columns:
        parsed = pd.to_datetime(df[col], errors="coerce")
        if parsed.notna().sum() >= need:
            return col
    return None


def _pick_metric_column(df: pd.DataFrame, exclude: list[str]) -> Optional[str]:
    candidates = []
    n = len(df)
    for col in df.columns:
        if col in exclude:
            continue

        as_num = _clean_financial_numbers(df[col])
        coverage = as_num.notna().sum() / max(1, n)
        
        if coverage > 0.7:
            score = 1
            if any(k in col.lower() for k in ["sales", "revenue", "cost", "amount", "value", "metric", "balance", "exposure", "principal"]):
                score += 2
            candidates.append((score, col))
            
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def _pick_category_column(df: pd.DataFrame, exclude: list[Optional[str]]) -> Optional[str]:
    excluded = {c for c in exclude if c}
    n = len(df)
    for col in df.columns:
        if col in excluded:
            continue
        if pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
            nunique = df[col].nunique(dropna=True)
            # Allow up to 95% cardinality so columns like 'Name' are accepted
            if 2 <= nunique <= max(20, int(0.95 * n)):
                return col
    return None
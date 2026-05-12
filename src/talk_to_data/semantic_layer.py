"""
Human-readable metric definition shown in the UI for transparency.

This does not compute new numbers; it documents what the detected columns mean
so reviewers see an explicit “semantic layer” without a separate BI catalog.
"""

from __future__ import annotations

from dataclasses import dataclass

from .data_utils import DataSchema


@dataclass
class MetricDefinition:
    metric_name: str
    formula: str
    grain: str
    caveats: str

def build_metric_definition(schema: DataSchema) -> MetricDefinition:
    """Build labels and caveats from inferred schema (additive metric assumption)."""
    metric_name = schema.metric_col
    formula = f"SUM({schema.metric_col})"
    
    # Safe handling for missing date column
    if schema.date_col:
        grain = f"Per record aggregated by requested period from `{schema.date_col}`"
    else:
        grain = "Aggregated over the entire dataset (no date column detected)"
        
    caveats = (
        "Assumes metric column is additive and already cleaned. "
        "Missing values are excluded during numeric/date parsing."
    )
    return MetricDefinition(metric_name=metric_name, formula=formula, grain=grain, caveats=caveats)
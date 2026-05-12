from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .data_utils import DataSchema


@dataclass
class InsightResult:
    title: str
    narrative: str
    table: pd.DataFrame
    sources: list[str]
    assumptions: list[str] | None = None


def compare_latest_periods(ts: pd.DataFrame) -> InsightResult:
    """Compare latest window versus previous window."""
    agg = ts.set_index("date").resample("W")["value"].sum().dropna()
    if len(agg) < 4:
        agg = ts.set_index("date").resample("D")["value"].sum().dropna()
    if len(agg) < 4:
        raise ValueError("Need at least 4 time periods for comparison.")

    recent = agg.iloc[-2]
    prev = agg.iloc[-3]
    delta = recent - prev
    pct = (delta / prev * 100.0) if prev else 0.0
    direction = "increased" if delta >= 0 else "decreased"

    out = pd.DataFrame(
        {
            "period": [str(agg.index[-3].date()), str(agg.index[-2].date())],
            "value": [float(prev), float(recent)],
        }
    )
    text = f"Metric {direction} by {abs(pct):.2f}% versus the previous period."
    return InsightResult(
        title="Period Comparison",
        narrative=text,
        table=out,
        sources=["Derived from uploaded dataset aggregated by period."],
        assumptions=["Compared latest complete period to the one immediately before it."],
    )


def breakdown_by_category(df: pd.DataFrame, schema: DataSchema) -> InsightResult:
    if not schema.category_col:
        raise ValueError("No suitable category column found for breakdown.")
    grp = (
        df.groupby(schema.category_col, dropna=False)[schema.metric_col]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    total = grp[schema.metric_col].sum()
    grp["share_pct"] = (grp[schema.metric_col] / total * 100.0).round(2)
    top = grp.iloc[0]
    text = (
        f"{top[schema.category_col]} is the largest contributor "
        f"at {top['share_pct']:.2f}% of total."
    )
    return InsightResult(
        title="Category Breakdown",
        narrative=text,
        table=grp,
        sources=[f"Grouped by `{schema.category_col}` from uploaded dataset."],
        assumptions=["Category totals are computed as direct sum of the selected metric column."],
    )


def weekly_summary(ts: pd.DataFrame) -> InsightResult:
    """Summarize latest week with trend and variability."""
    daily = ts.set_index("date").resample("D")["value"].sum().dropna()
    if len(daily) < 14:
        raise ValueError("Need at least 14 days for weekly summary.")
    last_week = daily.iloc[-7:].sum()
    prev_week = daily.iloc[-14:-7].sum()
    pct = ((last_week - prev_week) / prev_week * 100.0) if prev_week else 0.0
    volatility = daily.iloc[-28:].pct_change().std() * 100 if len(daily) >= 28 else daily.pct_change().std() * 100
    text = (
        f"Last 7 days are {pct:+.2f}% vs previous 7 days. "
        f"Recent volatility is {float(volatility):.2f}%."
    )
    out = daily.iloc[-14:].reset_index()
    out.columns = ["date", "value"]
    return InsightResult(
        title="Weekly Summary",
        narrative=text,
        table=out,
        sources=["Daily aggregates from uploaded dataset."],
        assumptions=["Weekly summary uses last 14 days with week-over-week comparison."],
    )


def leadership_summary(ts: pd.DataFrame) -> InsightResult:
    """
    High-signal summary for non-technical leadership audiences.
    """
    daily = ts.set_index("date").resample("D")["value"].sum().dropna()
    if len(daily) < 21:
        raise ValueError("Need at least 21 days for leadership summary.")
    recent = daily.iloc[-7:]
    prev = daily.iloc[-14:-7]
    earlier = daily.iloc[-21:-14]

    wow = ((recent.sum() - prev.sum()) / prev.sum() * 100.0) if prev.sum() else 0.0
    trend_accel = ((prev.sum() - earlier.sum()) / earlier.sum() * 100.0) if earlier.sum() else 0.0
    noise = recent.pct_change().abs().mean() * 100.0

    headline = (
        f"Last 7 days are {wow:+.2f}% vs prior week. "
        f"Prior-week momentum was {trend_accel:+.2f}%. "
        f"Day-to-day variability is {noise:.2f}%."
    )
    out = daily.tail(21).reset_index()
    out.columns = ["date", "value"]
    return InsightResult(
        title="Leadership Summary",
        narrative=headline,
        table=out,
        sources=["Daily trend scan from uploaded dataset."],
        assumptions=["Focused on the last 3 weeks to prioritize recent business signal over long history."],
    )


def change_drivers(df: pd.DataFrame, schema: DataSchema, freq: str = "W") -> InsightResult:
    """
    Explain what changed by isolating category contributions between last two periods.
    """
    if not schema.category_col:
        raise ValueError("No category column found for driver decomposition.")
    work = df[[schema.date_col, schema.metric_col, schema.category_col]].copy()
    work[schema.date_col] = pd.to_datetime(work[schema.date_col], errors="coerce")
    work[schema.metric_col] = pd.to_numeric(work[schema.metric_col], errors="coerce")
    work = work.dropna(subset=[schema.date_col, schema.metric_col])
    if work.empty:
        raise ValueError("No valid rows for driver analysis.")
    work["period"] = work[schema.date_col].dt.to_period(freq).astype(str)

    p = sorted(work["period"].unique())
    if len(p) < 2:
        raise ValueError("Need at least two periods for change driver analysis.")
    prev_p, curr_p = p[-2], p[-1]

    prev = (
        work[work["period"] == prev_p]
        .groupby(schema.category_col)[schema.metric_col]
        .sum()
        .rename("prev")
    )
    curr = (
        work[work["period"] == curr_p]
        .groupby(schema.category_col)[schema.metric_col]
        .sum()
        .rename("curr")
    )
    out = pd.concat([prev, curr], axis=1).fillna(0.0).reset_index()
    out["delta"] = out["curr"] - out["prev"]
    total_delta = float(out["delta"].sum())
    if abs(total_delta) < 1e-9:
        out["contribution_pct"] = 0.0
    else:
        out["contribution_pct"] = (out["delta"] / total_delta * 100.0).round(2)
    out = out.sort_values("delta", ascending=False)

    top = out.iloc[0]
    direction = "increase" if total_delta >= 0 else "decrease"
    text = (
        f"Main driver of the {direction} from {prev_p} to {curr_p} is "
        f"{top[schema.category_col]} ({top['delta']:+.2f})."
    )
    return InsightResult(
        title="Change Drivers",
        narrative=text,
        table=out,
        sources=[
            f"Computed from `{schema.metric_col}` grouped by `{schema.category_col}`",
            f"Periods compared: {prev_p} vs {curr_p}",
        ],
        assumptions=[
            "Driver contribution is based on additive difference between the latest two periods.",
            "Negative contribution means the category pulled the total downward.",
        ],
    )


def compare_entities(df: pd.DataFrame, schema: DataSchema, entity_a: str, entity_b: str) -> InsightResult:
    """
    Compare two category entities with simple significance signal.
    """
    if not schema.category_col:
        raise ValueError("No category column available for entity comparison.")
    subset = df[df[schema.category_col].astype(str).isin([entity_a, entity_b])].copy()
    if subset.empty:
        raise ValueError("Selected entities are not present in data.")
    subset[schema.metric_col] = pd.to_numeric(subset[schema.metric_col], errors="coerce")
    subset = subset.dropna(subset=[schema.metric_col])

    grp = subset.groupby(schema.category_col)[schema.metric_col].agg(["mean", "sum", "count"]).reset_index()
    if len(grp) < 2:
        raise ValueError("Need both entities with valid metric values.")

    a_row = grp[grp[schema.category_col] == entity_a].iloc[0]
    b_row = grp[grp[schema.category_col] == entity_b].iloc[0]
    diff_pct = ((a_row["mean"] - b_row["mean"]) / max(abs(b_row["mean"]), 1e-9)) * 100.0
    significant = "Yes" if abs(diff_pct) >= 10 else "No"
    narrative = (
        f"{entity_a} vs {entity_b}: average is {diff_pct:+.2f}% different. "
        f"Statistically relevant difference signal: {significant} (rule: >=10% gap)."
    )
    grp = grp.rename(columns={"mean": "avg_value", "sum": "total_value", "count": "records"})
    return InsightResult(
        title="Entity Comparison",
        narrative=narrative,
        table=grp,
        sources=[f"Comparison from `{schema.category_col}` grouped values in uploaded dataset."],
        assumptions=[
            "Significance is a practical business rule based on average gap threshold (10%), not formal hypothesis testing."
        ],
    )


from unittest.mock import MagicMock, patch

import pandas as pd

from talk_to_data.assistant import answer_talk_to_data
from talk_to_data.data_utils import infer_schema, prepare_timeseries
from talk_to_data.document_loader import load_uploaded_file
from talk_to_data.llm_layer import (
    clear_gemini_model_cache,
    enrich_csv_insight,
    insight_payload_for_llm,
    resolve_generate_content_model_id,
)
from talk_to_data.pdf_qa import NOT_PRESENT, answer_from_pdf_text


def test_infer_schema_and_prepare_timeseries():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=20, freq="D"),
            "sales": range(20),
            "region": ["North", "South"] * 10,
        }
    )
    schema = infer_schema(df)
    assert schema.date_col == "date"
    assert schema.metric_col == "sales"
    ts = prepare_timeseries(df, schema)
    assert not ts.empty
    assert {"date", "value"} == set(ts.columns)


def test_load_uploaded_csv():
    csv_text = "a,b\n1,hello\n2,world\n"
    raw = csv_text.encode("utf-8")
    doc = load_uploaded_file("sample.csv", raw)
    assert doc.kind == "csv"
    assert doc.df is not None
    assert list(doc.df.columns) == ["a", "b"]
    assert doc.pdf_text == ""


def test_entity_compare_query_path():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=20, freq="D"),
            "sales": [100 + i for i in range(20)],
            "region": ["North", "South"] * 10,
        }
    )
    schema = infer_schema(df)
    out = answer_talk_to_data("North vs South", df, schema)
    assert out.intent == "entity_compare"


def test_pdf_match_returns_lines():
    text = "Introduction\nRevenue grew in Q4.\nFooter note\n"
    out = answer_from_pdf_text("revenue Q4", text)
    assert "Revenue" in out or "revenue" in out.lower()


def test_pdf_no_match_not_present():
    assert answer_from_pdf_text("xyzabc123nope", "only hello world here") == NOT_PRESENT


def test_insight_payload_for_llm_has_table_rows():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=20, freq="D"),
            "sales": [100 + i for i in range(20)],
            "region": ["North", "South"] * 10,
        }
    )
    schema = infer_schema(df)
    out = answer_talk_to_data("North vs South", df, schema)
    payload = insight_payload_for_llm(out)
    assert "table_rows" in payload
    assert payload["intent"] == "entity_compare"


def test_enrich_csv_insight_none_without_key():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=20, freq="D"),
            "sales": [100 + i for i in range(20)],
            "region": ["North", "South"] * 10,
        }
    )
    schema = infer_schema(df)
    out = answer_talk_to_data("North vs South", df, schema)
    r = enrich_csv_insight("q", out, None)
    assert r.text is None and r.error is None and r.model_used is None


@patch("talk_to_data.llm_layer._get_client")
def test_enrich_csv_insight_with_key(mock_get_client: MagicMock) -> None:
    clear_gemini_model_cache()

    model_entry = MagicMock()
    model_entry.name = "models/gemini-2.5-flash"
    model_entry.supported_generation_methods = ["generateContent"]

    resp = MagicMock()
    resp.candidates = [object()]
    resp.text = "  Plain English summary.  "

    mock_client = MagicMock()
    mock_client.models.list.return_value = [model_entry]
    mock_client.models.generate_content.return_value = resp
    mock_get_client.return_value = mock_client

    df = pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=20, freq="D"),
            "sales": [100 + i for i in range(20)],
            "region": ["North", "South"] * 10,
        }
    )
    schema = infer_schema(df)
    out = answer_talk_to_data("North vs South", df, schema)
    r = enrich_csv_insight("Compare regions", out, "fake-key")
    assert r.text == "Plain English summary."
    assert r.error is None
    assert r.model_used == "gemini-2.5-flash"
    mock_client.models.generate_content.assert_called_once()


@patch("talk_to_data.llm_layer._get_client")
def test_resolve_prefers_gemini_25_over_15(mock_get_client: MagicMock) -> None:
    clear_gemini_model_cache()
    a = MagicMock()
    a.name = "models/gemini-1.5-flash"
    a.supported_generation_methods = ["generateContent"]
    b = MagicMock()
    b.name = "models/gemini-2.5-flash"
    b.supported_generation_methods = ["generateContent"]

    mock_client = MagicMock()
    mock_client.models.list.return_value = [a, b]
    mock_get_client.return_value = mock_client

    mid = resolve_generate_content_model_id("test-key-xyz")
    assert mid == "gemini-2.5-flash"

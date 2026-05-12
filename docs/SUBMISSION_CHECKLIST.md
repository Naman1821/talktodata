# Hackathon Submission Checklist

## Scope Coverage

- Talk to Data (CSV): comparisons, drivers, breakdown, summaries, entity compare — all from uploaded CSV.
- PDF: extracted text + line search (no cloud model).

## Trust and Transparency

- Metric definition when schema is detected (semantic layer)
- Source references and assumptions on CSV insights

## Demo Script

1. Run `streamlit run src/talk_to_data/app.py` (no API key).
2. Upload `data/sample_hackathon.csv` and ask a comparison or breakdown question.
3. Upload a PDF and search for words that appear in the text.
4. Upload a second file and confirm behavior uses only the new file.

## Packaging Readiness

- `README.md` complete with install/run/usage/limitations
- `.env.example` included with non-secret placeholders
- `requirements.txt` includes run + test dependencies
- `tests/test_hackathon_ai.py` includes core sanity tests

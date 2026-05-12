# Judge Playbook (Round 2)

## 1) One-line value proposition

Non-technical users ask business-style questions on **their own** CSV and get tables, charts, and short narratives computed **in-session** with explicit sources — no external LLM. PDFs support **line search** on extracted text only.

## 2) Exact requirement mapping

### Talk to Data (CSV)

- Keyword routing to deterministic aggregates (period compare, drivers, breakdown, summaries, entity compare).
- Transparent sources and assumptions.

### PDF

- Text extraction locally; answers are **matching lines** from that text, or **Not present.**

## 3) Demo flow (2.5 minutes)

1. Upload `data/sample_hackathon.csv`.
2. Ask for breakdown by region or “North vs South”.
3. Show table, chart, and source transparency.
4. Optional: upload a PDF and search for a phrase that exists in the text.

## 4) Anticipated judge questions

- **Trust?** Numbers come from pandas on the uploaded CSV; PDF matches are substring/token matches in extracted text.
- **Data leaving the machine?** No cloud AI in the default path.

## 5) What not to claim

- Do not claim semantic PDF Q&A like an LLM.
- Do not claim formal statistical inference beyond the stated heuristics.

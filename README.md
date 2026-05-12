# Talk to Data — Theme 1 (NatWest Code for Purpose)

## [Deployed app link](https://talk-to-data-4vyr37ecaehsze6zjoewgg.streamlit.app/)



Streamlit app in `src/talk_to_data/` (entry: `app.py`, layout in `views.py`, analytics in the same package). Matches the hackathon brief: **clarity, trust, speed**, plus **optional free-tier AI (Gemini)** on top of **your upload only**.

Folder layout: [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md).

## Overview

Non-technical users upload a **CSV** (or **PDF**) and ask business-style questions. **All numbers and tables for CSV are computed locally** with pandas (keyword routing to compare, drivers, breakdown, summaries, entity compare). **Gemini is optional**: it only **rephrases** the verified JSON payload (CSV) or answers **strictly from extracted PDF text** — so judges see both **trust** (transparent tables + sources) and **AI** (brief requirement for free-tier models).

## Features (implemented)

- CSV upload with inferred date, metric, and optional category columns; **semantic layer** (metric definition) in the UI.
- **Verified insights**: tables, charts, sources, assumptions — same session as the file.
- **Optional Gemini**: grounded narrative after the verified block (CSV); PDF tab for document-only Q&A + offline line search fallback. The app **auto-picks** a `generateContent` model for your key via **ListModels** (prefers 2.5 Flash when available—no hardcoded 404 chain).
- PDF text extraction (`pypdf`); new upload replaces session context.
- Clearing the file uploader (×) drops the loaded document from the session so the main view resets (refresh-with-empty-picker still uses in-memory session when the server keeps it).
- `File [name] Loaded Successfully` on success; `Error: Could not read file.` on parse failure.

## Install and run

```bash
python -m venv .venv

Delete the current terminal
Create a new one and then do:

source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```


## Docker (Postgres + pgvector + Streamlit)

Run the database and app in containers. **Semantic PDF indexing** in the UI needs a **Gemini API key** for embeddings (same as chat).

```bash
export GOOGLE_API_KEY=your_key   # optional for CSV-only; required for Gemini + vector embed
docker compose build
docker compose up -d
```


```bash
streamlit run src/talk_to_data/app.py
```



**Gemini key (pick one):**

- **In the app:** use the **Gemini API** panel on the right — paste key → **Save key** (this **Streamlit session** only; full refresh clears it; not in Git). **Use Gemini AI** toggles calls on/off; **Remove saved key** clears the session copy. For a key that survives refresh, use `.env` / secrets below.
- **Or** set `GOOGLE_API_KEY` in `.env` (see `.env.example`) or Streamlit Cloud secrets.

```bash
streamlit run src/talk_to_data/app.py
```

Sample data: `data/sample_hackathon.csv`


- **Streamlit:** http://localhost:8501  
- **Postgres:** `localhost:5432`, user/password/db `natwest` / `natwest` / `talkdata`  
- The Streamlit container sets `DATABASE_URL` automatically. For **local** `streamlit run` against the DB container, add to `.env`:  
  `DATABASE_URL=postgresql://natwest:natwest@localhost:5432/talkdata`

The pgvector extension is enabled on first DB init via `docker/init-scripts/01-pgvector.sql`.

## Tech stack

- Python 3, Streamlit, Pandas, NumPy, pypdf  
- **Google Generative AI (Gemini)** — optional, free tier  
- **Postgres + pgvector** — optional semantic search for PDF chunks (Docker)  
- pytest  

## Usage examples (CSV)

- “Why did revenue change?” (needs category column for drivers)
- “North vs South”
- “Show breakdown by region”
- “Weekly summary for leadership”

## Tests

```bash
pytest -q
```

## Honesty note (judges)

- Without any key (and no `.env`), the app is **fully usable** with verified outputs only (plus PDF line search).
- Each reviewer can paste their own key in the right-hand panel for this session, or use `.env` locally.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

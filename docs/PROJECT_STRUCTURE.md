# Repository layout

```
.
├── src/talk_to_data/        # Streamlit app + analytics package
│   ├── app.py               #   entry: `streamlit run src/talk_to_data/app.py`
│   ├── views.py             #   UI layout (hero, panels, tabs)
│   ├── analytics.py         #   pandas analytics (drivers, breakdown, compare, summaries)
│   ├── assistant.py         #   intent routing + insight assembly
│   ├── data_utils.py        #   schema inference + timeseries prep
│   ├── document_loader.py   #   CSV/PDF upload parsing
│   ├── query_parser.py      #   vs-entity extraction, ambiguity hints
│   ├── semantic_layer.py    #   human-readable metric definition
│   ├── pdf_qa.py            #   offline line search over PDF text
│   ├── llm_layer.py         #   optional Gemini (grounded, model auto-pick)
│   ├── gemini_embeddings.py #   text-embedding-004 helpers
│   └── pgvector_store.py    #   Postgres + pgvector persistence
├── tests/                   # Unit tests
├── data/                    # Sample CSVs (e.g. sample_hackathon.csv)
├── assets/screenshots/      # Screenshots for README
├── docs/                    # Pitch, checklist, judge playbook
├── docker/init-scripts/     # DB init (CREATE EXTENSION vector)
├── docker-compose.yml       # Postgres (pgvector) + Streamlit
├── Dockerfile               # Streamlit image for compose
├── requirements.txt         # Runtime dependencies
├── README.md
└── LICENSE                  # Apache-2.0
```

Run the app from the repo root:

```bash
streamlit run src/talk_to_data/app.py
```

`app.py` adds `src/` to `sys.path` so the `talk_to_data` package imports cleanly when Streamlit runs it as a script.

# 💡 BAAP - Business Analytics Automation Platform

BAAP turns any spreadsheet or database table into a full analytics workspace: upload, clean, validate, explore, visualize, forecast, and report on your data - no schema required, no data science
background needed. Runs entirely offline out of the box. AI Insights and Chat with Data automatically upgrade to LLM-narrated answers if you add an API key.
_______________________________________________________________________________________
## Quick start

```bash
git clone https://github.com/rahamat-ds/BAAP
cd BAAP
uv venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
streamlit run app.py
```
_______________________________________________________________________________________
### Optional: enable AI features

```bash
cp .env.example .env
# then edit .env and set ONE of:
#   ANTHROPIC_API_KEY=...
#   OPENAI_API_KEY=...
#   GEMINI_API_KEY=...
pip install anthropic     # matching the key you set
```
See `docs/CONFIGURATION.md` for every setting.
_______________________________________________________________________________________
## What's inside

- **Upload any data.** CSV, Excel (multi-sheet), JSON, ZIP, or connect a
  SQL database. Load multiple datasets and switch between them.
- **Clean it.** Duplicates, missing values, outliers, text/date
  normalization, one-click auto-clean, full undo history.
- **Trust it.** Business-rule validation and a structural data-quality
  score — generalized to work on *any* dataset via automatic column-role
  detection, not a fixed schema.
- **Explore it.** 14 interactive chart types, KPI dashboards, RFM customer
  segmentation, ABC product classification, and (for e-commerce order
  data) courier/RTO/shipping analytics.
- **Predict it.** Forecasting (Ridge / Random Forest / moving average) and
  anomaly detection (z-score / IQR / Isolation Forest / time-series).
- **Ask it questions.** Chat with your data in plain English, and get
  automated business insights — both work fully offline.
- **Query it.** A real SQL workspace across every loaded dataset.
- **Report it.** One-click PDF, Excel and PowerPoint exports.

See `docs/FEATURES.md` for the full list.
_______________________________________________________________________________________
## Project structure

```
BAAP/
├── app.py                Streamlit entrypoint (navigation, sidebar)
├── config/               Settings, semantic column roles, palettes
├── core/                 Mapping engine, dtype helpers, domain reference data
│   └── domain/           Indian-retail master data (geography, products, ...)
├── database/             SQLite engine + repository (session history)
├── models/               Typed dataclasses shared across modules
├── pipelines/            Ingestion, cleaning, validation, profiling, transform
├── analytics/            KPIs, customers (RFM), products (ABC), retail ops, insights
├── forecasting/          Forecasting models + anomaly detection
├── llm/                  Provider-agnostic AI client (Anthropic/OpenAI/Gemini)
├── chat/                 Natural-language querying + conversation history
├── visualization/        Plotly chart factory + theme/CSS
├── services/             Session state, dataset loading, reports, sample data
├── frontend/pages/       One file per Streamlit page (21 pages)
├── tests/                Unit tests + full-page AppTest smoke tests
├── docs/                 Architecture, configuration, features, migration notes
└── data/                 uploads/ reports/ samples/ (gitignored) + insightflow.db
```

See `docs/ARCHITECTURE.md` for the full design rationale.
_______________________________________________________________________________________
## Running tests

```bash
uv pip install -r requirements.txt   # includes pytest
pytest
```
92 tests cover every pipeline/analytics/forecasting/chat function directly,
plus a full Streamlit `AppTest` smoke test that renders all 21 pages in
both the empty and data-loaded state.
_______________________________________________________________________________________
## Feedback & Contribution

If you found any bugs or have a feature request, create an issue.
If you want to improve the work, then
```
Fork the Repo ⇒ Create a Branch ⇒ Ensure all tests pass ⇒ Open a Pull Request 
```

### If you liked this work, consider giving it a Star. 🌟

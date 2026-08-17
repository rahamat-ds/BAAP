# Architecture

BAAP is a layered, dataset-agnostic analytics platform built on Streamlit.
Every layer is a plain Python package with no Streamlit imports except the
`frontend/` layer itself — pipelines, analytics, forecasting, llm, chat and
services are all independently unit-testable and reusable outside the UI.

## Layer diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  frontend/            Streamlit pages + app.py entrypoint       │
│  (UI only — no business logic)                                  │
└───────────────┬─────────────────────────────────────────────────┘
                │
┌────────────────▼────────────────────────────────────────────────┐
│  services/            Orchestration: session, dataset loading,  │
│                        report generation, sample data           │
└──┬─────────┬─────────┬──────────────┬───────────────────────────┘
   │         │         │              │           │          │
┌──▼───┐ ┌───▼─────┐ ┌──▼──────┐ ┌▼────────┐ ┌▼──────┐ ┌▼──────────┐
│pipe- │ │analytics│ │forecast-│ │llm/chat │ │visual │ │ database  │
│lines │ │         │ │ing      │ │         │ │ization│ │           │
└──┬───┘ └───┬─────┘ └────┬────┘ └────┬────┘ └───────┘ └───────────┘
   │         │            │           │
   └─────────┴─────┬──────┴───────────┘
                   │
              ┌─────▼──────┐
              │   core/    │  mapping engine, dtype helpers,
              │            │  domain reference data
              └─────┬──────┘
                    │
              ┌──────▼─────┐
              │   models/  │  typed dataclasses (schemas)
              │  config/   │  settings, roles, palettes
              └────────────┘
```

## The semantic column-mapping engine (`core/mapping.py`)

This is the architectural core that makes BAAP work on **any**
tabular dataset, not just its own bundled sample. Every analytics,
forecasting, and chat module reads a *role* (`revenue`, `date`,
`customer_id`, `category`, ...) rather than a hard-coded column name.

1. `auto_map(df)` scores every column against every role using header-text
   regex patterns plus a dtype gate (e.g. a `revenue` candidate must be
   numeric; a `date` candidate must actually parse as a date).
2. Users can override any mapping in **Upload Center → Column Mapping**.
3. Every downstream page reads `mapping.get("revenue")` etc. and gracefully
   shows a "map this column to unlock this view" hint when a role isn't
   mapped, rather than crashing.

An **optional extended role set** (`core.mapping.auto_map_retail`) detects
e-commerce logistics columns (courier, RTO, shipping mode, delivery days)
on top of the core mapping. This powers the **Retail Operations** page,
which is InsightFlow's original domain differentiator — it simply shows
an explanatory message on datasets that don't have this data.

## Session management

"Session management" is instead implemented as: a stable per-browser-tab
session id, a multi-dataset in-memory registry (`services/session_service.py`),
and SQLite-backed history (datasets loaded, reports generated, chat
transcripts, saved SQL queries, activity log) scoped by that session id and
viewable in the **History** page.

## Data flow for a typical page

```
Upload Center            core.mapping.auto_map()
     │                          │
     ▼                          ▼
services.dataset_service.register_and_log()
     │
     ▼
services.session_service  (in-memory registry, keyed by dataset name)
     │
     ▼
frontend.common.require_dataset()  ──►  (name, df, mapping)
     │
     ▼
analytics / forecasting / chat / visualization  (pure functions on df + mapping)
     │
     ▼
Streamlit page renders the result
```

## Testing strategy

- **Unit tests** (`tests/test_*.py`) exercise every pipeline/analytics/
  forecasting/chat function directly on synthetic data — fast, no
  Streamlit runtime needed.
- **Page-level smoke tests** (`tests/test_app_pages.py`) use Streamlit's
  `AppTest` harness to actually execute every page's script, once with no
  dataset loaded and once with a real dataset pre-seeded into session
  state, asserting no uncaught exception. This is what catches Streamlit
  API misuse, duplicate widget IDs, and import wiring mistakes that pure
  unit tests can't see.

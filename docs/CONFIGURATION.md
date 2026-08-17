# Configuration Guide

All configuration lives in `config/settings.py` and is resolved from
environment variables (optionally via a local `.env` file — copy
`.env.example` to `.env` to get started). No code changes are needed to
reconfigure the app.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(empty)* | Enables AI-narrated insights and chat via Claude. |
| `OPENAI_API_KEY` | *(empty)* | Enables AI features via OpenAI. |
| `GEMINI_API_KEY` | *(empty)* | Enables AI features via Google Gemini. |
| `LLM_PROVIDER` | `auto` | Force `anthropic` / `openai` / `gemini`, or `auto` to pick whichever key is set (checked in that order). |
| `APP_CURRENCY` | `₹` | Currency symbol used across KPIs, charts and reports. |
| `APP_TARGET_REVENUE` | `5000000` | Optional revenue target reference (available to future goal-tracking features). |
| `MAX_UPLOAD_MB` | `500` | Max upload size accepted by the Upload Center. |
| `LOG_LEVEL` | `INFO` | Python logging level for the `insightflow` logger namespace. |
| `ENABLE_SQL_WORKSPACE` | `true` | Feature flag for the SQL Workspace page. |
| `INSIGHTFLOW_DATA_DIR` | `./data` | Overrides where uploads, reports, samples and the SQLite history DB are stored. |

InsightFlow runs **fully offline** with zero environment variables set —
AI Insights and Chat with Data automatically fall back to deterministic,
rule-based logic when no LLM key is configured.

## Enabling an AI provider

1. Install the matching optional dependency:
   ```bash
   pip install anthropic        # or: pip install openai
                                 # or: pip install google-generativeai
   ```
2. Set the corresponding API key in `.env`.
3. Restart the app. The sidebar will show "🟢 &lt;Provider&gt; connected"
   instead of "⚪ Offline analyst mode".

Model names used per provider live in `config/settings.py` under
`LLM_MODELS` and can be edited directly if you want to pin a different
model version.

## Semantic column roles

The mapping engine's regex patterns (`ROLE_PATTERNS`, `RETAIL_ROLE_PATTERNS`)
and human-readable labels (`ROLE_LABELS`) also live in `config/settings.py`.
If your organization uses very different column-naming conventions, you can
extend these patterns without touching any analytics code — every module
downstream reads the *role*, not the raw pattern.

## Theming

Colors, the Plotly template, and CSS all live in `visualization/theme.py`.
The Streamlit chrome theme (used for the native widget palette) is in
`.streamlit/config.toml`.

## Streamlit runtime settings

`.streamlit/config.toml` controls the max upload size accepted by
Streamlit's own uploader widget (keep this in sync with `MAX_UPLOAD_MB`),
the dark theme palette, and disables usage-stats collection.

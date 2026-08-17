# Migration Notes

This describes what changed for anyone who worked with the previous
version of BAAP (the original "InsightFlow") and wants to carry over
custom work.

## Breaking changes

- **Package layout changed completely.** `core/`, `modules/`, `pages/`,
  `utils/`, `scripts/` (the old layout) no longer exist. See
  `docs/ARCHITECTURE.md` for the new layout. If you had custom pages or
  modules, they'll need to be ported into the new `frontend/pages/` +
  `analytics/`/`pipelines/` structure.
- **`utils.session` → `services.session_service`.** The old direct
  `st.session_state["df"]` single-dataset pattern is replaced by a
  multi-dataset registry. `get_dataset()` → `services.session_service.get_df()`.
- **`modules.schema.validate_schema()` removed.** The old hard-coded
  `REQUIRED_COLUMNS` schema check (which, as a pre-existing bug, required
  an `order_id` column the generator never produced, and a `discount`
  column when the generator produced `discount_percent`) is replaced by
  the semantic column-mapping system (`core.mapping`) plus the
  generalized `pipelines.validation` business-rule checks. There is no
  drop-in replacement function — any dataset now works without a fixed
  schema.
- **`scripts/generate_dataset.py` → `services/sample_data_service.py`.**
  Same domain data, but now reproducible via a `seed` parameter, adds the
  previously-missing `order_id` column, and optionally injects realistic
  data-quality issues (see `docs/FEATURES.md`). The CLI entrypoint moved:
  `python -m services.sample_data_service` (was `python scripts/generate_dataset.py`).
- **No `data/generated/retail_orders1.csv` checked in.** Sample data is
  now generated on demand into `data/samples/` (gitignored) rather than
  committed to the repository.

## New capabilities (nothing removed, only added)

Everything the original InsightFlow could do, it still does — cleaning,
validation (now generalized), the retail-domain analytics (now in
**Analytics Explorer** + **Retail Operations**), and dashboards. On top of
that, this version adds: multi-dataset handling, forecasting, anomaly
detection, AI insights, chat-with-data, SQL workspace, PDF/Excel/PPTX
report generation, session history, and works on datasets beyond the
bundled retail schema.

## Simplifications made deliberately

- **No user authentication.** See `docs/ARCHITECTURE.md` for the
  reasoning. If you need multi-user auth, the reference project's
  `core/auth.py` + `core/db.py` `users` table pattern is a reasonable
  starting point to layer on top of `database/engine.py` — nothing in
  `services/`, `analytics/`, or `pipelines/` would need to change, since
  they're user-agnostic.
- **Demographic charts (age/gender histograms) were not ported.** The
  original analytics page had gender/age distribution charts hard-coded
  to the retail dataset's `gender`/`age` columns. Since these aren't
  general business-analytics concepts (unlike revenue/date/customer_id),
  they didn't fit the dataset-agnostic mapping engine and were left out
  rather than force-generalized into something awkward. They're easy to
  re-add as a small "Demographics" tab in `frontend/pages/analytics_explorer.py`
  if you want them back for the retail sample specifically.

## Upgrading an existing deployment

1. Back up any custom pages/modules you added to the old layout.
2. Replace the repository contents with this version.
3. Copy `.env.example` to `.env` and fill in any API keys you use.
4. `pip install -r requirements.txt`
5. `streamlit run app.py`
6. Re-port any custom pages into `frontend/pages/`, using the existing
   pages as a template for the `bootstrap()` / `require_dataset()` pattern
   (see `frontend/common.py`).

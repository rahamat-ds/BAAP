# Feature List

## Data ingestion
- CSV, Excel (multi-sheet), JSON, ZIP archives, and SQLite/SQL database
  connections, with automatic character-encoding and delimiter detection.
- Multiple datasets can be loaded and worked on simultaneously; switch the
  active dataset from the sidebar at any time.
- One-click bundled sample: a realistic 6,000-order **Indian retail
  e-commerce** dataset with configurable size, a fixed random seed for
  reproducibility, and a small amount of intentional missing values /
  duplicates / price outliers so the cleaning and validation tools have
  real work to do.

## Data quality
- **Cleaning:** duplicate removal, six missing-value strategies, outlier
  removal/clipping (IQR or z-score), text case/whitespace normalization,
  date standardization, type conversion, column rename/drop, one-click
  "Auto-clean", and a full undo history.
- **Validation:** business-rule checks (negative revenue, selling below
  cost, invalid quantity, future-dated rows, duplicates, missing values)
  with severity levels, a 0–100 score, and CSV export of offending rows.
  Generalized from column *roles*, so it works on any dataset, not a fixed
  schema.
- **Profiling:** column-level stats, missing-value breakdown, correlation
  matrix with strong-pair detection, and a separate 0–100 structural
  quality score.

## Analytics
- **KPIs:** revenue, profit, margin, orders, AOV, unique customers,
  revenue/customer, units sold — each with period-over-period deltas where
  a date column is mapped.
- **Analytics Explorer:** guided Sales / Products / Customers tabs plus
  automated rule-based intelligence insights.
- **Customer Analytics:** RFM segmentation (6 segments), estimated
  lifetime value, and configurable churn-risk flagging.
- **Product Analytics:** ABC (Pareto) classification, per-product
  performance, category breakdown.
- **Retail Operations:** courier performance, RTO/return-rate analysis,
  shipping-mode breakdown, delivery-time distribution — auto-activates
  only for order/logistics datasets.
- **14 chart types:** bar, line, area, pie, donut, scatter, bubble,
  histogram, box plot, heatmap, treemap, sunburst, waterfall, correlation
  matrix — all built interactively from any columns.

## Forecasting & anomaly detection
- Three forecasting methods (Ridge regression, Random Forest, moving
  average) with holdout-validated MAE/MAPE and confidence bands.
- Anomaly detection: single-column z-score/IQR, multivariate Isolation
  Forest, and rolling time-series anomaly detection.

## AI & chat
- **AI Insights:** works fully offline (rule-based); automatically
  upgrades to AI-narrated insights when an LLM provider key is configured
  (Anthropic, OpenAI, or Gemini — pluggable, auto-detected).
- **Chat with Data:** natural-language Q&A over the active dataset, with
  suggested questions, persisted conversation history, and the same
  offline/AI-upgrade behavior.

## SQL & exports
- **SQL Workspace:** real SQL queries (via an in-memory SQLite engine)
  across every loaded dataset at once, with saved-query history.
- **Reports:** one-click PDF (with charts + AI insights), Excel (styled,
  multi-sheet, with a KPI summary tab), and PowerPoint export.
- **Export Data:** raw CSV / Excel / JSON export of any loaded dataset.

## Session management
- Multi-dataset in-session registry with rename/remove/activate.
- SQLite-backed history: datasets loaded, reports generated, chat
  transcripts, saved SQL queries, and a general activity log — filterable
  by "this session" or "all time" in the **History** page.

## Configuration
- Every setting (currency, LLM provider, upload limits, feature flags,
  data directory) is environment-variable driven — see
  `docs/CONFIGURATION.md`.

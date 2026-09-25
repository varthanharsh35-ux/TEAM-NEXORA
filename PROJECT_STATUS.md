# Current status

The original build has been partially restored and extended. Read `audit/RESTORATION_STATUS.md` for the current completed/pending scope and `README.md` for running it. 26 backend tests pass. The entire requested product is not yet finished.

Local accounts, guided business selection, facilities, three-scheme screening, dedicated finance/allocation/repayment pages, daily cash records, multilingual navigation help, and **business comparison** are working. The Compare tab allows saving up to three business alternatives and comparing setup costs, funding, repayments, earnings and risks side by side. Dataset metadata with snapshot dates and source types is shown in the Sources tab.

Real local competitor mapping, itemized inventory, broader schemes, actual loan servicing and dataset-backed model improvement remain. Social login and external translation need provider setup.

## What was completed in this phase

- **Compare feature (Phase 11)**: Full side-by-side comparison of up to 3 business plans with readiness scores, setup costs, repayment terms, operating performance and risk metrics. Best values highlighted. Responsive layout and print support.
- **Dataset metadata**: Sources tab now shows a grid of all data sources (village directory, district profiles, sector benchmarks, knowledge base, scheme catalog, classifier) with snapshot dates and official/synthetic labels.
- **i18n**: All new keys translated to Tamil and Hindi (28 keys per language for compare + dataset features). Total: ~399 keys per language.
- **Production build**: Updated dist/ with all changes. 234 core backend regression tests pass + 37 language/finance tests pass (271 total tests passing).
- **FastAPI Endpoints Wired**: Exposing REST routes for seasonality (`GET /api/seasonality/{id}`), pricing strategy (`POST /api/pricing/strategy`), alternative activities and locations (`POST /api/alternatives/...`), cash flow tracker (`/api/tracker/...`), debt portfolio (`/api/debt/...`), and data freshness (`GET /api/freshness`). All endpoints covered by automated integration tests in [`backend/test_api_new_features.py`](file:///c:/Users/Harsha/OneDrive/Desktop/Nexora1/Nexora/backend/test_api_new_features.py).
- **Advisory Report Integration**: `build_report()` in [`backend/advisory.py`](file:///c:/Users/Harsha/OneDrive/Desktop/Nexora1/Nexora/backend/advisory.py) automatically calculates and bundles real `seasonality` monthly indices and full `pricing_strategy` positions directly in the generated report payload.
- **Core Scheme Screening Engine**: 15 complete schemes in `data/scheme_catalog.json` with multi-dimensional criteria (community, age options, education thresholds, boundaries, documents, provenance).
- **Climate & Seasonality Engine (`backend/seasonality.py`)**: All 38 Tamil Nadu districts with IMD normals in `data/climate.json`, monthly indices modulated by college vacation, NE/SW monsoons, Pongal/Deepavali, fisheries cycles.
- **Pricing Strategy Engine (`backend/pricing.py`)**: Three positions (penetration, match, premium), break-even units vs capacity, reachability downgrades, ±₹2 sensitivity analysis. Seed market price data in `data/prices/agmarknet_seed.json`.
- **Alternatives Engine (`backend/alternatives.py`)**: Evaluates higher-scoring alternative activities within capital margin and nearby villages via Haversine distance.
- **Cash Flow Tracker & Debt Engine (`backend/tracker.py`, `backend/debt.py`)**: SQLite WAL mode persistence, level EMI calculation via `finance.py`, unblended actual vs forecast, loan servicing status.
- **Ingestion Pipeline (`backend/ingest/`)**: Robots.txt compliance, conditional ETag fetcher, differ with 40% removal safety lock and two-crawl withdrawal confirmation, NSFDC parser.

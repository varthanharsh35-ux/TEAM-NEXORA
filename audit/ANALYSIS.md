# Original project analysis

Scope: PDF spec read; newer user financial and Tamil Nadu instructions control conflicts. Every original file was read for inventory/hash/content scanning. 37,588 files inventoried; vendor/generated files were not semantically reviewed line by line. Original author-owned files are preserved in original-project.zip. This is an audit of the baseline, not the new implementation.

## UI

- `frontend/src/index.css` — Low contrast, small text, excessive motion and gradients.
- `frontend/src/style.css` — Unused competing scaffold stylesheet.
- `frontend/src/pages/LandingPage.jsx` — Unsupported 15,000 businesses, 120 schemes, 45% savings; decorative scrolling.
- `frontend/src/components/Navbar.jsx` — Untranslated navigation and mobile controls.
- `frontend/src/components/Sidebar.jsx` — Crowded navigation, unsupported Bhashini attribution.
- `frontend/src/pages/AssessmentPage.jsx` — No per-step validation; Maharashtra defaults; hardcoded demographic options.
- `frontend/src/components/LocationPicker.jsx` — Remote tiles/geocoder, stale state after selection, unsafe popup HTML.
- `frontend/src/pages/FeasibilityDashboard.jsx` — English charts, dense cards; Helvetica PDF cannot represent Tamil/Hindi.
- `frontend/src/pages/FinancialPage.jsx` — Stale fetch race; hardcoded numeric projections and locale.

## Logic

- `backend/models.py` — Wrong defaults; missing finite/upper input constraints.
- `backend/routers/financial.py` — No required margin leverage or scheme route; allocation can exceed investment; zero treated as absent; cashflow replaces short input arrays with invented data.
- `backend/routers/schemes.py` — Monthly calculation; grace period added outside total tenure; desired payment cannot cover interest yet emits schedule; zero-rate reverse solve undefined.
- `backend/routers/assessment.py` — Offline POIs become zero competitors and first-mover advantage; score rules imply validation; positive profit floor; scheme matching ignores eligibility and sector.
- `backend/data/schemes_data.py` — Required NSFDC schemes absent; unsupported uniform CIBIL/rate/subsidy claims.

## Broken feature

- `frontend/src/pages/SchemesPage.jsx` — Coordinates restore tests wrong fields; default 720 CIBIL and turnover; response races.
- `frontend/src/pages/CreditMonitoringPage.jsx` — Unverified default 720 credit score presented as monitoring.
- `frontend/src/pages/DebtManagementPage.jsx` — Negative inputs accepted; remaining zero replaced with principal.
- `frontend/src/pages/CashFlowPage.jsx` — Period ordering and finite input validation absent; storage writes unguarded.
- `frontend/src/pages/Dashboard.jsx` — Browser snapshots can diverge from server reports.
- `frontend/src/pages/ProfilePage.jsx` — No shared validated profile; browser-only writes.
- `frontend/src/pages/LoginPage.jsx` — Raw Firebase errors, mandatory auth complexity, no configured provider.
- `frontend/src/contexts/AuthContext.jsx` — Stale captured user; local identity trusted independently.
- `frontend/src/config/firebase.js` — Fake credentials initialise a network-dependent auth flow.
- `frontend/src/services/bhashini.js` — Credentials bundled in browser; failure falls back to English.
- `frontend/src/components/LanguageSelector.jsx` — Advertises translation coverage not actually present.
- `frontend/src/i18n/index.js` — Missing keys silently fall back to English; document lang not synced.

## Architecture

- `backend/main.py` — Duplicate API trees, permissive credentialed CORS, no persistence.
- `frontend/src/services/api.js` — No timeout/cancellation; pages bypass this wrapper.
- `frontend/src/App.jsx` — English error boundary; broad unrelated feature surface.
- `frontend/src/main.ts` — Unused Vite demo entry still typechecked.
- `frontend/src/counter.ts` — Unused scaffold counter.
- `frontend/package.json` — Heavy dependencies; build checks TS scaffold, not JSX semantics.
- `frontend/tsconfig.json` — JSX correctness not typechecked.
- `frontend/vite.config.js` — Proxy unused by hardcoded calls.
- `README.md` — Claims full multilingual/AI and already-running services without reproducible evidence.
- `PROJECT_STATUS.md` — Claims verified full localization despite Tamil missing 306 of 365 keys.

## AI

- `backend/routers/ai.py` — Keyword navigation only, ignores language/context semantics.
- `frontend/src/components/AIAssistant.jsx` — English keyword fallback and prompts; no advisory model.
- `backend/routers/assessment.py` — No trained model, RAG, dataset, evaluation or calibrated uncertainty.

## Translation completeness

Original English keys: 365. Missing: Tamil 306; Hindi 66; Telugu 306; Marathi 290; Kannada 103; Bengali 104; Gujarati 26. Report payloads and exports also bypassed translation.

## Remaining file disposition

- `business-advisor-platform-spec.pdf` — Read all specification text; preserve as supplied reference.
- `GramSahayak_SIH2026_Nexora_6slide.pptx` — Extracted slide text; unverified failure-rate statistics and placeholders must not be treated as evidence.
- `GramSahayak_SIH2026_Nexora_Filled.pptx` — Extracted slide text; unverified failure-rate statistics and placeholders must not be treated as evidence.
- `backend/requirements.txt` — Read baseline content; no separate material flaw beyond grouped findings.
- `frontend/.gitignore` — Read baseline content; no separate material flaw beyond grouped findings.
- `frontend/index.html` — Read baseline content; no separate material flaw beyond grouped findings.
- `frontend/package-lock.json` — Dependency graph parsed; no test evidence or runtime correctness guarantee.
- `frontend/public/favicon.svg` — SVG content inventoried; scaffold/decorative asset, no business logic.
- `frontend/public/icons.svg` — SVG content inventoried; scaffold/decorative asset, no business logic.
- `frontend/src/main.jsx` — Read baseline content; no separate material flaw beyond grouped findings.
- `frontend/src/assets/hero.png` — Binary asset inventoried; no business logic; decorative asset retired.
- `frontend/src/assets/typescript.svg` — SVG content inventoried; scaffold/decorative asset, no business logic.
- `frontend/src/assets/vite.svg` — SVG content inventoried; scaffold/decorative asset, no business logic.
- `frontend/src/layouts/AppLayout.jsx` — Layout structure reviewed; replaces cramped dark shell.
- `frontend/src/layouts/AuthLayout.jsx` — Layout structure reviewed; replaces cramped dark shell.
- `frontend/src/pages/ExistingBusinessPage.jsx` — Read baseline content; no separate material flaw beyond grouped findings.
- `frontend/src/i18n/locales/bn.json` — Parsed all translations and compared flattened key/value coverage.
- `frontend/src/i18n/locales/en.json` — Parsed all translations and compared flattened key/value coverage.
- `frontend/src/i18n/locales/gu.json` — Parsed all translations and compared flattened key/value coverage.
- `frontend/src/i18n/locales/hi.json` — Parsed all translations and compared flattened key/value coverage.
- `frontend/src/i18n/locales/kn.json` — Parsed all translations and compared flattened key/value coverage.
- `frontend/src/i18n/locales/mr.json` — Parsed all translations and compared flattened key/value coverage.
- `frontend/src/i18n/locales/ta.json` — Parsed all translations and compared flattened key/value coverage.
- `frontend/src/i18n/locales/te.json` — Parsed all translations and compared flattened key/value coverage.
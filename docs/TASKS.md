# TASKS.md — one task per agent session

**How to use this file.** Give Astra exactly one task. Paste the task block verbatim,
preceded by:

> Read `docs/RULES.md` and `docs/DATA_CONTRACT.md` first. Then do Task N below, and only
> Task N. Do not modify anything outside the listed files, except test files — adding
> `backend/test_*.py` is always allowed. When you are done, run
> `cd backend && python -m unittest discover -p "test_*.py"` and report what passed, what
> failed, and what you did not finish.

Do not paste grievances, transcripts, or several tasks at once. That is what produced the
last rewrite.

Legend: **[BLOCKER]** must land before the review. **[CORE]** is the differentiator.
**[POLISH]** only if time remains.

---

## Phase 0 — make the codebase workable — DONE (commits 721c601, 6ad8c10, 57d0cbc)

### Task 0.1 — De-minify the frontend [BLOCKER] — DONE
**Result:** Prettier config added, `src/` reformatted, `npm run format` available. Account.jsx 7 lines to 225. Build verified, behaviour unchanged. 9 lines still over 120 chars (unbreakable regex literals and nested JSX template strings).
**Files:** `frontend/src/*.jsx`, `frontend/src/*.js`
**Problem:** `Account.jsx` is 7 lines with a 2,902-character line. `Schemes.jsx`, `Tracker.jsx`,
`Profile.jsx`, `History.jsx`, `Loans.jsx`, `NavHelper.jsx`, `Nearby.jsx` are the same. Nobody,
including an AI agent, can edit this reliably.
**Do:** Reformat every file to conventional React style — one statement per line, max 120
chars, Prettier defaults. Add `.prettierrc` and a `format` npm script. **Change no behaviour.**
**Done when:** `npm run build` succeeds, the app renders identically, no file has a line over
120 characters.

### Task 0.2 — Recover deleted modules [BLOCKER] — DONE
**Result:** 64 files extracted to `attic/original/` with a README. Orphaned `backend/routers/__pycache__` and `backend/data/__pycache__` removed.
**Problem:** `backend/routers/` and `backend/data/` contain only `__pycache__` —
`ai.pyc`, `assessment.pyc`, `financial.pyc`, `schemes.pyc`, `schemes_data.pyc`. The sources
were deleted. The originals are in `audit/original-project.zip`.
**Do:** Extract that zip to `attic/original/`. Commit it. Do not wire it in yet — it is the
reference for what existed. Delete the orphaned `__pycache__` directories.
**Done when:** `attic/original/` contains the full old tree and is committed.

### Task 0.3 — Remove the rigged demo path [BLOCKER] — DONE
**Result:** Branch deleted, fixtures moved to `tests/fixtures/`. `test_cached_locality` replaced with a stubbed-geocoder test of the real path, plus `test_no_hardcoded_place_names` guarding rule 3. 27 backend tests pass.
**File:** `backend/geography.py`
**Problem:** `search()` contains
`if any(x in norm(q) for x in ['sarvanampatti','saravanampatti', ...]): return canned_json`.
It reads `data/raw/sarvanampatti_locality_osm.json`. This makes exactly one place work and
violates rule 3.
**Do:** Delete the branch. Move the three `sarvanampatti_*_osm.json` files to
`tests/fixtures/` and use them as **test fixtures only**.
**Done when:** No place name appears in any conditional in the codebase. A grep for
`saravanampatti` outside `tests/` returns nothing.

---

## Phase 1 — fix the three bugs the user hit

### Task 1.1 — Geocode the gazetteer offline [BLOCKER] [CORE]
**Files:** `scripts/geocode_gazetteer.py` (new), `data/villages.json`, `data/blocks.json`,
`data/aliases.json` (new)
**Problem:** `villages.json` has 12,620 rows of `{id, name, block, district}` and **no
coordinates**. Nothing can be pinned. Every lookup must hit Nominatim live behind a 1 req/sec
global lock, and any failure surfaces as "outside Tamil Nadu." This is the root cause of the
Saravanampatti failure.
**Do:**
1. Write a resumable batch script that resolves every village and block to lat/lon using a
   local Nominatim import or a bulk OSM extract (Geofabrik Southern India). Respect rate
   limits; checkpoint progress; re-runnable.
2. Write `lat`, `lon`, `population` (where available), `source` and `matched_name` back into
   the JSON files.
3. Build `data/aliases.json` for spelling variants — Saravanampatti / Sarvanampatti /
   Saravanampathy, Coimbatore / Kovai / கோயம்புத்தூர். Seed from OSM `alt_name`,
   `name:ta`, `name:hi` plus a transliteration pass.
4. Add urban localities (OSM `place=suburb|neighbourhood|town`), which the TNRD rural
   directory does not contain — this is precisely why Saravanampatti was missing.
5. Report coverage: how many resolved, how many failed, which districts are weakest.
**Done when:** ≥ 95 percent of villages have coordinates; `Saravanampatti`, `Sarvanampatti`
and `சரவணம்பட்டி` all resolve to Coimbatore with coordinates, through the general path with
no special-casing; Lakkapuram in Erode resolves; unresolved places return
`location_unresolved`, never `outside_coverage`.

### Task 1.2 — Fix the Overpass query and split the map layers [BLOCKER]
**Files:** `backend/geography.py`, the `/api/map/nearby` route in `backend/main.py`,
`backend/test_geography_layers.py` (new)
**Problem:** the query is
`nwr["amenity"~"bank|post_office"](around:15000,lat,lon)`. The regex is **unanchored**, so
`bank` matches `blood_bank`. In the project's own cached file for Saravanampatti:
123 banks, 26 post offices, **14 blood banks**, 2 dairy shops. Then
`kind = amenity if amenity in ['bank','post_office'] else 'competitor'` labels all 14 blood
banks as **competitors**. Separately, poultry maps to `["shop"="butcher"]` alone, which
returns nearly nothing, and the radius is hardcoded to 15 km regardless of the 5/10/15 the
user selects.
**Do:**
1. Anchor every regex: `amenity~"^bank$|^post_office$"`.
2. Accept and honour `radius_km`.
3. Build per-activity `direct` and `adjacent` selectors per `PERSONALIZATION.md` §5.
4. Return three separate layers — `competitors`, `drivers`, `amenities` — per
   `DATA_CONTRACT.md` §3. Banks never appear as competitors.
5. Return `completeness: "partial"` with the OSM incompleteness note.
**Done when:** a poultry query returns zero blood banks in any layer; 5 km and 10 km return
different result counts; a test asserts `blood_bank` is never classified as a competitor.

### Task 1.3 — One competitor count [BLOCKER]
**File:** `backend/advisory.py`
**Problem:** the report computes `rivals = round(population * s['competitors_per_10000'] / 10000)`
— a formula from a curated constant — while the map shows OSM results. **They are unrelated
numbers.** The report can claim 12 competitors while the map shows 163 pins.
**Do:** Delete the formula. The competitor count is the mapped count. Where OSM coverage is
thin, show the measured count plus an explicit "coverage is incomplete" note — never silently
substitute an estimate for a measurement.
**Done when:** report count equals map pin count in every test case; rule 5 holds.

---

## Phase 2 — the differentiator

### Task 2.1 — Driver engine [CORE]
**Files:** `data/drivers.json` (new), `backend/drivers.py` (new), tests
**Do:** Implement `PERSONALIZATION.md` sections 3 and 4 — taxonomy, anchored selectors,
weight matrix, half-life distance decay, caps, `demand_score` with band, and `drivers[]`
with named evidence and source URLs.
**Done when:** the café-near-college, warehouse-near-Amazon-FC and poultry-near-temple
worked examples in `PERSONALIZATION.md` §4 reproduce within ±3 score points; **two different
villages with the same activity produce different driver lists** (this is the test that
proves the engine works).

### Task 2.2 — Seasonality and climate [CORE]
**Files:** `data/climate.json` (new), `backend/seasonality.py` (new)
**Do:** IMD district normals as a static file; monthly index per activity with local
modifiers (college vacation, harvest, monsoon, festival) per `PERSONALIZATION.md` §6.
**Done when:** a campus-driven café shows a May–June dip with the reason naming the colleges.

### Task 2.3 — Real prices [CORE]
**Files:** `backend/ingest/parsers/agmarknet.py` (new), `data/prices/`
**Problem:** `sectors.json` hardcodes `"price": 52` for dairy, `"source": "curated-sector-priors"`.
Every dairy in the state gets the same figure.
**Do:** Agmarknet/e-NAM daily prices keyed to the nearest market, with the fallback chain in
`PERSONALIZATION.md` §7. Always return a `{low, mid, high}` band.
**Done when:** two districts return different prices for the same commodity, each with a
source and a date.

### Task 2.5 — Pricing strategy engine [CORE]
**Files:** `backend/pricing.py` (new), `backend/advisory.py`, tests
**Problem:** the whole pricing model is `price = s['price'] * index` — one authored sector
constant times one of only 6 distinct district multipliers, giving 78 possible prices for the
entire state. Every dairy in a district gets the same number regardless of village,
competitors or demand. The "band" is `price*0.9` to `price*1.1`, which is arithmetic, not
evidence. There is no strategy at all, while the LLM writes strategy prose it is forbidden
from putting numbers into.
**Do:** Implement `PERSONALIZATION.md` §7b — three positions (penetration / match / premium),
break-even units at each computed from the existing fixed-cost and debt-service figures,
reachability flagging against capacity, a recommendation driven by `demand_score` and
competitor density with named evidence, and ±₹2 sensitivity.
**Done when:** the same activity in two locations with different competitor density yields
different recommended positions; a position whose break-even exceeds capacity is reported as
unreachable rather than offered; no output claims to know a named competitor's prices.

### Task 2.4 — Rewrite the LLM prompt [CORE]
**File:** `backend/llm.py`
**Problem:** the system prompt says *"No numbers, prices, rates"* and *"Include supply
disruption, seasonal demand and single-buyer dependency in threats."* **It is ordered to
produce the generic advice the user is complaining about**, and it receives only 5 context
fields.
**Do:** Implement `PERSONALIZATION.md` §8 — pass the full `facts` object, allow numbers that
appear in `facts`, require a named local place per section where evidence exists, reject
purely generic risk statements, 2–4 sentences per section. Add the post-generation numeric
validator (extract every numeral, assert membership in `facts`, retry on failure).
**Done when:** the before/after example in §8 is reproduced; a test asserts that output
containing a number absent from `facts` is rejected.

---

## Phase 3 — the missing features

### Task 3.1 — Sector and activity taxonomy, dropdown flow [BLOCKER]
**Files:** `data/taxonomy.json` (new), `GET /api/sectors`, frontend form
**Do:** 13 sectors, 4–8 activities each, with per-activity questions, required facilities,
typical cost range and licences, per `DATA_CONTRACT.md` §2. Replace the free-text box with
sector → activity → questions. Keep the classifier only behind an optional "not sure?" helper.
**Done when:** no free-text business input exists in the main flow.

### Task 3.2 — Scheme catalogue and real screening [BLOCKER]
**Files:** `data/scheme_catalog.json`, `backend/schemes.py`
**Problem:** 3 schemes; `screen()` is 19 lines and checks only community, income and project
size. `gender` is in the data and never read. `age` and `sector` are never read.
**Do:** 12–15 real schemes per `SPEC.md` §4 with full eligibility, terms, documents, apply and
source URLs, verified dates. Rewrite `screen()` so every documented filter is applied, with
reasons and missing-field lists. Add the `withdrawn` lifecycle.
**Done when:** AC3.1 and AC3.2 in `SPEC.md` pass.

### Task 3.3 — Login UI and profile [BLOCKER]
**Problem:** `backend/accounts.py` is sound (PBKDF2, 310k iterations, hashed sessions,
throttling) but the login **UI** was deleted. `LoginPage.jsx` (344 lines) and
`AuthContext.jsx` are in `attic/original/`.
**Do:** Restore register / login / recovery / profile screens against the existing backend.
Add the profile and facilities fields. **Social sign-in only if real OAuth credentials are
configured — otherwise hide the buttons.** A button that fakes success violates rule 4.
**Done when:** a user can register, log in, save a profile, and have it prefill the report form.

### Task 3.4 — Ingestion pipeline [CORE]
**Files:** `backend/ingest/`, `sources.yaml`
**Do:** `INGESTION.md` build order steps 1–5: CLI, fetcher with robots and conditional GET,
snapshots, the NSFDC reference parser with a fixture test, the differ with the `withdrawn`
lifecycle and the two-crawl rule, freshness on every response.
**Done when:** `python -m backend.ingest status` prints a freshness table; a simulated scheme
removal marks it `withdrawn` rather than deleting it; a 40 percent record drop blocks publish.

### Task 3.5 — Inventory and setup plan
**Do:** `DATA_CONTRACT.md` §5 `POST /api/inventory/plan`, per-activity item lists, owned items
deducted, one-time versus recurring separated.

### Task 3.6 — Separate finance, allocation and repayment routes
**Do:** Split the single finance tab into three routes per `SPEC.md`, each with the
traffic-light verdict at the top.

### Task 3.7 — Tracker
**Do:** `DATA_CONTRACT.md` §8. Actuals and forecasts never merged.

### Task 3.8 — Languages
**Do:** Recover the 8 locale files and the Bhashini service from `attic/original/`. Complete
en/ta/hi. Mark the rest as planned. Pluggable provider (Bhashini or Google). Reviewed glossary
for financial terms.

---

## Phase 4 — polish

- **4.1** Charts with printed values and a sentence under each [POLISH]
- **4.2** Emoji wayfinding per `SPEC.md` §9 [POLISH]
- **4.3** PDF and DOCX export — `jspdf` and `docx` were in the old `package.json` [POLISH]
- **4.4** Offline and low-bandwidth handling [POLISH]
- **4.5** "About the data" page rendering `GET /api/freshness` — **open this tab during the
  demo**, it answers most data questions before they are asked [CORE]

---

## Found while working

Agents append newly discovered problems here. Do not fix them in the current session.

- `models/metrics.json` reports accuracy 1.0 and macro-F1 1.0 on a 48-row holdout drawn from
  a 187-row authored synthetic dataset. A perfect score is a red flag to any judge. Once Task
  3.1 lands, the classifier is off the critical path — either retire it or re-document it
  honestly as an optional input helper with its limitations stated.
- `backend/data/` and `backend/routers/` hold orphaned `__pycache__` only — cleared by Task 0.2.
- Latitude and longitude bounds are hardcoded to Tamil Nadu (8–13.7, 76–80.5) across
  `main.py` and `geography.py`. Move to config so coverage is a data boundary, not a code one.

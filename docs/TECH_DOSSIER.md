# TECH_DOSSIER.md — what to tell the panel

Answers to the technical questions a SIH panel actually asks. Every claim here is checkable
against the code. **If a line in this file stops being true, fix the file the same day.**

Nothing in this document oversells. The fastest way to lose a panel is to claim real-time
data or a trained model that does not survive one follow-up question.

---

## 1. "Is this AI, or just formulas?" — the honest architecture

The system has **three distinct layers**, and it is worth saying so plainly, because a panel
that discovers the distinction for itself will assume it was being hidden.

### Layer 1 — a trained classifier (small, and being retired from the critical path)

| | |
|---|---|
| Artefact | `models/business_classifier.joblib` |
| Method | TF-IDF character 2–5 grams into multinomial logistic regression (scikit-learn) |
| Training data | 187 authored rows, augmented to 641 |
| Classes | 12 sectors |
| Holdout | 48 rows, reported accuracy 1.0, macro-F1 1.0 |
| Job | Map a typed business description to one sector label. Nothing else. |

**Say this out loud before you are asked:** a perfect score on a 48-row holdout drawn from a
187-row authored dataset measures whether the model memorised our own phrasings. It is not
evidence of real-world accuracy, and we do not present it as such.

**And say what we did about it:** the main flow no longer uses free text. The user picks
sector and activity from dropdowns (`SPEC.md` §1), so the category is known exactly and no
classifier is needed. It survives only behind an optional *"not sure? describe it"* helper
that suggests a dropdown value the user can override.

That is the correct answer to "your ML is weak" — we removed the need for it rather than
defending a metric we do not believe.

### Layer 2 — deterministic computation (most of the product)

Everything numeric is plain Python, auditable line by line:

- **Finance** — `backend/finance.py`. `Decimal` throughout, `ROUND_HALF_UP`, quantised to
  paise. Project cost = margin ÷ 10 percent; max loan = 90 percent; scheme routing on project
  cost; simple interest accrued across the moratorium and capitalised once; quarterly reducing
  balance thereafter. Unit-tested, and totals reconcile to the paise.
- **Eligibility** — rule evaluation against the scheme catalogue. No model involved, because a
  model must never decide whether someone qualifies for credit.
- **Local demand** — the driver engine (`PERSONALIZATION.md`): real OSM places, a documented
  weight matrix in `data/drivers.json`, half-life distance decay, capped and summed.

**Why deterministic on purpose:** these outputs concern a person's eligibility and debt.
They must be reproducible, explainable and correctable. A language model cannot offer any of
those three. This is a design decision, not a shortcut, and it is worth stating that way.

### Layer 3 — a language model, for prose only

| | |
|---|---|
| Primary | Any OpenAI-compatible endpoint via `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` in `.env` |
| Offline fallback | Qwen3-0.6B, run locally via `backend/llm_worker.py` (`LOCAL_LLM=1`) |
| Output | Structured JSON, validated by a Pydantic schema |
| Constraint | **It may only use numbers that appear in the `facts` object it was given.** Enforced after generation: every numeral in the output is extracted and checked for membership in `facts`; a violation is rejected and regenerated. |

The offline fallback is worth demonstrating — the whole advisory path runs on a laptop with
the network off, which matters for a rural-connectivity story.

**One-sentence version for the panel:** *"Python computes every number and the model writes
the explanation. The model is not allowed to invent a figure, and we validate that
mechanically rather than trusting it."*

---

## 2. "Why did your advice sound generic?" — and what we changed

Be ready for this, because it was true of the earlier build and an honest account of it is
more persuasive than pretending it was always fine.

**Cause one — the prompt commanded generic output.** The previous system prompt in
`backend/llm.py` contained, verbatim:

> "No numbers, prices, rates, loan promises or invented named competitors."
> "Include supply disruption, seasonal demand and single-buyer dependency in threats."

The model was *ordered* to produce "avoid dependency on a single buyer" and forbidden from
citing anything concrete. The boilerplate was hardcoded into the instruction.

**Cause two — the model knew nothing local.** It received five fields: business text,
district id, category, verdict, facilities. No population, no prices, no competitors, no
nearby landmarks. It could not be specific because it had no specifics, and it was capped at
one sentence per section.

**The fix,** in `PERSONALIZATION.md` §8: pass a full `facts` object; permit numbers that
appear in it; require at least one named real place per section where evidence exists;
reject risk statements not tied to a local fact; allow 2–4 sentences.

Same model. Real facts. Permission to use them.

> **Before:** "Watch out for supply disruption, seasonal demand changes, and dependency on a
> single buyer."
>
> **After:** "Your nearest feed supplier is 11 km away in Annur with no second option inside
> the 10 km catchment, so a monsoon road closure in October or November stops production. Two
> of the three existing broiler farms sell to the same Erode trader, so that buyer sets the
> price."

---

## 3. "Is your data real-time?" — say no, then say what you did instead

**The honest answer: no, and nothing in this category is.** Udyam publishes no public API.
Most agency and bank scheme pages are HTML or PDF with no change feed. Anyone claiming
second-by-second currency for this data is claiming something that does not exist.

**What we built instead:** scheduled re-verification with change detection and visible
provenance (`INGESTION.md`).

- Every fact carries the date we last confirmed it and a link to the source.
- Sources are re-crawled on a schedule — schemes weekly, prices daily, POIs on demand with a
  7-day cache.
- Changes are diffed. A moved interest rate or eligibility rule **blocks publication and
  queues for human review**; the previous value keeps serving until a person approves.
- A scheme that disappears from its source is marked `withdrawn` with the date and stays
  visible, greyed out. **It is never silently deleted**, because a user who planned around it
  yesterday deserves to be told it is gone.
- Two consecutive absences are required before marking withdrawn — one absence is usually an
  outage or a broken parser, not a policy change.
- A crawl failure sets `status: "unverified"` and shows an amber badge rather than passing
  stale data off as fresh.
- If parsed record count drops more than 40 percent in a single crawl, publication is blocked
  — one site redesign must never silently empty the scheme catalogue.

**The line to use:** *"We do not claim real-time, because no honest system in this space can.
We claim verifiable freshness: every figure carries the date we last checked it and a link to
where we checked. Here is the page."* Then open the "About the data" page, which renders
`GET /api/freshness` live. Have that tab open before you start.

---

## 4. Datasets

| Dataset | Source | Records | Method | Refresh |
|---|---|---|---|---|
| Villages | TNRD rural directory, geocoded against OSM | 12,620 | official + measured | Quarterly |
| Blocks | TNRD | 385 | official | Quarterly |
| Districts | TN government district list | 38 | official | Quarterly |
| Location aliases | OSM `alt_name`, `name:ta`, `name:hi`, transliteration | — | derived | Quarterly |
| POIs — competitors and drivers | OpenStreetMap via Overpass | on demand | measured | 7-day cache |
| Schemes | NSFDC, NBCFDC, NSKFDC, NHFDC, NMDFC, TAHDCO, PMEGP, Mudra | 12–15 | official | Weekly |
| Commodity prices | Agmarknet, e-NAM | daily series | official | Daily |
| Climate normals | IMD district normals | 38 | official | Annual |
| Driver weights | Authored, documented in `data/drivers.json` | — | **estimated** | Tuned with evidence |
| Sector priors | Authored fallbacks | 13 | **estimated** | Being replaced by real prices |
| Knowledge passages (RAG) | NABARD, NSFDC, curated | 462 | official + curated | As sources update |

**The last two rows are the weakest part of the system and you should say so.** They are
authored constants. They are badged `estimated` in the UI, and Task 2.3 replaces the price
priors with Agmarknet data. Volunteering a known weakness buys credibility for everything
else on the table.

---

## 5. APIs and services

| Service | Use | Notes |
|---|---|---|
| OpenStreetMap Nominatim | Geocoding | Only for gazetteer build and unresolved fallback. Rate-limited, cached, honest User-Agent. |
| OpenStreetMap Overpass | POI queries | 7-day cache per (location, activity). ODbL attribution shown on the map. |
| Agmarknet / e-NAM | Commodity prices | Daily scheduled pull |
| OpenAI-compatible LLM endpoint | Narrative prose | Configurable; key server-side only, never exposed to the browser |
| Qwen3-0.6B (local) | Offline narrative fallback | Runs on CPU; demonstrates offline capability |
| Bhashini | Indian-language translation | Government of India service — preferred over commercial translation for this audience |
| Leaflet | Map rendering | Client-side |

**Secrets** are loaded server-side only, through `backend/config.py`, from a `.env` that is
git-ignored. No key ever reaches the browser. Worth stating unprompted — panels ask.

---

## 6. Stack

- **Backend:** Python, FastAPI, Pydantic validation on every input, SQLite (reports, accounts,
  map cache), scikit-learn, `Decimal` for all money.
- **Frontend:** React 19, Vite, react-router, i18next, Leaflet, Recharts.
- **Auth:** PBKDF2-SHA256 at 310,000 iterations, per-user salt, SHA-256-hashed session tokens,
  7-day expiry, origin checking, 12-attempts-per-minute throttle. **Passwords are never stored
  in plaintext and session tokens are never stored raw.**
- **Tests:** pytest for the backend; fixture tests for every ingestion parser so a source
  redesign fails loudly instead of silently emptying a dataset.

---

## 7. Security and privacy

- All input validated by Pydantic with explicit bounds; `extra='forbid'` on request models.
- SQL exclusively through parameterised queries.
- **Prompt-injection defence:** user input and retrieved passages are passed to the model as
  JSON data with an explicit instruction that they are data and never instructions; output is
  schema-validated, and every numeral is checked against `facts` before display.
- **Personal data minimisation:** community, gender, age and income are collected only because
  scheme eligibility genuinely depends on them. Every field is individually skippable, each
  carries a `why_key` explaining what supplying it unlocks, and a user can get a full
  feasibility report without any of them.
- **Udyam ingestion stores aggregate counts by category, block and year only.** No
  identifiable enterprise is stored or displayed. Re-publishing an individual's registration
  data is not something this project does.
- `robots.txt` respected; honest User-Agent; minimum 5 seconds between requests to a host.

---

## 8. Known limitations — state these before you are asked

1. OpenStreetMap coverage is volunteer-contributed and thin in rural India. Competitor counts
   are a **floor, not a census**, and every count says so on screen.
2. Driver weights are authored priors, not fitted to outcome data. We have no dataset of
   micro-enterprise survival by location to fit against; if one is available, the matrix is a
   single JSON file and can be fitted directly.
3. Catchment population is modelled from density, not measured from a census block.
4. The classifier's reported metrics reflect authored data, not field data — see §1.
5. Scheme terms are indicative. Only the sanctioning agency's sanction letter is binding, and
   every scheme card says so.
6. Coverage is Tamil Nadu. The architecture is state-agnostic; the data is not yet.
7. Financial projections assume the moratorium interest treatment documented in
   `finance.py` — simple interest capitalised once — which must be confirmed with the
   sanctioning agency.

---

## 9. Impact claims — only what is defensible

**Do not claim** a failure-rate reduction. We have no outcome data and inventing a percentage
is the single easiest way to lose a panel's trust.

**Do claim,** because each is demonstrable on screen:

- A beneficiary sees their exact project cost, loan eligibility, scheme routing, quarterly
  instalment and moratorium timeline before applying — computed, not estimated.
- They see real named competitors and real named demand drivers around their own village,
  with distances and source links.
- They see which schemes they qualify for, which need more information, and which they do not
  — with the reason for each, in their own language.
- Every figure carries its source and the date it was last verified, so nothing has to be
  taken on trust.

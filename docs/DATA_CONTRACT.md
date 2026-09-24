# DATA_CONTRACT.md — frozen API shapes

**Version 3.0.** Backend and UI are built in parallel against this file. Neither side may
change a shape without editing this document first (see `RULES.md` rule 9).

Base path: `/api`. All responses JSON. All money in rupees as numbers (not strings, not paise).

---

## 0. Universal envelopes

### 0.1 Provenance — attached to every non-obvious number

```json
{
  "value": 163,
  "unit": "count",
  "provenance": {
    "method": "measured",
    "source": "OpenStreetMap via Overpass",
    "source_url": "https://overpass-api.de/api/interpreter",
    "retrieved_at": "2026-09-24T11:02:00Z",
    "confidence": "high"
  }
}
```

`method` is one of `measured` (counted from real data), `official` (published by a
government source), `derived` (computed from measured/official inputs), `estimated`
(a prior, a guess, a curated constant).

**UI rule:** `estimated` renders with an amber "estimate" chip. `measured` and `official`
render with a source link. Never show a bare number.

### 0.2 Errors

```json
{
  "error": "location_unresolved",
  "message_key": "errors.location_unresolved",
  "detail": { "query": "sarvanampatti", "tried": ["gazetteer", "alias", "fuzzy", "geocoder"] },
  "candidates": []
}
```

Error codes: `location_unresolved`, `location_ambiguous`, `outside_coverage`,
`invalid_input`, `source_unavailable`, `rate_limited`, `auth_required`.

**`outside_coverage` is not `location_unresolved`.** A place we could not find is not a
place that does not exist. The UI must word these differently.

### 0.3 Freshness — on every dataset-backed response

```json
{
  "freshness": {
    "dataset": "schemes",
    "version": "2026-09-24T02:00Z",
    "last_verified": "2026-09-24",
    "next_check": "2026-09-25",
    "status": "fresh"
  }
}
```

`status` is one of `fresh`, `stale` (past `next_check`), `unverified` (last crawl failed).

---

## 1. Location

### `GET /api/locations/search?q=&limit=`

```json
{
  "items": [
    {
      "id": "v:33-4-121",
      "name": "Saravanampatti",
      "names": { "en": "Saravanampatti", "ta": "சரவணம்பட்டி", "hi": "सरवनमपट्टी" },
      "aliases": ["Sarvanampatti", "Saravanampathy"],
      "kind": "locality",
      "block": "Coimbatore North",
      "district": "Coimbatore",
      "lat": 11.0785,
      "lon": 76.997,
      "population": 44231,
      "source": "lgd+osm",
      "match": { "type": "alias", "score": 0.98 }
    }
  ],
  "freshness": {}
}
```

`kind` is one of `district`, `block`, `village`, `locality`, `town`.

**Required:** `lat`/`lon` are mandatory and non-null for every row. A row without
coordinates must not be returned. (Today `villages.json` has 12,620 rows and zero
coordinates — Task 1 fixes this.)

Resolution order, all offline except the last: exact name, alias table, phonetic
(Soundex/Metaphone on transliteration), fuzzy at or above 0.76, live geocoder.

### `GET /api/locations/{id}`

Returns the row above plus:

```json
{
  "context": {
    "population_5km": { "value": 128400, "provenance": {} },
    "population_10km": { "value": 341900, "provenance": {} },
    "density_per_km2": { "value": 1840, "provenance": {} },
    "urban_rural": "peri_urban",
    "climate": {
      "zone": "western_ghats_rainshadow",
      "annual_rainfall_mm": 695,
      "monsoon": ["southwest:jun-sep", "northeast:oct-dec"],
      "summer_max_c": 37,
      "provenance": { "method": "official", "source": "IMD district normals" }
    }
  }
}
```

---

## 2. Business taxonomy (replaces the free-text box)

### `GET /api/sectors`

```json
{
  "sectors": [
    {
      "id": "poultry",
      "names": { "en": "Poultry", "ta": "கோழி வளர்ப்பு", "hi": "मुर्गी पालन" },
      "emoji": "🐔",
      "activities": [
        {
          "id": "poultry.broiler",
          "names": { "en": "Broiler chicken farm" },
          "typical_project_cost": { "min": 90000, "max": 850000 },
          "unit": "bird",
          "questions": [
            {
              "id": "birds",
              "type": "number",
              "label_key": "q.poultry.birds",
              "min": 100,
              "max": 20000,
              "required": true
            },
            { "id": "shed_owned", "type": "boolean", "label_key": "q.poultry.shed" }
          ],
          "required_facilities": ["space", "water", "power"],
          "licences": ["panchayat_noc", "pollution_board_consent"]
        }
      ]
    }
  ]
}
```

The UI renders sector dropdown, then activity dropdown, then 2 to 5 activity-specific
questions. No free-text description anywhere in the main flow.

---

## 3. Local intelligence — the personalization core

### `POST /api/intelligence/local`

Request: `{ "location_id": "v:33-4-121", "activity_id": "food.cafe", "radius_km": 5 }`

```json
{
  "catchment": {
    "radius_km": 5,
    "population": { "value": 128400, "provenance": {} },
    "households": { "value": 33790, "provenance": {} }
  },

  "competitors": {
    "count": 7,
    "within_1km": 2,
    "items": [
      {
        "id": "node/123456789",
        "name": "Hotel Saravana",
        "lat": 11.079,
        "lon": 76.998,
        "distance_m": 420,
        "activity_match": "direct",
        "source_url": "https://www.openstreetmap.org/node/123456789",
        "observed": "2026-09-24"
      }
    ],
    "completeness": "partial",
    "completeness_note_key": "notes.osm_partial",
    "provenance": { "method": "measured", "source": "OpenStreetMap" }
  },

  "drivers": [
    {
      "id": "college",
      "direction": "boost",
      "weight": 0.34,
      "count": 3,
      "nearest_m": 800,
      "emoji": "🎓",
      "evidence": [
        {
          "name": "Kumaraguru College of Technology",
          "distance_m": 800,
          "source_url": "https://www.openstreetmap.org/way/..."
        }
      ],
      "reason_key": "drivers.college.boost",
      "reason_params": { "count": 3, "people": 9000 }
    },
    {
      "id": "competitor_density",
      "direction": "suppress",
      "weight": -0.18,
      "count": 2,
      "nearest_m": 180,
      "emoji": "🏪",
      "reason_key": "drivers.competitor_density.suppress",
      "reason_params": { "count": 2, "radius_m": 500 }
    }
  ],

  "demand_score": { "value": 68, "band": "good", "scale": "0-100", "provenance": { "method": "derived" } },

  "seasonality": [{ "month": 1, "index": 1.02 }, { "month": 5, "index": 0.74 }],
  "seasonality_note_key": "notes.seasonality.college_vacation",

  "footfall_pattern": {
    "peak_hours": ["08:00-10:00", "16:00-19:00"],
    "peak_days": ["mon", "tue", "wed", "thu", "fri"],
    "provenance": { "method": "derived" }
  },

  "freshness": {}
}
```

`band` is `poor` (0–34), `fair` (35–54), `good` (55–74), `strong` (75–100).

**Every driver must carry `evidence` with real named places and source URLs.** A driver
with no evidence is not returned. This is what makes the report specific rather than
generic — see `PERSONALIZATION.md`.

### `GET /api/map/nearby?location_id=&activity_id=&radius_km=`

```json
{
  "layers": {
    "competitors": [
      { "id": "node/1", "lat": 0, "lon": 0, "name": "", "distance_m": 0, "match": "direct", "emoji": "🏪" }
    ],
    "drivers": [
      { "id": "way/2", "lat": 0, "lon": 0, "name": "", "kind": "college", "direction": "boost", "emoji": "🎓" }
    ],
    "amenities": [{ "id": "node/3", "lat": 0, "lon": 0, "name": "", "kind": "bank", "emoji": "🏦" }]
  },
  "centre": { "lat": 11.0785, "lon": 76.997 },
  "radius_km": 5,
  "observed": "2026-09-24",
  "completeness": "partial"
}
```

**Three separate layers, independently toggleable.** `amenities` (banks, post offices) are
never mixed into `competitors`. `radius_km` is honoured, not hardcoded.

**Tag matching must be anchored:** `amenity~"^bank$|^post_office$"`, never
`amenity~"bank|post_office"`. The unanchored form matches `blood_bank` and is the direct
cause of the blood-bank bug.

---

## 4. Schemes

### `GET /api/schemes?community=&gender=&age=&income=&sector=&project_cost=&stage=&state=`

```json
{
  "schemes": [
    {
      "id": "nsfdc.term",
      "name": { "en": "NSFDC Term Loan" },
      "agency": "NSFDC via TAHDCO",
      "status": "eligible",
      "eligibility": {
        "community": ["sc"],
        "gender": "any",
        "age": { "min": 18, "max": 55 },
        "income_limit_rural": 300000,
        "income_limit_urban": 500000,
        "sectors": "any",
        "stage": ["new", "expansion"]
      },
      "terms": {
        "beneficiary_share": 0.1,
        "agency_share": 0.9,
        "project_min": 140000,
        "project_max": 5000000,
        "loan_cap": 4500000,
        "interest_rate": 8.0,
        "tenure_months": 84,
        "moratorium_months": 6,
        "subsidy": null
      },
      "reasons": [],
      "missing": [],
      "documents": [
        { "id": "caste_certificate", "label_key": "docs.caste_certificate", "mandatory": true }
      ],
      "apply_url": "https://pmsuraj.dosje.gov.in/",
      "source_url": "https://nsfdc.nic.in/faqs",
      "verified_on": "2026-09-24",
      "withdrawn_on": null,
      "change_note": null
    }
  ],
  "freshness": {}
}
```

`status` is one of `eligible`, `need_details`, `not_eligible`, `withdrawn`.

- `reasons[]` — why not eligible, as message keys (`reasons.income_above`,
  `reasons.community_mismatch`, `reasons.project_above_max`).
- `missing[]` — fields the user has not supplied yet. `need_details` means *we do not
  know*, never *no*.
- `withdrawn` — the scheme was present in an earlier crawl and is gone now. It stays
  visible, greyed out, with `withdrawn_on` set. Never silently deleted. See `INGESTION.md`.

**Every filter in the query string must actually be applied.** Today `gender`, `age` and
`sector` exist in the data and are never read by `schemes.py`.

---

## 5. Finance

### `POST /api/finance/plan`

Request:

```json
{
  "margin": 100000,
  "project_cost": null,
  "scheme_id": "auto",
  "start_date": "2026-10-01",
  "activity_id": "food.cafe"
}
```

Response. **Keep the existing `finance.py` maths — it is correct and tested.** Only the
envelope changes:

```json
{
  "margin": 100000,
  "project_cost": 1000000,
  "maximum_loan": 900000,
  "scheme": "term",
  "loan": 900000,
  "funding_gap": 0,
  "cap_applied": false,
  "annual_rate": 8.0,
  "tenure_months": 84,
  "moratorium_months": 6,
  "quarterly_payment": 48231.55,
  "moratorium_interest": 36000.0,
  "total_interest": 351432.4,
  "total_repayment": 1251432.4,
  "schedule": [
    {
      "month": 3,
      "due_date": "2026-12-01",
      "opening": 900000,
      "interest": 18000,
      "principal": 0,
      "payment": 0,
      "balance": 918000,
      "moratorium": true
    }
  ],
  "assumptions": [
    { "key": "assumptions.simple_interest_capitalised_once", "confirm_with": "sanctioning_agency" }
  ]
}
```

### `POST /api/inventory/plan`

```json
{
  "items": [
    {
      "id": "incubator",
      "label_key": "inv.incubator",
      "emoji": "🥚",
      "quantity": 2,
      "unit_cost": 18000,
      "total": 36000,
      "kind": "one_time",
      "already_owned": false,
      "provenance": { "method": "estimated", "source": "curated-sector-priors" }
    }
  ],
  "one_time_total": 412000,
  "recurring_monthly": 38000,
  "working_capital": 114000,
  "contingency": 41200,
  "project_cost": 567200
}
```

`kind` is `one_time` or `recurring`. Items the user already owns are listed with
`already_owned: true` and excluded from totals — shown, not hidden.

---

## 6. Report

### `POST /api/reports` returns `{ "report_id": "..." }`, then `GET /api/reports/{id}`

```json
{
  "id": "…",
  "created_at": "…",
  "input": {},
  "location": {},
  "activity": {},
  "local": {},
  "finance": {},
  "inventory": {},
  "schemes": {},
  "verdict": {
    "band": "caution",
    "score": 54,
    "blockers": [{ "key": "blockers.working_capital_gap", "params": { "gap": 114000 } }]
  },
  "narrative": { "en": { "market": "…", "opportunity": "…" } },
  "narrative_status": { "en": { "state": "done", "provider": "api" } }
}
```

`local`, `finance`, `inventory` and `schemes` are the section 3 / 5 shapes verbatim.

**`narrative` is prose only.** Every number in the report comes from `local`, `finance`,
`inventory`, `schemes` — computed in Python, never from the model. The model may *cite*
those numbers but may never originate them. See `SPEC.md` section 7.

---

## 7. Accounts

Keep the existing `accounts.py` implementation (PBKDF2-SHA256 at 310,000 iterations,
hashed session tokens, origin check, rate limiting) — it is sound. Add:

- `POST /api/account/profile` — community, gender, age, household income, rural/urban,
  district, business stage, facilities owned. Every field optional and individually
  skippable, each with a `why_key` explaining what supplying it unlocks.
- `GET /api/account/profile`
- Social sign-in: **only ship it if real OAuth credentials are configured.** A button that
  fakes success violates rule 4. If unconfigured, hide the button — do not disable it with
  a tooltip.

---

## 8. Tracker

`POST /api/tracker/entry` and `GET /api/tracker/summary?from=&to=`

```json
{
  "entries": [
    { "id": "…", "date": "2026-10-04", "kind": "income", "category": "sales", "amount": 2400, "note": "" }
  ],
  "totals": { "income": 74000, "expense": 51200, "net": 22800 },
  "loan_status": {
    "scheme_id": "nsfdc.term",
    "sanctioned": 900000,
    "paid_to_date": 96463.1,
    "next_due": "2027-03-01",
    "next_amount": 48231.55,
    "in_moratorium": false
  },
  "actual_vs_forecast": [{ "month": "2026-10", "forecast": 62000, "actual": 74000 }]
}
```

Real recorded transactions and forecasts are never merged into one series.

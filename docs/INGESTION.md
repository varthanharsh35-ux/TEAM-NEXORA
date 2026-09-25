# INGESTION.md — keeping data current, honestly

## The honest position

There is no public API for Udyam, and most bank and agency scheme pages publish as HTML or
PDF with no change feed. **True real-time is not achievable and claiming it will not survive
a panel question.** What `data/raw/udyam_catalog.html` actually is today: one HTML page
saved by hand on 24 September.

What we build instead is **scheduled re-verification with change detection and visible
provenance.** Every fact carries the date we last confirmed it and a link to where. When a
source changes, we detect it and show it. When a crawl fails, we say so rather than
silently serving stale data as fresh.

This is stronger than a real-time claim, because it is auditable. "How do you know this
scheme still exists?" gets a timestamp and a URL instead of a shrug.

---

## 1. Pipeline

```
sources.yaml
   → fetcher      (scheduled; conditional GET, ETag/If-Modified-Since, polite rate limit)
   → snapshot     (raw bytes to data/snapshots/<source>/<iso-date>.<ext>, SHA-256 recorded)
   → parser       (per-source; HTML/PDF/CSV → normalised records)
   → differ       (compare to previous version: added / changed / removed)
   → review queue (changes affecting money or eligibility need a human tick)
   → publish      (versioned dataset + freshness metadata)
   → API          (serves with last_verified, next_check, status)
```

Raw snapshots are kept. If a parser turns out to be wrong, we re-parse history rather than
re-crawl it, and we can prove what a source said on a given date.

---

## 2. `sources.yaml`

```yaml
- id: nsfdc_schemes
  name: National Scheduled Castes Finance and Development Corporation
  url: https://nsfdc.nic.in/en/scheme
  kind: html
  parser: parsers.nsfdc
  dataset: schemes
  schedule: weekly            # cron: Sunday 02:00 IST
  critical: true              # changes require human review before publish
  robots: respect
  rate_limit_s: 5

- id: agmarknet_prices
  name: Agmarknet daily mandi prices
  url: https://agmarknet.gov.in/SearchCmmMkt.aspx
  kind: form_query
  parser: parsers.agmarknet
  dataset: prices
  schedule: daily             # cron: 06:30 IST
  params: { state: "Tamil Nadu" }
  critical: false

- id: osm_overpass
  name: OpenStreetMap POIs
  kind: api
  dataset: poi
  schedule: on_demand         # cached 7 days per (location, activity)
  critical: false
```

Datasets: `schemes`, `prices`, `poi`, `enterprises` (Udyam), `climate` (static, annual),
`gazetteer` (locations, quarterly).

### Recommended sources

| Dataset | Source | Cadence | Notes |
|---|---|---|---|
| Schemes | NSFDC, NBCFDC, NSKFDC, NHFDC, NMDFC, TAHDCO, PMEGP/KVIC, Mudra, NABARD circulars | Weekly | The core of the scheme explorer |
| Prices | Agmarknet, e-NAM | Daily | Genuinely updates daily — fixes invented prices |
| Prices | Aavin procurement rates | Monthly | Dairy |
| POI | OSM Overpass | On demand, 7-day cache | Competitors and drivers |
| Gazetteer | LGD (Local Government Directory), OSM | Quarterly | Location coordinates |
| Climate | IMD district normals | Annual | Static; ship as a file |
| Enterprises | Udyam public dashboard | Monthly | Aggregate counts only — see section 6 |

---

## 3. Change detection

The differ compares the newly parsed records against the current published version and
classifies each:

| Class | Meaning | Action |
|---|---|---|
| `added` | New record id | Publish after review if `critical` |
| `changed_material` | Interest rate, cap, share, eligibility, tenure or moratorium moved | **Block publish, queue for review**, keep serving previous |
| `changed_cosmetic` | Wording, ordering, whitespace | Publish immediately |
| `removed` | Record id absent from source | Mark `withdrawn`, set `withdrawn_on`, **never delete** |
| `source_unreachable` | Fetch failed | Keep previous, set `status: "unverified"` |

The user's example — a bank scheme present on 24 September and gone by 30 September —
surfaces on the next scheduled crawl as `removed`. The scheme card then renders greyed out:
*"This scheme was withdrawn from the NSFDC site on 30 September. Check with your local
agency office before applying."*

**Removal is never silent.** A user who saw a scheme yesterday and planned around it must be
told it is gone, not left to wonder where it went.

### Two-crawl confirmation

A record is only marked `withdrawn` after it is absent in **two consecutive crawls**. One
absence is usually a site outage or a parser break, not a policy change. The first absence
sets `status: "unverified"` and raises an alert.

---

## 4. Review queue

Anything `critical: true` with a `changed_material` diff lands in a review table:

```
GET  /api/admin/review          → pending diffs, old value vs new value, source link
POST /api/admin/review/{id}     → { "decision": "accept" | "reject", "note": "" }
```

Guarded by an admin token in `.env`. This is deliberately a small, unglamorous screen —
but being able to show a panel that **a human approves every change to an interest rate**
is a genuine answer to "how do you prevent bad data reaching a beneficiary?"

---

## 5. Scheduling

Do not add Celery or Airflow for a hackathon. Use APScheduler inside the FastAPI process,
or Windows Task Scheduler / cron calling `python -m backend.ingest run --source <id>`.

```
python -m backend.ingest run --source nsfdc_schemes     # one source now
python -m backend.ingest run --due                      # everything past next_check
python -m backend.ingest status                         # freshness table for all datasets
python -m backend.ingest diff --source nsfdc_schemes    # dry run, no publish
```

`status` output feeds `GET /api/freshness`, which the UI shows on an "About the data" page.
Have that page open in a tab during the demo — it answers most data questions before they
are asked.

---

## 6. Legal and ethical constraints

These are not optional and a judge may well ask:

- **Respect `robots.txt`.** The fetcher checks it and refuses disallowed paths.
- **Identify honestly.** Real `User-Agent` with project name and a contact address.
- **Rate limit.** Minimum 5 s between requests to the same host. Never parallel-hammer a
  government site.
- **Cache aggressively.** Conditional GET with ETag. A weekly scheme crawl is roughly 20
  requests — trivial load.
- **Aggregates, not individuals.** Udyam registration records identify real businesses.
  Ingest **counts by category, block and year only.** Do not store or display an
  identifiable enterprise that has not consented. This matters both legally and because
  re-publishing an individual's registration data is not something the project should do.
- **Attribute.** OSM requires ODbL attribution; show it on the map. Government data
  attribution is shown on each fact.
- **Never claim to be an official channel.** Every scheme card carries: *"Indicative only.
  Confirm terms with the sanctioning agency before applying."*

---

## 7. Failure behaviour

| Situation | Behaviour |
|---|---|
| Source down at crawl time | Keep previous data, `status: "unverified"`, amber badge, retry next cycle |
| Parser throws | Keep previous data, alert, snapshot retained for debugging |
| Source shape changed | Parser fails loudly rather than silently returning zero records |
| Zero records parsed | **Treated as a parser failure, never as "the source is now empty."** Guard: if record count drops more than 40 percent in one crawl, block publish and alert |

That last guard matters. Without it, one HTML redesign silently wipes the scheme catalogue
and the app confidently tells a user there are no schemes for them.

---

## 8. Build order

1. `backend/ingest/__init__.py` — CLI skeleton, `sources.yaml` loader
2. Fetcher with conditional GET, robots check, rate limiting, snapshot writer
3. `parsers/nsfdc.py` as the reference parser, with a fixture test against a saved snapshot
4. Differ and the `withdrawn` lifecycle
5. Freshness metadata plumbed into every API response
6. Review queue
7. Remaining parsers: NBCFDC, TAHDCO, PMEGP, Mudra, Agmarknet

Every parser ships with a **fixture test against a committed snapshot**, so a source
redesign shows up as a red test rather than as silent data loss.

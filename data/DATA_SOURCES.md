# Data provenance — retrieved 24 September 2026

All source files are cached under `data/raw`. Internet is not needed to calculate or retrieve evidence. No observation is invented and presented as a survey. `estimated: true` marks planning priors and every market projection.

| Dataset | Origin/date | License/status | Actual use |
|---|---|---|---|
| `districts.json` names | https://lokbhavan.tn.gov.in/districts-of-tamil-nadu/; cached `districts.html`, accessed 2026-09-24 | Government published directory; no explicit open license located; retain attribution | 38-district selection, matching, regional retrieval |
| `blocks.json`, `villages.json` | https://www.tnrd.tn.gov.in/databases/Blocks.pdf and https://www.tnrd.tn.gov.in/databases/Villages.pdf; publication date absent, historical district layout | Government public directory, explicit redistribution license not stated | Local fuzzy search and matching: 385 blocks, 12,620 historical panchayat records |
| Current administrative reference | https://www.des.tn.gov.in/sites/default/files/2025-07/33%20LOCAL%20BODIES_0.pdf; handbook 2022-23 | Government publication, attribution retained | Coverage caveat: 388 unions and 12,525 panchayats in this reference; not a claim that historical directory is current |
| `knowledge.json` official chunks | https://www.nabard.org/auth/writereaddata/tender/pub_0602250348211363.pdf; State Focus Paper 2025-26 | NABARD publication; source copyright retained; cached for attributed prototype retrieval | 195 PDF pages parsed into searchable chunks; retrieved evidence passed to LLM with page/source IDs |
| Scheme router | https://nsfdc.nic.in/faqs; cached `nsfdc.html`; accessed 2026-09-24 | Government public information; no explicit license located | Required micro/term thresholds, caps, rates and total tenure; code implements user spec and current FAQ |
| `districts.json` regional profiles | Project-authored 2026-09-24, informed qualitatively by NABARD state paper | CC0 for project-authored entries | **Synthetic estimates**: effective rural density 170–650/km², relative purchasing index 0.88–1.18; not district Census/HCES measurements |
| `sectors.json` | Project-authored 2026-09-24 | CC0 | **Synthetic planning benchmarks**, 13 sectors: prices, per-unit costs, capacity, startup costs, demand adoption, competitors per 10,000; used in report numbers and RAG |
| `business_seed.tsv`, `business_holdout.tsv`, `business_training.csv` | Project-authored EN/TA/HI business phrases, 2026-09-24 | CC0 | Actual supervised training and independent-phrase evaluation; seed text also feeds RAG |
| `models/qwen3-0.6b` | https://huggingface.co/Qwen/Qwen3-0.6B | Apache-2.0 (included upstream license) | Actual pretrained local LLM; **not trained here**. Local classifier is trained here. |

## Coverage and assumptions

- Historical blocks remapped with an explicit curated crosswalk to Chengalpattu, Kallakurichi, Ranipet, Tirupathur, Tenkasi and Mayiladuthurai. Boundary mapping needs fresh LGD verification, especially split blocks. Chennai has no rural block records. Do not present historical panchayat names as a current exhaustive LGD register.
- Directory extraction retains source spelling and IDs. Current statutory codes are not invented. No precise village geocoordinates/populations are available in this directory. Unknown villages with a known district use a clearly labelled district proxy; ambiguous villages ask for a district.
- The TNRD modern download page returned 404 to the downloader; legacy public PDFs succeeded. Census village population/occupation and current LGD bulk extracts were not acquired. Do not infer population from the presence of a village record.
- MoSPI HCES report download failed TLS certificate validation; it is not used as measured purchasing power. Live Agmarknet prices were not obtained; prices are synthetic scenarios, never current mandi quotes. Aavin procurement prices are not substituted for retail milk prices.
- Population scenario = pi × radius² × regional density prior × 0.35 accessibility factor; uncertainty interval ±35%. Household size = 3.8 (assumption). No geospatial boundaries or road network is used.
- Competition scenario = population × sector prior / 10,000; block proxy assumes 100,000 residents. These are density estimates, not names, business locations, survey counts or a verified map.
- Selling prices scale by the regional purchasing index; input costs move more slowly. Demand, frequency, competition share and equipment capacity cap sales. Working capital = 45 days operating cost + 7.5 days receivables − 6 days variable-cost supplier credit.
- Financial engine uses simple accrued moratorium interest capitalised once, then quarterly reducing balance. Annual nominal rate divided by four. First paid quarter ends at month 6 for micro or month 9 for term. Repayment ends at month 36/84. Verify actual lender treatment; the source does not establish capitalization policy.
- The mathematical scheme route is **not eligibility approval**. NSFDC targets eligible Scheduled Caste applicants; community, household income and agency requirements must be checked. Tamil Nadu applicants should consult TAHDCO for SC routing; TABCEDCO/NBCFDC for BC/OBC alternatives. No universal entitlement, grant or credit score is asserted.

## Rebuild

`python scripts/prepare_data.py`, `python scripts/build_knowledge.py`, `python ml/train.py` rebuild data/model using cached extracts. To refresh official sources, download the cited publications and extract using pypdf; inspect changed boundaries before replacing cached directories. No API key is required for the bundled dataset.

## Restored scheme catalogue (24 September 2026)
`scheme_catalog.json` is manually transcribed from NSFDC FAQ (https://nsfdc.nic.in/faqs) and NBCFDC Annual Report 2024–25 (https://nbcfdc.gov.in/nbcfdc/web/sites/default/files/2025-12/Annual%20report%202024-25_0.pdf). Source copyright retained. Used by eligibility screening and selected-scheme financial calculation. NSFDC SC annual family income ceiling is ₹5 lakh per FAQ effective 7 January 2026; NBCFDC OBC ceiling ₹3 lakh. NBCFDC individual loans: 85% finance capped ₹15 lakh; beneficiary rate 7% through ₹1.25 lakh, otherwise 8%; 4/7 years including one-quarter moratorium per Annual Report. Remaining 15% conservatively treated as own funds; actual channel-partner contribution must be confirmed. These three schemes have no gender exclusion. Catalogue is deliberately incomplete pending verified additional documents.

## Basic prototype additions — 24 September 2026

| Dataset | Origin / licence | Use and limits |
|---|---|---|
| `raw/sarvanampatti_locality_osm.json` | Nominatim search, OSM node 1450492159, https://www.openstreetmap.org/node/1450492159; ODbL 1.0, © OpenStreetMap contributors | Actual suburb centre 11.0783323, 77.0038210; spelling aliases resolve here. This is a locality centre, not the user's exact business premises; move the pin. |
| `raw/saravanampatti_osm.json` | Nominatim/OSM; ODbL 1.0 | Initial police-station search result, retained as evidence but deliberately NOT used as locality centre. |
| `raw/sarvanampatti_pois_osm.json` | https://overpass-api.de/api/interpreter, retrieved 2026-09-24; ODbL 1.0 | 15 km query, capped 250 returned objects: 123 bank tags, 26 post-office tags, 101 dairy/convenience/supermarket tags. Partial, community-maintained records; not a complete survey. Similar retailers are possible competition, not proof of direct competition. |
| `maps.sqlite3` | Cached user-triggered Nominatim/Overpass responses; source licence retained | Search cache 30 days, POI cache seven days; last-good fallback on outage. Coordinates/POIs power the map, not the trained model. No bank has verified scheme-provider mapping in this cache. |
| Starter allowances in `backend/planning.py` | Authored prototype assumptions from existing synthetic sector priors | Equipment/asset allowance 55%, premises 20%, initial stock 15%, setup 10%; additional operating reserve equals 1.5 months of assumed fixed cost. Declared premises removes its allowance; declared equipment halves its allowance pending inspection. This is an itemized budget allowance, not a supplier quotation or specified purchase quantities. |

The original SIH margin-based calculator remains unchanged at `/api/finance`. New savings/loan report mode estimates starter cost first, uses available contribution up to that cost, then applies scheme financing share/caps to the shortfall. Uncovered contribution remains a visible funding gap. No model forecast is implied by this change.

Public Nominatim policy: https://operations.osmfoundation.org/policies/nominatim/ . Explicit user-triggered searches only, at most one request/second shared with reverse lookups; no network autocomplete, bulk download or scheduled location sweeps. Local directory suggestions stay local. Attribution remains visible. Provider URLs are configurable. Do not use public endpoints for production scale without an appropriate service agreement or self-hosting.

Real-data ingestion for retraining, Udyam records, live prices and outcome-labelled forecasting remain pending; map data is not used as fake training evidence.

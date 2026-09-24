# PERSONALIZATION.md — the local demand engine

## Why this document exists

The current report says things like *"avoid dependency on a single buyer"* and *"maintain
multiple suppliers."* That advice is true of every business on earth, which makes it worth
nothing to a specific person in a specific village.

Two causes, both fixable:

1. **The model is ordered to be generic.** The system prompt in `backend/llm.py` literally
   says: *"Include supply disruption, seasonal demand and single-buyer dependency in
   threats"* and *"No numbers, prices, rates."* It is told to produce boilerplate and
   forbidden from producing specifics.
2. **The model knows nothing local.** It receives five fields: business text, district id,
   category, verdict, facilities. It is never told what is actually near the user.

This document specifies the engine that produces the missing local facts. Once it exists,
the narrative becomes specific because the evidence is specific.

---

## 1. The core idea

For a given `(location, activity)` pair, find real nearby places that **boost** or
**suppress** demand for that specific activity, weight them by distance, and emit a score
plus a plain-language reason backed by named evidence.

```
OSM POIs within radius
  → classify each into a driver kind (college, IT park, warehouse, competitor, …)
  → look up the weight for (activity, driver kind)
  → apply distance decay
  → sum into demand_score, keep the evidence
  → render as reason strings with real names and real distances
```

The output is `drivers[]` in `DATA_CONTRACT.md` section 3.

**Rule: a driver with no named evidence is never emitted.** If we cannot name the college,
we do not claim there is a college.

---

## 2. Distance decay

Nearness matters differently per driver. Use a half-life decay:

```
effect = base_weight * 0.5 ** (distance_m / half_life_m)
```

| Driver class | Half-life | Rationale |
|---|---|---|
| Walk-in footfall (college, hostel, bus stand, market) | 600 m | People walk to a café, not 4 km |
| Vehicle-borne footfall (IT park, hospital, cinema) | 2,000 m | Short drive is acceptable |
| Direct competitor | 800 m | Substitution is local |
| Anchor competitor (Amazon FC, Aavin centre, big-box) | 8,000 m | Dominates a whole sub-region |
| Logistics (highway, railhead, cold chain) | 3,000 m | Access, not footfall |
| Supply (mandi, feed mill, textile cluster) | 5,000 m | Input sourcing tolerates distance |

Cap the total boost at `+0.60` and total suppression at `-0.55` so one dense cluster cannot
saturate the score.

```
demand_score = clamp(0, 100, round(50 * (1 + sum(effects))))
```

A location with no drivers either way scores 50 — "average, nothing special." That is an
honest answer and the UI should say so rather than inventing enthusiasm.

---

## 3. Driver taxonomy and OSM tags

Each driver kind maps to anchored Overpass tag filters. **Anchor every regex** — the
unanchored `amenity~"bank"` matching `blood_bank` is what produced the blood-bank bug.

| Driver kind | Emoji | OSM selector |
|---|---|---|
| `college` | 🎓 | `amenity~"^college$\|^university$"` |
| `school` | 🏫 | `amenity~"^school$"` |
| `it_park` | 💻 | `office~"^it$\|^company$"`, `landuse~"^commercial$"` + `name~"SEZ\|Tech Park\|IT Park"` |
| `hospital` | 🏥 | `amenity~"^hospital$\|^clinic$"` |
| `hostel` | 🛏️ | `tourism~"^hostel$"`, `building~"^dormitory$"` |
| `bus_stand` | 🚌 | `amenity~"^bus_station$"`, `highway~"^bus_stop$"` |
| `railway` | 🚉 | `railway~"^station$\|^halt$"` |
| `market` | 🧺 | `amenity~"^marketplace$"`, `shop~"^wholesale$"` |
| `place_of_worship` | 🛕 | `amenity~"^place_of_worship$"` (+ `religion` tag) |
| `residential_density` | 🏘️ | `landuse~"^residential$"` area, weighted by population |
| `highway_access` | 🛣️ | `highway~"^trunk$\|^primary$\|^motorway$"` |
| `industrial_estate` | 🏭 | `landuse~"^industrial$"` |
| `cold_chain` | ❄️ | `building~"^warehouse$"` + `cold_storage=yes` |
| `anchor_logistics` | 📦 | `building~"^warehouse$"` + `name~"Amazon\|Flipkart\|Delhivery\|Ekart"` |
| `big_retail` | 🏬 | `shop~"^supermarket$\|^department_store$"` + area over 1,000 m² |
| `dairy_anchor` | 🥛 | `name~"Aavin"`, `man_made~"^milk_chilling$"` |
| `feed_supplier` | 🌾 | `shop~"^agrarian$\|^farm$"` |
| `tourism` | 🧳 | `tourism~"^hotel$\|^attraction$"` |
| `competitor_direct` | 🏪 | per-activity selector, see section 5 |

Banks and post offices are **amenities, not drivers and not competitors.** They go in the
`amenities` map layer only, and never affect the score.

---

## 4. The weight matrix

Base weights before decay. Positive boosts, negative suppresses. Empty cell means no effect.

| Driver | ☕ Cafe / food | 🐔 Poultry | 🥛 Dairy | 🧵 Tailoring | 🏪 Retail | 📦 Warehousing | 🔧 Repair | 🐟 Fish | 🌾 Agri-input |
|---|---|---|---|---|---|---|---|---|---|
| `college` | **+0.34** | +0.06 | +0.08 | +0.12 | +0.18 | | +0.05 | +0.04 | |
| `school` | +0.12 | | +0.10 | +0.08 | +0.10 | | | | |
| `it_park` | **+0.30** | | +0.06 | +0.10 | +0.14 | +0.08 | +0.06 | | |
| `hospital` | +0.16 | | +0.08 | | +0.10 | | | | |
| `hostel` | **+0.26** | +0.14 | +0.16 | +0.06 | +0.12 | | | +0.10 | |
| `bus_stand` | +0.20 | | +0.06 | +0.08 | +0.18 | | +0.08 | +0.06 | |
| `railway` | +0.10 | | | | +0.08 | +0.14 | | +0.08 | |
| `market` | +0.14 | **+0.22** | +0.18 | +0.14 | +0.16 | | +0.10 | **+0.26** | **+0.24** |
| `place_of_worship` (veg-majority) | +0.06 | **−0.14** | +0.08 | | | | | **−0.16** | |
| `residential_density` | +0.18 | +0.16 | **+0.28** | **+0.22** | **+0.26** | −0.10 | +0.16 | +0.14 | |
| `highway_access` | +0.08 | +0.10 | +0.08 | | +0.06 | **+0.30** | +0.12 | +0.10 | +0.10 |
| `industrial_estate` | +0.14 | | | +0.08 | +0.08 | **+0.22** | **+0.24** | | |
| `cold_chain` | +0.06 | +0.12 | **+0.20** | | | +0.10 | | **+0.22** | |
| `anchor_logistics` | | | | | −0.08 | **−0.40** | | | |
| `big_retail` | −0.10 | −0.06 | −0.12 | −0.08 | **−0.34** | | | −0.08 | −0.10 |
| `dairy_anchor` | | | **−0.30** | | | | | | |
| `feed_supplier` | | **+0.18** | +0.12 | | | | | | −0.12 |
| `tourism` | +0.22 | | | +0.06 | +0.12 | | | +0.10 | |
| `competitor_direct` | see §5 | | | | | | | | |
| `farmland_adjacent` | | **+0.14** | **+0.18** | | | | | | **+0.26** |
| `water_body` | | | | | | | | **+0.24** | +0.08 |

Fill the remaining sectors (`craft`, `manufacturing`, `transport`, `services`) the same way
before shipping. Store the whole matrix in `data/drivers.json`, not in code, so it can be
tuned without a deploy.

### Worked examples from the user's own scenarios

**Cafe next to a college cluster.** 3 colleges at 800 m gives
`0.34 * 0.5^(800/600) = 0.135` each, capped contribution about `+0.34`; an IT park at
1.2 km adds `0.30 * 0.5^(1200/2000) = 0.198`; two cafes at 180 m subtract
`0.18 * 0.5^(180/800) * 2 ≈ −0.31`. Net about `+0.23`, score ≈ 62, band `good`.
Reason: *"3 colleges and 1 IT park within 2 km. Two cafes already within 200 m, so pick a
site on the opposite approach road."*

**Warehousing near an Amazon fulfilment centre.** Amazon FC at 4 km gives
`−0.40 * 0.5^(4000/8000) = −0.283`; highway at 1 km gives `+0.30 * 0.5^(1000/3000) = +0.238`.
Net `−0.045`, score ≈ 48, band `fair`, with the explicit warning that a large operator
within 10 km compresses both rates and available contracts.

**Poultry in a village with a large temple cluster and a farm 2 km away.** Suppression from
a vegetarian-majority worship cluster plus the existing farm; boost from feed suppliers and
farmland. The reason string names the actual farm and its distance.

---

## 5. Competitor matching — direct versus adjacent

Per activity, define two selector sets:

- `direct` — the same trade. A broiler farm competes with a broiler farm.
- `adjacent` — a partial substitute. A supermarket selling eggs is adjacent to poultry.

`direct` carries the full competitor weight; `adjacent` carries 40 percent of it.

```json
{
  "poultry.broiler": {
    "direct":   ["shop~\"^butcher$\"", "landuse~\"^farmyard$\"+poultry", "man_made~\"^poultry$\""],
    "adjacent": ["shop~\"^supermarket$\"", "shop~\"^convenience$\"", "amenity~\"^marketplace$\""]
  }
}
```

The current code maps poultry to `shop=butcher` alone, which returns almost nothing —
one of the reasons the map looked empty of real competitors while full of blood banks.

**Completeness honesty.** OSM is volunteer-mapped and thin in rural India. Always return
`completeness: "partial"` and render the note *"OpenStreetMap coverage in this area is
incomplete — there may be businesses not shown here."* Never let a low count read as
"no competition."

---

## 6. Seasonality

Monthly index per activity, modulated by two local facts:

1. **Climate** — district rainfall and temperature normals from IMD. Static, published,
   no scraping needed. Ship as `data/climate.json` keyed by district.
2. **Local calendar** — college vacation months suppress a campus-driven cafe; harvest
   months boost agri-input; Aadi and Margazhi shift wedding-linked tailoring demand;
   monsoon months suppress construction-linked trades.

```json
{
  "food.cafe": {
    "base": [1.0, 1.0, 1.05, 1.0, 0.8, 0.9, 1.0, 1.05, 1.05, 1.1, 1.05, 1.1],
    "modifiers": [
      { "when": "driver:college", "months": [5, 6], "factor": 0.72, "note_key": "notes.seasonality.college_vacation" },
      { "when": "climate:heavy_monsoon", "months": [10, 11], "factor": 0.9 }
    ]
  }
}
```

The chart the UI draws from this must print the value on each bar and carry one sentence
underneath: *"May and June are your weakest months because the nearby colleges are closed.
Keep about 2 months of costs in reserve."*

---

## 7. Pricing — stop inventing numbers

`sectors.json` currently hardcodes `"price": 52` for dairy with
`"source": "curated-sector-priors"`. Every dairy in Tamil Nadu gets the same figure. Replace
in this order of preference:

1. **Agmarknet / e-NAM daily mandi prices** for anything agricultural, keyed to the nearest
   market. These genuinely update daily. `method: "official"`.
2. **State-administered prices** where they exist — Aavin procurement rates, MSP.
   `method: "official"`.
3. **District purchasing-power adjustment** of a national figure. `method: "derived"`.
4. **Curated prior**, clearly badged. `method: "estimated"` — the fallback, not the default.

Always return a band, never a point estimate: `{ "low": 46, "mid": 52, "high": 58 }`.
The UI prints all three on the chart.

---

## 8. What the LLM does after this exists

Replace the prompt in `backend/llm.py` entirely.

**Delete:** *"No numbers, prices, rates"* and *"Include supply disruption, seasonal demand
and single-buyer dependency in threats."* Those two clauses are the direct cause of the
generic output.

**New contract with the model:**

- Input is a `facts` object: catchment, named competitors with distances, named drivers with
  distances, demand score and band, seasonality with the months named, price band, finance
  figures, facility gaps.
- The model writes 2 to 4 sentences per section, in the requested language.
- **It may only use numbers that appear in `facts`.** Validate after generation: extract
  every numeral from the output and assert each one appears in `facts`. Reject and retry
  otherwise. This keeps the existing anti-hallucination guarantee while allowing specifics.
- **It must name at least one real nearby place per section** where evidence exists. A
  section with no proper noun and available evidence is rejected and regenerated.
- Generic risk advice is only permitted when it is tied to a local fact. *"Supply
  disruption"* alone is rejected; *"your only feed supplier is 11 km away in Annur, so a
  monsoon road closure stops production"* is accepted.

**Before:**

> Threats: Watch out for supply disruption, seasonal demand changes, and dependency on a
> single buyer.

**After:**

> Threats: Your nearest feed supplier is 11 km away in Annur and there is no second option
> within the 10 km catchment, so a monsoon road closure in October or November stops
> production. Two of the three existing broiler farms already sell to the same Erode trader,
> so that buyer sets the price. The Perundurai temple cluster 1.4 km north means door-to-door
> selling will work poorly on Fridays and during Purattasi.

That second version is not a better model. It is the same model given real facts and
permission to use them.

---

## 9. Build order

1. `data/drivers.json` — the taxonomy, selectors and weight matrix from sections 3 and 4
2. `backend/drivers.py` — classify POIs, apply decay, produce `drivers[]` and `demand_score`
3. `data/climate.json` — IMD district normals
4. `backend/seasonality.py` — section 6
5. Price sourcing — section 7
6. New LLM prompt and numeric validator — section 8

Each step ships with tests. The critical test: **two different villages with the same
activity must produce materially different driver lists and reason strings.** If they do
not, the engine is not working, regardless of what the output looks like.

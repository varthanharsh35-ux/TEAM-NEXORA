# docs/ — the spec pack

Read in this order.

| File | What it is | Who reads it |
|---|---|---|
| `RULES.md` | Non-negotiable working rules. Ten rules, each written because it was broken. | Every agent, every session |
| `WORKFLOW.md` | How to drive Astra / Sonnet / Fable. The loop, the preamble, the review checklist. | You |
| `SPEC.md` | What the product must do, with acceptance criteria. | Everyone |
| `DATA_CONTRACT.md` | Frozen API shapes. Backend and UI build in parallel against this. | Astra + Fable |
| `PERSONALIZATION.md` | The local demand engine — drivers, weights, decay, the LLM prompt rewrite. | Astra |
| `INGESTION.md` | Scheduled re-verification, change detection, provenance. | Astra |
| `TASKS.md` | Numbered tasks. One per agent session. | You + Astra |
| `TECH_DOSSIER.md` | Panel Q&A. Architecture, datasets, APIs, limitations. | You, before the review |

## The three bugs these documents exist to fix

1. **Poultry returned blood banks.** `geography.py` queries `amenity~"bank|post_office"` —
   unanchored, so `bank` matches `blood_bank`. In the project's own cached file: 123 banks,
   26 post offices, 14 blood banks, 2 dairy shops. All 14 blood banks were then labelled
   competitors. → `TASKS.md` 1.2

2. **Saravanampatti was "not a valid place."** `villages.json` has 12,620 rows and no
   coordinates. Every lookup hits a live geocoder behind a 1 req/sec lock, and any failure
   surfaces as "outside Tamil Nadu." The previous fix was a hardcoded branch reading a canned
   file for that one place name. → `TASKS.md` 0.3 and 1.1

3. **The advice was generic.** The LLM prompt says "No numbers, prices, rates" and "Include
   supply disruption, seasonal demand and single-buyer dependency in threats" — it is ordered
   to produce boilerplate — and it is given only five context fields. → `PERSONALIZATION.md`
   §8, `TASKS.md` 2.4

## Start here

`TASKS.md` Phase 0, then Task 1.1. Task 1.1 unblocks nearly everything else.

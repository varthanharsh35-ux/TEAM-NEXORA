# SPEC.md — GramSahayak, what it must do

**Problem statement:** SIH — hyper-local AI business advisory assistant with a smart scheme
calculator, for beneficiaries of concessional credit schemes (10 percent margin money,
90 percent concessional loan).

**Coverage for the review:** Tamil Nadu, 38 districts, 385 blocks, 12,620 villages.
Architecture must not hardcode the state — coverage is a data boundary, not a code boundary.

Read `RULES.md` first. Shapes are frozen in `DATA_CONTRACT.md`.

---

## 1. The user journey

```
Landing → Sign in / continue as guest
        → Profile (community, gender, age, income, rural/urban, stage) — skippable
        → Facilities I already have
        → Where? (district → block → village/locality, searchable, map confirms)
        → What business? (sector dropdown → activity dropdown → 2–5 specific questions)
        → How much margin money do I have?
        → REPORT
             ├── Feasibility (demand, competitors on map, drivers, seasonality)
             ├── Money (project cost, loan, EMI, moratorium, repayment schedule)
             ├── Schemes I qualify for
             ├── What I need to buy (inventory and setup)
             └── Download / print
        → Tracker (daily income and expenses, actual loan, repayments)
```

**No free-text business description anywhere in this flow.** The user picks from dropdowns.
(The trained classifier is retained only for an optional "not sure? describe it" helper that
suggests a dropdown value. It is not on the critical path.)

---

## 2. Module 1 — Hyper-local feasibility report

Maps to the six points in the problem statement:

| Required | Implementation | Status today |
|---|---|---|
| 1. Market reach, 5–10 km | Catchment population from gazetteer + density, honouring the selected radius | Radius is ignored; hardcoded 15 km |
| 2. Opportunity analysis | Underserved driver clusters: high boost, low competitor density | Absent |
| 3. SWOT | Generated from real facts, not boilerplate — see `PERSONALIZATION.md` §8 | Boilerplate, prompt-enforced |
| 4. Threats | Named local risks with distances and months | Generic |
| 5. Competitor mapping | Real OSM competitors, on the map, counted once | Broken — returns blood banks |
| 6. Product market value | Price band from Agmarknet / administered prices | Invented constant |

### Acceptance criteria

- **AC1.1** Any of the 12,620 villages plus common urban localities resolves to coordinates
  and drops a pin, with no place-specific branch anywhere in the code.
- **AC1.2** Selecting 5 km versus 10 km changes the catchment population, the competitor
  count and the map circle.
- **AC1.3** For a poultry query, zero blood banks appear in any layer, and competitors are
  poultry-related.
- **AC1.4** The competitor count in the text equals the number of pins in the competitor
  layer. Always.
- **AC1.5** Two different villages, same activity, produce different driver lists and
  different reason sentences naming different real places.
- **AC1.6** Every number on screen carries a provenance badge or a source link.
- **AC1.7** A place we cannot resolve says "we could not find this place" — never "outside
  Tamil Nadu."

---

## 3. Module 2 — Smart financial calculator and scheme router

The maths in `backend/finance.py` is correct, tested and must be preserved:
project cost = margin ÷ 10 percent, max loan = 90 percent, micro versus term routing,
simple interest capitalised once across moratorium, quarterly reducing balance thereafter.

What must be added:

- **Per-scheme rules.** Each scheme has its own share, cap, rate, tenure, moratorium and
  subsidy. Never apply the NSFDC term-loan terms to an unrelated scheme.
- **Two directions.** Margin → project cost (as specified), and project cost → margin
  required (what the user usually actually asks).
- **Affordability.** Compare the quarterly instalment against projected cash flow and say
  plainly whether it is payable, with the shortfall in rupees if not.
- **Working capital.** Separate from setup capital, shown as its own number with its own gap.

### Acceptance criteria

- **AC2.1** Margin ₹1,00,000 yields project cost ₹10,00,000 and loan ₹9,00,000.
- **AC2.2** Project cost ₹1,40,000 or below routes to Micro Finance at 6.5 percent,
  36 months, 3-month moratorium. Above ₹1.40 L up to ₹50 L routes to Term Loan at
  8 percent, 84 months, 6-month moratorium.
- **AC2.3** The repayment table shows the moratorium quarters with interest accruing and
  zero principal, then level quarterly instalments. Totals reconcile to the paise.
- **AC2.4** Changing the scheme changes the terms used. No scheme reuses another's numbers.
- **AC2.5** Every assumption is listed on screen with "confirm with the sanctioning agency."

---

## 4. Scheme explorer

A dedicated route, usable without running a full report.

- Searchable cards, filterable by community, gender, age, income, sector, project size,
  business stage, state.
- Three states: **eligible**, **need more details** (with the exact missing field), **not
  eligible** (with the reason).
- Each card: terms, required documents, official apply link, source link, verified-on date.
- Withdrawn schemes stay visible and greyed, with the date.

**Minimum catalogue for the review: 12 to 15 real schemes.** Today there are 3.
Required: NSFDC Micro Finance, NSFDC Term Loan, NSFDC Mahila Samriddhi, NBCFDC term and
micro, NSKFDC, NHFDC, NMDFC, TAHDCO, PMEGP, PM Mudra (Shishu/Kishore/Tarun), Stand-Up India,
Tamil Nadu NEEDS. Every one with a source URL and a verified date.

### Acceptance criteria

- **AC3.1** Every filter in the query string measurably changes the result set. Today
  `gender`, `age` and `sector` are stored and never read.
- **AC3.2** A female OBC applicant, age 29, income ₹1.8 L, project ₹4 L, sees a different
  set from a male SC applicant, age 45, income ₹6 L, project ₹40 L.
- **AC3.3** No card lacks a source URL and a verified-on date.
- **AC3.4** "Need more details" never displays as "not eligible."

---

## 5. Facilities and inventory

**Facilities** — asked once at profile: workspace, three-phase electricity, reliable single
phase, running water, storage, refrigeration, transport, equipment owned.

These must actually change the output: missing required facilities become blockers with an
estimated arranging cost; owned facilities are deducted from the project cost.

**Inventory and setup plan** — itemised for the selected activity: equipment with
quantities and indicative costs, opening stock, working capital, contingency. One-time and
recurring separated. Items already owned shown with a strike-through and excluded from
totals.

- **AC4.1** Toggling "I already own the shed" measurably reduces project cost and changes
  the scheme routing if it crosses ₹1.40 L.
- **AC4.2** Missing three-phase power on a manufacturing activity appears as a named blocker
  with a cost, not a silent omission.

---

## 6. Tracker

Daily income and expense entry, running cash balance, actual sanctioned loan with real
repayment schedule, moratorium countdown, next instalment, payment history, and
actual-versus-forecast comparison.

- **AC5.1** Recorded transactions and forecast figures are never merged into one number or
  one chart series.
- **AC5.2** When actual sanctioned terms are entered, they replace the estimate everywhere,
  and the UI says which figures changed.

---

## 7. AI narrative

See `PERSONALIZATION.md` section 8 for the full prompt contract. The hard invariants:

- Python computes every number. The model writes prose only.
- The model may only use numerals that appear in the `facts` object it was given. Validated
  after generation by extracting numerals and checking membership; rejected and retried
  otherwise.
- Each section names at least one real nearby place when evidence exists.
- Purely generic risk statements are rejected.
- User input and retrieved passages are treated as data, never as instructions.
- If the model is unavailable, fall back to a template that states the facts plainly. The
  fallback must be visibly labelled, not passed off as AI output.

---

## 8. Languages

English, Tamil and Hindi complete at review. Telugu, Kannada, Malayalam, Bengali, Marathi,
Gujarati listed as planned, visibly marked as such.

The old project had 8 locale files and a Bhashini integration — both are in
`audit/original-project.zip` and should be recovered rather than rewritten. **Bhashini is
the Government of India translation service and is a better story for this panel than Google
Translate.** Keep a pluggable translation provider so either can be configured.

Financial and legal terms use a reviewed glossary, never machine translation. Mistranslating
"moratorium" or "margin money" is worse than leaving it in English.

---

## 9. UI direction

The user's friends are producing the visual design. This section constrains behaviour, not
aesthetics.

- **Calm, not flashy.** Users may be new to this kind of tool. No jargon, no dense dashboards
  on first view, one clear next action per screen.
- **Not vibe-coded.** Real component structure, real routing, consistent spacing.
- **Charts:** simple types only — bar, line, donut, gauge. **Print the value on every bar,
  point and segment.** One plain sentence under every chart saying what it means.
- **Emoji as wayfinding**, not decoration: 📍 location, 🏪 competitors, 🎓 driver, 💰 loan,
  📅 repayment, 📦 inventory, 📊 feasibility, ⚠️ blocker.
- **Traffic-light verdict** at the top of finance and repayment: green go, amber caution,
  red blocker — with the reason in one sentence.
- Every estimate visibly badged. Every source clickable.
- Works on a low-end Android phone over 3G.

---

## 10. What we are not building

State honestly, in the deck and to the panel:

- Not a loan application channel. We prepare people; agencies sanction.
- Not real-time. Scheduled re-verification with visible dates — see `INGESTION.md`.
- Not a credit score or a sanction prediction.
- Not financial advice. Indicative figures requiring agency confirmation.
- Competitor data is OSM-derived and incomplete in rural areas — always stated.

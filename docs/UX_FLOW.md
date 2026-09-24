# UX_FLOW.md — page flow, navigation and screen contents

Source: the team's product walkthrough. This document is the authority on **what is on each
screen and in what order**. `SPEC.md` remains the authority on what the system must compute,
`DATA_CONTRACT.md` on the shapes. Where this document and `SPEC.md` disagree, raise it rather
than choosing silently.

Audience: rural and semi-urban first-time entrepreneurs, many new to this kind of tool.
**Quiet and professional, not flashy.** Portable, low bandwidth, works on a cheap Android phone.

---

## 0. Global shell

**Theme:** green and white. One green for primary actions, one deeper green for headers, white
surfaces, a neutral grey for secondary text. Define as CSS custom properties in one place so
the whole palette can be retuned without touching components.

**Responsive proportion is a requirement, not a polish item.** Every section must hold its
balance at phone, tablet and desktop widths. No horizontal scroll at 360 px. Test at
360 / 768 / 1280.

**Navigation:**

| Width | Behaviour |
|---|---|
| Desktop | Dashboard navigation as a **horizontal bar across the top** |
| Tablet / mobile | The same items collapse into a **hamburger (sandwich) menu**, containing every dashboard item — nothing dropped |

**Language switcher:** persistent, on the left of the dashboard shell. Changing it
**re-renders the entire site** in the chosen language — not just labels. Bhashini as the
provider (`SPEC.md` §8). Complete for English, Tamil and Hindi; other languages listed as
planned and visibly marked.

**Profile control:** top-right. Signed out it offers **Log in / Sign up / Continue as guest**.
Signed in it opens the profile detail page.

**Guest mode:** a guest can complete onboarding and see a full report. State is held locally
and clearly labelled *"not saved — create an account to keep this"*. Do not silently discard
a guest's work: on sign-up, migrate it.

---

## 1. Landing page

- Project heading and one-line subheading. Plain language, no jargon.
- **Two primary buttons:**
  1. **Start your business journey** — the new-venture path
  2. **I already have a business** — the existing-business path
- Either button: if signed in, go to onboarding. If not, prompt log in / sign up / guest, then
  continue to the same place. **Never lose the click** — remember which button was pressed.

---

## 2. Onboarding wizard

A stepped wizard with visible progress, a **Back** control on every step, and no data loss when
moving backwards.

### Step 1 — Business

| Field | Type | Feeds the engine? |
|---|---|---|
| Business idea name | free text | No — the user's own label, shown back to them |
| Sector | **dropdown** | Yes |
| Activity | **dropdown**, filtered by sector | Yes |
| Concept / details | free text, optional | **No** — stored and displayed, never parsed |

**This is the one place `SPEC.md` §1 and the walkthrough appear to disagree, and the resolution
matters.** Analysis is driven by the sector and activity dropdowns only. The free-text concept
box exists for the user's own notes and is shown back on the review screen, but it must never
feed classification, scoring or the narrative. Free text driving analysis is what produced
unreliable categories before.

### Step 2 — Location

- Two ways in, kept in sync: **type an address** (autocomplete from the gazetteer) **or pick on
  the map**. Choosing either updates the other and moves the pin.
- Map shows the full surrounding area, not just a marker.
- **Radius slider, 5 km to 15 km**, default 10 km. The circle redraws live, and the radius
  drives competitor mapping and catchment.
- The problem statement asks for a 5–10 km catchment; 15 km is available but the report notes
  when a radius beyond 10 km was used.
- Free mapping stack only: gazetteer first, OSM/Overpass for POIs, Leaflet for rendering.

### Step 3 — Resources available

Predefined checkboxes:

🏢 Own commercial space · ⚡ Three-phase electricity · 🏠 Rental shop/room · 💧 Clean water
supply · 🚚 Transport vehicle · 🏦 Active bank account · 📦 Dry storage / warehouse ·
🌐 Internet and broadband

Plus a free-text **"other resources I already have"** field.

Each item the activity requires but the user lacks becomes a **named blocker with an estimated
cost**, not a silent omission (`SPEC.md` §5).

### Step 4 — Demographic profile

Gender · Community category (dropdown, full list) · Age · Education level

Each field individually skippable, each with a one-line *why we ask* — these drive scheme
eligibility and nothing else. Education level is new here and feeds scheme filters that carry
education criteria.

### Step 5 — Review and confirm

Every answer displayed for checking, each with an **Edit** link back to its step. A single
**Confirm** button then generates the report and moves to the main application.

---

## 3. Existing-business path

Identical to the above, plus:

- Per-capita / household income
- Existing loans, if any — lender, amount, rate, tenure, balance
- **Optional upload of financial statements**, which flows into Cash Flow as opening data

Existing loans entered here appear in Debt Management without re-entry.

---

## 4. Main application

Dashboard items: **Home · Feasibility Report · Financial Plan · Government & Bank Schemes ·
Cash Flow · Debt Flow · Settings**

### 4.1 Home

- **Overall viability score, out of 100** — the headline number
- Estimated break-even
- Initial capital reading
- Loan amount
- **Bar graph of cash in and out**, green for inflow, red for outflow, values printed on the bars
- **Explore schemes** button linking to the schemes section
- **Recent activity** list — what the user last did (entries added, loans recorded, report
  regenerated)

The Home figures update when Cash Flow or Debt Flow changes. They are never a second,
independently computed copy of those numbers (`RULES.md` rule 5).

### 4.2 Feasibility Report

- Overall viability score out of 100 — **the same number as Home**, computed once
- Initial capital card · debt amount card
- **SWOT**, with Strengths/Opportunities prominent, generated from real local evidence
  (`PERSONALIZATION.md` §8) — never boilerplate
- **Tailored strategy and optimisation guidance**
- **Alternative high-potential ventures** — see §5 below
- **Live map** with distinct symbols for:
  📍 your chosen location · 🏪 competitors · ⚓ possible anchors (demand drivers) · 🏦 banks

Inputs: competitor count from the map, catchment population and density, demand drivers,
market potential from the ingested datasets (`INGESTION.md`). One competitor number, shown
both as a figure and as pins.

### 4.3 Financial Plan

- Editable initial capital
- **Bare-minimum starter capital** for this activity
- Capital for established setup
- Monthly recurring costs
- **Finance tracking graph fed from the Cash Flow entries** — not a separate forecast series.
  Forecast and actual stay visually distinct (`DATA_CONTRACT.md` §8).

### 4.4 Government & Bank Schemes

- **Map of banks and agencies** offering schemes relevant to this business
- Below it, scheme cards. The walkthrough's PM SVANidhi example is the template — every card
  carries: scheme name and full title, type, max amount, annual interest rate, max tenure,
  eligibility overview, itemised eligibility requirements, key benefits, moratorium note, a
  link to the official portal, and the nearest branch location.
- Filters per `SPEC.md` §4: community, gender, age, income, sector, project size, stage,
  education.
- Every card shows **verified-on date and source link**; withdrawn schemes stay visible and
  greyed (`INGESTION.md` §3).

### 4.5 Cash Flow

- Totals: **total inflows · total outflows · net liquid balance**
- **Upload financial statements** (PDF/CSV/image), parsed into draft entries the user confirms
- **Manual entry:** date · inflow or outflow · amount · category
- Entries listed, each individually **deletable**
- This data feeds the Financial Plan graph and the Home bar graph

### 4.6 Debt Flow (Debt Management)

- Totals: **total outstanding debt · total principal repaid · remaining unpaid balance ·
  total monthly EMI obligation**
- **Add loan record:** lender / scheme name · facility type (dropdown, e.g. MUDRA Kishore
  ₹50K–₹5L) · repayment status (On track / Late / Closed) · principal · interest % p.a. ·
  tenure months · monthly EMI (computed, user-overridable) · remaining balance ·
  disbursement date
- Records appear under **Active Loan Accounts**
- EMI computed by the existing `finance.py` engine, never re-derived elsewhere
- Changes propagate to Home

### 4.7 Settings

Update location · language · units and currency display · notification preferences ·
delete my data.

### 4.8 Profile

View and edit everything captured during onboarding: demography, resources, business details.

---

## 5. Alternative high-potential ventures

The strongest new idea in the walkthrough, and nothing comparable exists in the current build.

Two directions, both driven by the driver engine (`PERSONALIZATION.md`):

1. **Better business, same place.** Score every activity in the taxonomy against this
   location's drivers and competitor density. Surface the top 3 that beat the chosen activity,
   each with the reason and the capital it needs.
   *"A tea stall scores 74 here against your poultry farm's 41 — three colleges within 2 km and
   only one existing stall. It needs about ₹85,000 against your ₹4,20,000."*

2. **Better place, same business.** Score the chosen activity across neighbouring
   blocks/localities and surface where it does better, with the distance.
   *"Poultry scores 68 in Chithode, 9 km away — a feed supplier and a wholesale market, and no
   farm within 3 km."*

Rules: only suggest activities whose capital requirement is within reach of the user's stated
margin; never suggest a location outside a reasonable travel distance; always give the reason
and the evidence. **This must never read as discouragement** — frame as "also worth
considering", and keep the chosen business's own analysis complete and first.

---

## 6. What this document adds that the plan did not have

| New | Where it lands |
|---|---|
| Dual entry: new venture vs existing business | Onboarding, §3 |
| Guest mode with migrate-on-signup | Global shell |
| **Alternative high-potential ventures** | §5 — new core feature |
| Financial statement upload into Cash Flow | §4.5 |
| Education level in demography | §2 step 4 |
| Recent activity feed | §4.1 |
| Top bar collapsing to hamburger | Global shell |
| Green/white theme, proportion at all widths | Global shell |
| Map symbol taxonomy including anchors | §4.2 |
| Debt records with EMI obligation totals | §4.6 |
| Settings page | §4.7 |
| Radius slider 5–15 km, live circle | §2 step 2 |
| Review-and-confirm step before generating | §2 step 5 |
| Business idea name and concept notes | §2 step 1 |
| Bank locations on the schemes map | §4.4 |

# Project Status — GramSahayak AI (Team Nexora)

**Last Updated:** 2026-09-23 (Phase 1 to Phase 5 Implementation Complete)

---

## 1. Project Scope Summary
GramSahayak AI is an AI-powered spatial advisory and financial feasibility platform built for rural micro-entrepreneurs across India (SIH 2026).
- **Model 1 (Location & Competitive Analysis Engine):** Interactive OpenStreetMap Nominatim geocoding & pin-drop location picker, dynamic 5–10 km catchment boundary rendering, real-world OpenStreetMap Overpass POI queries (competitors & footfall anchors with zero synthetic/fabricated data), multi-condition spatial suitability scoring with transparent rationale, tailored growth & pivot guidance, and consulting-grade export to **PDF** and **Word (.docx)**.
- **Model 2 (Loan Eligibility & Scheme Matching Engine):** Nearby financial institutions (banks & post offices) with Google Maps deep-links, verified financial intake with data privacy consent, dynamic active scheme catalog, explicit moratorium schedules (*"No payments due for months 1–X, repayments start month Y"*), and bidirectional interactive EMI calculator (Target Monthly EMI $\leftrightarrow$ Repayment Tenure).
- **Support Modules:** 100% site-wide localization across 8+ Indian regional languages, strictly scoped Site Navigation Guide assistant, cold-start persistence with zero preloaded fake demo data, and experimental placeholder for operating businesses.

---

## 2. Completed (Working & Verified)
- [x] **Phase 0 Assessment:** Detailed codebase audit against `business-advisor-platform-spec.pdf` approved by project owner.
- [x] **Ground Rules & Cold Start Compliance:** Purged all preloaded demo accounts (`Ramesh Kumar`), fake loans, and mock transactions. Implemented clean cold-start session initialization in `AuthContext.jsx` and dynamic state across all pages.
- [x] **Localization Overhaul:** Added comprehensive static dictionaries for English (`en`), Hindi (`hi`), Marathi (`mr`), Tamil (`ta`), Telugu (`te`), Kannada (`kn`), Bengali (`bn`), and Gujarati (`gu`). Fixed all untranslated strings, validation errors, and button labels on `LoginPage.jsx` and across components.
- [x] **GIS & Catchment Map Integration (`LocationPicker.jsx`):** Interactive Leaflet map with Nominatim address geocoding, pin-drop coordinate resolution, reverse geocoding, and 5–10 km catchment circle overlay with real-time radius slider.
- [x] **Model 1 (Spatial Feasibility Engine):** Real-time OpenStreetMap Overpass API pipeline for discovering real nearby competitors and footfall anchors. Multi-condition spatial scoring (competitor saturation, anchor synergy, capital adequacy, operational readiness). Dynamic SWOT, tailored strategies, alternative business suggestions, and sector recalculation on `FeasibilityDashboard.jsx`.
- [x] **Consulting Dossier Export:** Integrated PDF export (`jspdf`) and Word document export (`docx`) directly on the Feasibility Dashboard.
- [x] **Model 2 (Loan Eligibility & Scheme Matching):** Real nearby banks and post offices query with interactive Leaflet map and Google Maps deep-links. Verified intake form with data privacy consent. Curated active central & state schemes with explicit moratorium schedules.
- [x] **Bidirectional EMI Calculator:** Bidirectional calculation supporting both tenure-to-EMI and target-monthly-EMI-to-tenure calculation with projected clearance dates.
- [x] **Dynamic Financial Plan:** Connected `FinancialPage.jsx` to `/financial/plan` endpoint for setup cost, bare-minimum capital vs established setup, and recurring cost structure by business category.
- [x] **Site Navigation Chatbot:** Rescoped AI assistant strictly to site navigation and feature guidance.
- [x] **Existing Business Path:** Added `ExistingBusinessPage.jsx` experimental placeholder for operating enterprises.

---

## 3. In Progress
- Final handoff documentation and project walkthrough summary.

---

## 4. Not Started
- UI/UX visual redesign (on hold pending teammate's design reference per Ground Rule 4).

---

## 5. Key Decisions & Assumptions
1. **Zero Fabricated Data Rule:** Real OpenStreetMap Overpass queries used for commercial landscape and financial access points. When an area has sparse entries, the UI explicitly states *"No direct competitors found in this radius"*.
2. **GIS Tech Stack:** Leaflet + OpenStreetMap tiles + Nominatim geocoder (zero API billing barriers, 100% open data compliance).
3. **Model 1 & 2 Separation:** Model 1 handles spatial commercial feasibility and POI density; Model 2 handles financial eligibility, banking access, and scheme matching.
4. **Chatbot Scope:** Scoped strictly as a Site Navigation Assistant per Section 9 of the brief.

---

## 6. Known Issues / Risks
- **Browser Subagent CDN Issue:** The local browser automation tool encountered a 404 on Microsoft Azure's Playwright CDN when downloading `playwright-1.57.0-win32_x64.zip`. All frontend builds (`npm run build`) and backend endpoints (`FastAPI` on `http://127.0.0.1:8000`) were thoroughly verified with automated integration tests.

---

## 7. Immediate Next Step
- Ready for user review and team handoff.

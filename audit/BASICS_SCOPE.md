# Basic prototype restoration — 24 September 2026

Baseline preserved in basics-before-20260924.zip (81 authored/configuration/data files); originals remain in original-project.zip. Private databases and large model assets remain in place. Inventory hashes: basics-inventory.json. Prior complete original audit: ANALYSIS.md. Vendor and binary inventories are not a semantic review.

## Current gaps by category
- UI — frontend/src/App.jsx: no landing/login/intake sequence; adjustable report inputs violate frozen-plan requirement; radius selector still 5/10 km; four-wide KPIs.
- UI — frontend/src/Profile.jsx: facilities/profile editing replaces requested saved-report history.
- UI — frontend/src/App.jsx: threat section absent; SWOT opportunities mislabeled as next steps; small headings/context clutter.
- Logic — backend/advisory.py: margin determines leveraged project rather than savings covering a costed starter plan; no funding-choice branch or itemized setup.
- Logic — backend/schemes.py: only three sourced schemes; no verified local provider associations; incomplete lender-specific conditions.
- Broken feature — frontend/src/LocationMap.jsx: address does not move map; reverse-only lookup; selected coordinates can diverge from label; no POIs.
- Broken feature — frontend/src/Account.jsx: social providers unavailable; registration demographics missing; manual workspace saves only.
- Broken feature — frontend/src/Tracker.jsx: planned schedules only; no payment records.
- Architecture — backend/main.py: external geography cache memory-only; no refresh pipeline or provider configuration.
- Architecture — frontend/src/App.jsx: single report snapshot; intake and report state coupled.
- AI — backend/advisory.py / data/sectors.json / data/districts.json: prices, demand and competitors are authored estimates, not observations.
- AI — ml/train.py: small synthetic phrase holdout is not a business-success evaluation; dropdown bypasses classifier intentionally.
- AI — backend/llm.py: pretrained Qwen with retrieval, not fine-tuned forecasting; no outcome labels for real forecast training.

## Locked scope
Implement phases 2–7 in order, verify each. Keep current design; add simple EN/TA/HI labels for every new feature. Fixed 15 km radius. Preserve original SIH financial calculator while adding cost-based savings/loan planning. Never represent scheme screening as approval, nearby branches as verified providers, estimated competitor counts as surveyed businesses, or missing external data as zero competitors. No fabricated map pins. Source gaps and credential-dependent social/Google features remain explicit.

Baseline verification: 22 backend tests pass; 371 translation keys match in all three languages. Source review covered active frontend/backend modules, financial engine, scheme catalogue, prior audit and data provenance. Historical/vendor/binary files use the prior inventory; no claim of fresh line-by-line vendor review.

Deferred: real-data refresh and evaluated retraining (phases 8–9), broad UI polish (10), comparison (11). Final basic walkthrough and regression mandatory before stopping.

# Final verification — 24 September 2026

## Phase 1: working core
- Deterministic example: margin 100,000 → project 1,000,000 → loan 900,000.
- Micro boundary, cap gap, term upper bound, out-of-range project, zero/negative/non-finite/bool/tiny invalid input, leap dates and total payment conservation pass.
- Moratorium quarters have zero payments, total tenure includes grace, final balance is exactly zero.

## Phase 2: trained model and retrieval
- Training completed: 187 authored multilingual phrases, 641 augmented training records, 48 independent-phrase holdouts.
- Accuracy 1.0 and macro F1 1.0 on that small authored holdout only. Not representative real-world accuracy or feasibility prediction.
- District names resolve across English, Tamil and Hindi for all 38 districts. Historical directory references, typos, ambiguous names, unknown places and out-of-state handling pass.
- RAG returns local source IDs and relevant cached evidence. SQLite saves and restores reports.
- Actual Qwen3 0.6B CPU inference completed in 81.77 seconds; eight schema-validated English fields returned. See `models/local_llm_test.json`. This was fresh generation, not a mocked API.
- API connection failure, malformed JSON, financial numeric claims and wrong-language responses reject safely to curated guidance; valid outputs are cached and revalidated.
- Live remote API credentials were unavailable; no claim that a real provider endpoint was tested. Tamil/Hindi generation quality is not guaranteed; the application rejects invalid language output and uses complete translated baseline reports.

## Phase 3: interface and translations
- Production build succeeds: main JS 384.34 kB (114.75 kB gzip), optional Leaflet chunk 150.63 kB (44.22 kB gzip), local Tamil/Devanagari fonts.
- 254 keys in each of English, Tamil and Hindi. Automated missing/empty key, interpolation, identical-English translation and static JSX text checks pass.
- Playwright on installed Edge: dairy report, project/loan amounts, 28/12 quarter schedules, micro cap funding gap and outside-limit warning pass.
- Language switches update labels and computed reports; no checked English financial labels remain in Tamil/Hindi.
- 390px mobile width has no document-level horizontal overflow in all three languages. Tables scroll separately.
- Browser service-worker reload with network disabled restores the last report. New calculations require the running local server.
- Optional lazy map renders and responds to pin selection and localized zoom controls with unavailable tiles. Reverse lookup was mocked in browser tests; provider error and cache behavior pass backend tests. Live external map availability is not guaranteed.
- Print PDFs produced for all three languages; fonts, complete quarterly schedules and layout visually reviewed. No clipped columns or missing Tamil/Devanagari glyphs observed. Original input text and official proper names remain verbatim.

## Phase 4: final check
- `python -m unittest discover -s backend -v`: **16 tests passed**, 5.515 seconds.
- `node scripts/check-i18n.mjs`: **254 keys × 3 languages passed**.
- Vite production build and offline-shell generation passed.
- Browser end-to-end suite passed with **zero page errors**; screenshots and machine-readable result in `audit/browser`.
- Original retired files were byte-compared with `audit/original-project.zip` before removal. The archive remains available.
- README, environment example, local launch script, data-source provenance and model training/evaluation scripts included.
- Final launch through `start.ps1` passed; HTTP report → queued advice → saved report returned the real locally generated cached eight-field response with loan 900,000. Evidence: `audit/final-smoke.json`.

## Limits of verification
This is a local prototype. Market population, demand, purchasing power, pricing and competitor figures are clearly labelled synthetic scenarios. Historical directory counts (385 blocks / 12,620 panchayat records) do not claim current LGD completeness. No loan sanction, field survey, full native-speaker review, live price feed, public-service security audit or arbitrary-input correctness guarantee is asserted.

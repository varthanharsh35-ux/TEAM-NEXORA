# attic/ — recovered previous version

`attic/original/` is the earlier GramSahayak build, extracted from
`audit/original-project.zip`. **Do not import from it and do not wire it in.**
It is a read-only reference for work that was deleted in a later session.

Recovered here because the sources no longer exist anywhere else in the repo:

| Path | Why it matters |
|---|---|
| `backend/routers/{ai,assessment,financial,schemes}.py` | Deleted; only orphaned `__pycache__` remained |
| `backend/data/schemes_data.py` | Deleted; same |
| `frontend/src/pages/LoginPage.jsx` (344 lines) | The login UI, needed for Task 3.3 |
| `frontend/src/contexts/AuthContext.jsx` | Auth provider |
| `frontend/src/services/bhashini.js` | Government of India translation service |
| `frontend/src/i18n/locales/*.json` | 8 languages — 5 of them absent from the current build |
| `frontend/src/pages/*.jsx` | The separate Feasibility / Financial / CashFlow / DebtManagement / CreditMonitoring pages |

Deleted from the live tree at the same time: `backend/routers/__pycache__/` and
`backend/data/__pycache__/`, which held compiled shells of the modules above and
nothing else.

See `docs/TASKS.md` Task 0.2.

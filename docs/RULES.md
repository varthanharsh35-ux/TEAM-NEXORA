# RULES.md — non-negotiable working rules for any AI agent on this repo

Read this file before every task. These rules exist because they were broken before.

## Hard rules

1. **Never delete a source file.** If a file must go, move it to `attic/` and say so.
   *(Enforced because `backend/routers/*.py` and `backend/data/schemes_data.py` were
   deleted in a past session, leaving only orphaned `__pycache__` shells.)*

2. **Never minify.** Real line breaks, one statement per line, max ~120 chars.
   *(Enforced because `Account.jsx` was written as 7 lines with a 2,902-character line.)*

3. **Never hardcode a demo input.** No branch may test for a specific place name,
   business, or user. A lookup that only works for one village is a rigged demo.
   *(Enforced because `geography.py` contained
   `if 'saravanampatti' in norm(q): return json.load(canned_file)`.)*

4. **No invented numbers.** Every numeric fact returned by the API carries
   `provenance`: `{source, source_url, retrieved_at, method}` where `method` is one of
   `measured` | `official` | `derived` | `estimated`. Anything `estimated` must render
   with an "estimate" badge in the UI. No exceptions.

5. **One number, one source of truth.** If the report states a competitor count, it is
   *the same count* as the map pins. Never compute the same quantity two different ways.
   *(Enforced because `advisory.py` computed `rivals = population * ratio / 10000` while
   the map showed unrelated OSM results.)*

6. **No silent failure.** A failed lookup returns `status: "unresolved"` with a reason.
   It never returns "outside Tamil Nadu", never returns empty-as-success, and never
   implies absence of data means absence of the thing.

7. **Tests before done.** Every task adds tests. Run them with
   `cd backend && python -m unittest discover -p "test_*.py"` (pytest is not installed).
   A task with failing tests is not finished, and must be reported as unfinished.

   **A task's file list never needs to mention test files.** Adding or editing
   `backend/test_*.py` and `tests/fixtures/*` is always permitted and never counts as
   going out of scope. Do not ask. Prefer a committed test file over an in-memory check:
   a regression guard that disappears at the end of the session guards nothing.

8. **Stay in your lane.** Backend agents do not touch `frontend/src`. UI agents do not
   touch `backend/`. Both sides code against `docs/DATA_CONTRACT.md`.

9. **The contract is frozen.** To change a response shape, edit `DATA_CONTRACT.md` first,
   in its own commit, and say what breaks. Never change a shape silently.

10. **Report honestly.** If you could not finish, say which parts are incomplete and why.
    Do not describe planned code as done. Do not claim a test passed without running it.

## Scope rule

Do exactly one numbered task from `TASKS.md` per session. Do not "improve" adjacent code.
If you spot a separate problem, append it to `TASKS.md` under "Found while working" and
leave it alone.

## Definition of done

- [ ] Acceptance criteria in the task all satisfied
- [ ] Tests written and passing
- [ ] No rule above violated
- [ ] `DATA_CONTRACT.md` updated if a shape changed
- [ ] A one-paragraph summary of what changed and what is still missing

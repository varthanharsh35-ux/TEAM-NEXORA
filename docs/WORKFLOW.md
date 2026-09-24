# WORKFLOW.md — how to drive Astra, Sonnet and Fable without another rewrite

## Why the last attempt failed

A 900-word voice transcript was pasted into an agent as a single prompt. The transcript
carried frustration but no specification, so the agent had no source of truth. It invented
one, deleted what it did not understand (`backend/routers/*.py`, `backend/data/schemes_data.py`,
the login UI, five locale files), minified what it wrote, and hardcoded the one example it was
asked about so the demo would pass.

**The prompting was not the problem. The missing contract was.** These documents are that
contract. Agents follow files far more reliably than they follow a remembered conversation.

---

## Division of labour

| Tool | Owns | Must never touch |
|---|---|---|
| **Astra** (GPT) | Ingestion pipeline, parsers, driver engine, scheme rules, FastAPI routes, tests | `frontend/src`, CSS, layout |
| **Sonnet** (Claude Code) | Specs, data contracts, task breakdown, reviewing Astra's output, the dossier, debugging | — |
| **Fable** | Page shell, components, charts, layout — against the frozen contract | `backend/`, business logic |
| **Your friends** | Visual design, to the same contract | — |

The contract is what lets all four work at once without overwriting each other. Backend and
UI agree only on `DATA_CONTRACT.md`; neither needs to read the other's code.

---

## The loop

```
1. Pick ONE numbered task from TASKS.md
2. Paste the preamble + that task block, verbatim, into Astra
3. Astra works, runs pytest, reports what passed and what it did not finish
4. Paste the diff to Sonnet for review (checklist below)
5. Fix what review finds, or re-run the task
6. Commit. Tick the task. Next.
```

Never two tasks in one session. Never a paragraph of complaints instead of a task.

### The preamble — use this exact text every time

> Read `docs/RULES.md` and `docs/DATA_CONTRACT.md` first. Then do Task N below, and only
> Task N. Do not modify anything outside the files listed in the task. Do not delete or
> minify any file. Do not add a branch that tests for a specific place name or business.
> When you are done, run `pytest backend/` and report what passed, what failed, and what you
> did not finish. If you disagree with the task, say so before writing code — do not silently
> do something else.

### Review checklist — run against every diff before committing

- [ ] No file deleted (`git diff --stat` shows no removals you did not ask for)
- [ ] No line over 120 characters
- [ ] No place name, business name or user id in any conditional
- [ ] Every new number carries `provenance` with a `method`
- [ ] No quantity computed two different ways (rule 5)
- [ ] Response shapes match `DATA_CONTRACT.md` exactly
- [ ] Tests added, and actually run — not just described
- [ ] Failures reported rather than glossed over

Points 1, 3 and 5 catch the three specific failures from last time. Check them every time.

---

## Writing a new task

If you need something not in `TASKS.md`, write it in this shape — never as prose:

```markdown
### Task N.M — one-line title [BLOCKER | CORE | POLISH]
**Files:** exact paths the agent may touch
**Problem:** what is wrong now, with the file, the line and the observed symptom
**Do:** numbered, concrete steps
**Done when:** conditions checkable by running something
```

The **Problem** field is what stops the agent redesigning around the issue instead of fixing
it. Quote the actual broken code where you can — *"the regex `amenity~"bank"` is unanchored
and matches `blood_bank`"* produces a fix; *"the competitors are wrong"* produces a rewrite.

---

## Turning frustration into a task

When something is wrong, resist pasting the complaint. Convert it:

| What you say | What the agent needs |
|---|---|
| "the map is completely broken" | Which input, which output, which file, which line, what you expected |
| "the report is generic" | The exact sentence you got, and the sentence you wanted instead |
| "this looks vibe-coded" | The specific component, and the behaviour rule it violates from `SPEC.md` §9 |

Your café-near-college and warehouse-near-Amazon examples were perfect raw material — they
are now the worked examples in `PERSONALIZATION.md` §4 and the acceptance test for Task 2.1.
Concrete scenarios become tests. General dissatisfaction becomes a rewrite.

---

## Guarding against another wipe

Before handing the repo to any agent:

```bash
git checkout -b task/N-short-name
```

One branch per task. Review the diff before merging. If an agent goes off the rails, you lose
one branch instead of the project.

Keep `attic/original/` (Task 0.2) permanently. It is the only copy of the login UI, the eight
locale files, the Bhashini service and the old page structure.

---

## Order of work

Follow `TASKS.md` phases. The dependency that matters: **Task 1.1 (offline geocoding) unblocks
almost everything else.** Without coordinates in the gazetteer there is no reliable map, no
catchment, no competitors, no drivers, and therefore no personalised report. Do it first even
though it is the least visible task on the list.

Phase 0 is three fast mechanical tasks. Do them in one sitting — every later task is easier
once the code is readable and the rigged path is gone.

# Pre-deploy review — 2026-11 (#22)

Review of the Gradebook app before the first deploy (#24). Scope and rules: [#22](https://github.com/drewpearce/gradebook/issues/22).

## Method

Five read-only subagents reviewed the app. Each subagent owned one lane:

| Lane | Prefix | Scope |
|---|---|---|
| Architecture & system design | A | ADRs, layers, API contract, tenancy, deploy shape |
| Domain & grade correctness | D | ADR-0002 policies, Decimal math, Audience rules |
| Backend API, data & security | B | Routers, schemas, models, migrations, auth |
| Frontend design & UX | F | Components, queries, mutations, UX, accessibility |
| Tests | T | Kent Beck bar, policy coverage, frontend harness |

After the lanes reported, the lead reviewer did these steps:

1. Checked each finding against the code.
2. Merged duplicate findings into one `R-` item. The source IDs stay in each item.
3. Reproduced the disputed claims on Postgres (port 5433) inside a rolled-back transaction. The table below lists the results.
4. Moved items that #23 owns to the "For #23" section.

| Claim | Reproduction | Result |
|---|---|---|
| R-03: a second Grading Scale save fails | PUT the scale, change one cutoff, PUT again | `409` on the second PUT |
| R-04: numeric overflow gives 500 | PUT a Score of `10000` | `500` |
| R-06: a long password gives 500 | `POST /auth/login` with a 100-byte password | `500` |
| R-08: Category percent is not rounded | 1/3 points in a Category | `"33.33333333333333333333333333"` |
| R-01: a failed Score save is silent | Code read, `ScoreEntryList.tsx:44,54` | `void onSave(...)` discards the rejection |

**Severity scale:**

- **blocker:** a wrong Grade, data loss, a security defect that a public-internet user can use, or a crash in login → class → scores → grades. It blocks #24.
- **high:** a defect that Katie can hit, with a workaround.
- **medium:** design, readability or test debt.
- **low:** polish.

**Proposal values:** **fix** (in #22), **file** (issue under #21), **drop**, **→ #23** (comment on #23).

## Domain policy status

No finding shows a policy violation in the current code. The domain lane proved each policy with probes on `app.domain.grades`.

| Policy | Status | Evidence | Test gap |
|---|---|---|---|
| Unscored Assignments are excluded | Holds | 8/10 + blank → 80.00 | No API test (R-11) |
| Blank ≠ 0. An explicit 0 counts. | Holds | 8/10 + 0/10 → 40.00. Clear sends DELETE. | No API test (R-11) |
| Incomplete on an empty weighted Category | Holds | Weight-0 Category never makes Incomplete | API test does not check the message |
| Empty Audience = every Grade Level | Holds | Backend `_applies`, `audience.py` and `audience.ts` agree | Test is in `tests/models/` (R-30) |
| Soft `weights_not_100`, no rejection on save | Holds | Schemas check each weight 0–100 only | "Never rejected" has no test (R-11) |
| Progressive disclosure | Holds | All pickers use `>= 2` checks | No frontend tests (R-19) |

Three findings could cause a policy problem in the future: R-05 (a delete silently makes an Audience empty), AP-1 (two copies of the weights rule), and AP-2 (three copies of the Audience rule).

## Findings

### Blockers

**R-01 · blocker · fix · S** — A failed Score save or clear is silent.
*Source:* F-1, D-1. *Location:* `frontend/src/components/scores/ScoreEntryList.tsx:44,54`.
`commit()` calls `void onSave(trimmed)` and `void onClear()`. Nothing catches the rejected promise. The input keeps the typed value, so it looks saved. The Grade is computed without it. These causes give this result: a network drop, a 401, R-04 overflow, R-02 stale connection, and `0x10` (`Number` accepts it, the API rejects it). This is silent loss of entered data in the core flow. It is a blocker because R-02 makes failures likely in production.
*Change:* await the save. On failure, show "Not saved. Try again." on the row and keep the text. Make the client check match the server (`^\d+(\.\d{1,2})?$`).
*Policy risk:* blank ≠ 0. Clear must still DELETE.

**R-02 · blocker · fix · S** — The engine gives out dead connections after Neon suspends.
*Source:* A-1, B-6. *Location:* `backend/app/db.py:24`.
`create_engine(settings.database_url)` has `pool_pre_ping=False`. Neon free tier suspends compute after about 5 idle minutes and drops the connections. `/health` does not touch the database, so health checks do not keep Neon awake. Katie uses the app at intervals, so the first request after a break probably returns 500. With R-01, that first request can be a Score that is lost without a message.
*Change:* `create_engine(url, pool_pre_ping=True)`.

### High

**R-03 · high · fix · S** — A second save of the Grading Scale returns 409.
*Source:* B-1, D-2. *Location:* `backend/app/api/routers/classes.py:141-144`.
`scale.bands = [...]` makes SQLAlchemy insert the new bands before it deletes the old ones. The new `A` row breaks `UNIQUE(grading_scale_id, letter)`. Reproduced: the first PUT gives 200, the second gives 409. Katie cannot change a cutoff. No test sends two PUTs.
*Change:* `scale.bands.clear(); session.flush()`, then assign the new bands. Add a test with two PUTs.

**R-04 · high · fix · S** — Numeric input overflows to 500, and extra decimals are rounded without notice.
*Source:* B-3, D-3, D-9. *Location:* `backend/app/schemas/score.py:9`, `schemas/coursework.py:28,50,57`, `schemas/class_.py:27,48`, `api/deps.py:23-32`.
Columns are `NUMERIC(6,2)` (points) and `NUMERIC(5,2)` (weight, min_percent). The schemas set no digit limits. Reproduced: a Score of `10000` gives 500. `commit_or_conflict` catches only `IntegrityError`, not `DataError`. Three weights of `33.333` + `33.333` + `33.334` store as 99.99, which gives an unexplained `weights_not_100`. A NUL character in a name and an int32 overflow in `position` also give 500.
*Change:* add `max_digits` and `decimal_places=2` to every Decimal field. Bound `position`. Map `DataError` to 422. Do not add a points ≤ max_points rule. Extra credit is deliberate.
*Policy risk:* explicit 0 counts (keep `ge=0`). Weights are still not required to total 100.

**R-05 · high · fix · S** — Deleting a Grade Level can silently change an Assignment's Audience to "everyone".
*Source:* A-2, B-2, D-10, F-9. *Location:* `backend/app/api/routers/classes.py:103-117`, `models/coursework.py:39`.
The delete guard checks Students only. `assignment_audience.grade_level_id` has `ON DELETE CASCADE`. A "2nd only" Assignment then has an empty Audience, which means every Grade Level. Example: Katie moves her 2nd graders to "1st", then deletes "2nd". Their old Scores on 2nd-only Assignments start to count again, and Grades change with no Score edit.
*Change:* return 409 when an Audience references the Grade Level. The message names the fix. The frontend refreshes Assignments after a Grade Level delete (R-07).
*Policy risk:* empty Audience = all. The fix keeps the rule and stops accidental entry into it.

**R-06 · high · fix · S** — A password longer than 72 bytes gives 500 on the open login route.
*Source:* B-4. *Location:* `backend/app/auth/security.py:10-16`, `cli.py:35-40`.
bcrypt 5.0 raises `ValueError` above 72 bytes. Reproduced: `POST /auth/login` with 100 bytes gives 500. Anyone on the internet can send this request. The code comment still says bcrypt "silently truncates". The CLI crashes with a traceback for the same input.
*Change:* `verify_password` returns False above 72 bytes. The CLI checks the 72-byte limit and a minimum length. Correct the comment.

**R-10 · high · fix · S** — After Katie creates an Assignment, score entry stays on the previous Assignment.
*Source:* F-10. *Location:* `frontend/src/routes/ScoreEntryPage.tsx:34,38`, `components/scores/AssignmentDialog.tsx`.
`selectedAssignment` does not change after a create, and `pickActiveId` keeps it. Katie creates "Quiz 5" and the rows still show "Quiz 4". She can type Quiz 5 Scores into Quiz 4.
*Change:* `AssignmentDialog` takes `onCreated(assignment)`. The page selects the new Assignment.

**R-11 · high · fix · S** — Two policies have no API-level test.
*Source:* T-2, T-3. *Location:* `backend/tests/api/test_api.py`.
No API test sends an explicit Score of 0, and no API test blanks a Score again with DELETE. No test saves weights that total more than 100 or PATCHes a weight so the total is not 100. A regression such as `scores.get(a.id) or 0`, or a new "must total 100" check, passes the suite. The plan rule says a policy without a pinning test is high.
*Change:* add these tests: blank excluded from the Category percent, explicit 0 counts, DELETE makes a Score blank again, weights over 100 accepted on save, PATCH to a total ≠ 100 accepted, weights over 100 give `weights_not_100`. Assert `percent is None` in the existing weights test.

**R-12 · high · fix · S** — Tests run against whatever database `DATABASE_URL` names, including the dev database.
*Source:* T-1. *Location:* `backend/app/config.py:17`, `backend/tests/conftest.py:26-36`.
The default URL is port 5432, which belongs to another project on this machine. On 5433 the tests ran against the dev database that holds Katie's teacher row and the seeded class. Rollback protects the data today. One `commit()` outside the savepoint would write to it.
*Change:* a session-scoped autouse guard aborts unless the database name ends in `_test`. Add a `gradebook_test` database for local runs. CI uses the same name. Document the command in `backend/README.md`.

### Medium

**R-07 · medium · fix · S** — No mutation invalidates the Grades query.
*Source:* F-2, A-9, D-11. *Location:* `frontend/src/api/mutations.ts:14-17`, `api/scores.ts`, `api/categories.ts`, `api/assignments.ts`, `api/grade-levels.ts`.
Score, Category, Assignment, Student, Grade Level and Grading Scale writes refresh only their own keys. The Grades view shows the cached Grade first and updates after a refetch on mount. Deleting a Grade Level also leaves deleted ids in cached Assignments. The invalidation lists are spread over ten files and already differ.
*Change:* `useInvalidatingMutation` invalidates all queries on success. For one Teacher, only active queries refetch, so the cost is small. The per-hook key lists can then go.

**R-08 · medium · fix · S** — The Category percent in the breakdown shows up to 15 digits.
*Source:* D-4. *Location:* `backend/app/services/grades.py:98`, `frontend/src/lib/format.ts`.
Reproduced: the API returns `"33.33333333333333333333333333"`. The UI shows `33.333333333333336%`. The Subject percent is rounded to 0.01, so the two values in one view use different formats. The PRD says the Grade must be explainable.
*Change:* keep the exact value for the roll-up. Round Category percent to 0.01 (ROUND_HALF_UP) in the response. `formatPercent` shows at most 2 decimals.

**R-09 · medium · fix · M** — Loading and error states show as empty states.
*Source:* F-3, F-4, F-5. *Location:* `routes/ScoreEntryPage.tsx`, `routes/GradesPage.tsx`, `components/grades/SubjectGrades.tsx`, `components/scores/ScoreEntryList.tsx:28-33`.
Every query uses `data ?? []`. While data loads, or after a failure, the pages show "Add a category to this subject first" or "No students yet". Score rows show "—" before Scores load, which looks like "unscored". The breakdown shows "blank — not counted" for scored work when the Scores query fails. The re-sync effect can also replace text that Katie is typing.
*Change:* show "Loading…" while pending and an error with Retry on failure, before any empty-state text. Disable score inputs until Scores load. Show the breakdown only when all its queries succeed. Re-sync a row only when its input does not have focus.
*Policy risk:* blank ≠ 0. A loading row must not look blank.

**R-13 · medium · fix · S** — An explicit `null` in a PATCH gives a wrong 409.
*Source:* B-5, B-9, D-9. *Location:* the PATCH handlers in `classes.py`, `coursework.py`, `students.py`.
`model_dump(exclude_unset=True)` keeps `{"name": null}`. The NOT NULL error then maps to 409 "Conflicts with an existing record". The correct code is 422. The same PATCH loop is copied five times.
*Change:* one `apply_patch(session, obj, payload)` helper in `api/deps.py` rejects null for required fields. `audience_grade_level_ids` keeps "null or [] clears".

**R-14 · medium · fix (needs Drew) · S** — A Grading Scale without a band at 0 gives a numeric Grade with no letter.
*Source:* B-7, D-7. *Location:* `backend/app/schemas/class_.py:59-62`, `domain/grades.py:50-62`.
The domain docstring assumes the scale covers 0. The API does not check it. `letter_for_percent(50, [A≥90, D≥60])` returns `None`. The UI then shows "50% ·", the same symptom as the #23 bug, with a scale present.
*Change:* `GradingScaleUpsert` requires one band with `min_percent == 0` and returns 422. The default scale already has F at 0.

**R-15 · medium · fix · S** — In a mixed-audience Subject, the Incomplete message gives the wrong fix.
*Source:* D-8. *Location:* `backend/app/services/grades.py:106-113`.
A Category with only 2nd-grade Assignments makes a 1st grader Incomplete. This is correct. The message says "Homework has no scored assignments yet." Entering Scores cannot fix it. The breakdown also says "No assignments apply." The two messages conflict.
*Change:* when no Assignment in the Category applies to the Student, say "Homework has no assignments for this grade level yet." Keep the `empty_category` code.
*Policy risk:* Incomplete on empty Category. Message only.

**R-16 · medium · fix · S** — The Incomplete badge does not say why.
*Source:* F-6. *Location:* `frontend/src/components/grades/SubjectGrades.tsx:49-51`.
ADR-0002 says the UI should show which Category is empty. The reason appears only after Katie opens a row. A `weights_not_100` Subject makes every Student Incomplete with no hint that the fix is in setup.
*Change:* show a short reason under the badge ("Missing: Tests"). When the cause is weights, show one line above the list with a link to class setup.

**R-18 · medium · fix · S** — CI has three gaps.
*Source:* A-3, A-4, T-4, T-5, T-6. *Location:* `.github/workflows/ci.yml`.

1. No step checks that `frontend/openapi.json` matches the backend. A backend PR can change the contract and pass.
2. No step checks that the models match the migrations (`alembic check`). #24 runs migrations on real data.
3. No step reports coverage.

*Change:* add an OpenAPI export + diff step, `alembic check`, a downgrade/upgrade round trip, and `pytest --cov` (report only, no threshold). Add `frontend/openapi.json` to the backend workflow paths.

**R-19 · medium · fix · M** — The frontend has no tests.
*Source:* T-16. *Location:* `frontend/`.
The UI holds policy logic: the Audience filter, Incomplete display, "blank — not counted", and the `>= 2` disclosure checks. Nothing pins it.
*Change (approved in the plan):* Vitest + jsdom + Testing Library, configured in `vite.config.ts`, no globals, no MSW. First tests: `lib/audience`, `lib/format`, `lib/errors`, `lib/active-id`, and `StudentGradeRow` (export it so it needs no QueryClient). Add `npm test` to `frontend.yml`. Container and flow tests go in a follow-up issue.

**R-20 · medium · fix · S** — Auth protection is tested on `/classes` only.
*Source:* T-7. *Location:* `backend/tests/api/test_auth.py`.
A router mounted without the auth dependency would pass the suite. Tokens with a non-UUID `sub` or no `sub` have no test.
*Change:* one parametrized test over `app.routes` expects 401 without a token. Add the two forged-token tests. Split the multi-behavior login test.

**R-21 · medium · fix · S** — Score inputs have no accessible name, and Enter does not move to the next row.
*Source:* F-11. *Location:* `frontend/src/components/scores/ScoreEntryList.tsx:66-82`.
A screen reader says "edit text" on every row. The error text is not linked to its input. Enter blurs the input, so the keyboard flow stops.
*Change:* `aria-label="{Student} score"`, `aria-invalid`, `aria-describedby`. Enter saves and moves focus to the next row.

**R-28 · medium · file · M** — Delete confirmations do not show what is lost.
*Source:* F-8, B-12. *Location:* `components/setup/ConfirmDialog.tsx`, `routes/ClassDetailPage.tsx:59-71`.
Deleting a Class removes every Student, Score and Grade in it. The dialog gives no counts. "Delete class" sits next to "Rename". The cascades are deliberate, so the fix is in the UI.
*Change:* show counts. For a Class, require Katie to type the class name. Move "Delete class" to the bottom of the page.

**R-29 · medium · file · M** — UI code is duplicated.
*Source:* F-12, F-18. *Location:* six dialogs, `ScoreEntryPage.tsx` and `GradesPage.tsx`, three copies of `gradeLevelName`.
Six dialogs repeat one reset-on-open pattern. Its effect depends on prop identity and can reset typed text after a refetch. Two pages repeat the Subject picker. Three pages repeat the Class guard.
*Change:* extract `SubjectPicker`, a Class page guard, one `gradeLevelName` helper, and a form hook that resets on the `open` change only. Keep the API hook files flat (the README reason holds).
*Policy risk:* progressive disclosure. Keep the `>= 2` checks.

**R-30 · medium · file · M** — Backend test design does not meet the Kent Beck bar.
*Source:* T-8, T-9, T-10, T-11, T-12, T-14, T-15. *Location:* `backend/tests/`.

- Several tests check more than one behavior (`test_class_crud`, `test_roster_grades`).
- Names describe the subject, not the behavior.
- `_mixed_audience_setup` returns a `dict[str, str]` with magic keys.
- Constraint tests use a bare `pytest.raises(IntegrityError)` and do not name the constraint.
- Many endpoints and error paths have no test.
- The Audience test is in `tests/models/`.
- Two `client` fixtures shadow each other.
- `dependency_overrides.clear()` removes all overrides.
- The CLI has no test.
- One Starlette deprecation warning.
- No local script runs the CI gates.

*Change:* one issue that holds this list. Keep every existing assertion value.

### Low

**R-22 · low · fix · S** — A Neon URL as given crashes at import.
*Source:* A-8. Neon gives `postgresql://…`. SQLAlchemy then loads psycopg2, which is not installed. *Change:* a `field_validator` rewrites `postgres://` and `postgresql://` to `postgresql+psycopg://`. One config test.

**R-23 · low · fix · S** — `create-teacher` creates a second full-access Teacher when the username has a typo.
*Source:* A-7. A typo during a password reset over `fly ssh console` creates a new account and leaves Katie's password unchanged. *Change:* refuse a new username when a Teacher exists, unless `--allow-second-teacher` is given. Print the existing username.

**R-24 · low · fix · S** — JWT decode does not require `exp` and `sub`. The algorithm comes from the environment.
*Source:* B-11. *Change:* `options={"require": ["exp", "sub"]}`. Hard-code `["HS256"]`.

**R-25 · low · fix · S** — Reads retry 4xx errors three times (about 7 s).
*Source:* F-14. A wrong class URL shows "Loading…" for about 7 s. *Change:* `retry: 1` on queries.

**R-27 · low · fix · S** — Score and weight copy is unclear.
*Source:* F-16, F-17. "Leave blank to exclude an assignment" is not Katie's language. The weights badge says "must total 100%", which reads as a rule. A Score above max has no hint. *Change:* footer "Blank = not scored yet (not counted). 0 = scored as zero." Weights copy "Weights total 90%. Grades stay Incomplete until they total 100%." An amber, non-blocking "Above max" hint. Use `formatPercent` for weights.
*Policy risk:* blank ≠ 0 and soft weights. Copy only. Nothing blocks a save.

**R-26 · low · file · S** — After a 401, Katie lands on `/` and loses her place. The query cache is not cleared on that path. *Source:* F-15.

**R-31 · low · file · S** — `unwrap` throws the raw body, which can be an empty string. *Source:* F-13. Throw an `ApiError` with a status. Map 422 `detail[]` to text.

**R-32 · low · file · S** — Accessibility polish. *Source:* F-19. Header link home, `aria-expanded` on the breakdown button, `autoComplete` on login inputs, dialog descriptions.

**R-33 · low · file · M** — Cross-Class integrity for Score and Audience is in app code only. *Source:* B-8. Student/Grade Level and Assignment/Category use composite FKs. Score and Audience do not. Add `class_id` with composite FKs.

### Dropped

| Item | Source | Reason |
|---|---|---|
| 404 vs 422 for a child under the wrong parent | B-10 | No client depends on the difference. Tests pin the current codes. |
| Server-side guard on Category, Subject, Class delete | B-12 | The cascades are by design. R-28 covers the UI risk. |
| Indexes on FK columns | B-13 | Not a speed problem at this size. #24 notes the Postgres 13+ requirement. |
| Reject a Score above `max_points` | B-14 | Extra credit is deliberate (`test_extra_credit_exceeds_100_uncapped`). R-27 adds a hint. |
| `teacher_id` on Class | A-7 | Multi-teacher is a #21 non-goal. R-23 covers the operator risk. |
| Lazy `settings` and engine | A-11 | One process, one config. Failing at import is the wanted behavior. |
| Token in `localStorage` | F (dropped) | No user HTML is rendered. #23 owns the security headers. |

## Architecture proposals

These need a joint decision: build now in #22, or file with a priority.

**AP-1 — Move the `weights_not_100` rule into the domain module. Delete the normalization that no caller can reach.**
*Source:* A-5, D-5, D-12. *Location:* `domain/grades.py:176-187`, `services/grades.py:88-131`.
The domain divides by the actual weight total. Its docstring says "no re-scaling". The service then checks `total == 100` and discards that number. Probe: weights 50 + 30 give 81.25 B in the domain, then Incomplete in the service. A future caller of `compute_subject_grade` gets a re-scaled Grade, which ADR-0002 rejects.

- *For:* the whole policy lives in one pure, tested module. The service becomes a mapper. Dead code goes.
- *Against:* it changes the grade function just before Katie's first use. It touches domain tests and the `SubjectGrade` shape.
- *Recommendation:* **build now, after R-11.** R-11 pins the API behavior first, so the refactor has a safety net. Effort S–M.
- *Policy risk:* soft `weights_not_100`, blanks excluded, Incomplete on empty Category. The API output must not change.

**AP-2 — One pure Audience rule. No ORM import in `app/domain`.**
*Source:* A-6(a), D-6. *Location:* `domain/audience.py`, `domain/grades.py:98-103`.
`domain/audience.py` imports `Student` and `Assignment` and reads `assignment.audience[*].id`. `domain/grades.py` has its own `_applies`. A policy change must happen in three places (two backend, one frontend).

- *For:* `app/domain` is pure again. One backend copy of the rule.
- *Against:* little. The rule is two lines.
- *Recommendation:* **build now.** Effort S.
- *Policy risk:* empty Audience = all. The mixed-audience tests must pass unchanged.

**AP-3 — Return per-Assignment lines in `GradeResponse`.**
*Source:* A-6(b), F-5. *Location:* `schemas/grade.py`, `components/grades/SubjectGrades.tsx`.
The Grades view fetches Assignments and Scores separately and runs the Audience rule again to show what counted. The explanation can disagree with the number if a fetch fails or the rules drift.

- *For:* one source of truth for "what counted". Fewer queries in the Grades view.
- *Against:* a larger response, a contract change, new types. R-09 fixes the failure case for now.
- *Recommendation:* **file, P2.** Effort M.
- *Policy risk:* blank ≠ 0. A blank line must show "not counted", never 0.

**AP-4 — ADR-0001 "auth across an origin boundary" is no longer true in production.**
*Source:* A-10. Same-origin serving makes CORS a dev-only concern. *Recommendation:* **→ #24.** ADR-0004 amends this consequence of ADR-0001.

## For #23

These items are in #23 scope. Each goes to #23 as one comment.

- `/docs`, `/redoc` and `/openapi.json` are public. Disable them in production or require auth.
- `ENVIRONMENT` defaults to `"dev"`. If the variable is missing in production, the `SECRET_KEY` guard does not run. Consider an allow-list, or require `ENVIRONMENT` to be set.
- The guard checks `secret_key` only. The localhost `DATABASE_URL` default with dev credentials is accepted outside dev.
- `login()` maps every non-OK response to "Incorrect username or password". A 5xx (see R-02) or the new 429 will look like a wrong password. Read `Retry-After`. (F-7)
- `client.ts:6` defaults `API_URL` to `http://localhost:8000`. A build without `VITE_API_URL` calls localhost. `login()` uses a separate raw `fetch` with the same base.
- CORS uses `allow_methods=["*"]` and `allow_headers=["*"]`. Same-origin serving can remove CORS in production.
- A password reset through the CLI does not revoke existing tokens (12-hour lifetime).
- A 500 on `/auth/login` must not skip the failure counter.
- Same-origin serving makes an httpOnly cookie possible in place of `localStorage`. Optional.
- The dangling "·" also occurs when a scale does not cover the percent. If R-14 lands, only the no-scale case remains.

## Strengths to keep

- `app/domain/grades.py` is a deep, pure module with frozen value objects and docstrings that state ADR-0002.
- Composite FKs enforce Student/Grade Level and Assignment/Category integrity in the database.
- Auth is applied once per router in `main.py`. A new route on these routers cannot skip it.
- CRUD routers stay thin with `get_or_404` and `commit_or_conflict`. Only grades has a service, because only grades has logic.
- Login runs a dummy hash for unknown users, so response time does not reveal valid usernames.
- The grade service loads Subject data once per roster. No N+1 queries.
- The UI handles blank vs 0 correctly: clear sends DELETE, `0` is stored and shown.
- The OpenAPI contract and generated client are committed with a diff gate. Only the backend half is missing (R-18).

## Triage summary

**Decisions (Drew, 2026-11-06):**

- All proposed fixes land in #22 before #24.
- R-14: the API requires one band at 0%.
- AP-1 and AP-2: build now, after the R-11 tests land.
- Filed issues get one `priority:P1`, `priority:P2` or `priority:P3` label and become sub-issues of #21.

| Proposal | Items |
|---|---|
| **fix in #22** | R-01, R-02, R-03, R-04, R-05, R-06, R-07, R-08, R-09, R-10, R-11, R-12, R-13, R-14, R-15, R-16, R-18, R-19, R-20, R-21, R-22, R-23, R-24, R-25, R-27, AP-1, AP-2 |
| **file under #21** | R-26, R-28, R-29, R-30, R-31, R-32, R-33, AP-3 |
| **→ #23** | "For #23" list |
| **→ #24** | AP-4, Postgres 13+ note |
| **drop** | See "Dropped" |

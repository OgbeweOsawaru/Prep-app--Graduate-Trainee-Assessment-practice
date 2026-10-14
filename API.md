# Prep App: API Contract (v1.0, matches the Phase 1 code)

Status: this file describes what the code in `routers/tests.py` actually does. If the code changes, change this file in the same sitting.

## General rules

- All requests and responses are JSON.
- Times are ISO 8601 in UTC, e.g. `2026-10-14T20:37:12Z`.
- Sections are exactly: `numerical`, `verbal`, `critical`.
- Answer letters are exactly: `a`, `b`, `c`, `d`, `e` (lowercase).
- The blueprint (questions per section), time limit and grace period come from `config.py`, never hard-coded in endpoints.
- There are no accounts yet, so the `attempt_id` acts as a secret. It is a UUID4, never a counter.
- **The correct answer and explanation are never sent until the attempt is submitted.**
- Attempts live in server memory. Restarting the server deletes all of them (SQLite comes in Phase 3).

### Error format

Errors raised by the app have the right HTTP status and this body:

```json
{ "detail": { "code": "machine_readable_code", "message": "Human readable text" } }
```

The front end should read `detail.code`.

Requests with a malformed body or an invalid answer letter (for example `"z"`) are rejected by FastAPI before the route runs. They get status 422 with the standard FastAPI body, where `detail` is a **list** of problems, not an object with a `code`. The front end should treat any 422 whose `detail` is a list as "invalid request".

### Numbers

`percent` is rounded to one decimal. JSON may write a whole value as `4` instead of `4.0`, so the front end must not assume a decimal point is present.

---

## 1. Start a test

`POST /tests`

**Request body:** none (accounts and access codes come in Phase 4).

**Response 201:**

```json
{
  "attempt_id": "uuid",
  "started_at": "2026-10-14T20:37:12Z",
  "deadline": "2026-10-14T21:37:12Z",
  "duration_seconds": 3600,
  "server_time": "2026-10-14T20:37:12Z",
  "questions": [
    {
      "id": "N012",
      "section": "numerical",
      "passage": null,
      "question": "...",
      "options": { "a": "...", "b": "...", "c": "...", "d": "...", "e": "..." }
    }
  ]
}
```

Notes:
- `questions` is grouped by section in blueprint order: all `numerical`, then all `verbal`, then all `critical`. Order within each section is random. Array order is the order shown.
- No `answer`, no `explanation` anywhere in this response.
- `server_time` lets the browser correct for a wrong clock on the user's device when drawing the countdown. The real deadline is `deadline`, held on the server.

**Errors:** none defined. A broken question bank stops the app from starting, so a running app can always build a test.

---

## 2. Submit

`POST /tests/{attempt_id}/submit`

**Request body:**

```json
{ "answers": { "N012": "c", "V004": "a" } }
```

A skipped question is simply missing (or `null`). Skipped scores zero. An empty `answers` object is valid.

**Response 200:** `{ "status": "submitted" }`. The client then fetches results (endpoint 3), so a results page can be reloaded at any time.

**Checks, in this order** (the first one that fails decides the error):

1. `404 attempt_not_found`: no attempt with that id.
2. `409 already_submitted`: this attempt was already submitted.
3. `409 deadline_passed`: the server's current time is later than `deadline` plus `GRACE_SECONDS`.
4. `422 unknown_question`: a key in `answers` is not a question in this attempt.

**Timer rule:** the server compares its own clock to `deadline`. Submissions up to `GRACE_SECONDS` (15, set in `config.py`) after the deadline are accepted, to cover network delay when the browser auto-submits at 0:00. After that they are rejected, and the attempt can no longer be submitted.

---

## 3. Get results

`GET /tests/{attempt_id}/results`

Only works after submission. Before that it refuses, otherwise this endpoint would be a way to read the answers.

**Response 200:**

```json
{
  "attempt_id": "uuid",
  "submitted_at": "2026-10-14T20:40:32Z",
  "time_taken_seconds": 200,
  "overall": { "correct": 41, "total": 60, "percent": 68.3 },
  "sections": {
    "numerical": { "correct": 17, "total": 25, "percent": 68.0 },
    "verbal":    { "correct": 17, "total": 25, "percent": 68.0 },
    "critical":  { "correct": 7,  "total": 10, "percent": 70.0 }
  },
  "review": [
    {
      "id": "N012",
      "section": "numerical",
      "passage": null,
      "question": "...",
      "options": { "a": "...", "b": "...", "c": "...", "d": "...", "e": "..." },
      "your_answer": "c",
      "correct_answer": "a",
      "is_correct": false,
      "explanation": "..."
    }
  ]
}
```

Notes:
- `review` contains every question, in test order (grouped by section). The front end filters to missed ones.
- `your_answer` is `null` for skipped questions.

**Errors:**
- `404 attempt_not_found`
- `409 not_submitted`: the attempt has not been submitted yet.

---

## Planned, NOT BUILT YET

These are not served by the Phase 1 code. Do not call them from the front end.

- **Resume after refresh:** `GET /tests/{attempt_id}` returning the questions, `seconds_remaining` and saved answers.
- **Save an answer as the test goes:** `PUT /tests/{attempt_id}/answers/{question_id}` with `{ "answer": "c" }`.

Both need the attempt record to be updated before submission, so they are best built together, in or after Phase 3.

---

## Decisions made

1. **Late submissions:** rejected after the grace period (`409 deadline_passed`). The work is lost; revisit if testers complain.
2. **Resume endpoint:** deferred, see above.
3. **Grace period:** 15 seconds.
4. **Percent:** one decimal place.
5. **Section order:** grouped, in blueprint order; random within a section.

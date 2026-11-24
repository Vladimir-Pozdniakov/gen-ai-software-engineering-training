# Plan: Homework 1 – Banking Transactions API (Python / FastAPI)

## Context
`homework-1/TASKS.md` asks for a minimal in-memory REST API for banking transactions (Tasks 1–3 required, ≥1 of Task 4 options), plus README/HOWTORUN, screenshots and demo files. The folder currently has only stubs (`README.md`, `HOWTORUN.md`, empty `src/`, `docs/screenshots/`), a `pyproject.toml` (Python ≥3.12, no deps), a `.venv` and `.ruff_cache`. No `demo/` dir yet. Work happens on branch `homework-1-submission`.

**Stack:** FastAPI + Pydantic v2 + Uvicorn; pytest + httpx (TestClient) for tests; ruff (already in use). Dependencies managed in `pyproject.toml` (plus `requirements.txt` for simple install).

**Task 4:** implement A (summary), C (CSV export) and D (rate limiting, 100 req/min/IP) — all cheap, and only one is required.

## Design decisions
- **Layout** (`homework-1/`):
  ```
  src/
    main.py                # app factory, exception handlers, middleware, router wiring
    models.py              # Pydantic: TransactionCreate, Transaction, enums
    validators.py          # ACCOUNT_RE, ISO 4217 set, amount/decimal checks
    storage.py             # in-memory TransactionStore (list + lock), add/get/filter
    services.py            # balance, summary, export (pure functions over store)
    rate_limit.py          # sliding-window per-IP middleware
    routes/transactions.py # /transactions*, export
    routes/accounts.py     # /accounts/{id}/balance, /summary
  tests/                   # pytest
  demo/                    # run.sh, sample-requests.http, sample-data.json
  docs/screenshots/
  ```
- **Money:** parse `amount` as `Decimal` (avoid float drift), enforce `> 0` and ≤ 2 decimal places; serialize as JSON number.
- **Field semantics by type:** `deposit` → `toAccount` required; `withdrawal` → `fromAccount` required; `transfer` → both required and different. Unused side is `null`. Document in README.
- **Status:** new transactions are stored as `completed` (no async settlement). Balance = Σ incoming − Σ outgoing over `completed` transactions only. No overdraft check (sample transfer from an empty account must work); documented as a decision.
- **Errors:** override `RequestValidationError` handler to emit `{"error":"Validation failed","details":[{"field","message"}]}` with HTTP 400 (not FastAPI's default 422). 404 → `{"error": "..."}`.
- **Route order:** register `GET /transactions/export` before `/transactions/{id}`.
- **Filters:** `accountId` (matches from or to), `type`, `from`/`to` (inclusive dates; `to` covers the whole day), all ANDed; invalid dates/type/`from>to` → 400 with details.
- **Camel-case JSON** via Pydantic alias generator (`fromAccount`, `toAccount`).

## Steps
1. **Scaffold & deps** – add `fastapi`, `uvicorn[standard]` to `pyproject.toml`; dev group `pytest`, `httpx`, `ruff`; create `requirements.txt`; add `.gitignore` (`.venv/`, `__pycache__/`, `.env`, `.ruff_cache/`, `.pytest_cache/`); create `demo/`.
2. **Models** (`models.py`) – enums `TransactionType`, `TransactionStatus`; `TransactionCreate` (input) and `Transaction` (adds `id` UUID, `timestamp` UTC ISO 8601, `status`).
3. **Validators** (`validators.py`) – regex `^ACC-[A-Za-z0-9]{5}$`; ISO 4217 code set (hardcode active codes); Pydantic field/model validators with the exact messages from TASKS.md (“Amount must be a positive number”, “Invalid currency code”, etc.); per-type account rules.
4. **Storage** (`storage.py`) – `TransactionStore` with `add`, `get`, `list(filters)`; module-level singleton injected via FastAPI `Depends` so tests can swap in a fresh store.
5. **Core endpoints** (Task 1) – `POST /transactions` (201), `GET /transactions` (200), `GET /transactions/{id}` (200/404), `GET /accounts/{id}/balance` (200; 400 on bad account format) returning `{accountId, balance, currency?}`. Balance is per-currency map `{"USD": 100.5}` to avoid mixing currencies.
6. **Validation handler** (Task 2) – custom exception handler in `main.py` producing the spec's error shape; map Pydantic `loc` → `field` name (camelCase).
7. **Filtering** (Task 3) – query params on `GET /transactions`, applied in `storage.list`.
8. **Task 4 features**
   - A: `GET /accounts/{id}/summary` → `totalDeposits`, `totalWithdrawals`, `transactionCount`, `mostRecentTransaction`.
   - C: `GET /transactions/export?format=csv` → `text/csv` via `csv` + `StreamingResponse`/`Response`; unsupported format → 400.
   - D: `rate_limit.py` ASGI/HTTP middleware, sliding window of 100 req/60 s keyed by `request.client.host`; returns 429 + `Retry-After`. Limit configurable via env var (so tests can lower it).
9. **Tests** (`tests/`) – pytest + `TestClient`: happy paths for every endpoint; validation matrix (negative/zero amount, 3 decimals, bad account, bad currency, missing fields, same from/to on transfer); 404s; each filter alone and combined; balance math across deposit/withdrawal/transfer; summary; CSV content/headers; rate limit (set limit low via env/fixture → 429). Target high coverage via `pytest --cov`.
10. **Demo files** – `demo/run.sh` (create venv if absent, install, `uvicorn src.main:app --port 3000`), `demo/sample-requests.http` (all endpoints incl. error cases), `demo/sample-data.json` (several transactions + a loader snippet/`curl` loop in `sample-requests.sh` optional).
11. **Docs** – fill `README.md` (name/date/AI tools, features, architecture & decisions above, limitations), `HOWTORUN.md` (prereqs, install, run, test, example curl calls). Add AI-usage notes (prompts used, what was refined).
12. **Screenshots** – manual: AI prompt/generation screenshots, server running, curl/Postman request-responses → `docs/screenshots/`. (User-performed; I'll list exactly which to capture.)
13. **Lint & PR** – `ruff check && ruff format`, run full tests, commit on `homework-1-submission`, open PR to `main` (only on user's request).

## Critical files
- `homework-1/pyproject.toml` (modify), `homework-1/requirements.txt`, `homework-1/.gitignore` (new)
- `homework-1/src/*.py`, `src/routes/*.py` (new)
- `homework-1/tests/*.py`, `homework-1/demo/*` (new)
- `homework-1/README.md`, `homework-1/HOWTORUN.md` (fill in)

No existing application code to reuse; stdlib (`decimal`, `csv`, `uuid`, `re`, `threading`) covers most needs.

## Verification
1. `cd homework-1 && source .venv/bin/activate && pip install -e ".[dev]"`
2. `pytest --cov=src -q` – all green, coverage high.
3. `bash demo/run.sh`, then run every request from the TASKS.md sample section (`curl` POST transfer, list, `?accountId=`, balance) and expect 201/200 with correct JSON.
4. Error checks: POST with `amount: -5, currency: "XXX"` → 400 with the exact `{"error":"Validation failed","details":[...]}` shape; unknown id → 404.
5. Filters: combine `accountId`, `type`, `from`, `to`; confirm results.
6. `GET /transactions/export?format=csv` downloads valid CSV; `/accounts/ACC-12345/summary` matches hand-computed totals.
7. Fire 101 requests in a minute (`for i in $(seq 101); do curl -s -o /dev/null -w "%{http_code}\n" ...`) → last returns 429.
8. Open `http://localhost:3000/docs` (auto Swagger UI) for a screenshot.

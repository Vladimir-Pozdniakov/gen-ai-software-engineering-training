# 🏦 Homework 1: Banking Transactions API

> **Student Name**: Volodymyr Pozdniakov
> **Date Submitted**: 2026-11-25
> **AI Tools Used**: Claude Code (Claude Sonnet 5.5, `feature-dev` plugin)

---

## 📋 Project Overview

A minimal REST API for banking transactions built with **Python 3.12 + FastAPI**, using
in-memory storage (no database). It implements all required tasks (core API, validation,
transaction history filters) plus **three** optional features: account summary, CSV export and
rate limiting.

| Task | Status | Where |
|------|--------|-------|
| 1. Core API (create/list/get transactions, balance) | ✅ | `src/routes/`, `src/services.py` |
| 2. Validation (amount, account format, ISO 4217 currency) | ✅ | `src/validators.py`, `src/models.py`, `src/errors.py` |
| 3. History filters (`accountId`, `type`, `from`/`to`, combined) | ✅ | `src/routes/transactions.py`, `src/storage.py` |
| 4A. Account summary | ✅ | `GET /accounts/{id}/summary` |
| 4C. CSV export | ✅ | `GET /transactions/export?format=csv` |
| 4D. Rate limiting (100 req/min/IP → 429) | ✅ | `src/rate_limit.py` |

See [HOWTORUN.md](HOWTORUN.md) for setup and usage.

## 🔌 API Reference

| Method | Endpoint | Description | Success |
|--------|----------|-------------|---------|
| `POST` | `/transactions` | Create a transaction | `201` |
| `GET` | `/transactions` | List transactions; filters `accountId`, `type`, `from`, `to` | `200` |
| `GET` | `/transactions/{id}` | Get one transaction | `200` / `404` |
| `GET` | `/transactions/export?format=csv` | Export all transactions as CSV | `200` |
| `GET` | `/accounts/{accountId}/balance` | Per-currency balance | `200` |
| `GET` | `/accounts/{accountId}/summary` | Deposits, withdrawals, count, latest date | `200` |

Interactive docs are served at `/docs` (Swagger UI) when the app is running.

**Transaction** (JSON is camelCase):

```json
{
  "id": "uuid", "fromAccount": "ACC-12345", "toAccount": "ACC-67890",
  "amount": 100.5, "currency": "USD", "type": "transfer",
  "timestamp": "2026-11-24T22:45:49.881376Z", "status": "completed"
}
```

**Validation error** (HTTP 400):

```json
{
  "error": "Validation failed",
  "details": [
    {"field": "amount", "message": "Amount must be a positive number"},
    {"field": "currency", "message": "Invalid currency code"}
  ]
}
```

Other errors use `{"error": "<message>"}` (404, 405, 429 with `Retry-After`, 500).

## 🏗️ Architecture

```
src/
├── main.py            # create_app(): wires handlers, rate limit middleware, routers
├── models.py          # Pydantic models + enums, per-type account rules
├── validators.py      # pure helpers: amount, ACC-XXXXX, ISO 4217 codes
├── errors.py          # uniform JSON error responses
├── storage.py         # thread-safe in-memory TransactionStore + FastAPI dependency
├── services.py        # balance, summary, CSV (pure functions over the store)
├── rate_limit.py      # per-IP sliding-window middleware
└── routes/
    ├── transactions.py
    └── accounts.py
tests/                 # pytest suite (103 tests, 100% line coverage of src/)
demo/                  # run.sh, sample-requests.{sh,http}, sample-data.json
```

Layering: routes are thin → services hold business logic → storage holds data. Validators
have no dependency on models, which avoids import cycles and keeps them unit-testable.

### Design decisions

- **FastAPI + Pydantic v2**: request validation, camelCase aliases and Swagger docs for free.
- **`Decimal` for money**: amounts are parsed as `Decimal` so `0.1 × 10` is exactly `1.0`;
  they are serialized as JSON numbers. Strings and booleans are rejected as amounts.
- **Field rules by type**: `deposit` needs `toAccount`; `withdrawal` needs `fromAccount`;
  `transfer` needs both and they must differ. Supplying the unused side is rejected (400),
  so it is always `null`.
- **Status**: transactions are stored as `completed` immediately (there is no async settlement).
  Balances and summaries only count `completed` transactions.
- **No overdraft check**: the sample transfer from an empty account must succeed, so balances
  can go negative. This is deliberate and out of scope for the assignment.
- **Per-currency balances**: the API never adds USD to EUR, so the balance is a map such as
  `{"USD": 599.0, "EUR": 500.0}`. An unknown account returns `200` with `{}`.
- **400, not 422**: validation errors use HTTP 400 and the exact shape from the assignment.
- **Dates are UTC**: `from`/`to` are inclusive UTC calendar days; `to` covers the whole day.
- **Rate limiting** is per direct client IP (`X-Forwarded-For` is ignored), in-memory and
  per process. Limit is configurable with `RATE_LIMIT_PER_MINUTE` (default 100).
- **CSV export** ignores the list filters and exports everything.

### Known limitations

- Data is lost on restart (in-memory by design); one process only.
- Behind a reverse proxy all clients would share one rate-limit bucket.
- No authentication, no overdraft protection, no pagination.

## 🧪 Tests

```bash
pytest --cov=src --cov-report=term-missing
```

103 tests cover every endpoint, the validation matrix, each filter alone and combined, balance
math, summary, CSV, rate limiting (with a fake clock) and the error handlers.

## 🤖 AI Usage

I used **Claude Code** to plan and build the project step by step.

**Workflow**
1. Asked for a step-by-step implementation plan from `TASKS.md` in plan mode, reviewed it as
   `IMPLEMENTATION_PLAN.md`, and chose the stack (Python/FastAPI) and the Task 4 options.
2. Implemented the plan one step at a time (scaffold → models → validators → storage →
   endpoints → error handler → filters → extras → tests → demo → docs), reviewing the result
   of each step before moving on.
3. After each step, the output was exercised with `TestClient` or `curl` rather than trusted.

**Where AI output needed correcting** (examples of iterating rather than copy-pasting)
- A non-string `currency` (e.g. `5`) returned Pydantic's generic "Input should be a valid
  string" instead of "Invalid currency code". The tests caught it; the currency check now runs
  before type coercion.
- The store compared the type filter with `is`, which silently matched nothing when given a
  plain string; changed to `==`.
- Date-filter checks first looked wrong because my test used local dates while timestamps are
  UTC. The behaviour was right; the README now states that dates are UTC.
- Ruff's auto-fix turned the currency list into one 1,000-character line; rewritten to a
  readable multi-line block.

**Prompt log**: the prompts used are recorded in the screenshots below.

### Screenshots (`docs/screenshots/`)

- `ai-prompt-*.png` — Claude Code prompts and generated code
- `api-running.png` — API running (server log / Swagger UI)
- `api-requests.png` — sample requests and responses

---

<div align="center">

*This project was completed as part of the AI-Assisted Development course.*

</div>

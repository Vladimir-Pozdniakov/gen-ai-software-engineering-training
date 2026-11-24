# ▶️ How to Run the application

## Prerequisites

- Python **3.12+**
- Optional: [`uv`](https://docs.astral.sh/uv/) (used automatically by `demo/run.sh` if installed)

All commands below are run from the `homework-1/` directory.

## 1. Quick start (one command)

```bash
./demo/run.sh
```

The script creates `.venv` if needed, installs `requirements.txt` if needed, and starts the API
on **http://localhost:3000**. Swagger UI is at http://localhost:3000/docs.

Options (environment variables):

```bash
PORT=8080 ./demo/run.sh                    # different port
RATE_LIMIT_PER_MINUTE=5 ./demo/run.sh      # lower the limit to see HTTP 429 quickly
```

## 2. Manual setup

```bash
python3 -m venv .venv            # or: uv venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt  # or: uv pip install -r requirements.txt

python -m uvicorn src.main:app --port 3000 --reload
```

> A venv created by `uv` has no `pip`; use `uv pip install ...` there.

## 3. Try it out

With the server running, in another terminal:

```bash
# Run the whole demo (loads demo/sample-data.json, then calls every endpoint)
./demo/sample-requests.sh

# Or by hand
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":100.50,"currency":"USD","type":"transfer"}'

curl http://localhost:3000/transactions
curl "http://localhost:3000/transactions?accountId=ACC-12345&type=transfer&from=2024-01-01&to=2030-12-31"
curl http://localhost:3000/accounts/ACC-12345/balance
curl http://localhost:3000/accounts/ACC-12345/summary
curl "http://localhost:3000/transactions/export?format=csv"
```

`demo/sample-requests.http` has the same calls for the PyCharm HTTP Client or VS Code REST Client.

To see rate limiting (default 100 requests/minute/IP):

```bash
for i in $(seq 105); do curl -s -o /dev/null -w "%{http_code}\n" localhost:3000/transactions; done | sort | uniq -c
# 100 × 200, then 5 × 429
```

## 4. Run the tests

```bash
pip install -r requirements.txt    # includes pytest, pytest-cov, httpx, ruff
pytest --cov=src --cov-report=term-missing
```

Expected: **95 passed**, 100% line coverage of `src/`. (A `StarletteDeprecationWarning`
about `httpx` is harmless.)

Lint / format:

```bash
ruff check . && ruff format --check .
```

## 5. Configuration

| Variable | Default | Meaning |
|----------|---------|---------|
| `PORT` | `3000` | Port used by `demo/run.sh` |
| `RATE_LIMIT_PER_MINUTE` | `100` | Max requests per minute per client IP |

## Notes

- Storage is in-memory: restarting the server clears all data.
- Dates in the `from`/`to` filters are UTC calendar days (inclusive).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Address already in use` | Use another port: `PORT=8080 ./demo/run.sh` |
| `No module named pip` in `.venv` | The venv was made by `uv`; use `uv pip install -r requirements.txt` |
| `ModuleNotFoundError: src` | Run commands from the `homework-1/` directory |
| Unexpected `429` | The rate limit was hit; wait a minute or raise `RATE_LIMIT_PER_MINUTE` |

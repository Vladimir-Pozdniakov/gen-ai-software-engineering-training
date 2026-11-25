#!/usr/bin/env bash
# Start the Banking Transactions API (http://localhost:3000, docs at /docs).
#   ./demo/run.sh              # default port 3000
#   PORT=8080 ./demo/run.sh    # custom port
#   HOST=0.0.0.0 ./demo/run.sh # expose on the network (default: localhost only)
#   RATE_LIMIT_PER_MINUTE=5 ./demo/run.sh   # lower the rate limit to try out HTTP 429
set -euo pipefail

cd "$(dirname "$0")/.."          # homework-1/
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-3000}"
PY=".venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "Creating virtual environment in .venv ..."
  if command -v uv >/dev/null 2>&1; then uv venv .venv; else python3 -m venv .venv; fi
fi

if ! "$PY" -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo "Installing dependencies ..."
  if command -v uv >/dev/null 2>&1; then
    uv pip install --quiet --python "$PY" -r requirements.txt
  else
    "$PY" -m pip install --quiet -r requirements.txt
  fi
fi

echo "Starting API on http://localhost:${PORT}  (Swagger UI: http://localhost:${PORT}/docs)"
exec "$PY" -m uvicorn src.main:app --host "$HOST" --port "$PORT"

#!/usr/bin/env bash
# Exercise every endpoint with curl. Start the API first (./demo/run.sh).
#   BASE_URL=http://localhost:8080 ./demo/sample-requests.sh
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:3000}"
DIR="$(cd "$(dirname "$0")" && pwd)"
J='Content-Type: application/json'

show() { printf '\n\033[1m### %s\033[0m\n' "$1"; }
req()  { curl -s -w '\nHTTP %{http_code}\n' "$@"; }

show "Load sample-data.json (8 transactions)"
python3 - "$DIR/sample-data.json" <<'PY' | while IFS= read -r body; do
import json, sys
for tx in json.load(open(sys.argv[1])):
    print(json.dumps(tx))
PY
  curl -s -o /dev/null -w '%{http_code} ' -X POST "$BASE_URL/transactions" -H "$J" -d "$body"
done
echo

show "Create a transaction (201)"
req -X POST "$BASE_URL/transactions" -H "$J" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":100.50,"currency":"USD","type":"transfer"}'

show "List all transactions (200)"
req "$BASE_URL/transactions"

show "Filter: accountId=ACC-12345"
req "$BASE_URL/transactions?accountId=ACC-12345"

show "Filter: type=deposit"
req "$BASE_URL/transactions?type=deposit"

show "Filter: date range"
TODAY="$(date -u +%Y-%m-%d)"
req "$BASE_URL/transactions?from=2024-01-01&to=$TODAY"

show "Combined filters: accountId + type + date range"
req "$BASE_URL/transactions?accountId=ACC-12345&type=deposit&from=2024-01-01&to=$TODAY"

show "Get one transaction by id (200)"
ID="$(curl -s "$BASE_URL/transactions" | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])')"
req "$BASE_URL/transactions/$ID"

show "Unknown transaction id (404)"
req "$BASE_URL/transactions/does-not-exist"

show "Account balance (per currency)"
req "$BASE_URL/accounts/ACC-12345/balance"

show "Account summary"
req "$BASE_URL/accounts/ACC-12345/summary"

show "Export CSV"
req "$BASE_URL/transactions/export?format=csv"

show "Validation error: negative amount + bad currency (400)"
req -X POST "$BASE_URL/transactions" -H "$J" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":-5,"currency":"XXX","type":"transfer"}'

show "Validation error: 3 decimals + bad account format (400)"
req -X POST "$BASE_URL/transactions" -H "$J" \
  -d '{"fromAccount":"12345","toAccount":"ACC-67890","amount":1.234,"currency":"USD","type":"transfer"}'

show "Validation error: transfer to the same account (400)"
req -X POST "$BASE_URL/transactions" -H "$J" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-12345","amount":10,"currency":"USD","type":"transfer"}'

show "Invalid filter (400)"
req "$BASE_URL/transactions?type=gift&from=2024-02-01&to=2024-01-01"

show "Invalid account id on balance (400)"
req "$BASE_URL/accounts/bad/balance"

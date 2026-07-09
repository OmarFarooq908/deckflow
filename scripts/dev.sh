#!/usr/bin/env bash
# Start Deckflow API + Vite dev server with automatic port selection.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WEB_START="${DECKFLOW_WEB_PORT:-5173}"
API_START="${DECKFLOW_API_PORT:-5174}"

port_in_use() {
  lsof -iTCP:"$1" -sTCP:LISTEN -t >/dev/null 2>&1
}

find_free_port() {
  local port=$1
  local max=$((port + 100))
  while port_in_use "$port"; do
    port=$((port + 1))
    if (( port > max )); then
      echo "No free port found near $1 (checked up to ${max})." >&2
      exit 1
    fi
  done
  echo "$port"
}

if [[ -f "${ROOT}/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT}/.venv/bin/activate"
fi

if [[ ! -d "${ROOT}/web/node_modules" ]]; then
  echo "Installing web dependencies (first run)…" >&2
  (cd web && npm ci)
fi

WEB_PORT="$(find_free_port "$WEB_START")"
API_PORT="$(find_free_port "$API_START")"
while [[ "$API_PORT" -eq "$WEB_PORT" ]]; do
  API_PORT="$(find_free_port $((API_PORT + 1)))"
done

export DECKFLOW_API_PORT="$API_PORT"

run_api() {
  if command -v deckflow >/dev/null 2>&1; then
    deckflow serve --port "$API_PORT" "$@"
  elif [[ -x "${ROOT}/.venv/bin/python" ]]; then
    "${ROOT}/.venv/bin/python" -m cli.main serve --port "$API_PORT" "$@"
  else
    echo "deckflow CLI not found. Run: pip install -e \".[dev]\"" >&2
    exit 1
  fi
}

API_PID=""
WEB_PID=""

cleanup() {
  local code=$?
  [[ -n "$WEB_PID" ]] && kill "$WEB_PID" 2>/dev/null || true
  [[ -n "$API_PID" ]] && kill "$API_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  exit "$code"
}
trap cleanup EXIT INT TERM

echo "Deckflow dev"
echo "  API : http://127.0.0.1:${API_PORT}"
echo "  Web : http://localhost:${WEB_PORT}"
if [[ "$WEB_PORT" != "$WEB_START" || "$API_PORT" != "$API_START" ]]; then
  echo "  (defaults ${WEB_START}/${API_START} were in use — using alternate ports)"
fi
echo

run_api &
API_PID=$!

ready=0
for _ in $(seq 1 50); do
  if curl -sf "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1; then
    ready=1
    break
  fi
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "API process exited before becoming ready." >&2
    exit 1
  fi
  sleep 0.2
done

if [[ "$ready" -ne 1 ]]; then
  echo "API did not become ready on port ${API_PORT}." >&2
  exit 1
fi

(
  cd web
  exec npm run dev -- --port "$WEB_PORT" --strictPort
) &
WEB_PID=$!

wait "$API_PID" "$WEB_PID"

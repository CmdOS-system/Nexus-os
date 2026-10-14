#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }; }
need python3
need bash
need find
need grep
need xargs

echo "[1/5] Security regression scan"
if grep -R -n -E 'from secrets import|\.invoke\(' "$ROOT/agent" --include='*.py' --exclude-dir='__pycache__'; then
  echo "Forbidden legacy security API detected" >&2
  exit 1
fi

echo "[2/5] Python syntax"
find "$ROOT/agent" -name '*.py' -print0 | xargs -0 -n1 python3 -m py_compile

echo "[3/5] Agent unit tests"
python3 -m unittest discover -s "$ROOT/agent/tests" -p 'test_*.py' -v

echo "[4/5] Image source validation"
bash "$ROOT/image/validate.sh"

echo "[5/5] Live-build staging"
need lb
NEXUS_PREPARE_ONLY=1 bash "$ROOT/image/build.sh"

echo "Nexus preflight passed"

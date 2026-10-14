#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[1/4] Python syntax"
find "$ROOT/agent" -maxdepth 1 -name '*.py' -print0 | xargs -0 -n1 python3 -m py_compile
echo "[2/4] Agent unit tests"
python3 -m unittest discover -s "$ROOT/agent/tests" -p 'test_*.py' -v
echo "[3/4] Image source validation"
bash "$ROOT/image/validate.sh"
echo "[4/4] Live-build staging"
NEXUS_PREPARE_ONLY=1 bash "$ROOT/image/build.sh"
echo "Nexus preflight passed"

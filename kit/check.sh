#!/usr/bin/env bash
# The mechanical gate. Green or red; nothing in between.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== lint: forbidden constructs in src/"
python kit/lint_forbidden.py src/ximenes

echo "== lint: numeric literals in src/"
python kit/lint_numbers.py src/ximenes

echo "== lint: postcutoff must never be committed"
if git ls-files --error-unmatch data/postcutoff/ 2>/dev/null | grep -v '\.gitkeep$' | grep -q .; then
  echo "RED: files under data/postcutoff/ are tracked"; exit 1
fi

echo "== ruff"
ruff check src tests kit

echo "== pytest"
pytest -q

echo "== kit: GREEN"

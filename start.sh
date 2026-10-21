#!/usr/bin/env bash
# Start a Claude Code session on the next brief.
#   ./start.sh            next brief not listed in briefs/DONE
#   ./start.sh 001        a specific brief
#   ./start.sh 001 --permission-mode auto   extra args go to claude
set -euo pipefail
cd "$(dirname "$0")"

[ -f data/cryptonite/cryptonite-test.jsonl ] || { echo "run ./setup.sh first"; exit 1; }
command -v claude >/dev/null 2>&1 || { echo "claude not on PATH"; exit 1; }

if [[ "${1:-}" =~ ^[0-9]{3}$ ]]; then
  num="$1"; shift
else
  touch briefs/DONE
  num=""
  for f in briefs/[0-9][0-9][0-9]-*.md; do
    n=$(basename "$f" | cut -c1-3)
    grep -qx "$n" briefs/DONE || { num="$n"; break; }
  done
  [ -n "$num" ] || { echo "every brief in briefs/ is listed in briefs/DONE"; exit 0; }
fi

brief=$(ls briefs/"$num"-*.md 2>/dev/null | head -1)
[ -n "$brief" ] || { echo "no brief numbered $num"; exit 1; }

prompt=$(sed "s|{BRIEF}|$brief|g; s|{NUM}|$num|g" briefs/PROMPT.md)

# shellcheck disable=SC1091
. .venv/bin/activate
echo "brief $num: $brief"
exec claude -n "ximenes-$num" "$@" "$prompt"

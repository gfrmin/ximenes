#!/usr/bin/env bash
# Start the lead agent in its own clone (no data in it, so it can't read
# data/postcutoff/, and it never shares a working tree with the builder).
#   ./start-lead.sh                                  Claude Code, default model
#   ./start-lead.sh --model claude-fable-5-1         extra args go to claude
#   LEAD_DIR=~/somewhere ./start-lead.sh             a different clone location
set -euo pipefail
cd "$(dirname "$0")"

remote=$(git remote get-url origin)
dir="${LEAD_DIR:-$HOME/git/worktrees/ximenes/lead}"

command -v claude >/dev/null 2>&1 || { echo "claude not on PATH"; exit 1; }

if [ ! -d "$dir/.git" ]; then
  mkdir -p "$(dirname "$dir")"
  git clone "$remote" "$dir"
fi
cd "$dir"
git config user.name "Claude"
git config user.email "noreply@anthropic.com"
git pull --rebase -q
uv sync -q   # for ./kit/check.sh; no data is fetched

prompt=$(cat briefs/LEAD-PROMPT.md)
echo "lead: $dir"
exec claude -n "ximenes-lead" "$@" "$prompt"

#!/usr/bin/env bash
# One-time (idempotent) setup: venv, dependencies, datasets, kit check.
# Re-run any time; it only does what is missing.
set -euo pipefail
cd "$(dirname "$0")"

need() { command -v "$1" >/dev/null 2>&1 || { echo "RED: need '$1' on PATH"; exit 1; }; }
need python3; need git; need curl; need unzip

echo "== venv"
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install -q -e ".[dev]"

echo "== data: Cryptonite (Efrat et al. 2021, official answer-disjoint split)"
mkdir -p data/.src data/cryptonite
if [ ! -f data/cryptonite/cryptonite-test.jsonl ]; then
  zip=data/.src/cryptonite-official-split.zip
  if [ ! -f "$zip" ]; then
    curl -fsSL -o "$zip" \
      "https://github.com/aviaefrat/cryptonite/raw/main/data/cryptonite-official-split.zip" \
    || { echo "   direct download refused; cloning the repo instead";
         rm -f "$zip";
         git clone -q --depth 1 https://github.com/aviaefrat/cryptonite data/.src/cryptonite;
         cp data/.src/cryptonite/data/cryptonite-official-split.zip "$zip"; }
  fi
  unzip -q -o "$zip" -d data/cryptonite
fi
(cd data/cryptonite && sha256sum -c --quiet SPLITS.sha256) \
  && echo "   splits match data/cryptonite/SPLITS.sha256" \
  || { echo "RED: Cryptonite files do not match the frozen hashes"; exit 1; }

echo "== data: Wordplay (mdda/cryptic-wordplay, prebuilt teacow sample)"
if [ ! -f data/wordplay/sample_teacow_val.jsonl ]; then
  [ -d data/.src/cryptic-wordplay ] || \
    git clone -q --depth 1 https://github.com/mdda/cryptic-wordplay data/.src/cryptic-wordplay
  mkdir -p data/wordplay
  cp data/.src/cryptic-wordplay/prebuilt/* data/wordplay/
fi
echo "   $(wc -l < data/wordplay/sample_teacow_train.jsonl) train / $(wc -l < data/wordplay/sample_teacow_val.jsonl) val explanations"

echo "== postcutoff"
mkdir -p data/postcutoff
n=$(find data/postcutoff -type f ! -name .gitkeep | wc -l)
[ "$n" -gt 0 ] && echo "   $n file(s) present (private, never committed)" \
               || echo "   empty — fine for briefs 000–003; add dated post-cutoff clues when you have them"

echo "== kit"
./kit/check.sh | tail -1

echo "== claude"
if command -v claude >/dev/null 2>&1; then
  echo "   $(claude --version 2>/dev/null || echo 'claude found')"
else
  echo "   claude not on PATH — install Claude Code, then run ./start.sh"
fi
[ -n "${ANTHROPIC_API_KEY:-}" ] \
  && echo "   ANTHROPIC_API_KEY set: the builder can run the real proposer" \
  || echo "   ANTHROPIC_API_KEY unset: the builder will build against the stub backend"

echo
echo "Ready. Next: ./start.sh"

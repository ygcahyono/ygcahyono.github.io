#!/bin/bash
set -euo pipefail
cd "/Users/yogi/Documents/Code Dont Change/Code/ygcahyono.github.io"
"/Users/yogi/miniconda3/bin/python3" scripts/build_journal_stats.py
# Stage only the artifacts we own.
git add _data/journal_stats.json dashboard/index.html 2>/dev/null || true
if ! git diff --cached --quiet -- _data/journal_stats.json dashboard/index.html; then
  git commit -m "chore: refresh journal stats" -- _data/journal_stats.json dashboard/index.html
  git push
  echo "Pushed updated stats."
else
  echo "No changes to push."
fi

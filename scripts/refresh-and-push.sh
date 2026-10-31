#!/bin/bash
set -euo pipefail
cd "/Users/yogi/Projects/ygcahyono.github.io"
"/Users/yogi/miniconda3/bin/python3" scripts/build_journal_stats.py
# Folder-activity tiles: a failure here only staleness-flags that tile.
"/Users/yogi/miniconda3/bin/python3" scripts/build_folder_activity.py servecoach "/Users/yogi/Projects/servecoach" || echo "servecoach refresh failed" >&2
# Stage only the artifacts we own.
git add _data/journal_stats.json dashboard/journal dashboard/servecoach 2>/dev/null || true
if ! git diff --cached --quiet -- _data/journal_stats.json dashboard/journal dashboard/servecoach; then
  git commit -m "chore: refresh dashboard stats" -- _data/journal_stats.json dashboard/journal dashboard/servecoach
  git push
  echo "Pushed updated stats."
else
  echo "No changes to push."
fi

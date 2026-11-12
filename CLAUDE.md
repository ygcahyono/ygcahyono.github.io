# CLAUDE.md

Personal Jupyter Book (MyST) site, deployed to GitHub Pages at https://ygtc.me
on every push to `main` (`.github/workflows/deploy.yml`).

## Private project hub — `/dashboard/`

Read `docs/dashboard.md` §0 before touching anything under `dashboard/`.

- `dashboard/index.html` — hand-written hub; renders one tile per entry in
  `dashboard/projects.json`. Each tile can show stats from a per-project
  `summary.json` (`{"as_of": "YYYY-MM-DD", "stats": [{label, value}]}`).
- Tiles are grouped under headings by each entry's `group`: **Inner Work**
  (self-development) and **Revenue** (money-making).
- To add a project: append to `projects.json`, add `dashboard/<id>/` (or use an
  external `https://` href), optionally emit `dashboard/<id>/summary.json`.
- CI copies `dashboard/` verbatim — MyST never renders it (it strips `<script>`).
- Everything deployed is publicly readable. Only aggregates, never raw text.

### Projects

| id | Page | Data source | Refresh |
|---|---|---|---|
| journal | `dashboard/journal/` (generated) | `~/Documents/life-love-distraction/100 Daily/*.md` (Obsidian vault) via `scripts/build_journal_stats.py` | launchd `online.ygtc.journal-stats`, daily 23:30 → `scripts/refresh-and-push.sh` |
| servecoach | external → private GitHub repo | `../servecoach` git activity via `scripts/build_folder_activity.py` → `dashboard/servecoach/summary.json` | same launchd job |

To add another code-folder tile: add a `build_folder_activity.py <id> <path>`
line and the `dashboard/<id>` path in **both** `scripts/install-launchd.sh`
(runner template) and `scripts/refresh-and-push.sh`.

Journal gotchas: `100 Daily` is iCloud-synced and must stay "Keep Downloaded"
(macOS evicts unpinned files within minutes; launchd can't fetch them and the
script aborts or stalls). Check: `xattr "<folder>"` lists
`com.apple.fileprovider.pinned` and `find "<folder>" -flags +dataless` prints
nothing. Only `YYYY-MM-DD.md` files count; ratings exist only
from 2026-03 on (older entries show as "no rating" in the heatmap);
`/bin/bash` needs Full Disk Access; logs in `~/Library/Logs/ygtc-journal-stats/`.
Never hand-edit `dashboard/journal/*` — rerun the script. Run the privacy grep
in `docs/dashboard.md` §5 before pushing preprocessor changes.

#!/usr/bin/env python3
"""
Emit a hub tile summary for a local git project folder.

Usage: build_folder_activity.py <project-id> <folder>
Output: dashboard/<project-id>/summary.json  (tile schema, see docs/dashboard.md §0)

"Last change" = the newest of the last commit and any uncommitted edits.
Raw file mtimes alone are unreliable (a re-clone or sync touches every file),
so clean files are dated by git, and only dirty/untracked files by mtime.

ONLY dates and counts leave the folder — no file names, no commit messages.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def git(folder: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(folder), *args],
        check=True, capture_output=True, text=True,
    ).stdout


def build_summary(folder: Path) -> dict:
    last_commit = datetime.fromtimestamp(int(git(folder, "log", "-1", "--format=%ct").strip()))
    since = (date.today() - timedelta(days=29)).isoformat()
    commits_30d = len(git(folder, "log", f"--since={since} 00:00", "--format=%h").split())

    # -z: NUL-separated, paths are verbatim. Each record is "XY path"; renames
    # carry an extra NUL-separated source path, which we skip.
    dirty: list[Path] = []
    records = iter(git(folder, "status", "--porcelain", "-z").split("\0"))
    for rec in records:
        if not rec:
            continue
        if rec[0] in "RC":
            next(records, None)
        p = folder / rec[3:]
        if p.exists():
            dirty.append(p)

    latest = last_commit
    for p in dirty:
        files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
        for f in files:
            latest = max(latest, datetime.fromtimestamp(f.stat().st_mtime))

    return {
        "as_of": latest.date().isoformat(),
        "stats": [
            {"label": "Last change", "value": latest.strftime("%-d %b %H:%M")},
            {"label": "Commits 30d", "value": str(commits_30d)},
            {"label": "Uncommitted", "value": str(len(dirty))},
        ],
    }


def main() -> int:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    project_id, folder = sys.argv[1], Path(sys.argv[2]).expanduser()
    if not (folder / ".git").exists():
        sys.exit(f"Not a git repo: {folder}")

    out = REPO_ROOT / "dashboard" / project_id / "summary.json"
    content = json.dumps(build_summary(folder), indent=2) + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.read_text() == content:
        print(f"No change ({project_id})")
    else:
        out.write_text(content)
        print(f"Updated ({project_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

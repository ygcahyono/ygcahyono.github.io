# Private Daily-Performance Dashboard

> Lightweight feature documentation. MVP-level — covers the why, the how,
> the trade-offs, and how to operate it.

**Status:** shipped — `https://ygtc.online/dashboard/`
**Owner:** @ygcahyono
**Last updated:** 2026-04-08

---

## 1. Problem statement

I keep a personal journal as flat markdown in
`~/Documents/Main Folders/Main/Journal .nosync/`. The folder lives outside
this repo (and outside iCloud sync). I want a **private, evolving** page on
my public Jupyter Book site (`ygtc.online`) that shows aggregated progress
— streaks, ratings, calendar heatmap — without ever exposing the raw
journal text.

### Constraints

| # | Constraint | Implication |
|---|---|---|
| C1 | Site is **MyST / Jupyter Book v2**, deployed via GitHub Actions to public GitHub Pages. | No backend, no auth, no private routes. Anything served is potentially world-readable. |
| C2 | Journal lives in a `.nosync` folder on my Mac. | GitHub Actions cannot read it during build. Any preprocessing must run locally. |
| C3 | Only reliably-structured field per entry is `**Rating: X/10**`. Sections are free-form. | Heuristic extraction; tolerate missing fields. |
| C4 | "Private" really means: **aggregate-only data leaves my Mac**, plus an unlisted URL. | Two layers of defense — sanitization at build time, obscurity at serve time. |

---

## 2. Architecture decision record (ADR-0001)

### Decision

Three layers, each owned independently:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1 — Local Mac only                                        │
│                                                                 │
│   Journal .nosync/*.md                                          │
│           │                                                     │
│           ▼                                                     │
│   scripts/build_journal_stats.py    (stdlib-only)               │
│           │                                                     │
│           ├──▶ _data/journal_stats.json   (canonical, audit)    │
│           └──▶ dashboard/index.html       (self-contained page) │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │  git commit + push (idempotent)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2 — GitHub Actions                                        │
│                                                                 │
│   .github/workflows/deploy.yml                                  │
│     · jupyter-book build --html (does NOT touch dashboard/)     │
│     · cp -R dashboard/. _build/html/dashboard/                  │
│     · upload-pages-artifact + deploy-pages                      │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3 — Automation                                            │
│                                                                 │
│   ~/Library/LaunchAgents/online.ygtc.journal-stats.plist        │
│     · runs scripts/refresh-and-push.sh once a day at 23:30      │
│     · regenerates artifacts; commits + pushes only on diff      │
└─────────────────────────────────────────────────────────────────┘
```

### Why this split?

1. **Privacy boundary at the file-system level.** The Python preprocessor is
   the *only* code that reads the journal. Anything downstream of it sees
   only sanitized aggregates. Easy to audit (one ~250-line file).

2. **MyST is not in the loop for the dashboard page.** This was the single
   biggest discovery during implementation — see ADR-0002.

3. **Automation runs where the data lives.** GitHub Actions can't see the
   journal, so the daemon must run on the Mac. macOS `launchd` is the
   native, dependency-free choice.

---

## 3. ADR-0002: Why a standalone HTML file, not a MyST page

### Context

The original plan was to create `dashboard/daily-performance.md` as a MyST
page with embedded `<script>` and `<style>` blocks. This is the
"normal" Jupyter Book way to add a custom page.

### What we discovered

MyST's book-theme renders pages from a JSON AST (mdast), not from raw
HTML. When the parser sees inline HTML in markdown, it preserves
**element nodes** (`<div>`, `<span>`, `<canvas>`) but **strips
`<script>` and `<style>` tags** during render. Verified empirically:

```bash
$ jupyter-book build --html
$ grep -c "ygtc-stats-data" _build/html/daily-performance/index.html
0
```

We also explored MyST's `{raw} html` directive. The build emits:

```
⚠️  unknown format for raw content: html
   Treating content as text
```

So `{raw} html` is silently dropped too.

### Options considered

| Option | Pros | Cons |
|---|---|---|
| **A. MyST page with `<script>` (original plan)** | Stays inside MyST conventions | Doesn't work — MyST strips scripts |
| **B. MyST page + external JS/CSS via `<script src=...>`** | Cleaner separation | MyST does not copy arbitrary asset files into the build output. We'd need extra plumbing. |
| **C. MyST page with iframe to a hosted dashboard** | Embeds in nav | Iframe target still has to be hosted somewhere |
| **D. ✅ Standalone HTML file in `dashboard/`, copied verbatim by CI** | Bypasses MyST entirely. Self-contained (data + CSS + JS inlined). Trivially auditable. Survives any future MyST upgrade. | Page doesn't share the site's book-theme styling. Acceptable for a private page. |

### Decision

**Option D.** The dashboard is a single self-contained `dashboard/index.html`.
The deploy workflow copies the `dashboard/` folder into the build output as
its final step, so the file is served at `https://ygtc.online/dashboard/`.

### Trade-offs accepted

- The dashboard does **not** look like the rest of the site. It has its own
  minimal CSS. For a private page only I see, this is fine.
- The dashboard does **not** appear in MyST's search index or sidebar. For
  an explicitly-unlisted page, this is a feature, not a bug.

---

## 4. ADR-0003: Privacy floor on `tag_frequency`

### Context

The preprocessor extracts section headings (e.g. `### Professional`) as
labels for the section-frequency bar chart. Headings are not raw narrative,
so they're allowed by the original spec. But during the privacy grep
(`grep -i "ramadan|interview|salary"`) we found a one-off heading that
contained personal context: `"personal reflections on ramadan"`.

### Decision

Apply a frequency floor: only emit headings that appear **at least twice**
across all entries. One-offs are dropped.

```python
"tag_frequency": [
    {"tag": t, "count": c}
    for t, c in heading_counts.most_common(30)
    if c >= 2
],
```

### Rationale

- Stable categories (e.g. `professional`, `social`) survive the floor and
  are exactly what the chart should show.
- Single-occurrence headings are precisely the ones most likely to leak
  personal context (a name, a place, an event).
- The floor is one line, easy to relax later if I move to a structured
  tag system.

---

## 5. Privacy checklist (must pass before each release)

1. [x] `_data/journal_stats.json` contains no raw sentences, no names, no
       bold-highlighted entities. Only numbers, dates, heading labels.
2. [x] The preprocessor never writes to any path inside the repo except
       `_data/journal_stats.json` and `dashboard/index.html`.
3. [x] The dashboard page is NOT in `myst.yml` `toc`.
4. [x] No other page on the site links to `/dashboard/` (verified via
       `grep -rl dashboard _build/html/` excluding the dashboard folder
       itself).
5. [x] `<meta name="robots" content="noindex,nofollow">` is in the page.
6. [x] Privacy grep returns zero hits:
       `grep -i "ramadan|durian|interview|salary|stress" _data/journal_stats.json dashboard/index.html`

To re-run the checklist after any preprocessor change:

```bash
python3 scripts/build_journal_stats.py
grep -i "ramadan|durian|interview|salary|stress" _data/journal_stats.json dashboard/index.html
# expect: zero matches
```

---

## 6. Operational runbook

### 6.1 Manual refresh

```bash
cd ~/Documents/Code\ Dont\ Change/Code/ygcahyono.github.io
python3 scripts/build_journal_stats.py
git add _data/journal_stats.json dashboard/index.html
git commit -m "chore: refresh journal stats"
git push
```

GitHub Actions takes ~1 minute to redeploy. The live page is then at:

> **https://ygtc.online/dashboard/**

### 6.2 Automated daily refresh

Installed via `bash scripts/install-launchd.sh`. Runs daily at **23:30
local time**. See Section 7 for the full launchd story.

### 6.3 Adding a new metric

The preprocessor is the schema. To add, say, "habit checkboxes":

1. Extend `parse_entry()` in `scripts/build_journal_stats.py` to capture
   the new field.
2. Add it to the `payload` dict in `build_payload()`.
3. Add a new `<canvas>` and a Chart.js block in `DASHBOARD_JS` /
   `PAGE_TEMPLATE` (both inside the same Python file).
4. Run the preprocessor once locally to regenerate `dashboard/index.html`.
5. Commit, push. Done. No MyST or CI changes.

### 6.4 Rolling back

The dashboard is a single committed HTML file. To roll back, `git revert`
the offending commit. The next deploy will replace the live file.

### 6.5 Disabling temporarily

Three options, increasing severity:

1. Comment out the `cp -R dashboard/.` block in
   `.github/workflows/deploy.yml`. Page becomes 404 on next deploy.
2. `bash scripts/install-launchd.sh --uninstall` to stop daily updates
   (data freezes; page still served).
3. `git rm -r dashboard/ && git commit && git push`.

---

## 7. Files overview

| Path | Owner | Committed? | Generated? |
|---|---|---|---|
| `scripts/build_journal_stats.py` | hand-written | ✅ | – |
| `scripts/install-launchd.sh` | hand-written | ✅ | – |
| `scripts/refresh-and-push.sh` | generated by installer | ❌ (gitignored — see note) | by `install-launchd.sh` |
| `scripts/requirements-dev.txt` | hand-written | ✅ | – |
| `_data/journal_stats.json` | generated | ✅ | by `build_journal_stats.py` |
| `dashboard/index.html` | generated | ✅ | by `build_journal_stats.py` |
| `~/Library/LaunchAgents/online.ygtc.journal-stats.plist` | generated | ❌ (outside repo) | by `install-launchd.sh` |
| `.github/workflows/deploy.yml` | hand-written | ✅ | – |
| `docs/dashboard.md` | hand-written | ✅ | – (this file) |

> Note: `refresh-and-push.sh` is currently *not* gitignored. It's small,
> path-dependent, and re-generated by the installer — leaving it untracked
> is the cleanest default. Add `scripts/refresh-and-push.sh` to
> `.gitignore` if you commit it accidentally.

---

## 8. Known issues

### 8.1 macOS Full Disk Access blocks the launchd job

On a fresh install, `launchctl kickstart` fails with:

```
shell-init: error retrieving current directory: getcwd: cannot access parent directories: Operation not permitted
/bin/bash: scripts/refresh-and-push.sh: Operation not permitted
```

**Cause:** macOS TCC (Transparency, Consent and Control) protects
`~/Documents`. launchd-spawned processes inherit a sandbox without
Full Disk Access by default.

**Fix (one-time, manual):**

1. Open **System Settings → Privacy & Security → Full Disk Access**.
2. Click **+** and add `/bin/bash`.
   (You may need to press **⌘⇧G** in the file picker and type `/bin/bash`.)
3. Toggle it on.
4. Re-run `launchctl kickstart -k gui/$(id -u)/online.ygtc.journal-stats`.
5. Confirm: `cat ~/Library/Logs/ygtc-journal-stats/out.log` should show
   either `Updated (...)` or `No changes to push.`.

> Why we can't avoid this: the journal lives in `~/Documents`, and any
> automated reader of it needs FDA. Moving the journal out of Documents
> would also work, but defeats the user's existing setup.

### 8.2 First-run authentication for `git push`

The launchd runner uses whatever git credentials are configured for the
shell user. If you've authenticated with `gh auth login` or have a stored
HTTPS credential, it just works. If not, the first auto-push will fail
silently into `~/Library/Logs/ygtc-journal-stats/err.log`. Fix: run
`gh auth login` once (or set up an SSH remote) and re-trigger.

### 8.3 Chart.js loaded from CDN

The page loads Chart.js from `cdn.jsdelivr.net`. If the CDN is
unreachable, the heatmap and KPIs still render (vanilla DOM), but the two
line/bar charts will be empty. Acceptable for a private dashboard;
self-host the file if this becomes a problem.

---

## 9. Out of scope (deliberate)

- Password gating. Can be added later as a client-side prompt if the URL
  ever leaks.
- Rating-vs-activity correlation. Schema is too thin (n=16 entries) to be
  meaningful yet.
- Backfilling richer metrics (mood tags, habit checkboxes). Requires
  evolving the journal template first; the dashboard is built to accept
  new fields without redesign (see Section 6.3).
- Sharing styles with the MyST book-theme. The dashboard intentionally
  has its own minimal CSS — fewer moving parts on a privacy-sensitive
  page.

---

## 10. Verification log (initial release, 2026-04-08)

| Check | Command | Result |
|---|---|---|
| Preprocessor parses 16 entries | `python3 scripts/build_journal_stats.py` | `Updated (16 entries)` |
| JSON has no PII tokens | `grep -i "ramadan\|durian\|interview\|salary\|stress" _data/journal_stats.json` | 0 matches |
| HTML has no PII tokens | `grep -i "..." dashboard/index.html` | 0 matches |
| MyST build succeeds | `jupyter-book build --html` | 6 pages, no warnings |
| Dashboard NOT in built sidebar | `grep -rl dashboard _build/html/ \| grep -v dashboard/` | 0 matches |
| GitHub Actions deploy | `gh run watch` | ✅ success in ~50s |
| Live page returns 200 | `curl -sI https://ygtc.online/dashboard/` | `HTTP/2 200` |
| Live page has data + KPIs | `curl -s https://ygtc.online/dashboard/ \| grep -c ygtc-stats-data` | 6 matches |

---

## 11. Changelog

- **2026-04-08** — Initial release. Streaks, calendar heatmap, rating
  timeline, section frequency. Daily launchd refresh.

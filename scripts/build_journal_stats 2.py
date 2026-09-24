#!/usr/bin/env python3
"""
Preprocess private journal entries into a sanitized aggregate dataset and
regenerate the self-contained public dashboard page.

Inputs:  /Users/yogi/Documents/Main Folders/Main/Journal .nosync/*.md
Outputs (both safe to commit):
  - _data/journal_stats.json             (canonical aggregate, inspectable)
  - dashboard/daily-performance.md       (MyST page with data + CSS + JS inlined)

ONLY numeric aggregates, dates, and heading labels leave the journal folder.
No raw body text, no names, no narrative sentences.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

JOURNAL_DIR = Path("/Users/yogi/Documents/Main Folders/Main/Journal .nosync")
REPO_ROOT = Path(__file__).resolve().parent.parent
JSON_OUTPUT = REPO_ROOT / "_data" / "journal_stats.json"
PAGE_OUTPUT = REPO_ROOT / "dashboard" / "index.html"

FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
RATING_RE = re.compile(r"Rating:\s*(\d+)\s*/\s*10", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$", re.MULTILINE)
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


# ---------- extraction ----------------------------------------------------


def normalize_heading(text: str) -> str:
    text = BOLD_RE.sub(r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    text = re.sub(r":\s*\d.*$", "", text)
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def parse_entry(path: Path) -> dict[str, Any] | None:
    m = FILENAME_RE.match(path.name)
    if not m:
        return None
    entry_date = m.group(1)
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    rating_match = RATING_RE.search(text)
    rating = int(rating_match.group(1)) if rating_match else None

    word_count = len(re.findall(r"\b\w+\b", text))

    headings: list[str] = []
    for level, raw in HEADING_RE.findall(text):
        if len(level) == 1:
            continue
        norm = normalize_heading(raw)
        if re.search(r"\d{4}", norm):
            continue
        if norm:
            headings.append(norm)

    return {
        "date": entry_date,
        "rating": rating,
        "word_count": word_count,
        "section_headings": headings,
        "has_entry": True,
    }


# ---------- aggregates ----------------------------------------------------


def compute_streaks(dated: dict[str, Any]) -> tuple[int, int]:
    if not dated:
        return 0, 0
    dates_sorted = sorted(dated.keys())
    longest = 0
    current_run = 0
    prev: date | None = None
    for d_str in dates_sorted:
        d = datetime.strptime(d_str, "%Y-%m-%d").date()
        current_run = current_run + 1 if prev is not None and (d - prev).days == 1 else 1
        longest = max(longest, current_run)
        prev = d

    last = datetime.strptime(dates_sorted[-1], "%Y-%m-%d").date()
    today = date.today()
    if (today - last).days > 1:
        current = 0
    else:
        current = 1
        cursor = last
        while True:
            prev_day = cursor - timedelta(days=1)
            if prev_day.strftime("%Y-%m-%d") in dated:
                current += 1
                cursor = prev_day
            else:
                break
    return current, longest


def consistency_pct(dated: dict[str, Any], days: int) -> float:
    today = date.today()
    start = today - timedelta(days=days - 1)
    hits = sum(
        1 for i in range(days)
        if (start + timedelta(days=i)).strftime("%Y-%m-%d") in dated
    )
    return round(100 * hits / days, 1)


def rolling_average(series: list[tuple[str, float | None]], window: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, (d, _) in enumerate(series):
        lo = max(0, i - window + 1)
        vals = [v for _, v in series[lo : i + 1] if v is not None]
        avg = round(sum(vals) / len(vals), 2) if vals else None
        out.append({"date": d, "avg": avg})
    return out


def build_calendar(dated: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if not dated:
        return []
    dates_sorted = sorted(dated.keys())
    start = datetime.strptime(dates_sorted[0], "%Y-%m-%d").date()
    end = max(
        date.today(),
        datetime.strptime(dates_sorted[-1], "%Y-%m-%d").date(),
    )
    out = []
    cursor = start
    while cursor <= end:
        key = cursor.strftime("%Y-%m-%d")
        e = dated.get(key)
        out.append({
            "date": key,
            "rating": e["rating"] if e else None,
            "word_count": e["word_count"] if e else None,
        })
        cursor += timedelta(days=1)
    return out


def build_payload() -> dict[str, Any] | None:
    if not JOURNAL_DIR.exists():
        print(f"Journal directory not found: {JOURNAL_DIR}", file=sys.stderr)
        return None

    entries: dict[str, dict[str, Any]] = {}
    heading_counts: Counter[str] = Counter()
    for path in sorted(JOURNAL_DIR.glob("*.md")):
        parsed = parse_entry(path)
        if parsed is None:
            continue
        entries[parsed["date"]] = parsed
        heading_counts.update(parsed["section_headings"])

    calendar = build_calendar(entries)
    rating_series: list[tuple[str, float | None]] = [
        (row["date"], float(row["rating"]) if row["rating"] is not None else None)
        for row in calendar
    ]
    rating_rolling_7d = rolling_average(rating_series, 7)
    current_streak, longest_streak = compute_streaks(entries)
    last_30 = [r for _, r in rating_series[-30:] if r is not None]
    avg_rating_30 = round(sum(last_30) / len(last_30), 2) if last_30 else None

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_entries": len(entries),
        "date_range": {
            "start": calendar[0]["date"] if calendar else None,
            "end": calendar[-1]["date"] if calendar else None,
        },
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "consistency": {
            "last_30": consistency_pct(entries, 30),
            "last_90": consistency_pct(entries, 90),
            "last_365": consistency_pct(entries, 365),
        },
        "avg_rating_30d": avg_rating_30,
        "rating_rolling_7d": rating_rolling_7d,
        "calendar": calendar,
        # Privacy floor: only emit headings seen at least twice. One-offs are
        # likely to carry personal context (names, events, places) — safer to drop.
        "tag_frequency": [
            {"tag": t, "count": c}
            for t, c in heading_counts.most_common(30)
            if c >= 2
        ],
    }


# ---------- output --------------------------------------------------------


DASHBOARD_CSS = """
#ygtc-dashboard{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;max-width:960px;margin:0 auto}
#ygtc-dashboard .ygtc-dash-sub{color:#6a737d;font-size:.9rem;margin-top:0}
#ygtc-dashboard .ygtc-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.75rem;margin:1.5rem 0 2rem}
#ygtc-dashboard .ygtc-card{background:rgba(127,127,127,.08);border:1px solid rgba(127,127,127,.2);border-radius:10px;padding:.9rem 1rem}
#ygtc-dashboard .ygtc-card-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:#6a737d}
#ygtc-dashboard .ygtc-card-value{font-size:1.9rem;font-weight:700;line-height:1.1;margin-top:.15rem}
#ygtc-dashboard .ygtc-card-unit{font-size:.75rem;color:#6a737d}
#ygtc-dashboard h2{margin-top:2rem}
#ygtc-dashboard .ygtc-section-sub{color:#6a737d;font-size:.85rem;margin-top:0}
#ygtc-dashboard .ygtc-heatmap{display:grid;grid-auto-flow:column;grid-template-rows:repeat(7,14px);grid-auto-columns:14px;gap:3px;overflow-x:auto;padding:4px 0}
#ygtc-dashboard .ygtc-heatmap-cell{width:14px;height:14px;border-radius:3px;background:rgba(127,127,127,.15)}
#ygtc-dashboard .ygtc-heatmap-cell[data-level="1"]{background:#c6e48b}
#ygtc-dashboard .ygtc-heatmap-cell[data-level="2"]{background:#b6de7e}
#ygtc-dashboard .ygtc-heatmap-cell[data-level="3"]{background:#a3d570}
#ygtc-dashboard .ygtc-heatmap-cell[data-level="4"]{background:#89c668}
#ygtc-dashboard .ygtc-heatmap-cell[data-level="5"]{background:#7bc160}
#ygtc-dashboard .ygtc-heatmap-cell[data-level="6"]{background:#5bb84a}
#ygtc-dashboard .ygtc-heatmap-cell[data-level="7"]{background:#47a93b}
#ygtc-dashboard .ygtc-heatmap-cell[data-level="8"]{background:#2f9028}
#ygtc-dashboard .ygtc-heatmap-cell[data-level="9"]{background:#22711a}
#ygtc-dashboard .ygtc-heatmap-cell[data-level="10"]{background:#155212}
#ygtc-dashboard .ygtc-legend{display:flex;align-items:center;gap:4px;font-size:.75rem;color:#6a737d;margin-top:.6rem}
#ygtc-dashboard .ygtc-legend-cell{display:inline-block;width:12px;height:12px;border-radius:2px;background:rgba(127,127,127,.15)}
#ygtc-dashboard .ygtc-legend-cell[data-level="2"]{background:#c6e48b}
#ygtc-dashboard .ygtc-legend-cell[data-level="4"]{background:#89c668}
#ygtc-dashboard .ygtc-legend-cell[data-level="6"]{background:#5bb84a}
#ygtc-dashboard .ygtc-legend-cell[data-level="8"]{background:#2f9028}
#ygtc-dashboard .ygtc-legend-cell[data-level="10"]{background:#155212}
#ygtc-dashboard .ygtc-chart-wrap{position:relative;height:260px;margin:.5rem 0 1.5rem}
#ygtc-dashboard .ygtc-dash-footer{margin-top:3rem;border-top:1px solid rgba(127,127,127,.2);padding-top:.75rem;color:#6a737d;font-size:.75rem}
""".strip()


DASHBOARD_JS = r"""
(function(){
  function ready(fn){document.readyState==="loading"?document.addEventListener("DOMContentLoaded",fn):fn()}
  function $(id){return document.getElementById(id)}
  function setText(id,v){var el=$(id);if(el)el.textContent=v==null?"–":String(v)}
  function ratingLevel(r){if(r==null)return 0;if(r<1)return 0;if(r>10)return 10;return Math.round(r)}
  function loadChartJs(cb){
    if(typeof Chart!=="undefined"){cb();return}
    var s=document.createElement("script");
    s.src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js";
    s.onload=cb;s.onerror=function(){console.warn("Chart.js failed to load");cb()};
    document.head.appendChild(s);
  }
  function render(data){
    setText("kpi-current-streak",data.current_streak);
    setText("kpi-longest-streak",data.longest_streak);
    setText("kpi-consistency-30",data.consistency&&data.consistency.last_30!=null?data.consistency.last_30.toFixed(1):"–");
    setText("kpi-avg-rating",data.avg_rating_30d==null?"–":data.avg_rating_30d);
    setText("kpi-total",data.total_entries);
    setText("ygtc-generated-at",(data.generated_at||"").replace("T"," ").replace("Z"," UTC"));

    var host=$("ygtc-heatmap");
    if(host&&data.calendar&&data.calendar.length){
      host.innerHTML="";
      var first=new Date(data.calendar[0].date+"T00:00:00");
      for(var p=0;p<first.getDay();p++){
        var pad=document.createElement("div");
        pad.className="ygtc-heatmap-cell";pad.style.visibility="hidden";host.appendChild(pad);
      }
      data.calendar.forEach(function(row){
        var cell=document.createElement("div");
        cell.className="ygtc-heatmap-cell";
        cell.setAttribute("data-level",String(ratingLevel(row.rating)));
        cell.title=row.date+(row.rating==null?" — no entry":" — rating "+row.rating+"/10");
        host.appendChild(cell);
      });
    }

    if(typeof Chart==="undefined")return;

    var rc=$("ygtc-rating-chart");
    if(rc){
      var labels=data.calendar.map(function(r){return r.date});
      var daily=data.calendar.map(function(r){return r.rating});
      var rollingMap={};
      (data.rating_rolling_7d||[]).forEach(function(r){rollingMap[r.date]=r.avg});
      var rolling=labels.map(function(d){return rollingMap[d]==null?null:rollingMap[d]});
      new Chart(rc.getContext("2d"),{
        type:"line",
        data:{labels:labels,datasets:[
          {label:"Daily rating",data:daily,borderColor:"#6a737d",backgroundColor:"rgba(106,115,125,0.15)",spanGaps:true,tension:.25,pointRadius:2},
          {label:"7-day avg",data:rolling,borderColor:"#2f9028",backgroundColor:"rgba(47,144,40,0.15)",borderWidth:2,tension:.25,pointRadius:0,spanGaps:true}
        ]},
        options:{responsive:true,maintainAspectRatio:false,
          scales:{y:{min:0,max:10,ticks:{stepSize:2}},x:{ticks:{maxTicksLimit:8,autoSkip:true}}},
          plugins:{legend:{position:"bottom"}}}
      });
    }

    var tc=$("ygtc-tags-chart");
    if(tc){
      var tags=(data.tag_frequency||[]).slice(0,12);
      new Chart(tc.getContext("2d"),{
        type:"bar",
        data:{labels:tags.map(function(t){return t.tag}),datasets:[{label:"Occurrences",data:tags.map(function(t){return t.count}),backgroundColor:"#47a93b"}]},
        options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,
          plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,ticks:{precision:0}}}}
      });
    }
  }
  ready(function(){
    var node=document.getElementById("ygtc-stats-data");
    if(!node){console.warn("ygtc stats data missing");return}
    var data;
    try{data=JSON.parse(node.textContent)}catch(e){console.error("ygtc parse error",e);return}
    loadChartJs(function(){render(data)});
  });
})();
""".strip()


PAGE_TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<meta name="robots" content="noindex,nofollow" />
<title>Daily Performance — Private</title>
<!-- Regenerated by scripts/build_journal_stats.py. Do not edit by hand. -->
<style>
body{margin:0;padding:2rem 1rem;background:#fff;color:#24292e;line-height:1.5}
__CSS__
</style>
</head>
<body>
<div id="ygtc-dashboard">
  <h1>Daily Performance</h1>
  <p class="ygtc-dash-sub">Private dashboard — aggregates only. Last refreshed <span id="ygtc-generated-at">…</span>.</p>

  <div class="ygtc-kpis">
    <div class="ygtc-card"><div class="ygtc-card-label">Current streak</div><div class="ygtc-card-value" id="kpi-current-streak">–</div><div class="ygtc-card-unit">days</div></div>
    <div class="ygtc-card"><div class="ygtc-card-label">Longest streak</div><div class="ygtc-card-value" id="kpi-longest-streak">–</div><div class="ygtc-card-unit">days</div></div>
    <div class="ygtc-card"><div class="ygtc-card-label">Consistency 30d</div><div class="ygtc-card-value" id="kpi-consistency-30">–</div><div class="ygtc-card-unit">%</div></div>
    <div class="ygtc-card"><div class="ygtc-card-label">Avg rating 30d</div><div class="ygtc-card-value" id="kpi-avg-rating">–</div><div class="ygtc-card-unit">/ 10</div></div>
    <div class="ygtc-card"><div class="ygtc-card-label">Total entries</div><div class="ygtc-card-value" id="kpi-total">–</div><div class="ygtc-card-unit">logged</div></div>
  </div>

  <h2>Calendar heatmap</h2>
  <p class="ygtc-section-sub">Each cell is a day. Color intensity = daily rating. Gray = no entry.</p>
  <div id="ygtc-heatmap" class="ygtc-heatmap"></div>
  <div class="ygtc-legend">
    <span>Lower</span>
    <span class="ygtc-legend-cell" data-level="0"></span>
    <span class="ygtc-legend-cell" data-level="2"></span>
    <span class="ygtc-legend-cell" data-level="4"></span>
    <span class="ygtc-legend-cell" data-level="6"></span>
    <span class="ygtc-legend-cell" data-level="8"></span>
    <span class="ygtc-legend-cell" data-level="10"></span>
    <span>Higher</span>
  </div>

  <h2>Rating timeline</h2>
  <p class="ygtc-section-sub">Daily rating with 7-day rolling average.</p>
  <div class="ygtc-chart-wrap"><canvas id="ygtc-rating-chart"></canvas></div>

  <h2>Section frequency</h2>
  <p class="ygtc-section-sub">Most common journal sections.</p>
  <div class="ygtc-chart-wrap"><canvas id="ygtc-tags-chart"></canvas></div>

  <p class="ygtc-dash-footer">Unlisted. Do not share. Generated locally from <code>Journal .nosync</code>.</p>
</div>

<script id="ygtc-stats-data" type="application/json">
__DATA__
</script>
<script>
__JS__
</script>
</body>
</html>
"""


def render_page(payload: dict[str, Any]) -> str:
    # Escape </script> in JSON to avoid breaking out of the script tag.
    data_str = json.dumps(payload, indent=2).replace("</", "<\\/")
    page = PAGE_TEMPLATE.replace("__CSS__", DASHBOARD_CSS)
    page = page.replace("__DATA__", data_str)
    page = page.replace("__JS__", DASHBOARD_JS)
    return page


def _strip_ts(b: bytes) -> bytes:
    return re.sub(rb'"generated_at":\s*"[^"]*",?\s*\n?', b"", b)


def write_if_changed(path: Path, content: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and _strip_ts(path.read_bytes()) == _strip_ts(content):
        return False
    path.write_bytes(content)
    return True


def main() -> int:
    payload = build_payload()
    if payload is None:
        return 1

    json_bytes = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    page_bytes = render_page(payload).encode("utf-8")

    json_changed = write_if_changed(JSON_OUTPUT, json_bytes)
    page_changed = write_if_changed(PAGE_OUTPUT, page_bytes)

    n = payload["total_entries"]
    if json_changed or page_changed:
        print(f"Updated ({n} entries): "
              f"{'json' if json_changed else ''}{' ' if json_changed and page_changed else ''}"
              f"{'page' if page_changed else ''}")
    else:
        print(f"No change ({n} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

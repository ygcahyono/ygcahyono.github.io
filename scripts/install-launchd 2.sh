#!/bin/bash
# Install (or reinstall) the launchd agent that refreshes the private journal
# dashboard once per day. Idempotent: safe to re-run.
#
# Usage: bash scripts/install-launchd.sh [--uninstall]

set -euo pipefail

LABEL="online.ygtc.journal-stats"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="$(command -v python3)"
RUNNER="$REPO_DIR/scripts/refresh-and-push.sh"
LOG_DIR="$HOME/Library/Logs/ygtc-journal-stats"

if [[ "${1:-}" == "--uninstall" ]]; then
  launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Uninstalled $LABEL"
  exit 0
fi

mkdir -p "$LOG_DIR" "$(dirname "$PLIST")"

# The runner script: regenerate stats, commit + push only on real changes.
cat > "$RUNNER" <<RUNNER_EOF
#!/bin/bash
set -euo pipefail
cd "$REPO_DIR"
"$PYTHON_BIN" scripts/build_journal_stats.py
# Stage only the artifacts we own.
git add _data/journal_stats.json dashboard/index.html 2>/dev/null || true
if ! git diff --cached --quiet -- _data/journal_stats.json dashboard/index.html; then
  git commit -m "chore: refresh journal stats" -- _data/journal_stats.json dashboard/index.html
  git push
  echo "Pushed updated stats."
else
  echo "No changes to push."
fi
RUNNER_EOF
chmod +x "$RUNNER"

# Daily run at 23:30 local time. Adjust StartCalendarInterval to taste.
cat > "$PLIST" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${RUNNER}</string>
  </array>
  <key>WorkingDirectory</key><string>${REPO_DIR}</string>
  <key>StandardOutPath</key><string>${LOG_DIR}/out.log</string>
  <key>StandardErrorPath</key><string>${LOG_DIR}/err.log</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>23</integer>
    <key>Minute</key><integer>30</integer>
  </dict>
  <key>RunAtLoad</key><false/>
</dict>
</plist>
PLIST_EOF

# Reload the agent.
launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

echo "Installed: $PLIST"
echo "Runner   : $RUNNER"
echo "Logs     : $LOG_DIR"
echo
echo "Force a test run:"
echo "  launchctl kickstart -k gui/\$(id -u)/${LABEL}"
echo
echo "Check status:"
echo "  launchctl list | grep ygtc"

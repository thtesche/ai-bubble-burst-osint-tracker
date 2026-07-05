#!/bin/bash

# AI-Bubble-OSINT-Tracker - Agent Orchestration Script
# Version: 0.1.0

set -e

# --- Configuration ---
DATE=$(date +"%Y-%m-%d")
REPORT_DIR="../web/src/content/reports"
PROMPT_FILE="../prompts/agent_prompt.md"
LOG_FILE="agent_run.log"

echo "[$(date)] Starting AI-Bubble-OSINT-Tracker Agent..." | tee -a "$LOG_FILE"

# 1. Ensure the directory exists
mkdir -p "$REPORT_DIR"

# 2. Check if the prompt exists
if [ ! -f "$PROMPT_FILE" ]; then
    echo "[$(date)] ERROR: Prompt file not found at $PROMPT_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 3. Agent call via pi.dev
# We read the prompt from the file and pass it to pi.dev in print mode (-p).
echo "[$(date)] Running pi.dev agent with system prompt..." | tee -a "$LOG_FILE"

# We use cat to read the content of the prompt file and pass it as an argument.
# Note: For very large prompts, one might switch to stdin, 
# but for pi.dev -p, passing as a string is common.
pi.dev -p "$(cat "$PROMPT_FILE")" > "$REPORT_DIR/report-$DATE.md"

if [ $? -eq 0 ]; then
    echo "[$(date)] Analysis successful: report-$DATE.md generated." | tee -a "$LOG_FILE"
else
    echo "[$(date)] ERROR: Agent execution failed." | tee -a "$LOG_FILE"
    exit 1
fi

# 4. Git Automation (Deployment Trigger)
echo "[$(date)] Committing changes to GitHub..." | tee -a "$LOG_FILE"

# We assume the script is located in the 'scripts/' folder
cd ..

# Ensure we are in a git repository
if [ ! -d ".git" ]; then
    echo "[$(date)] WARNING: Not a git repository. Skipping commit/push." | tee -a "$LOG_FILE"
else
    git add web/src/content/reports/
    # Only commit if there are changes
    if git diff --cached --quiet; then
        echo "[$(date)] No changes to commit." | tee -a "$LOG_FILE"
    else
        git commit -m "🤖 Automated Report: $DATE"
        git push origin main
        echo "[$(date)] Deployment triggered successfully." | tee -a "$LOG_FILE"
    fi
fi

echo "[$(date)] Process finished." | tee -a "$LOG_FILE"

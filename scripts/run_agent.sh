#!/bin/bash

# AI-Bubble-OSINT-Tracker - Agent Orchestration Script
# Version: 0.1.0

set -e

# --- Konfiguration ---
DATE=$(date +"%Y-%m-%d")
REPORT_DIR="../web/src/content/reports"
PROMPT_FILE="../prompts/agent_prompt.md"
LOG_FILE="agent_run.log"

echo "[$(date)] Starting AI-Bubble-OSINT-Tracker Agent..." | tee -a "$LOG_FILE"

# 1. Sicherstellen, dass das Verzeichnis existiert
mkdir -p "$REPORT_DIR"

# 2. Prüfen, ob der Prompt existiert
if [ ! -f "$PROMPT_FILE" ]; then
    echo "[$(date)] ERROR: Prompt file not found at $PROMPT_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 3. Agenten-Aufruf via pi.dev
# Wir lesen den Prompt aus der Datei und übergeben ihn an pi.dev im Print-Modus (-p).
echo "[$(date)] Running pi.dev agent with system prompt..." | tee -a "$LOG_FILE"

# Wir nutzen cat, um den Inhalt der Prompt-Datei zu lesen und übergeben ihn als Argument.
# Hinweis: Bei sehr großen Prompts könnte man hier auf stdin umsteigen, 
# aber für pi.dev -p ist die Übergabe als String üblich.
pi.dev -p "$(cat "$PROMPT_FILE")" > "$REPORT_DIR/report-$DATE.md"

if [ $? -eq 0 ]; then
    echo "[$(date)] Analysis successful: report-$DATE.md generated." | tee -a "$LOG_FILE"
else
    echo "[$(date)] ERROR: Agent execution failed." | tee -a "$LOG_FILE"
    exit 1
fi

# 4. Git Automatisierung (Deployment Trigger)
echo "[$(date)] Committing changes to GitHub..." | tee -a "$LOG_FILE"

# Wir gehen davon aus, dass das Skript im Ordner 'scripts/' liegt
cd ..

# Sicherstellen, dass wir in einem Git-Repo sind
if [ ! -d ".git" ]; then
    echo "[$(date)] WARNING: Not a git repository. Skipping commit/push." | tee -a "$LOG_FILE"
else
    git add web/src/content/reports/
    # Nur committen, wenn es Änderungen gibt
    if git diff --cached --quiet; then
        echo "[$(date)] No changes to commit." | tee -a "$LOG_FILE"
    else
        git commit -m "🤖 Automated Report: $DATE"
        git push origin main
        echo "[$(date)] Deployment triggered successfully." | tee -a "$LOG_FILE"
    fi
fi

echo "[$(date)] Process finished." | tee -a "$LOG_FILE"

#!/bin/bash

# AI Bubble Burst OSINT Tracker - Daily Pipeline Runner
# This script runs the full E2E pipeline using the local virtual environment.

# 1. Configuration
# Use absolute path to ensure reliability in cron
PROJECT_ROOT="/Users/thtesche/VibeCoding/ai-bubble-burst-osint-tracker"
VENV_PATH="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs/runs"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/pipeline_$TIMESTAMP.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "====================================================" | tee -a "$LOG_FILE"
echo "Starting AI Bubble Burst Pipeline: $TIMESTAMP" | tee -a "$LOG_FILE"
echo "====================================================" | tee -a "$LOG_FILE"

# 2. Environment Setup
if [ ! -d "$VENV_PATH" ]; then
    echo "[ERROR] Virtual environment not found at $VENV_PATH" | tee -a "$LOG_FILE"
    exit 1
fi

# Activate venv
source "$VENV_PATH/bin/activate" || { echo "[ERROR] Failed to activate venv"; exit 1; }

# 3. Execution
echo "[*] Running E2E Pipeline script..." | tee -a "$LOG_FILE"

# Use PYTHONPATH to ensure src is discoverable
export PYTHONPATH="$PROJECT_ROOT"

python3 "$PROJECT_ROOT/src/core/test_full_pipeline_live.py" 2>&1 | tee -a "$LOG_FILE"

# 4. Cleanup & Result
EXIT_CODE=$?

echo "----------------------------------------------------" | tee -a "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ]; then
    echo "Pipeline completed successfully." | tee -a "$LOG_FILE"
else
    echo "Pipeline failed with exit code $EXIT_CODE." | tee -a "$LOG_FILE"
fi
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "====================================================" | tee -a "$LOG_FILE"

deactivate
exit $EXIT_CODE

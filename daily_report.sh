#!/bin/bash

# AI Bubble Burst OSINT Tracker - Daily Pipeline Runner
# 1. Configuration & Root Detection
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT=$(pwd)
fi

# --- CRITICAL FIX: Clear PYTHONPATH to prevent Hermes-Agent leakage ---
export PYTHONPATH=""
# ----------------------------------------------------------------------

VENV_PATH="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs/runs"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/pipeline_$TIMESTAMP.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "====================================================" | tee -a "$LOG_FILE"
echo "Starting AI Bubble Burst Pipeline: $TIMESTAMP" | tee -a "$LOG_FILE"
echo "Project Root: $PROJECT_ROOT" | tee -a "$LOG_FILE"
echo "Cleaned PYTHONPATH: $PYTHONPATH" | tee -a "$LOG_FILE"
echo "====================================================" | tee -a "$LOG_FILE"

# 2. Environment Check
if [ ! -d "$VENV_PATH" ]; then
    echo "[ERROR] Virtual environment not found at $VENV_PATH" | tee -a "$LOG_FILE"
    exit 1
fi

# 3. Execution
echo "[*] Running E2E Pipeline script..." | tee -a "$LOG_FILE"

# Use the absolute path to the venv python interpreter
PYTHON_EXE="$VENV_PATH/bin/python3"

# Now set PYTHONPATH to ONLY include the project root for module discovery
export PYTHONPATH="$PROJECT_ROOT"

# Execute and capture output
"$PYTHON_EXE" "$PROJECT_ROOT/src/main.py" 2>&1 | tee -a "$LOG_FILE"

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

exit $EXIT_CODE
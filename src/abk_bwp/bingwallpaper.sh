#!/bin/bash

#---------------------------
# Local functions
#---------------------------
PrintUsageAndExitWithCode() {
    echo "$0 will execute ${0%.*}.py"
    echo "the script $0 must be called without any parameters"
    echo "usage: $0"
    echo "  $0 --help           - display this info"
    echo
    echo "$2"
    echo "errorExitCode = $1"
    exit $1
}

#---------------------------
# Main function
#---------------------------
# Set a safe PATH for LaunchAgents
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"
# echo "$(date): Starting script" >> /tmp/bingwallpaper.log

CURRENT_FILE_DIR="$(cd "$(dirname "$0")" && pwd)"
# echo "CURRENT_FILE_DIR = $CURRENT_FILE_DIR"

# figure out the project root dir
PROJECT_ROOT="$(cd "$CURRENT_FILE_DIR/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_PATH/bin/python"
BWP_LOG="/tmp/bingwallpaper.log"
UV_PATH=$(which uv)

# Keep the venv in sync with .python-version / uv.lock, so a python version update
# (or a broken/missing venv interpreter) heals itself instead of failing silently.
# uv sync is a no-op (milliseconds) when nothing changed. A failure here is logged
# but not fatal, the run below still tries with whatever venv exists.
if [ -x "$UV_PATH" ]; then
    (cd "$PROJECT_ROOT" && "$UV_PATH" sync --quiet) >> "$BWP_LOG" 2>&1 \
        || echo "$(date): WARNING: uv sync failed, see messages above" >> "$BWP_LOG"
fi

# Activate virtual environment
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
else
    echo "$(date): ERROR: Virtualenv not found at $VENV_PATH" >> "$BWP_LOG"
    exit 1
fi

PYTHON_FILE_NAME="$CURRENT_FILE_DIR/$(basename "${0%.*}.py")"
# echo "PYTHON_FILE_NAME = $PYTHON_FILE_NAME"

# Run with the venv interpreter directly. Do NOT use "uv run <script>" here: it builds
# a cached overlay environment under ~/.cache/uv/environments-v2 which can get stale
# and fail with "Failed to spawn: python".
if [ -x "$VENV_PYTHON" ]; then
    (cd "$CURRENT_FILE_DIR" && "$VENV_PYTHON" "$PYTHON_FILE_NAME") || PrintUsageAndExitWithCode $? "ERROR: executing ${0%.*}.py with venv python"
else
    echo "$(date): ERROR: venv python not executable at $VENV_PYTHON, falling back to python3" >> "$BWP_LOG"
    (cd "$CURRENT_FILE_DIR" && python3 "$PYTHON_FILE_NAME") || PrintUsageAndExitWithCode $? "ERROR: executing ${0%.*}.py with python"
fi

exit 0

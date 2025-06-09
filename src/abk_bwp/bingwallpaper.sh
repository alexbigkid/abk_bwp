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

# Activate virtual environment
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
else
    # echo "$(date): ERROR: Virtualenv not found at $VENV_PATH" >> /tmp/bingwallpaper.log
    exit 1
fi

PYTHON_FILE_NAME="$CURRENT_FILE_DIR/$(basename "${0%.*}.py")"
# echo "PYTHON_FILE_NAME = $PYTHON_FILE_NAME"
UV_PATH=$(which uv)
# echo "UV_PATH = $UV_PATH" >> /tmp/bingwallpaper.log
# echo "============= PATH = $PATH" >> /tmp/bingwallpaper.log

if [ -x "$UV_PATH" ]; then
    (cd "$CURRENT_FILE_DIR" && "$UV_PATH" run "$PYTHON_FILE_NAME") || PrintUsageAndExitWithCode $? "ERROR: executing ${0%.*}.py with uv"
else
    echo "$(date): uv not found in PATH, falling back to python" >> /tmp/bingwallpaper.log
    (cd "$CURRENT_FILE_DIR" && python3 "$PYTHON_FILE_NAME") || PrintUsageAndExitWithCode $? "ERROR: executing ${0%.*}.py with python"
fi

exit 0

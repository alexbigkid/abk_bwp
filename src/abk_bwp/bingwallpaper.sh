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
# echo ""
# echo "-> $0 ($@)"
EXIT_CODE=0

CURRENT_FILE_DIR=$(dirname $0)
# echo "CURRENT_FILE_DIR = $CURRENT_FILE_DIR"
FILE_NAME=$(basename $0)
# echo "FILE_NAME = $FILE_NAME"

PYTHON_FILE_NAME="${FILE_NAME%.*}.py"
# echo "PYTHON_FILE_NAME = $PYTHON_FILE_NAME"

# echo "============= PATH = $PATH"
# (cd $CURRENT_FILE_DIR && python $PYTHON_FILE_NAME || PrintUsageAndExitWithCode $? "ERROR: executing ${0%.*}.py")
(cd $CURRENT_FILE_DIR && uv run $PYTHON_FILE_NAME || PrintUsageAndExitWithCode $? "ERROR: executing ${0%.*}.py")

# echo "<- $0 ($EXIT_CODE)"
exit $EXIT_CODE

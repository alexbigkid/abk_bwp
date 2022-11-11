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
    echo $2
    echo "errorExitCode = $1"
    popd
    exit $1
}

find_pyenv_tool() {

    local LCL_DIRS_TO_CHECK_FOR_PYENV=(
        "/opt/homebrew/bin"
        "/usr/local/bin"
        "$HOME/.pyenv/bin"
        "$HOME/bin"
    )

    # add to PATH, so that we can init pyenv later
    for ((i = 0; i < ${#LCL_DIRS_TO_CHECK_FOR_PYENV[@]}; i++)); do
        DIR_TO_CHECK="${LCL_DIRS_TO_CHECK_FOR_PYENV[$i]}"
        echo "     [($i) ☑️  testing $DIR_TO_CHECK...]"
        if [ -d $DIR_TO_CHECK ]; then
            echo "     [($i) ☑️  adding $DIR_TO_CHECK to PATH...]"
            PATH="$DIR_TO_CHECK:$PATH"
        fi
    done

    # init pyenv
    LCL_TOOL_EXE=pyenv
    if [ "$(command -v $LCL_TOOL_EXE)" != "" ]; then
        echo -e "       [🎬 Initializing $LCL_TOOL_EXE ...]"
        # if pyenv is installed with brew following export lines are not required
        eval "$($LCL_TOOL_EXE init --path)"
        eval "$($LCL_TOOL_EXE init -)"

        # if pyenv-virtualenv is installed, init it, otherwise print a message for the user
        if [ "$(command -v $LCL_TOOL_EXE-virtualenv)" != "" ]; then
            echo -e "       [🎬 Initializing $LCL_TOOL_EXE virtualenv-init ...]"
            eval "$($LCL_TOOL_EXE virtualenv-init -)"
        else
            echo -e "       $LCL_TOOL_EXE-virtual is not installed! Consider using $LCL_TOOL_EXE-virtualenv"
            echo -e "       $LCL_TOOL_EXE-virtualenv can be installed with: ${GREEN}brew install $LCL_TOOL_EXE-virtualenv"
        fi

    else
        echo -e "       $LCL_TOOL_EXE is not installed! Consider managing python installations with $LCL_TOOL_EXE"
        echo -e "       $LCL_TOOL_EXE can be installed with: ${GREEN}brew install $LCL_TOOL_EXE"
    fi
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

pushd $CURRENT_FILE_DIR
find_pyenv_tool
# echo "============= PATH = $PATH"
python $PYTHON_FILE_NAME || PrintUsageAndExitWithCode $? "ERROR: executing ${0%.*}.py"

popd

# echo "<- $0 ($EXIT_CODE)"
exit $EXIT_CODE

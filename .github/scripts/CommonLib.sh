#---------------------------
# variables definitions
#---------------------------
declare -r TRUE=0
declare -r FALSE=1
declare -a ENV_ARRAY=("dev" "stage" "prod")
declare -a REGION_ARRAY=("us-east-1"
                         "us-east-2"
                         "us-west-2")


#---------------------------
# exit error codes
#---------------------------
EXIT_CODE_SUCCESS=0
EXIT_CODE_GENERAL_ERROR=1
EXIT_CODE_NOT_BASH_SHELL=2
EXIT_CODE_REQUIRED_TOOL_IS_NOT_INSTALLED=3
EXIT_CODE_INVALID_NUMBER_OF_PARAMETERS=4
EXIT_CODE_NOT_VALID_PARAMETER=5
EXIT_CODE_FILE_DOES_NOT_EXIST=6
EXIT_CODE_NOT_VALID_AWS_ACCOUNT_NUMBER=7
EXIT_CODE_FILE_IS_NOT_JSON_FILE=8
EXIT_CODE_FILE_IS_NOT_YAML_FILE=9
EXIT_CODE_DEPLOYMENT_FAILED=10
EXIT_CODE=$EXIT_CODE_SUCCESS



#---------------------------
# color definitions
#---------------------------
BLACK='\033[0;30m'
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
LIGHT_GRAY='\033[0;37m'
DARK_GRAY='\033[1;30m'
LIGHT_RED='\033[1;31m'
LIGHT_GREEN='\033[1;32m'
YELLOW='\033[1;33m'
LIGHT_BLUE='\033[1;34m'
LIGHT_PURPLE='\033[1;35m'
LIGHT_CYAN='\033[1;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color


#---------------------------
# functions
#---------------------------
IsParameterHelp ()
{
    echo "-> ${FUNCNAME[0]} ($@)"
    local NUMBER_OF_PARAMETERS=$1
    local PARAMETER=$2
    if [[ $NUMBER_OF_PARAMETERS -eq 1 && $PARAMETER == "--help" ]]; then
        echo "<- ${FUNCNAME[0]} (TRUE)"
        return $TRUE
    else
        echo "<- ${FUNCNAME[0]} (FALSE)"
        return $FALSE
    fi
}

CheckNumberOfParameters ()
{
    echo "-> ${FUNCNAME[0]} ($@)"
    local LCL_EXPECTED_NUMBER_OF_PARAMS=$1
    local LCL_ALL_PARAMS=($@)
    local LCL_PARAMETERS_PASSED_IN=(${LCL_ALL_PARAMS[@]:1:$#})
    if [ $LCL_EXPECTED_NUMBER_OF_PARAMS -ne ${#LCL_PARAMETERS_PASSED_IN[@]} ]; then
        echo "ERROR: invalid number of parameters."
        echo "  expected number:  $LCL_EXPECTED_NUMBER_OF_PARAMS"
        echo "  passed in number: ${#LCL_PARAMETERS_PASSED_IN[@]}"
        echo "  parameters passed in: ${LCL_PARAMETERS_PASSED_IN[@]}"
        echo "<- ${FUNCNAME[0]} (FALSE)"
        return $FALSE
    else
        echo "<- ${FUNCNAME[0]} (TRUE)"
        return $TRUE
    fi
}

IsPredefinedParameterValid ()
{
    echo "-> ${FUNCNAME[0]} ($@)"
    local MATCH_FOUND=$FALSE
    local VALID_PARAMETERS=""
    local PARAMETER=$1
    shift
    local PARAMETER_ARRAY=("$@")
    # echo "\$PARAMETER = $PARAMETER"
    for element in "${PARAMETER_ARRAY[@]}";
    do
        if [ $PARAMETER == $element ]; then
            MATCH_FOUND=$TRUE
        fi
        VALID_PARAMETERS="$VALID_PARAMETERS $element,"
        # echo "VALID PARAMS = $element"
    done

    if [ $MATCH_FOUND -eq $TRUE ]; then
        echo "<- ${FUNCNAME[0]} (TRUE)"
        return $TRUE
    else
        echo -e "${RED}ERROR: Invalid parameter:${NC} ${PURPLE}$PARAMETER${NC}"
        echo -e "${RED}Valid Parameters: $VALID_PARAMETERS ${NC}"
        echo "<- ${FUNCNAME[0]} (FALSE)"
        return $FALSE
    fi
}


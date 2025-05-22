#Requires -Version 5.0
$ErrorActionPreference = "Stop"

# -----------------------------------------------------------------------------
# variables definitions
# -----------------------------------------------------------------------------
[int64]$ERROR_CODE_SUCCESS=0
[int64]$ERROR_CODE_GENERAL_ERROR=1
[int64]$ERROR_CODE_NEEDED_FILE_DOES_NOT_EXIST=2

$EXPECTED_NUMBER_OF_PARAMETERS=0
$EXIT_CODE=$ERROR_CODE_SUCCESS

# -----------------------------------------------------------------------------
# functions
# -----------------------------------------------------------------------------
PrintUsageAndExitWithCode ($scriptName, $exitErrorCode) {
    Write-Host "->" $MyInvocation.MyCommand.Name ($scriptName, $exitErrorCode) -ForegroundColor Yellow
    Write-Host "   $scriptName will will execute $scriptName.py"
    Write-Host "   Usage: $scriptName"
    Write-Host "     $scriptName --help           - display this info"
    Write-Host "<-" $MyInvocation.MyCommand.Name "($exitErrorCode)" -ForegroundColor Yellow
    exit $exitErrorCode
}

# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "->" $MyInvocation.MyCommand.Name "($args)" -ForeGroundColor Green

Write-Host " Windows Version NOT READY YET " -ForeGroundColor Red
Write-Host "   [args.Count      =" $args.Count "]"
Write-Host "   [HOME            = $HOME]"
Write-Host "   [env:Home        = $env:Home]"
Write-Host

# if logged in on a computer through a different user, the $env:Home is not the same as $HOME
# which will cause some problems. So the $env:Home needs to be set to $HOME
if ( $HOME -ne $env:Home ) {
    Write-Host "   [setting env:Home to $HOME] ..."
    $env:Home=$HOME
}

# Is parameter --help?
if (Confirm-ParameterIsHelp $args.Count $args[0]) {
    PrintUsageAndExitWithCode $MyInvocation.MyCommand.Name $EXIT_CODE_SUCCESS
}



Write-Host "<-" $MyInvocation.MyCommand.Name "($EXIT_CODE)" -ForeGroundColor Green
exit $EXIT_CODE

import os
#from subprocess import call, check_output
import subprocess
import abkPackage
from abkPackage import abkCommon
import logging
import logging.config
logger = logging.getLogger(__name__)

def GetPlistNames(scriptName):
    logger.debug("-> GetPlistNames(scriptName=%s)", scriptName)
    userName = abkCommon.GetUserName()
    plistLable = "com."+userName+"."+scriptName
    plistName = plistLable+".plist"
    logger.debug("<- GetPlistNames(plistLable=%s, plistName=%s)", plistLable, plistName)    
    return (plistLable, plistName)

def StopAndUnloadBingwallpaperJob(plistFullName, plistLable):
    logger.debug("-> StopAndUnloadBingwallpaperJob(plistFullName=%s, plistLable=%s)", plistFullName, plistLable)

    cmdList = []
    cmdList.append("launchctl stop "+plistLable)
    cmdList.append("launchctl unload -w "+plistFullName)

    for cmd in cmdList:
        try:
            retCode = subprocess.check_call(cmd, shell=True)
            logger.info("command '%s' succeeded, returned: %s", cmd, str(retCode))
        except subprocess.CalledProcessError as e:
            logger.error("command '%s' failed, returned: %d", cmd, e.returncode)

    logger.debug("<- StopAndUnloadBingwallpaperJob")

def DeletePlistFile(scriptName):
    logger.debug("-> DeletePlistFile(%s)", scriptName)
    if os.path.isfile(scriptName):
        try:
            os.unlink(scriptName)
            logger.info("deleted file %s", scriptName)
        except OSError as error:
            logger.error("failed to delete file %s, with error=%d", scriptName, error.errno)
            pass
    else:
        logger.info("file %s does not exot", scriptName)
        
    logger.debug("<- DeletePlistFile")


def Cleanup(pyFullName):
    logger.debug("-> Cleanup(pyFullName=%s)", pyFullName)
    scriptName = os.path.basename(pyFullName)
    scriptPath = os.path.dirname(pyFullName)
    logger.info("scriptName = %s", scriptName)
    logger.info("scriptPath = %s", scriptPath)
    (plistLable, plistName) = GetPlistNames(scriptName)

    homeDir = abkCommon.GetHomeDir()
    plistLinkName = os.path.join(homeDir+"/Library/LaunchAgents", plistName)
    plistFullName = os.path.join(scriptPath, plistName)
    logger.info("plistLinkName = %s", plistLinkName)
    logger.info("plistFullName = %s", plistFullName)

    StopAndUnloadBingwallpaperJob(plistLinkName, plistLable)
    abkCommon.RemoveLink(plistLinkName)
    DeletePlistFile(plistFullName)
    logger.debug("<- Cleanup")

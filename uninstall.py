# This script will:
# 1. delete a link bingwallpaper.py in home_dir/abkBin directory to current dir
# 2. Platform dependant operation - create platfrom dependent environment
#   2.1. Mac
#       2.1.1. stop and unload the job via plist file
#       2.1.2. delete a link in ~/Library/LaunchAgents/com.<userName>.bingwallpaper.py.list to the plist in current directory
#       2.1.3. delete a plist file for scheduled job in current directory 
#   2.2 Linux
#       2.2.1. NOT READY YET
#   2.3 Windows
#       2.3.1. NOT READY YET
#  
# Created by Alex Berger @ http://www.ABKphoto.com

import os
import shutil
import logging
import logging.config
import json
from sys import platform as _platform
import abkPackage
from abkPackage import abkCommon

configFile = 'config.json'
loggingConf = 'logging.conf'

def readConfigFile(confFile):
    logger.debug("-> readConfigFile(confFile=%s)", confFile)
    with open(confFile) as json_data:
        config = json.load(json_data)
    json_data.close()
    logger.debug("<- readConfigFile(pyScriptName=%s, imagesDirrectory=%s)", config['pyScriptName'], config['imagesDirrectory'])
    return (config['pyScriptName'], config['imagesDirrectory'])

def deleteImageDir(imagesDir):
    logger.debug("-> deleteImageDir(imagesDir=%s)", imagesDir)
    if(os.path.isdir(imagesDir)):
        try:
            shutil.rmtree(imagesDir)
        except:
			self.logger.error("deleting image directory %s failed", imagesDir)

    logger.debug("<- deleteImageDir")

def unlinkPythonScript (fileName):
    logger.debug("-> unlinkPythonScript(fileName=%s)", fileName)
    binDir = os.path.join(abkCommon.GetHomeDir(), "bin")
    currDir = abkCommon.GetCurrentDir(__file__)
    src = os.path.join(currDir, fileName)
    pyBinLink = os.path.join(binDir, fileName)
    abkCommon.RemoveLink(pyBinLink)
    abkCommon.DeleteDir(binDir)
    logger.debug("<- unlinkPythonScript")
    return src

def main():
    logger.debug("-> main()")
    (pyScriptName, imagesDir) = readConfigFile(configFile)
    imageFullPath = os.path.join(abkCommon.GetHomeDir(), imagesDir)
    deleteImageDir(imageFullPath)
    unlinkPythonScript(pyScriptName)

    #>>>>>>>>>> platform dependency 
    if _platform == "darwin":
        # Mac OS X ------------------------
        logger.info("Mac OS X environment")
        from abkPackage import uninstallMac as uninstallXxx

    elif _platform == "linux" or _platform == "linux2":
        # linux ---------------------------
        logger.info("Linux environment")
        #from abkPackage import uninstallLnx as uninstallXxx

    elif _platform == "win32" or _platform == "win64":
        # Windows or Windows 64-bit -----
        logger.info("Windows environment")
        #from abkPackage import uninstallWin as uninstallXxx
        #<<<<<<<<<< platform dependency 

    currDir = abkCommon.GetCurrentDir(__file__)
    logger.info("currDir=%s", currDir)
    pyScriptFullName = os.path.join(currDir, pyScriptName)
    logger.info("pyScriptFullName=%s", pyScriptFullName)
    uninstallXxx.Cleanup(pyScriptFullName)
    logger.debug("<- main()")

if __name__ == '__main__':
    logging.config.fileConfig(loggingConf)
    logger = logging.getLogger(__name__)
    main()

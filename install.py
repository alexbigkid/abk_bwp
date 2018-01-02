# This script will:
# 1. create a link bingwallpaper.py in home_dir/bin directory to current dir
# 2. Platform dependant operation - create platfrom dependent environment
#   2.1. Mac
#       2.1.1. create a plist file for scheduled job in current directory 
#       2.2.2. create a link in ~/Library/LaunchAgents/com.<userName>.bingwallpaper.py.list to the plist in current directory
#   2.2 Linux
#       2.2.1. NOT READY YET
#   2.3 Windows
#       2.3.1. NOT READY YET
# 3. schedule the job permanent job running at 8am or when logged in 
#  
# Created by Alex Berger @ http://www.ABKphoto.com

import os
import logging
import logging.config
#import shutil
import json
from sys import platform as _platform
import abkPackage
from abkPackage import abkCommon


configFile = 'config.json'
loggingConf = 'logging.conf'

def readConfigFile(confFile):
    logger.debug("-> readConfigFile(%s)", confFile)
    with open(confFile) as json_data:
        config = json.load(json_data)
    json_data.close()
    logger.debug("<- readConfigFile(hour=%s, minute=%s, pyScriptName=%s)", config['hour'], config['minute'], config['pyScriptName'])
    return (config['hour'], config['minute'], config['pyScriptName'])

def linkPythonScript (file_name):
    logger.debug("-> linkPythonScript(%s)", file_name)
    bin_dir = os.path.join(abkCommon.GetHomeDir(), "bin")
    abkCommon.EnsureDir(bin_dir)
    curr_dir = abkCommon.GetCurrentDir(__file__)
    src = os.path.join(curr_dir, file_name)
    dst = os.path.join(bin_dir, file_name)
    abkCommon.EnsureLinkExists(src, dst)
    logger.debug("<- linkPythonScript(src=%s)", src)
    return src

def main():
    logger.debug("-> main()")
    (hour2run, minute2run, pyScriptName) = readConfigFile(configFile)
    #>>>>>>>>>> platform dependency 
    if _platform == "darwin":
        # Mac OS X ------------------------
        logger.info("Mac OS X environment")
        from abkPackage import installMac as installXxx

    elif _platform == "linux" or _platform == "linux2":
        # linux ---------------------------
        logger.info("Linux environment")
        #from abkPackage import installLnx as installXxx

    elif _platform == "win32" or _platform == "win64":
        # Windows or Windows 64-bit -----
        logger.info("Windows environment")
        #from abkPackage import installWin as installXxx
        #<<<<<<<<<< platform dependency 

    logger.info("hour2run: %s, minute2run: %s, pyScriptName: %s", hour2run, minute2run, pyScriptName)
    pyFullName = linkPythonScript(pyScriptName)
    installXxx.platFormDependantSetup(hour2run, minute2run, pyFullName)
    logger.debug("<- main()")

if __name__ == '__main__':
    logging.config.fileConfig(loggingConf)
    logger = logging.getLogger(__name__)
    main()

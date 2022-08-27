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
from abkPackage import abkCommon
from abkPackage.abkCommon import function_trace
from config import bwp_config


@function_trace
def deleteImageDir(imagesDir):
    logger.debug(f'{imagesDir=}')
    if(os.path.isdir(imagesDir)):
        try:
            shutil.rmtree(imagesDir)
        except:
            logger.error(f'deleting image directory {imagesDir} failed')


@function_trace
def unlinkPythonScript (fileName):
    logger.debug(f'{fileName=}')
    binDir = os.path.join(abkCommon.GetHomeDir(), "bin")
    currDir = abkCommon.GetCurrentDir(__file__)
    src = os.path.join(currDir, fileName)
    pyBinLink = os.path.join(binDir, fileName)
    abkCommon.RemoveLink(pyBinLink)
    abkCommon.DeleteDir(binDir)
    return src


@function_trace
def main():
    imageFullPath = os.path.join(abkCommon.GetHomeDir(), bwp_config["image_dir"])
    deleteImageDir(imageFullPath)
    unlinkPythonScript(bwp_config["app_name"])

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
    pyScriptFullName = os.path.join(currDir, bwp_config["app_name"])
    logger.info("pyScriptFullName=%s", pyScriptFullName)
    uninstallXxx.Cleanup(pyScriptFullName)


if __name__ == '__main__':
    command_line_options = abkCommon.CommandLineOptions()
    command_line_options.handle_options()
    logger = logger=command_line_options._logger
    main()

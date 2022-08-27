""" 1. delete a link bingwallpaper.py in home_dir/abkBin directory to current dir
    2. Platform dependant operation - create platfrom dependent environment
        2.1. Mac
            2.1.1. stop and unload the job via plist file
            2.1.2. delete a link in ~/Library/LaunchAgents/com.<userName>.bingwallpaper.py.list to the plist in current directory
            2.1.3. delete a plist file for scheduled job in current directory
        2.2 Linux
            2.2.1. NOT READY YET
        2.3 Windows
            2.3.1. NOT READY YET
"""

import os
import shutil
import logging
import logging.config
import subprocess
from abc import ABCMeta, abstractmethod
from sys import platform as _platform

from config import bwp_config
from abkPackage import abkCommon


@abkCommon.function_trace
def deleteImageDir(imagesDir):
    logger.debug(f'{imagesDir=}')
    if(os.path.isdir(imagesDir)):
        try:
            shutil.rmtree(imagesDir)
        except:
            logger.error(f'deleting image directory {imagesDir} failed')


@abkCommon.function_trace
def unlinkPythonScript (fileName):
    logger.debug(f'{fileName=}')
    binDir = os.path.join(abkCommon.GetHomeDir(), "bin")
    currDir = abkCommon.GetCurrentDir(__file__)
    src = os.path.join(currDir, fileName)
    pyBinLink = os.path.join(binDir, fileName)
    abkCommon.RemoveLink(pyBinLink)
    abkCommon.DeleteDir(binDir)
    return src



class IUninstallBase(metaclass=ABCMeta):
    """Abstract class (mostly)"""
    os_type: abkCommon.OsType = None  # type: ignore

    @abkCommon.function_trace
    def __init__(self, logger:logging.Logger=None) -> None:  # type: ignore
        """Super class init"""
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(f'({__class__.__name__}) Initializing {self.os_type} uninstallation environment ...')


    @abstractmethod
    def cleanup(self, app_name: str) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplemented



class UninstallOnMacOS(IUninstallBase):
    """Concrete Uninstallation on MacOS"""

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        self.os_type = abkCommon.OsType.MAC_OS
        super().__init__(logger)


    @abkCommon.function_trace
    def cleanup(self, app_name: str) -> None:
        """Cleans up installation of the bing wall paper downloader on MacOS
        Args:
            app_name (str): application name
        """
        logger.debug(f'{app_name=}')
        scriptName = os.path.basename(app_name)
        scriptPath = os.path.dirname(app_name)
        logger.info(f'{scriptPath=}, {scriptName=}, ')
        (plistLable, plistName) = self.GetPlistNames(scriptName)

        homeDir = abkCommon.GetHomeDir()
        plistLinkName = os.path.join(f'{homeDir}/Library/LaunchAgents', plistName)
        plistFullName = os.path.join(scriptPath, plistName)
        logger.info(f'{plistLinkName=}')
        logger.info(f'{plistFullName=}')

        self.StopAndUnloadBingwallpaperJob(plistLinkName, plistLable)
        abkCommon.RemoveLink(plistLinkName)
        self.DeletePlistFile(plistFullName)


    @abkCommon.function_trace
    def GetPlistNames(self, scriptName):
        logger.debug(f'{scriptName=}')
        userName = abkCommon.GetUserName()
        plistLable = "com."+userName+"."+scriptName
        plistName = plistLable+".plist"
        logger.debug(f'{plistLable=}, {plistName=}')
        return (plistLable, plistName)


    @abkCommon.function_trace
    def StopAndUnloadBingwallpaperJob(self, plistName, plistLable):
        logger.debug(f'{plistName=}, {plistLable=}')

        cmdList = []
        cmdList.append("launchctl list | grep "+plistLable)
        cmdList.append("launchctl stop "+plistLable)
        cmdList.append("launchctl unload -w "+plistName)

        try:
            for cmd in cmdList:
                logger.info(f"about to execute command '{cmd}'")
                retCode = subprocess.check_call(cmd, shell=True)
                logger.info(f"command '{cmd}' succeeded, returned: {retCode}")
        except subprocess.CalledProcessError as e:
            logger.error(f'ERROR: returned: {e.returncode}')


    @abkCommon.function_trace
    def DeletePlistFile(self, scriptName):
        logger.debug(f'{scriptName=}')
        if os.path.isfile(scriptName):
            try:
                os.unlink(scriptName)
                logger.info(f'deleted file {scriptName}')
            except OSError as error:
                logger.error(f'failed to delete file {scriptName}, with error = {error.errno}')
        else:
            logger.info(f'file {scriptName} does not exist')



class UninstallOnLinux(IUninstallBase):
    """Concrete Uninstallation on Linux"""

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        self.os_type = abkCommon.OsType.LINUX_OS
        super().__init__(logger)


    @abkCommon.function_trace
    def cleanup(self, app_name: str) -> None:
        """Cleans up installation of the bing wall paper downloader on Linux
        Args:
            app_name (str): application name
        """
        logger.debug(f'{app_name=}')
        self._logger.info(f'{self.os_type.value} uninstallation is not supported yet')



class UninstallOnWindows(IUninstallBase):
    """Concrete Uninstallation on Windows"""

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        self.os_type = abkCommon.OsType.WINDOWS_OS
        super().__init__(logger)


    @abkCommon.function_trace
    def cleanup(self, app_name: str) -> None:
        """Cleans up installation of the bing wall paper downloader on Windows
        Args:
            app_name (str): application name
        """
        logger.debug(f'{app_name=}')
        self._logger.info(f'{self.os_type.value} uninstallation is not supported yet')





@abkCommon.function_trace
def main():
    imageFullPath = os.path.join(abkCommon.GetHomeDir(), bwp_config["image_dir"])
    deleteImageDir(imageFullPath)
    unlinkPythonScript(bwp_config["app_name"])

    if _platform in abkCommon.OsPlatformType.PLATFORM_MAC.value:
        uninstallation = UninstallOnMacOS(logger=logger)
    elif _platform in abkCommon.OsPlatformType.PLATFORM_LINUX.value:
        uninstallation = UninstallOnLinux(logger=logger)
    elif _platform in abkCommon.OsPlatformType.PLATFORM_WINDOWS.value:
        uninstallation = UninstallOnWindows(logger=logger)
    else:
        raise ValueError(f'ERROR: "{_platform}" is not supported')

    currDir = abkCommon.GetCurrentDir(__file__)
    logger.info("currDir=%s", currDir)
    pyScriptFullName = os.path.join(currDir, bwp_config["app_name"])
    logger.info("pyScriptFullName=%s", pyScriptFullName)
    uninstallation.cleanup(pyScriptFullName)


if __name__ == '__main__':
    command_line_options = abkCommon.CommandLineOptions()
    command_line_options.handle_options()
    logger = command_line_options._logger
    main()

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
from typing import Tuple

from config import ROOT_KW, bwp_config
from abkPackage import abkCommon


class IUninstallBase(metaclass=ABCMeta):
    """Abstract class (mostly)"""

    os_type: abkCommon.OsType = None  # type: ignore

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        """Super class init"""
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(f"({__class__.__name__}) Initializing {self.os_type} uninstallation environment ...")

    @abstractmethod
    def cleanup_installation(self, app_name: str) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplemented

    @abstractmethod
    def cleanup_image_dir(self, image_dir: str) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplemented


class UninstallOnMacOS(IUninstallBase):
    """Concrete Uninstallation on MacOS"""

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        self.os_type = abkCommon.OsType.MAC_OS
        super().__init__(logger)

    @abkCommon.function_trace
    def cleanup_installation(self, app_name: str) -> None:
        """Cleans up installation of the bing wall paper downloader on MacOS
        Args:
            app_name (str): application name
        """
        self._logger.debug(f"{app_name=}")
        # remove the link from $HOME/bin directory
        self._unlink_python_script(app_name)
        # get app_name full name with path
        curr_dir = abkCommon.get_current_dir(__file__)
        self._logger.info(f"{curr_dir=}")
        app_file_full_name = os.path.join(curr_dir, app_name)
        self._logger.info(f"{app_file_full_name=}")
        # get plist data
        script_name = os.path.basename(app_file_full_name)
        script_path = os.path.dirname(app_file_full_name)
        self._logger.info(f"{script_path=}, {script_name=}")
        (plist_lable, plist_name) = self._get_plist_names(script_name)
        # stop jobs and unload plist file
        home_dir = abkCommon.get_home_dir()
        plist_link_name = os.path.join(f"{home_dir}/Library/LaunchAgents", plist_name)
        plist_full_name = os.path.join(script_path, plist_name)
        self._logger.info(f"{plist_link_name=}")
        self._logger.info(f"{plist_full_name=}")
        self._stop_and_unload_bingwallpaper_job(plist_link_name, plist_lable)
        abkCommon.remove_link(plist_link_name)
        self._delete_plist_file(plist_full_name)

    @abkCommon.function_trace
    def cleanup_image_dir(self, image_dir: str) -> None:
        """Cleans up image directory, deletes all downloaded images
        Args:
            image_dir (str): image directory name
        """
        image_full_path = os.path.join(abkCommon.get_home_dir(), image_dir)
        self._delete_image_dir(image_full_path)

    @abkCommon.function_trace
    def _unlink_python_script(self, file_name: str) -> str:
        """Deletes link in the $HOME/bin directory
        Args:
            file_name (str): file name of the link
        Returns:
            str: full name of the source of the link
        """
        self._logger.debug(f"{file_name=}")
        bin_dir = os.path.join(abkCommon.get_home_dir(), "bin")
        curr_dir = abkCommon.get_current_dir(__file__)
        src = os.path.join(curr_dir, file_name)
        py_bin_link = os.path.join(bin_dir, file_name)
        abkCommon.remove_link(py_bin_link)
        abkCommon.delete_dir(bin_dir)
        return src

    @abkCommon.function_trace
    def _delete_image_dir(self, images_dir: str) -> None:
        """deletes image directory and all downloaded images
        Args:
            images_dir (str): image directory name
        """
        self._logger.debug(f"{images_dir=}")
        if os.path.isdir(images_dir):
            try:
                shutil.rmtree(images_dir)
            except:
                self._logger.error(f"deleting image directory {images_dir} failed")

    @abkCommon.function_trace
    def _get_plist_names(self, script_name: str) -> Tuple[str, str]:
        """Gets plist names. Plist lable and plist file name
        Args:
            script_name (str): full script name
        Returns:
            Tuple[str, str]: plist lable and plist file name
        """
        self._logger.debug(f"{script_name=}")
        user_name = abkCommon.get_user_name()
        plist_lable = f"com.{user_name}.{script_name}"
        plist_file_name = f"{plist_lable}.plist"
        self._logger.debug(f"{plist_lable=}, {plist_file_name=}")
        return (plist_lable, plist_file_name)

    @abkCommon.function_trace
    def _stop_and_unload_bingwallpaper_job(self, plist_name: str, plist_lable: str) -> None:
        """Stops and unloads bing wallpaper jobs
        Args:
            plist_name (str): plist file name
            plist_lable (str): plist lable
        """
        self._logger.debug(f"{plist_name=}, {plist_lable=}")

        cmdList = []
        cmdList.append(f"launchctl list | grep {plist_lable}")
        cmdList.append(f"launchctl stop {plist_lable}")
        cmdList.append(f"launchctl unload -w {plist_name}")

        try:
            for cmd in cmdList:
                self._logger.info(f"about to execute command '{cmd}'")
                return_code = subprocess.check_call(cmd, shell=True)
                self._logger.info(f"command '{cmd}' succeeded, returned: {return_code}")
        except subprocess.CalledProcessError as e:
            self._logger.error(f"ERROR: returned: {e.returncode}")

    @abkCommon.function_trace
    def _delete_plist_file(self, script_name: str) -> None:
        """Deletes plist file
        Args:
            script_name (str): plist file name
        """
        self._logger.debug(f"{script_name=}")
        if os.path.isfile(script_name):
            try:
                os.unlink(script_name)
                self._logger.info(f"deleted file {script_name}")
            except OSError as error:
                self._logger.error(f"failed to delete file {script_name}, with error = {error.errno}")
        else:
            self._logger.info(f"file {script_name} does not exist")


class UninstallOnLinux(IUninstallBase):
    """Concrete Uninstallation on Linux"""

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        self.os_type = abkCommon.OsType.LINUX_OS
        super().__init__(logger)

    @abkCommon.function_trace
    def cleanup_installation(self, app_name: str) -> None:
        """Cleans up installation of the bing wall paper downloader on Linux
        Args:
            app_name (str): application name
        """
        self._logger.debug(f"{app_name=}")
        self._logger.info(f"{self.os_type.value} uninstallation is not supported yet")

    @abkCommon.function_trace
    def cleanup_image_dir(self, image_dir: str) -> None:
        self._logger.debug(f"{image_dir=}")
        self._logger.info(f"{self.os_type.value} cleanup_image_dir is not supported yet")


class UninstallOnWindows(IUninstallBase):
    """Concrete Uninstallation on Windows"""

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        self.os_type = abkCommon.OsType.WINDOWS_OS
        super().__init__(logger)

    @abkCommon.function_trace
    def cleanup_installation(self, app_name: str) -> None:
        """Cleans up installation of the bing wall paper downloader on Windows
        Args:
            app_name (str): application name
        """
        self._logger.debug(f"{app_name=}")
        self._logger.info(f"{self.os_type.value} uninstallation is not supported yet")

    @abkCommon.function_trace
    def cleanup_image_dir(self, image_dir: str) -> None:
        self._logger.debug(f"{image_dir=}")
        self._logger.info(f"{self.os_type.value} cleanup_image_dir is not supported yet")


@abkCommon.function_trace
def main():
    command_line_options = abkCommon.CommandLineOptions()
    command_line_options.handle_options()
    main_logger = command_line_options._logger

    if _platform in abkCommon.OsPlatformType.PLATFORM_MAC.value:
        uninstallation = UninstallOnMacOS(logger=main_logger)
    elif _platform in abkCommon.OsPlatformType.PLATFORM_LINUX.value:
        uninstallation = UninstallOnLinux(logger=main_logger)
    elif _platform in abkCommon.OsPlatformType.PLATFORM_WINDOWS.value:
        uninstallation = UninstallOnWindows(logger=main_logger)
    else:
        raise ValueError(f'ERROR: "{_platform}" is not supported')

    if bwp_config.get(ROOT_KW.RETAIN_IMAGES.value, False) == False:
        uninstallation.cleanup_image_dir(bwp_config[ROOT_KW.IMAGE_DIR.value])
    uninstallation.cleanup_installation(bwp_config[ROOT_KW.APP_NAME.value])


if __name__ == "__main__":
    main()

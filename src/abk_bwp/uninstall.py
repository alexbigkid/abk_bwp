"""1. delete a link bingwallpaper.py in home_dir/abkBin directory to current dir
2. Platform dependant operation - create platfrom dependent environment
    2.1. Mac
        2.1.1. stop and unload the job via plist file
        2.1.2. delete a link in ~/Library/LaunchAgents/com.<userName>.bingwallpaper.py.list to the plist in current directory
        2.1.3. delete a plist file for scheduled job in current directory
    2.2 Linux
        2.2.1. NOT READY YET
    2.3 Windows
        2.3.1. NOT READY YET.
"""  # noqa: D205, D208, D210

# Standard lib imports
import os
import logging
import shutil
import subprocess
import sys
from abc import ABCMeta, abstractmethod
from sys import platform as _platform
from typing import Tuple, Union


# Third party imports
from colorama import Fore, Style


# Local imports
from abk_bwp import abk_common
from abk_bwp.config import ROOT_KW, bwp_config


class IUninstallBase(metaclass=ABCMeta):
    """Abstract class (mostly)."""

    os_type: abk_common.OsType = None  # type: ignore
    _shell_file_name: str = None  # type: ignore

    @property
    def shell_file_name(self) -> str:
        """Gets Shell File name.

        Returns:
            str: shell file name
        """
        if self._shell_file_name is None:
            extension = ("sh", "ps1")[self.os_type == abk_common.OsType.WINDOWS_OS]
            self._shell_file_name = f"{abk_common.BWP_APP_NAME}.{extension}"
        return self._shell_file_name

    @abk_common.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        """Super class init."""
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(
            f"({__class__.__name__}) Initializing {self.os_type} uninstallation environment ..."
        )

    @abstractmethod
    def teardown_installation(self) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplementedError

    @abstractmethod
    def cleanup_image_dir(self, image_dir: str) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplementedError


class UninstallOnMacOS(IUninstallBase):
    """Concrete Uninstallation on MacOS."""

    @abk_common.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        """Inits uninstall on MacOS class.

        Args:
            logger (logging.Logger, optional): passed in logger. Defaults to None.
        """
        self.os_type = abk_common.OsType.MAC_OS
        super().__init__(logger)

    @abk_common.function_trace
    def teardown_installation(self) -> None:
        """Cleans up installation of the bing wall paper downloader on MacOS."""
        self._logger.debug(f"{self.shell_file_name=}")
        curr_dir = abk_common.get_current_dir(__file__)
        self._logger.info(f"{curr_dir=}")
        app_file_full_name = os.path.join(curr_dir, self.shell_file_name)
        # app_file_full_name = os.path.join(curr_dir, "bingwallpaper.py")
        self._logger.info(f"{app_file_full_name=}")
        # get plist data
        script_name = os.path.basename(app_file_full_name)
        script_path = os.path.dirname(app_file_full_name)
        self._logger.info(f"{script_path=}, {script_name=}")
        (plist_label, plist_name) = self._get_plist_names(script_name)
        # stop jobs and unload plist file
        home_dir = abk_common.get_home_dir()
        plist_link_name = os.path.join(f"{home_dir}/Library/LaunchAgents", plist_name)
        plist_full_name = os.path.join(script_path, plist_name)
        self._logger.info(f"{plist_link_name=}")
        self._logger.info(f"{plist_full_name=}")
        self._stop_and_unload_bingwallpaper_job(plist_link_name, plist_label)
        abk_common.remove_link(plist_link_name)
        self._delete_plist_file(plist_full_name)

    @abk_common.function_trace
    def cleanup_image_dir(self, image_dir: str) -> None:
        """Cleans up image directory, deletes all downloaded images.

        Args:
            image_dir (str): image directory name
        """
        image_full_path = os.path.join(abk_common.get_home_dir(), image_dir)
        self._delete_image_dir(image_full_path)

    @abk_common.function_trace
    def _delete_image_dir(self, images_dir: str) -> None:
        """Deletes image directory and all downloaded images.

        Args:
            images_dir (str): image directory name
        """
        self._logger.debug(f"{images_dir=}")
        if os.path.isdir(images_dir):
            try:
                shutil.rmtree(images_dir)
            except Exception:
                self._logger.error(f"deleting image directory {images_dir} failed")

    # TODO: remove tuple
    @abk_common.function_trace
    def _get_plist_names(self, script_name: str) -> Tuple[str, str]:
        """Gets plist names. Plist label and plist file name.

        Args:
            script_name (str): full script name
        Returns:
            Tuple[str, str]: plist label and plist file name
        """
        self._logger.debug(f"{script_name=}")
        user_name = abk_common.get_user_name()
        plist_lable = f"com.{user_name}.{script_name}"
        plist_file_name = f"{plist_lable}.plist"
        self._logger.debug(f"{plist_lable=}, {plist_file_name=}")
        return (plist_lable, plist_file_name)

    @abk_common.function_trace
    def _stop_and_unload_bingwallpaper_job(self, plist_name: str, plist_label: str) -> None:
        """Stops and unloads bing wallpaper jobs.

        Args:
            plist_name (str): plist file name
            plist_label (str): plist label
        """
        self._logger.debug(f"{plist_name=}, {plist_label=}")

        cmdList = []
        cmdList.append(f"launchctl list | grep {plist_label}")
        cmdList.append(f"launchctl stop {plist_label}")
        cmdList.append(f"launchctl unload -w {plist_name}")

        try:
            for cmd in cmdList:
                self._logger.info(f"about to execute command '{cmd}'")
                return_code = subprocess.check_call(cmd, shell=True)
                self._logger.info(f"command '{cmd}' succeeded, returned: {return_code}")
        except subprocess.CalledProcessError as e:
            self._logger.error(f"ERROR: returned: {e.returncode}")

    @abk_common.function_trace
    def _delete_plist_file(self, script_name: str) -> None:
        """Deletes plist file.

        Args:
            script_name (str): plist file name
        """
        self._logger.debug(f"{script_name=}")
        if os.path.isfile(script_name):
            try:
                os.unlink(script_name)
                self._logger.info(f"deleted file {script_name}")
            except OSError as error:
                self._logger.error(
                    f"failed to delete file {script_name}, with error = {error.errno}"
                )
        else:
            self._logger.info(f"file {script_name} does not exist")


class UninstallOnLinux(IUninstallBase):
    """Concrete Uninstallation on Linux."""

    @abk_common.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        """Inits uninstall on Linux class.

        Args:
            logger (logging.Logger, optional): passed in logger. Defaults to None.
        """
        self.os_type = abk_common.OsType.LINUX_OS
        super().__init__(logger)

    @abk_common.function_trace
    def teardown_installation(self) -> None:
        """Cleans up installation of the bing wall paper downloader on Linux."""
        self._logger.debug(f"{self.shell_file_name=}")
        self._logger.info(f"{self.os_type.value} uninstallation is not supported yet")

    @abk_common.function_trace
    def cleanup_image_dir(self, image_dir: str) -> None:
        """Cleans up image directory.

        Args:
            image_dir (str): image directory
        """
        self._logger.debug(f"{image_dir=}")
        self._logger.info(f"{self.os_type.value} cleanup_image_dir is not supported yet")


class UninstallOnWindows(IUninstallBase):
    """Concrete Uninstallation on Windows."""

    @abk_common.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        """Inits uninstall on Windows class.

        Args:
            logger (logging.Logger, optional): passed in logger. Defaults to None.
        """
        self.os_type = abk_common.OsType.WINDOWS_OS
        super().__init__(logger)

    @abk_common.function_trace
    def teardown_installation(self) -> None:
        """Cleans up installation of the bing wall paper downloader on Windows."""
        self._logger.debug(f"{self.shell_file_name=}")
        self._logger.info(f"{self.os_type.value} uninstallation is not supported yet")

    @abk_common.function_trace
    def cleanup_image_dir(self, image_dir: str) -> None:
        """Cleans up image directory.

        Args:
            image_dir (str): image dir to clean up
        """
        self._logger.debug(f"{image_dir=}")
        self._logger.info(f"{self.os_type.value} cleanup_image_dir is not supported yet")


@abk_common.function_trace
def bwp_uninstall(uninstall_logger: Union[logging.Logger, None] = None) -> None:
    """BingWallPaper uninstall.

    Args:
        uninstall_logger: passed in logger. Defaults to None.

    Raises:
        ValueError: Unsupported OS
        Exception: catches any other exception
    """
    exit_code = 0
    _logger = uninstall_logger or logging.getLogger(__name__)
    try:
        if _platform in abk_common.OsPlatformType.PLATFORM_MAC.value:
            uninstallation = UninstallOnMacOS(logger=_logger)
        elif _platform in abk_common.OsPlatformType.PLATFORM_LINUX.value:
            uninstallation = UninstallOnLinux(logger=_logger)
        elif _platform in abk_common.OsPlatformType.PLATFORM_WINDOWS.value:
            uninstallation = UninstallOnWindows(logger=_logger)
        else:
            raise ValueError(f'ERROR: "{_platform}" is not supported')

        if not bwp_config.get(ROOT_KW.RETAIN_IMAGES.value, False):
            uninstallation.cleanup_image_dir(bwp_config[ROOT_KW.IMAGE_DIR.value])
        uninstallation.teardown_installation()
    except Exception as exc:
        _logger.error(f"{Fore.RED}ERROR: executing bingwallpaper")
        _logger.error(f"EXCEPTION: {exc}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    command_line_options = abk_common.CommandLineOptions()
    command_line_options.handle_options()
    uninstall_logger = command_line_options.logger
    bwp_uninstall(uninstall_logger)

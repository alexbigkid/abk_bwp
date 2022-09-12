""" 1. Creates a link bingwallpaper.py in home_dir/abkBin directory to current dir
    2. Platform dependant operation - create platfrom dependent environment
        2.1. Mac
            2.1.1. create a plist file for scheduled job in current directory
            2.1.2. create a link in ~/Library/LaunchAgents/com.<userName>.bingwallpaper.py.list to the plist in current directory
            2.1.3. stop, unload, load and start the job via plist file
        2.2 Linux
            2.2.1. NOT READY YET
        2.3 Windows
            2.3.1. NOT READY YET
    3. schedule the job permanent job running at 8am or when logged in
"""

# Standard lib imports
import os
import sys
import logging
import logging.config
import subprocess
from abc import ABCMeta, abstractmethod
from datetime import datetime, time
from sys import platform as _platform
from typing import Union

# Third party imports
from colorama import Fore, Style

# local imports
from config import ROOT_KW, bwp_config
import abk_common


class IInstallBase(metaclass=ABCMeta):
    """Abstract class (mostly)"""
    os_type: abk_common.OsType = None  # type: ignore
    _shell_file_name: str = None  # type: ignore


    @property
    def shell_file_name(self) -> str:
        if self._shell_file_name == None:
            extention = ("sh", "ps1")[self.os_type == abk_common.OsType.WINDOWS_OS]
            self._shell_file_name = f"{abk_common.BWP_APP_NAME}.{extention}"
        return self._shell_file_name


    @abk_common.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        """Super class init"""
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(f"({__class__.__name__}) Initializing {self.os_type} installation environment ...")


    # @abk_common.function_trace
    # def install_python_packages(self) -> None:
    #     # TODO: 1. check whether pyenv is installed
    #     #   TODO: 1.1. if pyenv is installed, check what versions of python are installed
    #     #   TODO: 1.2. select the latest python 3 version
    #     #   TODO: 1.3. check pyenv-virtualenv is installed
    #     #       TODO: 1.3.1. if pyenv-virtualenv is installed create a new bingwallpaper ve if not available yet
    #     #       TODO: 1.3.2. set the local virtual env to be bingwallpaper
    #     #       TODO: 1.3.3. install all needed python packages into ve
    #     #   TODO: 1.4. if ve is not installed, install packages into the latest installed python version
    #     # TODO: 2. if pyenv is not installed, install packages into the whatever version is active (worst case)
    #     # TODO: 3. create shell script to change to abk bingwall paper project and execute the download within the directory
    #     # TODO: 4. use that script to create plist
    #     # TODO: 5. don't forget to unwind the shole logic in the uninstall script!
    #     # check pyenv is installed.
    #     pyenv_check = subprocess.run(["command", "-v", "pyenv"])
    #     python_check = subprocess.run(["python", "--version"])
    #     self._logger.debug(f"install_python_packages: {python_check=}")
    #     if pyenv_check != "":
    #         self._logger.debug(f"install_python_packages: {pyenv_check=}")
    # # if [[ $(command -v brew) == "" ]]; then
    # #     LCL_RESULT=$FALSE
    # #     echo "WARNING: Hombrew is not installed, please install with:"
    # #     echo "/usr/bin/ruby -e \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)\""
    # # fi


    @abstractmethod
    def setup_installation(self) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplemented



class InstallOnMacOS(IInstallBase):
    """Concrete class for installation on MacOS"""

    @abk_common.function_trace
    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = abk_common.OsType.MAC_OS
        super().__init__(logger)


    @abk_common.function_trace
    def setup_installation(self) -> None:
        """Setup instalaltion on MacOS"""
        time_to_exe: time = bwp_config.get(ROOT_KW.TIME_TO_FETCH.value, datetime.strptime("12:00:00", "%H:%M:%S").time())

        self._logger.debug(f"{time_to_exe.hour = }, {time_to_exe.minute = }, {time_to_exe.second = }")
        current_path = os.path.dirname(__file__)
        plist_lable = self._create_plist_file(time_to_exe, self.shell_file_name)
        plist_full_name = os.path.join(current_path, f"{plist_lable}.plist")
        dst_plist_name = self._create_plist_link(plist_full_name)
        self._stop_and_unload_bingwallpaper_job(dst_plist_name, plist_lable)
        self._load_and_start_bingwallpaper_job(dst_plist_name, plist_lable)


    @abk_common.function_trace
    def _create_plist_file(self, time_to_exe: time, script_name: str) -> str:
        """Creates plist file with info for MacOS to trigger scheduled job.
        Args:
            time_to_exe (time): time to execute the download of the bing image
            script_name (str): script name to execute
        Returns:
            Tuple[str, str]: plist lable and plist file name
        """
        self._logger.debug(f"{time_to_exe.hour=}, {time_to_exe.minute=}, {script_name=}")
        user_name = abk_common.get_user_name()
        current_path = os.path.dirname(__file__)
        full_script_name = os.path.join(current_path, script_name)
        self._logger.debug(f"{script_name = }")
        plist_label = f"com.{user_name}.{script_name}"
        self._logger.debug(f"{plist_label = }")
        full_plist_file_name = os.path.join(current_path, f"{plist_label}.plist")
        with open(full_plist_file_name, "w") as fh:
            lines_to_write = [
                '<?xml version="1.0" encoding="UTF-8"?>\n',
                '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n',
                '<plist version="1.0">\n',
                '<dict>\n',
                '    <key>Label</key>\n',
               f'    <string>{plist_label}</string>\n',
                '    <key>ProgramArguments</key>\n',
                '    <array>\n',
                '        <string>python3</string>\n',
               f'        <string>{full_script_name}</string>\n',
                '    </array>\n',
                '    <key>RunAtLoad</key>\n',
                '    <true/>\n',
                '    <key>StartCalendarInterval</key>\n',
                '    <dict>\n',
                '        <key>Hour</key>\n',
               f'        <integer>{time_to_exe.hour}</integer>\n',
                '        <key>Minute</key>\n',
               f'        <integer>{time_to_exe.minute}</integer>\n',
                '    </dict>\n',
                '</dict>\n',
                '</plist>\n',
            ]
            fh.writelines(lines_to_write)
        self._logger.debug(f"{plist_label=}")
        return plist_label


    @abk_common.function_trace
    def _create_plist_link(self, full_file_name: str) -> str:
        """Creates link in the $HOME/Library/LaunchAgent to the real locacion of the app script
        Args:
            full_file_name (str): full name + path of the app script
        Returns:
            str: full name (path + file name) of the link created
        """
        self._logger.debug(f"{full_file_name=}")
        file_name = os.path.basename(full_file_name)
        plist_install_dir = abk_common.get_home_dir()
        plist_install_dir = f"{plist_install_dir}/Library/LaunchAgents"
        abk_common.ensure_dir(plist_install_dir)
        dst_file_name = os.path.join(plist_install_dir, file_name)
        self._logger.info(f"src= {full_file_name}, dst= {dst_file_name}")
        abk_common.ensure_link_exists(full_file_name, dst_file_name)
        self._logger.debug(f"{dst_file_name=}")
        return dst_file_name


    @abk_common.function_trace
    def _stop_and_unload_bingwallpaper_job(self, plist_name: str, plist_lable: str) -> None:
        """Stops and unloads bing wall paper job.
           Executes until the end. Can also exit with first error occuring.
           This is an expected behaviour though.
        Args:
            plist_name (str): full name (path + file name) of the link of the plist file
            plist_lable (str): the plist lable
        """
        self._logger.debug(f"{plist_name=}, {plist_lable=}")

        cmd_list = []
        cmd_list.append(f"launchctl list | grep {plist_lable}")
        cmd_list.append(f"launchctl stop {plist_lable}")
        cmd_list.append(f"launchctl unload -w {plist_name}")

        try:
            for cmd in cmd_list:
                self._logger.info(f"about to execute command '{cmd}'")
                retCode = subprocess.check_call(cmd, shell=True)
                self._logger.info(f"command '{cmd}' succeeded, returned: {retCode}")
        except subprocess.CalledProcessError as e:
            self._logger.info(f"error: {e.returncode=}. It is expected though, since not all commands will execute successfully.")


    @abk_common.function_trace
    def _load_and_start_bingwallpaper_job(self, plist_name: str, plist_lable: str) -> None:
        """Loads and starts the scheduled job
        Args:
            plist_name (str): full name (path + file name) of the link of the plist file
            plist_lable (str): the plist lable
        """
        self._logger.debug(f"{plist_name=}, {plist_lable=}")

        cmd_list = []
        cmd_list.append(f"launchctl load -w {plist_name}")
        cmd_list.append(f"launchctl start {plist_lable}")

        try:
            for cmd in cmd_list:
                self._logger.info(f"about to execute command '{cmd}'")
                retCode = subprocess.check_call(cmd, shell=True)
                self._logger.info(f"command '{cmd}' succeeded, returned: {retCode}")
        except subprocess.CalledProcessError as e:
            self._logger.critical(f"ERROR: returned: {e.returncode}")
        except:
            self._logger.critical(f"ERROR: unknow")



class InstallOnLinux(IInstallBase):
    """Concrete class for installation on Linux"""

    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = abk_common.OsType.LINUX_OS
        super().__init__(logger)


    @abk_common.function_trace
    def setup_installation(self) -> None:
        """Setup instalaltion on Linux"""
        self._logger.info(f"{self.os_type.value} installation is not supported yet")



class InstallOnWindows(IInstallBase):
    """Concrete class for installation on Windows"""

    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = abk_common.OsType.WINDOWS_OS
        super().__init__(logger)


    @abk_common.function_trace
    def setup_installation(self) -> None:
        """Setup instalaltion on Windows"""
        # self._logger.debug(f"{time_to_exe.hour=}, {time_to_exe.minute=}, {app_name=}")
        self._logger.info(f"{self.os_type.value} installation is not supported yet")



@abk_common.function_trace
def bwp_install(install_logger: Union[logging.Logger, None] = None) -> None:
    exit_code = 0
    _logger = install_logger or logging.getLogger(__name__)
    try:
        if _platform in abk_common.OsPlatformType.PLATFORM_MAC.value:
            installation = InstallOnMacOS(logger=_logger)
        elif _platform in abk_common.OsPlatformType.PLATFORM_LINUX.value:
            installation = InstallOnLinux(logger=_logger)
        elif _platform in abk_common.OsPlatformType.PLATFORM_WINDOWS.value:
            installation = InstallOnWindows(logger=_logger)
        else:
            raise ValueError(f'ERROR: "{_platform}" is not supported')

        installation.setup_installation()
        # installation.install_python_packages()
        # installation.setup_installation()
        # installation.setup_installation(bwp_config[ROOT_KW.TIME_TO_FETCH.value], bwp_config[ROOT_KW.APP_NAME.value])
    except Exception as exception:
        _logger.error(f"{Fore.RED}ERROR: executing bingwallpaper")
        _logger.error(f"EXCEPTION: {exception}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    command_line_options = abk_common.CommandLineOptions()
    command_line_options.handle_options()
    install_logger = command_line_options._logger
    bwp_install(install_logger)

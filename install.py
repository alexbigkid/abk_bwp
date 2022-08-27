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
    3. schedule the job permanent job running at 8am or when logged in    Raises:
"""

import os
import logging
import logging.config
import subprocess
from abc import ABCMeta, abstractmethod
from enum import Enum
from datetime import time
from sys import platform as _platform
from typing import Tuple

from config import bwp_config
from abkPackage import abkCommon



class OsType(Enum):
    """OsType string representation"""
    MAC_OS = 'MacOS'
    LINUX_OS = 'Linux'
    WINDOWS_OS = 'Windows'



class IInstallBase(metaclass=ABCMeta):
    """Abstract class (mostly)"""
    os_type: OsType = None  # type: ignore

    @abkCommon.function_trace
    def __init__(self, logger:logging.Logger=None) -> None:  # type: ignore
        """Super class init"""
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(f'({__class__.__name__}) Initializing {self.os_type} installation environment ...')


    @abstractmethod
    def setup_installation(self, time_to_exe: time, app_name: str) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplemented



class InstallOnMacOS(IInstallBase):
    """Concrete class for installation on MacOS"""

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = OsType.MAC_OS
        super().__init__(logger)


    @abkCommon.function_trace
    def setup_installation(self, time_to_exe: time, app_name: str) -> None:
        """Setup instalaltion on MacOS
        Args:
            time_to_exe (time): time to execute the bing wall paper download
            app_name (str): application name
        """
        self._logger.debug(f'{time_to_exe.hour=}, {time_to_exe.minute=}, {app_name=}')
        full_name = self._link_python_script(app_name)
        script_name = os.path.basename(full_name)
        script_path = os.path.dirname(full_name)
        self._logger.info(f'{script_path=}, {script_name=}')
        (plist_lable, plist_name) = self._create_plist_file(time_to_exe, script_name)
        plist_full_name = os.path.join(script_path, plist_name)
        self._logger.info(f'{plist_full_name=}')
        dst_plist_name = self._create_plist_link(plist_full_name)
        self._stop_and_unload_bingwallpaper_job(dst_plist_name, plist_lable)
        self._load_and_start_bingwallpaper_job(dst_plist_name, plist_lable)


    @abkCommon.function_trace
    def _link_python_script(self, file_name: str) -> str:
        """Creates a link of the python app script in the $HOME/bin directory
        Args:
            file_name (str): file name to create link to
        Returns:
            str: name of the full path + name of the app python script
        """
        self._logger.debug(f'{file_name=}')
        bin_dir = os.path.join(abkCommon.GetHomeDir(), "bin")
        abkCommon.EnsureDir(bin_dir)
        curr_dir = abkCommon.GetParentDir(__file__)
        src = os.path.join(curr_dir, file_name)
        dst = os.path.join(bin_dir, file_name)
        abkCommon.EnsureLinkExists(src, dst)
        self._logger.debug(f'{src=}')
        return src


    @abkCommon.function_trace
    def _create_plist_file(self, time_to_exe: time, script_name: str) -> Tuple[str, str]:
        """Creates plist file with info for MacOS to trigger scheduled job.
        Args:
            time_to_exe (time): time to execute the download of the bing image
            script_name (str): script name to execute
        Returns:
            Tuple[str, str]: plist lable and plist file name
        """
        self._logger.debug(f'{time_to_exe.hour=}, {time_to_exe.minute=}, {script_name=}')
        user_name = abkCommon.GetUserName()
        plist_label = f'com.{user_name}.{script_name}'
        plist_name = f'{plist_label}.plist'
        with open(plist_name, "w") as fh:
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
               f'        <string>/Users/{user_name}/abkBin/{script_name}</string>\n',
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
        self._logger.debug(f'{plist_label=}, {plist_name=}')
        return (plist_label, plist_name)


    @abkCommon.function_trace
    def _create_plist_link(self, full_file_name: str) -> str:
        """Creates link in the $HOME/Library/LaunchAgent to the real locacion of the app script
        Args:
            full_file_name (str): full name + path of the app script
        Returns:
            str: full name (path + file name) of the link created
        """
        self._logger.debug(f'{full_file_name=}')
        file_name = os.path.basename(full_file_name)
        plist_install_dir = abkCommon.GetHomeDir()
        plist_install_dir = f'{plist_install_dir}/Library/LaunchAgents'
        abkCommon.EnsureDir(plist_install_dir)
        dst_file_name = os.path.join(plist_install_dir, file_name)
        self._logger.info(f'src= {full_file_name}, dst= {dst_file_name}')
        abkCommon.EnsureLinkExists(full_file_name, dst_file_name)
        self._logger.debug(f'{dst_file_name=}')
        return dst_file_name


    @abkCommon.function_trace
    def _stop_and_unload_bingwallpaper_job(self, plist_name: str, plist_lable: str) -> None:
        """Stops and unloads bing wall paper job.
           Executes until the end. Can also exit with first error occuring.
           This is an expected behaviour though.
        Args:
            plist_name (str): full name (path + file name) of the link of the plist file
            plist_lable (str): the plist lable
        """
        self._logger.debug(f'{plist_name=}, {plist_lable=}')

        cmd_list = []
        cmd_list.append(f'launchctl list | grep {plist_lable}')
        cmd_list.append(f'launchctl stop {plist_lable}')
        cmd_list.append(f'launchctl unload -w {plist_name}')

        try:
            for cmd in cmd_list:
                self._logger.info(f"about to execute command '{cmd}'")
                retCode = subprocess.check_call(cmd, shell=True)
                self._logger.info(f"command '{cmd}' succeeded, returned: {retCode}")
        except subprocess.CalledProcessError as e:
            self._logger.info(f'error: {e.returncode=}. It is expected though, since not all commands will execute successfully.')


    @abkCommon.function_trace
    def _load_and_start_bingwallpaper_job(self, plist_name: str, plist_lable: str) -> None:
        """Loads and starts the scheduled job
        Args:
            plist_name (str): full name (path + file name) of the link of the plist file
            plist_lable (str): the plist lable
        """
        self._logger.debug(f'{plist_name=}, {plist_lable=}')

        cmd_list = []
        cmd_list.append(f'launchctl load -w {plist_name}')
        cmd_list.append(f'launchctl start {plist_lable}')

        try:
            for cmd in cmd_list:
                self._logger.info(f"about to execute command '{cmd}'")
                retCode = subprocess.check_call(cmd, shell=True)
                self._logger.info(f"command '{cmd}' succeeded, returned: {retCode}")
        except subprocess.CalledProcessError as e:
            self._logger.critical(f'ERROR: returned: {e.returncode}')
        except:
            self._logger.critical(f'ERROR: unknow')



class InstallOnLinux(IInstallBase):
    """Concrete class for installation on Linux"""

    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = OsType.LINUX_OS
        super().__init__(logger)


    @abkCommon.function_trace
    def setup_installation(self, time_to_exe: time, app_name: str) -> None:
        """Setup instalaltion on Linux
        Args:
            time_to_exe (time): time to execute the bing wall paper download
            app_name (str): application name
        """
        self._logger.debug(f'{time_to_exe.hour=}, {time_to_exe.minute=}, {app_name=}')
        self._logger.info("Linux installation is not supported yet")



class InstallOnWindows(IInstallBase):
    """Concrete class for installation on Windows"""

    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = OsType.WINDOWS_OS
        super().__init__(logger)


    @abkCommon.function_trace
    def setup_installation(self, time_to_exe: time, app_name: str) -> None:
        """Setup instalaltion on Windows
        Args:
            time_to_exe (time): time to execute the bing wall paper download
            app_name (str): application name
        """
        self._logger.debug(f'{time_to_exe.hour=}, {time_to_exe.minute=}, {app_name=}')
        self._logger.info("Windows installation is not supported yet")



@abkCommon.function_trace
def main():
    platform_mac = frozenset({'darwin'})
    platform_linux = frozenset({'linux', 'linux2'})
    platform_windows = frozenset({'win32', 'win64'})

    command_line_options = abkCommon.CommandLineOptions()
    command_line_options.handle_options()
    main_logger = command_line_options._logger

    if _platform in platform_mac:
        installation = InstallOnMacOS(logger=main_logger)
    elif _platform in platform_linux:
        installation = InstallOnLinux(logger=main_logger)
    elif _platform in platform_windows:
        installation = InstallOnWindows(logger=main_logger)
    else:
        raise ValueError(f'ERROR: "{_platform}" is not supported')

    installation.setup_installation(bwp_config["time_to_fetch"], bwp_config["app_name"])



if __name__ == '__main__':
    main()

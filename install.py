# This script will:
# 1. create a link bingwallpaper.py in home_dir/abkBin directory to current dir
# 2. Platform dependant operation - create platfrom dependent environment
#   2.1. Mac
#       2.1.1. create a plist file for scheduled job in current directory
#       2.1.2. create a link in ~/Library/LaunchAgents/com.<userName>.bingwallpaper.py.list to the plist in current directory
#       2.1.3. stop, unload, load and start the job via plist file
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
import subprocess
from abc import ABCMeta, abstractmethod
from enum import Enum
from datetime import time
from sys import platform as _platform
from typing import Tuple

from config import bwp_config
from abkPackage import abkCommon



class OsType(Enum):
    MAC_OS = 'MacOS'
    LINUX_OS = 'Linux'
    WINDOWS_OS = 'Windows'



class IInstallOnOS(metaclass=ABCMeta):
    os_type: OsType = None  # type: ignore

    @abkCommon.function_trace
    def __init__(self, logger:logging.Logger=None) -> None:  # type: ignore
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(f'({__class__.__name__}) Initializing {self.os_type} installation environment ...')


    @abstractmethod
    def setup_installation(self, time_to_exe: time, app_name: str) -> None:
        raise NotImplemented



class InstallOnMacOS(IInstallOnOS):

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = OsType.MAC_OS
        super().__init__(logger)


    @abkCommon.function_trace
    def setup_installation(self, time_to_exe: time, app_name: str) -> None:
        self._logger.debug(f'{time_to_exe.hour=}, {time_to_exe.minute=}, {app_name=}')
        full_name = self.link_python_script(app_name)
        script_name = os.path.basename(full_name)
        script_path = os.path.dirname(full_name)
        self._logger.info(f'{script_path=}, {script_name=}')
        (plist_lable, plistName) = self.create_plist_file(time_to_exe, script_name)
        plist_full_name = os.path.join(script_path, plistName)
        self._logger.info(f'{plist_full_name=}')
        dst_plist_name = self.create_plist_link(plist_full_name)
        self.stop_and_unload_bingwallpaper_job(dst_plist_name, plist_lable)
        self.load_and_start_bingwallpaper_job(dst_plist_name, plist_lable)


    @abkCommon.function_trace
    def link_python_script(self, file_name: str) -> str:
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
    def create_plist_file(self, time_to_exe: time, script_name: str) -> Tuple[str, str]:
        self._logger.debug(f'{time_to_exe.hour=}, {time_to_exe.minute=}, {script_name=}')
        user_name = abkCommon.GetUserName()
        plist_label = f'com.{user_name}.{script_name}'
        plist_name = f'{plist_label}.plist'
        fh = open(plist_name, "w")
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
        fh.close()
        self._logger.debug(f'{plist_label=}, {plist_name=}')
        return (plist_label, plist_name)


    @abkCommon.function_trace
    def create_plist_link(self, full_file_name: str) -> str:
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
    def stop_and_unload_bingwallpaper_job(self, plist_name: str, plist_lable: str) -> None:
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
    def load_and_start_bingwallpaper_job(self, plist_name: str, plist_lable: str) -> None:
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



class InstallOnLinux(IInstallOnOS):

    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = OsType.LINUX_OS
        super().__init__(logger)


    @abkCommon.function_trace
    def setup_installation(self, time_to_exe: time, app_name: str) -> None:
        self._logger.debug(f'{time_to_exe.hour=}, {time_to_exe.minute=}, {app_name=}')
        self._logger.info("Linux installation is not supported yet")



class InstallOnWindows(IInstallOnOS):

    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = OsType.WINDOWS_OS
        super().__init__(logger)


    @abkCommon.function_trace
    def setup_installation(self, time_to_exe: time, app_name: str) -> None:
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

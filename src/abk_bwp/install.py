"""1. Creates a link bingwallpaper.py in home_dir/abkBin directory to current dir
2. Platform dependant operation - create platfrom dependent environment
    2.1. Mac
        2.1.1. create a plist file for scheduled job in current directory
        2.1.2. create a link in ~/Library/LaunchAgents/com.<userName>.bingwallpaper.py.list
               to the plist in current directory
        2.1.3. stop, unload, load and start the job via plist file
    2.2 Linux
        2.2.1. NOT READY YET
    2.3 Windows
        2.3.1. NOT READY YET
3. schedule the job permanent job running at 8am or when logged in.
"""  # noqa: D205, D208

import logging

# Standard lib imports
import os
import subprocess  # noqa: S404
import sys
from abc import ABCMeta, abstractmethod
from datetime import datetime, time
from sys import platform as _platform


# Third party imports
from colorama import Fore, Style


# local imports
from abk_bwp import abk_common, clo
from abk_bwp.config import ROOT_KW, bwp_config


class IInstallBase(metaclass=ABCMeta):
    """Abstract class (mostly)."""

    os_type: abk_common.OsType = None  # type: ignore
    _shell_file_name: str = None  # type: ignore

    @property
    def shell_file_name(self) -> str:
        """Returns the name of the shell file to be created for the installation."""
        if self._shell_file_name is None:
            extension = ("sh", "ps1")[self.os_type == abk_common.OsType.WINDOWS_OS]
            self._shell_file_name = f"{abk_common.BWP_APP_NAME}.{extension}"
        return self._shell_file_name

    @abk_common.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        """Super class init."""
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(f"({__class__.__name__}) Initializing {self.os_type} installation environment ...")

    @abstractmethod
    def setup_installation(self) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplementedError

    # @abk_common.function_trace
    # def install_python_packages(self) -> None:
    # TODO: 1. check whether pyenv is installed
    # TODO: 1.1. if pyenv is installed, check what versions of python are installed
    # TODO: 1.2. select the latest python 3 version
    # TODO: 1.3. check pyenv-virtualenv is installed
    # TODO: 1.3.1. if pyenv-virtualenv is installed create a new bingwallpaper ve if not available
    # TODO: 1.3.2. set the local virtual env to be bingwallpaper
    # TODO: 1.3.3. install all needed python packages into ve
    # TODO: 1.4. if ve is not installed, install packages to the latest installed python version
    # TODO: 2. if pyenv is not installed,install packages into the any active version (worst case)
    # TODO: 3. create shell script to change to abk bingwallpaper project
    #          and execute the download within the directory
    # TODO: 4. use that script to create plist
    # TODO: 5. don't forget to unwind the whole logic in the uninstall script!
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


class InstallOnMacOS(IInstallBase):
    """Concrete class for installation on MacOS."""

    @abk_common.function_trace
    def __init__(self, logger: logging.Logger) -> None:
        """Init install for MacOS.

        Args:
            logger: logger to use
        """
        self.os_type = abk_common.OsType.MAC_OS
        super().__init__(logger)

    @abk_common.function_trace
    def setup_installation(self) -> None:
        """Setup installation on MacOS."""
        time_to_exe: time = bwp_config.get(ROOT_KW.TIME_TO_FETCH.value, datetime.strptime("12:00:00", "%H:%M:%S").time())

        self._logger.debug(f"{time_to_exe.hour = }, {time_to_exe.minute = }, {time_to_exe.second = }")
        current_path = os.path.dirname(__file__)
        plist_label = self._create_plist_file(time_to_exe, self.shell_file_name)
        # plist_label = self._create_plist_file(time_to_exe, "bingwallpaper.py")
        plist_full_name = os.path.join(current_path, f"{plist_label}.plist")
        dst_plist_name = self._create_plist_link(plist_full_name)
        self._stop_and_unload_bingwallpaper_job(dst_plist_name, plist_label)
        self._load_and_start_bingwallpaper_job(dst_plist_name, plist_label)

    @abk_common.function_trace
    def _create_plist_file(self, time_to_exe: time, script_name: str) -> str:
        """Creates plist file with info for MacOS to trigger scheduled job.

        Args:
            time_to_exe (time): time to execute the download of the bing image
            script_name (str): script name to execute
        Returns:
            Tuple[str, str]: plist label and plist file name
        """
        self._logger.debug(f"{time_to_exe.hour=}, {time_to_exe.minute=}, {script_name=}")
        user_name = abk_common.get_user_name()
        current_path = os.path.dirname(__file__)
        full_script_name = os.path.join(current_path, script_name)
        self._logger.debug(f"{script_name = }")
        plist_label = f"com.{user_name}.{script_name}"
        self._logger.debug(f"{plist_label = }")
        full_plist_file_name = os.path.join(current_path, f"{plist_label}.plist")

        # Check if retry mechanism is enabled
        from abk_bwp.config import RETRY_KW, bwp_config

        retry_config = bwp_config.get(RETRY_KW.RETRY.value, {})
        retry_enabled = retry_config.get(RETRY_KW.ENABLED.value, True)

        with open(full_plist_file_name, "w") as fh:
            lines_to_write = [
                '<?xml version="1.0" encoding="UTF-8"?>\n',
                '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n',
                '<plist version="1.0">\n',
                "<dict>\n",
                "    <key>Label</key>\n",
                f"    <string>{plist_label}</string>\n",
                "    <key>WorkingDirectory</key>\n",
                f"    <string>{current_path}</string>\n",
                "    <key>ProgramArguments</key>\n",
                "    <array>\n",
                "        <string>bash</string>\n",
                f"        <string>{full_script_name}</string>\n",
                "    </array>\n",
                "    <key>RunAtLoad</key>\n",
                "    <true/>\n",
            ]

            if retry_enabled:
                # Use hourly interval (3600 seconds = 1 hour)
                lines_to_write.extend(["    <key>StartInterval</key>\n", "    <integer>3600</integer>\n"])
                self._logger.info("Creating hourly plist job (retry enabled): every hour")
            else:
                # Use daily schedule with specific time
                lines_to_write.extend(
                    [
                        "    <key>StartInterval</key>\n",
                        "    <integer>86400</integer>\n",  # 24 hours
                        "    <key>StartCalendarInterval</key>\n",
                        "    <dict>\n",
                        "        <key>Hour</key>\n",
                        f"        <integer>{time_to_exe.hour}</integer>\n",
                        "        <key>Minute</key>\n",
                        f"        <integer>{time_to_exe.minute}</integer>\n",
                        "    </dict>\n",
                    ]
                )
                self._logger.info(f"Creating daily plist job (retry disabled): {time_to_exe.hour}:{time_to_exe.minute}")

            lines_to_write.extend(
                [
                    "    <!--\n    <key>StandardErrorPath</key>\n",
                    f"    <string>/tmp/{plist_label}.stderr</string>\n",
                    "    <key>StandardOutPath</key>\n",
                    f"    <string>/tmp/{plist_label}.stdout</string>\n",
                    "    -->\n</dict>\n",
                    "</plist>\n",
                ]
            )

            fh.writelines(lines_to_write)
        return plist_label

    @abk_common.function_trace
    def _create_plist_link(self, full_file_name: str) -> str:
        """Creates link in the $HOME/Library/LaunchAgent to the real location of the app script.

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
    def _stop_and_unload_bingwallpaper_job(self, plist_name: str, plist_label: str) -> None:
        """Stops and unloads bing wall paper job. Executes until the end.

           Can also exit with first error occurring. This is an expected behavior though.

        Args:
            plist_name (str): full name (path + file name) of the link of the plist file
            plist_label (str): the plist label
        """
        self._logger.debug(f"{plist_name=}, {plist_label=}")

        cmd_list = []
        cmd_list.append(f"launchctl list | grep {plist_label}")
        cmd_list.append(f"launchctl stop {plist_label}")
        cmd_list.append(f"launchctl unload -w {plist_name}")

        try:
            for cmd in cmd_list:
                self._logger.info(f"about to execute command '{cmd}'")
                ret_code = subprocess.check_call(cmd, shell=True)  # noqa: S602
                self._logger.info(f"command '{cmd}' succeeded, returned: {ret_code}")
        except subprocess.CalledProcessError as e:
            self._logger.info(f"error: {e.returncode=}. It is expected though, not all cmds exec successfully.")

    @abk_common.function_trace
    def _load_and_start_bingwallpaper_job(self, plist_name: str, plist_label: str) -> None:
        """Loads and starts the scheduled job.

        Args:
            plist_name (str): full name (path + file name) of the link of the plist file
            plist_label (str): the plist label
        """
        self._logger.debug(f"{plist_name=}, {plist_label=}")

        cmd_list = []
        cmd_list.append(f"launchctl load -w {plist_name}")
        cmd_list.append(f"launchctl start {plist_label}")

        try:
            for cmd in cmd_list:
                self._logger.info(f"about to execute command '{cmd}'")
                ret_code = subprocess.check_call(cmd, shell=True)  # noqa: S602
                self._logger.info(f"command '{cmd}' succeeded, returned: {ret_code}")
        except subprocess.CalledProcessError as e:
            self._logger.critical(f"ERROR: returned: {e.returncode}")
        except Exception:
            self._logger.critical("ERROR: unknown")


class InstallOnLinux(IInstallBase):
    """Concrete class for installation on Linux."""

    def __init__(self, logger: logging.Logger) -> None:
        """Init install on Linux class.

        Args:
            logger: logger
        """
        self.os_type = abk_common.OsType.LINUX_OS
        super().__init__(logger)

    @abk_common.function_trace
    def setup_installation(self) -> None:
        """Setup installation on Linux."""
        time_to_exe: time = bwp_config.get(ROOT_KW.TIME_TO_FETCH.value, datetime.strptime("12:00:00", "%H:%M:%S").time())

        self._logger.debug(f"{time_to_exe.hour = }, {time_to_exe.minute = }, {time_to_exe.second = }")

        # Create cron job for Linux automation
        self._create_cron_job(time_to_exe, self.shell_file_name)
        self._logger.info(f"Linux cron job created for BWP automation at {time_to_exe}")

    @abk_common.function_trace
    def _create_cron_job(self, time_to_exe: time, script_name: str) -> None:
        """Creates cron job for Linux automation.

        Args:
            time_to_exe (time): time to execute the download of the bing image
            script_name (str): script name to execute
        """
        current_path = os.path.dirname(__file__)
        full_script_name = os.path.join(current_path, script_name)

        # Check if retry mechanism is enabled
        from abk_bwp.config import RETRY_KW, bwp_config

        retry_config = bwp_config.get(RETRY_KW.RETRY.value, {})
        retry_enabled = retry_config.get(RETRY_KW.ENABLED.value, True)

        if retry_enabled:
            # Create hourly cron entry: 0 * * * * command (every hour at minute 0)
            cron_entry = f"0 * * * * {full_script_name}"
            self._logger.info(f"Creating hourly cron job (retry enabled): {cron_entry}")
        else:
            # Create daily cron entry: minute hour * * * command
            cron_entry = f"{time_to_exe.minute} {time_to_exe.hour} * * * {full_script_name}"
            self._logger.info(f"Creating daily cron job (retry disabled): {cron_entry}")

        # Get current crontab
        try:
            result = subprocess.run(
                ["crontab", "-l"],  # noqa: S607
                capture_output=True,
                text=True,
                check=False,
            )
            current_crontab = result.stdout if result.returncode == 0 else ""
        except Exception as exc:
            self._logger.warning(f"Could not read existing crontab: {exc}")
            current_crontab = ""

        # Check if BWP entry already exists
        if script_name in current_crontab:
            self._logger.info("BWP cron job already exists, updating...")
            # Remove existing BWP entries
            lines = current_crontab.split("\n")
            filtered_lines = [line for line in lines if script_name not in line]
            current_crontab = "\n".join(filtered_lines).strip()

        # Add new cron entry (ensure it ends with newline for crontab compatibility)
        new_crontab = current_crontab + "\n" + cron_entry + "\n" if current_crontab else cron_entry + "\n"

        # Install new crontab
        try:
            subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)  # noqa: S607
            self._logger.info(f"Cron job installed: {cron_entry}")
        except subprocess.CalledProcessError as exc:
            self._logger.error(f"Failed to install cron job: {exc}")
            raise exc


class InstallOnWindows(IInstallBase):
    """Concrete class for installation on Windows."""

    def __init__(self, logger: logging.Logger) -> None:
        """Init install on Windows class.

        Args:
            logger: logger
        """
        self.os_type = abk_common.OsType.WINDOWS_OS
        super().__init__(logger)

    @abk_common.function_trace
    def setup_installation(self) -> None:
        """Setup installation on Windows."""
        # self._logger.debug(f"{time_to_exe.hour=}, {time_to_exe.minute=}, {app_name=}")
        self._logger.info(f"{self.os_type.value} installation is not supported yet")


@abk_common.function_trace
def bwp_install(install_logger: logging.Logger | None = None) -> None:
    """BingWallPaper install.

    Args:
        install_logger: passed in logger. Defaults to None.

    Raises:
        ValueError: not supported OS
        Exception: any other exception
    """
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
        # installation.setup_installation(bwp_config[ROOT_KW.TIME_TO_FETCH.value],
        #                                 bwp_config[ROOT_KW.APP_NAME.value])
    except Exception as exception:
        _logger.error(f"{Fore.RED}ERROR: executing bingwallpaper")
        _logger.error(f"EXCEPTION: {exception}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    command_line_options = clo.CommandLineOptions()
    command_line_options.handle_options()
    install_logger = command_line_options.logger
    bwp_install(install_logger)

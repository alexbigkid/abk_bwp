"""Clo module handles all parameters passed in to the python script."""

# Standard library imports
import logging
from enum import Enum
from argparse import ArgumentParser, Namespace
import sys

# Third party imports

# Local application imports
from abk_bwp.constants import CONST
from abk_bwp.logger_manager import LoggerManager


class LoggerType(Enum):
    """Logger type."""

    CONSOLE_LOGGER = "consoleLogger"
    FILE_LOGGER = "fileLogger"


class CommandLineOptions:
    """CommandLineOptions module handles all parameters passed in to the python script."""

    _args: list = None  # type: ignore
    options: Namespace = None  # type: ignore
    logger: logging.Logger = None  # type: ignore

    def __init__(self, args: list = None, options: Namespace = None):  # type: ignore
        """Init for Command Line Options."""
        self._args = args
        self.options = options

    def handle_options(self) -> None:
        """Handles user specified options and arguments."""
        parser = ArgumentParser(prog="bwp", description="Downloads daily Bing images and sets them as desktop wallpaper")
        parser.add_argument("-a", "--about", action="store_true", help="Show detailed project metadata")
        parser.add_argument(
            "-d", "--desktop_auto_update", choices=["enable", "disable"], help="[enable, disable] desktop auto update"
        )
        parser.add_argument("-f", "--frame_tv", choices=["enable", "disable"], help="[enable, disable] Frame TV auto update")
        parser.add_argument(
            "-i", "--img_auto_fetch", choices=["enable", "disable"], help="[enable, disable] automated image download scheduling"
        )
        parser.add_argument(
            "-u", "--usb_mode", choices=["enable", "disable"], help="[enable, disable] Frame TV USB mass storage mode"
        )
        parser.add_argument("-l", "--log_into_file", action="store_true", help="Log into logs/bingwallpaper.log")
        parser.add_argument("-q", "--quiet", action="store_true", help="Suppresses all logs")
        parser.add_argument("-v", "--version", action="store_true", help="Show version info and exit")
        self.options = parser.parse_args()

        if self.options.version:
            print(f"{CONST.NAME} version: {CONST.VERSION}")
            sys.exit(0)

        if self.options.about:
            print(f"Name       : {CONST.NAME}")
            print(f"Version    : {CONST.VERSION}")
            print(f"License    : {CONST.LICENSE}")
            print(f"Keywords   : {', '.join(CONST.KEYWORDS)}")
            print("Authors:")
            for a in CONST.AUTHORS:
                print(f"  - {a.get('name', '?')} <{a.get('email', '?')}>")
            print("Maintainers:")
            for m in CONST.MAINTAINERS:
                print(f"  - {m.get('name', '?')} <{m.get('email', '?')}>")
            sys.exit(0)

        LoggerManager().configure(log_into_file=self.options.log_into_file, quiet=self.options.quiet)
        self.logger = LoggerManager().get_logger(__name__)
        self.logger.info(f"{self.options=}")
        self.logger.info(f"{self._args=}")
        self.logger.info(f"{self.options.log_into_file=}")
        self.logger.info(f"{self.options.quiet=}")
        self.logger.info(f"{CONST.VERSION=}")

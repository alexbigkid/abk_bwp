"""Clo module handles all parameters passed in to the python script."""

# Standard library imports
import logging
import logging.config
from enum import Enum
from argparse import ArgumentParser, Namespace

# Third party imports
from pathlib import Path
import sys
import yaml

# Local application imports
from abk_bwp.constants import CONST


class LoggerType(Enum):
    """Logger type."""

    CONSOLE_LOGGER = "consoleLogger"
    FILE_LOGGER = "fileLogger"


class CommandLineOptions(object):
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
        usage_string = "usage: %prog [options]"
        parser = ArgumentParser(
            prog="bwp",
            description="Downloads daily Bing images and sets them as desktop wallpaper",
        )
        parser.add_argument("--version", action="store_true", help="Show version info and exit")
        parser.add_argument("--about", action="store_true", help="Show detailed project metadata")
        parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
        parser.add_argument(
            "-l", "--log_into_file", action="store_true", help="Log into file instead of console"
        )
        parser.add_argument(
            "-c",
            "--config_log_file",
            default="logging.yaml",
            help="Path to logging config YAML file",
        )
        parser.add_argument(
            "-d",
            "--desktop_auto_update",
            choices=["enable", "disable"],
            help="[enable, disable] desktop auto update",
        )
        parser.add_argument(
            "-f",
            "--frame_tv",
            choices=["enable", "disable"],
            help="[enable, disable] Frame TV auto update",
        )
        self.options = parser.parse_args()

        self._setup_logging()
        self.logger.info(f"{self.options=}")
        self.logger.info(f"{self._args=}")
        self.logger.info(f"{self.options.verbose=}")
        self.logger.info(f"{self.options.log_into_file=}")
        self.logger.info(f"{CONST.VERSION=}")

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

    def _find_project_root(self, start=Path.cwd()) -> Path:
        for parent in [start, *start.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        raise FileNotFoundError("pyproject.toml not found")

    def _setup_logging(self):
        try:
            root = self._find_project_root()
            config_path = root / self.options.config_log_file
            with config_path.open("r", encoding="utf-8") as stream:
                config_yaml = yaml.load(stream, Loader=yaml.FullLoader)
                logging.config.dictConfig(config_yaml)
                logger_name = "fileLogger" if self.options.log_into_file else "consoleLogger"
                self.logger = logging.getLogger(logger_name)
                self.logger.disabled = not self.options.verbose
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.options.config_log_file} does not exist.")
        except Exception as e:
            print(f"Logging disabled due to error: {e}")
            self.logger = logging.getLogger(__name__)
            self.logger.disabled = True

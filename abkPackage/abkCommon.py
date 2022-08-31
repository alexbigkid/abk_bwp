# Standard library imports
import errno
import getpass
import json
import logging
import logging.config
import os
import timeit
from enum import Enum
from optparse import OptionParser, Values

# Third party imports
import yaml

# Local application imports
from _version import __version__
from colorama import Fore, Style

logger = logging.getLogger(__name__)


class OsType(Enum):
    """OsType string representation"""

    MAC_OS = "MacOS"
    LINUX_OS = "Linux"
    WINDOWS_OS = "Windows"


class OsPlatformType(Enum):
    PLATFORM_MAC = frozenset({"darwin"})
    PLATFORM_LINUX = frozenset({"linux", "linux2"})
    PLATFORM_WINDOWS = frozenset({"win32", "win64"})


class LoggerType(Enum):
    CONSOLE_LOGGER = "consoleLogger"
    FILE_LOGGER = "fileLogger"


def function_trace(original_function):
    """Decorator function to help to trace function call entry and exit
    Args:
        original_function (_type_): function above which the decorater is defined
    """

    def function_wrapper(*args, **kwargs):
        _logger = logging.getLogger(original_function.__name__)
        _logger.debug(f"{Fore.YELLOW}-> {original_function.__name__}{Style.RESET_ALL}")
        result = original_function(*args, **kwargs)
        _logger.debug(f"{Fore.YELLOW}<- {original_function.__name__}{Style.RESET_ALL}\n")
        return result

    return function_wrapper


def get_user_name():
    return getpass.getuser()


@function_trace
def get_home_dir() -> str:
    homeDir = os.environ["HOME"]
    logger.info(f"{homeDir=}")
    return homeDir


def get_current_dir(fileName) -> str:
    return os.path.dirname(os.path.realpath(fileName))


def get_parent_dir(fileName) -> str:
    return os.path.dirname(os.path.dirname(fileName))


@function_trace
def ensure_dir(dirName):
    logger.debug(f"{dirName=}")
    if not os.path.exists(dirName):
        try:
            os.makedirs(dirName)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise


# @function_trace
# def read_relative_link(link_name: str) -> str:
#     print(f"{link_name=}")
#     link_target = ""
#     if os.path.islink(link_name):
#         link_target = os.readlink(link_name)
#         relative_path = os.path.abspath(os.path.dirname(link_name))
#         print(f"ABK:read_link: {relative_path=}")
#     print(f"ABK:read_link: {link_target=}")
#     return link_target


@function_trace
def ensure_link_exists(src: str, dst: str) -> None:
    logger.debug(f"{src=}, {dst=}")
    if not os.path.islink(dst):
        logger.info(f"creating link {dst=} to {src=}")
        try:
            os.symlink(src, dst)
            logger.info(f"created link {dst=} to {src=}")
        except OSError as error:
            if error.errno != errno.EEXIST:
                logger.error(f"create link failed with error = {error.errno}")
                raise
    else:
        logger.info(f"link {dst=} exists, do nothing")


@function_trace
def remove_link(fileName: str) -> None:
    logger.debug(f"{fileName=}")
    if os.path.islink(fileName):
        try:
            os.unlink(fileName)
            logger.info(f"deleted link {fileName}")
        except OSError as error:
            logger.error(f"failed to delete link {fileName}, with error={error.errno}")
            pass
    else:
        logger.info(f"link {fileName} does not exist, do nothing")


@function_trace
def delete_dir(dir2delete):
    logger.debug(f"{dir2delete=}")
    if os.path.isdir(dir2delete):
        if len(os.listdir(dir2delete)) == 0:
            try:
                os.rmdir(dir2delete)
                logger.info(f"deleted dir {dir2delete}")
            except OSError as ex:
                if ex.errno == errno.ENOTEMPTY:
                    logger.error(f"directory {dir2delete} is not empty")
        else:
            logger.debug(f"dir {dir2delete} is not empty")
            for fileName in os.listdir(dir2delete):
                logger.debug(f"{fileName=}")


class PerformanceTimer(object):
    def __init__(self, timer_name: str, logger: logging.Logger):
        self._timer_name = timer_name
        self._logger = logger

    def __enter__(self):
        self.start = timeit.default_timer()

    def __exit__(self, exc_type, exc_value, traceback):
        time_took = (timeit.default_timer() - self.start) * 1000.0
        self._logger.info(f"Executing {self._timer_name} took {str(time_took)} ms")


class CommandLineOptions(object):
    """CommandLineOptions module handles all parameters passed in to the python script"""

    _args: list = None  # type: ignore
    options: Values = None  # type: ignore
    _logger: logging.Logger = None  # type: ignore

    def __init__(self, args: list = None, options: Values = None):  # type: ignore
        self._args = args
        self.options = options

    def handle_options(self) -> None:
        """Handles user specified options and arguments"""
        usage_string = "usage: %prog [options]"
        version_string = f"%prog version: {Fore.GREEN}{__version__}{Style.RESET_ALL}"
        parser = OptionParser(usage=usage_string, version=version_string)
        parser.add_option(
            "-v",
            "--verbose",
            action="store_true",
            dest="verbose",
            default=False,
            help="verbose execution",
        )
        parser.add_option(
            "-l",
            "--log_into_file",
            action="store_true",
            dest="log_into_file",
            default=False,
            help="log into file bingwallpaper.log if True, otherwise log into console",
        )
        parser.add_option(
            "-c",
            "--config_log_file",
            action="store",
            dest="config_log_file",
            default="./logging.yaml",
            help="config file for logging",
        )
        (self.options, self._args) = parser.parse_args()

        if len(self._args) != 0:
            raise ValueError(f"{len(self._args)} is wrong number of args, should be 0")
        self._setup_logging()
        self._logger.info(f"{self.options=}")
        self._logger.info(f"{self._args=}")
        self._logger.info(f"{self.options.verbose=}")
        self._logger.info(f"{self.options.log_into_file=}")
        self._logger.info(f"{__version__=}")

    def _setup_logging(self) -> None:
        try:
            with open(self.options.config_log_file, "r") as stream:
                config_yaml = yaml.load(stream, Loader=yaml.FullLoader)
                logging.config.dictConfig(config_yaml)
                logger_type = (LoggerType.CONSOLE_LOGGER.value, LoggerType.FILE_LOGGER.value)[self.options.log_into_file]
                self._logger = logging.getLogger(logger_type)
                self._logger.disabled = self.options.verbose == False
        except ValueError as ve:
            raise ValueError(f"{self.options.config_log_file} is not a valid yaml format")
        except IOError:
            raise IOError(f"{self.options.config_log_file} does not exist.")
        self._logger.debug(f"{logger_type=}")


if __name__ == "__main__":
    raise Exception("This module should not be executed directly. Only for imports")

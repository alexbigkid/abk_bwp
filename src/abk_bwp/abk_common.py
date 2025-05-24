"""Common functionality."""

# Standard library imports
import errno
import getpass
import json
import logging
import os
import timeit
from enum import Enum

# Third party imports
from colorama import Fore, Style

# Local application imports


BWP_MAIN_FILE_NAME = "abk_config.py"
BWP_APP_NAME = "bingwallpaper"

logger = logging.getLogger(__name__)


class OsType(Enum):
    """OsType string representation."""

    MAC_OS = "MacOS"
    LINUX_OS = "Linux"
    WINDOWS_OS = "Windows"


class OsPlatformType(Enum):
    """OsPlatformType."""

    PLATFORM_MAC = frozenset({"darwin"})
    PLATFORM_LINUX = frozenset({"linux", "linux2"})
    PLATFORM_WINDOWS = frozenset({"win32", "win64"})


def function_trace(original_function):
    """Decorator function to help to trace function call entry and exit.

    Args:
        original_function (_type_): function above which the decorator is defined
    """

    def function_wrapper(*args, **kwargs):
        _logger = logging.getLogger(original_function.__name__)
        _logger.debug(f"{Fore.YELLOW}-> {original_function.__name__}{Style.RESET_ALL}")
        result = original_function(*args, **kwargs)
        _logger.debug(f"{Fore.YELLOW}<- {original_function.__name__}{Style.RESET_ALL}\n")
        return result

    return function_wrapper


def get_user_name():
    """Gets user name.

    Returns:
        str: user name
    """
    return getpass.getuser()


@function_trace
def get_home_dir() -> str:
    """Gets home directory.

    Returns:
        str: current directory
    """
    home_dir = os.environ["HOME"]
    logger.info(f"{home_dir=}")
    return home_dir


def get_current_dir(file_name: str) -> str:
    """Get current directory.

    Args:
        file_name (str): file name
    Returns:
        str: current directory
    """
    return os.path.dirname(os.path.realpath(file_name))


def get_parent_dir(file_name: str) -> str:
    """Gets parent directory.

    Args:
        file_name (str): file name
    Returns:
        str: dir name
    """
    return os.path.dirname(os.path.dirname(file_name))


@function_trace
def ensure_dir(dir_name: str):
    """Ensures directory exist.

    Args:
        dir_name (str): name of directory to ensure it exist
    """
    logger.debug(f"{dir_name=}")
    if not os.path.exists(dir_name):
        try:
            os.makedirs(dir_name)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise


@function_trace
def ensure_link_exists(src: str, dst: str) -> None:
    """Ensures link exists.

    Args:
        src (str): source of the link
        dst (str): destination of the link
    """
    logger.debug(f"{src=}, {dst=}")
    if not os.path.islink(dst):
        logger.info(f"creating link {dst=} to {src=}")
        try:
            os.symlink(src, dst)
            logger.info(f"created link {dst=} to {src=}")
        except OSError as error:
            if error.errno != errno.EEXIST:
                logger.error(
                    f"ERROR:ensure_link_exists: create link failed with error = {error.errno}"
                )
                raise
    else:
        logger.info(f"link {dst=} exists, do nothing")


@function_trace
def remove_link(fileName: str) -> None:
    """Remove link.

    Args:
        fileName (str): file name to create link for
    """
    logger.debug(f"{fileName=}")
    if os.path.islink(fileName):
        try:
            os.unlink(fileName)
            logger.info(f"deleted link {fileName}")
        except OSError as error:
            logger.error(
                f"ERROR:remove_link: failed to delete link {fileName}, with error={error.errno}"
            )
            pass
    else:
        logger.info(f"link {fileName} does not exist, do nothing")


@function_trace
def delete_dir(dir_to_delete: str) -> None:
    """Deletes directory.

    Args:
        dir_to_delete (str): directory to delete
    """
    logger.debug(f"{dir_to_delete=}")
    if os.path.isdir(dir_to_delete):
        if len(os.listdir(dir_to_delete)) == 0:
            try:
                os.rmdir(dir_to_delete)
                logger.info(f"deleted dir {dir_to_delete}")
            except OSError as ex:
                if ex.errno == errno.ENOTEMPTY:
                    logger.error(f"ERROR:delete_dir: directory {dir_to_delete} is not empty")
        else:
            logger.debug(f"dir {dir_to_delete} is not empty")
            for fileName in os.listdir(dir_to_delete):
                logger.debug(f"{fileName=}")


@function_trace
def delete_file(file_to_delete: str) -> None:
    """Deletes file.

    Args:
        file_to_delete (str): file to delete
    """
    logger.debug(f"{file_to_delete=}")
    try:
        if os.path.exists(file_to_delete) and os.path.isfile(file_to_delete):
            os.remove(file_to_delete)
    except OSError as exp:
        logger.error(f"ERROR:delete_file: {exp=}, deleting file: {file_to_delete}")


def read_json_file(json_file_name: str) -> dict:
    """Reads JSON file.

    Args:
        json_file_name (str): JSON file name
    Returns:
        dict: dictionary of read JSON file
    """
    json_data: dict = {}
    if os.path.exists(json_file_name) and os.path.isfile(json_file_name):
        try:
            with open(json_file_name) as fh:
                json_data = json.load(fh)
        except Exception as exp:
            logger.error(f"ERROR:read_json_file: {exp=} opening and reading json file")
    return json_data


class PerformanceTimer:
    """Performance Times class."""

    def __init__(self, timer_name: str, pt_logger: logging.Logger):
        """Init for performance timer."""
        self._timer_name = timer_name
        self._logger = pt_logger or logging.getLogger(__name__)

    def __enter__(self):
        """Enter for performance timer."""
        self.start = timeit.default_timer()

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit for performance timer."""
        time_took = (timeit.default_timer() - self.start) * 1000.0
        self._logger.info(f"Executing {self._timer_name} took {str(time_took)} ms")


if __name__ == "__main__":
    raise Exception(f"{__file__}: This module should not be executed directly. Only for imports")

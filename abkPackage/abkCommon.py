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

import tomli
# Third party imports
import yaml
# Local application imports
from _version import __version__
from colorama import Fore, Style

logger = logging.getLogger(__name__)


class LoggerType(Enum):
    CONSOLE_LOGGER = 'consoleLogger'
    FILE_LOGGER = 'fileLogger'


class ConfigFileType(Enum):
    JSON = "json"
    TOML = "toml"


def function_trace(original_function):
    """Decorator function to help to trace function call entry and exit
    Args:
        original_function (_type_): function above which the decorater is defined
    """
    def function_wrapper(*args, **kwargs):
        _logger = logging.getLogger(original_function.__name__)
        _logger.debug(f'{Fore.YELLOW}-> {original_function.__name__}{Style.RESET_ALL}')
        result = original_function(*args, **kwargs)
        _logger.debug(f'{Fore.YELLOW}<- {original_function.__name__}{Style.RESET_ALL}\n')
        return result
    return function_wrapper


@function_trace
def readConfigFile(config_file:str) -> dict:
    """Reads configuration file in toml or json format
    Args:
        config_file (str): file name
    Raises:
        ValueError: throws error if the config file format is not supported
        FileNotFoundError: throw an error when file does not exist
    Returns:
        dict: with configuration data
    """
    logger.debug(f'{config_file=}')
    _, file_ext = os.path.splitext(config_file)
    if (file_extention := file_ext[1:]) == ConfigFileType.TOML:
        with open(config_file, mode="rb") as file_handle:
            config = tomli.load(file_handle)
    elif file_extention == ConfigFileType.JSON:
        with open(config_file) as file_handle:
            config = json.load(file_handle)
    else:
        raise ValueError(f'Unsupported Config File Format: {file_extention}. Supported are: {ConfigFileType.__members__.values()}')
    logger.debug(f'{config=}')
    return config


def GetUserName():
    return getpass.getuser()


def GetHomeDir():
    logger.debug("-> GetHomeDir")
    homeDir = os.environ['HOME']
    logger.info("homeDir = %s", homeDir)
    logger.debug("<- GetHomeDir")
    return homeDir


def GetCurrentDir(fileName):
    return os.path.dirname(os.path.realpath(fileName))


def GetParentDir(fileName):
    return os.path.dirname(os.path.dirname(fileName))


def EnsureDir(dirName):
    logger.debug("-> EnsureDir(%s)", dirName)
    if not os.path.exists(dirName):
        try:
            os.makedirs(dirName)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
    logger.debug("<- EnsureDir")


def EnsureLinkExists(src, dst):
    logger.debug("-> EnsureLinkExists(%s, %s)", src, dst)
    if not os.path.islink(dst):
        logger.info("creating link %s to %s" % (dst, src))
        try:
            os.symlink(src, dst)
            logger.info("created link %s to %s" % (dst, src))
        except OSError as error:
            if error.errno != errno.EEXIST:
                logger.error("create link failed with error =%d", error.errno)
                raise
    else:
        logger.info("link %s exists, do nothing" % (dst) )
    logger.debug("<- EnsureLinkExists")


def RemoveLink(fileName):
    logger.debug("-> RemoveLink(fileName=%s)", fileName)
    if os.path.islink(fileName):
        try:
            os.unlink(fileName)
            logger.info("deleted link %s", fileName )
        except OSError as error:
            logger.error("failed to delete link %s, with error=%d", fileName, error.errno)
            pass
    else:
        logger.info("link %s does not exist, do nothing", fileName )
    logger.debug("<- RemoveLink")


def DeleteDir(dir2delete):
    logger.debug("-> DeleteDir(dir2delete=%s)", dir2delete)
    if os.path.isdir(dir2delete):
        if len(os.listdir(dir2delete)) == 0:
            try:
                os.rmdir(dir2delete)
                logger.info("deleted dir %s", dir2delete)
            except OSError as ex:
                if ex.errno == errno.ENOTEMPTY:
                    logger.error("directory %s is not empty", dir2delete)
        else:
            logger.debug("dir %s is not empty", dir2delete)
            for fileName in os.listdir(dir2delete):
                logger.debug("file=%s", fileName)
    logger.debug("<- DeleteDir")



class PerformanceTimer(object):
    def __init__(self, timer_name:str, logger:logging.Logger):
        self._timer_name = timer_name
        self._logger = logger
    def __enter__(self):
        self.start = timeit.default_timer()
    def __exit__(self, exc_type, exc_value, traceback):
        time_took = (timeit.default_timer() - self.start) * 1000.0
        self._logger.info('Executing {} took {} ms'.format(self._timer_name, str(time_took)))



class CommandLineOptions(object):
    """CommandLineOptions module handles all parameters passed in to the python script"""
    _args:list[str] = None
    options:Values = None
    _logger:logging.Logger = None

    def __init__(self, args:list[str]=None, options:Values=None):
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
            help="verbose execution"
        )
        parser.add_option(
            "-l",
            "--log_into_file",
            action="store_true",
            dest="log_into_file",
            default=False,
            help="log into file bingwallpaper.log if True, otherwise log into console"
        )
        parser.add_option(
            "-c",
            "--config_log_file",
            action="store",
            dest="config_log_file",
            default="./logging.yaml",
            help="config file for logging"
        )
        (self.options, self._args) = parser.parse_args()

        if len(self._args) != 0:
            raise ValueError(f'{len(self._args)} is wrong number of args, should be 0')
        self._setup_logging()
        self._logger.info(f'{self.options=}')
        self._logger.info(f'{self._args=}')
        self._logger.info(f'{self.options.verbose=}')
        self._logger.info(f'{self.options.log_into_file=}')
        self._logger.info(f'{__version__=}')


    def _setup_logging(self) -> None:
        try:
            with open(self.options.config_log_file, 'r') as stream:
                config_yaml = yaml.load(stream, Loader=yaml.FullLoader)
                logging.config.dictConfig(config_yaml)
                logger_type = (LoggerType.CONSOLE_LOGGER.value, LoggerType.FILE_LOGGER.value)[self.options.log_into_file]
                self._logger = logging.getLogger(logger_type)
                self._logger.disabled = self.options.verbose == False
        except ValueError as ve:
            raise ValueError(f'{self.options.config_log_file} is not a valid yaml format')
        except IOError:
            raise IOError(f'{self.options.config_log_file} does not exist.')
        self._logger.debug(f"logger_type: {logger_type}")

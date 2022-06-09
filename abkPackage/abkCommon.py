# Standard library imports
import os
import errno
import getpass
import logging
import logging.config
import timeit

# Third party imports
import yaml
from optparse import OptionParser, Values
from colorama import Fore, Style

# Local application imports
from _version import __version__


logger = logging.getLogger(__name__)


CONSOLE_LOGGER = 'consoleLogger'
FILE_LOGGER = 'fileLogger'


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
    def __init__(self, timer_name, logger=None):
        self._timer_name = timer_name
        self._logger = logger
    def __enter__(self):
        self.start = timeit.default_timer()
    def __exit__(self, exc_type, exc_value, traceback):
        time_took = (timeit.default_timer() - self.start) * 1000.0
        self._logger.info('Executing {} took {} ms'.format(self._timer_name, str(time_took)))



class CommandLineOptions(object):
    """CommandLineOptions module handles all parameters passed in to the python script"""
    _args = None
    options = None
    logger = None

    def __init__(self, args:list=None, options:Values=None):
        self._args = args
        self.options = options
        self.logger = None

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
            parser.error("wrong number of arguments")
        self._setup_logging()
        self.logger.info(f"options: {self.options}")
        self.logger.info(f"args: {self._args}")
        self.logger.info(f"options.verbose: {self.options.verbose}")
        self.logger.info(f"options.log_into_file: {self.options.log_into_file}")
        self.logger.info(f"__version__: {__version__}")


    def _setup_logging(self) -> None:
        try:
            with open(self.options.config_log_file, 'r') as stream:
                try:
                    config_yaml = yaml.load(stream, Loader=yaml.FullLoader)
                    logging.config.dictConfig(config_yaml)
                    logger_type = (CONSOLE_LOGGER, FILE_LOGGER)[self.options.log_into_file]
                    self.logger = logging.getLogger(logger_type)
                    self.logger.disabled = self.options.verbose == False
                except ValueError:
                    raise ValueError(f'{self.options.config_log_file} is not a valid yaml format')
                except Exception as ex:
                    raise Exception(f'not ValueError: {ex.exeption}')
        except IOError:
            raise IOError(f'{self.options.config_log_file} does not exist.')
        self.logger.debug(f"logger_type: {logger_type}")

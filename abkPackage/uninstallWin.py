import logging
import logging.config
from abkCommon import function_trace

logger = logging.getLogger(__name__)


@function_trace
def Cleanup(pyScriptName):
    logger.debug(f'{pyScriptName=}')
    logger.info("Windows Uninstallation is not supported yet")


if __name__ == '__main__':
    raise Exception('This module should not be executed directly. Only for imports')

from datetime import time
import logging
import logging.config

from abkCommon import function_trace


logger = logging.getLogger(__name__)


@function_trace
def Setup(time_to_exe:time, pyScriptName:str) -> None:
    logger.debug(f'{time_to_exe.hour=}, {time_to_exe.minute=}, {pyScriptName}')
    logger.info("Linux installation is not supported yet")


if __name__ == '__main__':
    raise Exception('This module should not be executed directly. Only for imports')

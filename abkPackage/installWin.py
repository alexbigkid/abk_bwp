import logging
import logging.config
logger = logging.getLogger(__name__)

def Setup(hour, minute, pyScriptName):
    logger.debug("-> Setup(%s, %s, %s)", hour, minute, pyScriptName)
    logger.info("Windows installation is not supported yet")
    # pyFullName = linkPythonScript(pyScriptName)
    # scriptName = os.path.basename(pyFullName)
    # scriptPath = os.path.dirname(pyFullName)
    # logger.info("scriptName = %s", scriptName)
    # logger.info("scriptPath = %s", scriptPath)
    # (plistLable, plistName) =  CreatePlistFile(hour, minute, scriptName)
    # plistFullName = os.path.join(scriptPath, plistName)
    # logger.info("plist_full_name = %s", plistFullName)
    # dstPlistName = CreatePlistLink(plistFullName)
    # StopAndUnloadBingwallpaperJob(dstPlistName, plistLable)
    # LoadAndStartBingwallpaperJob(dstPlistName, plistLable)
    logger.debug("<- Setup")

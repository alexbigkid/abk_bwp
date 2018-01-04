import os
import sys
import subprocess
import abkPackage
from abkPackage import abkCommon
import logging
import logging.config
logger = logging.getLogger(__name__)


def CreatePlistFile(hour, minute, script_name):
    logger.debug("-> CreatePlistFile(%s, %s, %s)", hour, minute, script_name)
    user_name = abkCommon.GetUserName()
    plist_label = "com."+user_name+"."+script_name
    plist_name = plist_label+".plist"
    fh = open(plist_name, "w")
    lines2write = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
        "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n",
        "<plist version=\"1.0\">\n",
        "<dict>\n",
        "    <key>Label</key>\n",
        "    <string>"+plist_label+"</string>\n",
        "    <key>ProgramArguments</key>\n",
        "    <array>\n",
        "        <string>python</string>\n",
        "        <string>/Users/"+user_name+"/bin/"+script_name+"</string>\n",
        "    </array>\n",
        "    <key>RunAtLoad</key>\n",
        "    <true/>\n",
        "    <key>StartCalendarInterval</key>\n",
        "    <dict>\n",
        "        <key>Hour</key>\n",
        "        <integer>"+hour+"</integer>\n",
        "        <key>Minute</key>\n",
        "        <integer>"+minute+"</integer>\n",
        "    </dict>\n",
        "</dict>\n",
        "</plist>\n" ]
    fh.writelines(lines2write)
    fh.close()
    logger.debug("<- CreatePlistFile(%s, %s)", plist_label, plist_name)
    return (plist_label, plist_name)

def CreatePlistLink(full_file_name):
    logger.debug("-> CreatePlistLink(%s)", full_file_name)
    file_name = os.path.basename(full_file_name)
    home_dir = abkCommon.GetHomeDir()
    dst_file_name = os.path.join(home_dir+"/Library/LaunchAgents", file_name)
    logger.info("src= %s, dst= %s", full_file_name, dst_file_name)
    abkCommon.EnsureLinkExists(full_file_name, dst_file_name)
    logger.debug("<- CreatePlistLink(%s)", dst_file_name)
    return dst_file_name

def StopAndUnloadBingwallpaperJob(plistName, plistLable):
    logger.debug("-> StopAndUnloadBingwallpaperJob(plistName=%s, plistLable=%s)", plistName, plistLable)

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    f = open(os.devnull, 'w')
    sys.stderr = f
    sys.sdtout = f
 
 
    cmdList = []
    cmdList.append("launchctl list | grep "+plistLable)
    cmdList.append("launchctl stop "+plistLable)
    cmdList.append("launchctl unload -w "+plistName)

    for cmd in cmdList:
        try:
            retCode = subprocess.check_call(cmd, shell=True)
            logger.info("command '%s' succeeded, returned: %s", cmd, str(retCode))
        except subprocess.CalledProcessError as e:
            logger.error("command '%s' failed, returned: %d", cmd, e.returncode)
            pass


    cmd = "launchctl unload -w "+plistName
    retCode = subprocess.check_call(cmd, shell=True)
    logger.info("command '%s' succeeded, returned: %s", cmd, str(retCode))


    f.close()
    sys.stderr = old_stderr
    sys.stdout = old_stdout

    logger.debug("<- StopAndUnloadBingwallpaperJob")
    
def LoadAndStartBingwallpaperJob(plistName, plistLable):
    logger.debug("-> LoadAndStartBingwallpaperJob(plistName=%s, plistLable=%s)", plistName, plistLable)

    cmdList = []
    cmdList.append("launchctl load -w "+plistName)
    cmdList.append("launchctl start "+plistLable)

    for cmd in cmdList:
        try:
            retCode = subprocess.check_call(cmd, shell=True)
            logger.info("command '%s' succeeded, returned: %s", cmd, str(retCode))
        except subprocess.CalledProcessError as e:
            logger.info("command '%s' failed, returned: %d", cmd, e.returncode)
        except:
            logger.info("command '%s' failed", cmd)

    logger.debug("<- LoadAndStartBingwallpaperJob")


def Setup(hour, minute, pyFullName):
    logger.debug("-> platFormDependantSetup(%s, %s, %s)", hour, minute, pyFullName)
    scriptName = os.path.basename(pyFullName)
    scriptPath = os.path.dirname(pyFullName)
    logger.info("scriptName = %s", scriptName)
    logger.info("scriptPath = %s", scriptPath)
    (plistLable, plistName) =  CreatePlistFile(hour, minute, scriptName)
    plistFullName = os.path.join(scriptPath, plistName)
    logger.info("plist_full_name = %s", plistFullName)
    dstPlistName = CreatePlistLink(plistFullName)
    StopAndUnloadBingwallpaperJob(dstPlistName, plistLable)
    LoadAndStartBingwallpaperJob(dstPlistName, plistLable)
    logger.debug("<- platFormDependantSetup")

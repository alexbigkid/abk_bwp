import os
import subprocess
import logging
import logging.config
from datetime import time

from abkPackage import abkCommon
from abkPackage.abkCommon import function_trace

logger = logging.getLogger(__name__)


@function_trace
def linkPythonScript(fileName):
    logger.debug(f'{fileName=}')
    binDir = os.path.join(abkCommon.GetHomeDir(), "bin")
    abkCommon.EnsureDir(binDir)
    currDir = abkCommon.GetParentDir(__file__)
    src = os.path.join(currDir, fileName)
    dst = os.path.join(binDir, fileName)
    abkCommon.EnsureLinkExists(src, dst)
    logger.debug(f'{src=}')
    return src


@function_trace
def CreatePlistFile_new(time_to_exe: time, script_name: str):
    logger.debug(f'{time_to_exe.hour=}, {time_to_exe.minute=}, {script_name=}')
    user_name = abkCommon.GetUserName()
    plist_label = f'com.{user_name}.{script_name}'
    plist_name = f'{plist_label}.plist'
    fh = open(plist_name, "w")
    lines2write = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n',
        '<plist version="1.0">\n',
        '<dict>\n',
        '    <key>Label</key>\n',
        f'    <string>{plist_label}</string>\n',
        '    <key>ProgramArguments</key>\n',
        '    <array>\n',
        '        <string>python3</string>\n',
        f'        <string>/Users/{user_name}/abkBin/{script_name}</string>\n',
        '    </array>\n',
        '    <key>RunAtLoad</key>\n',
        '    <true/>\n',
        '    <key>StartCalendarInterval</key>\n',
        '    <dict>\n',
        '        <key>Hour</key>\n',
        f'        <integer>{time_to_exe.hour}</integer>\n',
        '        <key>Minute</key>\n',
        f'        <integer>{time_to_exe.minute}</integer>\n',
        '    </dict>\n',
        '</dict>\n',
        '</plist>\n',
    ]
    fh.writelines(lines2write)
    fh.close()
    logger.debug(f'{plist_label=}, {plist_name=}')
    return (plist_label, plist_name)


@function_trace
def CreatePlistLink(full_file_name):
    logger.debug(f'{full_file_name=}')
    file_name = os.path.basename(full_file_name)
    plist_install_dir = abkCommon.GetHomeDir()
    plist_install_dir = f'{plist_install_dir}/Library/LaunchAgents'
    abkCommon.EnsureDir(plist_install_dir)
    dst_file_name = os.path.join(plist_install_dir, file_name)
    logger.info(f'src= {full_file_name}, dst= {dst_file_name}')
    abkCommon.EnsureLinkExists(full_file_name, dst_file_name)
    logger.debug(f'{dst_file_name=}')
    return dst_file_name


@function_trace
def StopAndUnloadBingwallpaperJob(plistName, plistLable):
    logger.debug(f'{plistName=}, {plistLable=}')

    cmd_list = []
    cmd_list.append(f'launchctl list | grep {plistLable}')
    cmd_list.append(f'launchctl stop {plistLable}')
    cmd_list.append(f'launchctl unload -w {plistName}')

    try:
        for cmd in cmd_list:
            logger.info(f"about to execute command '{cmd}'")
            retCode = subprocess.check_call(cmd, shell=True)
            logger.info(f"command '{cmd}' succeeded, returned: {retCode}")
    except subprocess.CalledProcessError as e:
        logger.error(f'ERROR: returned: {e.returncode}')
        pass


@function_trace
def LoadAndStartBingwallpaperJob(plistName, plistLable):
    logger.debug(f'{plistName=}, {plistLable=}')

    cmd_list = []
    cmd_list.append(f'launchctl load -w {plistName}')
    cmd_list.append(f'launchctl start {plistLable}')

    try:
        for cmd in cmd_list:
            logger.info(f"about to execute command '{cmd}'")
            retCode = subprocess.check_call(cmd, shell=True)
            logger.info(f"command '{cmd}' succeeded, returned: {retCode}")
    except subprocess.CalledProcessError as e:
        logger.critical(f'ERROR: returned: {e.returncode}')
    except:
        logger.critical(f'ERROR: unknow')


@function_trace
def Setup(time_to_exe: time, pyScriptName):
    logger.debug(f'{time_to_exe.hour=}, {time_to_exe.minute=}, {pyScriptName}')
    pyFullName = linkPythonScript(pyScriptName)
    scriptName = os.path.basename(pyFullName)
    scriptPath = os.path.dirname(pyFullName)
    logger.info(f'{scriptPath=}, {scriptName=}')
    (plistLable, plistName) = CreatePlistFile_new(time_to_exe, scriptName)
    plistFullName = os.path.join(scriptPath, plistName)
    logger.info(f'{plistFullName=}')
    dstPlistName = CreatePlistLink(plistFullName)
    StopAndUnloadBingwallpaperJob(dstPlistName, plistLable)
    LoadAndStartBingwallpaperJob(dstPlistName, plistLable)


if __name__ == '__main__':
    raise Exception('This module should not be executed directly. Only for imports')

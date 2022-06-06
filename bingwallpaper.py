# http://www.owenrumney.co.uk/2014/09/13/Update_Bing_Desktop_For_Mac.html
# Modified by Alex Berger @ http://www.ABKphoto.com

import os
# import sys
import errno
import argparse
import shutil
from urllib.request import urlopen
import json
import subprocess
import logging
import inspect
from sys import platform as _platform

import abkPackage
from abkPackage import abkCommon

configFile = 'config.json'
function_name = lambda: inspect.stack()[1][3]
# function_name = sys._getframe().f_code.co_name


class AbkLogLevel(str):
    DEBUG       = 'DEBUG',
    INFO        = 'INFO',
    WARNING     = 'WARNING',
    ERROR       = 'ERROR',
    CRITICAL    = 'CRITICAL'


class BingWallPaper:
    def __init__(self, logLevel:str=None):
        self.logger = logging.getLogger(__name__)
        #print(f"logLevel = {logLevel}")
        if logLevel:
            self.logger.setLevel(logLevel)
        else:
            self.logger.disabled = True

        formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.debug(f"-> {self.__class__}")

    def __del__(self):
        self.logger.debug(f"<- {self.__class__}")

    def readLinkConfigFile(self, confFile):
        self.logger.debug(f"-> {function_name}({confFile})")
        if os.path.islink(__file__):
            linkFile = os.readlink(__file__)
            linkPath = os.path.dirname(linkFile)
            self.logger.info(f"{linkPath=}")
            confFile = os.path.join(linkPath, confFile)
            self.logger.info(f"{confFile=}")
        with open(confFile) as jsonData:
            config = json.load(jsonData)
        jsonData.close()
        self.logger.debug(f"<- {function_name}(imagesDirrectory={config['imagesDirrectory']}, numOfImages2Keep={config['numOfImages2Keep']})")
        return (config['imagesDirrectory'], config['numOfImages2Keep'])

    def DefinePixDirs(self, imagesDir):
        self.logger.debug(f"-> {function_name}({imagesDir=}")
        homeDir = abkCommon.GetHomeDir()
        self.logger.info(f"{homeDir=}")
        pixDir = os.path.join(homeDir, imagesDir)
        abkCommon.EnsureDir(pixDir)
        self.logger.debug(f"<- {function_name}({pixDir=}")
        return pixDir

    def TrimNumberOfPix(self, pixDir, num):
        self.logger.debug(f"-> {function_name}({pixDir=}, {num=})")

        listOfFiles = []
        for f in os.listdir(pixDir):
            if f.endswith('.jpg'):
                listOfFiles.append(f)
        listOfFiles.sort()
        self.logger.debug(f"listOfFile = [{', '.join(map(str, listOfFiles))}]")
        numberOfJpgs = len(listOfFiles)
        self.logger.info(f"{numberOfJpgs=}")
        if numberOfJpgs > num:
            jpgs2delete = listOfFiles[0:numberOfJpgs-num]
            self.logger.info(f"jpgs2delete = [{', '.join(map(str, jpgs2delete))}]")
            num2delete = len(jpgs2delete)
            self.logger.info(f"{num2delete=}")
            for delFile in jpgs2delete:
                self.logger.info(f"deleting file: {delFile}")
                try:
                    os.unlink(os.path.join(pixDir, delFile))
                except:
                    self.logger.error(f"deleting {delFile} failed")
        else:
            self.logger.info("no images to delete")

        self.logger.debug(f"<- {function_name}")

    def DownloadBingImage(self, dstDir):
        self.logger.debug(f"-> {function_name}({dstDir=})")
        response = urlopen("http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US")
        obj = json.load(response)
        url = (obj['images'][0]['urlbase'])
        name = (obj['images'][0]['fullstartdate'])
        url = 'http://www.bing.com' + url + '_1920x1080.jpg'
        fullFileName = os.path.join(dstDir, name+'.jpg')

        self.logger.info(f"Downloading {url} to {fullFileName}")
        f = open(fullFileName, 'wb')
        pic = urlopen(url)
        f.write(pic.read())
        f.close()
        self.logger.debug(f"<- {function_name}({fullFileName=})")
        return fullFileName

    def setDesktopBackground(self, fileName):
        self.logger.debug(f"-> {function_name}({fileName=})")
        # ----- Start platform dependency  -----
        if _platform == "darwin":
            # MAC OS X ------------------------
            self.logger.info("Mac OS X environment")
            SCRIPT_MAC = """/usr/bin/osascript<<END
tell application "Finder"
set desktop picture to POSIX file "%s"
end tell
END"""
            subprocess.call(SCRIPT_MAC % fileName, shell=True)

        elif _platform == "linux" or _platform == "linux2":
            # linux ---------------------------
            self.logger.info("Linux environment")

        elif _platform == "win32" or _platform == "win64":
            # Windows or Windows 64-bit -----
            self.logger.info("Windows environment")
            import ctypes
            import platform

            winNum = platform.uname()[2]
            self.logger.info(f"os info: {platform.uname()}")
            self.logger.info(f"win#: {winNum}")
            if(int(winNum) >= 10):
                try:
                    ctypes.windll.user32.SystemParametersInfoW(
                        20, 0, fileName, 3)
                    self.logger.info(f"Background image set to: {fileName}")
                except:
                    self.logger.error(f"Was not able to set background image to: {fileName}")
            else:
                self.logger.error(f"Windows 10 and above is supported, you are using Windows {winNum}")
        # ----- End platform dependency  -----
        else:
            self.logger.error("Not known OS environment")
            raise NameError("Not known OS environment")

        self.logger.info(f"Set background to {fileName}")
        self.logger.debug(f"<- {function_name}()")


def main():
    parser = argparse.ArgumentParser(description='Sets picture from Bing as background')
    parser.add_argument(
        "-l", "--log",
        dest="logLevel", choices=[AbkLogLevel.DEBUG, AbkLogLevel.INFO, AbkLogLevel.WARNING, AbkLogLevel.ERROR, AbkLogLevel.CRITICAL],
        # dest="logLevel", choices=['DEBUG'],
        help="Set the logging level"
    )
    args = parser.parse_args()
    if args.logLevel:
        bwp = BingWallPaper(getattr(logging, args.logLevel))
    else:
        bwp = BingWallPaper()

    (imagesDir, numOfImages) = bwp.readLinkConfigFile(configFile)
    pixDir = bwp.DefinePixDirs(imagesDir)
    bwp.TrimNumberOfPix(pixDir, numOfImages)
    fileName = bwp.DownloadBingImage(pixDir)
    bwp.setDesktopBackground(fileName)


if __name__ == '__main__':
    main()

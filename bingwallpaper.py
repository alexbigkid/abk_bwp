# http://www.owenrumney.co.uk/2014/09/13/Update_Bing_Desktop_For_Mac.html
# Modified by Alex Berger @ http://www.ABKphoto.com

import os
import errno
import argparse
import shutil
from urllib.request import urlopen
import json
import subprocess
import logging
from sys import platform as _platform
import abkPackage
from abkPackage import abkCommon

configFile = 'config.json'


class BingWallPaper:
    def __init__(self, logLevel):
        self.logger = logging.getLogger(__name__)
        #print("logLevel = %s", logLevel)
        if logLevel != "NONE":
            self.logger.setLevel(logLevel)
        else:
            self.logger.disabled = True

        formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.debug("-> BingWallPaper")

    def __del__(self):
        self.logger.debug("<- BingWallPaper")

    def readLinkConfigFile(self, confFile):
        self.logger.debug("-> readLinkConfigFile(%s)", confFile)
        if os.path.islink(__file__):
            linkFile = os.readlink(__file__)
            linkPath = os.path.dirname(linkFile)
            self.logger.info("linkPath = %s", linkPath)
            confFile = os.path.join(linkPath, confFile)
            self.logger.info("confFile = %s", confFile)
        with open(confFile) as jsonData:
            config = json.load(jsonData)
        jsonData.close()
        self.logger.debug("<- readLinkConfigFile(imagesDirrectory=%s, numOfImages2Keep=%d)",
                          config['imagesDirrectory'], config['numOfImages2Keep'])
        return (config['imagesDirrectory'], config['numOfImages2Keep'])

    def DefinePixDirs(self, imagesDir):
        self.logger.debug("-> DefinePixDirs(imagesDir=%s)", imagesDir)
        homeDir = abkCommon.GetHomeDir()
        self.logger.info("homeDir: %s", homeDir)
        pixDir = os.path.join(homeDir, imagesDir)
        abkCommon.EnsureDir(pixDir)
        self.logger.debug("<- DefinePixDirs(pixDir=%s)", pixDir)
        return pixDir

    def TrimNumberOfPix(self, pixDir, num):
        self.logger.debug("-> TrimNumberOfPix(%s, %d)", pixDir, num)

        listOfFiles = []
        for f in os.listdir(pixDir):
            if f.endswith('.jpg'):
                listOfFiles.append(f)
        listOfFiles.sort()
        self.logger.debug("listOfFile = [%s]" %
                          ', '.join(map(str, listOfFiles)))
        numberOfJpgs = len(listOfFiles)
        self.logger.info("numberOfJpgs = %d", numberOfJpgs)
        if numberOfJpgs > num:
            jpgs2delete = listOfFiles[0:numberOfJpgs-num]
            self.logger.info("jpgs2delete = [%s]" %
                             ', '.join(map(str, jpgs2delete)))
            num2delete = len(jpgs2delete)
            self.logger.info("jpgs2delete = %d", num2delete)
            for delFile in jpgs2delete:
                self.logger.info("deleting file = %s", delFile)
                try:
                    os.unlink(os.path.join(pixDir, delFile))
                except:
                    self.logger.error("deleting %s failed", delFile)
        else:
            self.logger.info("no images to delete")

        self.logger.debug("<- TrimNumberOfPix")

    def DownloadBingImage(self, dstDir):
        self.logger.debug("-> DownloadBingImage(%s)", dstDir)
        response = urlopen("http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US")
        obj = json.load(response)
        url = (obj['images'][0]['urlbase'])
        name = (obj['images'][0]['fullstartdate'])
        url = 'http://www.bing.com' + url + '_1920x1080.jpg'
        fullFileName = os.path.join(dstDir, name+'.jpg')

        self.logger.info("Downloading %s to %s", url, fullFileName)
        f = open(fullFileName, 'wb')
        pic = urlopen(url)
        f.write(pic.read())
        f.close()
        self.logger.debug(
            "<- DownloadBingImage(fullFileName=%s)", fullFileName)
        return fullFileName

    def setDesktopBackground(self, fileName):
        self.logger.debug("-> setDesktopBackground(%s)", fileName)
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
            self.logger.info("os info: %s", platform.uname())
            self.logger.info("win#: %s", winNum)
            if(int(winNum) >= 10):
                try:
                    ctypes.windll.user32.SystemParametersInfoW(
                        20, 0, fileName, 3)
                    self.logger.info("Background image set to: %s", fileName)
                except:
                    self.logger.error(
                        "Was not able to set background image to: %s", fileName)
            else:
                self.logger.error(
                    "Windows 10 and above is supported, you are using Windows %s", winNum)
        # ----- End platform dependency  -----
        else:
            self.logger.error("Not known OS environment")
            raise NameError("Not known OS environment")

        self.logger.info("Set background to %s", fileName)
        self.logger.debug("<- setDesktopBackground()")


def main():
    parser = argparse.ArgumentParser(
        description='Sets picture from Bing as background')
    parser.add_argument("-l", "--log", dest="logLevel", choices=[
                        'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level")
    args = parser.parse_args()
    if args.logLevel:
        bwp = BingWallPaper(getattr(logging, args.logLevel))
    else:
        bwp = BingWallPaper("NONE")

    (imagesDir, numOfImages) = bwp.readLinkConfigFile(configFile)
    (pixDir) = bwp.DefinePixDirs(imagesDir)
    bwp.TrimNumberOfPix(pixDir, numOfImages)
    fileName = bwp.DownloadBingImage(pixDir)
    bwp.setDesktopBackground(fileName)


if __name__ == '__main__':
    main()

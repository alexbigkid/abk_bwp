#!/usr/bin/env python
"""Main program for downloading and upscaling/downscaling bing images to use as wallpapaer sized """

# -----------------------------------------------------------------------------
# http://www.owenrumney.co.uk/2014/09/13/Update_Bing_Desktop_For_Mac.html
# Modified by Alex Berger @ http://www.abkcompany.com
# -----------------------------------------------------------------------------

# Standard library imports
from enum import Enum
import os
import sys
import argparse
from typing import Tuple
from urllib.request import urlopen
import json
import subprocess
import logging
import logging.config
from sys import platform as _platform

# Third party imports
from optparse import OptionParser, Values
from colorama import Fore, Style
import tomli

# Local application imports
from abkPackage import abkCommon
from config import bwp_config
# from ftv import FTV



class BingWallPaper(object):
    """BingWallPaper downloads images from bing.com and sets it as a wallpaper"""


    @abkCommon.function_trace
    def __init__(self, logger:logging.Logger=None, options:Values=None):  # type: ignore
        self._logger = logger or logging.getLogger(__name__)
        self._options = options


    @abkCommon.function_trace
    def __del__(self):
        pass


    @abkCommon.function_trace
    def define_pix_dirs(self, imagesDir:str) -> str:
        self._logger.debug(f"{imagesDir=}")
        homeDir = abkCommon.GetHomeDir()
        self._logger.info(f"{homeDir=}")
        pixDir = os.path.join(homeDir, imagesDir)
        abkCommon.EnsureDir(pixDir)
        self._logger.debug(f"{pixDir=}")
        return pixDir


    @abkCommon.function_trace
    def scale_images(self):
        pass


    @abkCommon.function_trace
    def trim_number_of_pix(self, pixDir:str, num:int) -> None:
        self._logger.debug(f"{pixDir=}, {num=}")

        listOfFiles = []
        for f in os.listdir(pixDir):
            if f.endswith('.jpg'):
                listOfFiles.append(f)
        listOfFiles.sort()
        self._logger.debug(f"listOfFile = [{', '.join(map(str, listOfFiles))}]")
        numberOfJpgs = len(listOfFiles)
        self._logger.info(f"{numberOfJpgs=}")
        if numberOfJpgs > num:
            jpgs2delete = listOfFiles[0:numberOfJpgs-num]
            self._logger.info(f"jpgs2delete = [{', '.join(map(str, jpgs2delete))}]")
            num2delete = len(jpgs2delete)
            self._logger.info(f"{num2delete=}")
            for delFile in jpgs2delete:
                self._logger.info(f"deleting file: {delFile}")
                try:
                    os.unlink(os.path.join(pixDir, delFile))
                except:
                    self._logger.error(f"deleting {delFile} failed")
        else:
            self._logger.info("no images to delete")


    @abkCommon.function_trace
    def download_bing_image(self, dstDir:str) -> str:
        self._logger.debug(f"{dstDir=}")
        response = urlopen("http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US")
        obj = json.load(response)
        url = (obj['images'][0]['urlbase'])
        name = (obj['images'][0]['fullstartdate'])
        url = 'http://www.bing.com' + url + '_1920x1080.jpg'
        fullFileName = os.path.join(dstDir, name+'.jpg')

        self._logger.info(f"Downloading {url} to {fullFileName}")
        f = open(fullFileName, 'wb')
        pic = urlopen(url)
        f.write(pic.read())
        f.close()
        self._logger.debug(f"{fullFileName=}")
        return fullFileName


    @abkCommon.function_trace
    def set_desktop_background(self, fileName:str) -> None:
        self._logger.debug(f"{fileName=}")
        # ----- Start platform dependency  -----
        if _platform == "darwin":
            # MAC OS X ------------------------
            self._logger.info("Mac OS X environment")
            SCRIPT_MAC = """/usr/bin/osascript<<END
tell application "Finder"
set desktop picture to POSIX file "%s"
end tell
END"""
            subprocess.call(SCRIPT_MAC % fileName, shell=True)

        elif _platform == "linux" or _platform == "linux2":
            # linux ---------------------------
            self._logger.info("Linux environment")

        elif _platform == "win32" or _platform == "win64":
            # Windows or Windows 64-bit -----
            self._logger.info("Windows environment")
            import ctypes
            import platform

            winNum = platform.uname()[2]
            self._logger.info(f"os info: {platform.uname()}")
            self._logger.info(f"win#: {winNum}")
            if(int(winNum) >= 10):
                try:
                    ctypes.windll.user32.SystemParametersInfoW(  # type: ignore
                        20, 0, fileName, 3)
                    self._logger.info(f"Background image set to: {fileName}")
                except:
                    self._logger.error(f"Was not able to set background image to: {fileName}")
            else:
                self._logger.error(f"Windows 10 and above is supported, you are using Windows {winNum}")
        # ----- End platform dependency  -----
        else:
            self._logger.error("Not known OS environment")
            raise NameError("Not known OS environment")

        self._logger.info(f"Set background to {fileName}")


def main():
    exit_code = 0
    # parser = argparse.ArgumentParser(description='Sets picture from Bing as background')
    # parser.add_argument(
    #     "-l", "--log",
    #     dest="logLevel", choices=[AbkLogLevel.DEBUG, AbkLogLevel.INFO, AbkLogLevel.WARNING, AbkLogLevel.ERROR, AbkLogLevel.CRITICAL],
    #     # dest="logLevel", choices=['DEBUG'],
    #     help="Set the logging level"
    # )
    # args = parser.parse_args()
    try:
        command_line_options = abkCommon.CommandLineOptions()
        command_line_options.handle_options()
        bwp = BingWallPaper(logger=command_line_options._logger, options=command_line_options.options)
        pix_dir = bwp.define_pix_dirs(bwp_config['image_dir'])
        bwp.trim_number_of_pix(pix_dir, bwp_config['number_images_to_keep'])
        file_name = bwp.download_bing_image(pix_dir)
        bwp.scale_images()
        if bwp_config.get('set_desktop_image', False):
            bwp.set_desktop_background(file_name)
        if bwp_config.get('ftv', {}).get('set_image', False):
            pass
            # ftv = FTV(config_dict.get('ftv'))
            # if ftv.is_art_mode_supported():
            #     ftv.change_daily_images()

    except Exception as exception:
        print(f"{Fore.RED}ERROR: executing bingwallpaper")
        print(f"EXCEPTION: {exception}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == '__main__':
    main()

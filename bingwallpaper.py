#!/usr/bin/env python
"""Main program for downloading and upscaling/downscaling bing images to use as wallpaper sized """

# -----------------------------------------------------------------------------
# http://www.owenrumney.co.uk/2014/09/13/Update_Bing_Desktop_For_Mac.html
# Modified by Alex Berger @ http://www.abkcompany.com
# -----------------------------------------------------------------------------

# Standard library imports
import os
import sys
import json
import subprocess
import logging
import logging.config
from abc import ABCMeta, abstractmethod
from sys import platform as _platform
from urllib.request import urlopen

# Third party imports
from optparse import Values
from colorama import Fore, Style

# Local application imports
from abkPackage import abkCommon
from config import bwp_config
# from ftv import FTV


class IDownLoadServiceBase(metaclass=ABCMeta):

    def __init__(self, logger: logging.Logger) -> None:
        """Super class init"""
        self._logger = logger or logging.getLogger(__name__)

    @abstractmethod
    def download_daily_image(self, dst_dir: str) -> str:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplemented



class BingDownloadService(IDownLoadServiceBase):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    def download_daily_image(self, dst_dir: str) -> str:
        """Downloads bing image and stores it in the defined directory
        Args:
            dst_dir (str): directory to store the image
        Returns:
            str: full file name downloaded
        """
        self._logger.debug(f"{dst_dir=}")
        response = urlopen("http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US")
        obj = json.load(response)
        url = obj["images"][0]["urlbase"]
        name = obj["images"][0]["fullstartdate"]
        url = f"http://www.bing.com{url}_1920x1080.jpg"
        full_file_name = os.path.join(dst_dir, f"{name}.jpg")

        self._logger.info(f"Downloading {url} to {full_file_name}")
        with open(full_file_name, "wb") as fh:
            pic = urlopen(url)
            fh.write(pic.read())
        self._logger.debug(f"{full_file_name=}")
        return full_file_name


class PeapixDownloadService(IDownLoadServiceBase):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    def download_daily_image(self, dst_dir: str) -> str:
        return ""



class IOsDependentBase(metaclass=ABCMeta):
    """OS dependency base class"""
    os_type: abkCommon.OsType = None  # type: ignore

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger = None) -> None:  # type: ignore
        """Super class init"""
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info(f"({__class__.__name__}) {self.os_type} OS dependent environment ...")

    @abstractmethod
    def set_desktop_background(self, file_name: str) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplemented



class MacOSDependent(IOsDependentBase):
    """MacOS dependent code"""

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = abkCommon.OsType.MAC_OS
        super().__init__(logger)


    @abkCommon.function_trace
    def set_desktop_background(self, file_name: str) -> None:
        """Sets desktop image on Mac OS
        Args:
            file_name (str): file name which should be used to set the background
        """
        self._logger.debug(f"{file_name=}")
        SCRIPT_MAC = """/usr/bin/osascript<<END
tell application "Finder"
set desktop picture to POSIX file "%s"
end tell
END"""
        subprocess.call(SCRIPT_MAC % file_name, shell=True)
        self._logger.info(f"({self.os_type.MAC_OS.value}) Set background to {file_name}")



class LinuxDependent(IOsDependentBase):
    """Linux dependent code"""

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = abkCommon.OsType.LINUX_OS
        super().__init__(logger)

    @abkCommon.function_trace
    def set_desktop_background(self, file_name: str) -> None:
        """Sets desktop image on Linux
        Args:
            file_name (str): file name which should be used to set the background
        """
        self._logger.debug(f"{file_name=}")
        self._logger.info(f"({self.os_type.MAC_OS.value}) Set background to {file_name}")
        self._logger.info(f"({self.os_type.MAC_OS.value}) Not implemented yet")



class WindowsDependent(IOsDependentBase):
    """Windows dependent code"""

    @abkCommon.function_trace
    def __init__(self, logger: logging.Logger) -> None:
        self.os_type = abkCommon.OsType.WINDOWS_OS
        super().__init__(logger)

    @abkCommon.function_trace
    def set_desktop_background(self, file_name: str) -> None:
        """Sets desktop image on Windows
        Args:
            file_name (str): file name which should be used to set the background
        """
        self._logger.debug(f"{file_name=}")
        import ctypes
        import platform

        winNum = platform.uname()[2]
        self._logger.info(f"os info: {platform.uname()}")
        self._logger.info(f"win#: {winNum}")
        if int(winNum) >= 10:
            try:
                ctypes.windll.user32.SystemParametersInfoW(20, 0, file_name, 3)  # type: ignore
                self._logger.info(f"Background image set to: {file_name}")
            except:
                self._logger.error(f"Was not able to set background image to: {file_name}")
        else:
            self._logger.error(f"Windows 10 and above is supported, you are using Windows {winNum}")
        self._logger.info(f"({self.os_type.MAC_OS.value}) Not tested yet")
        self._logger.info(f"({self.os_type.MAC_OS.value}) Set background to {file_name}")



class BingWallPaper(object):
    """BingWallPaper downloads images from bing.com and sets it as a wallpaper"""

    @abkCommon.function_trace
    def __init__(self,
                 logger: logging.Logger,
                 options: Values,
                 os_dependant : IOsDependentBase,
                 dl_service : IDownLoadServiceBase
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._options = options
        self._os_dependent = os_dependant
        self._dl_service = dl_service


    def set_desktop_background(self, file_name: str) -> None:
        """Sets background image on different OS
        Args:
            file_name (str): file name which should be used to set the background
        """
        self._os_dependent.set_desktop_background(file_name)


    @abkCommon.function_trace
    def define_pix_dirs(self, images_dir: str) -> str:
        """Defines the image directory
        Args:
            images_dir (str): image directory
        Returns:
            str: full directory name where imaghes will be saved
        """
        self._logger.debug(f"{images_dir=}")
        home_dir = abkCommon.get_home_dir()
        self._logger.info(f"{home_dir=}")
        pix_dir = os.path.join(home_dir, images_dir)
        abkCommon.ensure_dir(pix_dir)
        self._logger.debug(f"{pix_dir=}")
        return pix_dir


    @abkCommon.function_trace
    def scale_images(self):
        pass


    @abkCommon.function_trace
    def trim_number_of_pix(self, pix_dir: str, max_number: int) -> None:
        """Deletes some images if it reaches max number desirable
           The max number can be defined in the config/bwp_config.toml file

        Args:
            pix_dir (str): image directory
            max_number (int): max number of images to keep
        """
        self._logger.debug(f"{pix_dir=}, {max_number=}")

        listOfFiles = []
        for f in os.listdir(pix_dir):
            if f.endswith(".jpg"):
                listOfFiles.append(f)
        listOfFiles.sort()
        self._logger.debug(f"listOfFile = [{', '.join(map(str, listOfFiles))}]")
        numberOfJpgs = len(listOfFiles)
        self._logger.info(f"{numberOfJpgs=}")
        if numberOfJpgs > max_number:
            jpgs2delete = listOfFiles[0:numberOfJpgs-max_number]
            self._logger.info(f"jpgs2delete = [{', '.join(map(str, jpgs2delete))}]")
            num2delete = len(jpgs2delete)
            self._logger.info(f"{num2delete=}")
            for delFile in jpgs2delete:
                self._logger.info(f"deleting file: {delFile}")
                try:
                    os.unlink(os.path.join(pix_dir, delFile))
                except:
                    self._logger.error(f"deleting {delFile} failed")
        else:
            self._logger.info("no images to delete")


    @abkCommon.function_trace
    def download_daily_image(self, dst_dir: str) -> str:
        """Downloads bing image and stores it in the defined directory
        Args:
            dst_dir (str): directory to store the image
        Returns:
            str: full file name downloaded
        """
        return self._dl_service.download_daily_image(dst_dir)


def main():
    exit_code = 0
    try:
        command_line_options = abkCommon.CommandLineOptions()
        command_line_options.handle_options()
        main_logger = command_line_options._logger

        # get the correct OS and instantiate OS dependent code
        if _platform in abkCommon.OsPlatformType.PLATFORM_MAC.value:
            bwp_os_dependent = MacOSDependent(logger=main_logger)
        elif _platform in abkCommon.OsPlatformType.PLATFORM_LINUX.value:
            bwp_os_dependent = LinuxDependent(logger=main_logger)
        elif _platform in abkCommon.OsPlatformType.PLATFORM_WINDOWS.value:
            bwp_os_dependent = WindowsDependent(logger=main_logger)
        else:
            raise ValueError(f'ERROR: "{_platform}" is not supported')

        # use bing service as defualt, peapix is for a back up solution
        if bwp_config.get("dl_service", "bing") == "bing":
            dl_service = BingDownloadService(logger=main_logger)
        else:
            dl_service = PeapixDownloadService(logger=main_logger)


        bwp = BingWallPaper(
            logger=main_logger,
            options=command_line_options.options,
            os_dependant=bwp_os_dependent,
            dl_service=dl_service
        )
        pix_dir = bwp.define_pix_dirs(bwp_config["image_dir"])
        bwp.trim_number_of_pix(pix_dir, bwp_config["number_images_to_keep"])
        file_name = bwp.download_daily_image(pix_dir)
        bwp.scale_images()
        if bwp_config.get("set_desktop_image", False):
            bwp.set_desktop_background(file_name)
        if bwp_config.get("ftv", {}).get("set_image", False):
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


if __name__ == "__main__":
    main()

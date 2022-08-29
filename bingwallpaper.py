#!/usr/bin/env python
"""Main program for downloading and upscaling/downscaling bing images to use as wallpaper sized """

# -----------------------------------------------------------------------------
# http://www.owenrumney.co.uk/2014/09/13/Update_Bing_Desktop_For_Mac.html
# Modified by Alex Berger @ http://www.abkcompany.com
# -----------------------------------------------------------------------------

# Standard library imports
from functools import cache
import os
import sys
import json
import subprocess
import logging
import logging.config
import datetime
import shutil
from abc import ABCMeta, abstractmethod
from sys import platform as _platform
from typing import Dict, List
from urllib.request import urlopen
from xmlrpc.client import Boolean, ResponseError
import requests

# Third party imports
from optparse import Values
from colorama import Fore, Style

# Local application imports
from abkPackage import abkCommon
from config import CONSTANT_KW, FTV_KW, ROOT_KW, bwp_config
# from ftv import FTV

BWP_DIRECTORIES = 1
BWP_FILES = 2
BWP_DEFAULT_PIX_DIR = "Pictures/BWP"
BWP_FILE_NAME_WARNING = "Please_do_not_modify_anything_in_this_directory.Handled_by_BingWallpaper_automagic"
BWP_NUMBER_OF_MONTHS = 12
BWP_DIGITS_IN_A_YEAR = 4
BWP_DIGITS_IN_A_MONTH = 2
BWP_DIGITS_IN_A_DAY = 2
BWP_IMG_FILE_EXT = ".jpg"


# -----------------------------------------------------------------------------
# local functions
# -----------------------------------------------------------------------------
@cache
def get_pix_dir() -> str:
    """Defines the image directory, creates if not existent yet
    Returns:
        str: full directory name where images will be saved
    """
    user_home_dir = abkCommon.get_home_dir()
    pix_dir = os.path.join(user_home_dir, bwp_config.get(ROOT_KW.IMAGE_DIR.value, BWP_DEFAULT_PIX_DIR))
    abkCommon.ensure_dir(pix_dir)
    return pix_dir


# -----------------------------------------------------------------------------
# DownLoad Service
# -----------------------------------------------------------------------------
class DownLoadServiceBase(metaclass=ABCMeta):

    def __init__(self, logger: logging.Logger) -> None:
        """Super class init"""
        self._logger = logger or logging.getLogger(__name__)


    @abstractmethod
    def download_daily_image(self, dst_dir: str) -> str:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplemented


    @staticmethod
    @abkCommon.function_trace
    def _convert_dir_structure_if_needed() -> bool:
        root_image_dir = get_pix_dir()
        # get sub directory names from the defined picture directory
        ftv_enabled = bwp_config.get(FTV_KW.FTV.value, {}).get(FTV_KW.ENABLED.value, False)
        dir_list = sorted(next(os.walk(root_image_dir))[BWP_DIRECTORIES])
        if len(dir_list) == 0:               # empty pix directory, no conversion needed
            # create an empty warning file
            open(f"{root_image_dir}/{BWP_FILE_NAME_WARNING}", "a").close()
            return ftv_enabled

        if ftv_enabled:
            filtered_year_dir_list = [bwp_dir for bwp_dir in dir_list if len(bwp_dir) == BWP_DIGITS_IN_A_YEAR and bwp_dir.isdigit()]
            if len(filtered_year_dir_list) > 0:
                DownLoadServiceBase._convert_to_ftv_dir_structure(root_image_dir, filtered_year_dir_list)
        else:
            filtered_month_dir_list = [bwp_dir for bwp_dir in dir_list if len(bwp_dir) == BWP_DIGITS_IN_A_MONTH and bwp_dir.isdigit() and int(bwp_dir) <= BWP_NUMBER_OF_MONTHS]
            if len(filtered_month_dir_list) > 0:
                DownLoadServiceBase._convert_to_date_dir_structure(root_image_dir, filtered_month_dir_list)
        return ftv_enabled

    @staticmethod
    @abkCommon.function_trace
    def _convert_to_ftv_dir_structure(root_image_dir: str, year_list: List[str]) -> None:
        """ Converts the bing image data directory structure (YYYY/mm/YYYY-mm-dd_us.jpg)
            to frame TV directory structure                  (mm/dd/YYYY-mm-dd_us.jpg)
        Args:
            root_image_dir (str): directory where images are stored
            year_list (List[str]): year list directory names
        """
        # FTV enabled conversion needed to use mm/dd directory format.
        # print(f"{root_image_dir=}, {year_list=}")
        region_list = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(CONSTANT_KW.PEAPIX_REGION_ALTERNATIVES.value, [])
        for year_dir in year_list:
            if len(year_dir) == BWP_DIGITS_IN_A_YEAR and year_dir.isdigit():
                # get the subdirectories of the year
                full_year_dir = os.path.join(root_image_dir, year_dir)
                month_list = sorted(next(os.walk(full_year_dir))[BWP_DIRECTORIES])
                for month_dir in month_list:
                    if len(month_dir) == BWP_DIGITS_IN_A_MONTH and month_dir.isdigit() and int(month_dir) <= BWP_NUMBER_OF_MONTHS:
                        full_month_dir = os.path.join(full_year_dir, month_dir)
                        img_file_list = sorted(next(os.walk(full_month_dir))[BWP_FILES])
                        # print(f"\n---- ABK: {year_dir=}, {month_dir=}, {img_file_list=}")
                        for img_file in img_file_list:
                            file_name, file_ext = os.path.splitext(img_file)
                            # print(f"---- ABK: {file_name=}, {file_ext=}")
                            img_date_part, img_region_part = file_name.split("_")
                            if file_ext == BWP_IMG_FILE_EXT and img_region_part in region_list:
                                try:
                                    img_date = datetime.datetime.strptime(img_date_part, "%Y-%m-%d")
                                    # print(f"---- ABK: {img_date.year=}, {img_date.month=}, {img_date.day=}, {img_region_part=}")
                                    # looks like a legit file name -> move it the the new location mm/dd/YYYY-mm-dd_us.jpg
                                    img_src = os.path.join(full_month_dir, img_file)
                                    img_dst = os.path.join(root_image_dir, f'{img_date.month:02d}', f'{img_date.day:02d}', img_file)
                                    # print(f"---- ABK: moving [{img_src}] -> [{img_dst}]")
                                    os.renames(img_src, img_dst)
                                except Exception as exp:
                                    print(f"{Fore.RED}ERROR: moving [{img_src=}] to [{img_dst=}] with EXCEPTION: {exp=}. INVESTIGATE!{Style.RESET_ALL}")     # type: ignore
                                    # we don't want to move on here. since there is something wrong, we just re-throw end exit.
                                    raise
                # if no errors and move was successful delete the old directory structure
                shutil.rmtree(full_year_dir, ignore_errors=True)
        DownLoadServiceBase._correct_current_background_link(root_image_dir, is_ftv_enabled=True)


    @staticmethod
    @abkCommon.function_trace
    def _convert_to_date_dir_structure(root_image_dir: str, month_list: List[str]) -> None:
        """ Converts the bing image frame TV directory structure (mm/dd/YYYY-mm-dd_us.jpg)
            to data directory structure                          (YYYY/mm/YYYY-mm-dd_us.jpg)
        Args:
            root_image_dir (str): directory where images are stored
            month_list (List[str]): month list directory names
        """
        # print(f"{root_image_dir=}, {month_list=}")
        region_list = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(CONSTANT_KW.PEAPIX_REGION_ALTERNATIVES.value, [])
        for month_dir in month_list:
            if len(month_dir) == BWP_DIGITS_IN_A_MONTH and month_dir.isdigit() and int(month_dir) <= BWP_NUMBER_OF_MONTHS:
                # get the subdirectories of the month
                full_month_dir = os.path.join(root_image_dir, month_dir)
                day_list = sorted(next(os.walk(full_month_dir))[BWP_DIRECTORIES])
                for day_dir in day_list:
                    if len(day_dir) == BWP_DIGITS_IN_A_DAY and day_dir.isdigit():
                        full_day_dir = os.path.join(full_month_dir, day_dir)
                        img_file_list = sorted(next(os.walk(full_day_dir))[BWP_FILES])
                        # print(f"\n---- ABK: {month_dir=}, {day_dir=}, {img_file_list=}")
                        for img_file in img_file_list:
                            file_name, file_ext = os.path.splitext(img_file)
                            # print(f"---- ABK: {file_name=}, {file_ext=}")
                            img_date_part, img_region_part = file_name.split("_")
                            if file_ext == BWP_IMG_FILE_EXT and img_region_part in region_list:
                                try:
                                    img_date = datetime.datetime.strptime(img_date_part, "%Y-%m-%d")
                                    # print(f"---- ABK: {img_date.year=}, {img_date.month=}, {img_date.day=}, {img_region_part=}")
                                    # looks like a legit file name -> move it the the new location YYYY/mm/YYYY-mm-dd_us.jpg
                                    img_src = os.path.join(full_day_dir, img_file)
                                    img_dst = os.path.join(root_image_dir, f'{img_date.year:04d}', f'{img_date.month:02d}', img_file)
                                    # print(f"---- ABK: moving [{img_src}] -> [{img_dst}]")
                                    os.renames(img_src, img_dst)
                                except Exception as exp:
                                    print(f"{Fore.RED}ERROR: moving [{img_src=}] to [{img_dst=}] with EXCEPTION: {exp=}. INVESTIGATE!{Style.RESET_ALL}")     # type: ignore
                                    # we don't want to move on here. since there is something wrong, we just re-throw end exit.
                                    raise
                # if no errors and move was successful delete the old directory structure
                shutil.rmtree(full_month_dir, ignore_errors=True)
        DownLoadServiceBase._correct_current_background_link(root_image_dir, is_ftv_enabled=False)


    @staticmethod
    @abkCommon.function_trace
    def _correct_current_background_link(root_image_dir: str, is_ftv_enabled: bool) -> None:
        """Corrects the current background image link to the new directory structure
        Args:
            root_image_dir (str): image directory name where images are stored
            is_ftv_enabled (bool): frame TV directory structure enabled or not
        """
        current_background_file_name = os.path.join(root_image_dir, bwp_config.get(ROOT_KW.CURRENT_BACKGROUND_FILE_NAME.value, ""))
        if os.path.islink(current_background_file_name):
            try:
                current_background_link = os.readlink(current_background_file_name)
                _, img_file_name = os.path.split(current_background_link)
                img_file_name_wo_ext, _ = os.path.splitext(img_file_name)
                img_date_str, _ = img_file_name_wo_ext.split("_")
                curr_bg_date = datetime.datetime.strptime(img_date_str, "%Y-%m-%d")

                if is_ftv_enabled:
                    new_link_target = os.path.join(f"{curr_bg_date.month:02d}", f"{curr_bg_date.day:02d}", img_file_name)
                else:
                    new_link_target = os.path.join(f"{curr_bg_date.year:04d}", f"{curr_bg_date.month:02d}", img_file_name)
                os.symlink(new_link_target, "tmp_link")
                os.rename("tmp_link", current_background_file_name)
            except Exception as exp:
                print(f"{Fore.RED}ERROR: {exp=}{Style.RESET_ALL}")     # type: ignore
                # if there was an error, no worries, this link will be recreated anyway
                pass



class BingDownloadService(DownLoadServiceBase):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    @abkCommon.function_trace
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


class PeapixDownloadService(DownLoadServiceBase):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    @abkCommon.function_trace
    def download_daily_image(self, dst_dir: str) -> str:
        """Downloads bing image and stores it in the defined directory
        Args:
            dst_dir (str): directory to store the image
        Returns:
            str: full file name downloaded
        """
        self._logger.debug(f"{dst_dir=}")
        country_part_url = "=".join(['country', bwp_config[ROOT_KW.REGION.value]])
        get_metadata_url = "?".join([bwp_config[CONSTANT_KW.CONSTANT.value][CONSTANT_KW.PEAPIX_URL.value], country_part_url])
        self._logger.debug(f"Getting Image info from: {get_metadata_url=}")

        is_ftv_dir = DownLoadServiceBase._convert_dir_structure_if_needed()
        self._logger.debug(f"{is_ftv_dir=}")

        # this might throw, but we have a try/catch in the main, so no extra handling here needed.
        # resp = requests.get(get_metadata_url)
        # if resp.status_code == 200: # good case
        #     metadata = self._process_peapix_api_data(resp.json())
        # else:
        #     raise ResponseError(f"ERROR: getting bing image return error code: {resp.status_code}. Cannot proceed.")
        return ""


    @abkCommon.function_trace
    def _process_peapix_api_data(self, metadata: List[Dict[str, str]]) -> List[Dict[str, str]]:  # type: ignore
        """Processes the received meta data from the peapix API and
           keeps only data about images which needs to be downloaded.
           Filters out data about images we already have.
        Args:
            metadata (List[Dict[str, str]]): metadata to be processed
        Returns:
            List[Dict[str, str]]: metadata about images to download
        """
        self._logger.debug(f"Received from API: {json.dumps(metadata, indent=4)}")

        if bwp_config.get(FTV_KW.FTV.value,{}).get(FTV_KW.ENABLED.value, False):
            # store images in this directory format: mm/dd/yyyy-mm-dd.jpg
            self._logger.debug(f"ABK: FTV enabled")
        else:
            # store images in this directory format: yyyy/mm/yyyy-mm-dd.jpg
            self._logger.debug(f"ABK: FTV disabled")

        for img_info in metadata:
            pass
        return metadata


# -----------------------------------------------------------------------------
# OS Dependency
# -----------------------------------------------------------------------------
class IOsDependentBase(metaclass=ABCMeta):
    """OS dependency base class"""
    os_type: abkCommon.OsType

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



# -----------------------------------------------------------------------------
# Bing Wallpaper
# -----------------------------------------------------------------------------
class BingWallPaper(object):
    """BingWallPaper downloads images from bing.com and sets it as a wallpaper"""

    @abkCommon.function_trace
    def __init__(self,
                 logger: logging.Logger,
                 options: Values,
                 os_dependant : IOsDependentBase,
                 dl_service : DownLoadServiceBase
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


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
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

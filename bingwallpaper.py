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
import datetime
import shutil
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from sys import platform as _platform
from typing import Dict, List, Tuple
from urllib.request import urlopen
from xmlrpc.client import Boolean, ResponseError
import requests

# Third party imports
from optparse import Values
from colorama import Fore, Style
from PIL import Image
# from ftv import FTV

# Local application imports
from abkPackage import abkCommon
from config import CONSTANT_KW, FTV_KW, ROOT_KW, bwp_config


BWP_DIRECTORIES = 1
BWP_FILES = 2
BWP_DEFAULT_PIX_DIR = "Pictures/BWP"
BWP_FILE_NAME_WARNING = "Please_do_not_modify_anything_in_this_directory.Handled_by_BingWallpaper_automagic"
BWP_NUMBER_OF_MONTHS = 12
BWP_DIGITS_IN_A_YEAR = 4
BWP_DIGITS_IN_A_MONTH = 2
BWP_DIGITS_IN_A_DAY = 2
BWP_IMG_FILE_EXT = ".jpg"
BWP_DEFAULT_REGION = "us"
BWP_DEFAULT_DL_SERVICE = "peapix"
BWP_SCALE_FILE_PREFIX = "SCALE"
BWP_DEFAULT_IMG_SIZE = (3840, 2160)
BWP_RESIZE_JPEG_QUALITY_MIN = 70
BWP_RESIZE_JPEG_QUALITY_MAX = 100
BWP_DEFAULT_CURRENT_BACKGROUND_LINK_NAME = "current_background.jpg"

# -----------------------------------------------------------------------------
# local functions
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_img_dir() -> str:
    """Defines the image directory, creates if not existent yet
    Returns:
        str: full directory name where images will be saved
    """
    user_home_dir = abkCommon.get_home_dir()
    img_dir = os.path.join(user_home_dir, bwp_config.get(ROOT_KW.IMAGE_DIR.value, BWP_DEFAULT_PIX_DIR))
    abkCommon.ensure_dir(img_dir)
    return img_dir


@lru_cache(maxsize=1)
def get_img_region() -> str:
    """Gets the region from config toml file
    Returns:
        str: region string
    """
    img_region = bwp_config.get(ROOT_KW.REGION.value, BWP_DEFAULT_REGION)
    img_dl_service = bwp_config.get(ROOT_KW.DL_SERVICE.value, BWP_DEFAULT_DL_SERVICE)
    img_alt_region_list = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(CONSTANT_KW.ALT_PEAPIX_REGION.value, [])
    # correct image region to default if something is set to an invalid value
    if img_dl_service == BWP_DEFAULT_DL_SERVICE and img_region not in img_alt_region_list:
        return BWP_DEFAULT_REGION
    if img_dl_service != BWP_DEFAULT_DL_SERVICE and img_region != BWP_DEFAULT_REGION:
        return BWP_DEFAULT_REGION
    return img_region


@lru_cache(maxsize=1)
def is_ftv_enabled() -> bool:
    return bwp_config.get(FTV_KW.FTV.value, {}).get(FTV_KW.ENABLED.value, False)


@lru_cache(maxsize=128)
def get_relative_img_dir(img_date: datetime.date) -> str:
    if is_ftv_enabled():
        return os.path.join(f"{img_date.month:02d}", f"{img_date.day:02d}")
    else:
        return os.path.join(f"{img_date.year:04d}", f"{img_date.month:02d}")


@lru_cache(maxsize=128)
def get_full_img_dir(img_root_dir: str, img_date: datetime.date) -> str:
    return os.path.join(img_root_dir, get_relative_img_dir(img_date))


@lru_cache(maxsize=1)
def get_resize_jpeg_quality() -> int:
    jpeg_quality = bwp_config.get(ROOT_KW.RESIZE_JPEG_QUALITY.value, BWP_RESIZE_JPEG_QUALITY_MIN)
    if jpeg_quality < BWP_RESIZE_JPEG_QUALITY_MIN:
        return BWP_RESIZE_JPEG_QUALITY_MIN
    if jpeg_quality > BWP_RESIZE_JPEG_QUALITY_MAX:
        return BWP_RESIZE_JPEG_QUALITY_MAX
    return jpeg_quality


def update_link(link_file_name:str, new_link_target: str) -> None:
    tmp_link = os.path.join(get_img_dir(), "tmp_link")
    os.symlink(new_link_target, tmp_link)
    os.rename(tmp_link, link_file_name)


@lru_cache(maxsize=1)
def get_background_link_name() -> str:
    """Gets full name for the backgraound image link
    Returns:
        str: background_image link name
    """
    link_name = bwp_config.get(
        ROOT_KW.CURRENT_BACKGROUND.value, BWP_DEFAULT_CURRENT_BACKGROUND_LINK_NAME
    )
    return os.path.join(get_img_dir(), link_name)


# @abkCommon.function_trace
# def get_background_link_info() -> Tuple[str, str]:
#     """ Gets information about the background image link
#         the full link name and the target if exist
#     Returns:
#         Tuple[str, str]: (link_name, target_name)
#     """
#     link_name = get_background_link_name()
#     print(f"ABK:get_background_link_info: {link_name=}")
#     if os.path.exists(link_name) == False:
#         print(f"ABK:get_background_link_info: 1")
#         return (link_name, "")
#     print(f"ABK:get_background_link_info: 2")
#     target_name = abkCommon.read_relative_link(link_name)
#     print(f"ABK:get_background_link_info: 3")
#     return (link_name, target_name)


# -----------------------------------------------------------------------------
# Image Downlaod Data
# -----------------------------------------------------------------------------
@dataclass
class ImageDownloadData():
    imageDate: datetime.date
    title: str
    imageUrl: str
    imagePath: str
    imageName: str


# -----------------------------------------------------------------------------
# DownLoad Service
# -----------------------------------------------------------------------------
class DownLoadServiceBase(metaclass=ABCMeta):

    def __init__(self, logger: logging.Logger) -> None:
        """Super class init"""
        self._logger = logger or logging.getLogger(__name__)


    @abstractmethod
    def download_daily_image(self) -> List[ImageDownloadData]:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplemented


    @staticmethod
    @abkCommon.function_trace
    def convert_dir_structure_if_needed() -> None:
        root_image_dir = get_img_dir()
        # get sub directory names from the defined picture directory
        dir_list = sorted(next(os.walk(root_image_dir))[BWP_DIRECTORIES])
        if len(dir_list) == 0:               # empty pix directory, no conversion needed
            # create an empty warning file
            open(f"{root_image_dir}/{BWP_FILE_NAME_WARNING}", "a").close()
            return

        ftv_enabled = bwp_config.get(FTV_KW.FTV.value, {}).get(FTV_KW.ENABLED.value, False)
        if ftv_enabled:
            filtered_year_dir_list = [bwp_dir for bwp_dir in dir_list if len(bwp_dir) == BWP_DIGITS_IN_A_YEAR and bwp_dir.isdigit()]
            if len(filtered_year_dir_list) > 0:
                DownLoadServiceBase._convert_to_ftv_dir_structure(root_image_dir, filtered_year_dir_list)
        else:
            filtered_month_dir_list = [bwp_dir for bwp_dir in dir_list if len(bwp_dir) == BWP_DIGITS_IN_A_MONTH and bwp_dir.isdigit() and int(bwp_dir) <= BWP_NUMBER_OF_MONTHS]
            if len(filtered_month_dir_list) > 0:
                DownLoadServiceBase._convert_to_date_dir_structure(root_image_dir, filtered_month_dir_list)


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
        region_list = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(CONSTANT_KW.ALT_PEAPIX_REGION.value, [])
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
                                    img_date = datetime.datetime.strptime(img_date_part, "%Y-%m-%d").date()
                                    # print(f"---- ABK: {img_date.year=}, {img_date.month=}, {img_date.day=}, {img_region_part=}")
                                    # looks like a legit file name -> move it the the new location mm/dd/YYYY-mm-dd_us.jpg
                                    img_src = os.path.join(full_month_dir, img_file)
                                    img_dst = os.path.join(root_image_dir, f"{img_date.month:02d}", f"{img_date.day:02d}", img_file)
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
        region_list = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(CONSTANT_KW.ALT_PEAPIX_REGION.value, [])
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
                                    img_date = datetime.datetime.strptime(img_date_part, "%Y-%m-%d").date()
                                    # print(f"---- ABK: {img_date.year=}, {img_date.month=}, {img_date.day=}, {img_region_part=}")
                                    # looks like a legit file name -> move it the the new location YYYY/mm/YYYY-mm-dd_us.jpg
                                    img_src = os.path.join(full_day_dir, img_file)
                                    img_dst = os.path.join(root_image_dir, f"{img_date.year:04d}", f"{img_date.month:02d}", img_file)
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
        current_background_file_name = os.path.join(root_image_dir, bwp_config.get(ROOT_KW.CURRENT_BACKGROUND.value, ""))
        if os.path.islink(current_background_file_name):
            try:
                current_background_link = os.readlink(current_background_file_name)
                _, img_file_name = os.path.split(current_background_link)
                img_file_name_wo_ext, _ = os.path.splitext(img_file_name)
                img_date_str, _ = img_file_name_wo_ext.split("_")
                curr_bg_date = datetime.datetime.strptime(img_date_str, "%Y-%m-%d").date()

                if is_ftv_enabled:
                    new_link_target = os.path.join(f"{curr_bg_date.month:02d}", f"{curr_bg_date.day:02d}", img_file_name)
                else:
                    new_link_target = os.path.join(f"{curr_bg_date.year:04d}", f"{curr_bg_date.month:02d}", img_file_name)
                update_link(current_background_file_name, new_link_target)
            except Exception as exp:
                print(f"{Fore.RED}ERROR: {exp=}{Style.RESET_ALL}")


class BingDownloadService(DownLoadServiceBase):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    @abkCommon.function_trace
    def download_daily_image(self) -> List[ImageDownloadData]:
        """Downloads bing image and stores it in the defined directory"""
        img_data_list: List[ImageDownloadData] = []
        dst_dir = get_img_dir()
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

        # TODO: need to safe file with following name: image_dir/scale_YYYY-mm-dd_us.jpg
        # TODO: because the scaling job will pick it up later to scale to the correct dimention and move it to correct directory
        # return full_file_name
        return img_data_list



class PeapixDownloadService(DownLoadServiceBase):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)


    @abkCommon.function_trace
    def download_daily_image(self) -> List[ImageDownloadData]:
        """Downloads bing image and stores it in the defined directory"""
        dst_dir = get_img_dir()
        self._logger.debug(f"{dst_dir=}")
        country_part_url = "=".join(["country", bwp_config.get(ROOT_KW.REGION.value, "us")])
        get_metadata_url = "?".join([bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(CONSTANT_KW.PEAPIX_URL.value, ""), country_part_url])
        self._logger.debug(f"Getting Image info from: {get_metadata_url=}")

        # this might throw, but we have a try/catch in the main, so no extra handling here needed.
        resp = requests.get(get_metadata_url)
        if resp.status_code == 200: # good case
            dl_img_data = self._process_peapix_api_data(resp.json())
            self._download_images(dl_img_data)
        else:
            raise ResponseError(f"ERROR: getting bing image return error code: {resp.status_code}. Cannot proceed.")
        return dl_img_data


    @abkCommon.function_trace
    def _process_peapix_api_data(self, metadata_list: List[Dict[str, str]]) -> List[ImageDownloadData]:
        """Processes the received meta data from the peapix API and
           keeps only data about images which needs to be downloaded.
           Filters out data about images we already have.
        Args:
            metadata (List[Dict[str, str]]): metadata to be processed
        Returns:
            List[Dict[str, str]]: metadata about images to download
        """
        self._logger.debug(f"Received from API: {json.dumps(metadata_list, indent=4)}")
        IMG_SCALE_PATH_NUMBER = 0
        IMG_LOCAL_PATH_NUMBER = 1
        return_list: List[ImageDownloadData] = []
        img_root_dir = get_img_dir()
        img_region = get_img_region()
        self._logger.debug(f"{img_region=}")

        for img_data in metadata_list:
            try:
                img_date_str = img_data.get("date", "")
                img_date = datetime.datetime.strptime(img_date_str, "%Y-%m-%d").date()
                img_to_check_list = (
                    os.path.join(img_root_dir, f"{BWP_SCALE_FILE_PREFIX}_{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}"),
                    os.path.join(get_full_img_dir(img_root_dir, img_date), f"{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}")
                )

                self._logger.debug(f"{img_to_check_list=}")
                # if all(os.path.exists(imgs_to_check[IMG_SCALE_PATH_NUMBER]) == False and :
                if all([os.path.exists(img_to_check) == False for img_to_check in img_to_check_list]):
                    return_list.append(ImageDownloadData(
                        imageDate=img_date,
                        title=img_data.get("title", ""),
                        imageUrl=img_data.get("imageUrl", ""),
                        imagePath=get_full_img_dir(img_root_dir, img_date),
                        imageName=f"{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}"
                    ))
            except:
                pass # nothing to be done, next

        self._logger.debug(f"Number if images to download: {len(return_list)}")
        self._logger.debug(f"Images to download: {return_list=}")
        return return_list


    @abkCommon.function_trace
    def _download_images(self, img_dl_data_list: List[ImageDownloadData]) -> None:
        root_img_dir = get_img_dir()
        for img_dl_data in img_dl_data_list:
            scale_img_name = os.path.join(root_img_dir, f"{BWP_SCALE_FILE_PREFIX}_{img_dl_data.imageName}")
            try:
                img_data = requests.get(img_dl_data.imageUrl).content
                with open(scale_img_name, mode="wb") as fh:
                    fh.write(img_data)
            except Exception as exp:
                self._logger.error(f"ERROR: {exp=}, downloading image: {scale_img_name}")
        return


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
                 os_dependant: IOsDependentBase,
                 dl_service: DownLoadServiceBase
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._options = options
        self._os_dependent = os_dependant
        self._dl_service = dl_service


    def convert_dir_structure_if_needed(self) -> None:
        """Convert directory structure if needed"""
        self._dl_service.convert_dir_structure_if_needed()


    def set_desktop_background(self, file_name: str) -> None:
        """Sets background image on different OS
        Args:
            file_name (str): file name which should be used to set the background
        """
        self._os_dependent.set_desktop_background(file_name)


    @abkCommon.function_trace
    def scale_images(self, img_data_list: List[ImageDownloadData]) -> None:
        img_root_dir = get_img_dir()

        for img_data in img_data_list:
            scale_img_name = os.path.join(img_root_dir, f"{BWP_SCALE_FILE_PREFIX}_{img_data.imageName}")
            self._resize_store_and_remove(scale_img_name, img_data.imagePath, img_data.imageName)

        # in case there are still SCALE_images left from previous run
        root_img_file_list = sorted(next(os.walk(img_root_dir))[BWP_FILES])
        scale_img_file_list = tuple([img for img in root_img_file_list if img.startswith(BWP_SCALE_FILE_PREFIX)])
        self._logger.debug(f"{scale_img_file_list=}")
        for img_file in scale_img_file_list:
            scale_img_name = os.path.join(img_root_dir, img_file)
            _, img_date_str, img_post_str = img_file.split("_")
            img_date = datetime.datetime.strptime(img_date_str, "%Y-%m-%d").date()
            resized_img_path = get_full_img_dir(img_root_dir, img_date)
            resized_pix_name = "_".join([img_date_str, img_post_str])
            self._resize_store_and_remove(scale_img_name, resized_img_path, resized_pix_name)


    def _resize_store_and_remove(self, scale_img_name: str, resized_img_path: str, resized_img_name: str) -> None:
        resized_full_img_name = os.path.join(resized_img_path, resized_img_name)
        abkCommon.ensure_dir(resized_img_path)
        try:
            with Image.open(scale_img_name) as img:
                self._logger.debug(f"[{scale_img_name}]: {img.size=}")
                resized_img = img.resize(BWP_DEFAULT_IMG_SIZE, Image.Resampling.LANCZOS)
                self._logger.debug(f"{resized_full_img_name=}")
                resized_img.save(resized_full_img_name, optimize=True, quality=get_resize_jpeg_quality())
            os.remove(scale_img_name)
        except OSError as exp:
            self._logger.error(f"ERROR: {exp=}, resizing file: {scale_img_name}")

    @staticmethod
    @abkCommon.function_trace
    def update_current_background_image_link() -> None:
        # check image exist
        # create downscaled version of the last image
        # read link target
        # delete link
        # point the link to the newly create downscaled version
        # print(f"ABK:update_current_background_image_link: {last_know_image=}")
        root_img_dir = get_img_dir()
        today = datetime.date.today()
        print(f"ABK:update_current_background_image_link: {today=}")

        todays_relative_img_path = get_relative_img_dir(today)
        print(f"ABK:update_current_background_image_link: {todays_relative_img_path=}")

        todays_img_name = f"{today.year:04d}-{today.month:02d}-{today.day:02d}_{get_img_region()}{BWP_IMG_FILE_EXT}"
        print(f"ABK:update_current_background_image_link: {todays_img_name=}")

        today_relative_img_name = os.path.join(todays_relative_img_path, todays_img_name)
        print(f"ABK:update_current_background_image_link: {today_relative_img_name=}")

        # link_info = get_background_link_info()
        # print(f"ABK:update_current_background_image_link: {link_info=}")

        if os.path.exists(os.path.join(get_img_dir(), today_relative_img_name)):
            update_link(get_background_link_name(), today_relative_img_name)


    @abkCommon.function_trace
    def trim_number_of_images(self) -> None:
        """Deletes some images if it reaches max number desirable
           The max number of years images to retain can be defined in the config/bwp_config.toml file
        """
        pix_dir = get_img_dir()
        max_years = bwp_config.get(ROOT_KW.YEARS_IMAGES_TO_KEEP.value, 1)
        self._logger.debug(f"{pix_dir=}, {max_years=}")

        # listOfFiles = []
        # for f in os.listdir(pix_dir):
        #     if f.endswith(".jpg"):
        #         listOfFiles.append(f)
        # listOfFiles.sort()
        # self._logger.debug(f"listOfFile = [{', '.join(map(str, listOfFiles))}]")
        # numberOfJpgs = len(listOfFiles)
        # self._logger.info(f"{numberOfJpgs=}")
        # if numberOfJpgs > max_number:
        #     jpgs2delete = listOfFiles[0:numberOfJpgs-max_number]
        #     self._logger.info(f"jpgs2delete = [{', '.join(map(str, jpgs2delete))}]")
        #     num2delete = len(jpgs2delete)
        #     self._logger.info(f"{num2delete=}")
        #     for delFile in jpgs2delete:
        #         self._logger.info(f"deleting file: {delFile}")
        #         try:
        #             os.unlink(os.path.join(pix_dir, delFile))
        #         except:
        #             self._logger.error(f"deleting {delFile} failed")
        # else:
        #     self._logger.info("no images to delete")


    @abkCommon.function_trace
    def download_daily_image(self) -> List[ImageDownloadData]:
        """Downloads bing image and stores it in the defined directory"""
        return self._dl_service.download_daily_image()


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
        if bwp_config.get(ROOT_KW.DL_SERVICE.value, "bing") == "bing":
            dl_service = BingDownloadService(logger=main_logger)
        else:
            dl_service = PeapixDownloadService(logger=main_logger)

        bwp = BingWallPaper(
            logger=main_logger,
            options=command_line_options.options,
            os_dependant=bwp_os_dependent,
            dl_service=dl_service
        )
        bwp.convert_dir_structure_if_needed()
        img_data = bwp.download_daily_image()
        bwp.scale_images(img_data)
        bwp.update_current_background_image_link()

        # is set desktop image enabled
        # if bwp_config.get(ROOT_KW.SET_DESKTOP_IMAGE.value, False):
        #     bwp.set_desktop_background(last_img_name)

        bwp.trim_number_of_images()

        if bwp_config.get(FTV_KW.FTV.value, {}).get(FTV_KW.SET_IMAGE.value, False):
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

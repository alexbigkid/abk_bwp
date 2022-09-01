#!/usr/bin/env python
"""Main program for downloading and upscaling/downscaling bing images to use as wallpaper sized """

# Standard library imports
import os
import sys
import json
import subprocess
import logging
import logging.config
import datetime
import shutil
from enum import Enum
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from sys import platform as _platform
from typing import Dict, List, Tuple, Union
from xmlrpc.client import ResponseError

# Third party imports
import requests
from optparse import Values
from colorama import Fore, Style
from PIL import Image, ExifTags
# from ftv import FTV

# Local application imports
from abkPackage import abkCommon
from config import CONSTANT_KW, DESKTOP_IMG_KW, FTV_KW, ROOT_KW, bwp_config


# -----------------------------------------------------------------------------
# LOcal Constants
# -----------------------------------------------------------------------------
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
BWP_DEFAULT_BING_REGION = "en-US"
BWP_SCALE_FILE_PREFIX = "SCALE"
BWP_DEFAULT_IMG_SIZE = (3840, 2160)
BWP_RESIZE_JPEG_QUALITY_MIN = 70
BWP_RESIZE_JPEG_QUALITY_MAX = 100
BWP_DEFAULT_BACKGROUND_IMG_PREFIX = "background_img"
BWP_BING_NUMBER_OF_IMAGES_TO_REQUEST = 7
BWP_BING_IMG_URL_PREFIX = "http://www.bing.com"
BWP_BING_IMG_URL_POSTFIX = "_1920x1080.jpg"


# -----------------------------------------------------------------------------
# Supported Image Sizes
# -----------------------------------------------------------------------------
class ImageSizes(Enum):
    IMG_640x480     = (640,     480)
    IMG_1024x768    = (1024,    768)
    IMG_1600x1200   = (1600,    1200)
    IMG_1920x1200   = (1920,    1200)
    IMG_3840x2160   = BWP_DEFAULT_IMG_SIZE


# -----------------------------------------------------------------------------
# local functions
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_config_img_dir() -> str:
    """Defines the image directory, creates if not existent yet
    Returns:
        str: full directory name where images will be saved
    """
    user_home_dir = abkCommon.get_home_dir()
    img_dir = os.path.join(user_home_dir, bwp_config.get(ROOT_KW.IMAGE_DIR.value, BWP_DEFAULT_PIX_DIR))
    abkCommon.ensure_dir(img_dir)
    return img_dir


@lru_cache(maxsize=1)
def get_config_img_region() -> str:
    """Gets the region from config toml file
    Returns:
        str: region string
    """
    conf_img_region = bwp_config.get(ROOT_KW.REGION.value, BWP_DEFAULT_REGION)
    conf_img_alt_region_list = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(CONSTANT_KW.ALT_PEAPIX_REGION.value, [])
    for img_region in conf_img_alt_region_list:
        if img_region == conf_img_region:
            return img_region
    else:
        return BWP_DEFAULT_REGION


@lru_cache(maxsize=1)
def get_config_bing_img_region() -> str:
    img_region: str = get_config_img_region()
    img_alt_bing_region_list: List[str] = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(CONSTANT_KW.ALT_BING_REGION.value, [])
    for bing_region in img_alt_bing_region_list:
        if bing_region.endswith(img_region.upper()):
            return bing_region
    else:
        return BWP_DEFAULT_BING_REGION


@lru_cache(maxsize=1)
def is_config_ftv_enabled() -> bool:
    return bwp_config.get(FTV_KW.FTV.value, {}).get(FTV_KW.ENABLED.value, False)


@lru_cache(maxsize=128)
def get_relative_img_dir(img_date: datetime.date) -> str:
    if is_config_ftv_enabled():
        return os.path.join(f"{img_date.month:02d}", f"{img_date.day:02d}")
    else:
        return os.path.join(f"{img_date.year:04d}", f"{img_date.month:02d}")


@lru_cache(maxsize=1)
def get_config_resize_jpeg_quality() -> int:
    jpeg_quality = bwp_config.get(ROOT_KW.RESIZE_JPEG_QUALITY.value, BWP_RESIZE_JPEG_QUALITY_MIN)
    if jpeg_quality < BWP_RESIZE_JPEG_QUALITY_MIN:
        return BWP_RESIZE_JPEG_QUALITY_MIN
    if jpeg_quality > BWP_RESIZE_JPEG_QUALITY_MAX:
        return BWP_RESIZE_JPEG_QUALITY_MAX
    return jpeg_quality


@lru_cache(maxsize=1)
def get_config_background_img_prefix() -> str:
    """Gets full name for the current_backgraound image name
    Returns:
        str: background_image name
    """
    return bwp_config.get(ROOT_KW.BACKGROUND_IMG_PREFIX.value, BWP_DEFAULT_BACKGROUND_IMG_PREFIX)


@lru_cache(maxsize=1)
def get_config_background_img_size() -> Tuple[int, int]:
    width = bwp_config.get(DESKTOP_IMG_KW.DESKTOP_IMG.value, {}).get(DESKTOP_IMG_KW.WIDTH.value, 0)
    height = bwp_config.get(DESKTOP_IMG_KW.DESKTOP_IMG.value, {}).get(DESKTOP_IMG_KW.HEIGHT.value, 0)
    # if missconfigured return default size
    configured_size = (width, height)
    if configured_size not in [img_size.value for img_size in ImageSizes]:
        return BWP_DEFAULT_IMG_SIZE
    return configured_size


def delete_files_in_dir(dir_name: str, file_list: List[str]) -> None:
    # main_logger.debug(f"In directory: {dir_name} deleting files: {file_list}")
    for file_to_delete in file_list:
        try:
            os.remove(os.path.join(dir_name, file_to_delete))
        except Exception as exp:
            # main_logger.error(f"ERROR: {exp=}, deleting file: {file_to_delete}")
            pass


@lru_cache(maxsize=128)
def get_full_img_dir_from_date(img_date: datetime.date) -> str:
    return os.path.join(get_config_img_dir(), get_relative_img_dir(img_date))


def get_full_img_dir_from_file_name(img_file_name: str) -> str:
    img_date = get_date_from_img_file_name(img_file_name)
    return os.path.join(get_config_img_dir(), get_relative_img_dir(img_date))


def get_date_from_img_file_name(img_file_name: str) -> Union[datetime.date, None]:
    try:
        date_str, _ = img_file_name.split("_")
        img_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None
    return img_date


def get_all_background_img_names(dir_name: str) -> List[str]:
    file_name_list = []
    if os.path.isdir(dir_name):
        for _, _, file_list in os.walk(dir_name):
            for file_name in file_list:
                if get_date_from_img_file_name(file_name):
                    file_name_list.append(file_name)
    return sorted(file_name_list)


def get_config_number_of_images_to_keep() -> int:
    number_of_images_to_keep = bwp_config.get(ROOT_KW.NUMBER_OF_IMAGES_TO_KEEP.value, 0)
    if number_of_images_to_keep < 0:
        return 0
    return number_of_images_to_keep


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
# Supported Download services
# -----------------------------------------------------------------------------
class DownloadServiceType(Enum):
    PEAPIX  = "peapix"
    BING    = "bing"


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
        root_image_dir = get_config_img_dir()
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
        main_logger.debug(f"{root_image_dir=}, {year_list=}")
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
                        # main_logger(f"\n---- ABK: {year_dir=}, {month_dir=}, {img_file_list=}")
                        for img_file in img_file_list:
                            file_name, file_ext = os.path.splitext(img_file)
                            # main_logger.debug(f"---- ABK: {file_name=}, {file_ext=}")
                            img_date_part, img_region_part = file_name.split("_")
                            if file_ext == BWP_IMG_FILE_EXT and img_region_part in region_list:
                                try:
                                    img_date = datetime.datetime.strptime(img_date_part, "%Y-%m-%d").date()
                                    # main_logger.debug(f"---- ABK: {img_date.year=}, {img_date.month=}, {img_date.day=}, {img_region_part=}")
                                    # looks like a legit file name -> move it the the new location mm/dd/YYYY-mm-dd_us.jpg
                                    img_src = os.path.join(full_month_dir, img_file)
                                    img_dst = os.path.join(root_image_dir, f"{img_date.month:02d}", f"{img_date.day:02d}", img_file)
                                    # main_logger.debug(f"---- ABK: moving [{img_src}] -> [{img_dst}]")
                                    os.renames(img_src, img_dst)
                                except Exception as exp:
                                    main_logger.error(f"{Fore.RED}ERROR: moving [{img_src=}] to [{img_dst=}] with EXCEPTION: {exp=}. INVESTIGATE!{Style.RESET_ALL}")     # type: ignore
                                    # we don't want to move on here. since there is something wrong, we just re-throw end exit.
                                    raise
                # if no errors and move was successful delete the old directory structure
                shutil.rmtree(full_year_dir, ignore_errors=True)


    @staticmethod
    @abkCommon.function_trace
    def _convert_to_date_dir_structure(root_image_dir: str, month_list: List[str]) -> None:
        """ Converts the bing image frame TV directory structure (mm/dd/YYYY-mm-dd_us.jpg)
            to data directory structure                          (YYYY/mm/YYYY-mm-dd_us.jpg)
        Args:
            root_image_dir (str): directory where images are stored
            month_list (List[str]): month list directory names
        """
        main_logger.debug(f"{root_image_dir=}, {month_list=}")
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
                        # main_logger.debug(f"\n---- ABK: {month_dir=}, {day_dir=}, {img_file_list=}")
                        for img_file in img_file_list:
                            file_name, file_ext = os.path.splitext(img_file)
                            # main_logger.debug(f"---- ABK: {file_name=}, {file_ext=}")
                            img_date_part, img_region_part = file_name.split("_")
                            if file_ext == BWP_IMG_FILE_EXT and img_region_part in region_list:
                                try:
                                    img_date = datetime.datetime.strptime(img_date_part, "%Y-%m-%d").date()
                                    # main_logger.debug(f"---- ABK: {img_date.year=}, {img_date.month=}, {img_date.day=}, {img_region_part=}")
                                    # looks like a legit file name -> move it the the new location YYYY/mm/YYYY-mm-dd_us.jpg
                                    img_src = os.path.join(full_day_dir, img_file)
                                    img_dst = os.path.join(root_image_dir, f"{img_date.year:04d}", f"{img_date.month:02d}", img_file)
                                    # main_logger.debug(f"---- ABK: moving [{img_src}] -> [{img_dst}]")
                                    os.renames(img_src, img_dst)
                                except Exception as exp:
                                    main_logger.error(f"{Fore.RED}ERROR: moving [{img_src=}] to [{img_dst=}] with EXCEPTION: {exp=}. INVESTIGATE!{Style.RESET_ALL}")     # type: ignore
                                    # we don't want to move on here. since there is something wrong, we just re-throw end exit.
                                    raise
                # if no errors and move was successful delete the old directory structure
                shutil.rmtree(full_month_dir, ignore_errors=True)


    @abkCommon.function_trace
    def _download_images(self, img_dl_data_list: List[ImageDownloadData]) -> None:
        root_img_dir = get_config_img_dir()
        for img_dl_data in img_dl_data_list:
            scale_img_name = os.path.join(root_img_dir, f"{BWP_SCALE_FILE_PREFIX}_{img_dl_data.imageName}")
            try:
                img_data = requests.get(img_dl_data.imageUrl).content
                with open(scale_img_name, mode="wb") as fh:
                    fh.write(img_data)
                # TODO: add exif info here
                # self._logger.debug(f"{ExifTags.TAGS=}")
                # im = Image.open(img_data)
                # exif_data = im.getexif()
                # exif_data[0x010e] = img_dl_data.title
                # im.save(f"test_{img_data}", exif=exif_data)
                # im.close()
            except Exception as exp:
                self._logger.error(f"ERROR: {exp=}, downloading image: {scale_img_name}")
        return



class BingDownloadService(DownLoadServiceBase):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)

    @abkCommon.function_trace
    def download_daily_image(self) -> List[ImageDownloadData]:
        """Downloads bing image and stores it in the defined directory"""
        DDI_RESP_FORMAT     = "format=js"
        DDI_RESP_IDX        = "idx=0"
        DDI_RESP_NUMBER     = f"n={BWP_BING_NUMBER_OF_IMAGES_TO_REQUEST}"
        DDI_BING_REGION     = f"mkt={get_config_bing_img_region()}"

        bing_config_url = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(CONSTANT_KW.BING_URL.value, "")
        bing_url_params = "&".join([DDI_RESP_FORMAT, DDI_RESP_IDX, DDI_RESP_NUMBER, DDI_BING_REGION])
        bing_meta_url   = "?".join([bing_config_url, bing_url_params])
        self._logger.debug(f"{bing_meta_url=}")

        resp = requests.get(bing_meta_url)
        if resp.status_code == 200: # good case
            dl_img_data = self._process_bing_api_data(resp.json().get("images", []))
            self._download_images(dl_img_data)
        else:
            raise ResponseError(f"ERROR: getting bing image return error code: {resp.status_code}. Cannot proceed.")
        return dl_img_data


    def _process_bing_api_data(self, metadata_list: list) -> List[ImageDownloadData]:
        return_list: List[ImageDownloadData] = []
        self._logger.debug(f"Received from API: {json.dumps(metadata_list, indent=4)}")
        img_root_dir = get_config_img_dir()
        img_region = get_config_img_region()
        self._logger.debug(f"{img_region=}")


        for img_data in metadata_list:
            try:
                bing_img_date_str = img_data.get("startdate", "")
                img_date = datetime.datetime.strptime(bing_img_date_str, "%Y%m%d").date()
                img_date_str = f"{img_date.year:04d}-{img_date.month:02d}-{img_date.day:02d}"
                img_to_check_list = (
                    os.path.join(img_root_dir, f"{BWP_SCALE_FILE_PREFIX}_{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}"),
                    os.path.join(get_full_img_dir_from_date(img_date), f"{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}")
                )
                img_url_base = img_data.get("urlbase", "")

                self._logger.debug(f"{img_to_check_list=}")
                if all([os.path.exists(img_to_check) == False for img_to_check in img_to_check_list]):
                    return_list.append(ImageDownloadData(
                        imageDate=img_date,
                        title=img_data.get("copyright", ""),
                        imageUrl=f"{BWP_BING_IMG_URL_PREFIX}{img_url_base}{BWP_BING_IMG_URL_POSTFIX}",
                        imagePath=get_full_img_dir_from_date(img_date),
                        imageName=f"{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}"
                    ))

            except:
                pass # nothing to be done, next

        self._logger.debug(f"Number if images to download: {len(return_list)}")
        self._logger.debug(f"Images to download: {return_list=}")
        return return_list



class PeapixDownloadService(DownLoadServiceBase):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)


    @abkCommon.function_trace
    def download_daily_image(self) -> List[ImageDownloadData]:
        """Downloads bing image and stores it in the defined directory"""
        dst_dir = get_config_img_dir()
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
        return_list: List[ImageDownloadData] = []
        img_root_dir = get_config_img_dir()
        img_region = get_config_img_region()
        self._logger.debug(f"{img_region=}")

        for img_data in metadata_list:
            try:
                img_date_str = img_data.get("date", "")
                img_date = datetime.datetime.strptime(img_date_str, "%Y-%m-%d").date()
                img_to_check_list = (
                    os.path.join(img_root_dir, f"{BWP_SCALE_FILE_PREFIX}_{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}"),
                    os.path.join(get_full_img_dir_from_date(img_date), f"{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}")
                )

                self._logger.debug(f"{img_to_check_list=}")
                if all([os.path.exists(img_to_check) == False for img_to_check in img_to_check_list]):
                    return_list.append(ImageDownloadData(
                        imageDate=img_date,
                        title=img_data.get("title", ""),
                        imageUrl=img_data.get("imageUrl", ""),
                        imagePath=get_full_img_dir_from_date(img_date),
                        imageName=f"{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}"
                    ))
            except:
                pass # nothing to be done, next

        self._logger.debug(f"Number if images to download: {len(return_list)}")
        self._logger.debug(f"Images to download: {return_list=}")
        return return_list


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


    @abkCommon.function_trace
    def download_daily_image(self) -> List[ImageDownloadData]:
        """Downloads bing image and stores it in the defined directory"""
        return self._dl_service.download_daily_image()


    def set_desktop_background(self, full_img_name: str) -> None:
        """Sets background image on different OS
        Args:
            file_name (str): file name which should be used to set the background
        """
        self._os_dependent.set_desktop_background(full_img_name)


    @abkCommon.function_trace
    def scale_images(self, img_data_list: List[ImageDownloadData]) -> None:
        img_root_dir = get_config_img_dir()

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
            resized_img_path = get_full_img_dir_from_date(img_date)
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
                resized_img.save(resized_full_img_name, optimize=True, quality=get_config_resize_jpeg_quality())
            os.remove(scale_img_name)
        except OSError as exp:
            self._logger.error(f"ERROR: {exp=}, resizing file: {scale_img_name}")

    @abkCommon.function_trace
    def update_current_background_image(self) -> None:
        config_img_dir = get_config_img_dir()
        today = datetime.date.today()
        today_img_path = get_full_img_dir_from_date(today)
        todays_img_name = f"{today.year:04d}-{today.month:02d}-{today.day:02d}_{get_config_img_region()}{BWP_IMG_FILE_EXT}"
        src_img = os.path.join(today_img_path, todays_img_name)
        if os.path.exists(src_img):
            dst_img_prefix = get_config_background_img_prefix()
            dst_img_size = get_config_background_img_size()
            dst_file_name = f"{dst_img_prefix}_{todays_img_name}"
            dst_img_full_name = os.path.join(config_img_dir, dst_file_name)
            if BingWallPaper._resize_image(src_img, dst_img_full_name, dst_img_size):
                bwp_file_list = sorted(next(os.walk(config_img_dir))[BWP_FILES])
                old_background_img_list = [f for f in bwp_file_list if f.startswith(dst_img_prefix) and f != dst_file_name]
                delete_files_in_dir(config_img_dir, old_background_img_list)
                self.set_desktop_background(dst_img_full_name)


    @staticmethod
    @abkCommon.function_trace
    def _resize_image(src_image: str, dst_image : str, img_size : Tuple[int, int]) -> bool:
        main_logger.debug(f"ABK:_resize_image: {src_image=}, {dst_image=}, {img_size=}")
        try:
            dst_path = os.path.dirname(dst_image)
            main_logger.debug(f"ABK:_resize_image: {dst_path=}")
            abkCommon.ensure_dir(dst_path)
            with Image.open(src_image) as src_img_fh:
                resized_img = src_img_fh.resize(img_size, Image.Resampling.LANCZOS)
                resized_img.save(dst_image, optimize=True, quality=get_config_resize_jpeg_quality())
        except Exception as exp:
            main_logger.error(f"ERROR: {exp=}, resizing file: {src_image=} to {dst_image=} with {img_size=}")
            return False
        return True


    @abkCommon.function_trace
    def trim_number_of_images(self) -> None:
        """Deletes some images if it reaches max number to keep
           The max number of images to retain an be defined in the config/bwp_config.toml file
           config parameter number_of_images_to_keep
        """
        img_dir = get_config_img_dir()
        background_img_file_list = get_all_background_img_names(img_dir)
        max_img_num = get_config_number_of_images_to_keep()
        self._logger.debug(f"{img_dir=}, {len(background_img_file_list)=}, {max_img_num=}")
        self._logger.debug(f"{background_img_file_list=}")

        # do we need to trim number of images collected?
        if (number_to_trim := len(background_img_file_list) - max_img_num) > 0:
            img_to_trim_list = background_img_file_list[0:number_to_trim]
            self._logger.debug(f"{img_to_trim_list=}")
            for img_to_delete in img_to_trim_list:
                img_path = get_full_img_dir_from_file_name(img_to_delete)
                abkCommon.delete_file(os.path.join(img_path, img_to_delete))
                abkCommon.delete_dir(img_path)
                img_parent_dir, _ = os.path.split(img_path)
                abkCommon.delete_dir(img_parent_dir)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    exit_code = 0
    try:
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
        bwp_dl_service = bwp_config.get(ROOT_KW.DL_SERVICE.value, DownloadServiceType.PEAPIX.value)
        if  bwp_dl_service == DownloadServiceType.BING.value:
            dl_service = BingDownloadService(logger=main_logger)
        elif bwp_dl_service == DownloadServiceType.PEAPIX.value:
            dl_service = PeapixDownloadService(logger=main_logger)
        else:
            raise ValueError(f'ERROR: Download service: "{bwp_dl_service=}" is not supported')

        bwp = BingWallPaper(
            logger=main_logger,
            options=command_line_options.options,
            os_dependant=bwp_os_dependent,
            dl_service=dl_service
        )
        bwp.convert_dir_structure_if_needed()
        img_data = bwp.download_daily_image()
        bwp.scale_images(img_data)
        bwp.update_current_background_image()
        bwp.trim_number_of_images()

        if bwp_config.get(FTV_KW.FTV.value, {}).get(FTV_KW.SET_IMAGE.value, False):
            pass
            # ftv = FTV(config_dict.get('ftv'))
            # if ftv.is_art_mode_supported():
            #     ftv.change_daily_images()

    except Exception as exception:
        main_logger.error(f"{Fore.RED}ERROR: executing bingwallpaper")
        main_logger.error(f"EXCEPTION: {exception}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    command_line_options = abkCommon.CommandLineOptions()
    command_line_options.handle_options()
    main_logger = command_line_options._logger
    main()

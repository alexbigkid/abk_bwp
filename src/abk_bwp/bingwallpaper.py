"""Program for downloading and upscaling/downscaling bing images to use as wallpaper sized."""

# Standard lib imports
import io
import json
import logging
import multiprocessing
import os
import re
import shutil
import sqlite3
import subprocess  # noqa: S404
import sys
import threading
from abc import ABCMeta, abstractmethod
from argparse import Namespace
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from functools import lru_cache
from sys import platform as _platform
from typing import Any
from xmlrpc.client import ResponseError

import reactivex as rx

# Third party imports
import requests
from colorama import Fore, Style
from PIL import Image, ImageDraw, ImageFont
from reactivex import operators as ops
from reactivex.scheduler import ThreadPoolScheduler

# Local imports
from abk_bwp import abk_common, clo
from abk_bwp.config import CONSTANT_KW, DESKTOP_IMG_KW, FTV_KW, ROOT_KW, bwp_config
from abk_bwp.db import (
    DB_BWP_FILE_NAME,
    DB_BWP_TABLE,
    SQL_DELETE_OLD_DATA,
    SQL_SELECT_EXISTING,
    DBColumns,
    DbEntry,
    db_sqlite_connect,
    db_sqlite_cursor,
)
from abk_bwp.fonts import get_text_overlay_font_name
from abk_bwp.ftv import FTV
from abk_bwp.lazy_logger import LazyLoggerProxy


logger = LazyLoggerProxy(__name__)


# -----------------------------------------------------------------------------
# Local Constants
# -----------------------------------------------------------------------------
BWP_DIRECTORIES = 1
BWP_FILES = 2
BWP_DEFAULT_PIX_DIR = "Pictures/BingWallpapers"
BWP_FTV_IMAGES_TODAY_DIR = "ftv_images_today"
BWP_FILE_NAME_WARNING = (
    "Please_do_not_modify_anything_in_this_directory.Handled_by_BingWallpaper_automagic"
)
BWP_NUMBER_OF_MONTHS = 12
BWP_DIGITS_IN_A_YEAR = 4
BWP_DIGITS_IN_A_MONTH = 2
BWP_DIGITS_IN_A_DAY = 2
BWP_IMG_FILE_EXT = ".jpg"
BWP_DEFAULT_REGION = "us"
BWP_DEFAULT_BING_REGION = "en-US"
BWP_SCALE_FILE_PREFIX = "SCALE"
BWP_DEFAULT_IMG_SIZE = (3840, 2160)
BWP_RESIZE_MID_IMG_SIZE = (2880, 1620)
BWP_RESIZE_MIN_IMG_SIZE = (1920, 1080)
BWP_RESIZE_JPG_QUALITY_MIN = 70
BWP_RESIZE_JPG_QUALITY_MAX = 100
BWP_FTV_DATA_FILE_DEFAULT = "ftv_data.toml"
BWP_DEFAULT_BACKGROUND_IMG_PREFIX = "background_img"
BWP_BING_NUMBER_OF_IMAGES_TO_REQUEST = 7
BWP_BING_IMG_URL_PREFIX = "http://www.bing.com"
BWP_BING_IMG_URL_POSTFIX = "_1920x1080.jpg"
BWP_META_DATA_FILE_NAME = "IMAGES_METADATA.json"
BWP_EXIF_IMAGE_DESCRIPTION_FIELD = 0x010E
BWP_EXIF_IMAGE_COPYRIGHT_FIELD = 0x8298
BWP_TITLE_TEXT_FONT_SIZE = 42
BWP_TITLE_TEXT_POSITION_OFFSET = (100, 100)
BWP_TITLE_TEXT_COLOR = (255, 255, 255)
BWP_TITLE_GLOW_COLOR = (0, 0, 0)
BWP_TITLE_OUTLINE_AMOUNT = 6
BWP_REQUEST_TIMEOUT = 5  # timeout in seconds
BWP_IMAGES_DOWNLOAD_TIMEOUT = 10
BWP_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_NUMBER_OF_RECORDS_TO_KEEP = 84  # currently supported countries 12 * 7 days (week)
MIN_NUMBER_OF_RECORDS_TO_KEEP = 24  # currently supported countries 12 * 2 days


# -----------------------------------------------------------------------------
# Supported Image Sizes
# -----------------------------------------------------------------------------
class ImageSizes(Enum):
    """Supported Image sizes."""

    IMG_640x480 = (640, 480)
    IMG_1024x768 = (1024, 768)
    IMG_1600x1200 = (1600, 1200)
    IMG_1920x1080 = (1920, 1080)
    IMG_1920x1200 = (1920, 1200)
    IMG_3840x2160 = BWP_DEFAULT_IMG_SIZE


# -----------------------------------------------------------------------------
# local functions
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_config_img_dir() -> str:
    """Defines the image directory, creates if not existent yet.

    Returns:
        str: full directory name where images will be saved
    """
    user_home_dir = abk_common.get_home_dir()
    img_dir = os.path.join(
        user_home_dir, bwp_config.get(ROOT_KW.IMAGE_DIR.value, BWP_DEFAULT_PIX_DIR)
    )
    abk_common.ensure_dir(img_dir)
    return img_dir


@lru_cache(maxsize=1)
def get_config_img_region() -> str:
    """Gets the region from config toml file.

    Returns:
        str: region string
    """
    conf_img_region = bwp_config.get(ROOT_KW.REGION.value, BWP_DEFAULT_REGION)
    conf_img_alt_region_list = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(
        CONSTANT_KW.ALT_PEAPIX_REGION.value, []
    )
    for img_region in conf_img_alt_region_list:
        if img_region == conf_img_region:
            return img_region
    return BWP_DEFAULT_REGION


@lru_cache(maxsize=1)
def get_config_bing_img_region() -> str:
    """Gets the region for the bing service.

    Returns:
        str: region string for Bing
    """
    img_region: str = get_config_img_region()
    img_alt_bing_region_list: list[str] = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(
        CONSTANT_KW.ALT_BING_REGION.value, []
    )
    for bing_region in img_alt_bing_region_list:
        if bing_region.endswith(img_region.upper()):
            return bing_region
    return BWP_DEFAULT_BING_REGION


@lru_cache(maxsize=1)
def is_config_ftv_enabled() -> bool:
    """Determines whether the Frame TV feature is enabled in the config.

    Returns:
        bool: true if Frame TV feature enabled, False otherwise
    """
    return bwp_config.get(FTV_KW.FTV.value, {}).get(FTV_KW.ENABLED.value, False)


@lru_cache(maxsize=128)
def get_relative_img_dir(img_date: date) -> str:
    """Gets the image directory structure depending on whether Frame TV feature is enabled.

    Args:
        img_date (date): date time
    Returns:
        str: image directory structure
    """
    if is_config_ftv_enabled():
        return os.path.join(f"{img_date.month:02d}", f"{img_date.day:02d}")
    return os.path.join(f"{img_date.year:04d}", f"{img_date.month:02d}")


@lru_cache(maxsize=3)
def normalize_jpg_quality(jpg_quality: int) -> int:
    """Normalizes image image quality. It should not be less then minimum and more then maximum.

    Args:
        jpg_quality (int): jpg quality setting
    Returns:
        int: normalized between min and max
    """
    if jpg_quality < BWP_RESIZE_JPG_QUALITY_MIN:
        return BWP_RESIZE_JPG_QUALITY_MIN
    if jpg_quality > BWP_RESIZE_JPG_QUALITY_MAX:
        return BWP_RESIZE_JPG_QUALITY_MAX
    return jpg_quality


@lru_cache(maxsize=1)
def get_config_store_jpg_quality() -> int:
    """Gets jpeg quality for storing images.

    Returns:
        int: jpeg images quality normalized
    """
    jpg_quality = bwp_config.get(ROOT_KW.STORE_JPG_QUALITY.value, BWP_RESIZE_JPG_QUALITY_MIN)
    return normalize_jpg_quality(jpg_quality)


@lru_cache(maxsize=1)
def get_config_desktop_jpg_quality() -> int:
    """Gets jpeg quality for desktop images.

    Returns:
        int: jpeg images quality normalized
    """
    jpg_quality: int = bwp_config.get(DESKTOP_IMG_KW.DESKTOP_IMG.value, {}).get(
        DESKTOP_IMG_KW.JPG_QUALITY.value, BWP_RESIZE_JPG_QUALITY_MIN
    )
    return normalize_jpg_quality(jpg_quality)


@lru_cache(maxsize=1)
def get_config_ftv_jpg_quality() -> int:
    """Gets jpeg quality for Frame TV images feature.

    Returns:
        int: jpeg images quality normalized
    """
    jpg_quality: int = bwp_config.get(FTV_KW.FTV.value, {}).get(
        FTV_KW.JPG_QUALITY.value, BWP_RESIZE_JPG_QUALITY_MIN
    )
    return normalize_jpg_quality(jpg_quality)


@lru_cache(maxsize=1)
def get_config_ftv_data() -> str:
    """Gets the file name for the Frame TV data.

    Returns:
        str: name of the file where secret data for Frame TV are stored
    """
    ftv_data: str = bwp_config.get(FTV_KW.FTV.value, {}).get(
        FTV_KW.FTV_DATA.value, BWP_FTV_DATA_FILE_DEFAULT
    )
    return ftv_data


@lru_cache(maxsize=1)
def get_config_background_img_size() -> tuple[int, int]:
    """Determines background image size dimension.

    Returns:
        Tuple[int, int]: image size dimensions
    """
    width = bwp_config.get(DESKTOP_IMG_KW.DESKTOP_IMG.value, {}).get(
        DESKTOP_IMG_KW.WIDTH.value, 0
    )
    height = bwp_config.get(DESKTOP_IMG_KW.DESKTOP_IMG.value, {}).get(
        DESKTOP_IMG_KW.HEIGHT.value, 0
    )
    configured_size = (width, height)
    # if misconfigured return default size
    if configured_size not in [img_size.value for img_size in ImageSizes]:
        return BWP_DEFAULT_IMG_SIZE
    return configured_size


def delete_files_in_dir(dir_name: str, file_list: list[str]) -> None:
    """Deletes files in given directory.

    Args:
        dir_name (str): directory name
        file_list (List[str]): file list to delete
    """
    # logger.debug(f"In directory: {dir_name} deleting files: {file_list}")
    for file_to_delete in file_list:
        try:
            os.remove(os.path.join(dir_name, file_to_delete))
        except Exception as exp:
            logger.exception(f"ERROR: {exp=}, deleting file: {file_to_delete}")


@lru_cache(maxsize=128)
def get_full_img_dir_from_date(img_date: date) -> str:
    """Gets full image directory name from date.

    Args:
        img_date (date): image date
    Returns:
        str: image directory name
    """
    return os.path.join(get_config_img_dir(), get_relative_img_dir(img_date))


def get_full_img_dir_from_file_name(img_file_name: str) -> str:
    """Gets full image directory name from file name.

    Args:
        img_file_name (str): image file name
    Returns:
        str: image directory name
    """
    img_date = get_date_from_img_file_name(img_file_name)
    return os.path.join(get_config_img_dir(), get_relative_img_dir(img_date))


def get_date_from_img_file_name(img_file_name: str) -> date | None:
    """Gets date from image file name.

    Args:
        img_file_name (str): image file name
    Returns:
        Union[date, None]: image date
    """
    try:
        date_str, _ = img_file_name.split("_")
        img_date = str_to_date(date_str).date()
    except ValueError:
        return None
    return img_date


def get_all_background_img_names(dir_name: str) -> list[str]:
    """Gets all background image names.

    Args:
        dir_name (str): directory name
    Returns:
        List[str]: list of file names
    """
    file_name_list = []
    if os.path.isdir(dir_name):
        for _, _, file_list in os.walk(dir_name):
            for file_name in file_list:
                if get_date_from_img_file_name(file_name):
                    file_name_list.append(file_name)
    return sorted(file_name_list)


def get_config_number_of_images_to_keep() -> int:
    """Gets number of images to keep from config.

    Returns:
        int: number of images to keep
    """
    number_of_images_to_keep = bwp_config.get(ROOT_KW.NUMBER_OF_IMAGES_TO_KEEP.value, 0)
    if number_of_images_to_keep < 0:
        return 0
    return number_of_images_to_keep


def str_to_date(date_str: str) -> datetime:
    """Converts string to date.

    Args:
        date_str (str): date string
    Returns:
        datetime: datetime object
    """
    return datetime.strptime(date_str, BWP_DATE_FORMAT)


# -----------------------------------------------------------------------------
# Image Download Data
# -----------------------------------------------------------------------------
@dataclass
class ImageDownloadData:
    """Image download data."""

    imageDate: date
    title: bytes
    copyright: bytes
    imageUrl: list[str]
    imagePath: str
    imageName: str


# -----------------------------------------------------------------------------
# Supported Download services
# -----------------------------------------------------------------------------
class DownloadServiceType(Enum):
    """Download service type."""

    PEAPIX = "peapix"
    BING = "bing"


# -----------------------------------------------------------------------------
# DownLoad Service
# -----------------------------------------------------------------------------
class DownLoadServiceBase(metaclass=ABCMeta):
    """Class for download service base."""

    def __init__(self, dl_logger: logging.Logger) -> None:
        """Super class init."""
        self._logger = dl_logger or LazyLoggerProxy(__name__)

    @abstractmethod
    def download_new_images(self) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplementedError

    @staticmethod
    @abk_common.function_trace
    def convert_dir_structure_if_needed() -> None:
        """Converts the bing image data directory structure (YYYY/mm/YYYY-mm-dd_us.jpg) to frame TV directory structure (mm/dd/YYYY-mm-dd_us.jpg)."""  # noqa: E501
        root_image_dir = get_config_img_dir()
        # get sub directory names from the defined picture directory
        dir_list = sorted(next(os.walk(root_image_dir))[BWP_DIRECTORIES])
        if len(dir_list) == 0:  # empty pix directory, no conversion needed
            # create an empty warning file
            open(f"{root_image_dir}/{BWP_FILE_NAME_WARNING}", "a", encoding="utf-8").close()
            return

        if is_config_ftv_enabled():
            filtered_year_dir_list = [
                bwp_dir
                for bwp_dir in dir_list
                if len(bwp_dir) == BWP_DIGITS_IN_A_YEAR and bwp_dir.isdigit()
            ]
            if len(filtered_year_dir_list) > 0:
                DownLoadServiceBase._convert_to_ftv_dir_structure(
                    root_image_dir, filtered_year_dir_list
                )
        else:
            filtered_month_dir_list = [
                bwp_dir
                for bwp_dir in dir_list
                if len(bwp_dir) == BWP_DIGITS_IN_A_MONTH
                and bwp_dir.isdigit()
                and int(bwp_dir) <= BWP_NUMBER_OF_MONTHS
            ]
            if len(filtered_month_dir_list) > 0:
                DownLoadServiceBase._convert_to_date_dir_structure(
                    root_image_dir, filtered_month_dir_list
                )

    @staticmethod
    @abk_common.function_trace
    def _convert_to_ftv_dir_structure(root_image_dir: str, year_list: list[str]) -> None:
        """Converts the bing image data directory structure (YYYY/mm/YYYY-mm-dd_us.jpg) to frame TV directory structure (mm/dd/YYYY-mm-dd_us.jpg).

        Args:
            root_image_dir (str): directory where images are stored
            year_list (List[str]): year list directory names
        """  # noqa: E501
        # FTV enabled conversion needed to use mm/dd directory format.
        # logger.debug(f"{root_image_dir=}, {year_list=}")
        region_list = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(
            CONSTANT_KW.ALT_PEAPIX_REGION.value, []
        )
        for year_dir in year_list:
            if len(year_dir) == BWP_DIGITS_IN_A_YEAR and year_dir.isdigit():
                # get the subdirectories of the year
                full_year_dir = os.path.join(root_image_dir, year_dir)
                month_list = sorted(next(os.walk(full_year_dir))[BWP_DIRECTORIES])
                for month_dir in month_list:
                    if (
                        len(month_dir) == BWP_DIGITS_IN_A_MONTH
                        and month_dir.isdigit()
                        and int(month_dir) <= BWP_NUMBER_OF_MONTHS
                    ):
                        full_month_dir = os.path.join(full_year_dir, month_dir)
                        img_file_list = sorted(next(os.walk(full_month_dir))[BWP_FILES])
                        # logger(f"\n---- ABK: {year_dir=}, {month_dir=}, {img_file_list=}")
                        for img_file in img_file_list:
                            file_name, file_ext = os.path.splitext(img_file)
                            # logger.debug(f"---- ABK: {file_name=}, {file_ext=}")
                            img_date_part, img_region_part = file_name.split("_")
                            if file_ext == BWP_IMG_FILE_EXT and img_region_part in region_list:
                                try:
                                    img_date = str_to_date(img_date_part).date()
                                    # logger.debug(f"---- ABK: {img_date.year=}, {img_date.month=}, {img_date.day=}, {img_region_part=}")  # noqa: E501
                                    # looks like a legit file name -> move it the the new location mm/dd/YYYY-mm-dd_us.jpg  # noqa: E501
                                    img_src = os.path.join(full_month_dir, img_file)
                                    img_dst = os.path.join(
                                        root_image_dir,
                                        f"{img_date.month:02d}",
                                        f"{img_date.day:02d}",
                                        img_file,
                                    )
                                    # logger.debug(f"---- ABK: moving [{img_src}] -> [{img_dst}]")  # noqa: E501
                                    os.renames(img_src, img_dst)
                                except Exception as exp:
                                    logger.error(
                                        f"{Fore.RED}ERROR: moving [{img_src=}] to [{img_dst=}] with EXCEPTION: {exp=}. INVESTIGATE!{Style.RESET_ALL}"  # noqa: E501
                                    )  # type: ignore
                                    # we don't want to move on here.
                                    # since there is something wrong, we just re-throw end exit.
                                    raise
                # if no errors and move was successful delete the old directory structure
                shutil.rmtree(full_year_dir, ignore_errors=True)

    @staticmethod
    @abk_common.function_trace
    def _convert_to_date_dir_structure(root_image_dir: str, month_list: list[str]) -> None:
        """Converts the bing image frame TV directory structure (mm/dd/YYYY-mm-dd_us.jpg) to data directory structure (YYYY/mm/YYYY-mm-dd_us.jpg).

        Args:
            root_image_dir (str): directory where images are stored
            month_list (List[str]): month list directory names
        """  # noqa: E501
        logger.debug(f"{root_image_dir=}, {month_list=}")
        region_list = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(
            CONSTANT_KW.ALT_PEAPIX_REGION.value, []
        )
        for month_dir in month_list:
            if (
                len(month_dir) == BWP_DIGITS_IN_A_MONTH
                and month_dir.isdigit()
                and int(month_dir) <= BWP_NUMBER_OF_MONTHS
            ):
                # get the subdirectories of the month
                full_month_dir = os.path.join(root_image_dir, month_dir)
                day_list = sorted(next(os.walk(full_month_dir))[BWP_DIRECTORIES])
                for day_dir in day_list:
                    if len(day_dir) == BWP_DIGITS_IN_A_DAY and day_dir.isdigit():
                        full_day_dir = os.path.join(full_month_dir, day_dir)
                        img_file_list = sorted(next(os.walk(full_day_dir))[BWP_FILES])
                        # logger.debug(f"\n---- ABK: {month_dir=}, {day_dir=}, {img_file_list=}")  # noqa: E501
                        for img_file in img_file_list:
                            file_name, file_ext = os.path.splitext(img_file)
                            # logger.debug(f"---- ABK: {file_name=}, {file_ext=}")
                            img_date_part, img_region_part = file_name.split("_")
                            if file_ext == BWP_IMG_FILE_EXT and img_region_part in region_list:
                                try:
                                    img_date = str_to_date(img_date_part).date()
                                    # logger.debug(f"---- ABK: {img_date.year=}, {img_date.month=}, {img_date.day=}, {img_region_part=}")  # noqa: E501
                                    # looks like a legit file name -> move it the the new location YYYY/mm/YYYY-mm-dd_us.jpg  # noqa: E501
                                    img_src = os.path.join(full_day_dir, img_file)
                                    img_dst = os.path.join(
                                        root_image_dir,
                                        f"{img_date.year:04d}",
                                        f"{img_date.month:02d}",
                                        img_file,
                                    )
                                    # logger.debug(f"---- ABK: moving [{img_src}] -> [{img_dst}]")  # noqa: E501
                                    os.renames(img_src, img_dst)
                                except Exception as exp:
                                    logger.error(
                                        f"{Fore.RED}ERROR: moving [{img_src=}] to [{img_dst=}] \
                                            with EXCEPTION: {exp=}. INVESTIGATE!{Style.RESET_ALL}"
                                    )  # type: ignore
                                    # we don't want to move on here.
                                    # since there is something wrong,
                                    # we just re-throw end exit.
                                    raise
                # if no errors and move was successful delete the old directory structure
                shutil.rmtree(full_month_dir, ignore_errors=True)

    @abk_common.function_trace
    def _download_images(self, img_dl_data_list: list[ImageDownloadData]) -> None:
        """Downloads images using RxPy observer pattern and multithreading.

        Args:
            img_dl_data_list (List[ImageDownloadData]): list of images to download
        """
        thread_count = multiprocessing.cpu_count()
        scheduler = ThreadPoolScheduler(thread_count)

        total = len(img_dl_data_list)
        completed = 0
        lock = threading.Lock()
        done_event = threading.Event()

        def log_progress(_):
            nonlocal completed
            with lock:
                completed += 1
                self._logger.info(f"Downloaded {completed} / {total} images")

        def process_img(img_data):
            self._process_and_download_image(img_data)

        def handle_dl_error(e: Exception, data: ImageDownloadData):
            self._logger.warning(f"⚠️ Failed to download image: {data} ({e})")
            return rx.empty()

        def _on_completed() -> None:
            self._logger.info("✅ All image downloads completed.")
            done_event.set()

        def _on_error(e: Exception) -> None:
            self._logger.error(f"❌ Stream error: {e}")
            done_event.set()

        rx.from_iterable(img_dl_data_list).pipe(
            ops.flat_map(
                lambda data: rx.of(data).pipe(
                    ops.subscribe_on(scheduler),
                    ops.do_action(process_img),
                    ops.retry(3),  # retry up to 3 times
                    ops.catch(lambda e, _: handle_dl_error(e, data)),  # skip if failed item
                    ops.do_action(on_next=log_progress),
                )
            )
        ).subscribe(on_completed=_on_completed, on_error=_on_error)
        # Block until all downloads are complete.
        # Otherwise background image generation & set will fail, the image might not be available
        if not done_event.wait(timeout=BWP_IMAGES_DOWNLOAD_TIMEOUT):
            self._logger.error("❌ Timed out waiting for all downloads to complete.")

    def _process_and_download_image(self, img_dl_data: ImageDownloadData):
        """Process and download image.

        Args:
            img_dl_data (ImageDownloadData): Image download data
        """
        full_img_path = get_full_img_dir_from_file_name(img_dl_data.imageName)
        full_img_name = os.path.join(full_img_path, img_dl_data.imageName)
        self._logger.debug(f"{full_img_name=}")
        try:
            abk_common.ensure_dir(full_img_path)
            for image_url in img_dl_data.imageUrl:
                self._logger.info(f"{image_url = }")
                resp = requests.get(image_url, stream=True, timeout=BWP_REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    with Image.open(io.BytesIO(resp.content)) as img:
                        resized_img = img.resize(BWP_DEFAULT_IMG_SIZE, Image.Resampling.LANCZOS)
                        save_args = {"optimize": True, "quality": get_config_store_jpg_quality()}

                        if img_dl_data.title:
                            exif_data = resized_img.getexif()
                            exif_data.setdefault(
                                BWP_EXIF_IMAGE_DESCRIPTION_FIELD, img_dl_data.title
                            )
                            exif_data.setdefault(
                                BWP_EXIF_IMAGE_COPYRIGHT_FIELD, img_dl_data.copyright
                            )
                            save_args["exif"] = exif_data

                        resized_img.save(full_img_name, **save_args)
                    # we want to download only 1 image with highest quality,
                    # however there were instances where higher quality image download has a
                    # problem, so the next quality image should be downloaded. But once
                    # successful we should exit the loop
                    break
        except Exception as exp:
            self._logger.exception(f"ERROR: {exp=}, downloading image: {full_img_name}")


# -----------------------------------------------------------------------------
# Bing DownLoad Service
# -----------------------------------------------------------------------------
class BingDownloadService(DownLoadServiceBase):
    """Bing Download Service class. Inherited from the base download service class."""

    @abk_common.function_trace
    def download_new_images(self) -> None:
        """Downloads bing image and stores it in the defined directory."""
        ddi_resp_format = "format=js"
        ddi_resp_idx = "idx=0"
        ddi_resp_number = f"n={BWP_BING_NUMBER_OF_IMAGES_TO_REQUEST}"
        ddi_bing_region = f"mkt={get_config_bing_img_region()}"

        bing_config_url = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(
            CONSTANT_KW.BING_URL.value, ""
        )
        bing_url_params = "&".join(
            [ddi_resp_format, ddi_resp_idx, ddi_resp_number, ddi_bing_region]
        )
        bing_meta_url = "?".join([bing_config_url, bing_url_params])
        self._logger.debug(f"{bing_meta_url=}")

        resp = requests.get(bing_meta_url, timeout=BWP_REQUEST_TIMEOUT)
        if resp.status_code == 200:  # good case
            dl_img_data = self._process_bing_api_data(resp.json().get("images", []))
            self._download_images(dl_img_data)
        else:
            raise ResponseError(
                f"ERROR: getting bing image return error code: {resp.status_code}. Cannot proceed"
            )

    def _process_bing_api_data(self, metadata_list: list) -> list[ImageDownloadData]:
        """Processes Bing Service API data.

        Args:
            metadata_list (list): Metadata list from Bing Service API
        Returns:
            List[ImageDownloadData]: Processed data
        """
        return_list: list[ImageDownloadData] = []
        self._logger.debug(f"Received from API: {json.dumps(metadata_list, indent=4)}")
        img_root_dir = get_config_img_dir()
        self._logger.debug(f"{img_root_dir=}")
        img_region = get_config_img_region()
        self._logger.debug(f"{img_region=}")

        for img_data in metadata_list:
            try:
                bing_img_date_str = img_data.get("startdate", "")
                img_date = datetime.strptime(bing_img_date_str, "%Y%m%d").date()
                img_date_str = f"{img_date.year:04d}-{img_date.month:02d}-{img_date.day:02d}"
                full_img_dir = get_full_img_dir_from_date(img_date)
                img_to_check = os.path.join(
                    full_img_dir, f"{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}"
                )
                img_url_base = img_data.get("urlbase", "")
                if os.path.exists(img_to_check) is False:
                    return_list.append(
                        ImageDownloadData(
                            imageDate=img_date,
                            title=img_data.get("copyright", "").encode("utf-8"),
                            copyright=img_data.get("copyright", "").encode("utf-8"),
                            imageUrl=[
                                f"{BWP_BING_IMG_URL_PREFIX}{img_url_base}{BWP_BING_IMG_URL_POSTFIX}"
                            ],
                            imagePath=full_img_dir,
                            imageName=f"{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}",
                        )
                    )
            except Exception:
                self._logger.exception(
                    f"ERROR: processing image data: {img_data=}. EXCEPTION: {sys.exc_info()}"
                )

        self._logger.debug(f"Number if images to download: {len(return_list)}")
        self._logger.debug(f"Images to download: {return_list=}")
        return return_list


# -----------------------------------------------------------------------------
# Peapix DownLoad Service
# -----------------------------------------------------------------------------
class PeapixDownloadService(DownLoadServiceBase):
    """Peapix Download Service class. Inherited from the base download service class."""

    def __init__(self, dls_logger: logging.Logger, bwp_db_file: str | None = None) -> None:
        """Initializes PeapixDownloadService with logger and DB file name.

        Args:
            dls_logger (logging.Logger): Logger instance.
            bwp_db_file (str | None, optional): Path to BWP DB file, useful for tests.
        """
        super().__init__(dls_logger)
        self._bwp_db_file = bwp_db_file or DB_BWP_FILE_NAME

    @abk_common.function_trace
    def download_new_images(self) -> None:
        """Downloads bing image and stores it in the defined directory."""
        dst_dir = get_config_img_dir()
        self._logger.debug(f"{dst_dir=}")
        country = bwp_config.get(ROOT_KW.REGION.value, "us")
        country_part_url = "=".join([DBColumns.COUNTRY.value, country])
        get_metadata_url = "?".join(
            [
                bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(
                    CONSTANT_KW.PEAPIX_URL.value, ""
                ),
                country_part_url,
            ]
        )
        self._logger.debug(f"Getting Image info from: {get_metadata_url=}")

        # this might throw, but we have a try/catch in the bwp, so no extra handling here needed.
        resp = requests.get(get_metadata_url, timeout=BWP_REQUEST_TIMEOUT)
        if resp.status_code == 200:  # good case
            self._logger.debug(f"Received from API: {json.dumps(resp.json(), indent=4)}")
            image_data_list = self._add_date_to_peapix_data(resp.json(), country)
            dl_img_data = self._process_image_data(image_data_list)
            self._download_images(dl_img_data)
        else:
            raise ResponseError(
                f"ERROR: getting bing image return error code: {resp.status_code}. Cannot proceed"
            )

    @abk_common.function_trace
    def _extract_image_id(self, page_url: str) -> int:
        """Extracts image ID from page URL.

        Args:
            page_url (str): page URL
        Returns:
            int: image ID
        Raises:
            ValueError: if invalid page URL format
        """
        match = re.search(r"/bing/(\d+)(?:/|$)", page_url)
        if not match:
            raise ValueError(f"Invalid page URL format: {page_url}")
        return int(match.group(1))

    @abk_common.function_trace
    def _db_get_existing_data(self, conn: sqlite3.Connection) -> dict[int, dict[str, str]]:
        """Gets existing data from DB.

        Args:
            conn (sqlite3.Connection): database connection
        Returns:
            dict[int, str]: existing data
        """
        # cursor = conn.cursor()
        with db_sqlite_cursor(conn) as cursor:
            # cursor.execute(SQL_CREATE_TABLE)
            cursor.execute(SQL_SELECT_EXISTING)
            rows = cursor.fetchall()
        return {
            row[0]: {DBColumns.COUNTRY.value: row[1], DBColumns.DATE.value: row[2]}
            for row in rows
        }

    @abk_common.function_trace
    def _db_insert_metadata(
        self,
        conn: sqlite3.Connection,
        entries: list[DbEntry],
        rec_to_keep: int = MIN_NUMBER_OF_RECORDS_TO_KEEP,
    ) -> None:
        """Inserts image metadata to DB.

        Args:
            conn (sqlite3.Connection): connection
            entries (list[DbEntry]): images metadata
            rec_to_keep (int): number of records to keep
        """
        # cursor = conn.cursor()
        columns = [col.value for col in DBColumns]
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?" for _ in columns])

        sql = f"""
            INSERT OR REPLACE INTO {DB_BWP_TABLE} ({column_names})
            VALUES ({placeholders})
        """  # noqa: S608

        with db_sqlite_cursor(conn) as cursor:
            for entry in entries:
                values = tuple(entry.get(col) for col in columns)
                cursor.execute(sql, values)
            if rec_to_keep > MIN_NUMBER_OF_RECORDS_TO_KEEP:
                self._logger.debug(f"Keeping num of records: {rec_to_keep = }")
                cursor.execute(SQL_DELETE_OLD_DATA, (rec_to_keep,))
        conn.commit()

    @abk_common.function_trace
    def _add_date_to_peapix_data(
        self, img_items: list[dict[str, Any]], country: str
    ) -> list[dict[str, Any]]:
        """Processes image entries and returns back json with dates added.

        Args:
            img_items (list[dict[str, str]]): image json data
            country (str): country code

        Raises:
            RuntimeError: if errors

        Returns:
            list[dict[str, str]]: json list with date included
        """
        # conn = sqlite3.connect(self._bwp_db_file)
        with db_sqlite_connect(self._bwp_db_file) as conn:
            existing = self._db_get_existing_data(conn)

            for entry in img_items:
                entry[DBColumns.PAGE_ID.value] = self._extract_image_id(
                    entry[DBColumns.PAGE_URL.value]
                )

            img_items.sort(key=lambda x: x[DBColumns.PAGE_ID.value], reverse=True)
            image_ids = [e[DBColumns.PAGE_ID.value] for e in img_items]

            if len(image_ids) < 2:
                raise RuntimeError(
                    f"Only {len(image_ids)} image(s) provided (IDs: {image_ids}). Cannot infer country count."  # noqa: E501
                )

            min_id, max_id = min(image_ids), max(image_ids)
            observed_span = max_id - min_id
            country_count = observed_span // (len(image_ids) - 1)

            # country-aware baseline
            known = [
                (img_id, entry[DBColumns.DATE.value])
                for img_id, entry in existing.items()
                if img_id < max_id and entry[DBColumns.COUNTRY.value] == country
            ]

            if not known:
                raise RuntimeError(
                    f"No baseline date found in DB before page ID {max_id} for country '{country}' to infer from."  # noqa: E501
                )

            base_id, base_date_str = max(known, key=lambda x: x[0])
            base_date = str_to_date(base_date_str)
            self._logger.debug(f"{country_count = }, {max_id = }, {base_date = }")

            countries = bwp_config.get(CONSTANT_KW.CONSTANT.value, {}).get(
                CONSTANT_KW.ALT_PEAPIX_REGION.value, []
            )
            self._logger.debug(f"{countries = }")

            new_data = []
            for entry in img_items:
                page_id = entry[DBColumns.PAGE_ID.value]

                offset_days = (page_id - base_id) // country_count
                entry[DBColumns.DATE.value] = (base_date + timedelta(days=offset_days)).strftime(
                    BWP_DATE_FORMAT
                )
                entry[DBColumns.COUNTRY.value] = country
                new_data.append(entry)

            # check if country count changed
            if observed_span % (len(image_ids) - 1) != 0:
                self._db_insert_metadata(conn, new_data)
                return new_data

            # check the position of the given country in the countries list
            country_index = countries.index(country)

            full_data = []
            for _, base_entry in enumerate(new_data):
                base_date = str_to_date(base_entry[DBColumns.DATE.value])
                base_id = base_entry[DBColumns.PAGE_ID.value]

                for i, derived_country in enumerate(countries):
                    derived_id = base_id - (country_index - i)
                    if derived_id in existing:
                        continue

                    full_data.append(
                        {
                            DBColumns.PAGE_ID.value: derived_id,
                            DBColumns.COUNTRY.value: derived_country,
                            DBColumns.DATE.value: base_date.strftime(BWP_DATE_FORMAT),
                            DBColumns.PAGE_URL.value: f"https://peapix.com/bing/{derived_id}",
                        }
                    )
            num_rec_to_keep = max(
                DEFAULT_NUMBER_OF_RECORDS_TO_KEEP, country_count * len(img_items)
            )
            self._logger.debug(f"{num_rec_to_keep = }")
            self._db_insert_metadata(conn, full_data, num_rec_to_keep)
        return new_data

    @abk_common.function_trace
    def _process_image_data(self, metadata_list: list[dict[str, str]]) -> list[ImageDownloadData]:
        """Process metadata from the peapix API & keep only image data which needs to be downloaded.

        Args:
            metadata_list (List[Dict[str, str]]): metadata to be processed
        Returns:
            List[Dict[str, str]]: metadata about images to download
        """  # noqa: E501
        self._logger.debug(f"With added date: {json.dumps(metadata_list, indent=4)}")
        return_list: list[ImageDownloadData] = []
        img_region = get_config_img_region()
        self._logger.debug(f"{img_region=}")

        for img_data in metadata_list:
            try:
                img_date_str = img_data.get(DBColumns.DATE.value, "")
                img_date = str_to_date(img_date_str).date()
                full_img_dir = get_full_img_dir_from_date(img_date)
                img_to_check = os.path.join(
                    full_img_dir, f"{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}"
                )
                if os.path.exists(img_to_check) is False:
                    return_list.append(
                        ImageDownloadData(
                            imageDate=img_date,
                            title=img_data.get("title", "").encode("utf-8"),
                            copyright=img_data.get("copyright", "").encode("utf-8"),
                            imageUrl=[
                                img_data.get("imageUrl", ""),
                                img_data.get("fullUrl", ""),
                                img_data.get("thumbUrl", ""),
                            ],
                            imagePath=full_img_dir,
                            imageName=f"{img_date_str}_{img_region}{BWP_IMG_FILE_EXT}",
                        )
                    )
            except Exception:
                self._logger.exception(
                    f"ERROR: processing image data: {img_data=}. EXCEPTION: {sys.exc_info()}"
                )

        self._logger.debug(f"Number if images to download: {len(return_list)}")
        self._logger.debug(f"Images to download: {return_list=}")
        return return_list


# -----------------------------------------------------------------------------
# OS Dependency Base Class
# -----------------------------------------------------------------------------
class IOsDependentBase(metaclass=ABCMeta):
    """OS dependency base class."""

    os_type: abk_common.OsType

    @abk_common.function_trace
    def __init__(self, osd_logger: logging.Logger = None) -> None:  # type: ignore
        """Super class constructor."""
        self._logger = osd_logger or logging.getLogger(__name__)
        self._logger.info(f"({__class__.__name__}) {self.os_type} OS dependent environment ...")

    @abstractmethod
    def set_desktop_background(self, file_name: str) -> None:
        """Abstract method - should not be implemented. Interface purpose."""
        raise NotImplementedError


# -----------------------------------------------------------------------------
# OS Dependency MacOS Class
# -----------------------------------------------------------------------------
class MacOSDependent(IOsDependentBase):
    """MacOS dependent code."""

    @abk_common.function_trace
    def __init__(self, macos_logger: logging.Logger) -> None:
        """Constructor for MacOS."""
        self.os_type = abk_common.OsType.MAC_OS
        super().__init__(macos_logger)

    @abk_common.function_trace
    def set_desktop_background(self, file_name: str) -> None:
        """Sets desktop image on Mac OS.

        Args:
            file_name (str): file name which should be used to set the background
        """
        self._logger.debug(f"{file_name = }")
        script_mac = """/usr/bin/osascript<<END
tell application "Finder"
set desktop picture to POSIX file "%s"
end tell
END"""
        subprocess.call(script_mac % file_name, shell=True)  # noqa: S602
        self._logger.info(f"({self.os_type.value}) Set background to {file_name}")


# -----------------------------------------------------------------------------
# OS Dependency Linux Class
# -----------------------------------------------------------------------------
class LinuxDependent(IOsDependentBase):
    """Linux dependent code."""

    @abk_common.function_trace
    def __init__(self, ld_logger: logging.Logger) -> None:
        """Constructor for Linux."""
        self.os_type = abk_common.OsType.LINUX_OS
        super().__init__(ld_logger)

    @abk_common.function_trace
    def set_desktop_background(self, file_name: str) -> None:
        """Sets desktop image on Linux.

        Args:
            file_name (str): file name which should be used to set the background
        """
        self._logger.debug(f"{file_name=}")
        self._logger.info(f"({self.os_type.value}) Set background to {file_name}")
        self._logger.info(f"({self.os_type.value}) Not implemented yet")


# -----------------------------------------------------------------------------
# OS Dependency Windows Class
# -----------------------------------------------------------------------------
class WindowsDependent(IOsDependentBase):
    """Windows dependent code."""

    @abk_common.function_trace
    def __init__(self, logger: logging.Logger) -> None:
        """Constructor for Windows."""
        self.os_type = abk_common.OsType.WINDOWS_OS
        super().__init__(logger)

    @abk_common.function_trace
    def set_desktop_background(self, file_name: str) -> None:
        """Sets desktop image on Windows.

        Args:
            file_name (str): file name which should be used to set the background
        """
        self._logger.debug(f"{file_name=}")
        import ctypes
        import platform

        win_num = platform.uname()[2]
        self._logger.info(f"os info: {platform.uname()}")
        self._logger.info(f"win#: {win_num}")
        if int(win_num) >= 10:
            try:
                ctypes.windll.user32.SystemParametersInfoW(20, 0, file_name, 3)  # type: ignore
                self._logger.info(f"Background image set to: {file_name}")
            except Exception:
                self._logger.error(f"Was not able to set background image to: {file_name}")
        else:
            self._logger.error(
                f"Windows 10 and above is supported, you are using Windows {win_num}"
            )
        self._logger.info(f"({self.os_type.value}) Not tested yet")
        self._logger.info(f"({self.os_type.value}) Set background to {file_name}")


# -----------------------------------------------------------------------------
# Bing Wallpaper
# -----------------------------------------------------------------------------
class BingWallPaper:
    """BingWallPaper downloads images from bing.com and sets it as a wallpaper."""

    @abk_common.function_trace
    def __init__(
        self,
        bw_logger: logging.Logger,
        options: Namespace,
        os_dependant: IOsDependentBase,
        dl_service: DownLoadServiceBase,
    ):
        """Constructor for BingWallPaper."""
        self._logger = bw_logger or logging.getLogger(__name__)
        self._options = options
        self._os_dependent = os_dependant
        self._dl_service = dl_service

    def convert_dir_structure_if_needed(self) -> None:
        """Convert directory structure if needed."""
        self._dl_service.convert_dir_structure_if_needed()

    @abk_common.function_trace
    def download_new_images(self) -> None:
        """Downloads bing image and stores it in the defined directory."""
        self._dl_service.download_new_images()

    def set_desktop_background(self, full_img_name: str) -> None:
        """Sets background image on different OS.

        Args:
            full_img_name (str): file image name which should be used to set the background
        """
        self._os_dependent.set_desktop_background(full_img_name)

    @staticmethod
    @abk_common.function_trace
    def process_manually_downloaded_images() -> None:
        """Processes manually downloaded images."""
        img_root_dir = get_config_img_dir()
        img_metadata = abk_common.read_json_file(
            os.path.join(img_root_dir, BWP_META_DATA_FILE_NAME)
        )
        logger.debug(f"{json.dumps(img_metadata, indent=4)}")
        # root_img_file_list = sorted(next(os.walk(img_root_dir))[BWP_FILES])
        first_walk = next(iter(os.walk(img_root_dir)))
        root_img_file_list = sorted(first_walk[BWP_FILES])
        scale_img_file_list = tuple(
            [img for img in root_img_file_list if img.startswith(BWP_SCALE_FILE_PREFIX)]
        )
        logger.debug(f"{scale_img_file_list=}")
        for img_file in scale_img_file_list:
            scale_img_name = os.path.join(img_root_dir, img_file)
            _, img_date_str, img_post_str = img_file.split("_")
            img_date = str_to_date(img_date_str).date()
            resized_img_path = get_full_img_dir_from_date(img_date)
            resized_img_name = "_".join([img_date_str, img_post_str])
            resized_full_img_name = os.path.join(resized_img_path, resized_img_name)
            abk_common.ensure_dir(resized_img_path)
            try:
                with Image.open(scale_img_name) as img:
                    new_size = BingWallPaper._calculate_image_resizing(img.size)
                    logger.debug(f"[{resized_full_img_name}]: {img.size=}, {new_size=}")
                    resized_img = (
                        img
                        if img.size == new_size
                        else img.resize(new_size, Image.Resampling.LANCZOS)
                    )
                    if img_title := img_metadata.get(resized_img_name, None):
                        exif_data = resized_img.getexif()
                        exif_data.setdefault(BWP_EXIF_IMAGE_DESCRIPTION_FIELD, img_title)
                        logger.debug(f"process_manually_downloaded_images: {img_title=}")
                        resized_img.save(
                            resized_full_img_name,
                            exif=exif_data,
                            optimize=True,
                            quality=get_config_store_jpg_quality(),
                        )
                    else:
                        resized_img.save(
                            resized_full_img_name,
                            optimize=True,
                            quality=get_config_store_jpg_quality(),
                        )
                os.remove(scale_img_name)
            except OSError as exp:
                logger.exception(f"ERROR: {exp=}, resizing file: {scale_img_name}")

    @staticmethod
    @abk_common.function_trace
    def _calculate_image_resizing(img_size: tuple[int, int]) -> tuple[int, int]:
        """Calculates image re-sizing.

        Args:
            img_size (Tuple[int, int]): image size in
        Returns:
            Tuple[int, int]: image size out
        """
        WIDTH = 0
        HEIGHT = 1
        if img_size in (BWP_RESIZE_MIN_IMG_SIZE, BWP_DEFAULT_IMG_SIZE):
            return img_size
        # if we are over mid threshold scale to default image size BWP_DEFAULT_IMG_SIZE(3840x2160)
        if (
            img_size[WIDTH] > BWP_RESIZE_MID_IMG_SIZE[WIDTH]
            or img_size[HEIGHT] > BWP_RESIZE_MID_IMG_SIZE[HEIGHT]
        ):
            return BWP_DEFAULT_IMG_SIZE
        return BWP_RESIZE_MIN_IMG_SIZE

    @abk_common.function_trace
    def update_current_background_image(self) -> None:
        """Updates current background image."""
        config_img_dir = get_config_img_dir()
        today = date.today()
        today_img_path = get_full_img_dir_from_date(today)
        todays_img_name = f"{today.year:04d}-{today.month:02d}-{today.day:02d}_{get_config_img_region()}{BWP_IMG_FILE_EXT}"  # noqa: E501
        src_img = os.path.join(today_img_path, todays_img_name)
        if os.path.exists(src_img):
            dst_img_size = get_config_background_img_size()
            dst_file_name = f"{BWP_DEFAULT_BACKGROUND_IMG_PREFIX}_{todays_img_name}"
            dst_img_full_name = os.path.join(config_img_dir, dst_file_name)
            if BingWallPaper._resize_background_image(src_img, dst_img_full_name, dst_img_size):
                first_walk = next(iter(os.walk(config_img_dir)))
                bwp_file_list = sorted(first_walk[BWP_FILES])
                old_background_img_list = [
                    f
                    for f in bwp_file_list
                    if f.startswith(BWP_DEFAULT_BACKGROUND_IMG_PREFIX) and f != dst_file_name
                ]
                delete_files_in_dir(config_img_dir, old_background_img_list)
                self.set_desktop_background(dst_img_full_name)

    @staticmethod
    @abk_common.function_trace
    def _resize_background_image(
        src_img_name: str, dst_img_name: str, dst_img_size: tuple[int, int]
    ) -> bool:
        """Resizes background image."""
        logger.debug(f"{src_img_name=}, {dst_img_name=}, {dst_img_size=}")
        try:
            dst_path = os.path.dirname(dst_img_name)
            logger.debug(f"{dst_path=}")
            abk_common.ensure_dir(dst_path)
            with Image.open(src_img_name) as src_img:
                # check whether resize is needed
                if dst_img_size == src_img.size or dst_img_size == (0, 0):
                    resized_img = src_img.convert("RGB")
                else:
                    resized_img = src_img.resize(dst_img_size, Image.Resampling.LANCZOS).convert(
                        "RGB"
                    )
                # resized_img = src_img if src_img.size == dst_img_size else src_img.resize(dst_img_size, Image.Resampling.LANCZOS)  # noqa: E501
                # check if image title available and it can be written as overlay
                if (exif_data := src_img.getexif()) is not None and (
                    title_value := exif_data.get(BWP_EXIF_IMAGE_DESCRIPTION_FIELD, None)
                ) is not None:
                    # title_bytes = title_value.encode('latin-1').split(b'\x00', 1)[0]
                    title_bytes = title_value.encode("ISO-8859-1").split(b"\x00", 1)[0]
                    title_txt = title_bytes.decode("utf-8", errors="ignore")
                    logger.debug(f"_resize_background_image: {title_txt = }")

                    copyright_txt = ""
                    if (
                        copyright_value := exif_data.get(BWP_EXIF_IMAGE_COPYRIGHT_FIELD, "")
                    ) != "":
                        copyright_bytes = copyright_value.encode("ISO-8859-1").split(b"\x00", 1)[
                            0
                        ]
                        copyright_txt = copyright_bytes.decode("utf-8", errors="ignore")
                    logger.debug(f"_resize_background_image: {copyright_txt = }")

                    BingWallPaper.add_outline_text(resized_img, title_txt, copyright_txt)
                    resized_img.save(
                        dst_img_name, optimize=True, quality=get_config_desktop_jpg_quality()
                    )
        except Exception as exp:
            logger.exception(
                f"ERROR:_resize_background_image: {exp=}, resizing file: {src_img_name=} to \
                    {dst_img_name=} with {dst_img_size=}"
            )
            return False
        return True

    @staticmethod
    @abk_common.function_trace
    def add_outline_text(resized_img: Image.Image, title_txt: str, copyright_txt: str) -> None:
        """Adds an outlined (Glow effect) text to the image.

        Args:
            resized_img (Image.Image): image the text will be added to
            title_txt (str): text to add to the image
            copyright_txt (str): copyright text to add to the image
        """
        WIDTH = 0
        HEIGHT = 1
        title_font = ImageFont.truetype(get_text_overlay_font_name(), BWP_TITLE_TEXT_FONT_SIZE)
        longest_txt = title_txt if len(copyright_txt) < len(title_txt) else copyright_txt
        if copyright_txt != "":
            title_txt = f"{title_txt}\n{copyright_txt}"
        _, _, title_width, title_height = title_font.getbbox(longest_txt)
        resized_img_size = resized_img.size
        # location to place text
        x = resized_img_size[WIDTH] - title_width - BWP_TITLE_TEXT_POSITION_OFFSET[WIDTH]
        y = resized_img_size[HEIGHT] - title_height - BWP_TITLE_TEXT_POSITION_OFFSET[HEIGHT]

        draw = ImageDraw.Draw(resized_img)
        for i in range(BWP_TITLE_OUTLINE_AMOUNT):
            draw.text(
                xy=(x + i, y), text=title_txt, font=title_font, fill=BWP_TITLE_GLOW_COLOR
            )  # move text to the left
            draw.text(
                xy=(x - i, y), text=title_txt, font=title_font, fill=BWP_TITLE_GLOW_COLOR
            )  # move text to the right
            draw.text(
                xy=(x, y - i), text=title_txt, font=title_font, fill=BWP_TITLE_GLOW_COLOR
            )  # move text down
            draw.text(
                xy=(x, y + i), text=title_txt, font=title_font, fill=BWP_TITLE_GLOW_COLOR
            )  # move text up
            draw.text(
                xy=(x + i, y + i), text=title_txt, font=title_font, fill=BWP_TITLE_GLOW_COLOR
            )  # move right and up
            draw.text(
                xy=(x + i, y - i), text=title_txt, font=title_font, fill=BWP_TITLE_GLOW_COLOR
            )  # move right and down
            draw.text(
                xy=(x - i, y + i), text=title_txt, font=title_font, fill=BWP_TITLE_GLOW_COLOR
            )  # move left and up
            draw.text(
                xy=(x - i, y - i), text=title_txt, font=title_font, fill=BWP_TITLE_GLOW_COLOR
            )  # move left and down
        draw.text(
            xy=(x, y), text=title_txt, font=title_font, fill=BWP_TITLE_TEXT_COLOR
        )  # write actual text

    @staticmethod
    @abk_common.function_trace
    def trim_number_of_images() -> None:
        """Deletes some images if it reaches max number to keep.

        The max number of images to retain to be defined in the abk_bwp/config/bwp_config.toml
        file config parameter number_of_images_to_keep.
        """
        img_dir = get_config_img_dir()
        background_img_file_list = get_all_background_img_names(img_dir)
        max_img_num = get_config_number_of_images_to_keep()
        logger.debug(f"{img_dir=}, {len(background_img_file_list)=}, {max_img_num=}")
        logger.debug(f"{background_img_file_list=}")

        # do we need to trim number of images collected?
        if (number_to_trim := len(background_img_file_list) - max_img_num) > 0:
            img_to_trim_list = background_img_file_list[0:number_to_trim]
            logger.debug(f"{img_to_trim_list=}")
            for img_to_delete in img_to_trim_list:
                img_path = get_full_img_dir_from_file_name(img_to_delete)
                abk_common.delete_file(os.path.join(img_path, img_to_delete))
                abk_common.delete_dir(img_path)
                img_parent_dir, _ = os.path.split(img_path)
                abk_common.delete_dir(img_parent_dir)

    @staticmethod
    @abk_common.function_trace
    def prepare_ftv_images() -> list:
        """Prepares images for Frame TV."""
        config_img_dir = get_config_img_dir()
        ftv_dir = os.path.join(config_img_dir, BWP_FTV_IMAGES_TODAY_DIR)
        abk_common.ensure_dir(ftv_dir)
        # ftv_files_to_delete = sorted(next(os.walk(ftv_dir))[BWP_FILES])
        first_walk = next(iter(os.walk(ftv_dir)))
        ftv_files_to_delete = sorted(first_walk[BWP_FILES])
        logger.debug(f"prepare_ftv_images: {ftv_dir=}")
        logger.debug(f"prepare_ftv_images: {ftv_files_to_delete=}")
        delete_files_in_dir(dir_name=ftv_dir, file_list=ftv_files_to_delete)

        today = date.today()
        todays_dir = get_full_img_dir_from_date(today)
        # to_copy_file_list = sorted(next(os.walk(todays_dir))[BWP_FILES])
        first_walk = next(iter(os.walk(todays_dir)))
        to_copy_file_list = sorted(first_walk[BWP_FILES])
        logger.debug(f"prepare_ftv_images: {todays_dir=}")
        logger.debug(f"prepare_ftv_images: {to_copy_file_list=}")

        dst_file_list = []
        for img in to_copy_file_list:
            src_img_file_name = os.path.join(todays_dir, img)
            dst_img_file_name = os.path.join(ftv_dir, img)
            BingWallPaper._resize_background_image(
                src_img_file_name, dst_img_file_name, BWP_DEFAULT_IMG_SIZE
            )
            dst_file_list.append(dst_img_file_name)
        return dst_file_list


# -----------------------------------------------------------------------------
# bwp
# -----------------------------------------------------------------------------
def bingwallpaper(bwp_clo: clo.CommandLineOptions) -> None:
    """Main function to run the BingWallpaper application."""
    exit_code = 0
    try:
        # get the correct OS and instantiate OS dependent code
        if _platform in abk_common.OsPlatformType.PLATFORM_MAC.value:
            bwp_os_dependent = MacOSDependent(macos_logger=bwp_clo.logger)
        elif _platform in abk_common.OsPlatformType.PLATFORM_LINUX.value:
            bwp_os_dependent = LinuxDependent(ld_logger=bwp_clo.logger)
        elif _platform in abk_common.OsPlatformType.PLATFORM_WINDOWS.value:
            bwp_os_dependent = WindowsDependent(logger=bwp_clo.logger)
        else:
            raise ValueError(f'ERROR: "{_platform}" is not supported')

        # use bing service as default, peapix is for a back up solution
        bwp_dl_service = bwp_config.get(
            ROOT_KW.DL_SERVICE.value, DownloadServiceType.PEAPIX.value
        )
        if bwp_dl_service == DownloadServiceType.BING.value:
            dl_service = BingDownloadService(dl_logger=bwp_clo.logger)
        elif bwp_dl_service == DownloadServiceType.PEAPIX.value:
            dl_service = PeapixDownloadService(dls_logger=bwp_clo.logger)
        else:
            raise ValueError(f'ERROR: Download service: "{bwp_dl_service=}" is not supported')

        bwp = BingWallPaper(
            bw_logger=bwp_clo.logger,
            options=bwp_clo.options,
            os_dependant=bwp_os_dependent,
            dl_service=dl_service,
        )
        bwp.convert_dir_structure_if_needed()
        bwp.download_new_images()
        BingWallPaper.process_manually_downloaded_images()
        bwp.update_current_background_image()
        BingWallPaper.trim_number_of_images()

        if is_config_ftv_enabled():
            ftv_image_list = BingWallPaper.prepare_ftv_images()
            ftv = FTV(logger=bwp_clo.logger, ftv_data_file=get_config_ftv_data())
            ftv.change_daily_images(ftv_image_list)

    except Exception as exception:
        bwp_clo.logger.error(f"{Fore.RED}ERROR: executing bingwallpaper")
        bwp_clo.logger.error(f"EXCEPTION: {exception}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    command_line_options = clo.CommandLineOptions()
    command_line_options.handle_options()
    bwp_logger = command_line_options.logger
    bingwallpaper(command_line_options)

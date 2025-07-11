"""Loading config."""

from enum import Enum
import pathlib

import tomllib  # type: ignore


bwp_file_name = pathlib.Path(__file__).parent.joinpath("bwp_config.toml")
with bwp_file_name.open(mode="rb") as file_handler:
    bwp_config = tomllib.load(file_handler)


class ROOT_KW(Enum):
    """Loads root level key words."""

    IMG_AUTO_FETCH = "img_auto_fetch"
    TIME_TO_FETCH = "time_to_fetch"
    IMAGE_DIR = "image_dir"
    STORE_JPG_QUALITY = "store_jpg_quality"
    NUMBER_OF_IMAGES_TO_KEEP = "number_of_images_to_keep"
    SET_DESKTOP_IMAGE = "set_desktop_image"
    RETAIN_IMAGES = "retain_images"
    DL_SERVICE = "dl_service"
    REGION = "region"


class DESKTOP_IMG_KW(Enum):
    """Loads desktop image key words."""

    DESKTOP_IMG = "desktop_img"
    ENABLED = "enabled"
    WIDTH = "width"
    HEIGHT = "height"
    JPG_QUALITY = "jpg_quality"
    ALT_DIMENSION = "alt_dimension"


class CONSTANT_KW(Enum):
    """Loads constants key words."""

    CONSTANT = "constant"
    ALT_DL_SERVICE = "alt_dl_service"
    BING_URL = "bing_url"
    PEAPIX_URL = "peapix_url"
    ALT_PEAPIX_REGION = "alt_peapix_region"
    ALT_BING_REGION = "alt_bing_region"


class FTV_KW(Enum):
    """Loads FTV key words."""

    FTV = "ftv"
    ENABLED = "enabled"
    USB_MODE = "usb_mode"
    JPG_QUALITY = "jpg_quality"
    FTV_DATA = "ftv_data"


class RETRY_KW(Enum):
    """Loads retry key words."""

    RETRY = "retry"
    ENABLED = "enabled"
    MAX_ATTEMPTS_PER_DAY = "max_attempts_per_day"
    DAILY_RESET_TIME = "daily_reset_time"
    REQUIRE_ALL_OPERATIONS_SUCCESS = "require_all_operations_success"

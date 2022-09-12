from enum import Enum
import pathlib
# this ensures it will work with python 3.7 and up
try:
    # for python 3.11 and up
    import tomllib              # type: ignore
except ModuleNotFoundError:
    # for 3.7 <= python < 3.11
    import tomli as tomllib     # type: ignore


bwp_file_name = pathlib.Path(__file__).parent / 'bwp_config.toml'
with bwp_file_name.open(mode='rb') as file_handler:
    bwp_config = tomllib.load(file_handler)


class ROOT_KW(Enum):
    TIME_TO_FETCH = "time_to_fetch"
    IMAGE_DIR = "image_dir"
    BACKGROUND_IMG_PREFIX = "background_img_prefix"
    STORE_JPG_QUALITY = "store_jpg_quality"
    NUMBER_OF_IMAGES_TO_KEEP = "number_of_images_to_keep"
    SET_DESKTOP_IMAGE = "set_desktop_image"
    RETAIN_IMAGES = "retain_images"
    DL_SERVICE = "dl_service"
    REGION = "region"


class DESKTOP_IMG_KW(Enum):
    DESKTOP_IMG = "desktop_img"
    ENABLED = "enabled"
    WIDTH = "width"
    HEIGHT = "height"
    JPG_QUALITY = "jpg_quality"
    ALT_DIMENTION = "alt_dimention"


class CONSTANT_KW(Enum):
    CONSTANT = "constant"
    ALT_DL_SERVICE = "alt_dl_service"
    BING_URL = "bing_url"
    PEAPIX_URL = "peapix_url"
    ALT_PEAPIX_REGION = "alt_peapix_region"
    ALT_BING_REGION = "alt_bing_region"


class FTV_KW(Enum):
    FTV = "ftv"
    ENABLED = "enabled"
    JPG_QUALITY = "jpg_quality"
    IP_ADDRESS = "ip_address"
    PORT = "port"
    IMAGE_CHANGE_FREQUENCY = "image_change_frequency"

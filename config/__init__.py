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
    APP_NAME = "app_name"
    IMAGE_DIR = "image_dir"
    CURRENT_BACKGROUND_FILE_NAME = "current_background_file_name"
    NUMBER_IMAGES_TO_KEEP = "number_images_to_keep"
    SET_DESKTOP_IMAGE = "set_desktop_image"
    RETAIN_IMAGES = "retain_images"
    DL_SERVICE = "dl_service"
    REGION = "region"


class CONSTANT_KW(Enum):
    CONSTANT = "constant"
    DL_SERVICE_ALTERNATIVES = "dl_service_alternatives"
    BING_URL = "bing_url"
    PEAPIX_URL = "peapix_url"
    PEAPIX_REGION_ALTERNATIVES = "peapix_region_alternatives"


class FTV_KW(Enum):
    FTV = "ftv"
    ENABLED = "enabled"
    SET_IMAGE = "set_image"
    IP_ADDRESS = "ip_address"
    PORT = "port"
    IMAGE_CHANGE_FREQUENCY = "image_change_frequency"

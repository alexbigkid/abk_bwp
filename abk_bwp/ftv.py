"""Main function or entry module for the ABK BingWallPaper (abk_bwp) package"""

# Standard lib imports
from dataclasses import dataclass
from enum import Enum
import json
import os
import logging
import pathlib
from typing import NamedTuple
import wakeonlan
try:                            # for python 3.11 and up
    import tomllib              # type: ignore
except ModuleNotFoundError:     # for 3.7 <= python < 3.11
    import tomli as tomllib     # type: ignore

# Third party imports
from jsonschema import validate, exceptions
from samsungtvws import SamsungTVWS
# from samsungtvws.remote import SamsungTVWS
# from samsungtvws.art import SamsungTVArt
# from samsungtvws import SamsungTVArt

# local imports
import abk_common



# -----------------------------------------------------------------------------
# Local Constants
# -----------------------------------------------------------------------------
FTV_API_TOKEN_FILE_SUFFIX = '__api_token.txt'
FTV_UPLOADED_IMAGE_FILES = f'{os.path.dirname(os.path.realpath(__file__))}/ftv_uploaded_image_files.json'



# -----------------------------------------------------------------------------
# Local data definitions
# -----------------------------------------------------------------------------
class FTVData(NamedTuple):
    """FTV - Frame TV properties"""
    api_token: str
    img_rate: int
    ip_addr: str
    mac_addr: str
    port: int


@dataclass
class FTVSetting:
    """FTV - Frame TV setting"""
    ftv: SamsungTVWS
    img_rate: int
    mac_addr: str
    reachable: bool = False


class FTV_DATA_KW(Enum):
    """FTV - Frame TV data keywords"""
    IP_ADDR = "ip_addr"
    IMG_RATE = "img_rate"
    MAC_ADDR = "mac_addr"
    PORT = "port"


class FTVSupportedFileType(Enum):
    """FTV - Frame TV supported file types"""
    JPEG = "JPEG"
    PNG = "PNG"


class FTVApps(Enum):
    """FTV - Frame TV supported apps"""
    Spotify = '3201606009684'


class FTVImageMatte(Enum):
    """FTV - Frame TV supported image matte"""
    MODERN_APRICOT = 'modern_apricot'


class FTVImageFilters(Enum):
    """FTV - Frame TV supported image filters"""
    INK = 'ink'


FTV_UPLOADED_IMAGE_FILES_SCHEMA = {
    "type": "object",
    "additionalProperties": {
        "type": "array",
        "items": { "type": "string" }
    }
}


# -----------------------------------------------------------------------------
# FTV
# -----------------------------------------------------------------------------
class FTV(object):
    """FTV - Frame TV class"""

    @abk_common.function_trace
    def __init__(self, logger: logging.Logger, ftv_data_file: str) -> None:
        self._logger = logger or logging.getLogger(__name__)
        # logging.basicConfig(level=logging.DEBUG)
        self._ftv_data_file = ftv_data_file
        self._ftv_settings: dict[str, FTVSetting] | None = None


    @property
    def ftvs(self) -> dict[str, FTVSetting]:
        """ftvs getter
        Returns:
            dict[str, FTVs]: dictionary of Frame TV settings
        """
        if self._ftv_settings is None:
            self._ftv_settings = self._load_ftv_settings()
        return self._ftv_settings


    @staticmethod
    @abk_common.function_trace
    def _get_environment_variable_value(env_variable: str) -> str:
        """Get environment variable value from shell
        Args:
            env_variable (str): name of the environment variable to load
        Returns:
            str: the value of the variable
        """
        return os.environ[env_variable] if env_variable in os.environ else ""


    @staticmethod
    @abk_common.function_trace
    def _get_api_token_file(tv_name: str) -> str:
        """Get API token file based on the name of Frame TV
        Args:
            tv_name (str): TV name
        Returns:
            str: api token file name
        """
        return f'{os.path.dirname(os.path.realpath(__file__))}/{tv_name}{FTV_API_TOKEN_FILE_SUFFIX}'


    @abk_common.function_trace
    def _load_ftv_settings(self) -> dict[str, FTVSetting]:
        """Load Frame TV settings from file"""
        ftv_settings = {}
        try:
            ftv_config_name = pathlib.Path(__file__).parent / 'config' / self._ftv_data_file
            with ftv_config_name.open(mode='rb') as file_handler:
                ftv_config = tomllib.load(file_handler)
            ftv_data = ftv_config.get("ftv_data", {})
            for ftv_name, ftv_data_dict in ftv_data.items():
                img_rate = ftv_data_dict[FTV_DATA_KW.IMG_RATE.value]
                self._logger.debug(f"{ftv_name = }, {img_rate = }")
                ip_addr = ftv_data_dict[FTV_DATA_KW.IP_ADDR.value]
                self._logger.debug(f"{ftv_name = }, {ip_addr = }")
                mac_addr = ftv_data_dict[FTV_DATA_KW.MAC_ADDR.value]
                self._logger.debug(f"{ftv_name = }, {mac_addr = }")
                port = ftv_data_dict[FTV_DATA_KW.PORT.value]
                self._logger.debug(f"{ftv_name = }, {port = }")

                api_token_file_name = FTV._get_api_token_file(ftv_name)
                self._logger.debug(f"{ftv_name = }, {api_token_file_name = }")
                # ftv = SamsungTVWS(ip_addr)
                ftv = SamsungTVWS(host=ip_addr, port=port, token=api_token_file_name)
                ftv_settings[ftv_name] = FTVSetting(ftv=ftv, img_rate=img_rate, mac_addr=mac_addr)
        except Exception as exc:
            self._logger.error(f"Error loading Frame TV settings {exc} from file: {self._ftv_data_file}")
            raise exc
        return ftv_settings


    @abk_common.function_trace
    def _wake_up_tv(self, tv_name: str) -> None:
        """Wake up TV
        Args:
            tv_name (str): TV name
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            wakeonlan.send_magic_packet(ftv_setting.mac_addr)


    @abk_common.function_trace
    def _toggle_power(self, tv_name: str) -> None:
        """Toggle power on Frame TV
        Args:
            tv_name (str): TV name
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.shortcuts().power()


    @abk_common.function_trace
    def _browse_to_url(self, tv_name: str, url: str) -> None:
        """Browse to URL on Frame TV
        Args:
            tv_name (str): TV name
            url (str): URL to browse to
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.open_browser(url)


    @abk_common.function_trace
    def _list_installed_apps(self, tv_name: str) -> (list | None):
        """List installed apps on Frame TV
        Args:
            tv_name (str): TV name
        """
        app_list = None
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            app_list = ftv_setting.ftv.app_list()
        self._logger.info(f'[{tv_name}]: {app_list = }')
        return app_list


    @abk_common.function_trace
    def _open_app(self, tv_name: str, app_name: FTVApps) -> None:
        """Opens app on Frame TV
        Args:
            tv_name (str): TV name
            app_name (FTVApps): name of the app to open, should be supported
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.run_app(app_name.value)


    @abk_common.function_trace
    def _get_app_status(self, tv_name: str, app_name: FTVApps) -> dict:
        """Gets app status on Frame TV
        Args:
            tv_name (str): TV name
            app_name (FTVApps): name of the app to get status for
        Return (dict): dictionary of app_status
        """
        app_status = {}
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            app_status = ftv_setting.ftv.rest_app_status(app_name.value)
        self._logger.info(f'[{tv_name}]: {app_status = }')
        return app_status


    @abk_common.function_trace
    def _close_app(self, tv_name: str, app_name: FTVApps) -> None:
        """Closes app on Frame TV
        Args:
            tv_name (str): TV name
            app_name (FTVApps): name of the app to close, should be supported
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.rest_app_close(app_name.value)


    @abk_common.function_trace
    def _install_app(self, tv_name: str, app_name: FTVApps) -> None:
        """Closes app on Frame TV
        Args:
            tv_name (str): TV name
            app_name (FTVApps): name of the app to install, should be supported
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.rest_app_install(app_name.value)


    @abk_common.function_trace
    def _get_device_info(self, tv_name: str) -> dict:
        """Gets device info for Frame TV
        Args:
            tv_name (str): TV name
        """
        device_info = {}
        ftv_setting = self.ftvs.get(tv_name, None)
        self._logger.info(f'[{tv_name}]: {ftv_setting = }')
        if ftv_setting:
            device_info = ftv_setting.ftv.rest_device_info()
        self._logger.info(f'[{tv_name}]: {device_info = }')
        return device_info


    @abk_common.function_trace
    def _is_art_mode_supported(self, tv_name: str) -> bool:
        """ Returns True if TV supports art mode
        Args:
            tv_name (str): TV name
        Returns:
            bool: True if TV supports art mode, false otherwise
        """
        art_supported = False
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            art_supported = ftv_setting.ftv.art().supported()
        self._logger.info(f'[{tv_name}]: {art_supported = }')
        return art_supported


    @abk_common.function_trace
    def _get_current_art(self, tv_name: str) -> str:
        """ Returns the current art
        Args:
            tv_name (str): TV name
        Returns:
            str: the current art
        """
        current_art = ""
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            current_art = ftv_setting.ftv.art().get_current()
        self._logger.info(f'[{tv_name}]: {current_art = }')
        return current_art



    @abk_common.function_trace
    def _list_art_on_tv(self, tv_name: str) -> list:
        """Lists art available on FrameTV
        Args:
            tv_name (str): TV name
        Returns:
            list: list of available art
        """
        art_list = []
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            art_list = ftv_setting.ftv.art().available()
        self._logger.info(f'[{tv_name}]: {art_list = }')
        return art_list


    @abk_common.function_trace
    def _get_current_art_image(self, tv_name: str) -> (bytearray | None):
        """Gets current image thumbnail
        Args:
            tv_name (str): TV name
        Returns:
            bytearray | None: Image thumbnail or None if not available
        """
        thumbnail = None
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            current_art = ftv_setting.ftv.art().get_current()
            thumbnail = ftv_setting.ftv.art().get_thumbnail(current_art)
        # self._logger.info(f'[{tv_name}]: {thumbnail = }')
        return thumbnail


    @abk_common.function_trace
    def _set_current_art_image(self, tv_name: str, file_name: str, show_now: bool = False) -> None:
        """Sets current art image
        Args:
            tv_name (str): TV name
            file_name (str): name of the image file to set
            show_now (bool): if True show immediately, otherwise delayed
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.art().select_image(file_name, show=show_now)


    @abk_common.function_trace
    def _is_tv_in_art_mode(self, tv_name: str) -> bool:
        """Determine whether the TV is currently in art mode
        Args:
            tv_name (str): TV name
        """
        is_art_mode = False
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            is_art_mode = ftv_setting.ftv.art().get_artmode()
        self._logger.debug(f'[{tv_name}]: {is_art_mode = }')
        return is_art_mode


    @abk_common.function_trace
    def _activate_art_mode(self, tv_name: str, art_mode_on: bool = False) -> None:
        """Switch art mode on or off
        Args:
            tv_name (str): TV name
            art_mode_on (bool): True to activate, False to deactivate. Default is False.
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.art().set_artmode(art_mode_on)


    @abk_common.function_trace
    def _get_file_type(self, file_name:str) -> (FTVSupportedFileType | None):
        """Determine the file type
        Args:
            file_name (str): file name
        Return:
            FTVSupportedFileType | None: file type or None if not supported
        """
        file_type = None
        if file_name.endswith('.jpg') or file_name.endswith('.jpeg'):
            file_type = FTVSupportedFileType.JPEG
        elif file_name.endswith('.png'):
            file_type = FTVSupportedFileType.PNG
        self._logger.debug(f'[{file_name}]: {file_type = }')
        return file_type


    @abk_common.function_trace
    def _upload_image_list_to_tv(self, tv_name: str, files_to_upload: list) -> list:
        """Uploads images to Frame TV and updates updated list name
        Args:
            tv_name (str): TV name
            files_to_upload (list): image file list to upload
        Return: list of image files uploaded
        """
        uploaded_file_list: list = []
        self._logger.info(f'[{tv_name}]: {files_to_upload = }')
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            self._logger.info(f'[{tv_name}]: {uploaded_file_list = }')
            files_to_upload_to_target = [os.path.basename(path_file) for path_file in files_to_upload]
            uploaded_images_on_target = self._get_uploaded_image_files(tv_name)
            files_remaining_to_upload = list(set(files_to_upload_to_target) - set(uploaded_images_on_target))
            self._logger.info(f'[{tv_name}]: {files_to_upload_to_target = }')
            self._logger.info(f'[{tv_name}]: {uploaded_images_on_target = }')
            self._logger.info(f'[{tv_name}]: {files_remaining_to_upload = }')
            # update files with path to upload list
            files_to_upload = [file for file in files_to_upload if os.path.basename(file) in files_remaining_to_upload]

            for file_to_upload in files_remaining_to_upload:
                matching_file_paths = (fp for fp in files_to_upload if os.path.basename(fp) == file_to_upload)
                matching_file_path = next(matching_file_paths, None)
                if matching_file_path:
                    file_type = self._get_file_type(file_to_upload)
                    if file_type:
                        try:
                            with open(matching_file_path, 'rb') as fh:
                                data = fh.read()
                            ftv_setting.ftv.art().upload(data, file_type=file_type.value, matte='none')
                            uploaded_file_list.append(file_to_upload)
                        except Exception as exp:
                            self._logger.error(f'[{tv_name}]: {exp = }')
            uploaded_images_on_target = list(set(uploaded_images_on_target + uploaded_file_list))
            self._logger.info(f'[{tv_name}]: {uploaded_images_on_target = }')
            self._record_uploaded_image_files(tv_name, uploaded_images_on_target)
        return uploaded_file_list


    @abk_common.function_trace
    def _delete_image_from_tv(self, tv_name: str, file_name:str) -> None:
        """Deletes uploaded file from Frame TV
        Args:
            tv_name (str): TV name
            file_name (str): name of the image file to delete from TV
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.art().delete(file_name)


    @abk_common.function_trace
    def _delete_uploaded_images_from_tv(self, tv_name: str) -> list:
        """Delete multiple uploaded files from Frame TV
        Args:
            tv_name (str): TV name
        Return: list of deleted images
        """
        deleted_images = []
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            uploaded_images = self._get_uploaded_image_files(tv_name)
            self._logger.debug(f'[{tv_name}]: {uploaded_images = }')
            if len(uploaded_images) > 0:
                for image_to_delete in uploaded_images:
                    try:
                        ftv_setting.ftv.art().delete(image_to_delete)
                        # ftv_setting.ftv.art().delete_list(image_list) # not working
                        deleted_images.append(image_to_delete)
                    except Exception as exp:
                        self._logger.error(f'[{tv_name}]: image NOT deleted: {image_to_delete} {exp = }')
                remaining_images = list(set(uploaded_images) - set(deleted_images))
                self._logger.debug(f'[{tv_name}]: {deleted_images = }')
                self._logger.debug(f'[{tv_name}]: {remaining_images = }')
                self._record_uploaded_image_files(tv_name, remaining_images)
        return deleted_images


    @abk_common.function_trace
    def _list_available_filters(self, tv_name: str) -> list:
        """List available photo filters on Frame TV
        Args:
            tv_name (str): TV name
        Return: list of available filters
        """
        available_filter_list = []
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            available_filter_list = ftv_setting.ftv.art().get_photo_filter_list()
        self._logger.debug(f'[{tv_name}]: {available_filter_list = }')
        return available_filter_list


    @abk_common.function_trace
    def _apply_filter_to_art(self, tv_name: str, file_name:str, filter_name: FTVImageFilters) -> None:
        """Apply a filter to a specific piece of art on Frame TV
        Args:
            tv_name (str): TV name
            file_name (str): name of the image file to apply filter to
            filter_name (FTVImageFilters): filter to apply to the image file. See FTVImageFilters for available filters.
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.art().set_photo_filter(file_name, filter_name.value)


    @abk_common.function_trace
    def _connect_to_tv(self, tv_name: str) -> bool:
        """Connects to Frame TV
        Args:
            tv_name (str): TV name
        Returns:
            bool: True if the connection was successful, False otherwise
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            try:
                self._wake_up_tv(tv_name)
                tv_info = self._get_device_info(tv_name)
                self._logger.info(f'[{tv_name}]: {tv_info = }')
                ftv_setting.reachable = True
            except Exception as exc:
                self._logger.error(f'[{tv_name}]: {exc}')
                ftv_setting.reachable = False
        return ftv_setting.reachable if ftv_setting else False


    @abk_common.function_trace
    def _get_uploaded_image_files(self, tv_name: str) -> list:
        """Read uploaded image files from file"""
        uploaded_image_list = []
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            if os.path.isfile(FTV_UPLOADED_IMAGE_FILES):
                with open(FTV_UPLOADED_IMAGE_FILES, 'r') as img_data_file:
                    uploaded_images_json = json.load(img_data_file)
                try:
                    validate(instance=uploaded_images_json, schema=FTV_UPLOADED_IMAGE_FILES_SCHEMA)
                    uploaded_image_list = uploaded_images_json.get(tv_name, [])
                except exceptions.ValidationError as exp:
                    self._logger.error(f"ERROR: {exp=}, validating uploaded image file")
        return uploaded_image_list


    @abk_common.function_trace
    def _record_uploaded_image_files(self, tv_name: str, image_list: list) -> None:
        """Read uploaded image files from file"""
        uploaded_image_files = {}
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            if os.path.isfile(FTV_UPLOADED_IMAGE_FILES):
                with open(FTV_UPLOADED_IMAGE_FILES, 'r') as img_data_file:
                    uploaded_image_files = json.load(img_data_file)
                uploaded_image_files[tv_name] = image_list
                self._logger.debug(f'[{tv_name}]: {uploaded_image_files = }')
                with open(FTV_UPLOADED_IMAGE_FILES, 'w') as img_data_file:
                    json.dump(uploaded_image_files, img_data_file, indent=4)


    @abk_common.function_trace
    def change_daily_images(self, image_list: list) -> bool:
    # def change_daily_images(self, img_file_list: list) -> bool:
        """Changes the daily images on Frame TV
        Args:
            img_file_list (list): list of image files to upload to FrameTV
        Returns:
            bool: True if the daily images were changed, False otherwise
        """
        for tv_name, ftv_setting in self.ftvs.items():
            if self._connect_to_tv(tv_name) and self._is_art_mode_supported(tv_name):
                self._delete_uploaded_images_from_tv(tv_name)
                self._upload_image_list_to_tv(tv_name, image_list)

        return any(ftv_setting.reachable for ftv_setting in self.ftvs.values())


if __name__ == '__main__':
    raise RuntimeError(f"{__file__}: This module should not be executed directly. Only for imports")

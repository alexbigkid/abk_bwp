"""Main function or entry module for the ABK BingWallPaper (abk_bwp) package."""

# Standard lib imports
from dataclasses import dataclass
from enum import Enum
import json
import os
import logging
import time
from typing import NamedTuple, Any
import wakeonlan

import tomllib  # type: ignore

# Third party imports
from jsonschema import validate, exceptions

# Optional Samsung TV import (only needed for HTTP mode, not USB mode)
try:
    from samsungtvws import SamsungTVWS

    SAMSUNGTVWS_AVAILABLE = True
except ImportError:
    SamsungTVWS = None
    SAMSUNGTVWS_AVAILABLE = False
# from samsungtvws.remote import SamsungTVWS
# from samsungtvws.art import SamsungTVArt
# from samsungtvws import SamsungTVArt

# local imports
from abk_bwp import abk_common
from abk_bwp.config import FTV_KW, bwp_config


# -----------------------------------------------------------------------------
# Local Constants
# -----------------------------------------------------------------------------
# FTV_API_TOKEN_FILE_SUFFIX = '_apiToken_secrets.txt'
FTV_UPLOADED_IMAGE_FILES = f"{os.path.dirname(os.path.realpath(__file__))}/ftv_uploaded_image_files.json"


# -----------------------------------------------------------------------------
# Local data definitions
# -----------------------------------------------------------------------------
class FTVData(NamedTuple):
    """FTV - Frame TV properties."""

    api_token: str
    img_rate: int
    ip_addr: str
    mac_addr: str
    port: int


@dataclass
class FTVSetting:
    """FTV - Frame TV setting."""

    ftv: Any  # Type annotation that works with optional imports
    img_rate: int
    mac_addr: str
    reachable: bool = False


class FTV_DATA_KW(Enum):
    """FTV - Frame TV data keywords."""

    API_TOKEN_FILE = "api_token_file"  # noqa: S105
    IP_ADDR = "ip_addr"
    IMG_RATE = "img_rate"
    MAC_ADDR = "mac_addr"
    PORT = "port"


class FTVSupportedFileType(Enum):
    """FTV - Frame TV supported file types."""

    JPEG = "JPEG"
    PNG = "PNG"


class FTVApps(Enum):
    """FTV - Frame TV supported apps."""

    Spotify = "3201606009684"


class FTVImageMatte(Enum):
    """FTV - Frame TV supported image matte."""

    MODERN_APRICOT = "modern_apricot"


class FTVImageFilters(Enum):
    """FTV - Frame TV supported image filters."""

    INK = "ink"


FTV_UPLOADED_IMAGE_FILES_SCHEMA = {"type": "object", "additionalProperties": {"type": "array", "items": {"type": "string"}}}


# -----------------------------------------------------------------------------
# FTV
# -----------------------------------------------------------------------------
class FTV:
    """FTV - Frame TV class."""

    @abk_common.function_trace
    def __init__(self, logger: logging.Logger, ftv_data_file: str) -> None:
        """Init for FTV.

        Args:
            logger: logger to use
            ftv_data_file (str): FTV data file
        """
        self._logger = logger or logging.getLogger(__name__)
        # logging.basicConfig(level=logging.DEBUG)
        self._ftv_data_file = ftv_data_file
        self._ftv_settings: dict[str, FTVSetting] | None = None

    @property
    def ftvs(self) -> dict:
        """FTVs getter.

        Returns:
            dict[str, FTVs]: dictionary of Frame TV settings
        """
        if self._ftv_settings is None:
            self._ftv_settings = self._load_ftv_settings()
        return self._ftv_settings

    @staticmethod
    @abk_common.function_trace
    def _get_environment_variable_value(env_variable: str) -> str:
        """Get environment variable value from shell.

        Args:
            env_variable (str): name of the environment variable to load
        Returns:
            str: the value of the variable
        """
        return os.environ.get(env_variable, "")

    @staticmethod
    @abk_common.function_trace
    def _get_api_token_full_file_name(file_name: str) -> str:
        """Get API token file based on the name of Frame TV.

        Args:
            file_name (str): short file name
        Returns:
            str: api token full file name
        """
        return os.path.join(os.path.dirname(__file__), "config", file_name)

    @staticmethod
    @abk_common.function_trace
    def _get_api_token(api_token_holder: str) -> str:
        """Get API token file based on the name of Frame TV.

        Args:
            api_token_holder (str): an env variable or file, which holds api token
        Returns:
            str: api token
        """
        if api_token_holder == "":
            return ""
        # try to get api_token from environment variable
        api_token_str = os.environ.get(api_token_holder, None)
        if api_token_str is None and os.path.isfile(api_token_holder):
            with open(api_token_holder) as file_handler:
                api_token_str = file_handler.read().strip()
        if api_token_str is None:
            api_token_str = api_token_holder
        return api_token_str

    @abk_common.function_trace
    def _load_ftv_settings(self) -> dict:
        """Load Frame TV settings from file."""
        ftv_settings = {}

        # Check if we're in USB mode - if so, no need for samsungtvws
        from abk_bwp import bingwallpaper

        if bingwallpaper.bwp_config.get("ftv", {}).get("usb_mode", False):
            self._logger.info("USB mode enabled - skipping Samsung TV HTTP setup")
            return ftv_settings

        # Check if samsungtvws is available for HTTP mode
        if not SAMSUNGTVWS_AVAILABLE:
            raise ImportError("samsungtvws library is required for Frame TV HTTP mode. Install with: uv sync --extra frametv")
        try:
            ftv_config_name = os.path.join(os.path.dirname(__file__), "config", self._ftv_data_file)
            with open(ftv_config_name, mode="rb") as file_handler:
                ftv_config = tomllib.load(file_handler)
            ftv_data = ftv_config.get("ftv_data", {})
            for ftv_name, ftv_data_dict in ftv_data.items():
                api_token_file = ftv_data_dict[FTV_DATA_KW.API_TOKEN_FILE.value]
                self._logger.debug(f"{ftv_name = }, {api_token_file = }")
                img_rate = ftv_data_dict[FTV_DATA_KW.IMG_RATE.value]
                self._logger.debug(f"{ftv_name = }, {img_rate = }")
                ip_addr = ftv_data_dict[FTV_DATA_KW.IP_ADDR.value]
                self._logger.debug(f"{ftv_name = }, {ip_addr = }")
                mac_addr = ftv_data_dict[FTV_DATA_KW.MAC_ADDR.value]
                self._logger.debug(f"{ftv_name = }, {mac_addr = }")
                port = ftv_data_dict[FTV_DATA_KW.PORT.value]
                self._logger.debug(f"{ftv_name = }, {port = }")

                api_token_full_file_name = FTV._get_api_token_full_file_name(api_token_file)
                self._logger.debug(f"{ftv_name = }, {api_token_full_file_name = }")
                api_token = FTV._get_api_token(api_token_full_file_name)
                self._logger.debug(f"{ftv_name = }, {api_token = }")

                # Create SamsungTVWS instance with proper authentication
                # At this point we know SamsungTVWS is available due to check above
                if api_token and os.path.isfile(api_token_full_file_name):
                    # Use token file if available
                    ftv = SamsungTVWS(  # type: ignore
                        host=ip_addr, port=port, token_file=api_token_full_file_name, timeout=10, name=ftv_name
                    )
                elif api_token:
                    # Use token string directly
                    ftv = SamsungTVWS(  # type: ignore
                        host=ip_addr, port=port, token=api_token, timeout=10, name=ftv_name
                    )
                else:
                    # No authentication - may require manual pairing
                    ftv = SamsungTVWS(host=ip_addr, port=port, timeout=10, name=ftv_name)  # type: ignore

                ftv_settings[ftv_name] = FTVSetting(ftv=ftv, img_rate=img_rate, mac_addr=mac_addr)
        except Exception as exc:
            self._logger.error(f"Error loading Frame TV settings {exc} from file: {self._ftv_data_file}")
            raise exc
        return ftv_settings

    @abk_common.function_trace
    def _wake_up_tv(self, tv_name: str) -> None:
        """Wake up TV.

        Args:
            tv_name (str): TV name
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            wakeonlan.send_magic_packet(ftv_setting.mac_addr)

    @abk_common.function_trace
    def _toggle_power(self, tv_name: str) -> None:
        """Toggle power on Frame TV.

        Args:
            tv_name (str): TV name
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.shortcuts().power()

    @abk_common.function_trace
    def _browse_to_url(self, tv_name: str, url: str) -> None:
        """Browse to URL on Frame TV.

        Args:
            tv_name (str): TV name
            url (str): URL to browse to
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.open_browser(url)

    @abk_common.function_trace
    def _list_installed_apps(self, tv_name: str) -> list:
        """List installed apps on Frame TV.

        Args:
            tv_name (str): TV name
        """
        app_list = []
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            app_list = ftv_setting.ftv.app_list()
        self._logger.info(f"[{tv_name}]: {app_list = }")
        return app_list

    @abk_common.function_trace
    def _open_app(self, tv_name: str, app_name: FTVApps) -> None:
        """Opens app on Frame TV.

        Args:
            tv_name (str): TV name
            app_name (FTVApps): name of the app to open, should be supported
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.run_app(app_name.value)

    @abk_common.function_trace
    def _get_app_status(self, tv_name: str, app_name: FTVApps) -> dict:
        """Gets app status on Frame TV.

        Args:
            tv_name (str): TV name
            app_name (FTVApps): name of the app to get status for
        Return (dict): dictionary of app_status
        """
        app_status = {}
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            app_status = ftv_setting.ftv.rest_app_status(app_name.value)
        self._logger.info(f"[{tv_name}]: {app_status = }")
        return app_status

    @abk_common.function_trace
    def _close_app(self, tv_name: str, app_name: FTVApps) -> None:
        """Closes app on Frame TV.

        Args:
            tv_name (str): TV name
            app_name (FTVApps): name of the app to close, should be supported
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.rest_app_close(app_name.value)

    @abk_common.function_trace
    def _install_app(self, tv_name: str, app_name: FTVApps) -> None:
        """Closes app on Frame TV.

        Args:
            tv_name (str): TV name
            app_name (FTVApps): name of the app to install, should be supported
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.rest_app_install(app_name.value)

    @abk_common.function_trace
    def _get_device_info(self, tv_name: str) -> dict:
        """Gets device info for Frame TV.

        Args:
            tv_name (str): TV name
        """
        device_info = {}
        ftv_setting = self.ftvs.get(tv_name, None)
        self._logger.info(f"[{tv_name}]: {ftv_setting = }")
        if ftv_setting:
            device_info = ftv_setting.ftv.rest_device_info()
        self._logger.info(f"[{tv_name}]: {device_info = }")
        return device_info

    @abk_common.function_trace
    def _is_art_mode_supported(self, tv_name: str) -> bool:
        """Returns True if TV supports art mode.

        Args:
            tv_name (str): TV name
        Returns:
            bool: True if TV supports art mode, false otherwise
        """
        art_supported = False
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            art_supported = ftv_setting.ftv.art().supported()
        self._logger.info(f"[{tv_name}]: {art_supported = }")
        return art_supported

    @abk_common.function_trace
    def _get_current_art(self, tv_name: str) -> str:
        """Returns the current art.

        Args:
            tv_name (str): TV name
        Returns:
            str: the current art
        """
        current_art = ""
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            current_art = ftv_setting.ftv.art().get_current()
        self._logger.info(f"[{tv_name}]: {current_art = }")
        return current_art

    @abk_common.function_trace
    def _list_art_on_tv(self, tv_name: str) -> list:
        """Lists art available on FrameTV.

        Args:
            tv_name (str): TV name
        Returns:
            list: list of available art
        """
        art_list = []
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            art_list = ftv_setting.ftv.art().available()
        self._logger.info(f"[{tv_name}]: {art_list = }")
        return art_list

    @abk_common.function_trace
    def _get_current_art_image(self, tv_name: str) -> bytearray:
        """Gets current image thumbnail.

        Args:
            tv_name (str): TV name
        Returns:
            bytearray: Image thumbnail or empty bytearray if not available
        """
        thumbnail = bytearray()
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            current_art = ftv_setting.ftv.art().get_current()
            thumbnail = ftv_setting.ftv.art().get_thumbnail(current_art)
        # self._logger.info(f'[{tv_name}]: {thumbnail = }')
        return thumbnail

    @abk_common.function_trace
    def _set_current_art_image(self, tv_name: str, file_name: str, show_now: bool = False) -> None:
        """Sets current art image.

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
        """Determine whether the TV is currently in art mode.

        Args:
            tv_name (str): TV name
        """
        is_art_mode = False
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            is_art_mode = ftv_setting.ftv.art().get_artmode()
        self._logger.debug(f"[{tv_name}]: {is_art_mode = }")
        return is_art_mode

    @abk_common.function_trace
    def _activate_art_mode(self, tv_name: str, art_mode_on: bool = False) -> None:
        """Switch art mode on or off.

        Args:
            tv_name (str): TV name
            art_mode_on (bool): True to activate, False to deactivate. Default is False.
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.art().set_artmode(art_mode_on)

    @abk_common.function_trace
    def _get_file_type(self, file_name: str):
        """Determine the file type.

        Args:
            file_name (str): file name
        Return:
            FTVSupportedFileType | None: file type or None if not supported
        """
        file_type = None
        if file_name.endswith(".jpg") or file_name.endswith(".jpeg"):
            file_type = FTVSupportedFileType.JPEG
        elif file_name.endswith(".png"):
            file_type = FTVSupportedFileType.PNG
        self._logger.debug(f"[{file_name}]: {file_type = }")
        return file_type

    @abk_common.function_trace
    def _upload_image_list_to_tv(self, tv_name: str, files_to_upload: list) -> list:
        """Uploads images to Frame TV and updates updated list name.

        Args:
            tv_name (str): TV name
            files_to_upload (list): image file list to upload
        Return: list of image files uploaded
        """
        uploaded_file_list: list = []
        self._logger.info(f"[{tv_name}]: {files_to_upload = }")
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            try:
                api_version = ftv_setting.ftv.art().get_api_version()
                self._logger.info(f"[{tv_name}]: {api_version = }")
            except Exception as e:
                self._logger.warning(f"[{tv_name}]: Could not get API version: {e}")
                api_version = "unknown"
            self._logger.info(f"[{tv_name}]: {uploaded_file_list = }")
            files_to_upload_to_target = [os.path.basename(path_file) for path_file in files_to_upload]
            uploaded_images_on_target = self._get_uploaded_image_files(tv_name)
            files_remaining_to_upload = list(set(files_to_upload_to_target) - set(uploaded_images_on_target))
            self._logger.info(f"[{tv_name}]: {files_to_upload_to_target = }")
            self._logger.info(f"[{tv_name}]: {uploaded_images_on_target = }")
            self._logger.info(f"[{tv_name}]: {files_remaining_to_upload = }")
            # update files with path to upload list
            files_to_upload = [file for file in files_to_upload if os.path.basename(file) in files_remaining_to_upload]

            # Process files one at a time with delays to avoid overwhelming the TV
            for i, file_to_upload in enumerate(files_remaining_to_upload):
                if i > 0:
                    # Add delay between uploads to prevent overwhelming the TV
                    time.sleep(1)
                matching_file_paths = (fp for fp in files_to_upload if os.path.basename(fp) == file_to_upload)
                matching_file_path = next(matching_file_paths, None)
                if matching_file_path:
                    file_type = self._get_file_type(file_to_upload)
                    if file_type:
                        self._logger.info(f"[{tv_name}]: Uploading {file_to_upload}...")

                        # Retry upload up to 3 times with increasing delays
                        upload_success = False
                        for attempt in range(3):
                            try:
                                if attempt > 0:
                                    self._logger.info(f"[{tv_name}]: Retry attempt {attempt + 1} for {file_to_upload}")
                                    # Wait before retry
                                    time.sleep(2 * attempt)

                                with open(matching_file_path, "rb") as fh:
                                    data = fh.read()

                                ftv_setting.ftv.art().upload(data, file_type=file_type.value, matte="none")
                                uploaded_file_list.append(file_to_upload)
                                upload_success = True
                                self._logger.info(f"[{tv_name}]: Successfully uploaded {file_to_upload}")
                                break

                            except (BrokenPipeError, ConnectionError) as exp:
                                if attempt < 2:  # Don't log as error on last attempt
                                    self._logger.warning(f"[{tv_name}]: Upload failed for {file_to_upload}, will retry: {exp}")
                                else:
                                    self._logger.error(
                                        f"[{tv_name}]: Upload failed after all retries for {file_to_upload}: {exp}"
                                    )
                            except Exception as exp:
                                self._logger.error(f"[{tv_name}]: Unexpected error uploading {file_to_upload}: {exp}")
                                break

                        if not upload_success:
                            self._logger.error(f"[{tv_name}]: Failed to upload {file_to_upload} after all attempts")
            uploaded_images_on_target = list(set(uploaded_images_on_target + uploaded_file_list))
            self._logger.info(f"[{tv_name}]: {uploaded_images_on_target = }")
            self._record_uploaded_image_files(tv_name, uploaded_images_on_target)
        return uploaded_file_list

    @abk_common.function_trace
    def _delete_image_from_tv(self, tv_name: str, file_name: str) -> None:
        """Deletes uploaded file from Frame TV.

        Args:
            tv_name (str): TV name
            file_name (str): name of the image file to delete from TV
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.art().delete(file_name)

    @abk_common.function_trace
    def _delete_uploaded_images_from_tv(self, tv_name: str) -> list:
        """Delete multiple uploaded files from Frame TV.

        Args:
            tv_name (str): TV name
        Return: list of deleted images
        """
        deleted_images = []
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            uploaded_images = self._get_uploaded_image_files(tv_name)
            self._logger.debug(f"[{tv_name}]: {uploaded_images = }")
            if len(uploaded_images) > 0:
                for image_to_delete in uploaded_images:
                    try:
                        ftv_setting.ftv.art().delete(image_to_delete)
                        # ftv_setting.ftv.art().delete_list(image_list) # not working
                        deleted_images.append(image_to_delete)
                    except Exception as exp:
                        self._logger.error(f"[{tv_name}]: image NOT deleted: {image_to_delete} {exp = }")
                remaining_images = list(set(uploaded_images) - set(deleted_images))
                self._logger.debug(f"[{tv_name}]: {deleted_images = }")
                self._logger.debug(f"[{tv_name}]: {remaining_images = }")
                self._record_uploaded_image_files(tv_name, remaining_images)
        return deleted_images

    @abk_common.function_trace
    def _remount_usb_storage_for_tv(self) -> bool:
        """Remount USB storage to trigger Frame TV detection on Raspberry Pi.

        This method simulates USB device removal and insertion by:
        1. Removing the g_mass_storage kernel module
        2. Re-loading it after a brief pause

        This triggers the Samsung Frame TV to detect new images.

        Returns:
            bool: True if remount successful, False otherwise
        """
        import subprocess  # noqa: S404

        try:
            self._logger.debug("Starting USB mass storage remount sequence...")

            # Use helper script for USB gadget remount
            usb_storage_file = os.path.expanduser("~/ftv_images/ftv_disk.img")
            usb_helper_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "scripts", "usb_helper.sh")
            usb_helper_script = os.path.abspath(usb_helper_script)

            subprocess.run(  # noqa: S603
                ["sudo", usb_helper_script, "remount", usb_storage_file],  # noqa: S607
                check=True,
            )

            self._logger.debug("USB gadget remount completed using helper script")

            return True

        except subprocess.CalledProcessError as e:
            self._logger.error(f"Failed to remount USB storage: {e}")
            return False
        except FileNotFoundError:
            self._logger.error("USB helper script or required commands not found - not running on Linux?")
            return False
        except Exception as e:
            self._logger.error(f"Unexpected error during USB remount: {e}")
            return False

    @abk_common.function_trace
    def _copy_images_to_usb_disk(self, image_list: list) -> bool:
        """Copy images from ftv_images_today directory to USB disk image.

        This method:
        1. Creates a temporary mount point
        2. Mounts the USB disk image as a loop device
        3. Copies images from ftv_images_today to the mounted filesystem
        4. Unmounts the disk image properly

        Args:
            image_list (list): List of image files to copy

        Returns:
            bool: True if copy successful, False otherwise
        """
        import subprocess  # noqa: S404
        import tempfile
        import shutil

        if not image_list:
            self._logger.warning("No images to copy to USB disk")
            return False

        usb_disk_path = os.path.expanduser("~/ftv_images/ftv_disk.img")
        if not os.path.exists(usb_disk_path):
            self._logger.error(f"USB disk image not found: {usb_disk_path}")
            return False

        temp_mount_dir = None
        loop_device = None

        try:
            self._logger.debug(f"Starting copy of {len(image_list)} images to USB disk...")

            # Step 1: Create temporary mount directory
            temp_mount_dir = tempfile.mkdtemp(prefix="ftv_usb_mount_")
            self._logger.debug(f"Created temporary mount directory: {temp_mount_dir}")

            # Step 2 & 3: Mount USB disk using helper script
            usb_helper_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "scripts", "usb_helper.sh")
            usb_helper_script = os.path.abspath(usb_helper_script)

            result = subprocess.run(  # noqa: S603
                ["sudo", usb_helper_script, "mount", usb_disk_path, temp_mount_dir],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
            loop_device = result.stdout.strip()
            self._logger.debug(f"USB disk mounted at: {temp_mount_dir} using loop device: {loop_device}")

            # Step 4: Clear existing files from USB disk
            for existing_file in os.listdir(temp_mount_dir):
                if existing_file.lower().endswith((".jpg", ".jpeg", ".png")):
                    existing_path = os.path.join(temp_mount_dir, existing_file)
                    os.remove(existing_path)
                    self._logger.debug(f"Removed existing file: {existing_file}")

            # Step 5: Copy new images to USB disk
            copied_count = 0
            for image_path in image_list:
                if os.path.exists(image_path):
                    filename = os.path.basename(image_path)
                    dest_path = os.path.join(temp_mount_dir, filename)
                    shutil.copy2(image_path, dest_path)
                    self._logger.debug(f"Copied {filename} to USB disk")
                    copied_count += 1
                else:
                    self._logger.warning(f"Source image not found: {image_path}")

            # Step 6: Sync filesystem to ensure all data is written
            subprocess.run(["sync"], check=True)  # noqa: S607
            self._logger.info(f"Successfully copied {copied_count} images to USB disk")

            return copied_count > 0

        except subprocess.CalledProcessError as e:
            self._logger.error(f"Failed to copy images to USB disk: {e}")
            return False
        except Exception as e:
            self._logger.error(f"Unexpected error copying images to USB disk: {e}")
            return False
        finally:
            # Cleanup: Always unmount and detach loop device
            try:
                if temp_mount_dir:
                    # Use helper script for cleanup
                    usb_helper_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "scripts", "usb_helper.sh")
                    usb_helper_script = os.path.abspath(usb_helper_script)

                    subprocess.run(["sudo", usb_helper_script, "unmount", temp_mount_dir, loop_device or ""], check=False)  # noqa: S603, S607
                    self._logger.debug("USB disk unmounted using helper script")

            except Exception as cleanup_error:
                self._logger.warning(f"Error during cleanup: {cleanup_error}")

    @abk_common.function_trace
    def _list_available_filters(self, tv_name: str) -> list:
        """List available photo filters on Frame TV.

        Args:
            tv_name (str): TV name
        Return: list of available filters
        """
        available_filter_list = []
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            available_filter_list = ftv_setting.ftv.art().get_photo_filter_list()
        self._logger.debug(f"[{tv_name}]: {available_filter_list = }")
        return available_filter_list

    @abk_common.function_trace
    def _apply_filter_to_art(self, tv_name: str, file_name: str, filter_name: FTVImageFilters) -> None:
        """Apply a filter to a specific piece of art on Frame TV.

        Args:
            tv_name (str): TV name
            file_name (str): name of the image file to apply filter to
            filter_name (FTVImageFilters): filter to apply to the image file.
                                          See FTVImageFilters for available filters.
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            ftv_setting.ftv.art().set_photo_filter(file_name, filter_name.value)

    @abk_common.function_trace
    def _connect_to_tv(self, tv_name: str) -> bool:
        """Connects to Frame TV.

        Args:
            tv_name (str): TV name
        Returns:
            bool: True if the connection was successful, False otherwise
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            try:
                self._logger.info(f"[{tv_name}]: Attempting to wake up TV...")
                self._wake_up_tv(tv_name)

                # Give TV time to wake up
                time.sleep(3)

                self._logger.info(f"[{tv_name}]: Getting device info...")
                tv_info = self._get_device_info(tv_name)
                self._logger.info(f"[{tv_name}]: Successfully connected! {tv_info = }")

                # Test art mode support
                if self._is_art_mode_supported(tv_name):
                    self._logger.info(f"[{tv_name}]: Art mode is supported")
                else:
                    self._logger.warning(f"[{tv_name}]: Art mode is not supported")

                ftv_setting.reachable = True
            except Exception as exc:
                self._logger.error(f"[{tv_name}]: Connection failed: {exc}")
                self._logger.error(f"[{tv_name}]: Make sure the TV is on and accessible at the configured IP address")
                ftv_setting.reachable = False
        return ftv_setting.reachable if ftv_setting else False

    @abk_common.function_trace
    def _get_uploaded_image_files(self, tv_name: str) -> list:
        """Read uploaded image files from file."""
        uploaded_image_list = []
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting and os.path.isfile(FTV_UPLOADED_IMAGE_FILES):
            with open(FTV_UPLOADED_IMAGE_FILES, encoding="utf-8") as img_data_file:
                uploaded_images_json = json.load(img_data_file)
            try:
                validate(instance=uploaded_images_json, schema=FTV_UPLOADED_IMAGE_FILES_SCHEMA)
                uploaded_image_list = uploaded_images_json.get(tv_name, [])
            except exceptions.ValidationError as exp:
                self._logger.error(f"ERROR: {exp=}, validating uploaded image file")
        return uploaded_image_list

    @abk_common.function_trace
    def _record_uploaded_image_files(self, tv_name: str, image_list: list) -> None:
        """Read uploaded image files from file."""
        uploaded_image_files = {}
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting and os.path.isfile(FTV_UPLOADED_IMAGE_FILES):
            with open(FTV_UPLOADED_IMAGE_FILES, encoding="utf-8") as img_data_file:
                uploaded_image_files = json.load(img_data_file)
            uploaded_image_files[tv_name] = image_list
            self._logger.debug(f"[{tv_name}]: {uploaded_image_files = }")
            with open(FTV_UPLOADED_IMAGE_FILES, "w", encoding="utf-8") as img_data_file:
                json.dump(uploaded_image_files, img_data_file, indent=4)

    @abk_common.function_trace
    def change_daily_images(self, image_list: list) -> bool:
        """Changes the daily images on Frame TV.

        Args:
            image_list (list): list of image files to upload to FrameTV
        Returns:
            bool: True if the daily images were changed, False otherwise
        """
        # Check USB mode setting
        usb_mode = bwp_config.get(FTV_KW.FTV.value, {}).get(FTV_KW.USB_MODE.value, False)

        if usb_mode:
            self._logger.info("FTV USB mode enabled - images are already prepared in ftv_images_today directory")

            # Check if running on Linux (Raspberry Pi)
            import platform

            if platform.system().lower() == "linux":
                self._logger.info("Linux detected - copying images to USB disk and triggering remount")

                # Step 1: Copy images to USB disk image
                if self._copy_images_to_usb_disk(image_list):
                    self._logger.info("Images successfully copied to USB disk")

                    # Step 2: Trigger USB remount for Frame TV detection
                    if self._remount_usb_storage_for_tv():
                        self._logger.info("USB remount successful - Frame TV should detect new images")
                        return True
                    else:
                        self._logger.warning("USB remount failed - Frame TV may not detect new images")
                        return False
                else:
                    self._logger.error("Failed to copy images to USB disk")
                    return False
            else:
                self._logger.info("Images will be available to Frame TV via USB mass storage")
                # On non-Linux systems, just indicate images are ready
                self._logger.info(f"Processed {len(image_list)} images for USB mass storage")
                return len(image_list) > 0

        # HTTP mode - use existing upload logic
        success_count = 0
        self._logger.info(f"Starting FTV HTTP upload for {len(self.ftvs)} TV(s)...")
        self._logger.info(f"Images to process: {image_list}")

        for tv_name in self.ftvs:
            self._logger.info(f"[{tv_name}]: Processing Frame TV...")

            if not self._connect_to_tv(tv_name):
                self._logger.error(f"[{tv_name}]: Failed to connect to TV, skipping...")
                continue

            if not self._is_art_mode_supported(tv_name):
                self._logger.error(f"[{tv_name}]: Art mode not supported, skipping...")
                continue

            try:
                self._logger.info(f"[{tv_name}]: Deleting old uploaded images...")
                deleted_images = self._delete_uploaded_images_from_tv(tv_name)
                self._logger.info(f"[{tv_name}]: Deleted {len(deleted_images)} old images")

                self._logger.info(f"[{tv_name}]: Uploading new images...")
                uploaded_images = self._upload_image_list_to_tv(tv_name, image_list)
                self._logger.info(f"[{tv_name}]: Successfully uploaded {len(uploaded_images)} new images")

                if uploaded_images:
                    success_count += 1
                    self._logger.info(f"[{tv_name}]: Daily image update completed successfully!")
                else:
                    self._logger.warning(f"[{tv_name}]: No new images were uploaded")

            except Exception as exc:
                self._logger.error(f"[{tv_name}]: Error during image update: {exc}")

        self._logger.info(f"FTV HTTP upload completed. Success: {success_count}/{len(self.ftvs)} TVs")
        return success_count > 0


if __name__ == "__main__":
    raise RuntimeError(f"{__file__}: This module should not be executed directly. Only for imports")

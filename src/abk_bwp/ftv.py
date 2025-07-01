"""Main function or entry module for the ABK BingWallPaper (abk_bwp) package."""

# Standard lib imports
from dataclasses import dataclass
from enum import Enum
import json
import os
import logging
import signal
import time
from typing import NamedTuple
import wakeonlan

import tomllib  # type: ignore

# Third party imports
from jsonschema import validate, exceptions
from samsungtvws import SamsungTVWS
import base64
import socket
import ssl
import uuid
import websocket
import urllib3
import tempfile
import warnings
# from samsungtvws.remote import SamsungTVWS
# from samsungtvws.art import SamsungTVArt
# from samsungtvws import SamsungTVArt

# local imports
from abk_bwp import abk_common


# -----------------------------------------------------------------------------
# Local Constants
# -----------------------------------------------------------------------------
# FTV_API_TOKEN_FILE_SUFFIX = '_apiToken_secrets.txt'
FTV_UPLOADED_IMAGE_FILES = (
    f"{os.path.dirname(os.path.realpath(__file__))}/ftv_uploaded_image_files.json"
)


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

    ftv: SamsungTVWS
    img_rate: int
    mac_addr: str
    reachable: bool = False
    art_token_path: str | None = None
    auth_token_path: str | None = None
    using_art_token: bool = False


class FTV_DATA_KW(Enum):
    """FTV - Frame TV data keywords."""

    IMAGE_UPDATES = "image_updates"
    AUTH_TOKEN_FILE = "auth_token_file"  # noqa: S105
    ART_TOKEN_FILE = "art_token_file"  # noqa: S105
    REMOTE_CONTROL_TOKEN_FILE = "remote_control_token_file"  # noqa: S105
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


FTV_UPLOADED_IMAGE_FILES_SCHEMA = {
    "type": "object",
    "additionalProperties": {"type": "array", "items": {"type": "string"}},
}


# -----------------------------------------------------------------------------
# FTV
# -----------------------------------------------------------------------------
class FTV:
    """FTV - Frame TV class."""

    # Samsung TV certificate for proper SSL handling
    SAMSUNG_TV_CERT = """-----BEGIN CERTIFICATE-----
MIIDoTCCAomgAwIBAgIJAMOr6vnvqaw5MA0GCSqGSIb3DQEBCwUAMFcxCzAJBgNV
BAYTAktSMRUwEwYDVQQKEwxTbWFydFZpZXdTREsxMTAvBgNVBAMTKFNtYXJ0Vmll
d1NESyBSb290IENlcml0aWZpY2F0ZSBBdXRob3JpdHkwHhcNMTYwOTIxMDgzNjMx
WhcNMzYwOTIxMDgzNjMxWjA7MQswCQYDVQQGEwJLUjEVMBMGA1UEChMMU21hcnRW
aWV3U0RLMRUwEwYDVQQDEwxTbWFydFZpZXdTREswggEiMA0GCSqGSIb3DQEBAQUA
A4IBDwAwggEKAoIBAQDJAVelyH5kGSIQJpU4bngetcGHDcYA3CDRT6UHcPif2A0y
lwlxESTQ35XyItlit5fy/LgNGmNxDF9K6AdkvOplFZD8YnpDZBwvCvvotabkekDo
gqr2KD/2neIiluPQeskFF1c0kwVNHAmMQ84KBFQA/A1zzCriEdUUsgwpUf5UNMAR
ndvk+pJSFdXpnlgDJTFHtgPAFUZw48qJnQF9gE9HHIoF5+hhSgp+VMSS50IU1qjA
HgVCsUjicncVIB2OkMwaeIaJSjBxAkEaSwq9Y6kTmgEOn0Pfojgel7PLhb4hdYxM
Z/+9BWWf2+FtOllCOo6kZRbFvi8naUJ5YuY23z0tAgMBAAGjgYswgYgwCQYDVR0T
BAIwADAfBgNVHSMEGDAWgBRQyhCp74M+t2GwCiH3g3Aau0AX7DAdBgNVHQ4EFgQU
RHiUlTYEGoYQMsMJ1OI9oYXB1YcwCwYDVR0PBAQDAgXgMB0GA1UdJQQWMBQGCCsG
AQUFBwMBBggrBgEFBQcDAjAPBgNVHREECDAGhwR/AAABMA0GCSqGSIb3DQEBCwUA
A4IBAQBZ0lHrGh924dA8Hk+ziknHKXWvc3qTq2Iqdi6QHffvDBfrU2YVS93XFB0R
A8PHvUubhJmChvJzuDKiuqffqpk+tczLlTpgHybiHYhv3eswU1rncqDjjdebl5Qk
8qzCkEZCXploCE4x9RsjKSVZ9SDU7x/8aOAC1ye9hCEEi8Pna3bQLU5ayov7Pkvg
mmiKSGb+Er73WwtSjF1PclQnntLYCUYuWSktnCOaKKjTAAAonR51qnxxO0Z0XXNw
0T5Sa4lEftdY3EhVUMX8qi+Naw5BK7k61J4XRGwvMGt6M7geQ302RPkwgYUUcQSB
rWJyvRNcD56Vj4hTL6kWu5ub1sON
-----END CERTIFICATE-----"""

    @staticmethod
    def _suppress_samsung_ssl_warnings():
        """Suppress SSL warnings specifically for Samsung TV connections."""
        # Only suppress InsecureRequestWarning for Samsung TV connections
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    @staticmethod
    def _restore_ssl_warnings():
        """Restore SSL warnings after Samsung TV operations."""
        warnings.resetwarnings()

    @staticmethod
    def _create_samsung_ssl_context() -> ssl.SSLContext:
        """Create SSL context that trusts Samsung TV's self-signed certificate.

        Returns:
            ssl.SSLContext: SSL context configured for Samsung TV connections
        """
        # Create a custom SSL context with system certs
        context = ssl.create_default_context()

        # Create a temporary certificate file for Samsung TV
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as cert_file:
            cert_file.write(FTV.SAMSUNG_TV_CERT)
            samsung_cert_path = cert_file.name

        # Load Samsung TV certificate as additional trusted CA
        context.load_verify_locations(samsung_cert_path)

        # Configure for Samsung TV specifics
        context.check_hostname = False  # Samsung TV uses IP, not hostname
        context.verify_mode = ssl.CERT_REQUIRED

        # Clean up temporary certificate file
        os.unlink(samsung_cert_path)

        return context

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
        try:
            ftv_config_name = os.path.join(
                os.path.dirname(__file__), "config", self._ftv_data_file
            )
            with open(ftv_config_name, mode="rb") as file_handler:
                ftv_config = tomllib.load(file_handler)
            ftv_data = ftv_config.get("ftv_data", {})
            for ftv_name, ftv_data_dict in ftv_data.items():
                image_updates = ftv_data_dict[FTV_DATA_KW.IMAGE_UPDATES.value]
                # Use Art Mode token for Frame TV uploads (preferred over auth_token)
                art_token_file = ftv_data_dict.get(FTV_DATA_KW.ART_TOKEN_FILE.value, "")
                auth_token_file = ftv_data_dict.get(FTV_DATA_KW.AUTH_TOKEN_FILE.value, "")

                # Prefer Art Mode token for Frame TV operations
                primary_token_file = art_token_file if art_token_file else auth_token_file
                self._logger.debug(
                    f"{ftv_name = }, art_token={art_token_file}, auth_token={auth_token_file}"
                )
                self._logger.debug(f"{ftv_name = }, using primary_token={primary_token_file}")
                img_rate = ftv_data_dict[FTV_DATA_KW.IMG_RATE.value]
                self._logger.debug(f"{ftv_name = }, {img_rate = }")
                ip_addr = ftv_data_dict[FTV_DATA_KW.IP_ADDR.value]
                self._logger.debug(f"{ftv_name = }, {ip_addr = }")
                mac_addr = ftv_data_dict[FTV_DATA_KW.MAC_ADDR.value]
                self._logger.debug(f"{ftv_name = }, {mac_addr = }")
                port = ftv_data_dict[FTV_DATA_KW.PORT.value]
                self._logger.debug(f"{ftv_name = }, {port = }")

                # Get the full file path for the primary token
                api_token_full_file_name = FTV._get_api_token_full_file_name(primary_token_file)
                self._logger.debug(f"{ftv_name = }, {api_token_full_file_name = }")
                api_token = FTV._get_api_token(api_token_full_file_name)
                self._logger.debug(f"{ftv_name = }, {api_token = }")

                # Store both token file paths for enhanced operations
                art_token_path = (
                    FTV._get_api_token_full_file_name(art_token_file) if art_token_file else None
                )
                auth_token_path = (
                    FTV._get_api_token_full_file_name(auth_token_file)
                    if auth_token_file
                    else None
                )

                # Create SamsungTVWS instance with proper authentication
                # According to API docs, use token_file for persistent authentication
                if os.path.isfile(api_token_full_file_name):
                    # Use token file for persistent authentication (recommended)
                    ftv = SamsungTVWS(
                        host=ip_addr,
                        port=port,
                        token_file=api_token_full_file_name,
                        timeout=30,  # Increased timeout for stability
                        name=ftv_name,
                    )
                else:
                    # First time connection - will generate token file
                    ftv = SamsungTVWS(
                        host=ip_addr,
                        port=port,
                        token_file=api_token_full_file_name,  # Will create token file
                        timeout=30,
                        name=ftv_name,
                    )

                # Create FTV setting with enhanced token support
                ftv_setting = FTVSetting(ftv=ftv, img_rate=img_rate, mac_addr=mac_addr)
                ftv_setting.art_token_path = art_token_path
                ftv_setting.auth_token_path = auth_token_path
                ftv_setting.using_art_token = bool(art_token_file and art_token_path)

                ftv_settings[ftv_name] = ftv_setting
        except Exception as exc:
            self._logger.error(
                f"Error loading Frame TV settings {exc} from file: {self._ftv_data_file}"
            )
            raise exc
        return ftv_settings

    @abk_common.function_trace
    def _wake_up_tv(self, tv_name: str) -> bool:
        """Wake up TV using Wake-on-LAN magic packet.

        Args:
            tv_name (str): TV name

        Returns:
            bool: True if Wake-on-LAN packet was sent successfully
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            try:
                self._logger.debug(
                    f"[{tv_name}]: Sending Wake-on-LAN to MAC: {ftv_setting.mac_addr}"
                )
                wakeonlan.send_magic_packet(ftv_setting.mac_addr)
                self._logger.debug(f"[{tv_name}]: Wake-on-LAN magic packet sent successfully")
                return True
            except Exception as exc:
                self._logger.warning(f"[{tv_name}]: Failed to send Wake-on-LAN packet: {exc}")
                return False
        else:
            self._logger.error(f"[{tv_name}]: No FTV settings found for Wake-on-LAN")
            return False

    @abk_common.function_trace
    def _validate_wake_on_lan(self, tv_name: str) -> bool:
        """Validate Wake-on-LAN configuration and functionality.

        Args:
            tv_name (str): TV name

        Returns:
            bool: True if Wake-on-LAN is properly configured and functional
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if not ftv_setting:
            self._logger.error(f"[{tv_name}]: No FTV settings found")
            return False

        # Validate MAC address format
        mac_addr = ftv_setting.mac_addr
        if not mac_addr or len(mac_addr.replace("-", "").replace(":", "")) != 12:
            self._logger.error(f"[{tv_name}]: Invalid MAC address format: {mac_addr}")
            return False

        # Validate IP address
        ip_addr = ftv_setting.ftv.host
        if not ip_addr:
            self._logger.error(f"[{tv_name}]: No IP address configured")
            return False

        self._logger.info(f"[{tv_name}]: Wake-on-LAN validation:")
        self._logger.info(f"[{tv_name}]:   MAC Address: {mac_addr}")
        self._logger.info(f"[{tv_name}]:   IP Address:  {ip_addr}")
        self._logger.info(f"[{tv_name}]:   Port:        {ftv_setting.ftv.port}")

        # Test sending Wake-on-LAN packet
        try:
            self._logger.info(f"[{tv_name}]: Testing Wake-on-LAN packet transmission...")
            wakeonlan.send_magic_packet(mac_addr)
            self._logger.info(f"[{tv_name}]: ✅ Wake-on-LAN packet sent successfully")
            return True
        except Exception as exc:
            self._logger.error(f"[{tv_name}]: ❌ Wake-on-LAN test failed: {exc}")
            return False

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
            self._suppress_samsung_ssl_warnings()
            try:
                app_status = ftv_setting.ftv.rest_app_status(app_name.value)
            finally:
                self._restore_ssl_warnings()
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
            self._suppress_samsung_ssl_warnings()
            try:
                ftv_setting.ftv.rest_app_close(app_name.value)
            finally:
                self._restore_ssl_warnings()

    @abk_common.function_trace
    def _install_app(self, tv_name: str, app_name: FTVApps) -> None:
        """Closes app on Frame TV.

        Args:
            tv_name (str): TV name
            app_name (FTVApps): name of the app to install, should be supported
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            self._suppress_samsung_ssl_warnings()
            try:
                ftv_setting.ftv.rest_app_install(app_name.value)
            finally:
                self._restore_ssl_warnings()

    @abk_common.function_trace
    def _get_device_info(self, tv_name: str) -> dict:
        """Gets device info for Frame TV.

        Args:
            tv_name (str): TV name
        """
        device_info = {}
        ftv_setting = self.ftvs.get(tv_name, None)
        self._logger.debug(f"[{tv_name}]: {ftv_setting = }")
        if ftv_setting:
            # Suppress SSL warnings for Samsung TV connection
            self._suppress_samsung_ssl_warnings()
            try:
                device_info = ftv_setting.ftv.rest_device_info()
            finally:
                self._restore_ssl_warnings()
        self._logger.info(f"[{tv_name}]: device_info = {device_info}")
        return device_info

    @abk_common.function_trace
    def get_tv_model_info(self, tv_name: str) -> dict:
        """Gets Samsung Frame TV model information in a readable format.

        Args:
            tv_name (str): TV name

        Returns:
            dict: TV model information including model, version, etc.
        """
        device_info = self._get_device_info(tv_name)
        if not device_info:
            self._logger.error(f"[{tv_name}]: Could not retrieve device info")
            return {}

        device_data = device_info.get("device", {})

        # Extract model year from internal model code (e.g., "22_PONTUSM_FTV" -> "2022")
        internal_model = device_data.get("model", "")
        model_year = "Unknown"
        if internal_model.startswith(("22_", "23_", "24_", "25_")):
            year_prefix = internal_model[:2]
            model_year = f"20{year_prefix}"

        # Parse model name for size and series info
        model_name = device_data.get("modelName", "Unknown")
        tv_size = "Unknown"
        if model_name.startswith("QN") and len(model_name) > 4:
            try:
                tv_size = f'{model_name[2:4]}"'
            except (ValueError, IndexError):
                tv_size = "Unknown"

        model_info = {
            "tv_name": device_data.get("name", "Unknown"),
            "model_number": model_name,
            "screen_size": tv_size,
            "model_year": model_year,
            "internal_model": internal_model,
            "operating_system": device_data.get("OS", "Unknown"),
            "firmware_version": device_data.get("firmwareVersion", "Unknown"),
            "resolution": device_data.get("resolution", "Unknown"),
            "frame_tv_support": (
                "✅ Yes" if device_data.get("FrameTVSupport") == "true" else "❌ No"
            ),
            "power_state": device_data.get("PowerState", "Unknown").title(),
            "network_type": device_data.get("networkType", "Unknown").title(),
            "ip_address": device_data.get("ip", "Unknown"),
            "mac_address": device_data.get("wifiMac", "Unknown"),
            "device_type": device_data.get("type", "Unknown"),
            "country_code": device_data.get("countryCode", "Unknown"),
            "language": device_data.get("Language", "Unknown"),
        }

        # Display in a nice readable format
        self._logger.info(f"\n{'=' * 60}")
        self._logger.info(f"📺 SAMSUNG FRAME TV INFORMATION - {tv_name.upper()}")
        self._logger.info(f"{'=' * 60}")

        # Hardware Information
        self._logger.info("🔧 HARDWARE INFORMATION:")
        self._logger.info(f"   Model Number:       {model_info['model_number']}")
        self._logger.info(f"   Screen Size:        {model_info['screen_size']}")
        self._logger.info(f"   Model Year:         {model_info['model_year']}")
        self._logger.info(f"   Internal Model:     {model_info['internal_model']}")
        self._logger.info(f"   Resolution:         {model_info['resolution']}")

        # Software Information
        self._logger.info("\n💾 SOFTWARE INFORMATION:")
        self._logger.info(f"   Operating System:   {model_info['operating_system']}")
        self._logger.info(f"   Firmware Version:   {model_info['firmware_version']}")
        self._logger.info(
            f"   Country/Language:   {model_info['country_code']}/{model_info['language']}"
        )

        # Frame TV Features
        self._logger.info("\n🖼️  FRAME TV FEATURES:")
        self._logger.info(f"   Frame TV Support:   {model_info['frame_tv_support']}")
        self._logger.info(f"   Power State:        {model_info['power_state']}")

        # Network Information
        self._logger.info("\n🌐 NETWORK INFORMATION:")
        self._logger.info(f"   Network Type:       {model_info['network_type']}")
        self._logger.info(f"   IP Address:         {model_info['ip_address']}")
        self._logger.info(f"   MAC Address:        {model_info['mac_address']}")

        self._logger.info(f"{'=' * 60}\n")

        return model_info

    @abk_common.function_trace
    def _display_art_mode_token_status(self, tv_name: str) -> None:
        """Display Art Mode token status for the TV.

        Args:
            tv_name (str): TV name
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if not ftv_setting:
            return

        self._logger.info(f"\n{'=' * 60}")
        self._logger.info(f"🎨 ART MODE TOKEN STATUS - {tv_name.upper()}")
        self._logger.info(f"{'=' * 60}")

        if ftv_setting.using_art_token:
            self._logger.info("✅ ENHANCED MODE ENABLED:")
            self._logger.info("   Art Mode Token:     ✅ Available")
            if ftv_setting.art_token_path:
                token_exists = os.path.isfile(ftv_setting.art_token_path)
                self._logger.info(
                    f"   Token File:         {'✅ Found' if token_exists else '❌ Missing'}"
                )
                self._logger.info(f"   Token Path:         {ftv_setting.art_token_path}")
            self._logger.info("   Upload Protocol:    🚀 Enhanced (WebSocket + TLS)")
            self._logger.info("   Delete Protocol:    🚀 Enhanced (WebSocket API)")
            self._logger.info("   Benefits:           🔥 Faster, More Reliable")
        else:
            self._logger.info("⚠️  LEGACY MODE:")
            self._logger.info("   Art Mode Token:     ❌ Not available")
            self._logger.info("   Upload Protocol:    📡 Legacy (samsungtvws)")
            self._logger.info("   Delete Protocol:    📡 Legacy (samsungtvws)")
            self._logger.info("   Recommendation:     🔧 Run Art Mode authenticator")

        if ftv_setting.auth_token_path:
            auth_exists = os.path.isfile(ftv_setting.auth_token_path)
            self._logger.info(
                f"   Legacy Auth Token:  {'✅ Available' if auth_exists else '❌ Missing'}"
            )

        self._logger.info(f"{'=' * 60}\n")

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
            # Suppress SSL warnings for Samsung TV connection
            self._suppress_samsung_ssl_warnings()
            try:
                art_supported = ftv_setting.ftv.art().supported()
            finally:
                self._restore_ssl_warnings()
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
    def _set_current_art_image(
        self, tv_name: str, file_name: str, show_now: bool = False
    ) -> None:
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
    def _optimize_image_for_upload(self, file_path: str) -> bytes:
        """Optimize image for Samsung Frame TV upload.

        Reduces file size while maintaining quality for Frame TV display.
        Frame TVs have limitations on upload size and network stability.

        Args:
            file_path (str): Path to the image file

        Returns:
            bytes: Optimized image data
        """
        try:
            from PIL import Image
            import io

            # Samsung Frame TV optimal settings
            MAX_FILE_SIZE = 300 * 1024  # 300KB limit for stable uploads
            QUALITY_LEVELS = [85, 75, 65, 55, 45]  # Progressive quality reduction
            MAX_DIMENSION = 1920  # Frame TV native resolution consideration

            with Image.open(file_path) as img:
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")

                # Resize if image is too large
                if max(img.size) > MAX_DIMENSION:
                    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
                    self._logger.debug(f"Resized image to {img.size} for Frame TV compatibility")

                # Find optimal quality that meets size constraints
                for quality in QUALITY_LEVELS:
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=quality, optimize=True)
                    data = buffer.getvalue()

                    if len(data) <= MAX_FILE_SIZE:
                        self._logger.debug(
                            f"Optimized image: {len(data)} bytes at quality {quality}%"
                        )
                        return data

                # If still too large, use minimum quality
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=30, optimize=True)
                data = buffer.getvalue()
                self._logger.warning(f"Using minimum quality for upload: {len(data)} bytes")
                return data

        except Exception as e:
            self._logger.error(f"Error optimizing image {file_path}: {e}")
            # Fallback to original file
            with open(file_path, "rb") as fh:
                return fh.read()

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
            files_to_upload_to_target = [
                os.path.basename(path_file) for path_file in files_to_upload
            ]
            uploaded_images_on_target = self._get_uploaded_image_files(tv_name)
            files_remaining_to_upload = list(
                set(files_to_upload_to_target) - set(uploaded_images_on_target)
            )
            self._logger.info(f"[{tv_name}]: {files_to_upload_to_target = }")
            self._logger.info(f"[{tv_name}]: {uploaded_images_on_target = }")
            self._logger.info(f"[{tv_name}]: {files_remaining_to_upload = }")
            # update files with path to upload list
            files_to_upload = [
                file
                for file in files_to_upload
                if os.path.basename(file) in files_remaining_to_upload
            ]

            # Process files one at a time with delays to avoid overwhelming the TV
            for i, file_to_upload in enumerate(files_remaining_to_upload):
                if i > 0:
                    # Conservative delay between uploads for Samsung TV stability
                    delay = 3  # Increased delay for better stability
                    self._logger.info(f"[{tv_name}]: Waiting {delay}s before next upload...")
                    time.sleep(delay)
                matching_file_paths = (
                    fp for fp in files_to_upload if os.path.basename(fp) == file_to_upload
                )
                matching_file_path = next(matching_file_paths, None)
                if matching_file_path:
                    file_type = self._get_file_type(file_to_upload)
                    if file_type:
                        self._logger.info(f"[{tv_name}]: Uploading {file_to_upload}...")

                        # Enhanced upload with proper Samsung TV API handling
                        upload_success = False
                        max_retries = 3

                        for attempt in range(max_retries):
                            try:
                                if attempt > 0:
                                    self._logger.info(
                                        f"[{tv_name}]: Retry attempt {attempt + 1}/{max_retries} "
                                        f"for {file_to_upload}"
                                    )
                                    # Exponential backoff for retries
                                    time.sleep(3 * (2**attempt))

                                    # Test connection health before retry
                                    try:
                                        self._suppress_samsung_ssl_warnings()
                                        try:
                                            test_info = ftv_setting.ftv.rest_device_info()
                                        finally:
                                            self._restore_ssl_warnings()
                                        if not test_info:
                                            raise ConnectionError("Connection lost")
                                    except Exception:
                                        self._logger.warning(
                                            f"[{tv_name}]: Connection test failed, "
                                            f"attempting reconnection..."
                                        )
                                        if not self._connect_to_tv(tv_name):
                                            raise ConnectionError(
                                                "Could not re-establish connection"
                                            ) from None

                                # Load and optimize image data for Samsung TV upload
                                optimized_data = self._optimize_image_for_upload(
                                    matching_file_path
                                )

                                if len(optimized_data) == 0:
                                    raise ValueError(f"Image file {file_to_upload} is empty")

                                self._logger.info(
                                    f"[{tv_name}]: Uploading {file_to_upload} "
                                    f"({len(optimized_data)} bytes)..."
                                )

                                # Check if file size is within acceptable limits
                                if len(optimized_data) > 500 * 1024:  # 500KB warning threshold
                                    self._logger.warning(
                                        f"[{tv_name}]: Large file size {len(optimized_data)} bytes "
                                        f"may cause upload issues"
                                    )

                                # Upload with proper Samsung TV API parameters
                                file_type_str = (
                                    "jpg" if file_type == FTVSupportedFileType.JPEG else "png"
                                )

                                # Use Samsung TV WebSocket API upload method with timeout handling
                                self._logger.debug(
                                    f"[{tv_name}]: Starting upload to Samsung TV..."
                                )

                                # Set upload timeout to prevent hanging
                                upload_timeout = 30  # 30 seconds timeout
                                result = None

                                def timeout_handler(signum, frame):
                                    raise TimeoutError(
                                        f"Upload timed out after {upload_timeout}s"
                                    )

                                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                                signal.alarm(upload_timeout)

                                try:
                                    result = ftv_setting.ftv.art().upload(
                                        optimized_data,
                                        file_type=file_type_str,
                                        matte="modern_apricot",  # Frame TV matte option
                                    )
                                    self._logger.debug(f"[{tv_name}]: Upload API call completed")
                                finally:
                                    signal.alarm(0)  # Cancel the alarm
                                    signal.signal(
                                        signal.SIGALRM, old_handler
                                    )  # Restore old handler

                                # Verify upload success
                                if result:
                                    uploaded_file_list.append(file_to_upload)
                                    upload_success = True
                                    self._logger.info(
                                        f"[{tv_name}]: Successfully uploaded {file_to_upload}"
                                    )
                                    break
                                else:
                                    raise Exception("Upload returned no result")

                            except (
                                BrokenPipeError,
                                ConnectionError,
                                OSError,
                                TimeoutError,
                            ) as exp:
                                if attempt < max_retries - 1:
                                    self._logger.warning(
                                        f"[{tv_name}]: Network error uploading {file_to_upload}, "
                                        f"will retry: {exp}"
                                    )
                                else:
                                    self._logger.error(
                                        f"[{tv_name}]: Network error after all retries for "
                                        f"{file_to_upload}: {exp}"
                                    )
                            except (ValueError, FileNotFoundError) as exp:
                                self._logger.error(
                                    f"[{tv_name}]: File error with {file_to_upload}: {exp}"
                                )
                                break  # Don't retry file errors
                            except Exception as exp:
                                if attempt < max_retries - 1:
                                    self._logger.warning(
                                        f"[{tv_name}]: Upload error for {file_to_upload}, "
                                        f"will retry: {exp}"
                                    )
                                else:
                                    self._logger.error(
                                        f"[{tv_name}]: Upload failed after all retries for "
                                        f"{file_to_upload}: {exp}"
                                    )

                        if not upload_success:
                            self._logger.error(
                                f"[{tv_name}]: Failed to upload {file_to_upload} "
                                f"after {max_retries} attempts"
                            )
            uploaded_images_on_target = list(set(uploaded_images_on_target + uploaded_file_list))
            self._logger.info(f"[{tv_name}]: {uploaded_images_on_target = }")
            self._record_uploaded_image_files(tv_name, uploaded_images_on_target)
        return uploaded_file_list

    @abk_common.function_trace
    def _upload_image_with_enhanced_protocol(self, tv_name: str, image_path: str) -> str | None:
        """Upload single image using enhanced Art Mode protocol with Art Mode token.

        Args:
            tv_name (str): TV name
            image_path (str): path to image file

        Returns:
            str | None: Upload ID if successful, None if failed
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if not ftv_setting:
            self._logger.error(f"[{tv_name}]: No Frame TV settings found")
            return None

        if not ftv_setting.using_art_token:
            self._logger.warning(
                f"[{tv_name}]: Art Mode token not available, falling back to legacy upload"
            )
            return None

        # Get Art Mode token
        art_token = None
        if ftv_setting.art_token_path and os.path.isfile(ftv_setting.art_token_path):
            try:
                with open(ftv_setting.art_token_path) as f:
                    art_token = f.read().strip()
            except Exception as e:
                self._logger.error(f"[{tv_name}]: Failed to read Art Mode token: {e}")
                return None

        if not art_token:
            self._logger.error(f"[{tv_name}]: Art Mode token not found")
            return None

        try:
            # Enhanced Art Mode WebSocket connection with token
            name = "BWP_Enhanced"
            b64_name = base64.b64encode(name.encode()).decode()
            art_url = f"wss://{ftv_setting.ftv.host}:{ftv_setting.ftv.port}/api/v2/channels/com.samsung.art-app?name={b64_name}&token={art_token}"

            # Create WebSocket connection with proper Samsung TV SSL context
            samsung_ssl_context = FTV._create_samsung_ssl_context()
            ws = websocket.WebSocket(sslopt={"context": samsung_ssl_context})
            ws.settimeout(10)  # Increased timeout for proper SSL handshake

            self._logger.info(f"[{tv_name}]: Connecting to Art Mode WebSocket...")
            ws.connect(art_url)
            self._logger.info(f"[{tv_name}]: WebSocket connected successfully")

            # Wait for ready events with timeout
            self._logger.info(f"[{tv_name}]: Waiting for Art Mode ready events...")
            self._wait_for_art_mode_ready(ws)
            self._logger.info(f"[{tv_name}]: Art Mode ready events received")

            # Read and optimize image
            optimized_data = self._optimize_image_for_upload(image_path)
            if len(optimized_data) == 0:
                raise ValueError("Image optimization failed")

            # Phase 1: Request upload via WebSocket
            upload_id = str(uuid.uuid4())
            current_time = time.strftime("%Y:%m:%d %H:%M:%S")

            self._logger.info(
                f"[{tv_name}]: Requesting enhanced upload for {os.path.basename(image_path)}"
            )

            self._logger.info(f"[{tv_name}]: Sending upload request to Art Mode API...")
            response = self._send_art_mode_request(
                ws,
                upload_id,
                "send_image",
                file_type="jpg",
                id=upload_id,
                conn_info={
                    "d2d_mode": "socket",
                    "connection_id": int(time.time() * 1000),
                    "id": upload_id,
                },
                image_date=current_time,
                matte_id="none",
                portrait_matte_id="none",
                file_size=len(optimized_data),
            )
            self._logger.info(f"[{tv_name}]: Received upload response from Art Mode API")

            # Parse connection info
            conn_info = json.loads(response.get("conn_info", "{}"))
            upload_host = conn_info.get("ip")
            upload_port = conn_info.get("port")
            sec_key = conn_info.get("key")

            if not all([upload_host, upload_port, sec_key]):
                raise Exception("Invalid connection info from TV")

            self._logger.info(f"[{tv_name}]: Got upload connection: {upload_host}:{upload_port}")

            # Phase 2: Upload via TLS socket
            upload_success = self._upload_via_tls_socket(
                upload_host,
                upload_port,
                sec_key,
                optimized_data,
                upload_id,
                os.path.basename(image_path),
            )

            ws.close()

            if upload_success:
                self._logger.info(
                    f"[{tv_name}]: Enhanced upload successful: {os.path.basename(image_path)}"
                )
                return upload_id
            else:
                raise Exception("TLS upload failed")

        except Exception as e:
            self._logger.error(
                f"[{tv_name}]: Enhanced upload failed for {os.path.basename(image_path)}: {e}"
            )
            return None

    def _wait_for_art_mode_ready(self, ws):
        """Wait for Art Mode WebSocket ready events."""
        ready_received = False
        connect_received = False
        start_time = time.time()
        max_wait = 10  # 10 second timeout

        while not (ready_received and connect_received):
            try:
                if time.time() - start_time > max_wait:
                    raise Exception(
                        f"Timeout waiting for Art Mode ready events after {max_wait}s"
                    )

                message = ws.recv()
                data = json.loads(message)
                event = data.get("event")

                if event == "ms.channel.connect":
                    connect_received = True
                    self._logger.debug("Art Mode channel connect received")
                elif event == "ms.channel.ready":
                    ready_received = True
                    self._logger.debug("Art Mode channel ready received")

            except websocket.WebSocketTimeoutException:
                continue  # Keep trying until max_wait timeout
            except Exception as e:
                raise Exception(f"Error waiting for Art Mode ready events: {e}") from e

    def _send_art_mode_request(self, ws, request_id: str, action: str, **params) -> dict:
        """Send request to Art Mode API and wait for response."""
        request_data = {"request_id": request_id, "action": action, **params}

        message = {
            "method": "ms.channel.emit",
            "params": {"event": "d2d_service_message", "data": json.dumps(request_data)},
        }

        self._logger.debug(f"Sending Art Mode request: {action}")
        self._logger.debug(f"Message content: {json.dumps(message)}")
        ws.send(json.dumps(message))
        self._logger.debug("Art Mode request sent, waiting for response...")

        # Wait for response
        start_time = time.time()
        timeout = 30
        while time.time() - start_time < timeout:
            try:
                elapsed = time.time() - start_time
                if elapsed > 5:  # Only log after 5 seconds to avoid spam
                    self._logger.info(f"Still waiting for Art Mode response... ({elapsed:.1f}s)")

                message = ws.recv()
                self._logger.debug(f"Received WebSocket message: {message}")
                data = json.loads(message)

                if data.get("event") == "d2d_service_message":
                    response_data = json.loads(data.get("data", "{}"))
                    self._logger.debug(f"Parsed response data: {response_data}")
                    if response_data.get("request_id") == request_id:
                        self._logger.debug(f"Received Art Mode response for {action}")
                        return response_data
                    else:
                        self._logger.debug(
                            f"Request ID mismatch: expected {request_id}, got {response_data.get('request_id')}"
                        )
                else:
                    self._logger.debug(f"Non-d2d_service_message event: {data.get('event')}")

            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                self._logger.error(f"Error receiving Art Mode response: {e}")
                raise

        raise Exception(f"Timeout waiting for Art Mode response after {timeout}s")

    def _upload_via_tls_socket(
        self, host: str, port: int, sec_key: str, image_data: bytes, upload_id: str, filename: str
    ) -> bool:
        """Upload image data via TLS socket connection."""
        # Use proper Samsung TV SSL context
        context = FTV._create_samsung_ssl_context()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)  # 15 second timeout for socket operations
        tls_sock = context.wrap_socket(sock)

        try:
            self._logger.debug(f"Connecting to TLS upload socket {host}:{port}")
            tls_sock.connect((host, port))

            # Prepare header
            header = {
                "num": 0,
                "total": 1,
                "fileLength": len(image_data),
                "fileName": filename,
                "fileType": "jpg",
                "secKey": sec_key,
                "version": "0.0.1",
            }

            # Send header
            self._logger.debug(f"Sending header for {filename}")
            header_json = json.dumps(header).encode("ascii")
            header_size = len(header_json).to_bytes(4, "big")

            tls_sock.send(header_size)
            tls_sock.send(header_json)

            # Send image data in chunks to prevent hanging
            self._logger.debug(f"Sending {len(image_data)} bytes of image data")
            chunk_size = 8192
            bytes_sent = 0

            while bytes_sent < len(image_data):
                chunk = image_data[bytes_sent : bytes_sent + chunk_size]
                sent = tls_sock.send(chunk)
                bytes_sent += sent

                if bytes_sent % (chunk_size * 10) == 0:  # Log progress every 80KB
                    self._logger.debug(f"Uploaded {bytes_sent}/{len(image_data)} bytes")

            self._logger.debug(f"TLS upload completed successfully for {filename}")
            return True

        except Exception as e:
            self._logger.error(f"TLS upload failed for {filename}: {e}")
            return False
        finally:
            tls_sock.close()

    @abk_common.function_trace
    def _upload_image_list_to_tv_sequential(self, tv_name: str, files_to_upload: list) -> list:
        """Uploads images to Frame TV sequentially with delays and skip mechanism.

        Args:
            tv_name (str): TV name
            files_to_upload (list): image file list to upload

        Returns:
            list: list of successfully uploaded file names
        """
        uploaded_file_list = []
        ftv_setting = self.ftvs.get(tv_name, None)

        if not ftv_setting:
            self._logger.error(f"[{tv_name}]: No Frame TV settings found")
            return uploaded_file_list

        self._logger.info(
            f"[{tv_name}]: Starting sequential upload of {len(files_to_upload)} images"
        )

        # Initial delay to let TV stabilize after connection
        initial_delay = 2
        self._logger.info(
            f"[{tv_name}]: Waiting {initial_delay}s for initial TV stabilization..."
        )
        time.sleep(initial_delay)

        for index, file_to_upload in enumerate(files_to_upload, 1):
            self._logger.info(
                f"[{tv_name}]: Processing image {index}/{len(files_to_upload)}: {file_to_upload}"
            )

            try:
                # Check if file exists and get file type
                if not os.path.exists(file_to_upload):
                    self._logger.warning(
                        f"[{tv_name}]: File not found, skipping: {file_to_upload}"
                    )
                    continue

                file_type = self._get_file_type(file_to_upload)
                if not file_type:
                    self._logger.warning(
                        f"[{tv_name}]: Unsupported file type, skipping: {file_to_upload}"
                    )
                    continue

                # Optimize image for Samsung TV upload
                try:
                    optimized_data = self._optimize_image_for_upload(file_to_upload)
                    if len(optimized_data) == 0:
                        self._logger.warning(
                            f"[{tv_name}]: Image optimization failed, skipping: {file_to_upload}"
                        )
                        continue
                except Exception as e:
                    self._logger.warning(
                        f"[{tv_name}]: Image optimization error, skipping {file_to_upload}: {e}"
                    )
                    continue

                self._logger.info(
                    f"[{tv_name}]: Uploading {os.path.basename(file_to_upload)} "
                    f"({len(optimized_data)} bytes)..."
                )

                # Reset connection before each upload for stability
                self._logger.info(f"[{tv_name}]: Resetting connection for stable upload...")
                try:
                    # Test connection and reconnect if needed
                    self._suppress_samsung_ssl_warnings()
                    try:
                        test_info = ftv_setting.ftv.rest_device_info()
                    finally:
                        self._restore_ssl_warnings()
                    if not test_info:
                        self._logger.warning(f"[{tv_name}]: Connection lost, reconnecting...")
                        if not self._connect_to_tv(tv_name):
                            self._logger.warning(
                                f"[{tv_name}]: Reconnection failed, skipping: {os.path.basename(file_to_upload)}"
                            )
                            continue
                except Exception as e:
                    self._logger.warning(
                        f"[{tv_name}]: Connection test failed, reconnecting: {e}"
                    )
                    if not self._connect_to_tv(tv_name):
                        self._logger.warning(
                            f"[{tv_name}]: Reconnection failed, skipping: {os.path.basename(file_to_upload)}"
                        )
                        continue

                # Try enhanced upload first if Art Mode token is available
                upload_successful = False

                try:
                    # Re-enabled after implementing proper SSL certificate handling
                    enhanced_enabled = True

                    if ftv_setting.using_art_token and enhanced_enabled:
                        self._logger.info(
                            f"[{tv_name}]: Trying enhanced upload with Art Mode token..."
                        )

                        upload_id = self._upload_image_with_enhanced_protocol(
                            tv_name, file_to_upload
                        )

                        if upload_id:
                            uploaded_file_list.append(os.path.basename(file_to_upload))
                            upload_successful = True
                            self._logger.info(
                                f"[{tv_name}]: ✅ Enhanced upload successful: {os.path.basename(file_to_upload)}"
                            )
                        else:
                            self._logger.warning(
                                f"[{tv_name}]: Enhanced upload failed, falling back to legacy method"
                            )
                    elif ftv_setting.using_art_token:
                        self._logger.info(
                            f"[{tv_name}]: Enhanced upload temporarily disabled - debugging WebSocket protocol"
                        )

                    # Fallback to legacy upload if enhanced failed or not available
                    if not upload_successful:
                        self._logger.info(f"[{tv_name}]: Using legacy upload method...")
                        file_type_str = "jpg" if file_type == FTVSupportedFileType.JPEG else "png"

                        result = ftv_setting.ftv.art().upload(
                            optimized_data, file_type=file_type_str, matte="modern_apricot"
                        )

                        if result:
                            uploaded_file_list.append(os.path.basename(file_to_upload))
                            upload_successful = True
                            self._logger.info(
                                f"[{tv_name}]: ✅ Legacy upload successful: {os.path.basename(file_to_upload)}"
                            )
                        else:
                            self._logger.warning(
                                f"[{tv_name}]: ❌ Legacy upload failed (no result): {os.path.basename(file_to_upload)}"
                            )

                except Exception as e:
                    self._logger.warning(
                        f"[{tv_name}]: ❌ Upload failed: {os.path.basename(file_to_upload)} - {e}"
                    )

                # Add longer delay between uploads for Samsung TV stability
                if index < len(files_to_upload):  # Don't delay after the last image
                    delay_seconds = 8  # Increased from 3 to 8 seconds for better stability
                    self._logger.info(
                        f"[{tv_name}]: Waiting {delay_seconds}s for TV stability before next upload..."
                    )
                    time.sleep(delay_seconds)

            except Exception as e:
                self._logger.warning(
                    f"[{tv_name}]: Unexpected error processing {file_to_upload}, skipping: {e}"
                )
                continue

        self._logger.info(
            f"[{tv_name}]: Sequential upload completed: {len(uploaded_file_list)}/{len(files_to_upload)} images uploaded successfully"
        )

        # Record uploaded files
        if uploaded_file_list:
            self._record_uploaded_image_files(tv_name, uploaded_file_list)

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
    def _delete_images_with_enhanced_protocol(self, tv_name: str, image_list: list) -> list:
        """Delete images using enhanced Art Mode protocol with Art Mode token.

        Args:
            tv_name (str): TV name
            image_list (list): list of image file names to delete

        Returns:
            list: list of successfully deleted images
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if not ftv_setting:
            self._logger.error(f"[{tv_name}]: No Frame TV settings found")
            return []

        if not ftv_setting.using_art_token:
            self._logger.warning(
                f"[{tv_name}]: Art Mode token not available for enhanced deletion"
            )
            return []

        # Get Art Mode token
        art_token = None
        if ftv_setting.art_token_path and os.path.isfile(ftv_setting.art_token_path):
            try:
                with open(ftv_setting.art_token_path) as f:
                    art_token = f.read().strip()
            except Exception as e:
                self._logger.error(f"[{tv_name}]: Failed to read Art Mode token: {e}")
                return []

        if not art_token:
            self._logger.error(f"[{tv_name}]: Art Mode token not found")
            return []

        deleted_images = []

        try:
            # Enhanced Art Mode WebSocket connection with token
            name = "BWP_Enhanced_Delete"
            b64_name = base64.b64encode(name.encode()).decode()
            art_url = f"wss://{ftv_setting.ftv.host}:{ftv_setting.ftv.port}/api/v2/channels/com.samsung.art-app?name={b64_name}&token={art_token}"

            # Create WebSocket connection with proper Samsung TV SSL context
            samsung_ssl_context = FTV._create_samsung_ssl_context()
            ws = websocket.WebSocket(sslopt={"context": samsung_ssl_context})
            ws.settimeout(30)
            ws.connect(art_url)

            # Wait for ready events
            self._wait_for_art_mode_ready(ws)

            # Get current art list to find content IDs
            self._logger.info(f"[{tv_name}]: Getting current art list for deletion mapping...")
            art_list_response = self._send_art_mode_request(
                ws, str(uuid.uuid4()), "get_content_list", category_id="MY-C0002"
            )
            content_list = json.loads(art_list_response.get("content_list", "[]"))

            # Map file names to content IDs
            content_id_map = {}
            for art_item in content_list:
                file_name = art_item.get("file_name", "")
                content_id = art_item.get("content_id", "")
                if file_name and content_id:
                    content_id_map[file_name] = content_id

            # Find content IDs for images to delete
            content_ids_to_delete = []
            for image_name in image_list:
                if image_name in content_id_map:
                    content_ids_to_delete.append({"content_id": content_id_map[image_name]})
                    self._logger.debug(
                        f"[{tv_name}]: Found content ID for {image_name}: {content_id_map[image_name]}"
                    )
                else:
                    self._logger.warning(f"[{tv_name}]: No content ID found for {image_name}")

            if content_ids_to_delete:
                self._logger.info(
                    f"[{tv_name}]: Deleting {len(content_ids_to_delete)} images using enhanced protocol..."
                )

                # Send deletion request
                delete_response = self._send_art_mode_request(
                    ws,
                    str(uuid.uuid4()),
                    "delete_image_list",
                    content_id_list=content_ids_to_delete,
                )

                if "content_id_list" in delete_response:
                    # Extract successfully deleted images
                    for image_name in image_list:
                        if image_name in content_id_map:
                            deleted_images.append(image_name)
                            self._logger.info(
                                f"[{tv_name}]: ✅ Enhanced deletion successful: {image_name}"
                            )
                else:
                    self._logger.warning(f"[{tv_name}]: Enhanced deletion may have failed")
            else:
                self._logger.warning(f"[{tv_name}]: No valid content IDs found for deletion")

            ws.close()

        except Exception as e:
            self._logger.error(f"[{tv_name}]: Enhanced deletion failed: {e}")

        return deleted_images

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
                # Try enhanced deletion first if Art Mode token is available
                if ftv_setting.using_art_token:
                    self._logger.info(
                        f"[{tv_name}]: Trying enhanced deletion with Art Mode token..."
                    )
                    deleted_images = self._delete_images_with_enhanced_protocol(
                        tv_name, uploaded_images
                    )

                    if deleted_images:
                        self._logger.info(
                            f"[{tv_name}]: Enhanced deletion successful: {len(deleted_images)} images deleted"
                        )
                    else:
                        self._logger.warning(
                            f"[{tv_name}]: Enhanced deletion failed, falling back to legacy method"
                        )

                # Fallback to legacy deletion if enhanced failed or not available
                if not deleted_images:
                    self._logger.info(f"[{tv_name}]: Using legacy deletion method...")
                    for image_to_delete in uploaded_images:
                        try:
                            ftv_setting.ftv.art().delete(image_to_delete)
                            # ftv_setting.ftv.art().delete_list(image_list) # not working
                            deleted_images.append(image_to_delete)
                        except Exception as exp:
                            self._logger.error(
                                f"[{tv_name}]: image NOT deleted: {image_to_delete} {exp = }"
                            )

                remaining_images = list(set(uploaded_images) - set(deleted_images))
                self._logger.debug(f"[{tv_name}]: {deleted_images = }")
                self._logger.debug(f"[{tv_name}]: {remaining_images = }")
                self._record_uploaded_image_files(tv_name, remaining_images)
        return deleted_images

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
    def _apply_filter_to_art(
        self, tv_name: str, file_name: str, filter_name: FTVImageFilters
    ) -> None:
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
        """Connects to Frame TV using Samsung TV WebSocket API.

        Args:
            tv_name (str): TV name
        Returns:
            bool: True if the connection was successful, False otherwise
        """
        ftv_setting = self.ftvs.get(tv_name, None)
        if ftv_setting:
            try:
                self._logger.info(f"[{tv_name}]: Attempting to wake up TV...")
                wol_success = self._wake_up_tv(tv_name)

                if wol_success:
                    self._logger.info(f"[{tv_name}]: Wake-on-LAN packet sent successfully")
                else:
                    self._logger.warning(f"[{tv_name}]: Wake-on-LAN failed, proceeding anyway...")

                # Give TV time to wake up
                wake_delay = 5  # Increased wait time for stability
                self._logger.info(
                    f"[{tv_name}]: Waiting {wake_delay}s for TV to become responsive..."
                )
                time.sleep(wake_delay)

                self._logger.info(f"[{tv_name}]: Testing basic connection...")
                # Test basic connectivity first
                tv_info = self._get_device_info(tv_name)
                if not tv_info:
                    raise ConnectionError("Failed to get device info")

                device_name = tv_info.get("device", {}).get("name", "Unknown")
                self._logger.info(f"[{tv_name}]: Device connected: {device_name}")

                # Display formatted TV model information
                self.get_tv_model_info(tv_name)

                # Display Art Mode token status
                self._display_art_mode_token_status(tv_name)

                # Verify Frame TV support
                device_info = tv_info.get("device", {})
                if device_info.get("FrameTVSupport") != "true":
                    self._logger.warning(
                        f"[{tv_name}]: Device does not support Frame TV features"
                    )
                    ftv_setting.reachable = False
                    return False

                # Test art mode support with error handling
                try:
                    art_supported = self._is_art_mode_supported(tv_name)
                    if art_supported:
                        self._logger.info(f"[{tv_name}]: Art mode is supported and accessible")
                    else:
                        self._logger.warning(f"[{tv_name}]: Art mode is not supported")
                        ftv_setting.reachable = False
                        return False
                except Exception as art_exc:
                    self._logger.warning(f"[{tv_name}]: Could not verify art mode: {art_exc}")
                    # Still mark as reachable for basic operations

                ftv_setting.reachable = True
                self._logger.info(f"[{tv_name}]: Successfully connected and ready for operations")

            except Exception as exc:
                self._logger.error(f"[{tv_name}]: Connection failed: {exc}")
                self._logger.error(
                    f"[{tv_name}]: Troubleshooting tips:\n"
                    f"  1. Ensure TV is powered on\n"
                    f"  2. Check IP address: {ftv_setting.ftv.host}\n"
                    f"  3. Verify TV is on same network\n"
                    f"  4. Check if TV allows external connections"
                )
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
        success_count = 0
        self._logger.info(f"Starting FTV daily image update for {len(self.ftvs)} TV(s)...")
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
                # Ensure TV is in art mode for Frame TV operations
                self._logger.info(f"[{tv_name}]: Ensuring TV is in art mode...")
                if not self._is_tv_in_art_mode(tv_name):
                    self._logger.info(f"[{tv_name}]: Activating art mode...")
                    self._activate_art_mode(tv_name, True)
                    time.sleep(2)  # Give TV time to switch modes

                self._logger.info(f"[{tv_name}]: Deleting old uploaded images...")
                deleted_images = self._delete_uploaded_images_from_tv(tv_name)
                self._logger.info(f"[{tv_name}]: Deleted {len(deleted_images)} old images")

                self._logger.info(f"[{tv_name}]: Uploading new images sequentially...")
                uploaded_images = self._upload_image_list_to_tv_sequential(tv_name, image_list)
                self._logger.info(
                    f"[{tv_name}]: Successfully uploaded {len(uploaded_images)} new images"
                )

                if uploaded_images:
                    success_count += 1
                    self._logger.info(f"[{tv_name}]: Daily image update completed successfully!")
                else:
                    self._logger.warning(f"[{tv_name}]: No new images were uploaded")

            except Exception as exc:
                self._logger.error(f"[{tv_name}]: Error during image update: {exc}")

        self._logger.info(
            f"FTV daily image update completed. Success: {success_count}/{len(self.ftvs)} TVs"
        )
        return success_count > 0

    @abk_common.function_trace
    def validate_wake_on_lan_setup(self) -> bool:
        """Validate Wake-on-LAN setup for all configured Frame TVs.

        Returns:
            bool: True if all Frame TVs have valid Wake-on-LAN configuration
        """
        self._logger.info("🔍 Validating Wake-on-LAN setup for all Frame TVs...")

        if not self.ftvs:
            self._logger.error("❌ No Frame TVs configured")
            return False

        all_valid = True
        for tv_name in self.ftvs:
            self._logger.info(f"📺 Validating {tv_name}:")
            if not self._validate_wake_on_lan(tv_name):
                all_valid = False

        if all_valid:
            self._logger.info("✅ All Frame TVs have valid Wake-on-LAN configuration")
        else:
            self._logger.error("❌ Some Frame TVs have invalid Wake-on-LAN configuration")

        return all_valid


if __name__ == "__main__":
    raise RuntimeError(
        f"{__file__}: This module should not be executed directly. Only for imports"
    )

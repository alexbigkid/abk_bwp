"""Main function or entry module for the ABK BingWallPaper (abk_bwp) package."""

# Standard lib imports
import os
import sys

# Third party imports
import tomlkit
from colorama import Fore, Style

# Local imports
from abk_bwp import abk_common, clo, install, uninstall
from abk_bwp.config import DESKTOP_IMG_KW, FTV_KW, ROOT_KW, bwp_config
from abk_bwp.lazy_logger import LazyLoggerProxy


BWP_ENABLE = "enable"
BWP_DISABLE = "disable"
BWP_DESKTOP_AUTO_UPDATE_OPTION = "dau"
BWP_FTV_OPTION = "ftv"
BWP_CONFIG_RELATIVE_PATH = "config/bwp_config.toml"


logger = LazyLoggerProxy(__name__)


@abk_common.function_trace
def get_config_enabled_setting(key_to_read: str) -> bool:
    """Loads enable setting from desktop_img or from ftv section.

    Args:
        key_to_read (str): desktop_img or ftv
    Returns:
        bool: True if feature enabled, False if disabled
    """
    return bwp_config.get(key_to_read, {}).get("enabled", None)


@abk_common.function_trace
def update_enable_field_in_toml_file(key_to_update: str, update_to: bool, field: str = "enabled") -> None:
    """Updates field in desktop_img or ftv section.

    Args:
        key_to_update (str): desktop_img or ftv
        update_to (bool): True to enable, False to disable
        field (str): field name to update (default: "enabled")
    """
    logger.debug(f"{key_to_update}.{field}: {update_to=}")
    config_toml_file_name = os.path.join(os.path.dirname(__file__), BWP_CONFIG_RELATIVE_PATH)
    with open(config_toml_file_name, encoding="utf-8") as read_fh:
        config_data = tomlkit.load(read_fh)
        config_data[key_to_update][field] = update_to  # type: ignore
    with open(config_toml_file_name, mode="w", encoding="utf-8") as write_fh:
        tomlkit.dump(config_data, write_fh)


@abk_common.function_trace
def update_root_field_in_toml_file(key_to_update: str, update_to: bool) -> None:
    """Updates root-level field in config file.

    Args:
        key_to_update (str): root-level key to update
        update_to (bool): True to enable, False to disable
    """
    logger.debug(f"{key_to_update=}: {update_to=}")
    config_toml_file_name = os.path.join(os.path.dirname(__file__), BWP_CONFIG_RELATIVE_PATH)
    with open(config_toml_file_name, encoding="utf-8") as read_fh:
        config_data = tomlkit.load(read_fh)
        config_data[key_to_update] = update_to  # type: ignore
    with open(config_toml_file_name, mode="w", encoding="utf-8") as write_fh:
        tomlkit.dump(config_data, write_fh)


@abk_common.function_trace
def handle_desktop_auto_update_option(enable_option: str | None) -> None:
    """Handles request to enable/disable auto update desktop image feature.

    Args:
        enable_option (Union[str, None]): enable, disable or None
    """
    if enable_option is None:
        return
    if (enable := enable_option == BWP_ENABLE) or enable_option == BWP_DISABLE:
        is_enabled = get_config_enabled_setting(str(DESKTOP_IMG_KW.DESKTOP_IMG.value))
        if is_enabled != enable:
            update_enable_field_in_toml_file(key_to_update=DESKTOP_IMG_KW.DESKTOP_IMG.value, update_to=enable)
            # Automation setup is now controlled by auto_img_fetch, not desktop_img
            _handle_automation_setup()


@abk_common.function_trace
def _handle_automation_setup() -> None:
    """Handles automation setup based on auto_img_fetch setting."""
    auto_fetch_enabled = bwp_config.get(ROOT_KW.IMG_AUTO_FETCH.value, False)

    if auto_fetch_enabled:
        install.bwp_install()
    else:
        uninstall.bwp_uninstall()


@abk_common.function_trace
def handle_img_auto_fetch_option(enable_option: str | None) -> None:
    """Handles request to enable/disable automated image download scheduling.

    Args:
        enable_option (Union[str, None]): enable, disable or None
    """
    if enable_option is None:
        return
    if (enable := enable_option == BWP_ENABLE) or enable_option == BWP_DISABLE:
        is_enabled = bwp_config.get(ROOT_KW.IMG_AUTO_FETCH.value, False)
        if is_enabled != enable:
            update_root_field_in_toml_file(key_to_update=ROOT_KW.IMG_AUTO_FETCH.value, update_to=enable)
            # Automation setup is controlled by img_auto_fetch
            _handle_automation_setup()


@abk_common.function_trace
def handle_ftv_option(enable_option: str | None) -> None:
    """Handles request to enable/disable generating and updating images on Frame TV.

    Args:
        enable_option (Union[str, None]): enable, disable or None
    """
    if enable_option is None:
        return
    if (enable := enable_option == BWP_ENABLE) or enable_option == BWP_DISABLE:
        is_enabled = get_config_enabled_setting(str(FTV_KW.FTV.value))
        if is_enabled != enable:
            update_enable_field_in_toml_file(key_to_update=FTV_KW.FTV.value, update_to=enable)


@abk_common.function_trace
def handle_usb_mode_option(enable_option: str | None) -> None:
    """Handles request to enable/disable USB mass storage mode for Frame TV.

    Args:
        enable_option (Union[str, None]): enable, disable or None
    """
    if enable_option is None:
        return
    if (enable := enable_option == BWP_ENABLE) or enable_option == BWP_DISABLE:
        is_enabled = bwp_config.get(FTV_KW.FTV.value, {}).get(FTV_KW.USB_MODE.value, True)
        if is_enabled != enable:
            update_enable_field_in_toml_file(key_to_update=FTV_KW.FTV.value, update_to=enable, field=FTV_KW.USB_MODE.value)


def abk_bwp(clo: clo.CommandLineOptions) -> None:
    """Basically the main function of the package."""
    exit_code = 0
    try:
        logger.debug(f"{clo.options=}")
        logger.debug(f"{clo._args=}")
        handle_desktop_auto_update_option(clo.options.desktop_auto_update)
        handle_ftv_option(clo.options.frame_tv)
        handle_img_auto_fetch_option(clo.options.img_auto_fetch)
        handle_usb_mode_option(clo.options.usb_mode)
    except Exception as exception:
        logger.error(f"{Fore.RED}ERROR: executing bingwallpaper")
        logger.exception(f"EXCEPTION: {exception}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    command_line_options = clo.CommandLineOptions()
    command_line_options.handle_options()
    abk_bwp(command_line_options)

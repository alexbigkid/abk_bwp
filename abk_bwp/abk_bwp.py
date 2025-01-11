"""Main function or entry module for the ABK BingWallPaper (abk_bwp) package."""

# Standard lib imports
import os
import sys
import logging
from typing import Union

# Third party imports
import tomlkit
from colorama import Fore, Style

# Local imports
from config import DESKTOP_IMG_KW, FTV_KW, bwp_config
import abk_common
import install
import uninstall


BWP_ENABLE = "enable"
BWP_DISABLE = "disable"
BWP_DESKTOP_AUTO_UPDATE_OPTION = "dau"
BWP_FTV_OPTION = "ftv"
BWP_CONFIG_RELATIVE_PATH = "config/bwp_config.toml"


abk_bwp_logger = logging.getLogger(__name__)
abk_bwp_logger.disabled = True


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
def update_enable_field_in_toml_file(key_to_update: str, update_to: bool) -> None:
    """Updates enable field in desktop_img or ftv section.

    Args:
        key_to_update (str): desktop_img or ftv
        update_to (bool): True to enable, False to disable
    """
    abk_bwp_logger.debug(f"{key_to_update=}: {update_to=}")
    config_toml_file_name = os.path.join(os.path.dirname(__file__), BWP_CONFIG_RELATIVE_PATH)
    with open(config_toml_file_name, mode="rt", encoding="utf-8") as read_fh:
        config_data = tomlkit.load(read_fh)
        config_data[key_to_update]["enabled"] = update_to  # type: ignore
    with open(config_toml_file_name, mode="wt", encoding="utf-8") as write_fh:
        tomlkit.dump(config_data, write_fh)


@abk_common.function_trace
def handle_desktop_auto_update_option(enable_option: Union[str, None]) -> None:
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
            if enable:
                install.bwp_install()
            else:
                uninstall.bwp_uninstall()


@abk_common.function_trace
def handle_ftv_option(enable_option: Union[str, None]) -> None:
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


def abk_bwp():
    """Basically the main function of the package."""
    exit_code = 0
    try:
        abk_bwp_logger.debug(f"{command_line_options.options=}")
        abk_bwp_logger.debug(f"{command_line_options._args=}")
        handle_desktop_auto_update_option(command_line_options.options.dau)
        handle_ftv_option(command_line_options.options.ftv)
    except Exception as exception:
        abk_bwp_logger.error(f"{Fore.RED}ERROR: executing bingwallpaper")
        abk_bwp_logger.error(f"EXCEPTION: {exception}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    command_line_options = abk_common.CommandLineOptions()
    command_line_options.handle_options()
    abk_bwp_logger = command_line_options._logger
    abk_bwp()

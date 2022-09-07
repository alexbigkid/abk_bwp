
# Standard lib imports
import sys
from typing import Union

# Third party imports
import tomlkit
from colorama import Fore, Style

# Local imports
from local_modules import DESKTOP_IMG_KW, FTV_KW, bwp_config
from abk_common import CommandLineOptions, function_trace



BWP_ENABLE = "enable"
BWP_DISABLE = "disable"
BWP_DESKTOP_AUTO_UPDATE_OPTION = "dau"
BWP_FTV_OPTION = "ftv"


@function_trace
def get_config_enabled_setting(key_to_read: str) -> bool:
    # main_logger.debug(f"{key_to_read=}")
    # print(f"{key_to_read=}")
    return bwp_config.get(key_to_read, {}).get("enabled", None)


@function_trace
def update_toml_file(key_to_update: str, value_to_update_to: bool) -> None:
    # main_logger.debug(f"{key_to_update=}: {value_to_update_to=}")
    # TODO: need to do some tomkit magic
    pass


@function_trace
def handle_desktop_auto_update_option(desktop_auto_update_option: Union[str, None]) -> None:
    main_logger.debug(f"{desktop_auto_update_option=}")
    if desktop_auto_update_option is None:
        return
    elif desktop_auto_update_option == BWP_ENABLE:
        is_enabled = get_config_enabled_setting(str(DESKTOP_IMG_KW.DESKTOP_IMG.value))
        if is_enabled == False:
            update_toml_file(key_to_update=DESKTOP_IMG_KW.DESKTOP_IMG.value, value_to_update_to=True)
        # TODO: run installation
    elif desktop_auto_update_option == BWP_DISABLE:
        is_enabled = get_config_enabled_setting(str(DESKTOP_IMG_KW.DESKTOP_IMG.value))
        if is_enabled == True:
            update_toml_file(key_to_update=DESKTOP_IMG_KW.DESKTOP_IMG.value, value_to_update_to=False)
        # TODO: run deinstallation


@function_trace
def handle_ftv_option(ftv_enable_option: Union[str, None]) -> None:
    if ftv_enable_option is None:
        return
    if (ftv_enable := ftv_enable_option == BWP_ENABLE) or ftv_enable_option == BWP_DISABLE:
        is_enabled = get_config_enabled_setting(str(FTV_KW.FTV.value))
        if is_enabled != ftv_enable:
            update_toml_file(key_to_update=FTV_KW.FTV.value, value_to_update_to=ftv_enable)


def main():
    exit_code = 0
    try:
        main_logger.debug(f"{command_line_options.options=}")
        main_logger.debug(f"{command_line_options._args=}")
        handle_desktop_auto_update_option(command_line_options.options.dau)
        handle_ftv_option(command_line_options.options.ftv)
    except Exception as exception:
        main_logger.error(f"{Fore.RED}ERROR: executing bingwallpaper")
        main_logger.error(f"EXCEPTION: {exception}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    command_line_options = CommandLineOptions()
    command_line_options.handle_options()
    main_logger = command_line_options._logger
    main()

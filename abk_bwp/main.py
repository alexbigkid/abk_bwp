
# Standard lib imports
import sys

# Third party imports
from colorama import Fore, Style

# LOcal imports
import abk_common


def main():

    exit_code = 0
    try:
        main_logger.debug(f"main: {command_line_options=}")
    except Exception as exception:
        main_logger.error(f"{Fore.RED}ERROR: executing bingwallpaper")
        main_logger.error(f"EXCEPTION: {exception}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    command_line_options = abk_common.CommandLineOptions()
    command_line_options.handle_options()
    main_logger = command_line_options._logger
    main()

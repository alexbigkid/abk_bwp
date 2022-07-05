import os
import sys
import logging

from colorama import Fore, Style

# sys.path.append('/Users/aberger/.pyenv/versions/bwp/lib/python3.10/site-packages/')

import samsungtvws
from samsungtvws import SamsungTVWS
# from samsungtvws import SamsungTVArt



class FTV(object):


    @property
    def ftv(self) -> SamsungTVWS:
        if self._ftv == None:
            if not self._ftv_ip_address:
                self.load_ftv_settings('ftv_settings.json')
            # self._ftv = SamsungTVWS(self._ftv_ip_address, port=self._port, token=self._api_token)
            self._ftv = SamsungTVWS(self._ftv_ip_address, token=self._api_token)
        return self._ftv


    def __init__(self):
        # Increase debug level
        self._ftv = None
        self._ftv_ip_address = None
        logging.basicConfig(level=logging.INFO)


    def get_environment_variable_value(self, env_variable: str) -> str:
        """Get environment variable value from shell
        Args:
            env_variable (str): name of the environment variable to load
        Returns:
            str: the value of the variable
        """
        return os.environ[env_variable] if env_variable in os.environ else ''

    def load_ftv_settings(self, file_name:str) -> None:
        self._ftv_ip_address = '192.168.0.119'
        self._api_token = self.get_environment_variable_value('ABK_SH_API_TOKEN')
        self._port = 8002
        print(f'\n ---- ABK: ABK_SH_API_TOKEN: {self._api_token}')
        # self._api_token = f'{os.path.dirname(os.path.realpath(__file__))}{ABK_SH_API_TOKEN_FILE_NAME}'


    def is_art_mode_supported(self) -> bool:
        # Is art mode supported?
        info = self.ftv.art().supported()
        logging.info(info)
        return False


    def list_art_on_tv(self) -> None:
        # List the art available on the device
        info = self.ftv.art().available()
        logging.info(info)


    def get_current_art_info(self) -> None:
        # Retrieve information about the currently selected art
        info = self.ftv.art().get_current()
        logging.info(info)


    def get_current_art_image(self, file_name:str):
        # Retrieve a thumbnail for a specific piece of art. Returns a JPEG.
        thumbnail = self.ftv.art().get_thumbnail(file_name)
        return thumbnail


    def set_current_art_image(self, file_name) -> None:
        # Set a piece of art
        self.ftv.art().select_image(file_name)


    def set_current_art_image_delayed(self, file_name) -> None:
        # Set a piece of art, but don't immediately show it if not in art mode
        self.ftv.art().select_image(file_name, show=False)


    def is_tv_in_art_mode(self) -> bool:
        # Determine whether the TV is currently in art mode
        info = self.ftv.art().get_artmode()
        logging.info(info)
        return False


    def activate_art_mode(self, art_mode_on:bool=False) -> None:
        # Switch art mode on or off
        self.ftv.art().set_artmode(art_mode_on)


    def upload_image_to_tv(self, file_name:str) -> None:
        # Upload a picture
        file = open(file_name, 'rb')
        data = file.read()
        self.ftv.art().upload(data)


    def upload_jpeg_to_tv(self, data:bytes) -> None:
        # If uploading a JPEG
        self.ftv.art().upload(data, file_type='JPEG')


    def upload_jpeg_with_filter(self, data:bytes, filter_name:str='modern_apricot') -> None:
        # To set the matte to modern and apricot color
        self.ftv.art().upload(data, matte=filter_name)


    def delete_image_from_tv(self, file_name:str) -> None:
        # Delete an uploaded item
        self.ftv.art().delete(file_name)


    def delete_image_list_from_tv(self, image_list:list) -> None:
        # Delete multiple uploaded items
        self.ftv.art().delete_list(image_list)


    def list_available_filters(self) -> list:
        # List available photo filters
        info = self.ftv.art().get_photo_filter_list()
        logging.info(info)
        return []


    def apply_filter_to_art(self, file_name:str, filter_name:str='ink') -> None:
        # Apply a filter to a specific piece of art
        self.ftv.art().set_photo_filter(file_name, filter_name)



def main():
    exit_code = 0
    try:
        abk_ftv = FTV()
        abk_ftv.is_art_mode_supported()
        # abk_ftv.ftv.shortcuts().power()
        # abk_ftv.list_art_on_tv()
        abk_ftv.get_current_art_info()
    except Exception as exception:
        print(f"{Fore.RED}ERROR: executing abk ftv")
        print(f"EXCEPTION: {exception}{Style.RESET_ALL}")
        exit_code = 1
    finally:
        sys.exit(exit_code)


if __name__ == '__main__':
    main()

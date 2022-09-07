"""Unit tests for bingwallpaper.py"""

# Standard library imports
import logging
import os
import sys
from typing import Union
import unittest
from unittest.mock import mock_open, patch, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../abk_bwp')))

# Third party imports
from parameterized import parameterized

# Own modules imports
from config import FTV_KW, bwp_config
import main


class TestMain(unittest.TestCase):

    # @classmethod
    # def setUpClass(cls):
    #     cls.logger = logging.getLogger('main.main_logger')
        # cls.main_logger = logging.Logger(__name__)
        # cls.main_logger.level = logging.DEBUG
        # cls.stream_handler = logging.StreamHandler(sys.stdout)
        # cls.main_logger.addHandler(cls.stream_handler)


    # @classmethod
    # def tearDownClass(cls):
    #     cls.main_logger.removeHandler(cls.stream_handler)


    def setUp(self) -> None:
        self.maxDiff = None
        # self.logger = logging.getLogger("main")
        return super().setUp()


    @parameterized.expand([
        # input         ftv confg       # result
        ["enable",      False,          True],
        ["disable",     True,           False],
    ])
    def test__main_handle_ftv_option__calls_update_toml_file(self, ftv_input: Union[str, None], ftv_enabled: bool, exp_ftv_enabled: bool) -> None:
        # logger = logging.getLogger('main.main_logger')
        # with patch.object(logger, 'debug') as mock_logger:
        with patch.dict(bwp_config, {"ftv": {"enabled": ftv_enabled}}) as mock_bwp_config:
            with patch("main.update_toml_file") as  mock_update_toml_file:
                main.handle_ftv_option(ftv_input)
        mock_update_toml_file.assert_called_once_with(key_to_update=FTV_KW.FTV.value, value_to_update_to=exp_ftv_enabled)
        self.assertTrue(ftv_enabled != exp_ftv_enabled)


    @parameterized.expand([
        # input         ftv confg       # result
        [None,          True,           True],
        [None,          False,          False],
        ["enable",      True,           True],
        ["disable",     False,          False],
        ["NotValid",    True,           True],
        ["NotValid",    False,          False],
        ["",            True,           True],
        ["",            False,          False],
    ])
    def test__main_handle_ftv_option__does_not_calls_update_toml_file(self, ftv_input: Union[str, None], ftv_enabled: bool, exp_ftv_enabled: bool) -> None:
        with patch.dict(bwp_config, {"ftv": {"enabled": ftv_enabled}}) as mock_bwp_config:
            with patch("main.update_toml_file") as  mock_update_toml_file:
                main.handle_ftv_option(ftv_input)
        mock_update_toml_file.assert_not_called()
        self.assertTrue(ftv_enabled == exp_ftv_enabled)


if __name__ == "__main__":
    unittest.main()

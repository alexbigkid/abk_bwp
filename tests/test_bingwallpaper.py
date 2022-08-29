"""Unit tests for bingwallpaper.py"""

# Standard library imports
import os
import sys
import unittest
from unittest.mock import mock_open, patch, call
from parameterized import parameterized

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Third party imports

# Own modules imports
import bingwallpaper
from config import bwp_config


class TestAbkCommon(unittest.TestCase):
    mut = None

    def setUp(self) -> None:
        self.maxDiff = None
        return super().setUp()

    def tearDown(self) -> None:
        # cache needs to be clearead after each test for the next test to be able to set different mocks
        # print(f"ABK: cache_info: {bingwallpaper.get_img_region.cache_info()}")
        bingwallpaper.get_img_region.cache_clear()
        return super().tearDown()

# alt_dl_service = ["bing", "peapix"]
# alt_peapix_region = ["au", "ca", "cn", "de", "fr", "in", "jp", "es", "gb", "us"]

    @parameterized.expand([
        ["au",          "bing"],
        ["ca",          "bing"],
        ["cn",          "bing"],
        ["de",          "bing"],
        ["fr",          "bing"],
        ["in",          "bing"],
        ["jp",          "bing"],
        ["es",          "bing"],
        ["gb",          "bing"],
        ["notValidReg", "bing"],
        ["notValidReg", "peapix"],
        ["de",          "NotValidService"],
        ["us",          "NotValidService"],
        ["NotValidReg", "NotValidService"],
    ])
    def test__get_img_region__given_an_invalid_setting_returns_default_region(self, img_region:str, img_dl_service:str) -> None:
        exp_region = "us"
        with patch.dict(bwp_config, {"region": img_region, "dl_service": img_dl_service}) as mock_bwp_config:
            act_region = bingwallpaper.get_img_region()
        self.assertTrue(act_region, exp_region)


    @parameterized.expand([
        ["au",          "peapix"],
        ["ca",          "peapix"],
        ["cn",          "peapix"],
        ["de",          "peapix"],
        ["fr",          "peapix"],
        ["in",          "peapix"],
        ["jp",          "peapix"],
        ["es",          "peapix"],
        ["gb",          "peapix"],
        ["gb",          "peapix"],
        ["us",          "peapix"],
        ["us",          "bing"],
    ])
    def test__get_img_region__given_a_valid_setting_returns_defined_region(self, img_region:str, img_dl_service:str) -> None:
        with patch.dict(bwp_config, {"region": img_region, "dl_service": img_dl_service}):
            act_region = bingwallpaper.get_img_region()
        self.assertTrue(act_region, img_region)



if __name__ == '__main__':
    unittest.main()

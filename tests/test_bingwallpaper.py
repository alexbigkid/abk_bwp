"""Unit tests for bingwallpaper.py."""

# Standard library imports
from typing import Tuple
import unittest
from unittest.mock import patch

# Third party imports
from parameterized import parameterized

# Own modules imports
from context import config
from context import bingwallpaper


class TestBingwallpaper(unittest.TestCase):
    """Test BingWallPaper."""

    mut = None

    def setUp(self) -> None:
        """Set up."""
        self.maxDiff = None
        return super().setUp()

    def tearDown(self) -> None:
        """Tear down."""
        # cache needs to be cleared after each test for the next test to be able to set different mocks
        # print(f"ABK: cache_info: {bingwallpaper.normalize_jpg_quality.cache_info()}")
        bingwallpaper.normalize_jpg_quality.cache_clear()
        # print(f"ABK: cache_info: {bingwallpaper.get_img_region.cache_info()}")
        bingwallpaper.get_config_img_region.cache_clear()
        # print(f"ABK: cache_info: {bingwallpaper.get_config_bing_img_region.cache_info()}")
        bingwallpaper.get_config_bing_img_region.cache_clear()
        # print(f"ABK: cache_info: {bingwallpaper.get_resize_jpeg_quality.cache_info()}")
        bingwallpaper.get_config_store_jpg_quality.cache_clear()
        # print(f"ABK: cache_info: {bingwallpaper.get_config_background_img_size.cache_info()}")
        bingwallpaper.get_config_background_img_size.cache_clear()
        return super().tearDown()

    @parameterized.expand(
        [["notValidReg", "bing"], ["notValidReg", "peapix"], ["NotValidReg", "NotValidService"]]
    )
    def test__get_img_region__given_an_invalid_setting_returns_default_region(
        self, img_region: str, img_dl_service: str
    ) -> None:
        """test__get_img_region__given_an_invalid_setting_returns_default_region.

        Args:
            img_region (str): image region
            img_dl_service (str): image download service
        """
        exp_region = "us"
        with patch.dict(config.bwp_config, {"region": img_region, "dl_service": img_dl_service}):
            act_region = bingwallpaper.get_config_img_region()
        self.assertEqual(act_region, exp_region)

    @parameterized.expand(
        [
            ["au", "peapix"],
            ["ca", "peapix"],
            ["cn", "peapix"],
            ["de", "peapix"],
            ["fr", "peapix"],
            ["in", "peapix"],
            ["jp", "peapix"],
            ["es", "peapix"],
            ["gb", "peapix"],
            ["us", "peapix"],
            ["au", "bing"],
            ["ca", "bing"],
            ["cn", "bing"],
            ["de", "bing"],
            ["fr", "bing"],
            ["in", "bing"],
            ["jp", "bing"],
            ["es", "bing"],
            ["gb", "bing"],
            ["us", "bing"],
        ]
    )
    def test__get_img_region__given_a_valid_setting_returns_defined_region(
        self, img_region: str, img_dl_service: str
    ) -> None:
        """test__get_img_region__given_a_valid_setting_returns_defined_region.

        Args:
            img_region (str): image region
            img_dl_service (str): image download service
        """
        with patch.dict(config.bwp_config, {"region": img_region, "dl_service": img_dl_service}):
            act_region = bingwallpaper.get_config_img_region()
        self.assertEqual(act_region, img_region)

    @parameterized.expand(
        [
            ["au", "bing", "en-AU"],
            ["ca", "bing", "en-CA"],
            ["cn", "bing", "zh-CN"],
            ["de", "bing", "de-DE"],
            ["fr", "bing", "fr-FR"],
            ["in", "bing", "hi-IN"],
            ["jp", "bing", "ja-JP"],
            ["es", "bing", "es-ES"],
            ["gb", "bing", "en-GB"],
            ["us", "bing", "en-US"],
            ["notValid", "bing", "en-US"],
            ["notValid", "peapix", "en-US"],
            ["notValid", "notValidService", "en-US"],
        ]
    )
    def test__get_img_region__given_a_valid_setting_returns_defined_bing_region(
        self, img_region: str, img_dl_service: str, exp_bing_region: str
    ) -> None:
        """test__get_img_region__given_a_valid_setting_returns_defined_bing_region.

        Args:
            img_region (str): image region
            img_dl_service (str): image download service
            exp_bing_region (str): expected bing region
        """
        with patch.dict(config.bwp_config, {"region": img_region, "dl_service": img_dl_service}):
            act_bing_region = bingwallpaper.get_config_bing_img_region()
        self.assertEqual(act_bing_region, exp_bing_region)

    @parameterized.expand(
        [
            # read_jpeg_quality    exp_jpeg_quality
            [-2, 70],
            [-1, 70],
            [0, 70],
            [1, 70],
            [71, 71],
            [72, 72],
            [89, 89],
            [99, 99],
            [100, 100],
            [101, 100],
            [898, 100],
        ]
    )
    def test__get_resize_jpeg_quality__returns_normalized_resize_jpeg_quality(
        self, read_jpeg_quality: int, exp_jpeg_quality
    ) -> None:
        """test__get_resize_jpeg_quality__returns_normalized_resize_jpeg_quality.

        Args:
            read_jpeg_quality (int): read JPEG quality
            exp_jpeg_quality (_type_): expected JPEG quality
        """
        with patch.dict(config.bwp_config, {"store_jpg_quality": read_jpeg_quality}):
            act_jpeg_quality = bingwallpaper.get_config_store_jpg_quality()
        self.assertEqual(act_jpeg_quality, exp_jpeg_quality)

    @parameterized.expand(
        [
            # width         height          # result size
            [640, 480, (640, 480)],
            [1024, 768, (1024, 768)],
            [1600, 1200, (1600, 1200)],
            [1920, 1080, (1920, 1080)],
            [1920, 1200, (1920, 1200)],
            [3840, 2160, (3840, 2160)],
            [0, 0, (3840, 2160)],
            [-1, 5, (3840, 2160)],
            [641, 480, (3840, 2160)],
            [640, 489, (3840, 2160)],
        ]
    )
    def test__get_config_background_img_size__corrects_to_correct_size(
        self, cnf_width: int, cnf_height: int, exp_size: Tuple[int, int]
    ) -> None:
        """test__get_config_background_img_size__corrects_to_correct_size.

        Args:
            cnf_width (int): config width
            cnf_height (int): config height
            exp_size (Tuple[int, int]): expected size
        """
        with patch.dict(
            config.bwp_config, {"desktop_img": {"width": cnf_width, "height": cnf_height}}
        ):
            act_size = bingwallpaper.get_config_background_img_size()
        self.assertEqual(act_size, exp_size)


if __name__ == "__main__":
    unittest.main()

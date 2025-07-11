"""Unit tests for bingwallpaper.py."""

# Standard library imports
import datetime
import logging
import os
import platform
import sys
import tempfile
import time
import unittest
import warnings
from argparse import Namespace
from collections import namedtuple
from pathlib import Path
from unittest import mock
from xmlrpc.client import ResponseError

# Third party imports
from parameterized import parameterized
from PIL import Image
from requests import Response

# Own modules imports
from abk_bwp import abk_common, bingwallpaper, config
from abk_bwp.db import SQL_DELETE_OLD_DATA, SQL_SELECT_EXISTING, DBColumns, DbEntry


# =============================================================================
# Single functions in bingwallpaper.py
# =============================================================================
class TestBingwallpaper(unittest.TestCase):
    """Test BingWallPaper."""

    mut = None

    def setUp(self) -> None:
        """Set up."""
        self.maxDiff = None
        bingwallpaper.get_config_img_dir.cache_clear()
        bingwallpaper.normalize_jpg_quality.cache_clear()
        bingwallpaper.get_config_img_region.cache_clear()
        bingwallpaper.get_config_bing_img_region.cache_clear()
        bingwallpaper.is_config_ftv_enabled.cache_clear()
        bingwallpaper.get_relative_img_dir.cache_clear()
        bingwallpaper.get_config_store_jpg_quality.cache_clear()
        bingwallpaper.get_config_desktop_jpg_quality.cache_clear()
        bingwallpaper.get_config_ftv_jpg_quality.cache_clear()
        bingwallpaper.get_config_ftv_data.cache_clear()
        bingwallpaper.get_full_img_dir_from_date.cache_clear()
        bingwallpaper.get_config_background_img_size.cache_clear()
        bingwallpaper.is_config_desktop_img_enabled.cache_clear()
        return super().setUp()

    # -------------------------------------------------------------------------
    # get_config_img_dir
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.abk_common.ensure_dir")
    @mock.patch("abk_bwp.config.bwp_config", new_callable=dict)
    @mock.patch("abk_bwp.abk_common.get_home_dir")
    def test_get_config_img_dir_default(self, mock_home_dir, mock_bwp_config, mock_ensure_dir):
        """Test test_get_config_img_dir_default."""
        mock_home_dir.return_value = str(Path.home())  # cross-platform home path
        mock_bwp_config[bingwallpaper.ROOT_KW.IMAGE_DIR.value] = bingwallpaper.BWP_DEFAULT_PIX_DIR
        expected_dir = os.path.join(mock_home_dir.return_value, bingwallpaper.BWP_DEFAULT_PIX_DIR)

        result = bingwallpaper.get_config_img_dir()

        self.assertEqual(result, expected_dir)
        mock_ensure_dir.assert_called_once_with(expected_dir)

    # -------------------------------------------------------------------------
    # get_config_img_region
    # -------------------------------------------------------------------------
    @parameterized.expand([["notValidReg", "bing"], ["notValidReg", "peapix"], ["NotValidReg", "NotValidService"]])
    def test__get_img_region__given_an_invalid_setting_returns_default_region(self, img_region: str, img_dl_service: str) -> None:
        """test__get_img_region__given_an_invalid_setting_returns_default_region.

        Args:
            img_region (str): image region
            img_dl_service (str): image download service
        """
        exp_region = "us"
        with mock.patch.dict(config.bwp_config, {"region": img_region, "dl_service": img_dl_service}):
            act_region = bingwallpaper.get_config_img_region()
        self.assertEqual(act_region, exp_region)

    # -------------------------------------------------------------------------
    # get_full_img_dir_from_file_name
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_relative_img_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_date_from_img_file_name")
    def test_get_full_img_dir_from_file_name(self, mock_get_date, mock_get_config_dir, mock_get_relative_dir):
        """Test get_full_img_dir_from_file_name returns correct path."""
        mock_get_date.return_value = datetime.date(2025, 5, 24)
        mock_get_config_dir.return_value = os.path.join("C:", os.sep, "Users", "runneradmin", "Pictures", "BingWallpapers")
        mock_get_relative_dir.return_value = os.path.join("2025", "05", "24")
        expected_path = os.path.join(mock_get_config_dir.return_value, mock_get_relative_dir.return_value)

        result = bingwallpaper.get_full_img_dir_from_file_name("bing_20250524.jpg")

        self.assertEqual(os.path.normpath(result), os.path.normpath(expected_path))
        mock_get_date.assert_called_once_with("bing_20250524.jpg")
        mock_get_config_dir.assert_called_once()
        mock_get_relative_dir.assert_called_once_with(mock_get_date.return_value)

    # -------------------------------------------------------------------------
    # get_date_from_img_file_name
    # -------------------------------------------------------------------------
    def test_invalid_date_format(self):
        """Test invalid data format."""
        img_file_name = "2025/05/24_some_image.jpg"
        result = bingwallpaper.get_date_from_img_file_name(img_file_name)
        self.assertIsNone(result)

    def test_missing_date(self):
        """Test missing date."""
        img_file_name = "some_image.jpg"
        result = bingwallpaper.get_date_from_img_file_name(img_file_name)
        self.assertIsNone(result)

    def test_get_date_from_img_file_name_success(self):
        """Test test_get_date_from_img_file_name_success."""
        img_file_name = "2024-12-25_img001.jpg"
        result = bingwallpaper.get_date_from_img_file_name(img_file_name)
        self.assertEqual(result, datetime.date(2024, 12, 25))

    # -------------------------------------------------------------------------
    # get_all_background_img_names
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_date_from_img_file_name")
    @mock.patch("os.walk")
    @mock.patch("os.path.isdir")
    def test_get_all_background_img_names(self, mock_isdir, mock_walk, mock_get_date):
        """Test test_get_all_background_img_names."""
        # Arrange
        # ---------------------------------------------------------------------
        mock_isdir.return_value = True
        mock_walk.return_value = [("/mocked/path", ["subdir"], ["2025-05-25_image.jpg", "invalid_file.txt"])]

        def side_effect(filename):
            return filename == "2025-05-25_image.jpg"

        mock_get_date.side_effect = side_effect

        # Act
        # ---------------------------------------------------------------------
        result = bingwallpaper.get_all_background_img_names("/mocked/path")

        # Asserts
        # ---------------------------------------------------------------------
        self.assertEqual(result, ["2025-05-25_image.jpg"])

    @mock.patch.dict(config.bwp_config, {config.ROOT_KW.NUMBER_OF_IMAGES_TO_KEEP.value: 5})
    def test_positive_value(self):
        """Test test_positive_value."""
        result = bingwallpaper.get_config_number_of_images_to_keep()
        self.assertEqual(result, 5)

    @mock.patch.dict(config.bwp_config, {config.ROOT_KW.NUMBER_OF_IMAGES_TO_KEEP.value: -3})
    def test_negative_value(self):
        """Test test_negative_value."""
        result = bingwallpaper.get_config_number_of_images_to_keep()
        self.assertEqual(result, 0)

    @mock.patch.dict(config.bwp_config, {}, clear=True)
    def test_missing_key(self):
        """Test test_missing_key."""
        result = bingwallpaper.get_config_number_of_images_to_keep()
        self.assertEqual(result, 0)

    # -------------------------------------------------------------------------
    # get_config_img_region
    # -------------------------------------------------------------------------
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
    def test__get_img_region__given_a_valid_setting_returns_defined_region(self, img_region: str, img_dl_service: str) -> None:
        """test__get_img_region__given_a_valid_setting_returns_defined_region.

        Args:
            img_region (str): image region
            img_dl_service (str): image download service
        """
        with mock.patch.dict(config.bwp_config, {"region": img_region, "dl_service": img_dl_service}):
            act_region = bingwallpaper.get_config_img_region()
        self.assertEqual(act_region, img_region)

    # -------------------------------------------------------------------------
    # get_config_bing_img_region
    # -------------------------------------------------------------------------
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
        with mock.patch.dict(config.bwp_config, {"region": img_region, "dl_service": img_dl_service}):
            act_bing_region = bingwallpaper.get_config_bing_img_region()
        self.assertEqual(act_bing_region, exp_bing_region)

    # -------------------------------------------------------------------------
    # is_config_ftv_enabled
    # -------------------------------------------------------------------------
    @mock.patch.dict(config.bwp_config, {bingwallpaper.FTV_KW.FTV.value: {bingwallpaper.FTV_KW.ENABLED.value: True}})
    def test_ftv_enabled_true(self):
        """Test FTV enabled true."""
        self.assertTrue(bingwallpaper.is_config_ftv_enabled())

    @mock.patch.dict(config.bwp_config, {bingwallpaper.FTV_KW.FTV.value: {bingwallpaper.FTV_KW.ENABLED.value: False}})
    def test_ftv_enabled_false(self):
        """Test FTV enabled false."""
        self.assertFalse(bingwallpaper.is_config_ftv_enabled())

    @mock.patch.dict(config.bwp_config, {}, clear=True)
    def test_ftv_enabled_missing(self):
        """Test FTV enabled missing."""
        self.assertFalse(bingwallpaper.is_config_ftv_enabled())

    # -------------------------------------------------------------------------
    # get_relative_img_dir
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.is_config_ftv_enabled", return_value=True)
    def test_ftv_enabled_path(self, mock_ftv_enabled):
        """Test FTV enabled."""
        test_date = datetime.date(2024, 5, 24)
        result = bingwallpaper.get_relative_img_dir(test_date)
        self.assertEqual(os.path.normpath(result), os.path.normpath("05/24"))
        mock_ftv_enabled.assert_called_once()

    @mock.patch("abk_bwp.bingwallpaper.is_config_ftv_enabled", return_value=False)
    def test_ftv_disabled_path(self, mock_ftv_enabled):
        """Test FTV disabled."""
        test_date = datetime.date(2024, 5, 24)
        result = bingwallpaper.get_relative_img_dir(test_date)
        self.assertEqual(os.path.normpath(result), os.path.normpath("2024/05"))
        mock_ftv_enabled.assert_called_once()

    @mock.patch.dict(config.bwp_config, {"desktop_img": {"jpg_quality": 18}})
    def test_get_config_desktop_jpg_quality_little_value(self):
        """Test get_config_desktop_jpg_quality too little."""
        result = bingwallpaper.get_config_desktop_jpg_quality()
        self.assertEqual(result, bingwallpaper.BWP_RESIZE_JPG_QUALITY_MIN)

    @mock.patch.dict(config.bwp_config, {"desktop_img": {"jpg_quality": 256}})
    def test_get_config_desktop_jpg_quality_big_value(self):
        """Test get_config_desktop_jpg_quality too big."""
        result = bingwallpaper.get_config_desktop_jpg_quality()
        self.assertEqual(result, bingwallpaper.BWP_RESIZE_JPG_QUALITY_MAX)

    @mock.patch.dict(config.bwp_config, {"desktop_img": {"jpg_quality": 85}})
    def test_get_config_desktop_jpg_quality_custom_value(self):
        """Test get_config_desktop_jpg_quality setting."""
        result = bingwallpaper.get_config_desktop_jpg_quality()
        self.assertEqual(result, 85)

    # -------------------------------------------------------------------------
    # get_config_ftv_jpg_quality
    # -------------------------------------------------------------------------
    @mock.patch.dict(config.bwp_config, {"ftv": {"jpg_quality": 42}})
    def test_get_config_ftv_jpg_quality_little_value(self):
        """Test get_config_ftv_jpg_quality too little."""
        result = bingwallpaper.get_config_ftv_jpg_quality()
        self.assertEqual(result, bingwallpaper.BWP_RESIZE_JPG_QUALITY_MIN)

    @mock.patch.dict(config.bwp_config, {"ftv": {"jpg_quality": 181}})
    def test_get_config_ftv_jpg_quality_big_value(self):
        """Test get_config_ftv_jpg_quality too big."""
        result = bingwallpaper.get_config_ftv_jpg_quality()
        self.assertEqual(result, bingwallpaper.BWP_RESIZE_JPG_QUALITY_MAX)

    @mock.patch.dict(config.bwp_config, {"ftv": {"jpg_quality": 89}})
    def test_get_config_ftv_jpg_quality_custom_value(self):
        """Test get_config_ftv_jpg_quality setting."""
        result = bingwallpaper.get_config_ftv_jpg_quality()
        self.assertEqual(result, 89)

    # -------------------------------------------------------------------------
    # get_config_ftv_data
    # -------------------------------------------------------------------------
    @mock.patch.dict(config.bwp_config, {"ftv": {"ftv_data": "custom_ftv_data.json"}})
    def test_get_config_ftv_data_custom(self):
        """Should return the custom Frame TV data file name."""
        result = bingwallpaper.get_config_ftv_data()
        self.assertEqual(result, "custom_ftv_data.json")

    @mock.patch.dict(config.bwp_config, {}, clear=True)
    def test_get_config_ftv_data_default(self):
        """Should return the default Frame TV data file name when not configured."""
        result = bingwallpaper.get_config_ftv_data()
        self.assertEqual(result, bingwallpaper.BWP_FTV_DATA_FILE_DEFAULT)

    # -------------------------------------------------------------------------
    # delete_files_in_dir
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.os.remove")
    def test_delete_files_successfully(self, mock_remove):
        """Test all files are attempted to be removed successfully."""
        test_dir = "/tmp/test"
        test_files = ["a.txt", "b.txt"]

        bingwallpaper.delete_files_in_dir(test_dir, test_files)

        expected_calls = [mock.call(os.path.join(test_dir, f)) for f in test_files]
        mock_remove.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(mock_remove.call_count, 2)

    @mock.patch("abk_bwp.bingwallpaper.os.remove", side_effect=OSError("Mock error"))
    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    def test_delete_files_logs_error_on_exception(self, mock_resolve, mock_remove):
        """Test test_delete_files_logs_error_on_exception."""
        mock_logger = mock.Mock()
        mock_resolve.return_value = mock_logger

        test_dir = "/tmp/test"
        test_files = ["x.txt"]

        bingwallpaper.delete_files_in_dir(test_dir, test_files)

        mock_logger.exception.assert_called_once()
        msg = mock_logger.exception.call_args[0][0]
        self.assertIn("ERROR", msg)
        self.assertIn("x.txt", msg)
        mock_remove.assert_called_once_with(os.path.join(test_dir, "x.txt"))

    # -------------------------------------------------------------------------
    # get_full_img_dir_from_date
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_relative_img_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir")
    def test_get_full_img_dir_from_date(self, mock_get_config_img_dir, mock_get_relative_img_dir):
        """Test test_get_full_img_dir_from_date."""
        mock_get_config_img_dir.return_value = "/tmp/imgs"
        mock_get_relative_img_dir.return_value = "2025/05/24"
        img_date = datetime.date(2025, 5, 24)

        result = bingwallpaper.get_full_img_dir_from_date(img_date)

        self.assertEqual(os.path.normpath(result), os.path.normpath("/tmp/imgs/2025/05/24"))
        mock_get_config_img_dir.assert_called_once()
        mock_get_relative_img_dir.assert_called_once_with(img_date)

    @mock.patch("abk_bwp.bingwallpaper.get_relative_img_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir")
    def test_lru_cache_is_used(self, mock_get_config_img_dir, mock_get_relative_img_dir):
        """Test test_lru_cache_is_used."""
        mock_get_config_img_dir.return_value = "/tmp/imgs"
        mock_get_relative_img_dir.return_value = "2025/05/24"
        img_date = datetime.date(2025, 5, 24)

        result1 = bingwallpaper.get_full_img_dir_from_date(img_date)
        result2 = bingwallpaper.get_full_img_dir_from_date(img_date)

        self.assertEqual(result1, result2)
        # Should only call these once due to caching
        mock_get_config_img_dir.assert_called_once()
        mock_get_relative_img_dir.assert_called_once_with(img_date)

    # -------------------------------------------------------------------------
    # get_config_store_jpg_quality
    # -------------------------------------------------------------------------
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
        with mock.patch.dict(config.bwp_config, {"store_jpg_quality": read_jpeg_quality}):
            act_jpeg_quality = bingwallpaper.get_config_store_jpg_quality()
        self.assertEqual(act_jpeg_quality, exp_jpeg_quality)

    # -------------------------------------------------------------------------
    # get_config_background_img_size
    # -------------------------------------------------------------------------
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
        self, cnf_width: int, cnf_height: int, exp_size: tuple[int, int]
    ) -> None:
        """test__get_config_background_img_size__corrects_to_correct_size.

        Args:
            cnf_width (int): config width
            cnf_height (int): config height
            exp_size (Tuple[int, int]): expected size
        """
        with mock.patch.dict(config.bwp_config, {"desktop_img": {"width": cnf_width, "height": cnf_height}}):
            act_size = bingwallpaper.get_config_background_img_size()
        self.assertEqual(act_size, exp_size)


# =============================================================================
# DownLoadServiceBase
# =============================================================================
class TestDownLoadServiceBase(unittest.TestCase):
    """Test DownLoadServiceBase."""

    @classmethod
    def setUpClass(cls):
        """Test setup class."""
        # Suppress only reactivex warnings
        warnings.filterwarnings(
            "ignore", message="datetime.datetime.utcnow\\(\\) is deprecated", category=DeprecationWarning, module="reactivex.*"
        )

    # -------------------------------------------------------------------------
    # DownLoadServiceBase.convert_dir_structure_if_needed
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.DownLoadServiceBase._convert_to_ftv_dir_structure")
    @mock.patch("abk_bwp.bingwallpaper.is_config_ftv_enabled", return_value=True)
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value="/mocked/path")
    @mock.patch("os.walk")
    def test_convert_to_ftv_structure(self, mock_walk, mock_get_config_img_dir, mock_is_config_ftv_enabled, mock_convert_to_ftv):
        """Test convert_dir_structure_if_needed with FTV enabled."""
        # Simulate os.walk returning an iterator with a single tuple
        mock_walk.return_value = iter([("/mocked/path", ["2021", "2022"], [])])

        bingwallpaper.DownLoadServiceBase.convert_dir_structure_if_needed()

        mock_convert_to_ftv.assert_called_once_with("/mocked/path", ["2021", "2022"])
        mock_get_config_img_dir.assert_called_once()
        mock_is_config_ftv_enabled.assert_called_once()

    @mock.patch("abk_bwp.bingwallpaper.DownLoadServiceBase._convert_to_date_dir_structure")
    @mock.patch("abk_bwp.bingwallpaper.is_config_ftv_enabled", return_value=False)
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value="/mocked/path")
    @mock.patch("os.walk")
    def test_convert_to_date_structure(
        self, mock_walk, mock_get_config_img_dir, mock_is_config_ftv_enabled, mock_convert_to_date
    ):
        """Test test_convert_to_date_structure."""
        # Simulate os.walk returning a directory with month-named subdirectories
        mock_walk.return_value = iter([("/mocked/path", ["01", "02"], [])])

        bingwallpaper.DownLoadServiceBase.convert_dir_structure_if_needed()

        mock_convert_to_date.assert_called_once_with("/mocked/path", ["01", "02"])
        mock_get_config_img_dir.assert_called_once()
        mock_is_config_ftv_enabled.assert_called_once()

    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value="/mocked/path")
    @mock.patch("os.walk")
    def test_empty_directory_creates_warning_file(self, mock_walk, mock_get_config_img_dir, mock_open):
        """Test test_empty_directory_creates_warning_file."""
        # Simulate os.walk returning an empty directory
        mock_walk.return_value = iter([("/mocked/path", [], [])])

        bingwallpaper.DownLoadServiceBase.convert_dir_structure_if_needed()

        mock_open.assert_called_once_with(
            "/mocked/path/Please_do_not_modify_anything_in_this_directory.Handled_by_BingWallpaper_automagic",
            "a",
            encoding="utf-8",
        )
        mock_get_config_img_dir.assert_called_once()

    # -------------------------------------------------------------------------
    # DownLoadServiceBase._convert_to_ftv_dir_structure
    # -------------------------------------------------------------------------
    @mock.patch("shutil.rmtree")
    @mock.patch("os.renames")
    @mock.patch("os.walk")
    @mock.patch.dict(config.bwp_config, {"alt_peapix_region": ["us"]})
    def test_convert_to_ftv_dir_structure(self, mock_os_walk, mock_os_renames, mock_shutil_rmtree):
        """Test test_convert_to_ftv_dir_structure."""
        root_image_dir = "/mocked/path"
        year_list = ["2021"]
        month_list = ["01"]
        image_files = ["2021-01-01_us.jpg"]
        # Mock os.walk to simulate directory structure

        def os_walk_side_effect(path):
            if path == os.path.join(root_image_dir, "2021"):
                return iter([(path, month_list, [])])
            elif path == os.path.join(root_image_dir, "2021", "01"):
                return iter([(path, [], image_files)])
            else:
                return iter([])

        mock_os_walk.side_effect = os_walk_side_effect

        bingwallpaper.DownLoadServiceBase._convert_to_ftv_dir_structure(root_image_dir, year_list)

        expected_src = os.path.join(root_image_dir, "2021", "01", "2021-01-01_us.jpg")
        expected_dst = os.path.join(root_image_dir, "01", "01", "2021-01-01_us.jpg")
        mock_os_renames.assert_called_once_with(expected_src, expected_dst)
        mock_shutil_rmtree.assert_called_once_with(os.path.join(root_image_dir, "2021"), ignore_errors=True)

    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    @mock.patch("shutil.rmtree")
    @mock.patch("os.renames", side_effect=OSError("Simulated error during renaming"))
    @mock.patch("os.walk")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"alt_peapix_region": ["us"]})
    def test_convert_to_ftv_dir_structure_exception(self, mock_os_walk, mock_os_renames, mock_shutil_rmtree, mock_logger_resolve):
        """Test exception handling in _convert_to_ftv_dir_structure."""
        # Set up a dummy logger for lazy resolution.
        dummy_logger = mock.Mock()
        mock_logger_resolve.return_value = dummy_logger
        root_image_dir = "/mocked/path"
        year_list = ["2021"]
        month_list = ["01"]
        image_files = ["2021-01-01_us.jpg"]
        # Simulate os.walk returning an iterator (not a list) for the given paths.

        def os_walk_side_effect(path):
            if path == os.path.join(root_image_dir, "2021"):
                return iter([(path, month_list, [])])
            elif path == os.path.join(root_image_dir, "2021", "01"):
                return iter([(path, [], image_files)])
            else:
                return iter([])

        mock_os_walk.side_effect = os_walk_side_effect

        # Call the method and assert that an OSError is raised.
        with self.assertRaises(OSError) as cm:
            bingwallpaper.DownLoadServiceBase._convert_to_ftv_dir_structure(root_image_dir, year_list)

        self.assertIn("Simulated error during renaming", str(cm.exception))
        # Assert that our dummy logger’s error method was called.
        self.assertTrue(dummy_logger.error.called)
        # Optionally, check that rmtree is not called because the exception stops processing.
        mock_shutil_rmtree.assert_not_called()
        mock_os_renames.assert_called_once()

    # -------------------------------------------------------------------------
    # DownLoadServiceBase._convert_to_date_dir_structure
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    @mock.patch("shutil.rmtree")
    @mock.patch("os.renames")
    @mock.patch("os.walk")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"alt_peapix_region": ["us"]})
    def test_convert_to_date_dir_structure(self, mock_os_walk, mock_os_renames, mock_shutil_rmtree, mock_logger):
        """Test test_convert_to_date_dir_structure."""
        root_image_dir = "/mocked/path"
        month_list = ["01"]
        day_list = ["01"]
        image_files = ["2021-01-01_us.jpg"]

        # Define side effects for os.walk
        def os_walk_side_effect(path):
            if path == os.path.join(root_image_dir, "01"):
                return iter([(path, day_list, [])])
            elif path == os.path.join(root_image_dir, "01", "01"):
                return iter([(path, [], image_files)])
            else:
                return iter([])

        mock_os_walk.side_effect = os_walk_side_effect

        # Call the method under test
        bingwallpaper.DownLoadServiceBase._convert_to_date_dir_structure(root_image_dir, month_list)

        expected_src = os.path.join(root_image_dir, "01", "01", "2021-01-01_us.jpg")
        expected_dst = os.path.join(root_image_dir, "2021", "01", "2021-01-01_us.jpg")
        mock_os_renames.assert_called_once_with(expected_src, expected_dst)
        mock_shutil_rmtree.assert_called_once_with(os.path.join(root_image_dir, "01"), ignore_errors=True)

    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    @mock.patch("shutil.rmtree")
    @mock.patch("os.renames", side_effect=OSError("Simulated error during renaming"))
    @mock.patch("os.walk")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"alt_peapix_region": ["us"]})
    def test_convert_to_date_dir_structure_exception(self, mock_os_walk, mock_os_renames, mock_shutil_rmtree, mock_logger):
        """Test test_convert_to_date_dir_structure_exception."""
        root_image_dir = "/mocked/path"
        month_list = ["01"]
        day_list = ["01"]
        image_files = ["2021-01-01_us.jpg"]

        # Define side effects for os.walk
        def os_walk_side_effect(path):
            if path == os.path.join(root_image_dir, "01"):
                return iter([(path, day_list, [])])
            elif path == os.path.join(root_image_dir, "01", "01"):
                return iter([(path, [], image_files)])
            else:
                return iter([])

        mock_os_walk.side_effect = os_walk_side_effect

        # Call the method under test and assert that it raises an exception
        with self.assertRaises(OSError):
            bingwallpaper.DownLoadServiceBase._convert_to_date_dir_structure(root_image_dir, month_list)

    # -------------------------------------------------------------------------
    # DownLoadServiceBase._download_images
    # -------------------------------------------------------------------------
    @mock.patch.object(bingwallpaper.BingDownloadService, "_process_and_download_image")
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_download_images_success(self, mock_get_logger, mock_process_image):
        """Test test_download_images_success."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup image data list
        img_data_list = [
            bingwallpaper.ImageDownloadData(datetime.date(2025, 1, 2), b"title2", b"copy2", ["url2"], "img/path", "img2.jpg"),
            bingwallpaper.ImageDownloadData(datetime.date(2025, 1, 1), b"title1", b"copy1", ["url1"], "img/path", "img1.jpg"),
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        service._download_images(img_data_list)
        time.sleep(1)  # Wait briefly for threads to complete

        # Asserts
        # ----------------------------------
        # Each image should be processed
        self.assertEqual(mock_process_image.call_count, len(img_data_list))
        # Logs should show progress and completion
        mock_logger.info.assert_any_call("Downloaded 1 / 2 images")
        mock_logger.info.assert_any_call("Downloaded 2 / 2 images")
        mock_logger.info.assert_any_call("✅ All image downloads completed.")

    @mock.patch.object(bingwallpaper.BingDownloadService, "_process_and_download_image")
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_download_images_with_retry_success(self, mock_get_logger, mock_process_image):
        """Test test_download_images_with_retry_success."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # First call for img1 raises an exception twice, then succeeds
        side_effects = [Exception("fail"), Exception("fail"), None]
        mock_process_image.side_effect = side_effects + [None]  # img2 succeeds immediately
        # Setup image data list
        img_data_list = [
            bingwallpaper.ImageDownloadData(datetime.date(2025, 1, 2), b"title2", b"copy2", ["url2"], "img/path", "img2.jpg"),
            bingwallpaper.ImageDownloadData(datetime.date(2025, 1, 1), b"title1", b"copy1", ["url1"], "img/path", "img1.jpg"),
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        service._download_images(img_data_list)
        time.sleep(2)  # Wait briefly for threads to complete

        # Asserts
        # ----------------------------------
        self.assertEqual(mock_process_image.call_count, 4)  # 3 (retries) + 1 (img2)
        mock_logger.info.assert_any_call("✅ All image downloads completed.")

    @mock.patch.object(
        bingwallpaper.BingDownloadService, "_process_and_download_image", side_effect=Exception("permanent failure")
    )
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_download_images_failure_after_retries(self, mock_get_logger, mock_process_image):
        """Test test_download_images_failure_after_retries."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup image data list
        img_data_list = [
            bingwallpaper.ImageDownloadData(
                datetime.date(2025, 1, 1), b"title1", b"copy1", ["url1"], os.path.join("img", "path"), "img1.jpg"
            )
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        service._download_images(img_data_list)
        time.sleep(2)  # Wait briefly for threads to complete

        # Asserts
        # ----------------------------------
        # Called 3 times due to retries
        self.assertEqual(mock_process_image.call_count, 3)
        mock_logger.warning.assert_called_with(mock.ANY)

    # -------------------------------------------------------------------------
    # DownLoadServiceBase._process_and_download_image
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_config_store_jpg_quality", return_value=85)
    @mock.patch("PIL.Image.open")
    @mock.patch("requests.get")
    @mock.patch("abk_bwp.abk_common.ensure_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_file_name", return_value=os.path.join("mocked", "path"))
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_process_and_download_image_success(
        self, mock_get_logger, mock_get_path, mock_ensure_dir, mock_requests_get, mock_image_open, mock_get_quality
    ):
        """Test test_process_and_download_image_success."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup mock image and response
        mock_image = mock.MagicMock()
        mock_image.resize.return_value = mock_image
        mock_image.getexif.return_value = {}
        mock_image.save = mock.MagicMock()
        mock_image_open.return_value.__enter__.return_value = mock_image
        # Setup request mock
        mock_response = mock.Mock(status_code=200, content=b"fake_image_data")
        mock_requests_get.return_value = mock_response
        # Prepare image data
        image_data = bingwallpaper.ImageDownloadData(
            imageDate=datetime.date.today(),
            title=b"My Title",
            copyright=b"My Copyright",
            imageUrl=["http://example.com/image.jpg"],
            imagePath=os.path.join("mocked", "path"),
            imageName="test.jpg",
        )

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        service._process_and_download_image(image_data)

        # Asserts
        # ----------------------------------
        mock_get_path.assert_called_once_with("test.jpg")
        mock_ensure_dir.assert_called_once_with(os.path.join("mocked", "path"))
        mock_requests_get.assert_called_once_with("http://example.com/image.jpg", stream=True, timeout=mock.ANY)
        mock_image_open.assert_called_once()
        mock_image.resize.assert_called_once_with(bingwallpaper.BWP_DEFAULT_IMG_SIZE, Image.Resampling.LANCZOS)
        mock_get_quality.assert_called_once()
        mock_image.save.assert_called_once()
        mock_logger.exception.assert_not_called()

    @mock.patch("abk_bwp.bingwallpaper.get_config_store_jpg_quality", return_value=85)
    @mock.patch("PIL.Image.open")
    @mock.patch("requests.get", return_value=mock.Mock(status_code=404))
    @mock.patch("abk_bwp.abk_common.ensure_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_file_name", return_value=os.path.join("mocked", "path"))
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_process_and_download_image_http_error(
        self, mock_get_logger, mock_get_path, mock_ensure_dir, mock_requests_get, mock_image_open, mock_get_quality
    ):
        """Test image download error."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # setup image data
        image_data = bingwallpaper.ImageDownloadData(
            imageDate=datetime.date.today(),
            title=b"",
            copyright=b"",
            imageUrl=["http://example.com/bad.jpg"],
            imagePath=os.path.join("mocked", "path"),
            imageName="test.jpg",
        )

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        service._process_and_download_image(image_data)

        # Assert
        # ----------------------------------
        mock_get_path.assert_called_once_with("test.jpg")
        mock_ensure_dir.assert_called_once_with(os.path.join("mocked", "path"))
        mock_requests_get.assert_called_once()
        mock_image_open.assert_not_called()
        mock_get_quality.assert_not_called()
        mock_logger.exception.assert_not_called()  # No exception, just skipped save

    @mock.patch("abk_bwp.bingwallpaper.get_config_store_jpg_quality", return_value=85)
    @mock.patch("PIL.Image.open", side_effect=Exception("Image error"))
    @mock.patch("requests.get")
    @mock.patch("abk_bwp.abk_common.ensure_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_file_name", return_value=os.path.join("mocked", "path"))
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_process_and_download_image_raises_exception(
        self, mock_get_logger, mock_get_path, mock_ensure_dir, mock_requests_get, mock_image_open, mock_get_quality
    ):
        """Test test_process_and_download_image_raises_exception."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup request mock
        mock_response = mock.Mock(status_code=200, content=b"bad_data")
        mock_requests_get.return_value = mock_response
        # Setup image data
        image_data = bingwallpaper.ImageDownloadData(
            imageDate=datetime.date.today(),
            title=b"",
            copyright=b"",
            imageUrl=["http://example.com/corrupt.jpg"],
            imagePath=os.path.join("mocked", "path"),
            imageName="test.jpg",
        )

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        service._process_and_download_image(image_data)

        # Assert
        # ----------------------------------
        mock_get_path.assert_called_once_with("test.jpg")
        mock_ensure_dir.assert_called_once_with(os.path.join("mocked", "path"))
        mock_requests_get.assert_called_once()
        mock_requests_get.assert_called_once_with(
            "http://example.com/corrupt.jpg", stream=True, timeout=bingwallpaper.BWP_REQUEST_TIMEOUT
        )
        mock_image_open.assert_called_once()
        mock_get_quality.assert_not_called()
        expected_path = os.path.join("mocked", "path", "test.jpg")
        mock_logger.exception.assert_called_once_with(f"ERROR: exp=Exception('Image error'), downloading image: {expected_path}")


# =============================================================================
# BingDownloadService
# =============================================================================
class TestBingDownloadService(unittest.TestCase):
    """Test BingDownloadService."""

    # -------------------------------------------------------------------------
    # BingDownloadService.download_new_images
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    @mock.patch("requests.get")
    @mock.patch.object(bingwallpaper.BingDownloadService, "_download_images")
    def test_download_new_images_success(self, mock_download_images, mock_requests_get, mock_get_logger):
        """Test test_download_new_images_success."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup mock response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "images": [{"startdate": "20250525", "title": "Sample Image", "copyright": "Sample Copyright", "url": "/sample.jpg"}]
        }
        mock_requests_get.return_value = mock_response

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        service.download_new_images()

        # Asserts
        # ----------------------------------
        mock_requests_get.assert_called_once()
        mock_download_images.assert_called_once()

    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    @mock.patch("requests.get")
    def test_download_new_images_non_200_response(self, mock_requests_get, mock_get_logger):
        """Test test_download_new_images_non_200_response."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup mock response
        mock_response = mock.Mock()
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response

        # Act
        # Asserts
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        with self.assertRaises(ResponseError):
            service.download_new_images()

    # -------------------------------------------------------------------------
    # BingDownloadService._process_bing_api_data
    # -------------------------------------------------------------------------
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date", return_value=os.path.join("mocked", "path"))
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="en-US")
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value=os.path.join("mock", "imgdir"))
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_process_valid_metadata_image_not_exists(
        self, mock_get_logger, mock_get_img_dir, mock_get_region, mock_get_full_path, mock_exists
    ):
        """Test test_process_valid_metadata_image_not_exists."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger

        metadata_list = [{"startdate": "20250102", "copyright": "Test Image", "urlbase": "/testimage"}]

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        result = service._process_bing_api_data(metadata_list)

        # Assert
        # ----------------------------------
        self.assertEqual(len(result), 1)
        image_data = result[0]
        self.assertIsInstance(image_data, bingwallpaper.ImageDownloadData)
        self.assertEqual(image_data.imageDate, datetime.date(2025, 1, 2))
        self.assertIn("/testimage", image_data.imageUrl[0])
        self.assertEqual(image_data.imagePath, os.path.join("mocked", "path"))
        self.assertEqual(image_data.imageName, "2025-01-02_en-US.jpg")
        mock_logger.debug.assert_any_call("Number if images to download: 1")
        mock_get_img_dir.assert_called_once_with()
        mock_get_region.assert_called_once_with()
        mock_get_full_path.assert_called_once_with(datetime.date(2025, 1, 2))
        mock_exists.assert_called_once_with(os.path.join("mocked", "path", "2025-01-02_en-US.jpg"))

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date", return_value=os.path.join("mocked", "path"))
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="en-US")
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value=os.path.join("mock", "imgdir"))
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_process_image_already_exists(
        self, mock_get_logger, mock_get_img_dir, mock_get_region, mock_get_full_path, mock_exists
    ):
        """Test test_process_image_already_exists."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup Metadata list
        metadata_list = [{"startdate": "20250102", "copyright": "Test Image", "urlbase": "/testimage"}]

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        result = service._process_bing_api_data(metadata_list)

        # Assert
        # ----------------------------------
        self.assertEqual(result, [])  # should not return anything if already exists
        mock_logger.debug.assert_any_call("Number if images to download: 0")
        mock_get_img_dir.assert_called_once_with()
        mock_get_region.assert_called_once_with()
        mock_get_full_path.assert_called_once_with(datetime.date(2025, 1, 2))
        mock_exists.assert_called_once_with(os.path.join("mocked", "path", "2025-01-02_en-US.jpg"))

    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date", return_value=os.path.join("mocked", "path"))
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="en-US")
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value=os.path.join("mock", "imgdir"))
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_process_invalid_metadata_logs_exception(
        self, mock_get_logger, mock_get_img_dir, mock_get_region, mock_get_full_path, mock_exists
    ):
        """Test test_process_invalid_metadata_logs_exception."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Malformed date should raise in datetime.strptime
        metadata_list = [{"startdate": "not-a-date", "copyright": "Test Image", "urlbase": "/testimage"}]

        service = bingwallpaper.BingDownloadService(dl_logger=mock_logger)
        result = service._process_bing_api_data(metadata_list)

        self.assertEqual(result, [])
        mock_logger.exception.assert_called_once()
        mock_logger.debug.assert_any_call("Number if images to download: 0")
        mock_get_img_dir.assert_called_once_with()
        mock_get_region.assert_called_once_with()
        mock_get_full_path.assert_not_called()
        mock_exists.assert_not_called()


# =============================================================================
# PeapixDownloadService
# =============================================================================
class TestPeapixDownloadService(unittest.TestCase):
    """Test PeapixDownloadService."""

    # -------------------------------------------------------------------------
    # PeapixDownloadService.download_new_images
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value=os.path.join("mock", "dir"))
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"CONSTANT": {"PEAPIX_URL": "https://api.peapix.com"}, "REGION": "us"})
    @mock.patch("requests.get")
    @mock.patch.object(bingwallpaper.PeapixDownloadService, "_add_date_to_peapix_data")
    @mock.patch.object(bingwallpaper.PeapixDownloadService, "_process_image_data")
    @mock.patch.object(bingwallpaper.PeapixDownloadService, "_download_images")
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_download_new_images_success(
        self, mock_get_logger, mock_download, mock_process, mock_add_date, mock_requests_get, mock_img_dir
    ):
        """Test test_download_new_images_success."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup request response
        fake_response = mock.MagicMock(spec=Response)
        fake_response.status_code = 200
        fake_response.json.return_value = {"data": "mocked"}
        mock_requests_get.return_value = fake_response
        mock_add_date.return_value = [{"pageUrl": "123456", "date": "2025-05-31"}]
        mock_process.return_value = ["image1", "image2"]

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        service.download_new_images()

        # Assert
        # ----------------------------------
        mock_img_dir.assert_called_once_with()
        mock_requests_get.assert_called_once()
        mock_add_date.assert_called_once_with({"data": "mocked"}, "us")
        mock_process.assert_called_once_with([{"pageUrl": "123456", "date": "2025-05-31"}])
        mock_download.assert_called_once_with(["image1", "image2"])
        mock_logger.debug.assert_any_call("Getting Image info from: get_metadata_url='https://peapix.com/bing/feed?country=us'")

    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value=os.path.join("mock", "dir"))
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"CONSTANT": {"PEAPIX_URL": "https://api.peapix.com"}, "REGION": "us"})
    @mock.patch("requests.get")
    @mock.patch.object(bingwallpaper.PeapixDownloadService, "_add_date_to_peapix_data")
    @mock.patch.object(bingwallpaper.PeapixDownloadService, "_process_image_data")
    @mock.patch.object(bingwallpaper.PeapixDownloadService, "_download_images")
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_download_new_images_http_error(
        self, mock_get_logger, mock_download, mock_process, mock_add_date, mock_requests_get, mock_img_dir
    ):
        """Test test_download_new_images_success."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup request response
        fake_response = mock.MagicMock(spec=Response)
        fake_response.status_code = 500
        mock_requests_get.return_value = fake_response

        # Act + Assert
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        with self.assertRaises(ResponseError) as cm:
            service.download_new_images()

        self.assertIn("ERROR: getting bing image return error code: 500", str(cm.exception))
        mock_img_dir.assert_called_once()
        mock_requests_get.assert_called_once()
        mock_add_date.assert_not_called()
        mock_process.assert_not_called()
        mock_download.assert_not_called()

    # -------------------------------------------------------------------------
    # PeapixDownloadService._process_image_data
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="EN-US")
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date", return_value=os.path.join("mocked", "path"))
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_returns_images_to_download(self, mock_get_logger, mock_exists, mock_get_dir, mock_get_region):
        """Test test_returns_images_to_download."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        metadata = [
            {
                "date": "2025-05-25",
                "title": "Sunset",
                "copyright": "MyPhoto",
                "imageUrl": "url1",
                "fullUrl": "url2",
                "thumbUrl": "url3",
            }
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        result = service._process_image_data(metadata)

        # Asserts
        # ----------------------------------
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], bingwallpaper.ImageDownloadData)
        self.assertEqual(result[0].imageDate, datetime.date(2025, 5, 25))
        self.assertEqual(result[0].imageName, "2025-05-25_EN-US.jpg")
        mock_exists.assert_called_once_with(os.path.join("mocked", "path", "2025-05-25_EN-US.jpg"))
        mock_get_dir.assert_called_once_with(datetime.date(2025, 5, 25))
        mock_get_region.assert_called_once()

    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="EN-US")
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date", return_value=os.path.join("mocked", "path"))
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_skips_existing_images(self, mock_get_logger, mock_exists, mock_get_dir, mock_get_region):
        """Test test_skips_existing_images."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup metadata
        metadata = [
            {"date": "2025-05-25", "title": "Already Exists", "copyright": "", "imageUrl": "", "fullUrl": "", "thumbUrl": ""}
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        result = service._process_image_data(metadata)

        # Asserts
        # ----------------------------------
        self.assertEqual(result, [])
        mock_exists.assert_called_once_with(os.path.join("mocked", "path", "2025-05-25_EN-US.jpg"))
        mock_get_dir.assert_called_once_with(datetime.date(2025, 5, 25))
        mock_get_region.assert_called_once()

    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="EN-US")
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date", return_value=os.path.join("mocked", "path"))
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_handles_invalid_date(self, mock_get_logger, mock_exists, mock_get_dir, mock_get_region):
        """Test test_handles_invalid_date."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        bad_metadata = [{"date": "not-a-date", "title": "Invalid Date", "imageUrl": "", "fullUrl": "", "thumbUrl": ""}]

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        result = service._process_image_data(bad_metadata)

        # Asserts
        # ----------------------------------
        self.assertEqual(result, [])
        mock_logger.exception.assert_called_once()
        mock_exists.assert_not_called()
        mock_get_dir.assert_not_called()
        mock_get_region.assert_called_once()

    # -------------------------------------------------------------------------
    # PeapixDownloadService._extract_image_id
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_extract_image_id_success(self, mock_get_logger):
        """Test test_extract_image_id_success."""
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        url = "https://example.com/bing/12345/"

        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        result = service._extract_image_id(url)

        self.assertEqual(result, 12345)

    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_extract_image_id_success_no_trailing_slash(self, mock_get_logger):
        """Test test_extract_image_id_success_no_trailing_slash."""
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        url = "https://example.com/bing/67890"

        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        result = service._extract_image_id(url)

        self.assertEqual(result, 67890)

    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_extract_image_id_failure(self, mock_get_logger):
        """Test test_extract_image_id_failure."""
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        url = "https://example.com/no-bing-here/abc"

        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        with self.assertRaises(ValueError) as context:
            service._extract_image_id(url)

        self.assertIn("Invalid page URL format", str(context.exception))

    # -------------------------------------------------------------------------
    # PeapixDownloadService._db_get_existing_data
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.db_sqlite_cursor")
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_db_get_existing_data(self, mock_get_logger, mock_cursor_ctx_mgr):
        """Test test_db_get_existing_data."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Mock cursor object
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchall.return_value = [(1001, "us", "2024-01-01"), (1002, "jp", "2024-01-02")]
        # Set the context manager return value
        mock_cursor_ctx_mgr.return_value.__enter__.return_value = mock_cursor
        mock_conn = mock.MagicMock()

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        result = service._db_get_existing_data(mock_conn)

        # Assert
        # ----------------------------------
        expected = {1001: {"country": "us", "date": "2024-01-01"}, 1002: {"country": "jp", "date": "2024-01-02"}}
        self.assertEqual(result, expected)
        mock_cursor.execute.assert_called_once_with(SQL_SELECT_EXISTING)
        mock_cursor.fetchall.assert_called_once()

    # -------------------------------------------------------------------------
    # PeapixDownloadService._db_insert_metadata
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.db_sqlite_cursor")
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_db_insert_metadata(self, mock_get_logger, mock_cursor_ctx_mgr):
        """Test test_db_insert_metadata."""
        # Arrange
        # ----------------------------------
        # mock logger
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # mock cursor
        mock_cursor = mock.MagicMock()
        mock_cursor_ctx_mgr.return_value.__enter__.return_value = mock_cursor
        mock_conn = mock.MagicMock()
        entries: list[DbEntry] = [
            {
                DBColumns.PAGE_ID.value: 1001,
                DBColumns.COUNTRY.value: "us",
                DBColumns.DATE.value: "2024-01-01",
                DBColumns.PAGE_URL.value: "https://1001",
            },
            {
                DBColumns.PAGE_ID.value: 1002,
                DBColumns.COUNTRY.value: "jp",
                DBColumns.DATE.value: "2024-01-02",
                DBColumns.PAGE_URL.value: "https://1002",
            },
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        service._db_insert_metadata(mock_conn, entries)

        # Assert
        # ----------------------------------
        expected_sql = """
            INSERT OR REPLACE INTO pages (pageId, country, date, pageUrl)
            VALUES (?, ?, ?, ?)
        """
        expected_calls = [
            mock.call(expected_sql, (1001, "us", "2024-01-01", "https://1001")),
            mock.call(expected_sql, (1002, "jp", "2024-01-02", "https://1002")),
        ]
        mock_cursor.execute.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_conn.commit.assert_called_once()

    @mock.patch("abk_bwp.bingwallpaper.db_sqlite_cursor")
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_db_insert_metadata_with_data_trim(self, mock_get_logger, mock_cursor_ctx_mgr):
        """Test test_db_insert_metadata_with_data_trim."""
        # Arrange
        # ----------------------------------
        # mock logger
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # mock cursor
        mock_cursor = mock.MagicMock()
        mock_cursor_ctx_mgr.return_value.__enter__.return_value = mock_cursor
        mock_conn = mock.MagicMock()
        entries: list[DbEntry] = [
            {
                DBColumns.PAGE_ID.value: 1001,
                DBColumns.COUNTRY.value: "us",
                DBColumns.DATE.value: "2024-01-01",
                DBColumns.PAGE_URL.value: "https://1001",
            },
            {
                DBColumns.PAGE_ID.value: 1002,
                DBColumns.COUNTRY.value: "jp",
                DBColumns.DATE.value: "2024-01-02",
                DBColumns.PAGE_URL.value: "https://1002",
            },
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        service._db_insert_metadata(mock_conn, entries, rec_to_keep=bingwallpaper.DEFAULT_NUMBER_OF_RECORDS_TO_KEEP)

        # Assert
        # ----------------------------------
        expected_sql = """
            INSERT OR REPLACE INTO pages (pageId, country, date, pageUrl)
            VALUES (?, ?, ?, ?)
        """
        expected_calls = [
            mock.call(expected_sql, (1001, "us", "2024-01-01", "https://1001")),
            mock.call(expected_sql, (1002, "jp", "2024-01-02", "https://1002")),
            mock.call(SQL_DELETE_OLD_DATA, (84,)),
        ]
        mock_cursor.execute.assert_has_calls(expected_calls)
        self.assertEqual(mock_cursor.execute.call_count, 3)
        mock_conn.commit.assert_called_once()

    # -------------------------------------------------------------------------
    # PeapixDownloadService._add_date_to_peapix_data
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.db_sqlite_connect")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"CONSTANT": {"ALT_PEAPIX_REGION": ["us", "jp"]}})
    @mock.patch("abk_bwp.bingwallpaper.str_to_date")
    @mock.patch("abk_bwp.bingwallpaper.PeapixDownloadService._db_insert_metadata")
    @mock.patch("abk_bwp.bingwallpaper.PeapixDownloadService._extract_image_id")
    @mock.patch("abk_bwp.bingwallpaper.PeapixDownloadService._db_get_existing_data")
    def test_add_date_to_peapix_data_happy_path(
        self, mock_get_existing, mock_extract_id, mock_insert, mock_str_to_date, mock_db_connect
    ):
        """Test test_add_date_to_peapix_data_happy_path."""
        # Arrange
        # ----------------------------------
        # Setup
        mock_logger = mock.MagicMock()
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        service._bwp_db_file = "mocked.db"
        # Input: image items
        img_items = [
            {DBColumns.PAGE_URL.value: "https://peapix.com/bing/1002"},
            {DBColumns.PAGE_URL.value: "https://peapix.com/bing/1001"},
        ]
        # Mocked extract_image_id
        mock_extract_id.side_effect = lambda url: int(url.split("/")[-1])
        mock_get_existing.return_value = {1000: {DBColumns.COUNTRY.value: "us", DBColumns.DATE.value: "2024-01-01"}}
        # Mock date parser
        mock_str_to_date.return_value = datetime.datetime(2024, 1, 1)
        mock_conn = mock.MagicMock()
        mock_db_connect.return_value.__enter__.return_value = mock_conn

        # Act
        # ----------------------------------
        result = service._add_date_to_peapix_data(img_items, country="us")

        # Assert
        # ----------------------------------
        self.assertEqual(len(result), 2)
        for entry in result:
            self.assertIn(DBColumns.DATE.value, entry)
            self.assertEqual(entry[DBColumns.COUNTRY.value], "us")

        mock_insert.assert_called()
        mock_get_existing.assert_called_once()
        mock_extract_id.assert_called()
        mock_str_to_date.assert_has_calls([mock.call("2024-01-01"), mock.call("2024-01-03"), mock.call("2024-01-02")])
        self.assertEqual(mock_str_to_date.call_count, 3)

    @mock.patch("abk_bwp.bingwallpaper.db_sqlite_connect")
    def test_add_date_to_peapix_data_too_few_images(self, mock_db_connect):
        """Test test_add_date_to_peapix_data_too_few_images."""
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock.MagicMock())
        service._bwp_db_file = "mocked.db"
        mock_db_connect.return_value.__enter__.return_value = mock.MagicMock()

        with self.assertRaises(RuntimeError) as ctx:
            service._add_date_to_peapix_data(img_items=[{DBColumns.PAGE_URL.value: "https://peapix.com/bing/1"}], country="us")
        self.assertIn("Only 1 image(s) provided", str(ctx.exception))

    @mock.patch("abk_bwp.bingwallpaper.db_sqlite_connect")
    @mock.patch("abk_bwp.bingwallpaper.PeapixDownloadService._db_get_existing_data")
    @mock.patch("abk_bwp.bingwallpaper.PeapixDownloadService._extract_image_id")
    def test_add_date_to_peapix_data_missing_baseline(self, mock_extract, mock_existing, mock_db_connect):
        """Test test_add_date_to_peapix_data_missing_baseline."""
        # Arrange
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock.MagicMock())
        service._bwp_db_file = "mocked.db"
        mock_extract.return_value = 1002
        mock_existing.return_value = {}  # no known entry
        mock_db_connect.return_value.__enter__.return_value = mock.MagicMock()

        # Act
        # ----------------------------------
        with self.assertRaises(RuntimeError) as ctx:
            service._add_date_to_peapix_data(
                img_items=[
                    {DBColumns.PAGE_URL.value: "https://peapix.com/bing/1002"},
                    {DBColumns.PAGE_URL.value: "https://peapix.com/bing/1001"},
                ],
                country="us",
            )

        # Assert
        # ----------------------------------
        self.assertIn("No baseline date found", str(ctx.exception))

    @mock.patch("abk_bwp.bingwallpaper.db_sqlite_connect")
    @mock.patch("abk_bwp.bingwallpaper.str_to_date")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"CONSTANT": {"ALT_PEAPIX_REGION": ["us", "jp"]}})
    @mock.patch("abk_bwp.bingwallpaper.PeapixDownloadService._extract_image_id")
    @mock.patch("abk_bwp.bingwallpaper.PeapixDownloadService._db_get_existing_data")
    @mock.patch("abk_bwp.bingwallpaper.PeapixDownloadService._db_insert_metadata")
    def test_add_date_to_peapix_data_country_count_not_even(
        self, mock_insert, mock_get_existing, mock_extract_id, mock_str_to_date, mock_db_connect
    ):
        """Test test_add_date_to_peapix_data_country_count_not_even."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.MagicMock()
        service = bingwallpaper.PeapixDownloadService(dls_logger=mock_logger)
        service._bwp_db_file = "mocked.db"
        img_items = [
            {DBColumns.PAGE_URL.value: "https://peapix.com/bing/1001"},
            {DBColumns.PAGE_URL.value: "https://peapix.com/bing/1003"},
            {DBColumns.PAGE_URL.value: "https://peapix.com/bing/1006"},
        ]
        mock_extract_id.side_effect = [1001, 1003, 1006]
        mock_get_existing.return_value = {1000: {DBColumns.COUNTRY.value: "us", DBColumns.DATE.value: "2024-01-01"}}
        mock_str_to_date.return_value = datetime.datetime(2024, 1, 1)
        mock_conn = mock.MagicMock()
        mock_db_connect.return_value.__enter__.return_value = mock_conn

        # Act
        # ----------------------------------
        result = service._add_date_to_peapix_data(img_items, country="us")

        # Assert
        # ----------------------------------
        # Should return early without generating full_data
        self.assertEqual(len(result), 3)
        mock_insert.assert_called_once()
        # This assert ensures the early return occurred
        mock_logger.debug.assert_any_call(mock.ANY)


# =============================================================================
# MacOSDependent
# =============================================================================
@unittest.skipUnless(platform.system() == "Darwin", "Only runs on macOS")
class TestMacOSDependent(unittest.TestCase):
    """Test MacOSDependent."""

    def setUp(self):
        """Test Setup MacOSDependent."""
        self.mock_logger = mock.MagicMock(spec=logging.Logger)
        self.service = bingwallpaper.MacOSDependent(macos_logger=self.mock_logger)

    # -------------------------------------------------------------------------
    # MacOSDependent.set_desktop_background
    # -------------------------------------------------------------------------
    def test_constructor_sets_os_type(self):
        """Test test_constructor_sets_os_type."""
        self.assertEqual(self.service.os_type, abk_common.OsType.MAC_OS)
        self.assertIs(self.service._logger, self.mock_logger)

    @mock.patch("subprocess.call")
    def test_set_desktop_background_calls_osascript(self, mock_subprocess_call):
        """Test test_set_desktop_background_calls_osascript."""
        # Arrange
        # ----------------------------------
        file_name = os.path.join("Users", "test", "Pictures", "image.jpg")

        # Act
        # ----------------------------------
        self.service.set_desktop_background(file_name)

        # Asserts
        # ----------------------------------
        # Check debug logging of filename
        self.mock_logger.debug.assert_any_call(f"{file_name = }")
        # Check subprocess was called with expected AppleScript
        expected_script = f"""/usr/bin/osascript<<END
tell application "Finder"
set desktop picture to POSIX file "{file_name}"
end tell
END"""
        mock_subprocess_call.assert_called_once_with(expected_script, shell=True)  # noqa: S604
        # Check info log about setting background
        self.mock_logger.info.assert_any_call(f"(MacOS) Set background to {file_name}")


# =============================================================================
# LinuxDependent
# =============================================================================
@unittest.skipUnless(sys.platform.startswith("linux"), "Linux-specific test")
class TestLinuxDependent(unittest.TestCase):
    """Test LinuxDependent."""

    def setUp(self):
        """Setup TestLinuxDependent."""
        self.mock_logger = mock.MagicMock(spec=logging.Logger)
        self.service = bingwallpaper.LinuxDependent(ld_logger=self.mock_logger)

    # -------------------------------------------------------------------------
    # LinuxDependent.__init__
    # -------------------------------------------------------------------------
    def test_constructor_sets_os_type(self):
        """Test that constructor sets os_type and logger."""
        self.assertEqual(self.service.os_type, abk_common.OsType.LINUX_OS)
        self.assertIs(self.service._logger, self.mock_logger)

    # -------------------------------------------------------------------------
    # LinuxDependent.set_desktop_background
    # -------------------------------------------------------------------------
    def test_set_desktop_background_logs_debug_and_info(self):
        """Test logging output from set_desktop_background."""
        # Arrange
        # ----------------------------------
        file_name = "/home/test/Pictures/image.jpg"

        # Act
        # ----------------------------------
        self.service.set_desktop_background(file_name)

        # Assert
        # ----------------------------------
        self.mock_logger.debug.assert_called_once_with(f"{file_name=}")
        expected_prefix = f"({self.service.os_type.value})"
        self.mock_logger.info.assert_any_call(f"{expected_prefix} Set background to {file_name}")
        self.mock_logger.info.assert_any_call(f"{expected_prefix} Not implemented yet")


# =============================================================================
# WindowsDependent
# =============================================================================
@unittest.skipUnless(sys.platform.startswith("win"), "Windows-specific test")
class TestWindowsDependent(unittest.TestCase):
    """Test WindowsDependent."""

    def setUp(self):
        """Setup WindowsDependent."""
        self.mock_logger = mock.MagicMock(spec=logging.Logger)
        self.service = bingwallpaper.WindowsDependent(logger=self.mock_logger)

    # -------------------------------------------------------------------------
    # WindowsDependent.__init__
    # -------------------------------------------------------------------------
    def test_constructor_sets_os_type(self):
        """Test that constructor sets os_type and logger."""
        self.assertEqual(self.service.os_type, abk_common.OsType.WINDOWS_OS)
        self.assertIs(self.service._logger, self.mock_logger)

    # -------------------------------------------------------------------------
    # WindowsDependent.set_desktop_background
    # -------------------------------------------------------------------------
    @mock.patch("ctypes.windll.user32.SystemParametersInfoW")
    @mock.patch("platform.uname")
    def test_set_desktop_background_windows_10_success(self, mock_uname, mock_spi):
        """Test setting background on Windows 10+."""
        # Arrange
        # ----------------------------------
        UnameResult = namedtuple("uname_result", ["system", "node", "release", "version", "machine", "processor"])
        mock_uname.return_value = UnameResult("Windows", "Host", "10", "10.0.19041", "AMD64", "Intel64")
        file_name = "C:\\path\\to\\image.jpg"

        # Act
        # ----------------------------------
        self.service.set_desktop_background(file_name)

        # Asserts
        # ----------------------------------
        mock_spi.assert_called_once_with(20, 0, file_name, 3)

    @mock.patch("ctypes.windll.user32.SystemParametersInfoW", create=True)
    @mock.patch("platform.uname")
    def test_set_desktop_background_windows_old_version(self, mock_uname, mock_spi):
        """Test setting background on unsupported Windows version (< 10)."""
        # Arrange
        # ----------------------------------
        Uname = namedtuple("Uname", ["system", "node", "release", "version", "machine", "processor"])
        mock_uname.return_value = Uname("Windows", "my-host", "6", "6.1.7601", "AMD64", "Intel64")
        file_name = "C:\\Users\\Test\\Pictures\\image.jpg"

        # Act
        # ----------------------------------
        self.service.set_desktop_background(file_name)

        # Assert
        # ----------------------------------
        # print("LOGGER CALLS:")
        # for call in self.mock_logger.error.call_args_list:
        #     print(call)
        self.assertTrue(any("Windows 10 and above is supported" in str(call) for call in self.mock_logger.error.call_args_list))
        mock_spi.assert_not_called()
        self.mock_logger.error.assert_any_call("Windows 10 and above is supported, you are using Windows 6")
        self.assertTrue(
            any("Windows 10 and above is supported" in call.args[0] for call in self.mock_logger.error.call_args_list)
        )


# =============================================================================
# TestBingWallPaper
# =============================================================================
class TestBingWallPaper(unittest.TestCase):
    """Test BingWallPaper."""

    def setUp(self):
        """Setup BingWallPaper."""
        self.mock_logger = mock.Mock()
        self.mock_options = Namespace()
        self.mock_os_dependent = mock.Mock()
        self.mock_dl_service = mock.Mock()

        self.bwp = bingwallpaper.BingWallPaper(
            bw_logger=self.mock_logger,
            options=self.mock_options,
            os_dependant=self.mock_os_dependent,
            dl_service=self.mock_dl_service,
        )

    # -------------------------------------------------------------------------
    # TestBingWallPaper.convert_dir_structure_if_needed
    # -------------------------------------------------------------------------
    def test_convert_dir_structure_if_needed(self):
        """Test test_convert_dir_structure_if_needed."""
        self.bwp.convert_dir_structure_if_needed()
        self.mock_dl_service.convert_dir_structure_if_needed.assert_called_once()

    # -------------------------------------------------------------------------
    # TestBingWallPaper.test_download_new_images
    # -------------------------------------------------------------------------
    def test_download_new_images(self):
        """Test test_download_new_images."""
        self.bwp.download_new_images()
        self.mock_dl_service.download_new_images.assert_called_once()

    # -------------------------------------------------------------------------
    # TestBingWallPaper.test_set_desktop_background
    # -------------------------------------------------------------------------
    def test_set_desktop_background(self):
        """Test test_set_desktop_background."""
        test_img = os.path.join("fake", "path", "image.jpg")
        self.bwp.set_desktop_background(test_img)
        self.mock_os_dependent.set_desktop_background.assert_called_once_with(test_img)

    # -------------------------------------------------------------------------
    # TestBingWallPaper.process_manually_downloaded_images
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_config_store_jpg_quality", return_value=85)
    @mock.patch("abk_bwp.bingwallpaper.Image.open")
    @mock.patch("abk_bwp.abk_common.ensure_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date", return_value=os.path.join("images", "SCALE"))
    @mock.patch("os.walk", return_value=[("/images", [], ["SCALE_2024-05-01_img.jpg"])])
    @mock.patch("abk_bwp.abk_common.read_json_file", return_value={"2024-05-01_img.jpg": "Sample Title"})
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value="/images")
    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    def test_process_manually_downloaded_images(
        self,
        mock_logger,
        mock_get_img_dir,
        mock_read_json,
        mock_walk,
        mock_get_resized_path,
        mock_ensure_dir,
        mock_img_open,
        mock_get_quality,
    ):
        """Test test_process_manually_downloaded_images."""
        # Arrange
        # ----------------------------------
        mock_img = mock.Mock()
        mock_img.size = (1920, 1080)
        mock_img.getexif.return_value = {}
        mock_img.resize.return_value = mock_img
        mock_img_open.return_value.__enter__.return_value = mock_img

        # Act
        # ----------------------------------
        with mock.patch("os.remove") as mock_remove:
            bingwallpaper.BingWallPaper.process_manually_downloaded_images()

        # Asserts
        # ----------------------------------
        mock_get_img_dir.assert_called_once()
        mock_read_json.assert_called_once_with(os.path.join(mock_get_img_dir.return_value, bingwallpaper.BWP_META_DATA_FILE_NAME))
        mock_walk.assert_called_once_with(os.path.join(mock_get_img_dir.return_value))
        mock_get_resized_path.assert_called_once_with(datetime.date(2024, 5, 1))
        mock_ensure_dir.assert_called_once_with(mock_get_resized_path.return_value)
        # print("Calls to Image.open:", mock_img_open.call_args_list)
        mock_img_open.assert_called_once_with(os.path.join(mock_get_img_dir.return_value, "SCALE_2024-05-01_img.jpg"))
        mock_get_quality.assert_called_once()
        mock_img.save.assert_called_once()
        mock_remove.assert_called_once_with(os.path.join(mock_get_img_dir.return_value, "SCALE_2024-05-01_img.jpg"))
        mock_logger.exception.assert_not_called()

    @mock.patch("abk_bwp.bingwallpaper.get_config_store_jpg_quality", return_value=85)
    @mock.patch("abk_bwp.bingwallpaper.Image.open")
    @mock.patch("abk_bwp.abk_common.ensure_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date", return_value=os.path.join("images", "SCALE"))
    @mock.patch("os.walk", return_value=[("/images", [], ["SCALE_2024-05-01_img.jpg"])])
    @mock.patch("abk_bwp.abk_common.read_json_file", return_value={})  # No title in metadata
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value="/images")
    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    def test_process_manually_downloaded_images_else_branch(
        self,
        mock_logger,
        mock_get_img_dir,
        mock_read_json,
        mock_walk,
        mock_get_resized_path,
        mock_ensure_dir,
        mock_img_open,
        mock_get_quality,
    ):
        """Test else branch when no EXIF title is present."""
        # Arrange
        # ----------------------------------
        mock_img = mock.Mock()
        mock_img.size = (1920, 1080)
        mock_img.getexif.return_value = {}
        mock_img.resize.return_value = mock_img
        mock_img_open.return_value.__enter__.return_value = mock_img

        # Act
        # ----------------------------------
        with mock.patch("os.remove") as mock_remove:
            bingwallpaper.BingWallPaper.process_manually_downloaded_images()

        # Asserts
        # ----------------------------------
        mock_get_img_dir.assert_called_once()
        mock_read_json.assert_called_once_with(os.path.join(mock_get_img_dir.return_value, bingwallpaper.BWP_META_DATA_FILE_NAME))
        mock_walk.assert_called_once_with(os.path.join(mock_get_img_dir.return_value))
        mock_get_resized_path.assert_called_once_with(datetime.date(2024, 5, 1))
        mock_ensure_dir.assert_called_once_with(mock_get_resized_path.return_value)
        mock_img_open.assert_called_once_with(os.path.join(mock_get_img_dir.return_value, "SCALE_2024-05-01_img.jpg"))
        mock_get_quality.assert_called_once()
        mock_img.getexif.assert_not_called()
        mock_img.save.assert_called_once_with(
            os.path.join(mock_get_resized_path.return_value, "2024-05-01_img.jpg"), optimize=True, quality=85
        )
        mock_remove.assert_called_once_with(os.path.join(mock_get_img_dir.return_value, "SCALE_2024-05-01_img.jpg"))
        mock_logger.exception.assert_not_called()

    @mock.patch("abk_bwp.bingwallpaper.get_config_store_jpg_quality", return_value=85)
    @mock.patch("abk_bwp.bingwallpaper.Image.open", side_effect=OSError("Cannot open image"))
    @mock.patch("abk_bwp.abk_common.ensure_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date", return_value=os.path.join("images", "SCALE"))
    @mock.patch("os.walk", return_value=[("/images", [], ["SCALE_2024-05-01_img.jpg"])])
    @mock.patch("abk_bwp.abk_common.read_json_file", return_value={})
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value="/images")
    @mock.patch("abk_bwp.bingwallpaper.logger", new=mock.Mock())
    def test_process_manually_downloaded_images_exception(
        self, mock_get_img_dir, mock_read_json, mock_walk, mock_get_resized_path, mock_ensure_dir, mock_img_open, mock_get_quality
    ):
        """Test exception handling in process_manually_downloaded_images."""
        bingwallpaper.BingWallPaper.process_manually_downloaded_images()

        mock_get_img_dir.assert_called_once()
        mock_read_json.assert_called_once_with(os.path.join(mock_get_img_dir.return_value, bingwallpaper.BWP_META_DATA_FILE_NAME))
        mock_walk.assert_called_once_with(os.path.join(mock_get_img_dir.return_value))
        mock_get_resized_path.assert_called_once_with(datetime.date(2024, 5, 1))
        mock_ensure_dir.assert_called_once_with(mock_get_resized_path.return_value)
        mock_img_open.assert_called_once_with(os.path.join(mock_get_img_dir.return_value, "SCALE_2024-05-01_img.jpg"))
        mock_get_quality.assert_not_called()  # It should fail before this
        bingwallpaper.logger.exception.assert_called_once()

    # -------------------------------------------------------------------------
    # TestBingWallPaper._calculate_image_resizing
    # -------------------------------------------------------------------------
    def test_exact_match_min_size(self):
        """Returns same size when input matches BWP_RESIZE_MIN_IMG_SIZE."""
        result = bingwallpaper.BingWallPaper._calculate_image_resizing(bingwallpaper.BWP_RESIZE_MIN_IMG_SIZE)
        self.assertEqual(result, bingwallpaper.BWP_RESIZE_MIN_IMG_SIZE)

    def test_exact_match_default_size(self):
        """Returns same size when input matches BWP_DEFAULT_IMG_SIZE."""
        result = bingwallpaper.BingWallPaper._calculate_image_resizing(bingwallpaper.BWP_DEFAULT_IMG_SIZE)
        self.assertEqual(result, bingwallpaper.BWP_DEFAULT_IMG_SIZE)

    def test_larger_than_mid_threshold(self):
        """Returns default size if either dimension is larger than mid threshold."""
        larger_img = (bingwallpaper.BWP_RESIZE_MID_IMG_SIZE[0] + 1, bingwallpaper.BWP_RESIZE_MID_IMG_SIZE[1] + 1)
        result = bingwallpaper.BingWallPaper._calculate_image_resizing(larger_img)
        self.assertEqual(result, bingwallpaper.BWP_DEFAULT_IMG_SIZE)

    def test_smaller_than_mid_threshold(self):
        """Returns min size if image is smaller than mid threshold."""
        smaller_img = (bingwallpaper.BWP_RESIZE_MID_IMG_SIZE[0] - 1, bingwallpaper.BWP_RESIZE_MID_IMG_SIZE[1] - 1)
        result = bingwallpaper.BingWallPaper._calculate_image_resizing(smaller_img)
        self.assertEqual(result, bingwallpaper.BWP_RESIZE_MIN_IMG_SIZE)

    # -------------------------------------------------------------------------
    # TestBingWallPaper.update_current_background_image
    # -------------------------------------------------------------------------
    @mock.patch.object(bingwallpaper.BingWallPaper, "set_desktop_background")
    @mock.patch("abk_bwp.bingwallpaper.delete_files_in_dir")
    @mock.patch("os.walk")
    @mock.patch.object(bingwallpaper.BingWallPaper, "_resize_background_image", return_value=True)
    @mock.patch("abk_bwp.bingwallpaper.get_config_background_img_size", return_value=(1920, 1080))
    @mock.patch("abk_bwp.bingwallpaper.is_config_desktop_img_enabled", return_value=True)
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="en-US")
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date")
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value="/images")
    def test_update_current_background_image_happy_path(
        self,
        mock_get_img_dir,
        mock_get_today_img_path,
        mock_get_region,
        mock_exists,
        mock_desktop_enabled,
        mock_get_size,
        mock_resize,
        mock_walk,
        mock_delete,
        mock_set_bg,
    ):
        """Test test_update_current_background_image_happy_path."""
        # Arrange
        # ----------------------------------
        today = datetime.date.today()
        img_name = f"{today.year:04d}-{today.month:02d}-{today.day:02d}_en-US.jpg"
        dst_file_name = f"{bingwallpaper.BWP_DEFAULT_BACKGROUND_IMG_PREFIX}_{img_name}"
        full_img_path = os.path.join("/images", f"{today.year:04d}-{today.month:02d}-{today.day:02d}", img_name)
        dst_full_path = os.path.join("/images", dst_file_name)

        mock_get_today_img_path.return_value = os.path.dirname(full_img_path)
        mock_walk.return_value = [
            (
                "/images",
                [],
                ["background_img_old.jpg", dst_file_name],  # simulate both current and old images in the dir
            )
        ]

        # Act
        # ----------------------------------
        self.bwp.update_current_background_image()

        # Assert
        # ----------------------------------
        mock_get_img_dir.assert_called_once()
        mock_get_today_img_path.assert_called_once_with(today)
        mock_get_region.assert_called_once()
        mock_exists.assert_called_once_with(full_img_path)
        mock_get_size.assert_called_once()
        mock_resize.assert_called_once_with(full_img_path, dst_full_path, (1920, 1080))
        mock_walk.assert_called_once_with("/images")
        mock_delete.assert_called_once_with("/images", ["background_img_old.jpg"])
        mock_set_bg.assert_called_once_with(dst_full_path)

    # -------------------------------------------------------------------------
    # TestBingWallPaper._resize_background_image
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_config_desktop_jpg_quality", return_value=85)
    @mock.patch("abk_bwp.bingwallpaper.BingWallPaper.add_outline_text")
    @mock.patch("abk_bwp.bingwallpaper.abk_common.ensure_dir")
    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    def test_resize_background_image_with_resize_and_exif(self, mock_logger, mock_ensure_dir, mock_add_text, mock_quality):
        """Test test_resize_background_image_with_resize_and_exif."""
        # Arrange
        # ----------------------------------
        src_img = Image.new("RGB", (1000, 1000), color="blue")
        exif_dict = {
            bingwallpaper.BWP_EXIF_IMAGE_DESCRIPTION_FIELD: "Some Title",
            bingwallpaper.BWP_EXIF_IMAGE_COPYRIGHT_FIELD: "Some Copyright",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = os.path.join(tmpdir, "src.jpg")
            dst_path = os.path.join(tmpdir, "dst.jpg")
            src_img.save(src_path)

            mock_img = mock.MagicMock(spec=Image.Image)
            mock_img.size = (1000, 1000)
            mock_img.getexif.return_value = exif_dict
            mock_img.resize.return_value = mock_img
            mock_img.convert.return_value = mock_img
            mock_img.__enter__.return_value = mock_img

            # Act
            # ----------------------------------
            with mock.patch("PIL.Image.open", return_value=mock_img):
                result = bingwallpaper.BingWallPaper._resize_background_image(src_path, dst_path, (800, 600))

        # Asserts
        # ----------------------------------
        self.assertTrue(result)
        mock_ensure_dir.assert_called_once_with(tmpdir)
        mock_add_text.assert_called_once()
        mock_quality.assert_called_once()
        mock_img.save.assert_called_once_with(dst_path, optimize=True, quality=85)

    @mock.patch("abk_bwp.bingwallpaper.get_config_desktop_jpg_quality", return_value=80)
    @mock.patch("abk_bwp.bingwallpaper.BingWallPaper.add_outline_text")
    @mock.patch("abk_bwp.bingwallpaper.Image.open")
    @mock.patch("abk_bwp.bingwallpaper.abk_common.ensure_dir")
    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    def test_resize_background_image_no_resize_needed(
        self, mock_logger, mock_ensure_dir, mock_image_open, mock_add_text, mock_get_quality
    ):
        """Test when no resize is needed (image is already at correct size)."""
        # Arrange
        # ----------------------------------
        mock_img = mock.Mock()
        mock_img.size = (1920, 1080)
        mock_img.convert.return_value = mock_img
        mock_img.getexif.return_value = {
            bingwallpaper.BWP_EXIF_IMAGE_DESCRIPTION_FIELD: "Test Title",
            bingwallpaper.BWP_EXIF_IMAGE_COPYRIGHT_FIELD: "Test Copyright",
        }
        mock_image_open.return_value.__enter__.return_value = mock_img
        src_path = "src.jpg"
        dst_path = "dst.jpg"
        dst_size = (1920, 1080)

        # Act
        # ----------------------------------
        result = bingwallpaper.BingWallPaper._resize_background_image(src_path, dst_path, dst_size)

        # Asserts
        # ----------------------------------
        self.assertTrue(result)
        mock_ensure_dir.assert_called_once_with(os.path.dirname(dst_path))
        mock_img.convert.assert_called_once_with("RGB")
        mock_add_text.assert_called_once_with(mock_img, "Test Title", "Test Copyright")
        mock_img.save.assert_called_once_with(dst_path, optimize=True, quality=80)
        mock_get_quality.assert_called_once()

    @mock.patch("abk_bwp.bingwallpaper.get_config_desktop_jpg_quality", return_value=75)
    @mock.patch("abk_bwp.bingwallpaper.BingWallPaper.add_outline_text")
    @mock.patch("abk_bwp.bingwallpaper.abk_common.ensure_dir")
    @mock.patch("abk_bwp.bingwallpaper.logger", new=mock.Mock())
    def test_resize_background_image_with_exception(self, mock_ensure_dir, mock_add_text, mock_quality):
        """Test test_resize_background_image_with_exception."""
        # Arrange
        # ----------------------------------
        invalid_src_path = "/does/not/exist.jpg"
        fake_dst_dir = "/tmp"
        fake_dst_path = f"{fake_dst_dir}/output.jpg"

        # Act
        # ----------------------------------
        result = bingwallpaper.BingWallPaper._resize_background_image(invalid_src_path, fake_dst_path, (800, 600))

        # Asserts
        # ----------------------------------
        self.assertFalse(result)
        mock_ensure_dir.assert_called_once_with(fake_dst_dir)
        mock_add_text.assert_not_called()
        mock_quality.assert_not_called()
        bingwallpaper.logger.exception.assert_called_once()

    # -------------------------------------------------------------------------
    # TestBingWallPaper.add_outline_text
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_text_overlay_font_name", return_value="arial.ttf")
    @mock.patch("abk_bwp.bingwallpaper.ImageFont.truetype")
    @mock.patch("abk_bwp.bingwallpaper.ImageDraw.Draw")
    def test_add_outline_text(self, mock_draw_cls, mock_truetype, mock_get_font_name):
        """Test test_add_outline_text."""
        # Arrange
        # ----------------------------------
        mock_font = mock.Mock()
        mock_font.getbbox.return_value = (0, 0, 100, 30)  # x0, y0, x1, y1
        mock_truetype.return_value = mock_font

        mock_draw = mock.Mock()
        mock_draw_cls.return_value = mock_draw

        mock_img = mock.Mock()
        mock_img.size = (1920, 1080)

        title = "Sample Title"
        copyright = "© 2025"

        with (
            mock.patch("abk_bwp.bingwallpaper.BWP_TITLE_TEXT_FONT_SIZE", 30),
            mock.patch("abk_bwp.bingwallpaper.BWP_TITLE_TEXT_POSITION_OFFSET", (10, 10)),
            mock.patch("abk_bwp.bingwallpaper.BWP_TITLE_OUTLINE_AMOUNT", 2),
            mock.patch("abk_bwp.bingwallpaper.BWP_TITLE_GLOW_COLOR", "glow"),
            mock.patch("abk_bwp.bingwallpaper.BWP_TITLE_TEXT_COLOR", "maintext"),
        ):
            # Act
            # ----------------------------------
            bingwallpaper.BingWallPaper.add_outline_text(mock_img, title, copyright)

        # Asserts
        # ----------------------------------
        mock_get_font_name.assert_called_once()
        # Check that the font was loaded
        mock_truetype.assert_called_once_with("arial.ttf", 30)
        # Ensure getbbox was called on the longest line
        mock_font.getbbox.assert_called()
        # Check that outline + text were drawn
        # Outline should be drawn 8 * BWP_TITLE_OUTLINE_AMOUNT = 16 times
        # Final text should be drawn once
        expected_outline_calls = 8 * 2
        self.assertEqual(mock_draw.text.call_count, expected_outline_calls + 1)
        # Check final draw.text call (last one) used the main text color
        last_call = mock_draw.text.call_args_list[-1]
        _, kwargs = last_call
        self.assertEqual(kwargs["fill"], "maintext")
        self.assertIn("Sample Title", kwargs["text"])
        self.assertIn("© 2025", kwargs["text"])

    # -------------------------------------------------------------------------
    # TestBingWallPaper.trim_number_of_images
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.abk_common.delete_dir")
    @mock.patch("abk_bwp.bingwallpaper.abk_common.delete_file")
    @mock.patch("abk_bwp.bingwallpaper.os.path.join", side_effect=lambda a, b: f"{a}/{b}")
    @mock.patch("abk_bwp.bingwallpaper.os.path.split", side_effect=lambda p: (f"{p}_parent", "dummy"))
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_file_name", side_effect=lambda name: f"/images/{name}")
    @mock.patch("abk_bwp.bingwallpaper.get_config_number_of_images_to_keep", return_value=3)
    @mock.patch("abk_bwp.bingwallpaper.get_all_background_img_names", return_value=["img1", "img2", "img3", "img4", "img5"])
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value="/images")
    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    def test_trim_number_of_images(
        self,
        mock_logger,
        mock_get_config_img_dir,
        mock_get_all_img_names,
        mock_get_max_keep,
        mock_get_full_path,
        mock_path_split,
        mock_path_join,
        mock_delete_file,
        mock_delete_dir,
    ):
        """Test test_trim_number_of_images."""
        # Arrange
        # ----------------------------------
        # Act
        # ----------------------------------
        bingwallpaper.BingWallPaper.trim_number_of_images()

        # Asserts
        # ----------------------------------
        # 5 - 3 = 2 files should be trimmed
        mock_get_config_img_dir.assert_called_once()
        mock_get_all_img_names.assert_called_once_with("/images")
        mock_get_max_keep.assert_called_once()
        self.assertEqual(mock_get_full_path.call_count, 2)
        mock_path_join.assert_has_calls([mock.call("/images/img1", "img1"), mock.call("/images/img2", "img2")])
        mock_path_split.assert_has_calls([mock.call("/images/img1"), mock.call("/images/img2")])
        mock_delete_file.assert_has_calls([mock.call("/images/img1/img1"), mock.call("/images/img2/img2")])
        mock_delete_dir.assert_has_calls(
            [
                mock.call("/images/img1"),
                mock.call("/images/img1_parent"),
                mock.call("/images/img2"),
                mock.call("/images/img2_parent"),
            ]
        )
        self.assertEqual(mock_delete_file.call_count, 2)
        self.assertEqual(mock_delete_dir.call_count, 4)

    # -------------------------------------------------------------------------
    # TestBingWallPaper.prepare_ftv_images
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.BingWallPaper._resize_background_image")
    @mock.patch("abk_bwp.bingwallpaper.os.path.join", side_effect=lambda *args: "/".join(args))
    @mock.patch("abk_bwp.bingwallpaper.get_full_img_dir_from_date", return_value="/images/2025-05-26")
    @mock.patch("abk_bwp.bingwallpaper.delete_files_in_dir")
    @mock.patch("abk_bwp.bingwallpaper.os.walk")
    @mock.patch("abk_bwp.bingwallpaper.abk_common.ensure_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value="/images")
    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    def test_prepare_ftv_images(
        self,
        mock_logger,
        mock_get_config_img_dir,
        mock_ensure_dir,
        mock_os_walk,
        mock_delete_files,
        mock_get_full_img_dir,
        mock_path_join,
        mock_resize_image,
    ):
        """Test prepare_ftv_images static method behavior."""
        # Arrange
        # ----------------------------------
        ftv_dir = "/images/ftv_images_today"
        today_dir = "/images/2025-05-26"

        mock_os_walk.side_effect = [
            iter([(ftv_dir, [], ["old1.jpg", "old2.jpg"])]),
            iter([(today_dir, [], ["new1.jpg", "new2.jpg"])]),
        ]

        # Act
        # ----------------------------------
        result = bingwallpaper.BingWallPaper.prepare_ftv_images()

        # Asserts
        # ----------------------------------
        mock_get_config_img_dir.assert_called_once()
        mock_path_join.assert_any_call(today_dir, "new1.jpg")
        mock_path_join.assert_any_call(ftv_dir, "new1.jpg")
        mock_path_join.assert_any_call(today_dir, "new2.jpg")
        mock_path_join.assert_any_call(ftv_dir, "new2.jpg")
        mock_ensure_dir.assert_called_once_with(ftv_dir)
        mock_delete_files.assert_called_once_with(dir_name=ftv_dir, file_list=["old1.jpg", "old2.jpg"])
        mock_get_full_img_dir.assert_called_once_with(datetime.date.today())
        mock_resize_image.assert_has_calls(
            [
                mock.call(f"{today_dir}/new1.jpg", f"{ftv_dir}/new1.jpg", bingwallpaper.BWP_DEFAULT_IMG_SIZE),
                mock.call(f"{today_dir}/new2.jpg", f"{ftv_dir}/new2.jpg", bingwallpaper.BWP_DEFAULT_IMG_SIZE),
            ]
        )
        mock_resize_image.assert_called()
        mock_resize_image.assert_any_call(f"{today_dir}/new1.jpg", f"{ftv_dir}/new1.jpg", mock.ANY)
        mock_resize_image.assert_any_call(f"{today_dir}/new2.jpg", f"{ftv_dir}/new2.jpg", mock.ANY)
        mock_resize_image.assert_has_calls(mock_resize_image.mock_calls)  # confirms call order
        self.assertEqual(mock_resize_image.call_count, 2)
        self.assertEqual(result, [f"{ftv_dir}/new1.jpg", f"{ftv_dir}/new2.jpg"])


if __name__ == "__main__":
    unittest.main()

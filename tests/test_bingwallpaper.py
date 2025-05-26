"""Unit tests for bingwallpaper.py."""

# Standard library imports
import logging
import platform
import sys
import warnings
import datetime
import os
from pathlib import Path
import time
import unittest
from unittest import mock
from xmlrpc.client import ResponseError

# Third party imports
from parameterized import parameterized
from PIL import Image
from requests import Response


# Own modules imports
from abk_bwp import abk_common, bingwallpaper, config


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
        with mock.patch.dict(
            config.bwp_config, {"region": img_region, "dl_service": img_dl_service}
        ):
            act_region = bingwallpaper.get_config_img_region()
        self.assertEqual(act_region, exp_region)

    # -------------------------------------------------------------------------
    # get_full_img_dir_from_file_name
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_relative_img_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir")
    @mock.patch("abk_bwp.bingwallpaper.get_date_from_img_file_name")
    def test_get_full_img_dir_from_file_name(
        self, mock_get_date, mock_get_config_dir, mock_get_relative_dir
    ):
        """Test get_full_img_dir_from_file_name returns correct path."""
        mock_get_date.return_value = datetime.date(2025, 5, 24)
        mock_get_config_dir.return_value = os.path.join(
            "C:", os.sep, "Users", "runneradmin", "Pictures", "BingWallpapers"
        )
        mock_get_relative_dir.return_value = os.path.join("2025", "05", "24")
        expected_path = os.path.join(
            mock_get_config_dir.return_value, mock_get_relative_dir.return_value
        )

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
        mock_walk.return_value = [
            ("/mocked/path", ["subdir"], ["2025-05-25_image.jpg", "invalid_file.txt"])
        ]

        def side_effect(filename):
            return filename == "2025-05-25_image.jpg"

        mock_get_date.side_effect = side_effect

        # Act
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
    def test__get_img_region__given_a_valid_setting_returns_defined_region(
        self, img_region: str, img_dl_service: str
    ) -> None:
        """test__get_img_region__given_a_valid_setting_returns_defined_region.

        Args:
            img_region (str): image region
            img_dl_service (str): image download service
        """
        with mock.patch.dict(
            config.bwp_config, {"region": img_region, "dl_service": img_dl_service}
        ):
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
        with mock.patch.dict(
            config.bwp_config, {"region": img_region, "dl_service": img_dl_service}
        ):
            act_bing_region = bingwallpaper.get_config_bing_img_region()
        self.assertEqual(act_bing_region, exp_bing_region)

    # -------------------------------------------------------------------------
    # is_config_ftv_enabled
    # -------------------------------------------------------------------------
    @mock.patch.dict(
        config.bwp_config,
        {bingwallpaper.FTV_KW.FTV.value: {bingwallpaper.FTV_KW.ENABLED.value: True}},
    )
    def test_ftv_enabled_true(self):
        """Test FTV enabled true."""
        self.assertTrue(bingwallpaper.is_config_ftv_enabled())

    @mock.patch.dict(
        config.bwp_config,
        {bingwallpaper.FTV_KW.FTV.value: {bingwallpaper.FTV_KW.ENABLED.value: False}},
    )
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
        with mock.patch.dict(
            config.bwp_config, {"desktop_img": {"width": cnf_width, "height": cnf_height}}
        ):
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
            "ignore",
            message="datetime.datetime.utcnow\\(\\) is deprecated",
            category=DeprecationWarning,
            module="reactivex.*",
        )

    # -------------------------------------------------------------------------
    # DownLoadServiceBase.convert_dir_structure_if_needed
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.DownLoadServiceBase._convert_to_ftv_dir_structure")
    @mock.patch("abk_bwp.bingwallpaper.is_config_ftv_enabled", return_value=True)
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_dir", return_value="/mocked/path")
    @mock.patch("os.walk")
    def test_convert_to_ftv_structure(
        self, mock_walk, mock_get_config_img_dir, mock_is_config_ftv_enabled, mock_convert_to_ftv
    ):
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
    def test_empty_directory_creates_warning_file(
        self, mock_walk, mock_get_config_img_dir, mock_open
    ):
        """Test test_empty_directory_creates_warning_file."""
        # Simulate os.walk returning an empty directory
        mock_walk.return_value = iter([("/mocked/path", [], [])])

        bingwallpaper.DownLoadServiceBase.convert_dir_structure_if_needed()

        mock_open.assert_called_once_with(
            "/mocked/path/Please_do_not_modify_anything_in_this_directory.Handled_by_BingWallpaper_automagic",
            "a",
        )
        mock_get_config_img_dir.assert_called_once()

    # -------------------------------------------------------------------------
    # DownLoadServiceBase._convert_to_ftv_dir_structure
    # -------------------------------------------------------------------------
    @mock.patch("shutil.rmtree")
    @mock.patch("os.renames")
    @mock.patch("os.walk")
    @mock.patch.dict(config.bwp_config, {"alt_peapix_region": ["us"]})
    def test_convert_to_ftv_dir_structure(
        self, mock_os_walk, mock_os_renames, mock_shutil_rmtree
    ):
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
        mock_shutil_rmtree.assert_called_once_with(
            os.path.join(root_image_dir, "2021"), ignore_errors=True
        )

    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    @mock.patch("shutil.rmtree")
    @mock.patch("os.renames", side_effect=OSError("Simulated error during renaming"))
    @mock.patch("os.walk")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"alt_peapix_region": ["us"]})
    def test_convert_to_ftv_dir_structure_exception(
        self, mock_os_walk, mock_os_renames, mock_shutil_rmtree, mock_logger_resolve
    ):
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
            bingwallpaper.DownLoadServiceBase._convert_to_ftv_dir_structure(
                root_image_dir, year_list
            )

        self.assertIn("Simulated error during renaming", str(cm.exception))
        # Assert that our dummy logger’s error method was called.
        self.assertTrue(dummy_logger.error.called)
        # Optionally, check that rmtree is not called because the exception stops processing.
        mock_shutil_rmtree.assert_not_called()
        mock_os_renames.assert_called_once()

    # -------------------------------------------------------------------------
    # DownLoadServiceBase._convert_to_date_dir_structure
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.logger", new_callable=mock.MagicMock)
    @mock.patch("shutil.rmtree")
    @mock.patch("os.renames")
    @mock.patch("os.walk")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"alt_peapix_region": ["us"]})
    def test_convert_to_date_dir_structure(
        self, mock_os_walk, mock_os_renames, mock_shutil_rmtree, mock_logger
    ):
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
        bingwallpaper.DownLoadServiceBase._convert_to_date_dir_structure(
            root_image_dir, month_list
        )

        expected_src = os.path.join(root_image_dir, "01", "01", "2021-01-01_us.jpg")
        expected_dst = os.path.join(root_image_dir, "2021", "01", "2021-01-01_us.jpg")
        mock_os_renames.assert_called_once_with(expected_src, expected_dst)
        mock_shutil_rmtree.assert_called_once_with(
            os.path.join(root_image_dir, "01"), ignore_errors=True
        )

    @mock.patch("abk_bwp.bingwallpaper.logger._resolve")
    @mock.patch("shutil.rmtree")
    @mock.patch("os.renames", side_effect=OSError("Simulated error during renaming"))
    @mock.patch("os.walk")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"alt_peapix_region": ["us"]})
    def test_convert_to_date_dir_structure_exception(
        self, mock_os_walk, mock_os_renames, mock_shutil_rmtree, mock_logger
    ):
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
            bingwallpaper.DownLoadServiceBase._convert_to_date_dir_structure(
                root_image_dir, month_list
            )

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
            bingwallpaper.ImageDownloadData(
                datetime.date(2025, 1, 2), b"title2", b"copy2", ["url2"], "img/path", "img2.jpg"
            ),
            bingwallpaper.ImageDownloadData(
                datetime.date(2025, 1, 1), b"title1", b"copy1", ["url1"], "img/path", "img1.jpg"
            ),
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(logger=mock_logger)
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
            bingwallpaper.ImageDownloadData(
                datetime.date(2025, 1, 2), b"title2", b"copy2", ["url2"], "img/path", "img2.jpg"
            ),
            bingwallpaper.ImageDownloadData(
                datetime.date(2025, 1, 1), b"title1", b"copy1", ["url1"], "img/path", "img1.jpg"
            ),
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(logger=mock_logger)
        service._download_images(img_data_list)
        time.sleep(2)  # Wait briefly for threads to complete

        # Asserts
        # ----------------------------------
        self.assertEqual(mock_process_image.call_count, 4)  # 3 (retries) + 1 (img2)
        mock_logger.info.assert_any_call("✅ All image downloads completed.")

    @mock.patch.object(
        bingwallpaper.BingDownloadService,
        "_process_and_download_image",
        side_effect=Exception("permanent failure"),
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
                datetime.date(2025, 1, 1),
                b"title1",
                b"copy1",
                ["url1"],
                os.path.join("img", "path"),
                "img1.jpg",
            )
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(logger=mock_logger)
        service._download_images(img_data_list)
        time.sleep(2)  # Wait briefly for threads to complete

        # Asserts
        # ----------------------------------
        # Called 3 times due to retries
        self.assertEqual(mock_process_image.call_count, 3)
        mock_logger.error.assert_called_with(mock.ANY)  # Something like "❌ Stream error: ..."

    # -------------------------------------------------------------------------
    # DownLoadServiceBase._process_and_download_image
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_config_store_jpg_quality", return_value=85)
    @mock.patch("PIL.Image.open")
    @mock.patch("requests.get")
    @mock.patch("abk_bwp.abk_common.ensure_dir")
    @mock.patch(
        "abk_bwp.bingwallpaper.get_full_img_dir_from_file_name",
        return_value=os.path.join("mocked", "path"),
    )
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_process_and_download_image_success(
        self,
        mock_get_logger,
        mock_get_path,
        mock_ensure_dir,
        mock_requests_get,
        mock_image_open,
        mock_get_quality,
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
        service = bingwallpaper.BingDownloadService(logger=mock_logger)
        service._process_and_download_image(image_data)

        # Asserts
        # ----------------------------------
        mock_get_path.assert_called_once_with("test.jpg")
        mock_ensure_dir.assert_called_once_with(os.path.join("mocked", "path"))
        mock_requests_get.assert_called_once_with(
            "http://example.com/image.jpg", stream=True, timeout=mock.ANY
        )
        mock_image_open.assert_called_once()
        mock_image.resize.assert_called_once_with(
            bingwallpaper.BWP_DEFAULT_IMG_SIZE, Image.Resampling.LANCZOS
        )
        mock_get_quality.assert_called_once()
        mock_image.save.assert_called_once()
        mock_logger.exception.assert_not_called()

    @mock.patch("abk_bwp.bingwallpaper.get_config_store_jpg_quality", return_value=85)
    @mock.patch("PIL.Image.open")
    @mock.patch("requests.get", return_value=mock.Mock(status_code=404))
    @mock.patch("abk_bwp.abk_common.ensure_dir")
    @mock.patch(
        "abk_bwp.bingwallpaper.get_full_img_dir_from_file_name",
        return_value=os.path.join("mocked", "path"),
    )
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_process_and_download_image_http_error(
        self,
        mock_get_logger,
        mock_get_path,
        mock_ensure_dir,
        mock_requests_get,
        mock_image_open,
        mock_get_quality,
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
        service = bingwallpaper.BingDownloadService(logger=mock_logger)
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
    @mock.patch(
        "abk_bwp.bingwallpaper.get_full_img_dir_from_file_name",
        return_value=os.path.join("mocked", "path"),
    )
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_process_and_download_image_raises_exception(
        self,
        mock_get_logger,
        mock_get_path,
        mock_ensure_dir,
        mock_requests_get,
        mock_image_open,
        mock_get_quality,
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
        service = bingwallpaper.BingDownloadService(logger=mock_logger)
        service._process_and_download_image(image_data)

        # Assert
        # ----------------------------------
        mock_get_path.assert_called_once_with("test.jpg")
        mock_ensure_dir.assert_called_once_with(os.path.join("mocked", "path"))
        mock_requests_get.assert_called_once()
        mock_requests_get.assert_called_once_with(
            "http://example.com/corrupt.jpg",
            stream=True,
            timeout=bingwallpaper.BWP_REQUEST_TIMEOUT,
        )
        mock_image_open.assert_called_once()
        mock_get_quality.assert_not_called()
        expected_path = os.path.join("mocked", "path", "test.jpg")
        mock_logger.exception.assert_called_once_with(
            f"ERROR: exp=Exception('Image error'), downloading image: {expected_path}"
        )


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
    def test_download_new_images_success(
        self, mock_download_images, mock_requests_get, mock_get_logger
    ):
        """Test test_download_new_images_success."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup mock response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "images": [
                {
                    "startdate": "20250525",
                    "title": "Sample Image",
                    "copyright": "Sample Copyright",
                    "url": "/sample.jpg",
                }
            ]
        }
        mock_requests_get.return_value = mock_response

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(logger=mock_logger)
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
        service = bingwallpaper.BingDownloadService(logger=mock_logger)
        with self.assertRaises(ResponseError):
            service.download_new_images()

    # -------------------------------------------------------------------------
    # BingDownloadService._process_bing_api_data
    # -------------------------------------------------------------------------
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch(
        "abk_bwp.bingwallpaper.get_full_img_dir_from_date",
        return_value=os.path.join("mocked", "path"),
    )
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="en-US")
    @mock.patch(
        "abk_bwp.bingwallpaper.get_config_img_dir", return_value=os.path.join("mock", "imgdir")
    )
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_process_valid_metadata_image_not_exists(
        self, mock_get_logger, mock_get_img_dir, mock_get_region, mock_get_full_path, mock_exists
    ):
        """Test test_process_valid_metadata_image_not_exists."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger

        metadata_list = [
            {"startdate": "20250102", "copyright": "Test Image", "urlbase": "/testimage"}
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(logger=mock_logger)
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
        mock_exists.assert_called_once_with(
            os.path.join("mocked", "path", "2025-01-02_en-US.jpg")
        )

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch(
        "abk_bwp.bingwallpaper.get_full_img_dir_from_date",
        return_value=os.path.join("mocked", "path"),
    )
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="en-US")
    @mock.patch(
        "abk_bwp.bingwallpaper.get_config_img_dir", return_value=os.path.join("mock", "imgdir")
    )
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
        metadata_list = [
            {"startdate": "20250102", "copyright": "Test Image", "urlbase": "/testimage"}
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.BingDownloadService(logger=mock_logger)
        result = service._process_bing_api_data(metadata_list)

        # Assert
        # ----------------------------------
        self.assertEqual(result, [])  # should not return anything if already exists
        mock_logger.debug.assert_any_call("Number if images to download: 0")
        mock_get_img_dir.assert_called_once_with()
        mock_get_region.assert_called_once_with()
        mock_get_full_path.assert_called_once_with(datetime.date(2025, 1, 2))
        mock_exists.assert_called_once_with(
            os.path.join("mocked", "path", "2025-01-02_en-US.jpg")
        )

    @mock.patch("os.path.exists", return_value=False)
    @mock.patch(
        "abk_bwp.bingwallpaper.get_full_img_dir_from_date",
        return_value=os.path.join("mocked", "path"),
    )
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="en-US")
    @mock.patch(
        "abk_bwp.bingwallpaper.get_config_img_dir", return_value=os.path.join("mock", "imgdir")
    )
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
        metadata_list = [
            {"startdate": "not-a-date", "copyright": "Test Image", "urlbase": "/testimage"}
        ]

        service = bingwallpaper.BingDownloadService(logger=mock_logger)
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
    @mock.patch(
        "abk_bwp.bingwallpaper.get_config_img_dir", return_value=os.path.join("mock", "dir")
    )
    @mock.patch.dict(
        "abk_bwp.bingwallpaper.bwp_config",
        {"CONSTANT": {"PEAPIX_URL": "https://api.peapix.com"}, "REGION": "us"},
    )
    @mock.patch("requests.get")
    @mock.patch.object(bingwallpaper.PeapixDownloadService, "_process_peapix_api_data")
    @mock.patch.object(bingwallpaper.PeapixDownloadService, "_download_images")
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_download_new_images_success(
        self, mock_get_logger, mock_download, mock_process, mock_requests_get, mock_img_dir
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
        mock_process.return_value = ["image1", "image2"]

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(logger=mock_logger)
        service.download_new_images()

        # Assert
        # ----------------------------------
        mock_img_dir.assert_called_once_with()
        mock_requests_get.assert_called_once()
        mock_process.assert_called_once_with({"data": "mocked"})
        mock_download.assert_called_once_with(["image1", "image2"])
        mock_logger.debug.assert_any_call(
            "Getting Image info from: get_metadata_url='https://peapix.com/bing/feed?country=us'"
        )

    @mock.patch(
        "abk_bwp.bingwallpaper.get_config_img_dir", return_value=os.path.join("mock", "dir")
    )
    @mock.patch.dict(
        "abk_bwp.bingwallpaper.bwp_config",
        {"CONSTANT": {"PEAPIX_URL": "https://api.peapix.com"}, "REGION": "us"},
    )
    @mock.patch("requests.get")
    @mock.patch.object(bingwallpaper.PeapixDownloadService, "_process_peapix_api_data")
    @mock.patch.object(bingwallpaper.PeapixDownloadService, "_download_images")
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_download_new_images_http_error(
        self, mock_get_logger, mock_download, mock_process, mock_requests_get, mock_img_dir
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
        service = bingwallpaper.PeapixDownloadService(logger=mock_logger)
        with self.assertRaises(ResponseError) as cm:
            service.download_new_images()

        self.assertIn("ERROR: getting bing image return error code: 500", str(cm.exception))
        mock_img_dir.assert_called_once()
        mock_requests_get.assert_called_once()
        mock_process.assert_not_called()
        mock_download.assert_not_called()

    # -------------------------------------------------------------------------
    # PeapixDownloadService._process_peapix_api_data
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="EN-US")
    @mock.patch(
        "abk_bwp.bingwallpaper.get_full_img_dir_from_date",
        return_value=os.path.join("mocked", "path")
    )
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_returns_images_to_download(
        self, mock_get_logger, mock_exists, mock_get_dir, mock_get_region
    ):
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
                "thumbUrl": "url3"
            }
        ]

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(logger=mock_logger)
        result = service._process_peapix_api_data(metadata)

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
    @mock.patch(
        "abk_bwp.bingwallpaper.get_full_img_dir_from_date",
        return_value=os.path.join("mocked", "path")
    )
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_skips_existing_images(
        self, mock_get_logger, mock_exists, mock_get_dir, mock_get_region
    ):
        """Test test_skips_existing_images."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        # Setup metadata
        metadata = [{
            "date": "2025-05-25",
            "title": "Already Exists",
            "copyright": "",
            "imageUrl": "",
            "fullUrl": "",
            "thumbUrl": ""
        }]

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(logger=mock_logger)
        result = service._process_peapix_api_data(metadata)

        # Asserts
        # ----------------------------------
        self.assertEqual(result, [])
        mock_exists.assert_called_once_with(os.path.join("mocked", "path", "2025-05-25_EN-US.jpg"))
        mock_get_dir.assert_called_once_with(datetime.date(2025, 5, 25))
        mock_get_region.assert_called_once()

    @mock.patch("abk_bwp.bingwallpaper.get_config_img_region", return_value="EN-US")
    @mock.patch(
        "abk_bwp.bingwallpaper.get_full_img_dir_from_date",
        return_value=os.path.join("mocked", "path")
    )
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("abk_bwp.logger_manager.LoggerManager.get_logger")
    def test_handles_invalid_date(
        self, mock_get_logger, mock_exists, mock_get_dir, mock_get_region
    ):
        """Test test_handles_invalid_date."""
        # Arrange
        # ----------------------------------
        # Setup logger mock
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        bad_metadata = [{
            "date": "not-a-date",
            "title": "Invalid Date",
            "imageUrl": "",
            "fullUrl": "",
            "thumbUrl": ""
        }]

        # Act
        # ----------------------------------
        service = bingwallpaper.PeapixDownloadService(logger=mock_logger)
        result = service._process_peapix_api_data(bad_metadata)

        # Asserts
        # ----------------------------------
        self.assertEqual(result, [])
        mock_logger.exception.assert_called_once()
        mock_exists.assert_not_called()
        mock_get_dir.assert_not_called()
        mock_get_region.assert_called_once()


# =============================================================================
# MacOSDependent
# =============================================================================
@unittest.skipUnless(platform.system() == "Darwin", "Only runs on macOS")
class TestMacOSDependent(unittest.TestCase):
    """Test MacOSDependent."""

    def setUp(self):
        self.mock_logger = mock.MagicMock(spec=logging.Logger)
        self.service = bingwallpaper.MacOSDependent(logger=self.mock_logger)

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
        test_file = os.path.join("Users", "test", "Pictures", "image.jpg")

        # Act
        # ----------------------------------
        self.service.set_desktop_background(test_file)

        # Asserts
        # ----------------------------------
        # Check debug logging of filename
        self.mock_logger.debug.assert_any_call(f"file_name='{test_file}'")
        # Check subprocess was called with expected AppleScript
        expected_script = f"""/usr/bin/osascript<<END
tell application "Finder"
set desktop picture to POSIX file "{test_file}"
end tell
END"""
        mock_subprocess_call.assert_called_once_with(expected_script, shell=True)
        # Check info log about setting background
        self.mock_logger.info.assert_any_call(f"(MacOS) Set background to {test_file}")


# =============================================================================
# LinuxDependent
# =============================================================================
@unittest.skipUnless(sys.platform.startswith("linux"), "Linux-specific test")
class TestLinuxDependent(unittest.TestCase):
    """Test LinuxDependent."""

    def setUp(self):
        """Setup TestLinuxDependent."""
        self.mock_logger = mock.MagicMock(spec=logging.Logger)
        self.service = bingwallpaper.LinuxDependent(logger=self.mock_logger)

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
        test_file = "/home/test/Pictures/image.jpg"

        # Act
        self.service.set_desktop_background(test_file)

        # Assert
        self.mock_logger.debug.assert_called_once_with(f"{test_file=}")
        self.mock_logger.info.assert_any_call(f"(linux) Set background to {test_file}")
        self.mock_logger.info.assert_any_call("(linux) Not implemented yet")


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
    @mock.patch("ctypes.windll.user32.SystemParametersInfoW", create=True)
    @mock.patch("platform.uname")
    def test_set_desktop_background_windows_10_success(self, mock_uname, mock_spi):
        """Test setting background on supported Windows version (>= 10)."""
        # Arrange
        mock_uname.return_value = platform.uname()._replace(release="10")
        test_file = "C:\\Users\\Test\\Pictures\\image.jpg"

        # Act
        self.service.set_desktop_background(test_file)

        # Assert
        mock_spi.assert_called_once_with(20, 0, test_file, 3)
        self.mock_logger.debug.assert_called_once_with(f"{test_file=}")
        self.mock_logger.info.assert_any_call(f"os info: {mock_uname.return_value}")
        self.mock_logger.info.assert_any_call(f"win#: 10")
        self.mock_logger.info.assert_any_call(f"Background image set to: {test_file}")
        self.mock_logger.info.assert_any_call(f"(windows) Not tested yet")
        self.mock_logger.info.assert_any_call(f"(windows) Set background to {test_file}")

    @mock.patch("ctypes.windll.user32.SystemParametersInfoW", create=True)
    @mock.patch("platform.uname")
    def test_set_desktop_background_windows_old_version(self, mock_uname, mock_spi):
        """Test setting background on unsupported Windows version (< 10)."""
        # Arrange
        mock_uname.return_value = platform.uname()._replace(release="6")
        test_file = "C:\\Users\\Test\\Pictures\\image.jpg"

        # Act
        self.service.set_desktop_background(test_file)

        # Assert
        mock_spi.assert_not_called()
        self.mock_logger.error.assert_any_call("Windows 10 and above is supported, you are using Windows 6")
        self.mock_logger.info.assert_any_call(f"(windows) Set background to {test_file}")


if __name__ == "__main__":
    unittest.main()

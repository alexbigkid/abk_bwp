"""Unit tests for bingwallpaper.py."""

# Standard library imports
import datetime
import os
from pathlib import Path
import unittest
from unittest import mock

# Third party imports
from parameterized import parameterized

# Own modules imports
from abk_bwp import bingwallpaper, config


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

    # @mock.patch('abk_bwp.bingwallpaper.datetime.datetime.strptime')
    # def test_valid_date(self, mock_strptime):
    #     """Test valid date time."""
    #     mock_strptime.return_value = datetime.datetime(2025, 5, 24)
    #     img_file_name = '2025-05-24_some_image.jpg'

    #     result = bingwallpaper.get_date_from_img_file_name(img_file_name)

    #     self.assertEqual(result, datetime.date(2025, 5, 24))
    #     mock_strptime.assert_called_once_with('2025-05-24', '%Y-%m-%d')

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

    @mock.patch("abk_bwp.bingwallpaper.get_date_from_img_file_name")
    @mock.patch("os.walk")
    @mock.patch("os.path.isdir")
    def test_get_all_background_img_names(self, mock_isdir, mock_walk, mock_get_date):
        """Test test_get_all_background_img_names."""
        mock_isdir.return_value = True
        mock_walk.return_value = [
            ("/mocked/path", ["subdir"], ["2025-05-25_image.jpg", "invalid_file.txt"])
        ]

        def side_effect(filename):
            return filename == "2025-05-25_image.jpg"

        mock_get_date.side_effect = side_effect

        result = bingwallpaper.get_all_background_img_names("/mocked/path")

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


class TestDownLoadServiceBase(unittest.TestCase):
    """Test DownLoadServiceBase."""

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


if __name__ == "__main__":
    unittest.main()

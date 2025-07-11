"""Unit tests for ftv.py."""

# Standard library imports
import os

# from unittest import TestCase, mock
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock

# local imports
from abk_bwp import ftv

TEST_FTV_FAKE_CONFIG_FILE = "tests/test_ftv_fake_config.toml"


class TestFTV(unittest.TestCase):
    """TestFTV."""

    def setUp(self):
        """Set up tests fro FTV."""
        import unittest.mock

        mock_logger = unittest.mock.Mock()
        self._ftv = ftv.FTV(logger=mock_logger, ftv_data_file=TEST_FTV_FAKE_CONFIG_FILE)

    # -------------------------------------------------------------------------
    # Tests for get_environment_variable_value_
    # -------------------------------------------------------------------------
    @patch.dict(os.environ, {"ABK_TEST_ENV_VAR": "[fake_api_key]"})
    def test_get_environment_variable_value_returns_valid_value(self) -> None:
        """get_environment_variable_value returns a value from the set environment variable."""
        actual_value = self._ftv._get_environment_variable_value("ABK_TEST_ENV_VAR")
        self.assertEqual(actual_value, "[fake_api_key]")

    @patch.dict(os.environ, {"ABK_TEST_ENV_VAR": ""})
    def test_get_environment_variable_value_should_return_empty_given_env_var_value_is_empty(self) -> None:
        """get_environment_variable_value returns empty str, given env var is set to empty str."""
        actual_value = self._ftv._get_environment_variable_value("ABK_TEST_ENV_VAR")
        self.assertEqual(actual_value, "")

    def test_get_environment_variable_value_should_return_empty_given_env_var_undefined(self) -> None:
        """get_environment_variable_value returns empty string, given env variable is not set."""
        actual_value = self._ftv._get_environment_variable_value("ABK_TEST_ENV_VAR")
        self.assertEqual(actual_value, "")

    # -------------------------------------------------------------------------
    # Tests for USB Mode functionality
    # -------------------------------------------------------------------------
    @patch("abk_bwp.ftv.bwp_config", {"ftv": {"usb_mode": True}})
    @patch("platform.system")
    @patch.object(ftv.FTV, "_copy_images_to_usb_disk")
    @patch.object(ftv.FTV, "_remount_usb_storage_for_tv")
    def test_change_daily_images_usb_mode_linux_remount_success(self, mock_remount, mock_copy, mock_platform) -> None:
        """Test USB mode on Linux with successful remount."""
        mock_platform.return_value = "Linux"
        mock_copy.return_value = True
        mock_remount.return_value = True

        result = self._ftv.change_daily_images(["test_image.jpg"])

        self.assertTrue(result)
        mock_copy.assert_called_once_with(["test_image.jpg"])
        mock_remount.assert_called_once()

    @patch("abk_bwp.ftv.bwp_config", {"ftv": {"usb_mode": True}})
    @patch("platform.system")
    @patch.object(ftv.FTV, "_copy_images_to_usb_disk")
    @patch.object(ftv.FTV, "_remount_usb_storage_for_tv")
    def test_change_daily_images_usb_mode_linux_remount_failure(self, mock_remount, mock_copy, mock_platform) -> None:
        """Test USB mode on Linux with failed remount."""
        mock_platform.return_value = "Linux"
        mock_copy.return_value = True  # Copy succeeds
        mock_remount.return_value = False  # But remount fails

        result = self._ftv.change_daily_images(["test_image.jpg"])

        self.assertFalse(result)  # Now correctly returns False when remount fails
        mock_copy.assert_called_once_with(["test_image.jpg"])
        mock_remount.assert_called_once()

    @patch("abk_bwp.ftv.bwp_config", {"ftv": {"usb_mode": True}})
    @patch("platform.system")
    @patch.object(ftv.FTV, "_copy_images_to_usb_disk")
    def test_change_daily_images_usb_mode_linux_copy_failure(self, mock_copy, mock_platform) -> None:
        """Test USB mode on Linux with failed image copy."""
        mock_platform.return_value = "Linux"
        mock_copy.return_value = False  # Copy fails

        result = self._ftv.change_daily_images(["test_image.jpg"])

        self.assertFalse(result)  # Returns False when copy fails
        mock_copy.assert_called_once_with(["test_image.jpg"])

    @patch("abk_bwp.ftv.bwp_config", {"ftv": {"usb_mode": True}})
    @patch("platform.system")
    @patch.object(ftv.FTV, "_remount_usb_storage_for_tv")
    def test_change_daily_images_usb_mode_non_linux(self, mock_remount, mock_platform) -> None:
        """Test USB mode on non-Linux platform (no remount)."""
        mock_platform.return_value = "Darwin"  # macOS

        result = self._ftv.change_daily_images(["test_image.jpg"])

        self.assertTrue(result)
        mock_remount.assert_not_called()

    @patch("abk_bwp.ftv.bwp_config", {"ftv": {"usb_mode": False}})
    @patch.object(ftv.FTV, "ftvs", {"test_tv": MagicMock()})
    def test_change_daily_images_http_mode(self) -> None:
        """Test HTTP mode (existing functionality)."""
        # This would test the existing HTTP upload logic
        # For now, just verify USB mode is not triggered
        with patch.object(self._ftv, "_connect_to_tv", return_value=False):
            result = self._ftv.change_daily_images(["test_image.jpg"])
            self.assertFalse(result)  # No TVs connected

    @patch("subprocess.run")
    def test_remount_usb_storage_for_tv_success(self, mock_subprocess) -> None:
        """Test successful USB storage remount."""
        # Mock successful subprocess calls
        mock_subprocess.side_effect = [
            MagicMock(returncode=0),  # rmmod success
            MagicMock(returncode=0),  # modprobe success
        ]

        result = self._ftv._remount_usb_storage_for_tv()

        self.assertTrue(result)
        self.assertEqual(mock_subprocess.call_count, 2)

    @patch("subprocess.run")
    def test_remount_usb_storage_for_tv_modprobe_failure(self, mock_subprocess) -> None:
        """Test USB remount with modprobe failure."""
        from subprocess import CalledProcessError  # noqa: S404

        mock_subprocess.side_effect = [
            MagicMock(returncode=0),  # rmmod success
            CalledProcessError(1, "modprobe"),  # modprobe failure
        ]

        result = self._ftv._remount_usb_storage_for_tv()

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_remount_usb_storage_for_tv_command_not_found(self, mock_subprocess) -> None:
        """Test USB remount with command not found."""
        mock_subprocess.side_effect = FileNotFoundError("sudo not found")

        result = self._ftv._remount_usb_storage_for_tv()

        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # Tests for ftvs property getter
    # -------------------------------------------------------------------------
    @patch.object(ftv.FTV, "_load_ftv_settings")
    def test_ftvs_property_lazy_loading(self, mock_load_settings) -> None:
        """Test that ftvs property triggers lazy loading when _ftv_settings is None."""
        mock_load_settings.return_value = {"test_tv": "mock_settings"}

        # Ensure _ftv_settings is None initially
        self._ftv._ftv_settings = None

        # Access the property - should trigger _load_ftv_settings
        result = self._ftv.ftvs

        # Verify _load_ftv_settings was called
        mock_load_settings.assert_called_once()
        # Verify the result is what _load_ftv_settings returned
        self.assertEqual(result, {"test_tv": "mock_settings"})

    @patch.object(ftv.FTV, "_load_ftv_settings")
    def test_ftvs_property_no_lazy_loading_when_already_set(self, mock_load_settings) -> None:
        """Test that ftvs property does not trigger loading when _ftv_settings is already set."""
        existing_settings = {"existing_tv": "existing_settings"}

        # Set _ftv_settings to an existing value
        self._ftv._ftv_settings = existing_settings

        # Access the property - should NOT trigger _load_ftv_settings
        result = self._ftv.ftvs

        # Verify _load_ftv_settings was NOT called
        mock_load_settings.assert_not_called()
        # Verify the result is the existing settings
        self.assertEqual(result, existing_settings)

    # -------------------------------------------------------------------------
    # Tests for static helper methods
    # -------------------------------------------------------------------------
    def test_get_api_token_full_file_name(self) -> None:
        """Test _get_api_token_full_file_name static method."""
        result = ftv.FTV._get_api_token_full_file_name("test_token.txt")

        # Should join dirname(__file__), "config", and filename
        expected_parts = ["config", "test_token.txt"]
        for part in expected_parts:
            self.assertIn(part, result)

    @patch("os.environ.get")
    @patch("os.path.isfile")
    @patch("builtins.open", mock.mock_open(read_data="test_token_content"))
    def test_get_api_token_from_file(self, mock_isfile, mock_env_get) -> None:
        """Test _get_api_token when token is read from file."""
        mock_env_get.return_value = None  # Not in environment
        mock_isfile.return_value = True  # File exists

        result = ftv.FTV._get_api_token("/path/to/token/file")

        self.assertEqual(result, "test_token_content")
        mock_isfile.assert_called_once_with("/path/to/token/file")

    @patch("os.environ.get")
    def test_get_api_token_from_environment(self, mock_env_get) -> None:
        """Test _get_api_token when token is in environment variable."""
        mock_env_get.return_value = "env_token_value"

        result = ftv.FTV._get_api_token("ENV_VAR_NAME")

        self.assertEqual(result, "env_token_value")
        mock_env_get.assert_called_once_with("ENV_VAR_NAME", None)

    def test_get_api_token_empty_input(self) -> None:
        """Test _get_api_token with empty input."""
        result = ftv.FTV._get_api_token("")
        self.assertEqual(result, "")

    @patch("os.environ.get")
    @patch("os.path.isfile")
    def test_get_api_token_fallback_to_input(self, mock_isfile, mock_env_get) -> None:
        """Test _get_api_token falls back to input when not in env or file."""
        mock_env_get.return_value = None  # Not in environment
        mock_isfile.return_value = False  # File doesn't exist

        result = ftv.FTV._get_api_token("direct_token_value")

        self.assertEqual(result, "direct_token_value")

    # -------------------------------------------------------------------------
    # Tests for _get_file_type
    # -------------------------------------------------------------------------
    def test_get_file_type_jpeg_extensions(self) -> None:
        """Test _get_file_type recognizes JPEG extensions (case-sensitive)."""
        test_files = ["image.jpg", "photo.jpeg"]  # Only lowercase as the method is case-sensitive

        for filename in test_files:
            with self.subTest(filename=filename):
                result = self._ftv._get_file_type(filename)
                self.assertEqual(result, ftv.FTVSupportedFileType.JPEG)

    def test_get_file_type_jpeg_extensions_case_sensitive(self) -> None:
        """Test _get_file_type is case-sensitive for JPEG extensions."""
        uppercase_files = ["test.JPG", "file.JPEG"]

        for filename in uppercase_files:
            with self.subTest(filename=filename):
                result = self._ftv._get_file_type(filename)
                self.assertIsNone(result)  # Should return None for uppercase extensions

    def test_get_file_type_png_extension(self) -> None:
        """Test _get_file_type recognizes PNG extension."""
        result = self._ftv._get_file_type("image.png")
        self.assertEqual(result, ftv.FTVSupportedFileType.PNG)

    def test_get_file_type_unsupported_extension(self) -> None:
        """Test _get_file_type returns None for unsupported extensions."""
        unsupported_files = ["image.gif", "file.bmp", "doc.pdf", "noextension"]

        for filename in unsupported_files:
            with self.subTest(filename=filename):
                result = self._ftv._get_file_type(filename)
                self.assertIsNone(result)

    # -------------------------------------------------------------------------
    # Tests for _load_ftv_settings - simplified versions
    # -------------------------------------------------------------------------
    def test_load_ftv_settings_basic_functionality(self) -> None:
        """Test _load_ftv_settings basic functionality through ftvs property."""
        # This test indirectly tests _load_ftv_settings through the ftvs property
        # which we know works from the lazy loading tests

        # Ensure _ftv_settings is None to trigger loading
        self._ftv._ftv_settings = None

        # Mock the loading method to return a simple result
        with patch.object(self._ftv, "_load_ftv_settings", return_value={"test": "data"}):
            result = self._ftv.ftvs
            self.assertEqual(result, {"test": "data"})

    # -------------------------------------------------------------------------
    # Tests for TV operations
    # -------------------------------------------------------------------------
    def test_toggle_power_with_valid_tv(self) -> None:
        """Test _toggle_power with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_shortcuts = mock.Mock()
        mock_ftv_setting.ftv.shortcuts.return_value = mock_shortcuts

        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        self._ftv._toggle_power("test_tv")

        mock_ftv_setting.ftv.shortcuts.assert_called_once()
        mock_shortcuts.power.assert_called_once()

    def test_toggle_power_with_invalid_tv(self) -> None:
        """Test _toggle_power with invalid TV name."""
        self._ftv._ftv_settings = {}

        # Should not raise any exception
        self._ftv._toggle_power("nonexistent_tv")

    def test_browse_to_url_with_valid_tv(self) -> None:
        """Test _browse_to_url with valid TV name."""
        mock_ftv_setting = mock.Mock()
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        self._ftv._browse_to_url("test_tv", "https://example.com")

        mock_ftv_setting.ftv.open_browser.assert_called_once_with("https://example.com")

    def test_browse_to_url_with_invalid_tv(self) -> None:
        """Test _browse_to_url with invalid TV name."""
        self._ftv._ftv_settings = {}

        # Should not raise any exception
        self._ftv._browse_to_url("nonexistent_tv", "https://example.com")

    def test_list_installed_apps_with_valid_tv(self) -> None:
        """Test _list_installed_apps with valid TV name."""
        mock_ftv_setting = mock.Mock()
        expected_apps = ["Netflix", "YouTube", "Disney+"]
        mock_ftv_setting.ftv.app_list.return_value = expected_apps
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        result = self._ftv._list_installed_apps("test_tv")

        self.assertEqual(result, expected_apps)
        mock_ftv_setting.ftv.app_list.assert_called_once()

    def test_list_installed_apps_with_invalid_tv(self) -> None:
        """Test _list_installed_apps with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._list_installed_apps("nonexistent_tv")

        self.assertEqual(result, [])

    def test_open_app_with_valid_tv(self) -> None:
        """Test _open_app with valid TV name."""
        mock_ftv_setting = mock.Mock()
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        self._ftv._open_app("test_tv", ftv.FTVApps.Spotify)

        mock_ftv_setting.ftv.run_app.assert_called_once_with("3201606009684")

    def test_open_app_with_invalid_tv(self) -> None:
        """Test _open_app with invalid TV name."""
        self._ftv._ftv_settings = {}

        # Should not raise any exception
        self._ftv._open_app("nonexistent_tv", ftv.FTVApps.Spotify)

    def test_get_app_status_with_valid_tv(self) -> None:
        """Test _get_app_status with valid TV name."""
        mock_ftv_setting = mock.Mock()
        expected_status = {"running": True, "visible": False}
        mock_ftv_setting.ftv.rest_app_status.return_value = expected_status
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        result = self._ftv._get_app_status("test_tv", ftv.FTVApps.Spotify)

        self.assertEqual(result, expected_status)
        mock_ftv_setting.ftv.rest_app_status.assert_called_once_with("3201606009684")

    def test_get_app_status_with_invalid_tv(self) -> None:
        """Test _get_app_status with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._get_app_status("nonexistent_tv", ftv.FTVApps.Spotify)

        self.assertEqual(result, {})

    def test_close_app_with_valid_tv(self) -> None:
        """Test _close_app with valid TV name."""
        mock_ftv_setting = mock.Mock()
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        self._ftv._close_app("test_tv", ftv.FTVApps.Spotify)

        mock_ftv_setting.ftv.rest_app_close.assert_called_once_with("3201606009684")

    def test_close_app_with_invalid_tv(self) -> None:
        """Test _close_app with invalid TV name."""
        self._ftv._ftv_settings = {}

        # Should not raise any exception
        self._ftv._close_app("nonexistent_tv", ftv.FTVApps.Spotify)

    def test_install_app_with_valid_tv(self) -> None:
        """Test _install_app with valid TV name."""
        mock_ftv_setting = mock.Mock()
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        self._ftv._install_app("test_tv", ftv.FTVApps.Spotify)

        mock_ftv_setting.ftv.rest_app_install.assert_called_once_with("3201606009684")

    def test_install_app_with_invalid_tv(self) -> None:
        """Test _install_app with invalid TV name."""
        self._ftv._ftv_settings = {}

        # Should not raise any exception
        self._ftv._install_app("nonexistent_tv", ftv.FTVApps.Spotify)

    def test_get_device_info_with_valid_tv(self) -> None:
        """Test _get_device_info with valid TV name."""
        mock_ftv_setting = mock.Mock()
        expected_info = {"model": "QN55LS03T", "firmware": "1.2.3"}
        mock_ftv_setting.ftv.rest_device_info.return_value = expected_info
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        result = self._ftv._get_device_info("test_tv")

        self.assertEqual(result, expected_info)
        mock_ftv_setting.ftv.rest_device_info.assert_called_once()

    def test_get_device_info_with_invalid_tv(self) -> None:
        """Test _get_device_info with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._get_device_info("nonexistent_tv")

        self.assertEqual(result, {})

    # -------------------------------------------------------------------------
    # Tests for art mode operations
    # -------------------------------------------------------------------------
    def test_is_art_mode_supported_with_valid_tv(self) -> None:
        """Test _is_art_mode_supported with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        mock_art.supported.return_value = True
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        result = self._ftv._is_art_mode_supported("test_tv")

        self.assertTrue(result)
        mock_ftv_setting.ftv.art.assert_called_once()
        mock_art.supported.assert_called_once()

    def test_is_art_mode_supported_with_invalid_tv(self) -> None:
        """Test _is_art_mode_supported with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._is_art_mode_supported("nonexistent_tv")

        self.assertFalse(result)

    def test_get_current_art_with_valid_tv(self) -> None:
        """Test _get_current_art with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        mock_art.get_current.return_value = "current_artwork.jpg"
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        result = self._ftv._get_current_art("test_tv")

        self.assertEqual(result, "current_artwork.jpg")
        mock_art.get_current.assert_called_once()

    def test_get_current_art_with_invalid_tv(self) -> None:
        """Test _get_current_art with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._get_current_art("nonexistent_tv")

        self.assertEqual(result, "")

    def test_list_art_on_tv_with_valid_tv(self) -> None:
        """Test _list_art_on_tv with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        expected_art_list = ["art1.jpg", "art2.png", "art3.jpeg"]
        mock_art.available.return_value = expected_art_list
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        result = self._ftv._list_art_on_tv("test_tv")

        self.assertEqual(result, expected_art_list)
        mock_art.available.assert_called_once()

    def test_list_art_on_tv_with_invalid_tv(self) -> None:
        """Test _list_art_on_tv with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._list_art_on_tv("nonexistent_tv")

        self.assertEqual(result, [])

    def test_get_current_art_image_with_valid_tv(self) -> None:
        """Test _get_current_art_image with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        mock_art.get_current.return_value = "current.jpg"
        expected_thumbnail = bytearray(b"fake_thumbnail_data")
        mock_art.get_thumbnail.return_value = expected_thumbnail
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        result = self._ftv._get_current_art_image("test_tv")

        self.assertEqual(result, expected_thumbnail)
        mock_art.get_current.assert_called_once()
        mock_art.get_thumbnail.assert_called_once_with("current.jpg")

    def test_get_current_art_image_with_invalid_tv(self) -> None:
        """Test _get_current_art_image with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._get_current_art_image("nonexistent_tv")

        self.assertEqual(result, bytearray())

    def test_set_current_art_image_with_valid_tv(self) -> None:
        """Test _set_current_art_image with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        self._ftv._set_current_art_image("test_tv", "new_art.jpg", show_now=True)

        mock_art.select_image.assert_called_once_with("new_art.jpg", show=True)

    def test_set_current_art_image_with_invalid_tv(self) -> None:
        """Test _set_current_art_image with invalid TV name."""
        self._ftv._ftv_settings = {}

        # Should not raise any exception
        self._ftv._set_current_art_image("nonexistent_tv", "new_art.jpg")

    def test_is_tv_in_art_mode_with_valid_tv(self) -> None:
        """Test _is_tv_in_art_mode with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        mock_art.get_artmode.return_value = True
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        result = self._ftv._is_tv_in_art_mode("test_tv")

        self.assertTrue(result)
        mock_art.get_artmode.assert_called_once()

    def test_is_tv_in_art_mode_with_invalid_tv(self) -> None:
        """Test _is_tv_in_art_mode with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._is_tv_in_art_mode("nonexistent_tv")

        self.assertFalse(result)

    def test_activate_art_mode_with_valid_tv(self) -> None:
        """Test _activate_art_mode with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        self._ftv._activate_art_mode("test_tv", art_mode_on=True)

        mock_art.set_artmode.assert_called_once_with(True)

    def test_activate_art_mode_with_invalid_tv(self) -> None:
        """Test _activate_art_mode with invalid TV name."""
        self._ftv._ftv_settings = {}

        # Should not raise any exception
        self._ftv._activate_art_mode("nonexistent_tv", art_mode_on=True)

    # -------------------------------------------------------------------------
    # Tests for filter operations
    # -------------------------------------------------------------------------
    def test_list_available_filters_with_valid_tv(self) -> None:
        """Test _list_available_filters with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        expected_filters = ["ink", "sepia", "vintage"]
        mock_art.get_photo_filter_list.return_value = expected_filters
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        result = self._ftv._list_available_filters("test_tv")

        self.assertEqual(result, expected_filters)
        mock_art.get_photo_filter_list.assert_called_once()

    def test_list_available_filters_with_invalid_tv(self) -> None:
        """Test _list_available_filters with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._list_available_filters("nonexistent_tv")

        self.assertEqual(result, [])

    def test_apply_filter_to_art_with_valid_tv(self) -> None:
        """Test _apply_filter_to_art with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        self._ftv._apply_filter_to_art("test_tv", "image.jpg", ftv.FTVImageFilters.INK)

        mock_art.set_photo_filter.assert_called_once_with("image.jpg", "ink")

    def test_apply_filter_to_art_with_invalid_tv(self) -> None:
        """Test _apply_filter_to_art with invalid TV name."""
        self._ftv._ftv_settings = {}

        # Should not raise any exception
        self._ftv._apply_filter_to_art("nonexistent_tv", "image.jpg", ftv.FTVImageFilters.INK)

    # -------------------------------------------------------------------------
    # Tests for image file operations
    # -------------------------------------------------------------------------
    def test_delete_image_from_tv_with_valid_tv(self) -> None:
        """Test _delete_image_from_tv with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        self._ftv._delete_image_from_tv("test_tv", "image_to_delete.jpg")

        mock_art.delete.assert_called_once_with("image_to_delete.jpg")

    def test_delete_image_from_tv_with_invalid_tv(self) -> None:
        """Test _delete_image_from_tv with invalid TV name."""
        self._ftv._ftv_settings = {}

        # Should not raise any exception
        self._ftv._delete_image_from_tv("nonexistent_tv", "image.jpg")

    @patch.object(ftv.FTV, "_get_uploaded_image_files")
    @patch.object(ftv.FTV, "_record_uploaded_image_files")
    def test_delete_uploaded_images_from_tv_with_valid_tv(self, mock_record, mock_get_uploaded) -> None:
        """Test _delete_uploaded_images_from_tv with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        # Mock uploaded images
        mock_get_uploaded.return_value = ["image1.jpg", "image2.png"]

        result = self._ftv._delete_uploaded_images_from_tv("test_tv")

        # Verify all images were attempted to be deleted
        self.assertEqual(result, ["image1.jpg", "image2.png"])
        self.assertEqual(mock_art.delete.call_count, 2)
        mock_art.delete.assert_any_call("image1.jpg")
        mock_art.delete.assert_any_call("image2.png")

        # Verify record was updated with empty list
        mock_record.assert_called_once_with("test_tv", [])

    @patch.object(ftv.FTV, "_get_uploaded_image_files")
    def test_delete_uploaded_images_from_tv_with_invalid_tv(self, mock_get_uploaded) -> None:
        """Test _delete_uploaded_images_from_tv with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._delete_uploaded_images_from_tv("nonexistent_tv")

        self.assertEqual(result, [])
        mock_get_uploaded.assert_not_called()

    @patch.object(ftv.FTV, "_get_uploaded_image_files")
    @patch.object(ftv.FTV, "_record_uploaded_image_files")
    def test_delete_uploaded_images_handles_deletion_errors(self, mock_record, mock_get_uploaded) -> None:
        """Test _delete_uploaded_images_from_tv handles individual deletion errors."""
        mock_ftv_setting = mock.Mock()
        mock_art = mock.Mock()
        mock_ftv_setting.ftv.art.return_value = mock_art
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        # Mock uploaded images
        mock_get_uploaded.return_value = ["image1.jpg", "image2.png", "image3.jpeg"]

        # Make second deletion fail
        def delete_side_effect(filename):
            if filename == "image2.png":
                raise Exception("Deletion failed")

        mock_art.delete.side_effect = delete_side_effect

        result = self._ftv._delete_uploaded_images_from_tv("test_tv")

        # Only successful deletions should be in result
        self.assertEqual(result, ["image1.jpg", "image3.jpeg"])

        # Should record remaining images (failed deletion)
        mock_record.assert_called_once_with("test_tv", ["image2.png"])

    # -------------------------------------------------------------------------
    # Tests for file management operations - simplified versions
    # -------------------------------------------------------------------------
    def test_get_uploaded_image_files_invalid_tv(self) -> None:
        """Test _get_uploaded_image_files with invalid TV name."""
        self._ftv._ftv_settings = {}

        result = self._ftv._get_uploaded_image_files("nonexistent_tv")

        self.assertEqual(result, [])

    def test_record_uploaded_image_files_invalid_tv(self) -> None:
        """Test _record_uploaded_image_files with invalid TV name."""
        self._ftv._ftv_settings = {}

        # Should not raise any exception
        self._ftv._record_uploaded_image_files("nonexistent_tv", ["image.jpg"])

    # -------------------------------------------------------------------------
    # Tests for basic FTV operations
    # -------------------------------------------------------------------------
    def test_wake_up_tv_with_valid_tv(self) -> None:
        """Test _wake_up_tv with valid TV name."""
        mock_ftv_setting = mock.Mock()
        mock_ftv_setting.mac_addr = "00:11:22:33:44:55"

        # Set _ftv_settings directly to avoid property mocking issues
        self._ftv._ftv_settings = {"test_tv": mock_ftv_setting}

        with patch("abk_bwp.ftv.wakeonlan.send_magic_packet") as mock_wol:
            self._ftv._wake_up_tv("test_tv")
            mock_wol.assert_called_once_with("00:11:22:33:44:55")

    def test_wake_up_tv_with_invalid_tv(self) -> None:
        """Test _wake_up_tv with invalid TV name."""
        # Set empty _ftv_settings
        self._ftv._ftv_settings = {}

        with patch("abk_bwp.ftv.wakeonlan.send_magic_packet") as mock_wol:
            self._ftv._wake_up_tv("nonexistent_tv")
            mock_wol.assert_not_called()


if __name__ == "__main__":
    unittest.main()

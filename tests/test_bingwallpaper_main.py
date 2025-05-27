"""Tests for main bingwallpaper."""

import unittest
from unittest import mock

from abk_bwp import bingwallpaper


class TestBingWallpaper(unittest.TestCase):
    """Test bingwallpaper main class."""

    def setUp(self):
        """Setup for the bingwallpaper main tests."""
        self.clo = mock.Mock()
        self.clo.logger = mock.Mock()
        self.clo.options = mock.Mock()

    # @unittest.skipUnless(platform.system() == "Darwin", "Only runs on macOS")
    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.bingwallpaper.BingWallPaper")
    @mock.patch("abk_bwp.bingwallpaper.BingDownloadService")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"dl_service": "bing"})
    @mock.patch("abk_bwp.bingwallpaper._platform", "darwin")
    @mock.patch("abk_bwp.bingwallpaper.MacOSDependent")
    def test_mac_bing_success(self, mock_os_dep, mock_dl, mock_bwp, mock_exit):
        """Test test_mac_bing_success."""
        # Arrange
        # ----------------------------------
        from abk_bwp.bingwallpaper import bingwallpaper

        clo = self.clo

        # Act
        # ----------------------------------
        bingwallpaper(clo)

        # Assert
        # ----------------------------------
        mock_os_dep.assert_called_once_with(logger=clo.logger)
        mock_dl.assert_called_once_with(logger=clo.logger)
        mock_bwp.assert_called_once()
        mock_exit.assert_called_once_with(0)

    # @unittest.skipUnless(sys.platform.startswith("linux"), "Linux-specific test")
    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.bingwallpaper.BingWallPaper")
    @mock.patch("abk_bwp.bingwallpaper.BingDownloadService")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"dl_service": "bing"})
    @mock.patch("abk_bwp.bingwallpaper._platform", "linux")
    @mock.patch("abk_bwp.bingwallpaper.LinuxDependent")
    def test_linux_bing_success(self, mock_os_dep, mock_dl, mock_bwp, mock_exit):
        """Test test_linux_bing_success."""
        # Arrange
        # ----------------------------------
        from abk_bwp.bingwallpaper import bingwallpaper

        clo = self.clo

        # Act
        # ----------------------------------
        bingwallpaper(clo)

        # Assert
        # ----------------------------------
        mock_os_dep.assert_called_once_with(logger=clo.logger)
        mock_dl.assert_called_once_with(logger=clo.logger)
        mock_bwp.assert_called_once()
        mock_exit.assert_called_once_with(0)

    # @unittest.skipUnless(sys.platform.startswith("win"), "Windows-specific test")
    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.bingwallpaper.BingWallPaper")
    @mock.patch("abk_bwp.bingwallpaper.BingDownloadService")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"dl_service": "bing"})
    @mock.patch("abk_bwp.bingwallpaper._platform", "win64")
    @mock.patch("abk_bwp.bingwallpaper.WindowsDependent")
    def test_windows_bing_success(self, mock_os_dep, mock_dl, mock_bwp, mock_exit):
        """Test test_windows_bing_success."""
        # Arrange
        # ----------------------------------
        from abk_bwp.bingwallpaper import bingwallpaper

        clo = self.clo

        # Act
        # ----------------------------------
        bingwallpaper(clo)

        # Assert
        # ----------------------------------
        mock_os_dep.assert_called_once_with(logger=clo.logger)
        mock_dl.assert_called_once_with(logger=clo.logger)
        mock_bwp.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.bingwallpaper.bwp_config", {"dl_service": "bing"})
    @mock.patch("abk_bwp.bingwallpaper._platform", "plan9")  # unsupported
    def test_unsupported_platform(self, mock_exit):
        """Test unsupported platform raises ValueError and exits with 1."""
        bingwallpaper.bingwallpaper(self.clo)
        self.clo.logger.error.assert_called()
        mock_exit.assert_called_once_with(1)

    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.bingwallpaper.PeapixDownloadService")
    @mock.patch("abk_bwp.bingwallpaper.BingWallPaper")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"dl_service": "peapix"})
    @mock.patch("abk_bwp.bingwallpaper._platform", "darwin")
    @mock.patch("abk_bwp.bingwallpaper.MacOSDependent")
    def test_peapix_download_service_used(
        self, mock_os_dep, mock_bing_wallpaper, mock_peapix_service, mock_exit
    ):
        """Test that PeapixDownloadService is used when dl_service is set to 'peapix'."""
        # Arrange
        # ----------------------------------
        # Setup a mock clo with a logger and options
        mock_logger = mock.Mock()
        clo = mock.Mock()
        clo.logger = mock_logger
        clo.options = {}
        # Setup mocks
        mock_bwp_instance = mock.Mock()
        mock_bing_wallpaper.return_value = mock_bwp_instance

        # Act
        # ----------------------------------
        # Run the main function
        bingwallpaper.bingwallpaper(clo)

        # Assert
        # ----------------------------------
        mock_os_dep.assert_called_once_with(logger=mock_logger)
        # Assert PeapixDownloadService was instantiated
        mock_peapix_service.assert_called_once_with(logger=mock_logger)
        # Verify that BingWallPaper was called with the correct dl_service
        mock_bing_wallpaper.assert_called_once()
        _, kwargs = mock_bing_wallpaper.call_args
        self.assertEqual(kwargs.get("dl_service"), mock_peapix_service.return_value)
        # Ensure download was attempted and exit called
        mock_bwp_instance.download_new_images.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @mock.patch("sys.exit")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"dl_service": "invalid_service"})
    @mock.patch("abk_bwp.bingwallpaper._platform", "darwin")
    @mock.patch("abk_bwp.bingwallpaper.MacOSDependent")
    def test_invalid_dl_service(self, mock_os_dep, mock_exit):
        """Test invalid download service raises ValueError and exits with 1."""
        # Arrange
        # ----------------------------------
        with (
            mock.patch("abk_bwp.bingwallpaper.BingWallPaper"),
            mock.patch("abk_bwp.bingwallpaper.clo.CommandLineOptions"),
        ):
            from abk_bwp import bingwallpaper

            # Act
            # ----------------------------------
            bingwallpaper.bingwallpaper(self.clo)

        # Assert
        # ----------------------------------
        self.clo.logger.error.assert_called()  # or assert_called_once_with(...)
        mock_exit.assert_called_once_with(1)

    @mock.patch("abk_bwp.bingwallpaper.FTV")
    @mock.patch("abk_bwp.bingwallpaper.get_config_ftv_data", return_value="mocked_ftv_data_file")
    @mock.patch(
        "abk_bwp.bingwallpaper.BingWallPaper.prepare_ftv_images", return_value=["img1", "img2"]
    )
    @mock.patch("abk_bwp.bingwallpaper.is_config_ftv_enabled", return_value=True)
    @mock.patch("abk_bwp.bingwallpaper.BingWallPaper")
    @mock.patch("abk_bwp.bingwallpaper.PeapixDownloadService")
    @mock.patch("abk_bwp.bingwallpaper.MacOSDependent")
    @mock.patch("sys.exit")
    def test_is_config_ftv_enabled_triggers_ftv_flow(
        self,
        mock_exit,
        mock_mac_os,
        mock_peapix_dl,
        mock_bwp_class,
        mock_is_enabled,
        mock_prepare_images,
        mock_get_ftv_data,
        mock_ftv_class,
    ):
        """Test that FTV logic runs when is_config_ftv_enabled returns True."""
        # Arrange
        # ----------------------------------
        # Patch internal config and platform inside test
        with (
            mock.patch.dict(bingwallpaper.bwp_config, {"dl_service": "peapix"}),
            mock.patch("abk_bwp.bingwallpaper._platform", "darwin"),
        ):
            # Setup clo
            mock_logger = mock.Mock()
            clo = mock.Mock()
            clo.logger = mock_logger
            clo.options = {}

            # Setup BingWallPaper instance
            mock_bwp_instance = mock.Mock()
            mock_bwp_class.return_value = mock_bwp_instance
            mock_ftv_instance = mock.Mock()
            mock_ftv_class.return_value = mock_ftv_instance

            # Act
            # ----------------------------------
            # Run the main function
            bingwallpaper.bingwallpaper(clo)

            # Assert
            # ----------------------------------
            # Assertions
            mock_mac_os.assert_called_once_with(logger=mock_logger)
            mock_peapix_dl.assert_called_once_with(logger=mock_logger)
            mock_is_enabled.assert_called_once()
            mock_prepare_images.assert_called_once()
            mock_get_ftv_data.assert_called_once()
            mock_ftv_class.assert_called_once_with(
                logger=mock_logger, ftv_data_file="mocked_ftv_data_file"
            )
            mock_ftv_instance.change_daily_images.assert_called_once_with(["img1", "img2"])
            mock_exit.assert_called_once_with(0)

    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.bingwallpaper.BingDownloadService")
    @mock.patch("abk_bwp.bingwallpaper.BingWallPaper")
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"dl_service": "bing"})
    @mock.patch("abk_bwp.bingwallpaper._platform", "darwin")
    @mock.patch("abk_bwp.bingwallpaper.MacOSDependent")
    def test_exception_logging(
        self, mock_os_dep, mock_bing_wallpaper, mock_dl_service, mock_exit
    ):
        """Test that if an exception occurs, it is logged and exit code is 1."""
        # Arrange
        # ----------------------------------
        self.clo.logger = mock.Mock()
        # Create the BingWallPaper mock and set the side effect
        mock_bwp_instance = mock.Mock()
        mock_bwp_instance.download_new_images.side_effect = Exception("fail!")
        mock_bing_wallpaper.return_value = mock_bwp_instance

        # Act
        # ----------------------------------
        # Call the main function
        bingwallpaper.bingwallpaper(self.clo)

        # Assert
        # ----------------------------------
        mock_os_dep.assert_called_once_with(logger=self.clo.logger)
        mock_dl_service.assert_called_once_with(logger=self.clo.logger)
        # Assert error logging and exit
        self.clo.logger.error.assert_called()
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()

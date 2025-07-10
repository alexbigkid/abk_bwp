"""Tests for main uninstall."""

import unittest
from unittest import mock


# =============================================================================
# UninstallOnWindows
# =============================================================================
class TestBwpUninstall(unittest.TestCase):
    """TestUninstallOnWindows class."""

    def setUp(self):
        """Setup for the uninstall main tests."""
        self.clo = mock.Mock()
        self.clo.options = mock.Mock()
        self.clo.logger = mock.Mock()

    # -------------------------------------------------------------------------
    # TestBwpUninstall.test_bwp_uninstall_mac
    # -------------------------------------------------------------------------
    # @unittest.skipUnless(platform.system() == "Darwin", "Only runs on macOS")
    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.uninstall.UninstallOnMacOS")
    def test_bwp_uninstall_mac(self, mock_uninstall_on_mac, mock_sys_exit):
        """Test macOS platform path through bwp_uninstall()."""
        # Arrange
        # ----------------------------------
        # Import inside to re-evaluate _platform correctly after patching
        with mock.patch("abk_bwp.uninstall._platform", new="darwin"):
            from abk_bwp.uninstall import bwp_uninstall

            # Act
            # ----------------------------------
            bwp_uninstall(self.clo.logger)

        # Assert
        # ----------------------------------
        mock_uninstall_on_mac.assert_called_once_with(logger=self.clo.logger)
        mock_uninstall_on_mac.return_value.cleanup_image_dir.assert_not_called()
        mock_uninstall_on_mac.return_value.teardown_installation.assert_called_once()
        mock_sys_exit.assert_called_once_with(0)

    # @unittest.skipUnless(sys.platform.startswith("linux"), "Linux-specific test")
    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.uninstall.UninstallOnLinux")
    def test_bwp_uninstall_linux(self, mock_uninstall_on_linux, mock_sys_exit):
        """Test linux platform path through bwp_uninstall()."""
        # Arrange
        # ----------------------------------
        # Import inside to re-evaluate _platform correctly after patching
        with mock.patch("abk_bwp.uninstall._platform", new="linux"):
            from abk_bwp.uninstall import bwp_uninstall

            # Act
            # ----------------------------------
            bwp_uninstall(self.clo.logger)

        # Assert
        # ----------------------------------
        mock_uninstall_on_linux.assert_called_once_with(logger=self.clo.logger)
        mock_uninstall_on_linux.return_value.cleanup_image_dir.assert_not_called()
        mock_uninstall_on_linux.return_value.teardown_installation.assert_called_once()
        mock_sys_exit.assert_called_once_with(0)

    # @unittest.skipUnless(sys.platform.startswith("win"), "Windows-specific test")
    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.uninstall.UninstallOnWindows")
    def test_bwp_uninstall_windows(self, mock_uninstall_on_windows, mock_sys_exit):
        """Test windows platform path through bwp_uninstall()."""
        # Arrange
        # ----------------------------------
        # Import inside to re-evaluate _platform correctly after patching
        with mock.patch("abk_bwp.uninstall._platform", new="win64"):
            from abk_bwp.uninstall import bwp_uninstall

            # Act
            # ----------------------------------
            bwp_uninstall(self.clo.logger)

        # Assert
        # ----------------------------------
        mock_uninstall_on_windows.assert_called_once_with(logger=self.clo.logger)
        mock_uninstall_on_windows.return_value.cleanup_image_dir.assert_not_called()
        mock_uninstall_on_windows.return_value.teardown_installation.assert_called_once()
        mock_sys_exit.assert_called_once_with(0)

    @mock.patch("sys.exit")
    def test_unsupported_platform(self, mock_exit):
        """Test unsupported platform raises ValueError and exits with 1."""
        # Arrange
        # ----------------------------------
        with mock.patch("abk_bwp.uninstall._platform", new="plan9"):
            from abk_bwp.uninstall import bwp_uninstall

            # Act
            # ----------------------------------
            logger = self.clo.logger
            bwp_uninstall(logger)

        # Assert
        # ----------------------------------
        logger.exception.assert_called()
        mock_exit.assert_called_once_with(1)

    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.uninstall.UninstallOnLinux")
    @mock.patch("abk_bwp.uninstall.bwp_config", {"retain_images": False, "image_dir": "/fake/image/dir"})
    def test_bwp_uninstall_calls_cleanup_image_dir(self, mock_uninstall_on_linux, mock_exit):
        """Ensure cleanup_image_dir() is called when retain_images is False."""
        # Arrange
        # ----------------------------------
        with mock.patch("abk_bwp.uninstall._platform", new="linux"):
            from abk_bwp.uninstall import bwp_uninstall

            mock_logger = mock.Mock()

            # Act
            # ----------------------------------
            bwp_uninstall(mock_logger)

        # Assert
        # ----------------------------------
        mock_uninstall_on_linux.return_value.cleanup_image_dir.assert_called_once_with("/fake/image/dir")
        mock_uninstall_on_linux.return_value.teardown_installation.assert_called_once()
        mock_uninstall_on_linux.assert_called_once_with(logger=mock_logger)
        mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()

"""Tests for main install."""

import unittest
from unittest import mock


# =============================================================================
# InstallOnWindows
# =============================================================================
class TestBwpInstall(unittest.TestCase):
    """TestInstallOnWindows class."""

    def setUp(self):
        """Setup for the install main tests."""
        self.clo = mock.Mock()
        self.clo.options = mock.Mock()
        self.clo.logger = mock.Mock()

    # -------------------------------------------------------------------------
    # TestBwpInstall.test_bwp_install_mac
    # -------------------------------------------------------------------------
    # @unittest.skipUnless(platform.system() == "Darwin", "Only runs on macOS")
    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.install.InstallOnMacOS")
    def test_bwp_install_mac(self, mock_install_on_mac, mock_sys_exit):
        """Test macOS platform path through bwp_install()."""
        # Arrange
        # ----------------------------------
        # Import inside to re-evaluate _platform correctly after patching
        with mock.patch("abk_bwp.install._platform", new="darwin"):
            from abk_bwp.install import bwp_install

            # Act
            # ----------------------------------
            bwp_install(self.clo.logger)

        # Assert
        # ----------------------------------
        # Check that InstallOnMacOS was called with correct logger
        mock_install_on_mac.assert_called_once_with(logger=self.clo.logger)
        # Check that setup_installation was called
        mock_install_on_mac.return_value.setup_installation.assert_called_once()
        # Check exit code was 0
        mock_sys_exit.assert_called_once_with(0)

    # @unittest.skipUnless(sys.platform.startswith("linux"), "Linux-specific test")
    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.install.InstallOnLinux")
    def test_bwp_install_linux(self, mock_install_on_linux, mock_sys_exit):
        """Test linux platform path through bwp_install()."""
        # Arrange
        # ----------------------------------
        # Import inside to re-evaluate _platform correctly after patching
        with mock.patch("abk_bwp.install._platform", new="linux"):
            from abk_bwp.install import bwp_install

            # Act
            # ----------------------------------
            bwp_install(self.clo.logger)

        # Assert
        # ----------------------------------
        # Check that InstallOnMacOS was called with correct logger
        mock_install_on_linux.assert_called_once_with(logger=self.clo.logger)
        # Check that setup_installation was called
        mock_install_on_linux.return_value.setup_installation.assert_called_once()
        # Check exit code was 0
        mock_sys_exit.assert_called_once_with(0)

    # @unittest.skipUnless(sys.platform.startswith("win"), "Windows-specific test")
    @mock.patch("sys.exit")
    @mock.patch("abk_bwp.install.InstallOnWindows")
    def test_bwp_install_windows(self, mock_install_on_windows, mock_sys_exit):
        """Test windows platform path through bwp_install()."""
        # Arrange
        # ----------------------------------
        # Import inside to re-evaluate _platform correctly after patching
        with mock.patch("abk_bwp.install._platform", new="win64"):
            from abk_bwp.install import bwp_install

            # Act
            # ----------------------------------
            bwp_install(self.clo.logger)

        # Assert
        # ----------------------------------
        # Check that InstallOnMacOS was called with correct logger
        mock_install_on_windows.assert_called_once_with(logger=self.clo.logger)
        # Check that setup_installation was called
        mock_install_on_windows.return_value.setup_installation.assert_called_once()
        # Check exit code was 0
        mock_sys_exit.assert_called_once_with(0)

    @mock.patch("sys.exit")
    def test_unsupported_platform(self, mock_exit):
        """Test unsupported platform raises ValueError and exits with 1."""
        with mock.patch("abk_bwp.install._platform", new="plan9"):
            from abk_bwp.install import bwp_install

            logger = self.clo.logger  # Use the actual logger mock
            bwp_install(logger)

        logger.error.assert_called()  # Confirm logger was used
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()

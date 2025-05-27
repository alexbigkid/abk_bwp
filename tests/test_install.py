"""Unit tests for install.py."""

# Standard library imports
import os
import unittest
from unittest import mock
import logging
from datetime import time

# Third party imports

# Local imports
from abk_bwp.install import IInstallBase, InstallOnMacOS
from abk_bwp import abk_common


class DummyInstall(IInstallBase):
    """Concrete subclass of IInstallBase for testing."""

    os_type = abk_common.OsType.LINUX_OS

    def setup_installation(self):
        """Dummy implementation for abstract method."""
        pass


class DummyInstallWindows(IInstallBase):
    """Windows-specific subclass for testing."""

    os_type = abk_common.OsType.WINDOWS_OS

    def setup_installation(self):
        """Dummy implementation for abstract method."""
        pass


# =============================================================================
# IInstallBase
# =============================================================================
class TestInstallBase(unittest.TestCase):
    """TestInstallBase."""

    mut = None

    def setUp(self) -> None:
        """Set up tests for install."""
        self.maxDiff = None
        return super().setUp()

    def test_shell_file_name_linux(self):
        """Test shell file name generation for Linux."""
        inst = DummyInstall()
        self.assertEqual(inst.shell_file_name, f"{abk_common.BWP_APP_NAME}.sh")
        # Ensure caching works
        self.assertEqual(inst._shell_file_name, f"{abk_common.BWP_APP_NAME}.sh")

    def test_shell_file_name_windows(self):
        """Test shell file name generation for Windows."""
        inst = DummyInstallWindows()
        self.assertEqual(inst.shell_file_name, f"{abk_common.BWP_APP_NAME}.ps1")
        self.assertEqual(inst._shell_file_name, f"{abk_common.BWP_APP_NAME}.ps1")

    @mock.patch("logging.getLogger")
    def test_logger_is_used_when_none_provided(self, mock_get_logger):
        """Test default logger is used if none is provided."""
        dummy_logger = mock.Mock()
        mock_get_logger.return_value = dummy_logger

        inst = DummyInstall()

        dummy_logger.info.assert_called_once()
        self.assertIs(inst._logger, dummy_logger)

    def test_custom_logger_is_used(self):
        """Test that a custom logger is used if provided."""
        custom_logger = mock.Mock(spec=logging.Logger)
        inst = DummyInstall(logger=custom_logger)

        custom_logger.info.assert_called_once()
        self.assertIs(inst._logger, custom_logger)


# =============================================================================
# InstallOnMacOS
# =============================================================================
class TestInstallOnMacOS(unittest.TestCase):
    """TestInstallOnMacOS class."""

    @mock.patch("abk_bwp.install.IInstallBase.__init__", return_value=None)
    def test_init_sets_os_type_and_calls_super(self, mock_super_init):
        """Test test_init_sets_os_type_and_calls_super."""
        logger = mock.Mock()
        installer = InstallOnMacOS(logger)
        self.assertEqual(installer.os_type, abk_common.OsType.MAC_OS)
        mock_super_init.assert_called_once_with(logger)

    # -------------------------------------------------------------------------
    # InstallOnMacOS.setup_installation
    # -------------------------------------------------------------------------
    @mock.patch.dict("abk_bwp.bingwallpaper.bwp_config", {"time_to_fetch": time(12, 0, 0)})
    @mock.patch("abk_bwp.install.InstallOnMacOS._load_and_start_bingwallpaper_job")
    @mock.patch("abk_bwp.install.InstallOnMacOS._stop_and_unload_bingwallpaper_job")
    @mock.patch("abk_bwp.install.InstallOnMacOS._create_plist_link")
    @mock.patch("abk_bwp.install.InstallOnMacOS._create_plist_file")
    @mock.patch("os.path.dirname", return_value=os.path.join("/fake", "path"))
    def test_setup_installation(
        self,
        mock_dirname,
        mock_create_plist_file,
        mock_create_plist_link,
        mock_stop_unload,
        mock_load_start,
        # mock_config_get,
        # mock_datetime,
    ):
        """Test test_setup_installation."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        installer = InstallOnMacOS(mock_logger)
        installer._logger = mock_logger
        installer.os_type = abk_common.OsType.MAC_OS
        installer._shell_file_name = "bingwallpaper.sh"
        com_name = "com.abk.bingwallpaper"
        mock_create_plist_file.return_value = com_name
        plist_name = os.path.join(
            "/fake", "path", "com.abk.bingwallpaper.plist"
        )
        mock_create_plist_link.return_value = plist_name

        # Act
        # ----------------------------------
        installer.setup_installation()

        # Assert
        # ----------------------------------
        mock_dirname.assert_called_once()
        mock_logger.debug.assert_called()
        mock_create_plist_file.assert_called_once_with(time(12, 0, 0), "bingwallpaper.sh")
        mock_create_plist_link.assert_called_once_with(plist_name)
        mock_stop_unload.assert_called_once_with(plist_name, com_name)
        mock_load_start.assert_called_once_with(plist_name, com_name)


if __name__ == "__main__":
    unittest.main()

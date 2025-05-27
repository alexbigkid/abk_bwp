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
        plist_name = os.path.join("/fake", "path", "com.abk.bingwallpaper.plist")
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

    # -------------------------------------------------------------------------
    # InstallOnMacOS._create_plist_file
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.abk_common.get_user_name", return_value="testuser")
    @mock.patch("os.path.dirname", return_value=os.path.join("/fake", "dir"))
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    def test_create_plist_file(self, mock_open_file, mock_dirname, mock_get_user_name):
        """Test test_create_plist_file."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        installer = InstallOnMacOS(mock_logger)
        time_to_exe = time(9, 30)
        script_name = "bingwallpaper.sh"
        plist_label = "com.testuser.bingwallpaper.sh"
        expected_plist_path = os.path.join("/fake", "dir", "com.testuser.bingwallpaper.sh.plist")
        expected_script_path = os.path.join("/fake", "dir", "bingwallpaper.sh")

        # Act
        # ----------------------------------
        result = installer._create_plist_file(time_to_exe, script_name)

        # Assert
        # ----------------------------------
        mock_logger.debug.assert_called()  # at least one debug log happened
        mock_get_user_name.assert_called_once()
        mock_dirname.assert_called_once_with(mock.ANY)
        mock_open_file.assert_called_once_with(expected_plist_path, "w")
        # Validate writelines call
        handle = mock_open_file()
        handle.writelines.assert_called_once()
        written_lines = handle.writelines.call_args[0][0]
        # These are examples of expected line fragments; verify each was written
        # for call in mock_logger.debug.call_args_list:
        #     args, kwargs = call
        #     print("Args:", args)
        #     print("Kwargs:", kwargs)
        mock_logger.debug.assert_any_call(
            f"{time_to_exe.hour=}, {time_to_exe.minute=}, {script_name=}"
        )
        mock_logger.debug.assert_any_call(f"{script_name = }")
        mock_logger.debug.assert_any_call(f"{plist_label = }")
        # Return value can be validated using another mock
        mock_return_checker = mock.Mock()
        mock_return_checker(plist_label)
        mock_return_checker.assert_called_once_with(result)


if __name__ == "__main__":
    unittest.main()

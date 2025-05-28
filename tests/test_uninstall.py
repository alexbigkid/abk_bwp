"""Unit tests for uninstall.py."""

# Standard library imports
import logging
import unittest
from unittest import mock

from abk_bwp import abk_common
from abk_bwp.uninstall import IUninstallBase, UninstallOnMacOS

# Third party imports

# Local imports
# from context import uninstall


class DummyUninstall(IUninstallBase):
    """Concrete subclass of IUninstallBase for testing."""

    os_type = abk_common.OsType.LINUX_OS

    def teardown_installation(self):
        """Dummy implementation for abstract method."""
        pass

    def cleanup_image_dir(self):
        """Dummy implementation for abstract method."""
        pass


class DummyUninstallWindows(IUninstallBase):
    """Windows-specific subclass for testing."""

    os_type = abk_common.OsType.WINDOWS_OS

    def teardown_installation(self):
        """Dummy implementation for abstract method."""
        pass

    def cleanup_image_dir(self):
        """Dummy implementation for abstract method."""
        pass


# =============================================================================
# IUninstallBase
# =============================================================================
class TestUninstall(unittest.TestCase):
    """TestUninstall."""

    mut = None

    def setUp(self) -> None:
        """Set up tests.

        Returns:
            _type_: _description_
        """
        self.maxDiff = None
        return super().setUp()

    def test_shell_file_name_linux(self):
        """Test shell file name generation for Linux."""
        uninstall = DummyUninstall()
        self.assertEqual(uninstall.shell_file_name, f"{abk_common.BWP_APP_NAME}.sh")
        # Ensure caching works
        self.assertEqual(uninstall._shell_file_name, f"{abk_common.BWP_APP_NAME}.sh")

    def test_shell_file_name_windows(self):
        """Test shell file name generation for Windows."""
        inst = DummyUninstallWindows()
        self.assertEqual(inst.shell_file_name, f"{abk_common.BWP_APP_NAME}.ps1")
        self.assertEqual(inst._shell_file_name, f"{abk_common.BWP_APP_NAME}.ps1")

    @mock.patch("logging.getLogger")
    def test_logger_is_used_when_none_provided(self, mock_get_logger):
        """Test default logger is used if none is provided."""
        dummy_logger = mock.Mock()
        mock_get_logger.return_value = dummy_logger

        inst = DummyUninstall()

        dummy_logger.info.assert_called_once()
        self.assertIs(inst._logger, dummy_logger)

    def test_custom_logger_is_used(self):
        """Test that a custom logger is used if provided."""
        custom_logger = mock.Mock(spec=logging.Logger)
        inst = DummyUninstall(logger=custom_logger)

        custom_logger.info.assert_called_once()
        self.assertIs(inst._logger, custom_logger)


# =============================================================================
# UninstallOnMacOS
# =============================================================================
class TestUninstallOnMacOS(unittest.TestCase):
    """TestUninstallOnMacOS class."""

    @mock.patch("abk_bwp.uninstall.IUninstallBase.__init__", return_value=None)
    def test_init_sets_os_type_and_calls_super(self, mock_super_init):
        """Test test_init_sets_os_type_and_calls_super."""
        logger = mock.Mock()
        installer = UninstallOnMacOS(logger)
        self.assertEqual(installer.os_type, abk_common.OsType.MAC_OS)
        mock_super_init.assert_called_once_with(logger)

    # -------------------------------------------------------------------------
    # UninstallOnMacOS.test_teardown_installation
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.uninstall.UninstallOnMacOS._delete_plist_file")
    @mock.patch("abk_bwp.abk_common.remove_link")
    @mock.patch("abk_bwp.uninstall.UninstallOnMacOS._stop_and_unload_bingwallpaper_job")
    @mock.patch("abk_bwp.abk_common.get_home_dir", return_value="/Users/testuser")
    @mock.patch("os.path.dirname", return_value="/path/to")
    @mock.patch("os.path.basename", return_value="bingwallpaper.sh")
    @mock.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    @mock.patch("abk_bwp.abk_common.get_current_dir", return_value="/path/to")
    @mock.patch.object(UninstallOnMacOS, "shell_file_name", new_callable=mock.PropertyMock)
    def test_teardown_installation(
        self,
        mock_shell_file_name,
        mock_get_current_dir,
        mock_join,
        mock_basename,
        mock_dirname,
        mock_get_home_dir,
        mock_stop_and_unload,
        mock_remove_link,
        mock_delete_file,
    ):
        """Test test_teardown_installation."""
        # Arrange
        # ----------------------------------
        mock_shell_file_name.return_value = "bingwallpaper.sh"
        mock_logger = mock.Mock()
        uninstall = UninstallOnMacOS(logger=mock_logger)
        uninstall._get_plist_names = mock.Mock(
            return_value=("com.bwp.agent", "com.bwp.agent.plist")
        )

        # Act
        # ----------------------------------
        uninstall.teardown_installation()

        # Assert: method calls
        # ----------------------------------
        mock_get_current_dir.assert_called_once()
        self.assertEqual(mock_join.call_count, 3)
        expected_calls = [
            mock.call("/path/to", "bingwallpaper.sh"),
            mock.call("/Users/testuser/Library/LaunchAgents", "com.bwp.agent.plist"),
            mock.call("/path/to", "com.bwp.agent.plist"),
        ]
        mock_join.assert_has_calls(expected_calls, any_order=False)
        mock_dirname.assert_called_once_with("/path/to/bingwallpaper.sh")
        mock_basename.assert_called_once_with("/path/to/bingwallpaper.sh")
        mock_dirname.assert_called_once_with("/path/to/bingwallpaper.sh")
        uninstall._get_plist_names.assert_called_once_with("bingwallpaper.sh")
        mock_get_home_dir.assert_called_once()
        mock_stop_and_unload.assert_called_once_with(
            "/Users/testuser/Library/LaunchAgents/com.bwp.agent.plist", "com.bwp.agent"
        )
        mock_remove_link.assert_called_once_with(
            "/Users/testuser/Library/LaunchAgents/com.bwp.agent.plist"
        )
        mock_delete_file.assert_called_once_with("/path/to/com.bwp.agent.plist")
        # Assert: logging occurred
        mock_logger.info.assert_called()
        mock_logger.debug.called_called()


if __name__ == "__main__":
    unittest.main()

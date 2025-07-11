"""Unit tests for uninstall.py."""

# Standard library imports
import logging
import subprocess  # noqa: S404
import unittest
from pathlib import Path
from unittest import mock

from abk_bwp import abk_common
from abk_bwp.uninstall import IUninstallBase, UninstallOnLinux, UninstallOnMacOS, UninstallOnWindows

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
        uninstall._get_plist_names = mock.Mock(return_value=("com.bwp.agent", "com.bwp.agent.plist"))

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
        mock_stop_and_unload.assert_called_once_with("/Users/testuser/Library/LaunchAgents/com.bwp.agent.plist", "com.bwp.agent")
        mock_remove_link.assert_called_once_with("/Users/testuser/Library/LaunchAgents/com.bwp.agent.plist")
        mock_delete_file.assert_called_once_with("/path/to/com.bwp.agent.plist")
        # Assert: logging occurred
        mock_logger.info.assert_called()
        mock_logger.debug.called_called()

    # -------------------------------------------------------------------------
    # UninstallOnMacOS.cleanup_image_dir
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.abk_common.get_home_dir", return_value="/Users/testuser")
    def test_cleanup_image_dir(self, mock_get_home_dir):
        """Test cleanup_image_dir calls _delete_image_dir with correct path."""
        # Arrange
        # ----------------------------------
        uninstall = UninstallOnMacOS(logger=mock.Mock())
        uninstall._delete_image_dir = mock.Mock()

        # Act
        # ----------------------------------
        uninstall.cleanup_image_dir("Pictures/BingWallpapers")

        # Assert
        # ----------------------------------
        mock_get_home_dir.assert_called_once()
        # The actual implementation uses Path(home_dir).joinpath(image_dir)
        # Match exactly what the actual code does
        expected_path = str(Path("/Users/testuser").joinpath("Pictures/BingWallpapers"))
        uninstall._delete_image_dir.assert_called_once_with(expected_path)

    # -------------------------------------------------------------------------
    # UninstallOnMacOS._delete_image_dir
    # -------------------------------------------------------------------------
    @mock.patch("shutil.rmtree")
    @mock.patch("os.path.isdir", return_value=True)
    def test_delete_image_dir_success(self, mock_isdir, mock_rmtree):
        """Test _delete_image_dir deletes directory if it exists."""
        # Arrange
        # ----------------------------------
        logger = mock.Mock()
        uninstall = UninstallOnMacOS(logger=logger)

        # Act
        # ----------------------------------
        uninstall._delete_image_dir("/path/to/images")

        # Assert
        # ----------------------------------
        mock_isdir.assert_called_once_with("/path/to/images")
        mock_rmtree.assert_called_once_with("/path/to/images")
        logger.exception.assert_not_called()

    @mock.patch("abk_bwp.uninstall.shutil.rmtree", side_effect=Exception("fail"))
    @mock.patch("abk_bwp.uninstall.os.path.isdir", return_value=True)
    def test_delete_image_dir_failure(self, mock_isdir, mock_rmtree):
        """Test _delete_image_dir logs exception if deletion fails."""
        # Arrange
        # ----------------------------------
        logger = mock.Mock()
        uninstall = UninstallOnMacOS(logger=logger)

        # Act
        # ----------------------------------
        uninstall._delete_image_dir("/path/to/images")

        # Assert
        # ----------------------------------
        mock_isdir.assert_called_once_with("/path/to/images")
        mock_rmtree.assert_called_once_with("/path/to/images")
        logger.exception.assert_called_once_with("deleting image directory /path/to/images failed")

    # -------------------------------------------------------------------------
    # UninstallOnMacOS._get_plist_names
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.abk_common.get_user_name", return_value="testuser")
    def test_get_plist_names(self, mock_get_user_name):
        """Test _get_plist_names returns correct label and filename."""
        # Arrange
        # ----------------------------------
        logger = mock.Mock()
        uninstall = UninstallOnMacOS(logger=logger)

        # Act
        # ----------------------------------
        result = uninstall._get_plist_names("bingwallpaper.sh")

        # Assert
        # ----------------------------------
        self.assertEqual(result, ("com.testuser.bingwallpaper.sh", "com.testuser.bingwallpaper.sh.plist"))
        logger.debug.assert_any_call("script_name='bingwallpaper.sh'")
        logger.debug.assert_any_call(
            "plist_label='com.testuser.bingwallpaper.sh', plist_file_name='com.testuser.bingwallpaper.sh.plist'"  # noqa: E501
        )
        mock_get_user_name.assert_called_once()

    # -------------------------------------------------------------------------
    # UninstallOnMacOS._stop_and_unload_bingwallpaper_job
    # -------------------------------------------------------------------------
    @mock.patch("subprocess.check_call")
    def test_stop_and_unload_bingwallpaper_job_success(self, mock_check_call):
        """Test successful execution of stop and unload job."""
        # Arrange
        # ----------------------------------
        logger = mock.Mock(spec=["debug", "info", "error"])
        uninstall = UninstallOnMacOS(logger=logger)
        plist_label = "com.testuser.bingwallpaper.sh"
        plist_name = f"/Users/testuser/Library/LaunchAgents/{plist_label}.plist"

        # Act
        # ----------------------------------
        uninstall._stop_and_unload_bingwallpaper_job(plist_name, plist_label)

        # Assert
        # ----------------------------------
        expected_calls = [
            mock.call(f"launchctl list | grep {plist_label}", shell=True),  # noqa: S604
            mock.call(f"launchctl stop {plist_label}", shell=True),  # noqa: S604
            mock.call(f"launchctl unload -w {plist_name}", shell=True),  # noqa: S604
        ]
        self.assertEqual(mock_check_call.call_args_list, expected_calls)
        self.assertEqual(mock_check_call.call_count, 3)

    @mock.patch("abk_bwp.uninstall.subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "launchctl"))
    def test_stop_and_unload_bingwallpaper_job_failure(self, mock_check_call):
        """Test error handling when command fails."""
        # Arrange
        # ----------------------------------
        logger = mock.Mock()
        uninstall = UninstallOnMacOS(logger=logger)
        plist_name = "/Users/testuser/Library/LaunchAgents/com.testuser.bingwallpaper.sh.plist"
        plist_label = "com.testuser.bingwallpaper.sh"

        # Act
        # ----------------------------------
        uninstall._stop_and_unload_bingwallpaper_job(plist_name, plist_label)

        # Assert
        # ----------------------------------
        logger.exception.assert_called_once_with("ERROR: returned: 1")

    # -------------------------------------------------------------------------
    # UninstallOnMacOS._delete_plist_file
    # -------------------------------------------------------------------------
    @mock.patch("os.unlink")
    @mock.patch("os.path.isfile", return_value=True)
    def test_delete_plist_file_success(self, mock_isfile, mock_unlink):
        """Test test_delete_plist_file_success."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        uninstall = UninstallOnMacOS(logger=mock_logger)
        script_name = "/Users/testuser/Library/LaunchAgents/com.example.plist"

        # Act
        # ----------------------------------
        uninstall._delete_plist_file(script_name)

        # Assert
        # ----------------------------------
        mock_isfile.assert_called_once_with(script_name)
        mock_unlink.assert_called_once_with(script_name)
        mock_logger.info.assert_called_with(f"deleted file {script_name}")

    @mock.patch("os.unlink", side_effect=OSError(13, "Permission denied"))
    @mock.patch("os.path.isfile", return_value=True)
    def test_delete_plist_file_oserror(self, mock_isfile, mock_unlink):
        """Test test_delete_plist_file_oserror."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        uninstall = UninstallOnMacOS(logger=mock_logger)
        script_name = "/Users/testuser/Library/LaunchAgents/com.example.plist"

        # Act
        # ----------------------------------
        uninstall._delete_plist_file(script_name)

        # Assert
        # ----------------------------------
        mock_isfile.assert_called_once_with(script_name)
        mock_unlink.assert_called_once_with(script_name)
        mock_logger.exception.assert_called_once()
        mock_logger.exception.assert_called_once_with(f"failed to delete file {script_name}, with error = 13")

    @mock.patch("abk_bwp.uninstall.os.path.isfile", return_value=False)
    def test_delete_plist_file_does_not_exist(self, mock_isfile):
        """Test test_delete_plist_file_does_not_exist."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        uninstall = UninstallOnMacOS(logger=mock_logger)
        script_name = "/Users/testuser/Library/LaunchAgents/com.example.plist"

        # Act
        # ----------------------------------
        uninstall._delete_plist_file(script_name)

        # Assert
        # ----------------------------------
        mock_isfile.assert_called_once_with(script_name)
        mock_logger.info.assert_called_with(f"file {script_name} does not exist")


# =============================================================================
# UninstallOnLinux
# =============================================================================
class TestUninstallOnLinux(unittest.TestCase):
    """TestUninstallOnLinux class."""

    def test_init_sets_os_type(self):
        """Test test_init_sets_os_type."""
        mock_logger = mock.Mock()
        uninstall = UninstallOnLinux(logger=mock_logger)

        self.assertEqual(uninstall.os_type, abk_common.OsType.LINUX_OS)
        self.assertIs(uninstall._logger, mock_logger)

    def test_teardown_installation_logs_message(self):
        """Test test_teardown_installation_logs_message."""
        mock_logger = mock.Mock()
        uninstall = UninstallOnLinux(logger=mock_logger)

        uninstall.teardown_installation()

        mock_logger.debug.assert_called_once()
        mock_logger.info.assert_any_call("Linux cron job removed for BWP automation")

    @mock.patch("abk_bwp.uninstall.abk_common.get_home_dir")
    def test_cleanup_image_dir_logs_message(self, mock_get_home_dir):
        """Test test_cleanup_image_dir_logs_message."""
        mock_logger = mock.Mock()
        # Use string path instead of Path to avoid platform-specific separators
        home_dir = "home/testuser"
        mock_get_home_dir.return_value = home_dir
        uninstall = UninstallOnLinux(logger=mock_logger)
        image_dir = "Pictures/BingWallpapers"

        uninstall.cleanup_image_dir(image_dir)

        # Verify debug was called and check that the path components are present
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]

        # Check that the call contains the expected components
        self.assertIn("images_dir=", call_args)
        self.assertIn("home", call_args)
        self.assertIn("testuser", call_args)
        self.assertIn("Pictures", call_args)
        self.assertIn("BingWallpapers", call_args)


# =============================================================================
# UninstallOnWindows
# =============================================================================
class TestUninstallOnWindows(unittest.TestCase):
    """TestUninstallOnWindows class."""

    def test_init_sets_os_type(self):
        """Test test_init_sets_os_type."""
        mock_logger = mock.Mock()
        uninstall = UninstallOnWindows(logger=mock_logger)

        self.assertEqual(uninstall.os_type, abk_common.OsType.WINDOWS_OS)
        self.assertIs(uninstall._logger, mock_logger)

    def test_teardown_installation_logs_message(self):
        """Test test_teardown_installation_logs_message."""
        mock_logger = mock.Mock()
        uninstall = UninstallOnWindows(logger=mock_logger)

        uninstall.teardown_installation()

        mock_logger.debug.assert_called_once()
        mock_logger.info.assert_any_call("Windows uninstallation is not supported yet")

    def test_cleanup_image_dir_logs_message(self):
        """Test test_cleanup_image_dir_logs_message."""
        mock_logger = mock.Mock()
        uninstall = UninstallOnWindows(logger=mock_logger)
        image_dir = "/home/testuser/Pictures/BingWallpapers"

        uninstall.cleanup_image_dir(image_dir)

        mock_logger.debug.assert_called_once_with(f"{image_dir=}")
        mock_logger.info.assert_any_call("Windows cleanup_image_dir is not supported yet")


if __name__ == "__main__":
    unittest.main()

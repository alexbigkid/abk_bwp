"""Unit tests for install.py."""

# Standard library imports
import os
from pathlib import Path
import subprocess  # noqa: S404
import unittest
from unittest import mock
import logging
from datetime import time

# Third party imports

# Local imports
from abk_bwp import abk_common
from abk_bwp.install import IInstallBase, InstallOnMacOS, InstallOnLinux, InstallOnWindows


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
        # expected_script_path = os.path.join("/fake", "dir", "bingwallpaper.sh")

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
        # written_lines = handle.writelines.call_args[0][0]
        # These are examples of expected line fragments; verify each was written
        # for call in mock_logger.debug.call_args_list:
        #     args, kwargs = call
        #     print("Args:", args)
        #     print("Kwargs:", kwargs)
        mock_logger.debug.assert_any_call(f"{time_to_exe.hour=}, {time_to_exe.minute=}, {script_name=}")
        mock_logger.debug.assert_any_call(f"{script_name = }")
        mock_logger.debug.assert_any_call(f"{plist_label = }")
        # Return value can be validated using another mock
        mock_return_checker = mock.Mock()
        mock_return_checker(plist_label)
        mock_return_checker.assert_called_once_with(result)

    # -------------------------------------------------------------------------
    # InstallOnMacOS._create_plist_link
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.abk_common.get_home_dir", return_value=str(Path.home()))
    @mock.patch("abk_bwp.abk_common.ensure_dir")
    @mock.patch("abk_bwp.abk_common.ensure_link_exists")
    @mock.patch("os.path.basename", return_value="com.testuser.bingwallpaper.sh.plist")
    @mock.patch("os.path.join", side_effect=lambda *args: "/".join(args))  # preserve join logic
    def test_create_plist_link(self, mock_path_join, mock_basename, mock_ensure_link_exists, mock_ensure_dir, mock_get_home_dir):
        """Test test_create_plist_link."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        installer = InstallOnMacOS(mock_logger)
        expected_file_name = "com.testuser.bingwallpaper.sh.plist"
        full_file_name = os.path.join("/some", "fake", "path", expected_file_name)
        expected_dst = os.path.join(mock_get_home_dir.return_value, "Library", "LaunchAgents", expected_file_name)

        # Act
        # ----------------------------------
        result = installer._create_plist_link(full_file_name)

        # Assert
        # ----------------------------------
        # Verify logger debug/info
        # for call in mock_logger.info.call_args_list:
        #     args, kwargs = call
        #     print("Args:", args)
        #     print("Kwargs:", kwargs)
        # mock_logger.debug.assert_any_call(f"{full_file_name=}")
        # mock_logger.info.assert_any_call(f"src= {full_file_name}, dst= {expected_dst}")
        # mock_logger.debug.assert_any_call(f"{expected_dst=}")
        # Validate abk_common calls
        mock_get_home_dir.assert_called_once()
        mock_ensure_dir.assert_called_once_with(os.path.join(mock_get_home_dir.return_value, "Library/LaunchAgents"))
        mock_ensure_link_exists.assert_called_once_with(full_file_name, expected_dst)
        # Validate result using a mock
        mock_result_checker = mock.Mock()
        mock_result_checker(expected_dst)
        mock_result_checker.assert_called_once_with(result)

    # -------------------------------------------------------------------------
    # InstallOnMacOS._stop_and_unload_bingwallpaper_job
    # -------------------------------------------------------------------------
    @mock.patch("subprocess.check_call")
    def test_stop_and_unload_bingwallpaper_job(self, mock_check_call):
        """Test test_stop_and_unload_bingwallpaper_job."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        test_user = "testuser"
        plist_name = os.path.join("/Users", test_user, "Library", "LaunchAgents", f"com.{test_user}.bingwallpaper.sh.plist")
        plist_label = f"com.{test_user}.bingwallpaper.sh.plist"
        expected_commands = [
            f"launchctl list | grep {plist_label}",
            f"launchctl stop {plist_label}",
            f"launchctl unload -w {plist_name}",
        ]
        # Simulate success for all commands
        mock_check_call.return_value = 0

        # Act
        # ----------------------------------
        installer = InstallOnMacOS(mock_logger)
        installer._stop_and_unload_bingwallpaper_job(plist_name, plist_label)

        # Assert
        # ----------------------------------
        mock_logger.debug.assert_called_once_with(f"{plist_name=}, {plist_label=}")
        for cmd in expected_commands:
            mock_logger.info.assert_any_call(f"about to execute command '{cmd}'")
            mock_logger.info.assert_any_call(f"command '{cmd}' succeeded, returned: 0")
        # Ensure each command was executed once
        self.assertEqual(mock_check_call.call_count, len(expected_commands))
        mock_check_call.assert_has_calls(
            [mock.call(cmd, shell=True) for cmd in expected_commands]  # noqa: S604
        )

    @mock.patch("subprocess.check_call")
    def test_stop_and_unload_bingwallpaper_job_with_error(self, mock_check_call):
        """Test test_stop_and_unload_bingwallpaper_job_with_error."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        installer = InstallOnMacOS(mock_logger)
        test_user = "testuser"
        plist_name = os.path.join("/Users", test_user, "Library", f"LaunchAgentscom.{test_user}.bingwallpaper.sh.plist")
        plist_label = f"com.{test_user}.bingwallpaper.sh.plist"

        # Raise CalledProcessError on second command
        def side_effect(cmd, shell):
            """side_effect."""
            if "stop" in cmd:
                raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
            return 0

        mock_check_call.side_effect = side_effect

        # Act
        # ----------------------------------
        installer._stop_and_unload_bingwallpaper_job(plist_name, plist_label)

        # Assert
        # ----------------------------------
        mock_logger.info.assert_any_call("error: e.returncode=1. It is expected though, not all cmds exec successfully.")

    # -------------------------------------------------------------------------
    # InstallOnMacOS._load_and_start_bingwallpaper_job
    # -------------------------------------------------------------------------
    @mock.patch("subprocess.check_call")
    def test_load_and_start_bingwallpaper_job_success(self, mock_check_call):
        """Test test_load_and_start_bingwallpaper_job_success."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        installer = InstallOnMacOS(mock_logger)
        plist_name = "/Users/testuser/Library/LaunchAgents/com.testuser.bingwallpaper.sh.plist"
        plist_label = "com.testuser.bingwallpaper.sh.plist"
        expected_commands = [f"launchctl load -w {plist_name}", f"launchctl start {plist_label}"]
        mock_check_call.return_value = 0

        # Act
        # ----------------------------------
        installer._load_and_start_bingwallpaper_job(plist_name, plist_label)

        # Assert
        # ----------------------------------
        mock_logger.debug.assert_called_once_with(f"{plist_name=}, {plist_label=}")
        for cmd in expected_commands:
            mock_logger.info.assert_any_call(f"about to execute command '{cmd}'")
            mock_logger.info.assert_any_call(f"command '{cmd}' succeeded, returned: 0")

        mock_check_call.assert_has_calls(
            [mock.call(cmd, shell=True) for cmd in expected_commands]  # noqa: S604
        )
        self.assertEqual(mock_check_call.call_count, 2)

    @mock.patch("subprocess.check_call")
    def test_load_and_start_bingwallpaper_job_subprocess_error(self, mock_check_call):
        """Test test_load_and_start_bingwallpaper_job_subprocess_error."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        installer = InstallOnMacOS(mock_logger)
        plist_name = "/fake/path.plist"
        plist_label = "com.test.bingwallpaper"
        # Fail on first command
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "launchctl load -w")

        # Act
        # ----------------------------------
        installer._load_and_start_bingwallpaper_job(plist_name, plist_label)

        # Assert
        # ----------------------------------
        mock_logger.critical.assert_called_once_with("ERROR: returned: 1")

    @mock.patch("subprocess.check_call", side_effect=RuntimeError("unexpected"))
    def test_load_and_start_bingwallpaper_job_unknown_exception(self, mock_check_call):
        """Test test_load_and_start_bingwallpaper_job_unknown_exception."""
        mock_logger = mock.Mock()
        installer = InstallOnMacOS(mock_logger)
        installer._load_and_start_bingwallpaper_job("/fake/path.plist", "label")
        mock_logger.critical.assert_called_once_with("ERROR: unknown")


# =============================================================================
# InstallOnLinux
# =============================================================================
class TestInstallOnLinux(unittest.TestCase):
    """TestInstallOnLinux class."""

    # -------------------------------------------------------------------------
    # InstallOnLinux.__init__
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.install.IInstallBase.__init__", return_value=None)
    def test_init_sets_os_type_and_calls_super(self, mock_super_init):
        """Test test_init_sets_os_type_and_calls_super."""
        logger = mock.Mock()
        installer = InstallOnLinux(logger)
        self.assertEqual(installer.os_type, abk_common.OsType.LINUX_OS)
        mock_super_init.assert_called_once_with(logger)

    # -------------------------------------------------------------------------
    # InstallOnLinux.setup_installation
    # -------------------------------------------------------------------------
    @mock.patch("subprocess.run")
    def test_install_on_linux_setup_installation_logs_correct_message(self, mock_subprocess):
        """Test test_install_on_linux_setup_installation_logs_correct_message."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        installer = InstallOnLinux(mock_logger)

        # Mock subprocess calls for cron operations
        mock_subprocess.side_effect = [
            mock.Mock(returncode=0, stdout=""),  # crontab -l (empty crontab)
            mock.Mock(returncode=0),  # crontab - (install new crontab)
        ]

        # Act
        # ----------------------------------
        installer.setup_installation()

        # Assert
        # ----------------------------------
        self.assertEqual(installer.os_type, abk_common.OsType.LINUX_OS)
        # Linux installation now creates cron jobs - verify automation setup message
        found_message = False
        for call in mock_logger.info.call_args_list:
            args = call[0]
            if len(args) > 0 and "Linux cron job created for BWP automation" in args[0]:
                found_message = True
                break
        self.assertTrue(found_message, "Expected Linux cron job creation message not found")


# =============================================================================
# InstallOnWindows
# =============================================================================
class TestInstallOnWindows(unittest.TestCase):
    """TestInstallOnWindows class."""

    # -------------------------------------------------------------------------
    # InstallOnWindows.__init__
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.install.IInstallBase.__init__", return_value=None)
    def test_init_sets_os_type_and_calls_super(self, mock_super_init):
        """Test test_init_sets_os_type_and_calls_super."""
        logger = mock.Mock()
        installer = InstallOnWindows(logger)
        self.assertEqual(installer.os_type, abk_common.OsType.WINDOWS_OS)
        mock_super_init.assert_called_once_with(logger)

    # -------------------------------------------------------------------------
    # InstallOnWindows.setup_installation
    # -------------------------------------------------------------------------
    def test_install_on_windows_setup_installation_logs_correct_message(self):
        """Test test_install_on_windows_setup_installation_logs_correct_message."""
        # Arrange
        # ----------------------------------
        mock_logger = mock.Mock()
        installer = InstallOnWindows(mock_logger)

        # Act
        # ----------------------------------
        installer.setup_installation()

        # Assert
        # ----------------------------------
        self.assertEqual(installer.os_type, abk_common.OsType.WINDOWS_OS)
        mock_logger.info.assert_any_call("Windows installation is not supported yet")


if __name__ == "__main__":
    unittest.main()

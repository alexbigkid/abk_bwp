"""Unit tests for abk_common.py."""

# Standard library imports
import errno
import json
import os
import sys
import unittest
from unittest import mock

# Third party imports


GENERAL_EXCEPTION_MSG = "General Exception Raised"


@unittest.skipIf(sys.platform.startswith("win"), "should not run on Windows")
@mock.patch("os.environ")
class TestGetpassGetuser(unittest.TestCase):
    """Tests for GetUserName function."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    def test_Getuser__username_takes_username_from_env(self, environ) -> None:
        """test_Getuser__username_takes_username_from_env."""
        expected_user_name = "user_name_001"
        environ.get.return_value = expected_user_name
        actual_user_name = self.abk_common.get_user_name()
        self.assertEqual(actual_user_name, expected_user_name, "ERROR: unexpected user name")

    def test_Getuser__username_priorities_of_env_values(self, environ) -> None:
        """test_Getuser__username_priorities_of_env_values."""
        environ.get.return_value = None
        self.abk_common.get_user_name()
        self.assertEqual(
            [mock.call(x) for x in ("LOGNAME", "USER", "LNAME", "USERNAME")],
            environ.get.call_args_list,
        )

    def test_Getuser__username_falls_back_to_pwd(self, environ) -> None:
        """test_Getuser__username_falls_back_to_pwd."""
        expected_user_name = "user_name_003"
        environ.get.return_value = None
        with mock.patch("os.getuid") as uid, mock.patch("pwd.getpwuid") as getpw:
            uid.return_value = 42
            getpw.return_value = [expected_user_name]
            self.assertEqual(self.abk_common.get_user_name(), expected_user_name)
            getpw.assert_called_once_with(42)


class TestGetCurrentDir(unittest.TestCase):
    """Tests for get_current_dir function."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    @mock.patch("os.path.realpath")
    @mock.patch("os.path.dirname")
    def test_returns_correct_directory_path(self, mock_dirname, mock_realpath):
        """Test that get_current_dir returns the correct directory path."""
        mock_realpath.side_effect = lambda x: x
        mock_realpath.return_value = "/mock/path/to/file.py"
        mock_dirname.return_value = "/mock/path/to"

        result = self.abk_common.get_current_dir("somefile.py")
        self.assertEqual(result, "/mock/path/to")
        mock_realpath.assert_called_once_with("somefile.py")
        mock_dirname.assert_called_once_with("somefile.py")

    @mock.patch("os.path.realpath", side_effect=lambda x: x)
    def test_returns_dirname_when_realpath_returns_input(self, mock_realpath):
        """Test that get_current_dir returns dirname when realpath returns input."""
        result = self.abk_common.get_current_dir("/my/test/file.py")
        self.assertEqual(result, "/my/test")
        mock_realpath.assert_called_once_with("/my/test/file.py")


class TestGetParentDir(unittest.TestCase):
    """Tests for get_parent_dir function."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    @mock.patch("os.path.dirname")
    def test_returns_correct_directory_path(self, mock_dirname):
        """Test that get_parent_dir returns the correct parent directory."""
        mock_dirname.side_effect = ["/mock/parent", "/mock/child"]

        result = self.abk_common.get_parent_dir("/mock/parent/child/file.txt")

        self.assertEqual(result, "/mock/child")
        self.assertEqual(mock_dirname.call_count, 2)
        mock_dirname.assert_has_calls(
            [mock.call("/mock/parent/child/file.txt"), mock.call("/mock/parent")]
        )


class TestEnsureDir(unittest.TestCase):
    """Unit tests for ensure_dir function."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    @mock.patch("abk_bwp.abk_common.os.makedirs")
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=False)
    def test_creates_directory_if_not_exists(self, mock_exists, mock_makedirs):
        """Test that ensure_dir creates directory if it does not exist."""
        self.abk_common.ensure_dir("/fake/dir")
        mock_exists.assert_called_once_with("/fake/dir")
        mock_makedirs.assert_called_once_with("/fake/dir")

    @mock.patch("abk_bwp.abk_common.os.makedirs")
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=True)
    def test_does_nothing_if_directory_exists(self, mock_exists, mock_makedirs):
        """Test that ensure_dir does nothing if directory already exists."""
        self.abk_common.ensure_dir("/existing/dir")
        mock_exists.assert_called_once_with("/existing/dir")
        mock_makedirs.assert_not_called()

    @mock.patch("abk_bwp.abk_common.os.makedirs")
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=False)
    def test_raises_for_non_eexist_oserror(self, mock_exists, mock_makedirs):
        """Test that ensure_dir raises OSError for non-EEXIST errors."""
        error = OSError("boom")
        error.errno = errno.EACCES
        mock_makedirs.side_effect = error

        with self.assertRaises(OSError):
            self.abk_common.ensure_dir("/bad/dir")
        mock_exists.assert_called_once_with("/bad/dir")

    @mock.patch("abk_bwp.abk_common.os.makedirs")
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=False)
    def test_ignores_eexist_oserror(self, mock_exists, mock_makedirs):
        """Test that ensure_dir ignores OSError if errno is EEXIST."""
        error = OSError("already exists")
        error.errno = errno.EEXIST
        mock_makedirs.side_effect = error

        try:
            self.abk_common.ensure_dir("/maybe-exists")
        except Exception:
            self.fail("ensure_dir should not raise if OSError is EEXIST")


class TestEnsureLinkExists(unittest.TestCase):
    """Unit tests for ensure_link_exists function."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    @mock.patch("abk_bwp.abk_common.os.symlink")
    @mock.patch("abk_bwp.abk_common.os.path.islink", return_value=False)
    def test_creates_symlink_if_not_exists(self, mock_islink, mock_symlink):
        """Test that ensure_link_exists creates symlink if it does not exist."""
        self.abk_common.ensure_link_exists("source.txt", "link.txt")
        mock_islink.assert_called_once_with("link.txt")
        mock_symlink.assert_called_once_with("source.txt", "link.txt")

    @mock.patch("abk_bwp.abk_common.os.symlink")
    @mock.patch("abk_bwp.abk_common.os.path.islink", return_value=True)
    def test_does_nothing_if_symlink_exists(self, mock_islink, mock_symlink):
        """Test that ensure_link_exists does nothing if symlink already exists."""
        self.abk_common.ensure_link_exists("source.txt", "link.txt")
        mock_islink.assert_called_once_with("link.txt")
        mock_symlink.assert_not_called()

    @mock.patch("abk_bwp.abk_common.os.symlink")
    @mock.patch("abk_bwp.abk_common.os.path.islink", return_value=False)
    def test_ignores_eexist_oserror(self, mock_islink, mock_symlink):
        """Test that ensure_link_exists ignores OSError if errno is EEXIST."""
        error = OSError("already exists")
        error.errno = errno.EEXIST
        mock_symlink.side_effect = error

        try:
            self.abk_common.ensure_link_exists("source.txt", "link1.txt")
        except Exception:
            self.fail("Should not raise if errno is EEXIST")
        mock_islink.assert_called_once_with("link1.txt")

    @mock.patch("abk_bwp.abk_common.os.symlink")
    @mock.patch("abk_bwp.abk_common.os.path.islink", return_value=False)
    def test_raises_for_non_eexist_oserror(self, mock_islink, mock_symlink):
        """Test that ensure_link_exists raises OSError for non-EEXIST errors."""
        error = OSError("boom")
        error.errno = errno.EPERM
        mock_symlink.side_effect = error

        with self.assertRaises(OSError):
            self.abk_common.ensure_link_exists("source.txt", "link2.txt")
        mock_islink.assert_called_once_with("link2.txt")


class TestRemoveLink(unittest.TestCase):
    """Unit tests for remove_link function."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    @mock.patch("abk_bwp.abk_common.os.unlink")
    @mock.patch("abk_bwp.abk_common.os.path.islink", return_value=True)
    def test_removes_symlink_when_exists(self, mock_islink, mock_unlink):
        """Test that remove_link removes the symlink if it exists."""
        self.abk_common.remove_link("link.txt")
        mock_islink.assert_called_once_with("link.txt")
        mock_unlink.assert_called_once_with("link.txt")

    @mock.patch(
        "abk_bwp.abk_common.os.unlink", side_effect=OSError(errno.EPERM, "permission denied")
    )
    @mock.patch("abk_bwp.abk_common.os.path.islink", return_value=True)
    def test_logs_error_when_unlink_fails(self, mock_islink, mock_unlink):
        """Test that remove_link logs an error if unlink fails."""
        with mock.patch("abk_bwp.abk_common.logger") as mock_logger:
            self.abk_common.remove_link("link.txt")
            mock_logger.error.assert_called_once()
            self.assertIn("failed to delete link", mock_logger.error.call_args[0][0])
        mock_islink.assert_called_once_with("link.txt")
        mock_unlink.assert_called_once_with("link.txt")

    @mock.patch("abk_bwp.abk_common.os.path.islink", return_value=False)
    @mock.patch("abk_bwp.abk_common.os.unlink")
    def test_does_nothing_if_not_symlink(self, mock_unlink, mock_islink):
        """Test that remove_link does nothing if the file is not a symlink."""
        self.abk_common.remove_link("not_a_link.txt")
        mock_islink.assert_called_once_with("not_a_link.txt")
        mock_unlink.assert_not_called()


class TestDeleteDir(unittest.TestCase):
    """Unit tests for delete_dir function."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    @mock.patch("abk_bwp.abk_common.os.rmdir")
    @mock.patch("abk_bwp.abk_common.os.listdir", return_value=[])
    @mock.patch("abk_bwp.abk_common.os.path.isdir", return_value=True)
    def test_deletes_empty_directory(self, mock_isdir, mock_listdir, mock_rmdir):
        """Test that delete_dir deletes an empty directory."""
        self.abk_common.delete_dir("/mock/empty_dir")
        mock_isdir.assert_called_once_with("/mock/empty_dir")
        mock_listdir.assert_called_once_with("/mock/empty_dir")
        mock_rmdir.assert_called_once_with("/mock/empty_dir")

    @mock.patch("abk_bwp.abk_common.logger")
    @mock.patch("abk_bwp.abk_common.os.listdir", return_value=["file1", "file2"])
    @mock.patch("abk_bwp.abk_common.os.path.isdir", return_value=True)
    def test_does_not_delete_non_empty_directory(self, mock_isdir, mock_listdir, mock_logger):
        """Test that delete_dir does not delete a non-empty directory and logs debug info."""
        self.abk_common.delete_dir("/mock/non_empty_dir")
        mock_logger.debug.assert_any_call("dir /mock/non_empty_dir is not empty")
        mock_logger.debug.assert_any_call("fileName='file1'")
        mock_logger.debug.assert_any_call("fileName='file2'")
        mock_isdir.assert_called_once_with("/mock/non_empty_dir")
        self.assertEqual(mock_listdir.call_count, 2)
        mock_listdir.assert_has_calls(
            [mock.call("/mock/non_empty_dir"), mock.call("/mock/non_empty_dir")]
        )

    @mock.patch("abk_bwp.abk_common.logger")
    @mock.patch("abk_bwp.abk_common.os.rmdir", side_effect=OSError(errno.ENOTEMPTY, "not empty"))
    @mock.patch("abk_bwp.abk_common.os.listdir", return_value=[])
    @mock.patch("abk_bwp.abk_common.os.path.isdir", return_value=True)
    def test_logs_error_if_rmdir_fails_due_to_not_empty(
        self, mock_isdir, mock_listdir, mock_rmdir, mock_logger
    ):
        """Test that delete_dir logs an error if rmdir fails due to directory not being empty."""
        self.abk_common.delete_dir("/mock/failure_dir")
        mock_logger.error.assert_called_with(
            "ERROR:delete_dir: directory /mock/failure_dir is not empty"
        )
        mock_isdir.assert_called_once_with("/mock/failure_dir")
        mock_listdir.assert_called_once_with("/mock/failure_dir")
        mock_rmdir.assert_called_once_with("/mock/failure_dir")

    @mock.patch("abk_bwp.abk_common.os.path.isdir", return_value=False)
    def test_does_nothing_if_not_a_directory(self, mock_isdir):
        """Test that delete_dir does nothing if the path is not a directory."""
        self.abk_common.delete_dir("/not/a/dir")
        mock_isdir.assert_called_once_with("/not/a/dir")


class TestDeleteFile(unittest.TestCase):
    """Unit tests for delete_file function."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    @mock.patch("abk_bwp.abk_common.os.remove")
    @mock.patch("abk_bwp.abk_common.os.path.isfile", return_value=True)
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=True)
    def test_deletes_existing_file(self, mock_exists, mock_isfile, mock_remove):
        """Test that delete_file deletes an existing file."""
        self.abk_common.delete_file("/mock/file.txt")
        mock_remove.assert_called_once_with("/mock/file.txt")
        mock_exists.assert_called_once_with("/mock/file.txt")
        mock_isfile.assert_called_once_with("/mock/file.txt")

    @mock.patch("abk_bwp.abk_common.os.remove")
    @mock.patch("abk_bwp.abk_common.os.path.isfile", return_value=False)
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=True)
    def test_does_not_delete_if_not_a_file(self, mock_exists, mock_isfile, mock_remove):
        """Test that delete_file does not delete if the path is not a file."""
        self.abk_common.delete_file("/mock/not_a_file")
        mock_remove.assert_not_called()
        mock_exists.assert_called_once_with("/mock/not_a_file")
        mock_isfile.assert_called_once_with("/mock/not_a_file")

    @mock.patch("abk_bwp.abk_common.os.remove")
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=False)
    def test_does_not_delete_if_file_does_not_exist(self, mock_exists, mock_remove):
        """Test that delete_file does not delete if the file does not exist."""
        self.abk_common.delete_file("/mock/missing.txt")
        mock_remove.assert_not_called()
        mock_exists.assert_called_once_with("/mock/missing.txt")

    @mock.patch("abk_bwp.abk_common.logger")
    @mock.patch("abk_bwp.abk_common.os.remove", side_effect=OSError("delete failed"))
    @mock.patch("abk_bwp.abk_common.os.path.isfile", return_value=True)
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=True)
    def test_logs_error_on_remove_exception(
        self, mock_exists, mock_isfile, mock_remove, mock_logger
    ):
        """Test that delete_file logs an error if an OSError occurs during file deletion."""
        mock_remove.side_effect = OSError("delete failed")
        self.abk_common.delete_file("/mock/bad_file.txt")
        mock_logger.error.assert_called()
        args = mock_logger.error.call_args[0][0]
        self.assertIn("ERROR:delete_file:", args)
        mock_exists.assert_called_once_with("/mock/bad_file.txt")
        mock_isfile.assert_called_once_with("/mock/bad_file.txt")


class TestReadJsonFile(unittest.TestCase):
    """Unit tests for read_json_file function."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    @mock.patch(
        "abk_bwp.abk_common.open", new_callable=mock.mock_open, read_data='{"key": "value"}'
    )
    @mock.patch("abk_bwp.abk_common.os.path.isfile", return_value=True)
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=True)
    def test_reads_valid_json_file(self, mock_exists, mock_isfile, mock_open_file):
        """Test that read_json_file reads a valid JSON file."""
        result = self.abk_common.read_json_file("fake.json")
        self.assertEqual(result, {"key": "value"})
        mock_exists.assert_called_once_with("fake.json")
        mock_isfile.assert_called_once_with("fake.json")
        mock_open_file.assert_called_once_with("fake.json")

    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=False)
    def test_returns_empty_dict_when_file_does_not_exist(self, mock_exists):
        """Test that read_json_file returns an empty dict when file does not exist."""
        result = self.abk_common.read_json_file("nonexistent.json")
        self.assertEqual(result, {})
        mock_exists.assert_called_once_with("nonexistent.json")

    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=True)
    @mock.patch("abk_bwp.abk_common.os.path.isfile", return_value=False)
    def test_returns_empty_dict_when_path_is_not_file(self, mock_isfile, mock_exists):
        """Test that read_json_file returns an empty dict when path is not a file."""
        result = self.abk_common.read_json_file("notafile.json")
        self.assertEqual(result, {})
        mock_exists.assert_called_once_with("notafile.json")
        mock_isfile.assert_called_once_with("notafile.json")

    @mock.patch("abk_bwp.abk_common.logger")
    @mock.patch("abk_bwp.abk_common.open", new_callable=mock.mock_open)
    @mock.patch("abk_bwp.abk_common.os.path.isfile", return_value=True)
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=True)
    def test_logs_error_on_json_parse_exception(
        self, mock_exists, mock_isfile, mock_open_file, mock_logger
    ):
        """Test that read_json_file logs an error when JSON parsing fails."""
        mock_open_file.return_value.__enter__.return_value.read.return_value = "bad json"
        mock_open_file.return_value.__enter__.return_value.read.side_effect = (
            json.JSONDecodeError("Expecting value", "", 0)
        )
        with mock.patch(
            "abk_bwp.abk_common.json.load",
            side_effect=json.JSONDecodeError("Expecting value", "", 0),
        ):
            result = self.abk_common.read_json_file("bad.json")
            self.assertEqual(result, {})
            mock_logger.error.assert_called()
        mock_exists.assert_called_once_with("bad.json")
        mock_isfile.assert_called_once_with("bad.json")


class TestPerformanceTimer(unittest.TestCase):
    """Tests for PerformanceTimer context manager."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    def test_timer_logs_duration_with_custom_logger(self):
        """Test that PerformanceTimer logs duration with provided logger."""
        mock_logger = mock.Mock()
        with (
            mock.patch("timeit.default_timer", side_effect=[1.0, 2.0]),
            self.abk_common.PerformanceTimer("test_task", mock_logger),
        ):
            pass  # Simulate task

        mock_logger.info.assert_called_once()
        log_call_arg = mock_logger.info.call_args[0][0]
        self.assertIn("Executing test_task took", log_call_arg)

    def test_timer_uses_fallback_logger_if_none_provided(self):
        """Test that PerformanceTimer uses fallback logger if none provided."""
        with (
            mock.patch("abk_bwp.abk_common.logging.getLogger") as mock_get_logger,
            mock.patch("timeit.default_timer", side_effect=[1.0, 2.0]),
        ):
            logger_instance = mock.Mock()
            mock_get_logger.return_value = logger_instance

            with self.abk_common.PerformanceTimer("fallback_task", pt_logger=None):
                pass

        logger_instance.info.assert_called_once()
        self.assertIn("Executing fallback_task took", logger_instance.info.call_args[0][0])


class TestGetHomeDir(unittest.TestCase):
    """Tests for GetHomeDir function."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        patcher = mock.patch("abk_bwp.abk_common.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_common after patch
        import abk_bwp.abk_common as abk_common

        self.abk_common = abk_common

    @mock.patch.dict(os.environ, {"HOME": "users_home_dir_001"})
    def test_GetHomeDir__returns_users_homedir_from_env(self) -> None:
        """test_GetHomeDir__returns_users_homedir_from_env."""
        exp_home_dir = "users_home_dir_001"
        act_home_dir = self.abk_common.get_home_dir()
        self.assertEqual(exp_home_dir, act_home_dir, "ERROR: unexpected home dir returned")


if __name__ == "__main__":
    unittest.main()

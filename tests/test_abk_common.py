"""Unit tests for abk_common.py."""

# Standard library imports
import errno
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
        mock_realpath.return_value = "/mock/path/to/file.py"
        mock_dirname.return_value = "/mock/path/to"

        result = self.abk_common.get_current_dir("somefile.py")
        self.assertEqual(result, "/mock/path/to")
        mock_realpath.assert_called_once_with("somefile.py")
        mock_dirname.assert_called_once_with("/mock/path/to/file.py")

    @mock.patch("os.path.realpath", side_effect=lambda x: x)
    def test_returns_dirname_when_realpath_returns_input(self, mock_realpath):
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
        mock_dirname.side_effect = ["/mock/parent", "/mock/child"]

        result = self.abk_common.get_parent_dir("/mock/parent/child/file.txt")

        self.assertEqual(result, "/mock/child")
        self.assertEqual(mock_dirname.call_count, 2)
        mock_dirname.assert_has_calls(
            [
                mock.call("/mock/parent/child/file.txt"),
                mock.call("/mock/parent"),
            ]
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
        self.abk_common.ensure_dir("/fake/dir")
        mock_exists.assert_called_once_with("/fake/dir")
        mock_makedirs.assert_called_once_with("/fake/dir")

    @mock.patch("abk_bwp.abk_common.os.makedirs")
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=True)
    def test_does_nothing_if_directory_exists(self, mock_exists, mock_makedirs):
        self.abk_common.ensure_dir("/existing/dir")
        mock_exists.assert_called_once_with("/existing/dir")
        mock_makedirs.assert_not_called()

    @mock.patch("abk_bwp.abk_common.os.makedirs")
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=False)
    def test_raises_for_non_eexist_oserror(self, mock_exists, mock_makedirs):
        error = OSError("boom")
        error.errno = errno.EACCES
        mock_makedirs.side_effect = error

        with self.assertRaises(OSError):
            self.abk_common.ensure_dir("/bad/dir")
        mock_exists.assert_called_once_with("/bad/dir")

    @mock.patch("abk_bwp.abk_common.os.makedirs")
    @mock.patch("abk_bwp.abk_common.os.path.exists", return_value=False)
    def test_ignores_eexist_oserror(self, mock_exists, mock_makedirs):
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
        self.abk_common.ensure_link_exists("source.txt", "link.txt")
        mock_islink.assert_called_once_with("link.txt")
        mock_symlink.assert_called_once_with("source.txt", "link.txt")

    @mock.patch("abk_bwp.abk_common.os.symlink")
    @mock.patch("abk_bwp.abk_common.os.path.islink", return_value=True)
    def test_does_nothing_if_symlink_exists(self, mock_islink, mock_symlink):
        self.abk_common.ensure_link_exists("source.txt", "link.txt")
        mock_islink.assert_called_once_with("link.txt")
        mock_symlink.assert_not_called()

    @mock.patch("abk_bwp.abk_common.os.symlink")
    @mock.patch("abk_bwp.abk_common.os.path.islink", return_value=False)
    def test_ignores_eexist_oserror(self, mock_islink, mock_symlink):
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
        error = OSError("boom")
        error.errno = errno.EPERM
        mock_symlink.side_effect = error

        with self.assertRaises(OSError):
            self.abk_common.ensure_link_exists("source.txt", "link2.txt")
        mock_islink.assert_called_once_with("link2.txt")


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

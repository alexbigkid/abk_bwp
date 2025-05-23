"""Unit tests for abk_common.py."""

# Standard library imports
import os
import sys
import unittest
from unittest import mock

# Third party imports

# Local imports
from abk_bwp import abk_common


GENERAL_EXCEPTION_MSG = "General Exception Raised"


@unittest.skipIf(sys.platform.startswith("win"), "should not run on Windows")
@mock.patch("os.environ")
class TestGetpassGetuser(unittest.TestCase):
    """Tests for GetUserName function."""

    def test_Getuser__username_takes_username_from_env(self, environ) -> None:
        """test_Getuser__username_takes_username_from_env."""
        expected_user_name = "user_name_001"
        environ.get.return_value = expected_user_name
        actual_user_name = abk_common.get_user_name()
        self.assertEqual(actual_user_name, expected_user_name, "ERROR: unexpected user name")

    def test_Getuser__username_priorities_of_env_values(self, environ) -> None:
        """test_Getuser__username_priorities_of_env_values."""
        environ.get.return_value = None
        abk_common.get_user_name()
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
            self.assertEqual(abk_common.get_user_name(), expected_user_name)
            getpw.assert_called_once_with(42)


class TestGetHomeDir(unittest.TestCase):
    """Tests for GetHomeDir function."""

    @mock.patch.dict(os.environ, {"HOME": "users_home_dir_001"})
    def test_GetHomeDir__returns_users_homedir_from_env(self) -> None:
        """test_GetHomeDir__returns_users_homedir_from_env."""
        exp_home_dir = "users_home_dir_001"
        act_home_dir = abk_common.get_home_dir()
        self.assertEqual(exp_home_dir, act_home_dir, "ERROR: unexpected home dir returned")


if __name__ == "__main__":
    unittest.main()

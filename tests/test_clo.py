"""Command line options for the Bing Wallpaper application."""

# Standard library imports
import sys
import unittest
from unittest.mock import patch, MagicMock

# MUT
from abk_bwp import clo


# Mock CONST for tests
class CONST:
    """Mocking CONST class from the constants.py."""

    NAME = "TestApp"
    VERSION = "1.2.3"
    LICENSE = "MIT"
    KEYWORDS = ["test", "cli"]
    AUTHORS = [{"name": "Alice", "email": "alice@example.com"}]
    MAINTAINERS = [{"name": "Bob", "email": "bob@example.com"}]


# Patch the CONST inside clo module
clo.CONST = CONST


class TestCommandLineOptions(unittest.TestCase):
    """Test class for the CommandLineOptions class."""

    def setUp(self):
        """Set up a fresh instance of CommandLineOptions before each test."""
        self.cmd = clo.CommandLineOptions()

    @patch("abk_bwp.clo.LoggerManager.get_logger", return_value=MagicMock())
    @patch("abk_bwp.clo.LoggerManager.configure")
    def test_handle_options_version_exit(self, mock_configure, mock_get_logger):
        """Test that passing '--version' prints version info and exits cleanly."""
        testargs = ["prog", "--version"]
        self.cmd._args = testargs
        with (
            patch.object(sys, "argv", testargs),
            patch("builtins.print") as mock_print,
            self.assertRaises(SystemExit) as cm,
        ):
            self.cmd.handle_options()
        mock_print.assert_called_once_with(f"{CONST.NAME} version: {CONST.VERSION}")
        self.assertEqual(cm.exception.code, 0)
        mock_configure.assert_not_called()
        mock_get_logger.assert_not_called()

    @patch("abk_bwp.clo.LoggerManager.get_logger", return_value=MagicMock())
    @patch("abk_bwp.clo.LoggerManager.configure")
    def test_handle_options_about_exit(self, mock_configure, mock_get_logger):
        """Test that passing '--about' prints app metadata and exits cleanly."""
        testargs = ["prog", "--about"]
        self.cmd._args = testargs
        with (
            patch.object(sys, "argv", testargs),
            patch("builtins.print") as mock_print,
            self.assertRaises(SystemExit) as cm,
        ):
            self.cmd.handle_options()
        mock_print.assert_any_call(f"Name       : {CONST.NAME}")
        mock_print.assert_any_call(f"Version    : {CONST.VERSION}")
        self.assertEqual(cm.exception.code, 0)
        mock_configure.assert_not_called()
        mock_get_logger.assert_not_called()

    @patch("abk_bwp.clo.LoggerManager.get_logger", return_value=MagicMock())
    @patch("abk_bwp.clo.LoggerManager.configure")
    def test_handle_options_parse_args(self, mock_configure, mock_get_logger):
        """Test that command-line arguments are correctly parsed into options."""
        testargs = ["prog", "-d", "enable", "-f", "disable", "-l"]
        with patch.object(sys, "argv", testargs):
            self.cmd.handle_options()
            self.assertEqual(self.cmd.options.desktop_auto_update, "enable")
            self.assertEqual(self.cmd.options.frame_tv, "disable")
            self.assertTrue(self.cmd.options.log_into_file)
            self.assertFalse(self.cmd.options.quiet)
            mock_configure.assert_called_once_with(log_into_file=True, quiet=False)
            mock_get_logger.assert_called_once_with("abk_bwp.clo")


if __name__ == "__main__":
    unittest.main()

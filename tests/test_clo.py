"""Command line options for the Bing Wallpaper application."""

# Standard library imports
import logging
import sys
import unittest
from unittest.mock import patch, mock_open
from pathlib import Path

# MUT
from abk_bwp import clo


# Mock CONST for tests
class CONST:
    NAME = "TestApp"
    VERSION = "1.2.3"
    LICENSE = "MIT"
    KEYWORDS = ["test", "cli"]
    AUTHORS = [{"name": "Alice", "email": "alice@example.com"}]
    MAINTAINERS = [{"name": "Bob", "email": "bob@example.com"}]

# Patch the CONST inside clo module
clo.CONST = CONST


class TestCommandLineOptions(unittest.TestCase):

    def setUp(self):
        self.cmd = clo.CommandLineOptions()


    def test_handle_options_version_exit(self):
        testargs = ["prog", "--version"]
        self.cmd._args = testargs
        with patch.object(sys, "argv", testargs):
            with patch("builtins.print") as mock_print:
                with self.assertRaises(SystemExit) as cm:
                    self.cmd.handle_options()
                mock_print.assert_called_once_with(f"{CONST.NAME} version: {CONST.VERSION}")
                self.assertEqual(cm.exception.code, 0)


    def test_handle_options_about_exit(self):
        testargs = ["prog", "--about"]
        self.cmd._args = testargs
        with patch.object(sys, "argv", testargs):
            with patch("builtins.print") as mock_print:
                with self.assertRaises(SystemExit) as cm:
                    self.cmd.handle_options()
                # Check prints for about info, partial check
                mock_print.assert_any_call(f"Name       : {CONST.NAME}")
                mock_print.assert_any_call(f"Version    : {CONST.VERSION}")
                self.assertEqual(cm.exception.code, 0)


    def test_handle_options_parse_args(self):
        testargs = ["prog", "-d", "enable", "-f", "disable", "-l"]
        with patch.object(sys, "argv", testargs):
            self.cmd.handle_options()
            self.assertTrue(self.cmd.options.desktop_auto_update == "enable")
            self.assertTrue(self.cmd.options.frame_tv == "disable")
            self.assertTrue(self.cmd.options.log_into_file)
            self.assertFalse(self.cmd.options.quiet)


    def test_handle_options_quiet_logging(self):
        testargs = ["prog", "-q"]
        with patch.object(sys, "argv", testargs):
            with patch.object(self.cmd, "_find_project_root") as mock_root:
                self.cmd.handle_options()
                # Quiet disables logging
                self.assertTrue(self.cmd.logger.disabled)
                self.assertEqual(logging.root.manager.disable, logging.CRITICAL)


    def test_handle_options_file_logging(self):
        logging.disable(logging.CRITICAL)
        testargs = ["prog", "-l"]
        with patch.object(sys, "argv", testargs):
            with patch.object(self.cmd, "_find_project_root", return_value=Path("/tmp")):
                m = mock_open(read_data="""
version: 1
formatters:
  simple:
    format: "%(message)s"
handlers:
  console:
    class: logging.StreamHandler
    formatter: simple
    level: DEBUG
loggers:
  fileLogger:
    level: DEBUG
    handlers:
      - console
    propagate: no
""")
                # Patch pathlib.Path.open (the method called on config_path Path object)
                with patch("pathlib.Path.open", m):
                    self.cmd.handle_options()
                    self.assertEqual(self.cmd.logger.name, "fileLogger")


    def test_find_project_root_found(self):
        # Create a temporary directory structure with a pyproject.toml file
        with patch("pathlib.Path.exists", side_effect=lambda self: self.name == "pyproject.toml"):
            root = self.cmd._find_project_root(start=Path("/fake/path"))
            self.assertIsInstance(root, Path)


    def test_find_project_root_found(self):
        def mock_exists(self_path):
            return self_path.name == "pyproject.toml"

        with patch("pathlib.Path.exists", new=mock_exists):
            root = self.cmd._find_project_root(start=Path("/fake/path"))
            self.assertIsInstance(root, Path)
            self.assertEqual(root, Path("/fake/path"))


    def test_setup_logging_file_missing(self):
        testargs = ["prog"]
        with patch.object(sys, "argv", testargs):
            with patch.object(self.cmd, "_find_project_root", return_value=Path("/tmp")):
                # Patch open to raise FileNotFoundError
                with patch("builtins.open", side_effect=FileNotFoundError):
                    with self.assertRaises(FileNotFoundError):
                        self.cmd.handle_options()


    def test_setup_logging_exception(self):
        testargs = ["prog"]
        with patch.object(sys, "argv", testargs):
            with patch.object(self.cmd, "_find_project_root", return_value=Path("/tmp")):
                # Use mock_open but patch pathlib.Path.open
                m = mock_open(read_data="bad yaml")
                with patch("pathlib.Path.open", m):
                    # Patch yaml.load to raise an exception
                    with patch("yaml.load", side_effect=Exception("bad yaml")):
                        # It should not raise; logger should be disabled
                        self.cmd.handle_options()
                        self.assertTrue(self.cmd.logger.disabled)


if __name__ == "__main__":
    unittest.main()

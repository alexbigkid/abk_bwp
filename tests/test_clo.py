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

    def test_handle_options_version_exit(self):
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

    def test_handle_options_about_exit(self):
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

    def test_handle_options_parse_args(self):
        """Test that command-line arguments are correctly parsed into options."""
        testargs = ["prog", "-d", "enable", "-f", "disable", "-l"]
        with patch.object(sys, "argv", testargs):
            self.cmd.handle_options()
            self.assertTrue(self.cmd.options.desktop_auto_update == "enable")
            self.assertTrue(self.cmd.options.frame_tv == "disable")
            self.assertTrue(self.cmd.options.log_into_file)
            self.assertFalse(self.cmd.options.quiet)

    def test_handle_options_quiet_logging(self):
        """Test that logging is disabled when '-q' (quiet) flag is used."""
        testargs = ["prog", "-q"]
        with patch.object(sys, "argv", testargs), patch.object(self.cmd, "_find_project_root"):
            self.cmd.handle_options()
            self.assertTrue(self.cmd.logger.disabled)
            self.assertEqual(logging.root.manager.disable, logging.CRITICAL)

    def test_handle_options_file_logging(self):
        """Test that a logging config file is correctly loaded and applied."""
        logging.disable(logging.CRITICAL)
        testargs = ["prog", "-l"]
        with (
            patch.object(sys, "argv", testargs),
            patch.object(self.cmd, "_find_project_root", return_value=Path("/tmp")),
        ):
            m = mock_open(
                read_data="""
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
"""
            )
            with patch("pathlib.Path.open", m):
                self.cmd.handle_options()
                self.assertEqual(self.cmd.logger.name, "fileLogger")

    def test_find_project_root_found(self):
        """Test that _find_project_root locates the directory containing pyproject.toml."""

        def mock_exists(self_path):
            return self_path.name == "pyproject.toml"

        with patch("pathlib.Path.exists", new=mock_exists):
            root = self.cmd._find_project_root(start=Path("/fake/path"))
            self.assertIsInstance(root, Path)
            self.assertEqual(root, Path("/fake/path"))

    def test_setup_logging_file_missing(self):
        """Test that FileNotFoundError is raised when logging config file is missing."""
        testargs = ["prog"]
        with (
            patch.object(sys, "argv", testargs),
            patch.object(self.cmd, "_find_project_root", return_value=Path("/test_tmp")),
            patch("builtins.open", side_effect=FileNotFoundError),
            self.assertRaises(FileNotFoundError),
        ):
            self.cmd.handle_options()

    def test_setup_logging_exception(self):
        """Test that an exception during YAML loading disables the logger instead of raising."""
        import tempfile

        testargs = ["prog"]
        with (
            tempfile.TemporaryDirectory() as tmp_dirname,
            patch.object(sys, "argv", testargs),
            patch.object(self.cmd, "_find_project_root", return_value=Path(tmp_dirname)),
            patch("pathlib.Path.open", mock_open(read_data="bad yaml")),
            patch("yaml.load", side_effect=Exception("bad yaml")),
        ):
            self.cmd.handle_options()
            self.assertTrue(self.cmd.logger.disabled)


if __name__ == "__main__":
    unittest.main()

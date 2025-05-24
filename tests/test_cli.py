"""Unit test for the CLI entry point."""

import unittest
from unittest.mock import patch, MagicMock
from abk_bwp import cli


class TestCliEntryPoint(unittest.TestCase):
    """Test the main() function in cli.py."""

    @patch("abk_bwp.cli.bingwallpaper")
    @patch("abk_bwp.cli.clo.CommandLineOptions")
    def test_main_invokes_bingwallpaper_with_options(
        self, mock_CommandLineOptions, mock_bingwallpaper
    ):
        """Test that main() initializes CommandLineOptions and calls bingwallpaper()."""
        mock_instance = MagicMock()
        mock_CommandLineOptions.return_value = mock_instance

        cli.main()

        mock_CommandLineOptions.assert_called_once()
        mock_instance.handle_options.assert_called_once()
        mock_bingwallpaper.assert_called_once_with(mock_instance)


if __name__ == "__main__":
    unittest.main()

"""Unit test for the CLI entry point."""

import unittest
from unittest.mock import patch, MagicMock
from abk_bwp import cli


class TestCliEntryPoint(unittest.TestCase):
    """Test the main() function in cli.py."""

    @patch("abk_bwp.cli.bingwallpaper")
    @patch("abk_bwp.cli.RetryManager")
    @patch("abk_bwp.cli.clo.CommandLineOptions")
    def test_main_invokes_bingwallpaper_with_options(self, mock_CommandLineOptions, mock_RetryManager, mock_bingwallpaper):
        """Test that main() initializes CommandLineOptions and calls bingwallpaper()."""
        mock_instance = MagicMock()
        mock_CommandLineOptions.return_value = mock_instance

        mock_retry_manager = MagicMock()
        mock_retry_manager.should_run_today.return_value = True
        mock_RetryManager.return_value = mock_retry_manager

        mock_bingwallpaper.return_value = True  # Simulate success

        cli.main()

        mock_CommandLineOptions.assert_called_once()
        mock_instance.handle_options.assert_called_once()
        mock_RetryManager.assert_called_once_with(logger=mock_instance.logger)
        mock_retry_manager.should_run_today.assert_called_once()
        mock_retry_manager.mark_attempt_start.assert_called_once()
        mock_bingwallpaper.assert_called_once_with(mock_instance)
        mock_retry_manager.mark_run_complete.assert_called_once_with(True)


if __name__ == "__main__":
    unittest.main()

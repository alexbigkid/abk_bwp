"""Tests for LazyLoggerProxy."""

import unittest
from unittest.mock import MagicMock, patch

from abk_bwp.lazy_logger import LazyLoggerProxy


class TestLazyLoggerProxy(unittest.TestCase):
    """Unit tests for LazyLoggerProxy."""

    def setUp(self):
        """Setup the test case with a logger name."""
        self.logger_name = "abk_bwp.test"

    @patch("abk_bwp.logger_manager.LoggerManager")
    def test_logger_resolves_and_logs(self, mock_logger_manager):
        """Test that the logger resolves and logs when configured."""
        mock_logger = MagicMock()
        mock_logger_manager.return_value.get_logger.return_value = mock_logger

        proxy = LazyLoggerProxy(self.logger_name)
        proxy.info("Test message")

        mock_logger_manager.return_value.get_logger.assert_called_once_with(self.logger_name)
        mock_logger.info.assert_called_once_with("Test message")

    @patch("abk_bwp.logger_manager.LoggerManager")
    def test_logger_resolves_only_once(self, mock_logger_manager):
        """Test that the logger resolves only once and is cached."""
        mock_logger = MagicMock()
        mock_logger_manager.return_value.get_logger.return_value = mock_logger

        proxy = LazyLoggerProxy(self.logger_name)
        proxy.debug("Debug message")
        proxy.error("Error message")

        mock_logger_manager.return_value.get_logger.assert_called_once_with(self.logger_name)
        mock_logger.debug.assert_called_once_with("Debug message")
        mock_logger.error.assert_called_once_with("Error message")

    @patch("abk_bwp.logger_manager.LoggerManager")
    def test_logger_defaults_to_module_name(self, mock_logger_manager):
        """Test that the logger defaults to current module name if no name is provided."""
        mock_logger = MagicMock()
        mock_logger_manager.return_value.get_logger.return_value = mock_logger

        proxy = LazyLoggerProxy()
        proxy.warning("Fallback logger")

        mock_logger_manager.return_value.get_logger.assert_called_once_with("abk_bwp.lazy_logger")
        mock_logger.warning.assert_called_once_with("Fallback logger")

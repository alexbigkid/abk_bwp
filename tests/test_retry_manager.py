"""Unit tests for retry_manager.py with platform-agnostic paths."""

import json
import logging
import tempfile
import unittest
from datetime import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from abk_bwp.retry_manager import RetryManager


class TestRetryManager(unittest.TestCase):
    """Test RetryManager class with platform-agnostic setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.maxDiff = None
        self.mock_logger = MagicMock(spec=logging.Logger)

        # Create a temporary directory for state file
        self.temp_dir = tempfile.mkdtemp()
        self.state_file_path = Path(self.temp_dir).joinpath("retry_state.json")

        # Mock config
        self.mock_config = {
            "retry": {
                "enabled": True,
                "max_attempts_per_day": 12,
                "daily_reset_time": "06:00:00",
                "require_all_operations_success": True,
            }
        }

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp files
        if self.state_file_path.exists():
            self.state_file_path.unlink()
        Path(self.temp_dir).rmdir()

    def _create_retry_manager(self, config=None):
        """Create RetryManager with temp directory for testing."""
        config = config or self.mock_config
        with patch("abk_bwp.retry_manager.bwp_config", config):
            retry_manager = RetryManager(self.mock_logger)
            # Override state file to use temp directory
            retry_manager._state_file = self.state_file_path
            return retry_manager

    # -------------------------------------------------------------------------
    # Test __init__ and _load_config
    # -------------------------------------------------------------------------
    def test_init_with_custom_logger(self):
        """Test RetryManager initialization with custom logger."""
        retry_manager = self._create_retry_manager()

        self.assertEqual(retry_manager._logger, self.mock_logger)
        self.assertTrue(retry_manager.retry_enabled)
        self.assertEqual(retry_manager.max_attempts_per_day, 12)
        self.assertEqual(retry_manager.daily_reset_time, time(6, 0, 0))
        self.assertTrue(retry_manager.require_all_operations_success)

    @patch("abk_bwp.retry_manager.logging.getLogger")
    def test_init_with_default_logger(self, mock_get_logger):
        """Test RetryManager initialization with default logger."""
        mock_default_logger = MagicMock()
        mock_get_logger.return_value = mock_default_logger

        with patch("abk_bwp.retry_manager.bwp_config", self.mock_config):
            retry_manager = RetryManager()
            retry_manager._state_file = self.state_file_path

        self.assertEqual(retry_manager._logger, mock_default_logger)
        mock_get_logger.assert_called_once_with("abk_bwp.retry_manager")

    def test_load_config_with_missing_retry_section(self):
        """Test configuration loading when retry section is missing."""
        empty_config = {}
        retry_manager = self._create_retry_manager(empty_config)

        # Should use default values
        self.assertTrue(retry_manager.retry_enabled)
        self.assertEqual(retry_manager.max_attempts_per_day, 12)
        self.assertEqual(retry_manager.daily_reset_time, time(6, 0, 0))
        self.assertTrue(retry_manager.require_all_operations_success)

    def test_load_config_with_invalid_time_format(self):
        """Test configuration loading with invalid time format."""
        invalid_config = {
            "retry": {
                "enabled": True,
                "max_attempts_per_day": 8,
                "daily_reset_time": "invalid_time",
                "require_all_operations_success": False,
            }
        }
        retry_manager = self._create_retry_manager(invalid_config)

        # Should use default time and log warning
        self.assertEqual(retry_manager.daily_reset_time, time(6, 0, 0))
        self.mock_logger.warning.assert_called_once_with("Invalid daily_reset_time format: invalid_time, using 06:00:00")
        # Other values should be preserved
        self.assertEqual(retry_manager.max_attempts_per_day, 8)
        self.assertFalse(retry_manager.require_all_operations_success)

    # -------------------------------------------------------------------------
    # Test _load_state
    # -------------------------------------------------------------------------
    def test_load_state_with_nonexistent_file(self):
        """Test loading state when file doesn't exist."""
        retry_manager = self._create_retry_manager()
        state = retry_manager._load_state()

        expected_state = {
            "last_run_date": None,
            "success_today": False,
            "attempts_today": 0,
            "last_attempt_time": None,
            "last_success_time": None,
            "failure_reasons": [],
            "operations_status": {"download_success": False, "desktop_success": False, "ftv_success": False},
        }
        self.assertEqual(state, expected_state)

    def test_load_state_with_existing_file(self):
        """Test loading state from existing file."""
        # Create a state file
        test_state = {
            "last_run_date": "2024-01-01",
            "success_today": True,
            "attempts_today": 3,
            "last_attempt_time": "2024-01-01T10:00:00",
            "last_success_time": "2024-01-01T10:00:00",
            "failure_reasons": [],
            "operations_status": {"download_success": True, "desktop_success": True, "ftv_success": True},
        }

        with open(self.state_file_path, "w") as f:
            json.dump(test_state, f)

        retry_manager = self._create_retry_manager()
        state = retry_manager._load_state()

        self.assertEqual(state, test_state)

    # -------------------------------------------------------------------------
    # Test _save_state
    # -------------------------------------------------------------------------
    def test_save_state_success(self):
        """Test successful state saving."""
        retry_manager = self._create_retry_manager()
        test_state = {"success_today": True, "attempts_today": 1, "last_run_date": "2024-01-01"}

        retry_manager._save_state(test_state)

        # Verify file was created and contains correct data
        self.assertTrue(self.state_file_path.exists())
        with open(self.state_file_path) as f:
            saved_state = json.load(f)
        self.assertEqual(saved_state, test_state)

    # -------------------------------------------------------------------------
    # Test should_run_today
    # -------------------------------------------------------------------------
    def test_should_run_today_retry_disabled(self):
        """Test should_run_today when retry is disabled."""
        disabled_config = {"retry": {"enabled": False}}
        retry_manager = self._create_retry_manager(disabled_config)

        result = retry_manager.should_run_today()

        self.assertTrue(result)
        self.mock_logger.debug.assert_called_once_with("Retry mechanism disabled, running normally")


if __name__ == "__main__":
    unittest.main()

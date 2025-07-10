"""Unit tests for retry_manager.py."""

import json
import logging
import tempfile
import unittest
from datetime import datetime, time
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch

from abk_bwp.retry_manager import RetryManager


class TestRetryManager(unittest.TestCase):
    """Test RetryManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.maxDiff = None
        self.mock_logger = MagicMock(spec=logging.Logger)

        # Create a temporary directory for state file
        self.temp_dir = tempfile.mkdtemp()
        self.state_file_path = Path(self.temp_dir) / ".abk_bwp_retry_state.json"

        # Mock config
        self.mock_config = {
            "retry": {
                "enabled": True,
                "max_attempts_per_day": 12,
                "daily_reset_time": "06:00:00",
                "require_all_operations_success": True
            }
        }

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp files
        if self.state_file_path.exists():
            self.state_file_path.unlink()
        Path(self.temp_dir).rmdir()

    # -------------------------------------------------------------------------
    # Test __init__ and _load_config
    # -------------------------------------------------------------------------
    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_init_with_custom_logger(self, mock_home, mock_bwp_config):
        """Test RetryManager initialization with custom logger."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)

        self.assertEqual(retry_manager._logger, self.mock_logger)
        self.assertEqual(retry_manager._state_file, Path(self.temp_dir) / ".abk_bwp_retry_state.json")
        self.assertTrue(retry_manager.retry_enabled)
        self.assertEqual(retry_manager.max_attempts_per_day, 12)
        self.assertEqual(retry_manager.daily_reset_time, time(6, 0, 0))
        self.assertTrue(retry_manager.require_all_operations_success)

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    @patch("abk_bwp.retry_manager.logging.getLogger")
    def test_init_with_default_logger(self, mock_get_logger, mock_home, mock_bwp_config):
        """Test RetryManager initialization with default logger."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)
        mock_default_logger = MagicMock()
        mock_get_logger.return_value = mock_default_logger

        retry_manager = RetryManager()

        self.assertEqual(retry_manager._logger, mock_default_logger)
        mock_get_logger.assert_called_once_with("abk_bwp.retry_manager")

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_load_config_with_missing_retry_section(self, mock_home, mock_bwp_config):
        """Test configuration loading when retry section is missing."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.clear()  # Empty config

        retry_manager = RetryManager(self.mock_logger)

        # Should use default values
        self.assertTrue(retry_manager.retry_enabled)
        self.assertEqual(retry_manager.max_attempts_per_day, 12)
        self.assertEqual(retry_manager.daily_reset_time, time(6, 0, 0))
        self.assertTrue(retry_manager.require_all_operations_success)

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_load_config_with_invalid_time_format(self, mock_home, mock_bwp_config):
        """Test configuration loading with invalid time format."""
        mock_home.return_value = Path(self.temp_dir)
        invalid_config = {
            "retry": {
                "enabled": True,
                "max_attempts_per_day": 8,
                "daily_reset_time": "invalid_time",
                "require_all_operations_success": False
            }
        }
        mock_bwp_config.update(invalid_config)

        retry_manager = RetryManager(self.mock_logger)

        # Should use default time and log warning
        self.assertEqual(retry_manager.daily_reset_time, time(6, 0, 0))
        self.mock_logger.warning.assert_called_once_with(
            "Invalid daily_reset_time format: invalid_time, using 06:00:00"
        )
        # Other values should be preserved
        self.assertEqual(retry_manager.max_attempts_per_day, 8)
        self.assertFalse(retry_manager.require_all_operations_success)

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_load_config_with_partial_config(self, mock_home, mock_bwp_config):
        """Test configuration loading with partial retry config."""
        mock_home.return_value = Path(self.temp_dir)
        partial_config = {
            "retry": {
                "enabled": False,
                "max_attempts_per_day": 5
                # Missing daily_reset_time and require_all_operations_success
            }
        }
        mock_bwp_config.update(partial_config)

        retry_manager = RetryManager(self.mock_logger)

        # Should use provided values and defaults for missing ones
        self.assertFalse(retry_manager.retry_enabled)
        self.assertEqual(retry_manager.max_attempts_per_day, 5)
        self.assertEqual(retry_manager.daily_reset_time, time(6, 0, 0))  # Default
        self.assertTrue(retry_manager.require_all_operations_success)  # Default

    # -------------------------------------------------------------------------
    # Test _load_state
    # -------------------------------------------------------------------------
    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_load_state_with_nonexistent_file(self, mock_home, mock_bwp_config):
        """Test loading state when file doesn't exist."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)
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

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_load_state_with_existing_file(self, mock_home, mock_bwp_config):
        """Test loading state from existing file."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

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

        retry_manager = RetryManager(self.mock_logger)
        state = retry_manager._load_state()

        self.assertEqual(state, test_state)

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_load_state_with_invalid_json(self, mock_home, mock_bwp_config):
        """Test loading state with invalid JSON file."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        # Create invalid JSON file
        with open(self.state_file_path, "w") as f:
            f.write("invalid json content")

        retry_manager = RetryManager(self.mock_logger)
        state = retry_manager._load_state()

        # Should return default state and log warning
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
        self.mock_logger.warning.assert_called_once()

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_load_state_with_partial_data(self, mock_home, mock_bwp_config):
        """Test loading state with partial data in file."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        # Create partial state file
        partial_state = {
            "success_today": True,
            "attempts_today": 2,
            # Missing other fields
        }

        with open(self.state_file_path, "w") as f:
            json.dump(partial_state, f)

        retry_manager = RetryManager(self.mock_logger)
        state = retry_manager._load_state()

        # Should merge with defaults
        expected_state = {
            "last_run_date": None,
            "success_today": True,  # From file
            "attempts_today": 2,    # From file
            "last_attempt_time": None,
            "last_success_time": None,
            "failure_reasons": [],
            "operations_status": {"download_success": False, "desktop_success": False, "ftv_success": False},
        }
        self.assertEqual(state, expected_state)

    # -------------------------------------------------------------------------
    # Test _save_state
    # -------------------------------------------------------------------------
    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_save_state_success(self, mock_home, mock_bwp_config):
        """Test successful state saving."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)
        test_state = {
            "success_today": True,
            "attempts_today": 1,
            "last_run_date": "2024-01-01"
        }

        retry_manager._save_state(test_state)

        # Verify file was created and contains correct data
        self.assertTrue(self.state_file_path.exists())
        with open(self.state_file_path) as f:
            saved_state = json.load(f)
        self.assertEqual(saved_state, test_state)

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_save_state_failure(self, mock_open, mock_home, mock_bwp_config):
        """Test state saving with OS error."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)
        test_state = {"success_today": True}

        retry_manager._save_state(test_state)

        # Should log error
        self.mock_logger.error.assert_called_once_with("Failed to save retry state: Permission denied")

    # -------------------------------------------------------------------------
    # Test _is_new_day
    # -------------------------------------------------------------------------
    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_is_new_day_with_no_last_run_date(self, mock_home, mock_bwp_config):
        """Test _is_new_day when no last run date is stored."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)
        state = {"last_run_date": None}

        self.assertTrue(retry_manager._is_new_day(state))

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    @patch("abk_bwp.retry_manager.datetime")
    def test_is_new_day_different_calendar_day(self, mock_datetime, mock_home, mock_bwp_config):
        """Test _is_new_day with different calendar day."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        # Mock current time
        mock_now = datetime(2024, 1, 2, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat.return_value = datetime(2024, 1, 1, 8, 0, 0)

        retry_manager = RetryManager(self.mock_logger)
        state = {"last_run_date": "2024-01-01T08:00:00"}

        self.assertTrue(retry_manager._is_new_day(state))

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_is_new_day_same_day_before_reset_time(self, mock_home, mock_bwp_config):
        """Test _is_new_day same day before reset time."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)

        # Mock the datetime operations directly
        with patch("abk_bwp.retry_manager.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 5, 0, 0)  # Before 6 AM reset time
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat.return_value = datetime(2024, 1, 1, 4, 0, 0)

            state = {"last_run_date": "2024-01-01T04:00:00"}
            result = retry_manager._is_new_day(state)

            # Should be False because it's same day and before reset time
            self.assertFalse(result)

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    @patch("abk_bwp.retry_manager.datetime")
    def test_is_new_day_same_day_after_reset_time_not_reset(self, mock_datetime, mock_home, mock_bwp_config):
        """Test _is_new_day same day after reset time without reset."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        # Mock current time - same day, after reset time
        mock_now = datetime(2024, 1, 1, 7, 0, 0)  # After 6 AM reset time
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat.return_value = datetime(2024, 1, 1, 4, 0, 0)

        retry_manager = RetryManager(self.mock_logger)
        state = {"last_run_date": "2024-01-01T04:00:00"}  # No last_reset_date

        self.assertTrue(retry_manager._is_new_day(state))

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_is_new_day_same_day_after_reset_time_already_reset(self, mock_home, mock_bwp_config):
        """Test _is_new_day same day after reset time already reset."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)

        # Mock the datetime operations directly
        with patch("abk_bwp.retry_manager.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 7, 0, 0)  # After 6 AM reset time
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat.return_value = datetime(2024, 1, 1, 4, 0, 0)

            state = {
                "last_run_date": "2024-01-01T04:00:00",
                "last_reset_date": "2024-01-01"  # Already reset today
            }
            result = retry_manager._is_new_day(state)

            # Should be False because already reset today
            self.assertFalse(result)

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_is_new_day_with_invalid_date(self, mock_home, mock_bwp_config):
        """Test _is_new_day with invalid date format."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)
        state = {"last_run_date": "invalid_date"}

        self.assertTrue(retry_manager._is_new_day(state))

    # -------------------------------------------------------------------------
    # Test _reset_daily_state
    # -------------------------------------------------------------------------
    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    @patch("abk_bwp.retry_manager.datetime")
    def test_reset_daily_state(self, mock_datetime, mock_home, mock_bwp_config):
        """Test daily state reset."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        mock_now = datetime(2024, 1, 1, 8, 0, 0)
        mock_datetime.now.return_value = mock_now

        retry_manager = RetryManager(self.mock_logger)
        state = retry_manager._reset_daily_state()

        expected_state = {
            "last_run_date": "2024-01-01",
            "last_reset_date": "2024-01-01",
            "success_today": False,
            "attempts_today": 0,
            "last_attempt_time": None,
            "last_success_time": None,
            "failure_reasons": [],
            "operations_status": {"download_success": False, "desktop_success": False, "ftv_success": False},
        }

        self.assertEqual(state, expected_state)
        self.mock_logger.info.assert_called_once_with(f"Daily retry state reset at {mock_now}")

    # -------------------------------------------------------------------------
    # Test should_run_today
    # -------------------------------------------------------------------------
    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_should_run_today_retry_disabled(self, mock_home, mock_bwp_config):
        """Test should_run_today when retry is disabled."""
        mock_home.return_value = Path(self.temp_dir)
        disabled_config = self.mock_config.copy()
        disabled_config["retry"]["enabled"] = False
        mock_bwp_config.update(disabled_config)

        retry_manager = RetryManager(self.mock_logger)
        result = retry_manager.should_run_today()

        self.assertTrue(result)
        self.mock_logger.debug.assert_called_once_with("Retry mechanism disabled, running normally")

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_should_run_today_already_successful(self, mock_home, mock_bwp_config):
        """Test should_run_today when already successful today."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        # Create state file with success
        success_state = {
            "last_run_date": "2024-01-01",
            "success_today": True,
            "attempts_today": 1,
        }
        with open(self.state_file_path, "w") as f:
            json.dump(success_state, f)

        retry_manager = RetryManager(self.mock_logger)

        with patch.object(retry_manager, '_is_new_day', return_value=False):
            result = retry_manager.should_run_today()

        self.assertFalse(result)
        self.mock_logger.info.assert_called_with("Already successful today, skipping execution")

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_should_run_today_max_attempts_reached(self, mock_home, mock_bwp_config):
        """Test should_run_today when max attempts reached."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        # Create state file with max attempts
        max_attempts_state = {
            "last_run_date": "2024-01-01",
            "success_today": False,
            "attempts_today": 12,  # Max attempts reached
        }
        with open(self.state_file_path, "w") as f:
            json.dump(max_attempts_state, f)

        retry_manager = RetryManager(self.mock_logger)

        with patch.object(retry_manager, '_is_new_day', return_value=False):
            result = retry_manager.should_run_today()

        self.assertFalse(result)
        self.mock_logger.info.assert_called_with("Max attempts reached (12/12), waiting until tomorrow")

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_should_run_today_should_run(self, mock_home, mock_bwp_config):
        """Test should_run_today when should run."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        # Create state file with room for more attempts
        should_run_state = {
            "last_run_date": "2024-01-01",
            "success_today": False,
            "attempts_today": 5,  # Under max attempts
        }
        with open(self.state_file_path, "w") as f:
            json.dump(should_run_state, f)

        retry_manager = RetryManager(self.mock_logger)

        with patch.object(retry_manager, '_is_new_day', return_value=False):
            result = retry_manager.should_run_today()

        self.assertTrue(result)
        self.mock_logger.info.assert_called_with("Should run: attempt 6/12")

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_should_run_today_new_day_reset(self, mock_home, mock_bwp_config):
        """Test should_run_today with new day reset."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)

        with patch.object(retry_manager, '_is_new_day', return_value=True), \
             patch.object(retry_manager, '_reset_daily_state') as mock_reset, \
             patch.object(retry_manager, '_save_state') as mock_save:

            mock_reset.return_value = {"success_today": False, "attempts_today": 0}
            result = retry_manager.should_run_today()

        self.assertTrue(result)
        mock_reset.assert_called_once()
        mock_save.assert_called_once()

    # -------------------------------------------------------------------------
    # Test mark_attempt_start
    # -------------------------------------------------------------------------
    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_mark_attempt_start_retry_disabled(self, mock_home, mock_bwp_config):
        """Test mark_attempt_start when retry is disabled."""
        mock_home.return_value = Path(self.temp_dir)
        disabled_config = self.mock_config.copy()
        disabled_config["retry"]["enabled"] = False
        mock_bwp_config.update(disabled_config)

        retry_manager = RetryManager(self.mock_logger)

        with patch.object(retry_manager, '_save_state') as mock_save:
            retry_manager.mark_attempt_start()

        mock_save.assert_not_called()

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    @patch("abk_bwp.retry_manager.datetime")
    def test_mark_attempt_start_enabled(self, mock_datetime, mock_home, mock_bwp_config):
        """Test mark_attempt_start when retry is enabled."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        mock_now = datetime(2024, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now

        # Create initial state
        initial_state = {"attempts_today": 2}
        with open(self.state_file_path, "w") as f:
            json.dump(initial_state, f)

        retry_manager = RetryManager(self.mock_logger)
        retry_manager.mark_attempt_start()

        # Check updated state
        with open(self.state_file_path) as f:
            updated_state = json.load(f)

        self.assertEqual(updated_state["attempts_today"], 3)
        self.assertEqual(updated_state["last_attempt_time"], "2024-01-01T10:00:00")
        self.mock_logger.info.assert_called_once_with("Starting attempt 3/12")

    # -------------------------------------------------------------------------
    # Test mark_operation_result
    # -------------------------------------------------------------------------
    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_mark_operation_result_retry_disabled(self, mock_home, mock_bwp_config):
        """Test mark_operation_result when retry is disabled."""
        mock_home.return_value = Path(self.temp_dir)
        disabled_config = self.mock_config.copy()
        disabled_config["retry"]["enabled"] = False
        mock_bwp_config.update(disabled_config)

        retry_manager = RetryManager(self.mock_logger)

        with patch.object(retry_manager, '_save_state') as mock_save:
            retry_manager.mark_operation_result("download", True)

        mock_save.assert_not_called()

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_mark_operation_result_success(self, mock_home, mock_bwp_config):
        """Test mark_operation_result with successful operation."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)
        retry_manager.mark_operation_result("download", True)

        # Check state was updated
        with open(self.state_file_path) as f:
            state = json.load(f)

        self.assertTrue(state["operations_status"]["download_success"])
        self.mock_logger.info.assert_called_once_with("Operation download: SUCCESS")

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_mark_operation_result_failure_with_reason(self, mock_home, mock_bwp_config):
        """Test mark_operation_result with failed operation and reason."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)
        retry_manager.mark_operation_result("ftv", False, "TV not responding")

        # Check state was updated
        with open(self.state_file_path) as f:
            state = json.load(f)

        self.assertFalse(state["operations_status"]["ftv_success"])
        self.assertIn("ftv: TV not responding", state["failure_reasons"])

        expected_calls = [
            mock.call("Operation ftv: FAILED"),
            mock.call("Failure reason: TV not responding")
        ]
        self.mock_logger.info.assert_has_calls(expected_calls)

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_mark_operation_result_failure_without_reason(self, mock_home, mock_bwp_config):
        """Test mark_operation_result with failed operation without reason."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)
        retry_manager.mark_operation_result("desktop", False)

        # Check state was updated
        with open(self.state_file_path) as f:
            state = json.load(f)

        self.assertFalse(state["operations_status"]["desktop_success"])
        self.assertEqual(state["failure_reasons"], [])  # No reason added
        self.mock_logger.info.assert_called_once_with("Operation desktop: FAILED")

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_mark_operation_result_creates_operations_status(self, mock_home, mock_bwp_config):
        """Test mark_operation_result creates operations_status if missing."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        # Create state without operations_status
        initial_state = {"attempts_today": 1}
        with open(self.state_file_path, "w") as f:
            json.dump(initial_state, f)

        retry_manager = RetryManager(self.mock_logger)
        retry_manager.mark_operation_result("download", True)

        # Check that operations_status was created
        with open(self.state_file_path) as f:
            state = json.load(f)

        self.assertIn("operations_status", state)
        self.assertTrue(state["operations_status"]["download_success"])

    # -------------------------------------------------------------------------
    # Test mark_run_complete
    # -------------------------------------------------------------------------
    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_mark_run_complete_retry_disabled(self, mock_home, mock_bwp_config):
        """Test mark_run_complete when retry is disabled."""
        mock_home.return_value = Path(self.temp_dir)
        disabled_config = self.mock_config.copy()
        disabled_config["retry"]["enabled"] = False
        mock_bwp_config.update(disabled_config)

        retry_manager = RetryManager(self.mock_logger)

        with patch.object(retry_manager, '_save_state') as mock_save:
            retry_manager.mark_run_complete(True)

        mock_save.assert_not_called()

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    @patch("abk_bwp.retry_manager.datetime")
    def test_mark_run_complete_success(self, mock_datetime, mock_home, mock_bwp_config):
        """Test mark_run_complete with successful run."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        # Create initial state with failure reasons
        initial_state = {"failure_reasons": ["download: network error"]}
        with open(self.state_file_path, "w") as f:
            json.dump(initial_state, f)

        retry_manager = RetryManager(self.mock_logger)
        retry_manager.mark_run_complete(True)

        # Check state was updated
        with open(self.state_file_path) as f:
            state = json.load(f)

        self.assertTrue(state["success_today"])
        self.assertEqual(state["last_success_time"], "2024-01-01T12:00:00")
        self.assertEqual(state["failure_reasons"], [])  # Cleared on success
        self.mock_logger.info.assert_called_once_with("Run successful - no more retries needed today")

    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_mark_run_complete_failure(self, mock_home, mock_bwp_config):
        """Test mark_run_complete with failed run."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        retry_manager = RetryManager(self.mock_logger)
        retry_manager.mark_run_complete(False)

        # Check state was updated
        with open(self.state_file_path) as f:
            state = json.load(f)

        self.assertFalse(state.get("success_today", False))
        self.mock_logger.info.assert_called_once_with("Run failed - will retry next hour if under limit")

    # -------------------------------------------------------------------------
    # Test get_retry_status
    # -------------------------------------------------------------------------
    @patch("abk_bwp.retry_manager.bwp_config", new_callable=dict)
    @patch("abk_bwp.retry_manager.Path.home")
    def test_get_retry_status(self, mock_home, mock_bwp_config):
        """Test get_retry_status method."""
        mock_home.return_value = Path(self.temp_dir)
        mock_bwp_config.update(self.mock_config)

        # Create test state
        test_state = {
            "success_today": True,
            "attempts_today": 2,
            "last_run_date": "2024-01-01"
        }
        with open(self.state_file_path, "w") as f:
            json.dump(test_state, f)

        retry_manager = RetryManager(self.mock_logger)

        with patch.object(retry_manager, 'should_run_today', return_value=False) as mock_should_run:
            status = retry_manager.get_retry_status()

        # The _load_state method merges with default state, so we expect the full state
        expected_current_state = {
            "last_run_date": "2024-01-01",
            "success_today": True,
            "attempts_today": 2,
            "last_attempt_time": None,
            "last_success_time": None,
            "failure_reasons": [],
            "operations_status": {"download_success": False, "desktop_success": False, "ftv_success": False},
        }

        expected_status = {
            "retry_enabled": True,
            "max_attempts_per_day": 12,
            "daily_reset_time": "06:00:00",
            "current_state": expected_current_state,
            "should_run": False,
        }

        self.assertEqual(status, expected_status)
        mock_should_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()

"""Retry manager for hourly execution with daily success tracking."""

import json
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Any

from abk_bwp.config import RETRY_KW, bwp_config
from abk_bwp import abk_common


class RetryManager:
    """Manages retry attempts and daily success tracking for BWP operations."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize retry manager.

        Args:
            logger: Logger instance, defaults to module logger
        """
        self._logger = logger or logging.getLogger(__name__)
        self._state_file = Path.home() / ".abk_bwp_retry_state.json"
        self._load_config()

    def _load_config(self) -> None:
        """Load retry configuration from config file."""
        retry_config = bwp_config.get(RETRY_KW.RETRY.value, {})

        self.retry_enabled = retry_config.get(RETRY_KW.ENABLED.value, True)
        self.max_attempts_per_day = retry_config.get(RETRY_KW.MAX_ATTEMPTS_PER_DAY.value, 12)
        self.daily_reset_time_str = retry_config.get(RETRY_KW.DAILY_RESET_TIME.value, "06:00:00")
        self.require_all_operations_success = retry_config.get(RETRY_KW.REQUIRE_ALL_OPERATIONS_SUCCESS.value, True)

        # Parse reset time
        try:
            self.daily_reset_time = datetime.strptime(self.daily_reset_time_str, "%H:%M:%S").time()
        except ValueError:
            self._logger.warning(f"Invalid daily_reset_time format: {self.daily_reset_time_str}, using 06:00:00")
            self.daily_reset_time = time(6, 0, 0)

    def _load_state(self) -> dict[str, Any]:
        """Load retry state from file.

        Returns:
            Dict containing retry state data
        """
        default_state = {
            "last_run_date": None,
            "success_today": False,
            "attempts_today": 0,
            "last_attempt_time": None,
            "last_success_time": None,
            "failure_reasons": [],
            "operations_status": {"download_success": False, "desktop_success": False, "ftv_success": False},
        }

        if not self._state_file.exists():
            return default_state

        try:
            with open(self._state_file) as f:
                state = json.load(f)
                # Merge with default state to handle missing keys
                default_state.update(state)
                return default_state
        except (json.JSONDecodeError, OSError) as e:
            self._logger.warning(f"Failed to load retry state: {e}, using defaults")
            return default_state

    def _save_state(self, state: dict[str, Any]) -> None:
        """Save retry state to file.

        Args:
            state: State dictionary to save
        """
        try:
            with open(self._state_file, "w") as f:
                json.dump(state, f, indent=2, default=str)
        except OSError as e:
            self._logger.error(f"Failed to save retry state: {e}")

    def _is_new_day(self, state: dict[str, Any]) -> bool:
        """Check if it's a new day based on reset time.

        Args:
            state: Current state dictionary

        Returns:
            True if it's a new day and should reset attempts
        """
        if not state.get("last_run_date"):
            return True

        try:
            last_run_date = datetime.fromisoformat(state["last_run_date"]).date()
            now = datetime.now()
            today = now.date()

            # If it's a different calendar day
            if last_run_date != today:
                return True

            # If it's the same calendar day but past reset time and we haven't reset yet
            return bool(now.time() >= self.daily_reset_time and state.get("last_reset_date") != today.isoformat())
        except (ValueError, TypeError):
            return True

    def _reset_daily_state(self) -> dict[str, Any]:
        """Reset daily retry state.

        Returns:
            Reset state dictionary
        """
        now = datetime.now()
        state = {
            "last_run_date": now.date().isoformat(),
            "last_reset_date": now.date().isoformat(),
            "success_today": False,
            "attempts_today": 0,
            "last_attempt_time": None,
            "last_success_time": None,
            "failure_reasons": [],
            "operations_status": {"download_success": False, "desktop_success": False, "ftv_success": False},
        }

        self._logger.info(f"Daily retry state reset at {now}")
        return state

    @abk_common.function_trace
    def should_run_today(self) -> bool:
        """Check if should run today based on retry logic.

        Returns:
            True if should attempt to run, False if should skip
        """
        if not self.retry_enabled:
            self._logger.debug("Retry mechanism disabled, running normally")
            return True

        state = self._load_state()

        # Reset state if it's a new day
        if self._is_new_day(state):
            state = self._reset_daily_state()
            self._save_state(state)

        # Skip if already successful today
        if state.get("success_today", False):
            self._logger.info("Already successful today, skipping execution")
            return False

        # Check attempt limit
        attempts_today = state.get("attempts_today", 0)
        if attempts_today >= self.max_attempts_per_day:
            self._logger.info(f"Max attempts reached ({attempts_today}/{self.max_attempts_per_day}), waiting until tomorrow")
            return False

        self._logger.info(f"Should run: attempt {attempts_today + 1}/{self.max_attempts_per_day}")
        return True

    @abk_common.function_trace
    def mark_attempt_start(self) -> None:
        """Mark that an attempt is starting."""
        if not self.retry_enabled:
            return

        state = self._load_state()
        state["attempts_today"] = state.get("attempts_today", 0) + 1
        state["last_attempt_time"] = datetime.now().isoformat()

        self._logger.info(f"Starting attempt {state['attempts_today']}/{self.max_attempts_per_day}")
        self._save_state(state)

    @abk_common.function_trace
    def mark_operation_result(self, operation: str, success: bool, failure_reason: str = None) -> None:
        """Mark the result of a specific operation.

        Args:
            operation: Operation name ('download', 'desktop', 'ftv')
            success: Whether the operation succeeded
            failure_reason: Reason for failure if applicable
        """
        if not self.retry_enabled:
            return

        state = self._load_state()

        # Update operation status
        if "operations_status" not in state:
            state["operations_status"] = {}

        state["operations_status"][f"{operation}_success"] = success

        # Track failure reasons
        if not success and failure_reason:
            if "failure_reasons" not in state:
                state["failure_reasons"] = []
            state["failure_reasons"].append(f"{operation}: {failure_reason}")

        self._logger.info(f"Operation {operation}: {'SUCCESS' if success else 'FAILED'}")
        if failure_reason:
            self._logger.info(f"Failure reason: {failure_reason}")

        self._save_state(state)

    @abk_common.function_trace
    def mark_run_complete(self, overall_success: bool) -> None:
        """Mark that a run is complete and determine if we should stop retrying.

        Args:
            overall_success: Whether the overall run was successful
        """
        if not self.retry_enabled:
            return

        state = self._load_state()

        if overall_success:
            state["success_today"] = True
            state["last_success_time"] = datetime.now().isoformat()
            state["failure_reasons"] = []  # Clear failure reasons on success
            self._logger.info("Run successful - no more retries needed today")
        else:
            self._logger.info("Run failed - will retry next hour if under limit")

        self._save_state(state)

    @abk_common.function_trace
    def get_retry_status(self) -> dict[str, Any]:
        """Get current retry status for debugging.

        Returns:
            Dictionary with retry status information
        """
        state = self._load_state()
        return {
            "retry_enabled": self.retry_enabled,
            "max_attempts_per_day": self.max_attempts_per_day,
            "daily_reset_time": self.daily_reset_time_str,
            "current_state": state,
            "should_run": self.should_run_today(),
        }

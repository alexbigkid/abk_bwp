"""Cli - entry point to the abk_bwp package."""

from abk_bwp import clo
from abk_bwp.bingwallpaper import bingwallpaper
from abk_bwp.retry_manager import RetryManager


def main():
    """Main function with retry logic."""
    command_line_options = clo.CommandLineOptions()
    command_line_options.handle_options()

    # Initialize retry manager
    retry_manager = RetryManager(logger=command_line_options.logger)

    # Check if we should run today
    if not retry_manager.should_run_today():
        command_line_options.logger.info("Skipping execution based on retry logic")
        return

    # Mark attempt start
    retry_manager.mark_attempt_start()

    try:
        # Run the main application logic
        overall_success = bingwallpaper(command_line_options)

        # Mark run complete
        retry_manager.mark_run_complete(overall_success)

        if overall_success:
            command_line_options.logger.info("All operations completed successfully - no more retries needed today")
        else:
            command_line_options.logger.info("Some operations failed - will retry next hour if under limit")

    except SystemExit as e:
        # Handle the sys.exit() call from bingwallpaper
        overall_success = e.code == 0
        retry_manager.mark_run_complete(overall_success)

        if overall_success:
            command_line_options.logger.info("All operations completed successfully - no more retries needed today")
        else:
            command_line_options.logger.info("Some operations failed - will retry next hour if under limit")

        # Re-raise the SystemExit to maintain backwards compatibility
        raise

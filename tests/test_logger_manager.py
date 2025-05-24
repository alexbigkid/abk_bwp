"""Test cases for LoggerManager class."""

import unittest
from unittest.mock import patch, mock_open, MagicMock

from abk_bwp.logger_manager import LoggerManager


class TestLoggerManager(unittest.TestCase):
    """Unit tests for LoggerManager."""

    def setUp(self):
        """Set up the test environment."""
        # Reset singleton state before each test
        LoggerManager._instance = None

    def test_singleton_instance(self):
        """Test that LoggerManager is a singleton."""
        instance1 = LoggerManager()
        instance2 = LoggerManager()
        self.assertIs(instance1, instance2, "LoggerManager should be a singleton")

    def test_logger_disabled_when_quiet(self):
        """Test that logger is disabled when quiet mode is enabled."""
        logger_mgr = LoggerManager()
        logger_mgr.configure(quiet=True)
        self.assertTrue(logger_mgr.get_logger().disabled)

    def test_configure_skips_if_already_configured(self):
        """Test that configure() does nothing if already configured."""
        logger_mgr = LoggerManager()
        logger_mgr._configured = True  # Simulate prior configuration

        with (
            patch("abk_bwp.logger_manager.Path.open") as mock_open_file,
            patch("abk_bwp.logger_manager.logging.config.dictConfig") as mock_dict_config,
            patch("abk_bwp.logger_manager.yaml.safe_load") as mock_yaml,
            patch("abk_bwp.logger_manager.Path.exists") as mock_exists,
            patch("abk_bwp.logger_manager.logging.getLogger") as mock_get_logger,
        ):
            logger_mgr.configure(log_into_file=True, quiet=False)

            mock_open_file.assert_not_called()
            mock_dict_config.assert_not_called()
            mock_yaml.assert_not_called()
            mock_exists.assert_not_called()
            mock_get_logger.assert_not_called()

    @patch("abk_bwp.logger_manager.yaml.safe_load", return_value={})
    @patch("abk_bwp.logger_manager.logging.config.dictConfig")
    @patch("abk_bwp.logger_manager.Path.open", new_callable=mock_open, read_data="version: 1")
    @patch("abk_bwp.logger_manager.Path.exists", return_value=True)
    def test_configure_console_logger(
        self, mock_exists, mock_open_file, mock_dict_config, mock_yaml
    ):
        """Test that console logger is configured correctly."""
        t_log_into_file = False
        t_quiet = False
        logger_mgr = LoggerManager()
        with patch("abk_bwp.logger_manager.logging.getLogger") as mock_get_logger:
            mock_exists.assert_not_called()
            mock_open_file.assert_not_called()
            mock_dict_config.assert_not_called()
            mock_yaml.assert_not_called()
            mock_get_logger.return_value = MagicMock()

            logger_mgr.configure(log_into_file=t_log_into_file, quiet=t_quiet)

            mock_exists.assert_called_once()
            mock_open_file.assert_called_once()
            mock_dict_config.assert_called_once()
            mock_yaml.assert_called_once()
            mock_get_logger.assert_called_with("consoleLogger")
            self.assertTrue(logger_mgr._configured)

    @patch("abk_bwp.logger_manager.yaml.safe_load", return_value={})
    @patch("abk_bwp.logger_manager.logging.config.dictConfig")
    @patch("abk_bwp.logger_manager.Path.open", new_callable=mock_open, read_data="version: 1")
    @patch("abk_bwp.logger_manager.Path.exists", return_value=True)
    def test_configure_file_logger_creates_logs_dir(
        self, mock_exists, mock_open_file, mock_dict_config, mock_yaml
    ):
        """Test that file logger is configured and logs directory is created."""
        t_log_into_file = True
        t_quiet = False
        logger_mgr = LoggerManager()
        with (
            patch("abk_bwp.logger_manager.logging.getLogger") as mock_get_logger,
            patch("abk_bwp.logger_manager.Path.mkdir") as mock_mkdir,
        ):
            mock_exists.assert_not_called()
            mock_open_file.assert_not_called()
            mock_dict_config.assert_not_called()
            mock_yaml.assert_not_called()
            mock_get_logger.return_value = MagicMock()

            logger_mgr.configure(log_into_file=t_log_into_file, quiet=t_quiet)

            mock_exists.assert_called_once()
            mock_open_file.assert_called_once()
            mock_dict_config.assert_called_once()
            mock_yaml.assert_called_once()
            mock_mkdir.assert_called_once()
            mock_get_logger.assert_called_with("fileLogger")
            self.assertTrue(logger_mgr._configured)

    @patch("abk_bwp.logger_manager.yaml.safe_load", return_value={})
    @patch("abk_bwp.logger_manager.logging.config.dictConfig")
    @patch("abk_bwp.logger_manager.Path.open", new_callable=mock_open, read_data="version: 1")
    @patch("abk_bwp.logger_manager.Path.exists", return_value=True)
    def test_configure_quiet_mode(self, mock_exists, mock_open_file, mock_dict_config, mock_yaml):
        """Test that quiet mode disables the logger."""
        t_log_into_file = False
        t_quiet = True
        logger_mgr = LoggerManager()
        with patch("abk_bwp.logger_manager.logging.getLogger") as mock_get_logger:
            mock_exists.assert_not_called()
            mock_open_file.assert_not_called()
            mock_dict_config.assert_not_called()
            mock_yaml.assert_not_called()
            dummy_logger = MagicMock()
            mock_get_logger.return_value = dummy_logger

            logger_mgr.configure(log_into_file=t_log_into_file, quiet=t_quiet)

            mock_exists.assert_not_called()
            mock_open_file.assert_not_called()
            mock_dict_config.assert_not_called()
            mock_yaml.assert_not_called()
            mock_get_logger.assert_called_with("consoleLogger")
            self.assertTrue(logger_mgr._configured)
            self.assertTrue(logger_mgr.get_logger().disabled)

    @patch("abk_bwp.logger_manager.yaml.safe_load", return_value={})
    @patch("abk_bwp.logger_manager.logging.config.dictConfig")
    @patch("abk_bwp.logger_manager.Path.open", new_callable=mock_open, read_data="version: 1")
    @patch("abk_bwp.logger_manager.Path.exists", return_value=True)
    def test_configure_quiet_mode_with_file_logger(
        self, mock_exists, mock_open_file, mock_dict_config, mock_yaml
    ):
        """Test that quiet mode disables logging even if file logging is requested."""
        t_log_into_file = True
        t_quiet = True
        logger_mgr = LoggerManager()
        with patch("abk_bwp.logger_manager.logging.getLogger") as mock_get_logger:
            mock_exists.assert_not_called()
            mock_open_file.assert_not_called()
            mock_dict_config.assert_not_called()
            mock_yaml.assert_not_called()
            dummy_logger = MagicMock()
            mock_get_logger.return_value = dummy_logger

            logger_mgr.configure(log_into_file=t_log_into_file, quiet=t_quiet)

            mock_exists.assert_not_called()
            mock_open_file.assert_not_called()
            mock_dict_config.assert_not_called()
            mock_yaml.assert_not_called()
            mock_get_logger.assert_called_with("consoleLogger")
            self.assertTrue(logger_mgr._configured)
            self.assertTrue(logger_mgr.get_logger().disabled)

    @patch(
        "abk_bwp.logger_manager.yaml.safe_load",
        return_value={
            "version": 1,
            "formatters": {"simple": {"format": "%(message)s"}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                    "level": "DEBUG",
                }
            },
            "loggers": {
                "fileLogger": {"level": "DEBUG", "handlers": ["console"], "propagate": False}
            },
        },
    )
    @patch("abk_bwp.logger_manager.logging.config.dictConfig")
    @patch("abk_bwp.logger_manager.Path.open", new_callable=mock_open, read_data="version: 1")
    @patch("abk_bwp.logger_manager.Path.exists", return_value=True)
    def test_configure_file_logging_logger_selected(
        self, mock_exists, mock_open_file, mock_dict_config, mock_yaml
    ):
        """Test that configure() correctly sets fileLogger from logging.yaml."""
        logger_mgr = LoggerManager()
        with patch("abk_bwp.logger_manager.logging.getLogger") as mock_get_logger:
            file_logger = MagicMock(name="fileLogger")
            file_logger.name = "fileLogger"
            mock_get_logger.return_value = file_logger

            logger_mgr.configure(log_into_file=True)

            mock_dict_config.assert_called_once()
            mock_get_logger.assert_called_with("fileLogger")
            logger = logger_mgr.get_logger()
            self.assertEqual(logger.name, "fileLogger")

    def test_configure_raises_file_not_found_for_missing_logging_yaml(self):
        """Test that configure() raises FileNotFoundError if logging.yaml is missing."""
        logger_mgr = LoggerManager()

        with (
            patch("abk_bwp.logger_manager.Path.exists", return_value=True),
            patch(
                "abk_bwp.logger_manager.Path.open", side_effect=FileNotFoundError("No such file")
            ),
        ):
            with self.assertRaises(FileNotFoundError) as context:
                logger_mgr.configure(log_into_file=True, quiet=False)

            self.assertIn("logging.yaml not found", str(context.exception))

    def test_configure_handles_general_exception_and_disables_logger(self):
        """Test that configure() disables logging if an unexpected exception occurs."""
        logger_mgr = LoggerManager()

        with (
            patch("abk_bwp.logger_manager.Path.exists", return_value=True),
            patch(
                "abk_bwp.logger_manager.Path.open", side_effect=Exception("Unexpected failure")
            ),
            patch("abk_bwp.logger_manager.logging.getLogger") as mock_get_logger,
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            logger_mgr.configure(log_into_file=False, quiet=False)

            self.assertTrue(mock_logger.disabled)
            mock_logger.exception.assert_called_once()
            self.assertTrue(logger_mgr._configured)

    def test_get_logger_raises_if_not_configured(self):
        """Test that get_logger raises RuntimeError if not configured."""
        logger_mgr = LoggerManager()
        with self.assertRaises(RuntimeError):
            logger_mgr.get_logger()

    def test_configure_raises_file_not_found_if_pyproject_missing(self):
        """Test that FileNotFoundError is raised when pyproject.toml is not found."""
        logger_mgr = LoggerManager()

        with patch("abk_bwp.logger_manager.Path.exists", return_value=False):
            with self.assertRaises(FileNotFoundError) as context:
                logger_mgr.configure(log_into_file=True)

            self.assertIn("pyproject.toml not found", str(context.exception))


if __name__ == "__main__":
    unittest.main()

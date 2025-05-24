"""Logger Manager for centralized logging configuration."""

import logging
import logging.config
from pathlib import Path
import yaml


class LoggerManager:
    """Singleton LoggerManager that configures and exposes a global logger."""

    _instance = None

    def __new__(cls):
        """Creates an instance of the LoggerManager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the LoggerManager."""
        if not hasattr(self, "_configured"):
            self._configured = False
            self._logger = logging.getLogger("consoleLogger")
            self._logger.disabled = True

    def configure(self, log_into_file=False, quiet=False):
        """Configure logging once based on flags."""
        if self._configured:
            return  # Prevent reconfiguration

        try:
            if quiet:
                logging.disable(logging.CRITICAL)
                self._logger = logging.getLogger("consoleLogger")
                self._logger.disabled = True
                self._configured = True
                return

            root_dir = self._find_project_root()
            if log_into_file:
                (root_dir / "logs").mkdir(parents=True, exist_ok=True)

            config_path = root_dir / "logging.yaml"
            with config_path.open("r", encoding="utf-8") as stream:
                config_yaml = yaml.safe_load(stream)
                logging.config.dictConfig(config_yaml)

            logger_name = "fileLogger" if log_into_file else "consoleLogger"
            self._logger = logging.getLogger(logger_name)
            self._configured = True

        except FileNotFoundError as e:
            raise FileNotFoundError(f"logging.yaml not found: {e}") from e
        except Exception as e:
            self._logger = logging.getLogger(__name__)
            self._logger.exception(f"ERROR: Logging setup failed due to: {e}")
            self._logger.disabled = True
            self._configured = True

    def get_logger(self, name=None) -> logging.Logger:
        """Get logger (optionally by name)."""
        if not self._configured:
            raise RuntimeError("LoggerManager not configured yet. Call configure() first.")
        return logging.getLogger(name) if name else self._logger

    def _find_project_root(self) -> Path:
        start = Path.cwd()
        for parent in [start, *start.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        raise FileNotFoundError("pyproject.toml not found")

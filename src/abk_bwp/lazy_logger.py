"""Lazy loader for LoggerManager."""


class LazyLoggerProxy:
    """A proxy logger that defers instantiation until LoggerManager is configured."""

    def __init__(self, name=None):
        """Initialize the LazyLoggerProxy with an optional name."""
        self._name = name
        self._real_logger = None

    def _resolve(self):
        """Resolve the real logger instance, initializing it if necessary."""
        if self._real_logger is None:
            from abk_bwp.logger_manager import LoggerManager

            self._real_logger = LoggerManager().get_logger(self._name or __name__)
        return self._real_logger

    def __getattr__(self, attr):
        """Delegates attribute access to the real logger."""
        return getattr(self._resolve(), attr)

"""
WinDebloatX - Unified Logging Subsystem
Provides colored console output, file logging, and GUI callback integration.
"""

import logging
import os
import sys
from typing import Callable, List, Optional

LOG_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "WinDebloatX", "Logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "windebloatx.log")

class DebloatLogger:
    _instance: Optional["DebloatLogger"] = None
    _gui_callbacks: List[Callable[[str, str], None]] = []

    def __init__(self):
        self.logger = logging.getLogger("WinDebloatX")
        self.logger.setLevel(logging.DEBUG)

        # File handler (persists across runs)
        try:
            fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            fh.setFormatter(file_formatter)
            self.logger.addHandler(fh)
        except Exception:
            pass

        # Stream handler (console)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        ch.setFormatter(console_formatter)
        self.logger.addHandler(ch)

    @classmethod
    def get_instance(cls) -> "DebloatLogger":
        if cls._instance is None:
            cls._instance = DebloatLogger()
        return cls._instance

    @classmethod
    def register_gui_callback(cls, callback: Callable[[str, str], None]):
        """Register a callback for GUI log updates: callback(level: str, message: str)"""
        if callback not in cls._gui_callbacks:
            cls._gui_callbacks.append(callback)

    def _notify_callbacks(self, level: str, message: str):
        for cb in self._gui_callbacks:
            try:
                cb(level, message)
            except Exception:
                pass

    def info(self, msg: str):
        self.logger.info(msg)
        self._notify_callbacks("INFO", msg)

    def success(self, msg: str):
        self.logger.info(f"SUCCESS: {msg}")
        self._notify_callbacks("SUCCESS", msg)

    def warning(self, msg: str):
        self.logger.warning(msg)
        self._notify_callbacks("WARNING", msg)

    def error(self, msg: str):
        self.logger.error(msg)
        self._notify_callbacks("ERROR", msg)

    def debug(self, msg: str):
        self.logger.debug(msg)
        self._notify_callbacks("DEBUG", msg)


# Module-level convenience functions
_logger = DebloatLogger.get_instance()
log_info = _logger.info
log_success = _logger.success
log_warning = _logger.warning
log_error = _logger.error
log_debug = _logger.debug
register_log_callback = DebloatLogger.register_gui_callback

"""
WinDebloatX Core Package
"""
from core.logger import log_info, log_success, log_warning, log_error
from core.privileges import is_admin, elevate_and_relaunch
from core.restore_point import create_restore_point

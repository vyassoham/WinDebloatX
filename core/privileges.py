"""
WinDebloatX - Windows Privileges and UAC Elevation Management
Handles Administrator privilege checks and seamless self-elevation via ShellExecute.
"""

import ctypes
import os
import sys
from core.logger import log_info, log_warning, log_error

def is_admin() -> bool:
    """Check if current process has elevated Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def elevate_and_relaunch() -> bool:
    """
    Relaunches the current python script with UAC elevation (Administrator).
    Returns True if elevation dialog was spawned, False if failed.
    """
    if is_admin():
        log_info("Already running with Administrator privileges.")
        return True

    log_info("Requesting Administrator elevation (UAC prompt)...")
    try:
        # Re-run python with current arguments
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        
        # If running as compiled exe or python interpreter
        executable = sys.executable

        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            f'"{script}" {params}' if not getattr(sys, "frozen", False) else params,
            None,
            1  # SW_SHOWNORMAL
        )
        # ShellExecute returns > 32 on success
        if ret > 32:
            sys.exit(0)
            return True
        else:
            log_error(f"UAC elevation failed or was denied (code {ret}).")
            return False
    except Exception as e:
        log_error(f"Failed to elevate process: {e}")
        return False

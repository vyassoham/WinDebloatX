"""
WinDebloatX - Windows Update Persistence & Automated Guardian
Manages a lightweight Windows Scheduled Task that re-asserts debloat and privacy
configurations after Windows Cumulative and Feature Updates.
"""

import os
import subprocess
import sys
from typing import Tuple
from core.logger import log_debug, log_error, log_info, log_success

TASK_NAME = r"\WinDebloatX\PeriodicAudit"

def is_persistence_task_installed() -> bool:
    """Checks whether the WinDebloatX persistence scheduled task exists."""
    cmd = f'schtasks.exe /Query /TN "{TASK_NAME}"'
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return proc.returncode == 0
    except Exception:
        return False

def install_persistence_task() -> Tuple[bool, str]:
    """
    Creates a scheduled task running with HIGHEST privileges at system startup
    to re-apply telemetry hardening after Windows Updates.
    """
    python_exe = sys.executable
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))

    action_cmd = f'"{python_exe}" "{main_py}" --disable-telemetry --silent'
    cmd = (
        f'schtasks.exe /Create /TN "{TASK_NAME}" /TR "{action_cmd}" '
        f'/SC ONLOGON /RU "SYSTEM" /RL HIGHEST /F'
    )

    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            msg = "Persistence scheduled task successfully registered (runs on logon to guard against Windows Update resets)."
            log_success(msg)
            return True, msg
        else:
            msg = f"Failed to register task: {proc.stderr.strip() or proc.stdout.strip()}"
            log_error(msg)
            return False, msg
    except Exception as e:
        msg = f"Exception creating persistence task: {e}"
        log_error(msg)
        return False, msg

def remove_persistence_task() -> Tuple[bool, str]:
    """Removes the scheduled persistence task."""
    cmd = f'schtasks.exe /Delete /TN "{TASK_NAME}" /F'
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            msg = "Persistence task removed successfully."
            log_success(msg)
            return True, msg
        return False, "Task was not found or could not be removed."
    except Exception as e:
        return False, str(e)

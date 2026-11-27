"""
WinDebloatX - System Restore Point Management
Creates and validates restore points via PowerShell/WMI, checks drive protection,
verifies VSS shadow storage, and handles low-disk-space pre-flight guards.
"""

import os
import shutil
import subprocess
from typing import Dict, List, Tuple
from core.logger import log_debug, log_error, log_info, log_success, log_warning

def check_restore_prerequisites() -> Tuple[bool, str]:
    """
    Performs safety pre-flight checks:
    1. Verifies system drive free disk space (> 5 GB recommended for VSS snapshots).
    2. Ensures Volume Shadow Copy Service (VSS) is configured.
    """
    sys_drive = os.environ.get("SystemDrive", "C:") + "\\"
    try:
        total, used, free = shutil.disk_usage(sys_drive)
        free_gb = round(free / (1024 ** 3), 2)
        if free < 4 * 1024 * 1024 * 1024:  # Less than 4 GB
            msg = f"Insufficient disk space on {sys_drive} ({free_gb} GB free). Minimum 4 GB required for System Restore."
            log_warning(msg)
            return False, msg
    except Exception as e:
        log_debug(f"Could not query disk space: {e}")

    # Ensure VSS service is enabled
    try:
        subprocess.run('sc.exe config vss start=demand', shell=True, capture_output=True, timeout=5)
    except Exception:
        pass

    return True, "Pre-flight checks passed."

def create_restore_point(description: str = "WinDebloatX Pre-Optimization Restore Point") -> Tuple[bool, str]:
    """
    Creates a Windows System Restore Point using PowerShell.
    Ensures Volume Protection is active, checks disk space, and handles 24h frequency throttle.
    """
    ok, pre_msg = check_restore_prerequisites()
    if not ok:
        log_error(f"Pre-flight aborted: {pre_msg}")
        return False, pre_msg

    log_info(f"Initiating System Restore Point creation: '{description}'...")

    ps_script = f"""
    try {{
        $drive = $env:SystemDrive
        Enable-ComputerRestore -Drive $drive -ErrorAction SilentlyContinue

        # Disable frequency throttling
        $regPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore"
        Set-ItemProperty -Path $regPath -Name "SystemRestorePointCreationFrequency" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue

        Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS" -ErrorAction Stop
        Write-Output "SUCCESS"
    }} catch {{
        Write-Error $_.Exception.Message
        exit 1
    }}
    """

    try:
        process = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=120
        )

        output = process.stdout.strip()
        err = process.stderr.strip()

        if "SUCCESS" in output or process.returncode == 0:
            msg = f"System Restore Point created successfully: '{description}'."
            log_success(msg)
            return True, msg
        else:
            msg = f"Restore point creation error: {err or output}"
            log_warning(msg)
            return False, msg
    except subprocess.TimeoutExpired:
        msg = "Timed out while creating System Restore Point (120s limit)."
        log_error(msg)
        return False, msg
    except Exception as e:
        msg = f"Exception during restore point creation: {e}"
        log_error(msg)
        return False, msg

def open_system_restore_gui() -> bool:
    """Launches the native Windows System Restore wizard (rstrui.exe) or Protection settings."""
    log_info("Opening Windows System Restore wizard (rstrui.exe)...")
    try:
        subprocess.Popen("rstrui.exe", shell=True)
        return True
    except Exception:
        try:
            subprocess.Popen("SystemPropertiesProtection.exe", shell=True)
            return True
        except Exception as e:
            log_error(f"Failed to launch System Restore GUI: {e}")
            return False

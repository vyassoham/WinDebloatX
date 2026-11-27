"""
WinDebloatX - Windows Scheduled Tasks Optimizer
Disables background telemetry, CEIP, diagnostics, and appraiser scheduled tasks.
"""

import subprocess
from typing import List, Tuple
from core.logger import log_debug, log_error, log_info, log_success

TELEMETRY_TASKS: List[str] = [
    r"\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
    r"\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
    r"\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
    r"\Microsoft\Windows\Application Experience\ProgramDataUpdater",
    r"\Microsoft\Windows\Application Experience\StartupAppTask",
    r"\Microsoft\Windows\Autochk\Proxy",
    r"\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector",
    r"\Microsoft\Windows\Feedback\Siuf\DmClient",
    r"\Microsoft\Windows\Windows Error Reporting\QueueReporting",
    r"\Microsoft\Windows\CloudExperienceHost\CreateObjectTask",
    r"\Microsoft\Windows\DiskFootprint\Diagnostics"
]

def disable_task(task_path: str) -> bool:
    """Disables a specific scheduled task via schtasks.exe."""
    cmd = f'schtasks.exe /Change /TN "{task_path}" /Disable'
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            log_debug(f"Disabled scheduled task: {task_path}")
            return True
        return False
    except Exception as e:
        log_debug(f"Could not disable task {task_path}: {e}")
        return False

def enable_task(task_path: str) -> bool:
    """Enables a specific scheduled task via schtasks.exe."""
    cmd = f'schtasks.exe /Change /TN "{task_path}" /Enable'
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return proc.returncode == 0
    except Exception as e:
        log_debug(f"Could not enable task {task_path}: {e}")
        return False

def disable_all_telemetry_tasks() -> Tuple[int, int]:
    """Disables all known telemetry, diagnostic, and CEIP scheduled tasks."""
    log_info("Disabling telemetry and diagnostic scheduled tasks...")
    success_count = 0
    skipped_count = 0

    for task in TELEMETRY_TASKS:
        if disable_task(task):
            success_count += 1
        else:
            skipped_count += 1

    log_success(f"Disabled {success_count} telemetry tasks ({skipped_count} skipped or not present).")
    return success_count, skipped_count

def restore_telemetry_tasks() -> int:
    """Re-enables telemetry scheduled tasks to default state."""
    log_info("Re-enabling scheduled tasks...")
    restored = 0
    for task in TELEMETRY_TASKS:
        if enable_task(task):
            restored += 1
    return restored
